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
from coincap_client import CoinbaseClient
from cryptocompare_client import CryptoCompareClient
from cache_manager import CacheManager
from name_lookup import NameLookup
from tournament import calculate_tournament_rankings, format_rankings_summary

app = Flask(__name__)
CORS(app)

# Initialize API clients
massive = MassiveClient(config.MASSIVE_API_KEY)
coinbase = CoinbaseClient()
cryptocompare = CryptoCompareClient()

# Initialize persistent cache and name lookup
cache_manager = CacheManager()
name_lookup = NameLookup()
cache = cache_manager.data  # For backwards compatibility

def fetch_single_asset(symbol: str) -> list:
    """
    Fetch data for a single asset
    Returns: List of weekly prices or None if failed
    """
    print(f"    Fetching {symbol}...")
    
    # Try Coinbase first (if it's crypto)
    if symbol in coinbase.get_all_products():
        try:
            return coinbase.get_weekly_data(symbol, weeks=config.MA_PERIOD)
        except:
            pass
    
    # Try CryptoCompare (if it's crypto)
    if symbol in cryptocompare.symbols:
        try:
            return cryptocompare.get_weekly_data(symbol, weeks=config.MA_PERIOD)
        except:
            pass
    
    # Try Massive (stocks/ETFs)
    try:
        return massive.get_weekly_data(symbol, weeks=config.MA_PERIOD)
    except Exception as e:
        print(f"    ✗ {symbol}: {e}")
        return None

def fetch_assets_by_type(asset_type: str, test_mode=False) -> dict:
    """
    Fetch data for assets of a specific type
    Returns: Dict of {symbol: [prices]}
    """
    all_data = {}
    
    if asset_type == 'stocks':
        symbols = massive.get_sp500_symbols()
        if test_mode:
            symbols = symbols[:50]
        print(f"Fetching {len(symbols)} stocks...")
        
        for symbol in symbols:
            try:
                prices = massive.get_weekly_data(symbol, weeks=config.MA_PERIOD)
                if len(prices) >= config.MA_PERIOD:
                    all_data[symbol] = prices
            except:
                pass
    
    elif asset_type == 'etfs':
        symbols = massive.get_major_etfs()
        if test_mode:
            symbols = symbols[:10]
        print(f"Fetching {len(symbols)} ETFs...")
        
        for symbol in symbols:
            try:
                prices = massive.get_weekly_data(symbol, weeks=config.MA_PERIOD)
                if len(prices) >= config.MA_PERIOD:
                    all_data[symbol] = prices
            except:
                pass
    
    elif asset_type == 'crypto':
        # Only BTC and ETH for now
        symbols = ['BTC', 'ETH']
        print(f"Fetching {len(symbols)} crypto (BTC + ETH only)...")
        
        for symbol in symbols:
            try:
                prices = coinbase.get_weekly_data(symbol, weeks=config.MA_PERIOD)
                if len(prices) >= config.MA_PERIOD:
                    all_data[symbol] = prices
            except:
                pass
    
    return all_data

