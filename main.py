"""
Ratio - Asset Strength Rankings API
Main Flask application
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import time
import json

import config
from massive_client import MassiveClient
from coincap_client import CoinCapClient
from tournament import calculate_tournament_rankings, format_rankings_summary

app = Flask(__name__)
CORS(app)

# Initialize API clients
massive = MassiveClient(config.MASSIVE_API_KEY)
coincap = CoinCapClient()

# In-memory cache (will use Redis in production)
cache = {
    'big_board': None,
    'crypto_explorer': None,
    'last_update': None
}

def fetch_all_assets():
    """
    Fetch data for all assets
    Returns: Dict of {symbol: [weekly_closes]}
    """
    print("\n" + "="*60)
    print(f"FETCHING ALL ASSET DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    all_data = {}
    errors = []
    
    # 1. Fetch stocks
    print("\n📊 Fetching S&P 500 stocks...")
    stock_symbols = massive.get_sp500_symbols()
    print(f"Found {len(stock_symbols)} stock symbols")
    
    for i, symbol in enumerate(stock_symbols):
        try:
            prices = massive.get_weekly_data(symbol, weeks=config.MA_PERIOD)
            print(f"  {symbol}: Got {len(prices)} weeks of data")
            if len(prices) >= config.MA_PERIOD:
                all_data[symbol] = prices
                print(f"  ✓ {symbol} added to dataset")
            else:
                errors.append(f"{symbol}: insufficient data ({len(prices)} weeks)")
                print(f"  ✗ {symbol}: only {len(prices)} weeks")
            
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(stock_symbols)} stocks...")
                time.sleep(0.5)  # Reduced from 1 second
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
            print(f"  ✗ {symbol}: ERROR - {str(e)}")
    
    print(f"✓ Loaded {len([s for s in stock_symbols if s in all_data])} stocks")
    
    # 2. Fetch ETFs
    print("\n📈 Fetching ETFs...")
    etf_symbols = massive.get_major_etfs()
    print(f"Found {len(etf_symbols)} ETF symbols")
    
    for i, symbol in enumerate(etf_symbols):
        try:
            prices = massive.get_weekly_data(symbol, weeks=config.MA_PERIOD)
            if len(prices) >= config.MA_PERIOD:
                all_data[symbol] = prices
            else:
                errors.append(f"{symbol}: insufficient data")
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(etf_symbols)} ETFs...")
                time.sleep(1)
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
    
    print(f"✓ Loaded {len([s for s in etf_symbols if s in all_data])} ETFs")
    
    # 3. Fetch crypto
    print("\n🪙 Fetching cryptocurrency data...")
    crypto_symbols = coincap.get_top_crypto_symbols(limit=config.CRYPTO_LIMIT)
    print(f"Found {len(crypto_symbols)} crypto symbols")
    
    for i, symbol in enumerate(crypto_symbols):
        try:
            prices = coincap.get_weekly_data(symbol, weeks=config.MA_PERIOD)
            if len(prices) >= config.MA_PERIOD:
                all_data[symbol] = prices
            else:
                errors.append(f"{symbol}: insufficient data")
            
            if (i + 1) % 20 == 0:
                print(f"  Processed {i + 1}/{len(crypto_symbols)} crypto...")
                time.sleep(0.5)
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
    
    print(f"✓ Loaded {len([s for s in crypto_symbols if s in all_data])} cryptocurrencies")
    
    print("\n" + "="*60)
    print(f"TOTAL ASSETS LOADED: {len(all_data)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
    print("="*60 + "\n")
    
    return all_data

def update_rankings():
    """
    Fetch fresh data and calculate rankings
    Updates global cache
    """
    try:
        # Fetch all asset data
        assets_data = fetch_all_assets()
        
        if len(assets_data) < 10:
            raise ValueError("Not enough assets loaded")
        
        # Calculate tournament rankings
        print("\n🏆 Calculating tournament rankings...")
        all_rankings = calculate_tournament_rankings(assets_data)
        
        # Identify crypto assets for crypto explorer
        crypto_rankings = [
            asset for asset in all_rankings 
            if asset['symbol'] in coincap.symbol_to_id or 
               asset['symbol'] in coincap.get_top_crypto_symbols(limit=config.CRYPTO_LIMIT)
        ]
        
        # Get top 20 crypto for big board
        top_20_crypto = crypto_rankings[:config.CRYPTO_TOP_FOR_BIGBOARD]
        top_20_crypto_symbols = [asset['symbol'] for asset in top_20_crypto]
        
        # Create big board (stocks + ETFs + top 20 crypto)
        big_board = [
            asset for asset in all_rankings
            if asset['symbol'] not in coincap.symbol_to_id or  # Not crypto
               asset['symbol'] in top_20_crypto_symbols  # Or top 20 crypto
        ]
        
        # Update cache
        cache['big_board'] = big_board
        cache['crypto_explorer'] = crypto_rankings
        cache['last_update'] = datetime.now().isoformat()
        
        print("\n✅ Rankings updated successfully!")
        print(format_rankings_summary(big_board, top_n=10))
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating rankings: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    big_board = cache.get('big_board') or []
    crypto_explorer = cache.get('crypto_explorer') or []
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'last_update': cache.get('last_update'),
        'big_board_assets': len(big_board),
        'crypto_assets': len(crypto_explorer),
        'massive_api': 'configured' if config.MASSIVE_API_KEY != 'YOUR_KEY_HERE' else 'not configured',
        'data_loaded': cache.get('last_update') is not None
    })

@app.route('/api/big-board', methods=['GET'])
def get_big_board():
    """Get Big Board rankings"""
    if not cache.get('big_board'):
        return jsonify({'error': 'Data not yet loaded. Try again in a moment.'}), 503
    
    # Optional filters
    asset_type = request.args.get('type')  # 'stocks', 'etfs', 'crypto'
    limit = request.args.get('limit', type=int)
    
    results = cache['big_board']
    
    # Apply filters (simplified for MVP)
    if asset_type:
        # Would filter by type
        pass
    
    if limit:
        results = results[:limit]
    
    return jsonify({
        'rankings': results,
        'total': len(cache['big_board']),
        'last_update': cache['last_update'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/crypto-explorer', methods=['GET'])
def get_crypto_explorer():
    """Get Crypto Explorer rankings"""
    if not cache.get('crypto_explorer'):
        return jsonify({'error': 'Data not yet loaded.'}), 503
    
    limit = request.args.get('limit', type=int)
    results = cache['crypto_explorer']
    
    if limit:
        results = results[:limit]
    
    return jsonify({
        'rankings': results,
        'total': len(cache['crypto_explorer']),
        'last_update': cache['last_update'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/asset/<symbol>', methods=['GET'])
def get_asset(symbol):
    """Get individual asset details"""
    symbol = symbol.upper()
    
    # Search in big board
    asset = next((a for a in cache.get('big_board', []) if a['symbol'] == symbol), None)
    
    # Search in crypto explorer if not found
    if not asset:
        asset = next((a for a in cache.get('crypto_explorer', []) if a['symbol'] == symbol), None)
    
    if not asset:
        return jsonify({'error': f'Asset {symbol} not found'}), 404
    
    return jsonify(asset)

@app.route('/api/network-test', methods=['GET'])
def network_test():
    """Test network connectivity"""
    import socket
    import requests
    
    results = {}
    
    # Test DNS resolution
    try:
        ip = socket.gethostbyname('api.polygon.io')
        results['polygon_dns'] = f'✓ Resolved to {ip}'
    except Exception as e:
        results['polygon_dns'] = f'✗ DNS failed: {str(e)}'
    
    try:
        ip = socket.gethostbyname('api.coincap.io')
        results['coincap_dns'] = f'✓ Resolved to {ip}'
    except Exception as e:
        results['coincap_dns'] = f'✗ DNS failed: {str(e)}'
    
    # Test HTTP connection
    try:
        response = requests.get('https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-10?apiKey=' + config.MASSIVE_API_KEY, timeout=5)
        results['polygon_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['polygon_http'] = f'✗ HTTP failed: {str(e)}'
    
    try:
        response = requests.get('https://api.coincap.io/v2/assets/bitcoin', timeout=5)
        results['coincap_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['coincap_http'] = f'✗ HTTP failed: {str(e)}'
    
    return jsonify(results)

@app.route('/api/update', methods=['GET', 'POST'])
def trigger_update():
    """Manually trigger data update (for testing)"""
    success = update_rankings()
    if success:
        return jsonify({'message': 'Update successful', 'timestamp': cache['last_update']})
    else:
        return jsonify({'error': 'Update failed'}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("RATIO - ASSET STRENGTH RANKINGS API")
    print("="*60)
    print(f"Massive API: {'✓ Configured' if config.MASSIVE_API_KEY != 'YOUR_KEY_HERE' else '✗ Not configured'}")
    print(f"CoinCap API: ✓ Ready (no key needed)")
    print(f"Port: {config.PORT}")
    print("="*60 + "\n")
    
    # Skip initial data load - do it via /api/update endpoint instead
    print("⚠️  Data not loaded on startup.")
    print("📍 Trigger data load: POST to /api/update")
    
    # Start server
    print(f"\n🚀 Starting server on port {config.PORT}...")
    print(f"📍 Health check: http://localhost:{config.PORT}/api/health")
    print(f"📍 Big Board: http://localhost:{config.PORT}/api/big-board")
    print(f"📍 Crypto Explorer: http://localhost:{config.PORT}/api/crypto-explorer\n")
    
    app.run(host='0.0.0.0', port=config.PORT, debug=config.DEBUG)