def fetch_all_assets(test_mode=False):
    """
    Fetch data for all assets
    
    Args:
        test_mode: If True, use limited asset set for fast iteration
        
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
    
    if test_mode:
        stock_symbols = stock_symbols[:50]  # Only 50 stocks in test mode
        print(f"⚡ TEST MODE: Limiting to {len(stock_symbols)} stocks")
    else:
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
    
    if test_mode:
        etf_symbols = etf_symbols[:10]  # Only 10 ETFs in test mode
        print(f"⚡ TEST MODE: Limiting to {len(etf_symbols)} ETFs")
    else:
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
    
    # 3. Fetch crypto from Coinbase (BTC + ETH only)
    print("\n🪙 Fetching cryptocurrency data from Coinbase...")
    coinbase_symbols = ['BTC', 'ETH']  # Only BTC and ETH for now
    
    if test_mode:
        coinbase_symbols = ['BTC']  # Just BTC in test mode
        print(f"⚡ TEST MODE: Limiting to {len(coinbase_symbols)} crypto")
    else:
        print(f"Found {len(coinbase_symbols)} crypto (BTC + ETH only)")
    
    for i, symbol in enumerate(coinbase_symbols):
        try:
            prices = coinbase.get_weekly_data(symbol, weeks=config.MA_PERIOD)
            if len(prices) >= config.MA_PERIOD:
                all_data[symbol] = prices
            else:
                errors.append(f"{symbol}: insufficient data")
            
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(coinbase_symbols)} crypto from Coinbase...")
        except Exception as e:
            errors.append(f"{symbol}: {str(e)}")
    
    print(f"✓ Loaded {len([s for s in coinbase_symbols if s in all_data])} from Coinbase")
    
    # Skip CryptoCompare for now (only using BTC + ETH from Coinbase)
    cryptocompare_symbols = []
    
    print(f"✓ Loaded {len([s for s in coinbase_symbols if s in all_data]) + len([s for s in cryptocompare_symbols if s in all_data])} cryptocurrencies total")
    
    print("\n" + "="*60)
    print(f"TOTAL ASSETS LOADED: {len(all_data)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
    print("="*60 + "\n")
    
    return all_data

def update_rankings(test_mode=False, asset_type=None, symbol=None):
    """
    Fetch fresh data and calculate rankings
    Updates global cache
    
    Args:
        test_mode: If True, use limited asset set for fast iteration (2-3 min)
        asset_type: If set, only update this type ('stocks', 'etfs', 'crypto')
        symbol: If set, only update this single asset
    """
    try:
        # Start with existing cached data
        existing_data = cache_manager.get_assets().copy()
        
        # Determine what to fetch
        if symbol:
            # INCREMENTAL: Add/update single asset
            print(f"\n⚡ INCREMENTAL UPDATE: {symbol}")
            new_data = fetch_single_asset(symbol)
            if new_data:
                existing_data[symbol] = new_data
            assets_data = existing_data
            
        elif asset_type:
            # TYPE-SPECIFIC: Update only one asset type
            print(f"\n⚡ TYPE-SPECIFIC UPDATE: {asset_type}")
            new_data = fetch_assets_by_type(asset_type, test_mode=test_mode)
            # Merge with existing
            existing_data.update(new_data)
            assets_data = existing_data
            
        else:
            # FULL UPDATE: Fetch everything
            print(f"\n⚡ FULL UPDATE")
            assets_data = fetch_all_assets(test_mode=test_mode)
        
        # Save asset data to persistent cache
        cache_manager.data['assets'] = assets_data
        
        if len(assets_data) < 10:
            raise ValueError("Not enough assets loaded")
        
        # Calculate tournament rankings
        print("\n🏆 Calculating tournament rankings...")
        all_rankings = calculate_tournament_rankings(assets_data)
        
        # Get symbols lists for categorization
        stock_symbols = set(massive.get_sp500_symbols())
        etf_symbols = set(massive.get_major_etfs())
        coinbase_crypto = set(coinbase.symbol_to_product.keys())
        cryptocompare_crypto = set(cryptocompare.symbols.keys())
        all_crypto_symbols = coinbase_crypto | cryptocompare_crypto
        
        # Add asset type and name to each ranking
        for asset in all_rankings:
            symbol = asset['symbol']
            if symbol in all_crypto_symbols:
                asset['type'] = 'crypto'
            elif symbol in etf_symbols:
                asset['type'] = 'etf'
            elif symbol in stock_symbols:
                asset['type'] = 'stock'
            else:
                asset['type'] = 'stock'  # Default to stock
            
            # Add asset name
            asset['name'] = name_lookup.get_name(symbol, asset['type'], config.MASSIVE_API_KEY)
        
        # Identify crypto assets for crypto explorer
        crypto_rankings = [
            asset for asset in all_rankings 
            if asset.get('type') == 'crypto'
        ]
        
        # Get top 20 crypto for big board
        top_20_crypto = crypto_rankings[:config.CRYPTO_TOP_FOR_BIGBOARD]
        top_20_crypto_symbols = [asset['symbol'] for asset in top_20_crypto]
        
        # Create big board (stocks + ETFs + top 20 crypto)
        big_board = [
            asset for asset in all_rankings
            if asset.get('type') != 'crypto' or  # Not crypto
               asset['symbol'] in top_20_crypto_symbols  # Or top 20 crypto
        ]
        
        # Update cache and save to disk
        cache_manager.update_rankings(big_board, crypto_rankings)
        cache_manager.save()
        
        print("\n✅ Rankings updated successfully!")
        print(f"📊 Total assets: {len(assets_data)} ({cache_manager.data['metadata']['stocks']} stocks, {cache_manager.data['metadata']['etfs']} ETFs, {cache_manager.data['metadata']['crypto']} crypto)")
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
        ip = socket.gethostbyname('api.exchange.coinbase.com')
        results['coinbase_dns'] = f'✓ Resolved to {ip}'
    except Exception as e:
        results['coinbase_dns'] = f'✗ DNS failed: {str(e)}'
    
    # Test HTTP connection
    try:
        response = requests.get('https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-10?apiKey=' + config.MASSIVE_API_KEY, timeout=5)
        results['polygon_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['polygon_http'] = f'✗ HTTP failed: {str(e)}'
    
    try:
        response = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400', timeout=5)
        results['coinbase_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['coinbase_http'] = f'✗ HTTP failed: {str(e)}'
    
    return jsonify(results)

@app.route('/api/cron-update', methods=['GET', 'POST'])
def cron_update():
    """
    Automated update endpoint for cron jobs
    Does FAST incremental updates - recalculates rankings with existing cached data
    """
    try:
        print("\n🤖 CRON: Starting automated update...")
        
        # Get existing cached asset data
        existing_data = cache_manager.get_assets()
        
        if len(existing_data) < 10:
            return jsonify({'error': 'No cached data - run manual update first'}), 503
        
        # Just recalculate rankings with existing data (FAST - ~10 seconds)
        print("🏆 Recalculating tournament rankings...")
        all_rankings = calculate_tournament_rankings(existing_data)
        
        # Get symbols lists for categorization
        stock_symbols = set(massive.get_sp500_symbols())
        etf_symbols = set(massive.get_major_etfs())
        all_crypto_symbols = {'BTC', 'ETH'}  # Just BTC + ETH
        
        # Add asset type and name to each ranking
        for asset in all_rankings:
            symbol = asset['symbol']
            if symbol in all_crypto_symbols:
                asset['type'] = 'crypto'
            elif symbol in etf_symbols:
                asset['type'] = 'etf'
            elif symbol in stock_symbols:
                asset['type'] = 'stock'
            else:
                asset['type'] = 'stock'
            
            # Add asset name
            asset['name'] = name_lookup.get_name(symbol, asset['type'], config.MASSIVE_API_KEY)
        
        # Identify crypto assets
        crypto_rankings = [asset for asset in all_rankings if asset.get('type') == 'crypto']
        
        # Get top 20 crypto
        top_20_crypto = crypto_rankings[:20]
        top_20_crypto_symbols = [asset['symbol'] for asset in top_20_crypto]
        
        # Create big board
        big_board = [
            asset for asset in all_rankings
            if asset.get('type') != 'crypto' or asset['symbol'] in top_20_crypto_symbols
        ]
        
        # Update cache and save
        cache_manager.update_rankings(big_board, crypto_rankings)
        cache_manager.save()
        
        print("🤖 CRON: Update complete!")
        
        return jsonify({
            'message': 'Automated update successful (recalculated with cached data)',
            'timestamp': cache['last_update'],
            'metadata': cache_manager.data['metadata'],
            'note': 'Rankings refreshed - to fetch new price data, use /api/update'
        })
        
    except Exception as e:
        print(f"🤖 CRON: Update failed - {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['GET', 'POST'])
def trigger_update():
    """
    Manually trigger data update
    
    Parameters:
        test=true - Use limited asset set (70 assets, ~2-3 min)
        type=stocks|etfs|crypto - Update only specific asset type
        symbol=BTC - Update single asset
    
    Examples:
        /api/update - Full update (all assets)
        /api/update?test=true - Fast test mode
        /api/update?type=crypto - Update only crypto
        /api/update?symbol=BNB - Add/update just BNB
    """
    # Parse parameters
    test_mode = request.args.get('test', '').lower() == 'true'
    asset_type = request.args.get('type', '').lower() or None
    symbol = request.args.get('symbol', '').upper() or None
    
    # Validate asset_type
    if asset_type and asset_type not in ['stocks', 'etfs', 'crypto']:
        return jsonify({'error': 'Invalid type. Must be: stocks, etfs, or crypto'}), 400
    
    # Execute update
    success = update_rankings(test_mode=test_mode, asset_type=asset_type, symbol=symbol)
    
    if success:
        # Build response message
        if symbol:
            mode_msg = f'Updated {symbol}'
        elif asset_type:
            mode_msg = f'Updated {asset_type}'
        elif test_mode:
            mode_msg = 'Test mode update (limited assets)'
        else:
            mode_msg = 'Full update'
        
        return jsonify({
            'message': f'{mode_msg} successful',
            'timestamp': cache['last_update'],
            'assets': len(cache.get('big_board', [])),
            'metadata': cache_manager.data['metadata']
        })
    else:
        return jsonify({'error': 'Update failed'}), 500

@app.route('/api/grid/<grid_type>', methods=['GET'])
def get_grid(grid_type):
    """
    Calculate grid matchups using tournament algorithm
    Returns TRUE synthetic pair W/L results
    """
    try:
        from tournament import wins_matchup
        
        # Define grid symbols
        grids = {
            'mag7': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA'],
            'indices': ['SPY', 'QQQ', 'DIA', 'GLD', 'SLV', 'IBIT', 'ETHA'],
            'coms': ['GLD', 'SLV', 'USO', 'UNG', 'CORN', 'WEAT', 'SOYB'],
            'crypto': ['BTC', 'ETH']
        }
        
        if grid_type not in grids:
            return jsonify({'error': 'Invalid grid type'}), 400
        
        symbols = grids[grid_type]
        print(f"Processing grid for {grid_type}: {symbols}")
        
        # Get price histories from cache
        assets_data = cache_manager.get_assets()
        print(f"Assets in cache: {list(assets_data.keys())[:10]}...")
        
        # Calculate matchups using tournament algorithm
        matchups = {}
        
        for symbol1 in symbols:
            matchups[symbol1] = {}
            
            for symbol2 in symbols:
                if symbol1 == symbol2:
                    matchups[symbol1][symbol2] = '-'
                    continue
                
                # Get price histories (assets are stored as {symbol: [prices]})
                prices1 = assets_data.get(symbol1, [])
                prices2 = assets_data.get(symbol2, [])
                
                print(f"Comparing {symbol1} ({len(prices1)} prices) vs {symbol2} ({len(prices2)} prices)")
                
                if not prices1 or not prices2:
                    print(f"Missing data: {symbol1}={bool(prices1)}, {symbol2}={bool(prices2)}")
                    matchups[symbol1][symbol2] = 'N/A'
                    continue
                
                if len(prices1) < config.MA_PERIOD or len(prices2) < config.MA_PERIOD:
                    print(f"Insufficient data: {symbol1}={len(prices1)}, {symbol2}={len(prices2)}")
                    matchups[symbol1][symbol2] = 'N/A'
                    continue
                
                # Use tournament algorithm to determine winner
                try:
                    asset1_wins = wins_matchup(prices1, prices2)
                    
                    if asset1_wins:
                        matchups[symbol1][symbol2] = {'result': 'W'}
                    else:
                        matchups[symbol1][symbol2] = {'result': 'L'}
                except Exception as e:
                    print(f"Error comparing {symbol1} vs {symbol2}: {e}")
                    matchups[symbol1][symbol2] = {'result': 'T'}
        
        print(f"Grid calculation complete: {len(matchups)} rows")
        
        return jsonify({
            'grid_type': grid_type,
            'symbols': symbols,
            'matchups': matchups,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"ERROR in grid endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("RATIO - ASSET STRENGTH RANKINGS API")
    print("="*60)
    print(f"Massive API: {'✓ Configured' if config.MASSIVE_API_KEY != 'YOUR_KEY_HERE' else '✗ Not configured'}")
    print(f"Coinbase API: ✓ Ready (~200 crypto)")
    print(f"CryptoCompare API: ✓ Ready (top 50 missing coins)")
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
