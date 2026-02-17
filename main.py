"""
Ratio - Asset Strength Rankings API
Main Flask application
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import time
import json

import threading
import time
import json

import config
from massive_client import MassiveClient
from coingecko_client import CoinGeckoClient
from cryptocompare_client import CryptoCompareClient
from stooq_client import StooqClient
from cache_manager import CacheManager
from name_lookup import NameLookup
from tournament import calculate_tournament_rankings, format_rankings_summary

app = Flask(__name__)
CORS(app)

# Initialize API clients
massive = MassiveClient(config.MASSIVE_API_KEY)
coingecko = CoinGeckoClient()
cryptocompare = CryptoCompareClient()
stooq = StooqClient()

# Initialize persistent cache and name lookup
cache_manager = CacheManager()
name_lookup = NameLookup()
cache = cache_manager.data  # For backwards compatibility

# Background update status tracking
update_status = {
    'is_running': False,
    'started_at': None,
    'progress': 0,
    'total': 0,
    'current_task': None,
    'completed_at': None,
    'error': None
}
update_lock = threading.Lock()

def fetch_single_asset(symbol: str) -> list:
    """
    Fetch data for a single asset
    Returns: List of weekly prices or None if failed
    """
    print(f"    Fetching {symbol}...")
    
    # Try Binance first (if it's crypto)
    if symbol in binance.get_all_products():
        try:
            return binance.get_weekly_data(symbol, weeks=config.MA_PERIOD)
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
        # Fetch top 100 crypto from CryptoCompare (their API max is 100)
        crypto_limit = min(config.CRYPTO_LIMIT if hasattr(config, 'CRYPTO_LIMIT') else 100, 100)
        
        try:
            symbols = cryptocompare.get_top_coins(limit=crypto_limit)
            print(f"Fetching top {len(symbols)} cryptocurrencies from CryptoCompare...")
        except Exception as e:
            print(f"ERROR getting crypto symbols: {e}")
            symbols = []
        
        if test_mode:
            symbols = symbols[:5]
            print(f"TEST MODE: Limiting to {len(symbols)} crypto")
        
        crypto_loaded = 0
        for i, symbol in enumerate(symbols):
            try:
                # Rate limiting - CryptoCompare allows ~50 calls/min, wait 1.5 sec each
                if i > 0:
                    time.sleep(1.5)
                
                prices = cryptocompare.get_weekly_data(symbol, weeks=config.MA_PERIOD)
                if len(prices) >= config.MA_PERIOD:
                    all_data[symbol] = prices
                    crypto_loaded += 1
                    
                    if crypto_loaded == 1:
                        print(f"  ✓ {symbol}: First crypto loaded!")
                
                # Progress update every 10
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(symbols)} crypto ({crypto_loaded} loaded)...")
            except Exception as e:
                print(f"  ✗ {symbol}: {str(e)}")
                pass
        
        print(f"✓ Loaded {crypto_loaded}/{len(symbols)} cryptocurrencies")
    
    return all_data

def fetch_all_assets(test_mode=False, skip_crypto=False):
    """
    Fetch data for all assets
    
    Args:
        test_mode: If True, use limited asset set for fast iteration
        skip_crypto: If True, skip crypto loading (for fast daily updates)
        
    Returns: Dict of {symbol: [weekly_closes]}
    """
    print("\n" + "="*60)
    print(f"FETCHING ALL ASSET DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if skip_crypto:
        print("⚡ SKIP_CRYPTO MODE: Crypto will not be updated")
    print("="*60)
    
    all_data = {}
    errors = []
    
    # 1. Fetch stocks
    print("\n📊 Fetching stocks...")
    
    # Option: Use S&P 1500 (comprehensive) or just S&P 500
    use_sp1500 = config.USE_SP1500 if hasattr(config, 'USE_SP1500') else True
    
    if use_sp1500:
        print("Using S&P 1500 (complete official list)")
        stock_symbols = massive.get_sp_1500_symbols()
    else:
        print("Using S&P 500 only")
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
    
    # 3. Fetch crypto from CryptoCompare (Top 100 by market cap)
    if skip_crypto:
        print("\n🪙 Cryptocurrency data - SKIPPED (skip_crypto=True)")
        print("  Crypto assets will retain their previous cached values")
    else:
        print("\n🪙 Fetching cryptocurrency data from CryptoCompare...")
        
        # Get top cryptocurrencies by market cap (CryptoCompare max is 100)
        crypto_limit = min(config.CRYPTO_LIMIT if hasattr(config, 'CRYPTO_LIMIT') else 100, 100)
        
        try:
            cryptocompare_symbols = cryptocompare.get_top_coins(limit=crypto_limit)
            print(f"  Got {len(cryptocompare_symbols)} crypto symbols from CryptoCompare")
        except Exception as e:
            print(f"  ✗ ERROR getting symbols: {e}")
            cryptocompare_symbols = []
        
        if test_mode:
            cryptocompare_symbols = cryptocompare_symbols[:5]  # Just 5 in test mode
            print(f"⚡ TEST MODE: Limiting to {len(cryptocompare_symbols)} crypto")
        else:
            if len(cryptocompare_symbols) > 0:
                print(f"Loading top {len(cryptocompare_symbols)} cryptocurrencies by market cap...")
            else:
                print(f"  ✗ No crypto symbols available - skipping crypto")
        
        crypto_loaded = 0
        crypto_failed = 0
        
        for i, symbol in enumerate(cryptocompare_symbols):
            try:
                # Rate limiting - CryptoCompare allows ~50 calls/min, wait 1.5 sec each
                if i > 0:
                    time.sleep(1.5)
                
                prices = cryptocompare.get_weekly_data(symbol, weeks=config.MA_PERIOD)
                if len(prices) >= config.MA_PERIOD:
                    all_data[symbol] = prices
                    crypto_loaded += 1
                    
                    # Print first successful load
                    if crypto_loaded == 1:
                        print(f"  ✓ {symbol}: Successfully loaded {len(prices)} weeks (first crypto loaded!)")
                else:
                    errors.append(f"{symbol}: insufficient data ({len(prices)} weeks)")
                    crypto_failed += 1
                
                # Progress update every 10
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(cryptocompare_symbols)} crypto ({crypto_loaded} loaded, {crypto_failed} failed)...")
                
            except Exception as e:
                # Print all errors so we can see what's failing
                print(f"  ✗ {symbol}: {str(e)}")
                errors.append(f"{symbol}: {str(e)}")
                crypto_failed += 1
        
        print(f"✓ Crypto loading complete: {crypto_loaded} loaded, {crypto_failed} failed out of {len(cryptocompare_symbols)} total")
    
    # Skip CryptoCompare for now (only using BTC + ETH from Binance)
    cryptocompare_symbols = []
    
    print(f"✓ Loaded {len([s for s in binance_symbols if s in all_data]) + len([s for s in cryptocompare_symbols if s in all_data])} cryptocurrencies total")
    
    # 4. Fetch Forex pairs and calculate cross rates
    print("\n💱 Fetching Forex pairs...")
    
    # Base currencies we want to track
    base_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']
    
    # Fetch USD-based pairs from Stooq
    usd_pairs = stooq.get_major_forex_pairs()
    
    if test_mode:
        usd_pairs = usd_pairs[:3]
        base_currencies = base_currencies[:4]
        print(f"⚡ TEST MODE: Limiting to {len(usd_pairs)} forex pairs")
    else:
        print(f"Fetching {len(usd_pairs)} USD-based pairs to calculate cross rates...")
    
    # Fetch USD pair data
    usd_data = {}
    for i, pair in enumerate(usd_pairs):
        try:
            prices = stooq.get_weekly_data(pair, weeks=config.MA_PERIOD)
            if len(prices) >= config.MA_PERIOD:
                usd_data[pair] = prices
            else:
                errors.append(f"{pair}: insufficient data")
        except Exception as e:
            errors.append(f"{pair}: {str(e)}")
    
    print(f"✓ Loaded {len(usd_data)} USD-based pairs")
    
    # Calculate all cross pairs
    print("  Calculating cross rates...")
    
    # Create lookup for USD rates (invert where needed)
    usd_rates = {}
    for week_idx in range(config.MA_PERIOD):
        usd_rates[week_idx] = {}
        
        # USD is always 1.0
        usd_rates[week_idx]['USD'] = 1.0
        
        # EUR, GBP, AUD, NZD are quoted as XXX/USD
        if 'EURUSD' in usd_data:
            usd_rates[week_idx]['EUR'] = usd_data['EURUSD'][week_idx]
        if 'GBPUSD' in usd_data:
            usd_rates[week_idx]['GBP'] = usd_data['GBPUSD'][week_idx]
        if 'AUDUSD' in usd_data:
            usd_rates[week_idx]['AUD'] = usd_data['AUDUSD'][week_idx]
        if 'NZDUSD' in usd_data:
            usd_rates[week_idx]['NZD'] = usd_data['NZDUSD'][week_idx]
        
        # JPY, CAD, CHF are quoted as USD/XXX (need to invert)
        if 'USDJPY' in usd_data:
            usd_rates[week_idx]['JPY'] = 1.0 / usd_data['USDJPY'][week_idx]
        if 'USDCAD' in usd_data:
            usd_rates[week_idx]['CAD'] = 1.0 / usd_data['USDCAD'][week_idx]
        if 'USDCHF' in usd_data:
            usd_rates[week_idx]['CHF'] = 1.0 / usd_data['USDCHF'][week_idx]
    
    # Now calculate all cross pairs
    cross_pair_count = 0
    for base in base_currencies:
        for quote in base_currencies:
            if base == quote:
                continue
            
            # Calculate cross rate: base/quote = (base/USD) / (quote/USD)
            pair_symbol = f"{base}{quote}"
            cross_prices = []
            
            try:
                for week_idx in range(config.MA_PERIOD):
                    if base in usd_rates[week_idx] and quote in usd_rates[week_idx]:
                        cross_rate = usd_rates[week_idx][base] / usd_rates[week_idx][quote]
                        cross_prices.append(cross_rate)
                
                if len(cross_prices) >= config.MA_PERIOD:
                    all_data[pair_symbol] = cross_prices
                    cross_pair_count += 1
                    
            except Exception as e:
                errors.append(f"{pair_symbol}: calculation error - {str(e)}")
    
    print(f"✓ Calculated {cross_pair_count} forex cross pairs from {len(usd_data)} base pairs")
    
    print("\n" + "="*60)
    print(f"TOTAL ASSETS LOADED: {len(all_data)}")
    if errors:
        print(f"Errors: {len(errors)}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
    print("="*60 + "\n")
    
    return all_data

def update_rankings(test_mode=False, asset_type=None, symbol=None, skip_crypto=False):
    """
    Fetch fresh data and calculate rankings
    Updates global cache
    
    Args:
        test_mode: If True, use limited asset set for fast iteration (2-3 min)
        asset_type: If set, only update this type ('stocks', 'etfs', 'crypto')
        symbol: If set, only update this single asset
        skip_crypto: If True, skip crypto loading for faster daily updates
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
            if skip_crypto:
                print(f"\n⚡ FULL UPDATE (SKIP CRYPTO)")
            else:
                print(f"\n⚡ FULL UPDATE")
            assets_data = fetch_all_assets(test_mode=test_mode, skip_crypto=skip_crypto)
            # If skipping crypto, merge in existing crypto data
            if skip_crypto:
                for symbol, data in existing_data.items():
                    # Check if it's a crypto symbol (not in new data)
                    if symbol not in assets_data:
                        assets_data[symbol] = data
        
        # Save asset data to persistent cache
        cache_manager.data['assets'] = assets_data
        
        if len(assets_data) < 10:
            raise ValueError("Not enough assets loaded")
        
        # Calculate tournament rankings
        print("\n🏆 Calculating tournament rankings...")
        all_rankings = calculate_tournament_rankings(assets_data)
        
        # Get symbols lists for categorization
        sp500_symbols_set = set(massive.get_sp500_symbols())
        sp1500_symbols = set(massive.get_sp_1500_symbols())
        etf_symbols = set(massive.get_major_etfs())
        
        # Forex pairs are any symbol that looks like XXXYYY (6 letters, currency codes)
        forex_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF'}
        
        # Crypto symbols - any symbol in all_data that's not stock/etf/forex
        # We'll detect crypto by elimination after checking other types
        
        # Add asset type, S&P 500 flag, and name to each ranking
        for asset in all_rankings:
            symbol = asset['symbol']
            
            # Mark if in S&P 500
            asset['sp500'] = symbol in sp500_symbols_set
            
            # Detect forex pairs (6 chars, both halves are currency codes)
            is_forex = (
                len(symbol) == 6 and 
                symbol[:3] in forex_currencies and 
                symbol[3:] in forex_currencies
            )
            
            if is_forex:
                asset['type'] = 'forex'
            elif symbol in etf_symbols:
                asset['type'] = 'etf'
            elif symbol in sp1500_symbols:
                asset['type'] = 'stock'
            else:
                # Everything else is crypto
                asset['type'] = 'crypto'
            
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

def background_update_task(test_mode=False, asset_type=None, symbol=None, skip_crypto=False):
    """
    Background task that runs the actual data loading
    Updates global update_status as it progresses
    """
    global update_status
    
    try:
        with update_lock:
            update_status['is_running'] = True
            update_status['started_at'] = datetime.now().isoformat()
            update_status['progress'] = 0
            update_status['current_task'] = 'Starting update...'
            update_status['error'] = None
        
        # Run the actual update
        update_rankings(test_mode=test_mode, asset_type=asset_type, symbol=symbol, skip_crypto=skip_crypto)
        
        with update_lock:
            update_status['is_running'] = False
            update_status['completed_at'] = datetime.now().isoformat()
            update_status['current_task'] = 'Complete'
            update_status['progress'] = 100
            
        print("✅ Background update completed successfully")
        
    except Exception as e:
        with update_lock:
            update_status['is_running'] = False
            update_status['error'] = str(e)
            update_status['current_task'] = f'Failed: {str(e)}'
        
        print(f"❌ Background update failed: {e}")

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

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache data (use if stuck or corrupted)"""
    try:
        cache_manager.clear()
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """Get detailed cache status"""
    import os
    assets_data = cache_manager.get_assets()
    big_board = cache.get('big_board') or []
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'last_update': cache.get('last_update'),
        'cache_file_exists': os.path.exists(cache_manager.cache_file),
        'assets_in_cache': len(assets_data),
        'big_board_rankings': len(big_board),
        'symbols_sample': list(assets_data.keys())[:10] if assets_data else []
    })

@app.route('/api/test/market-cap', methods=['GET'])
def test_market_cap_filter():
    """
    DRY RUN: Test how many stocks would be loaded with market cap filter
    Does NOT actually load data or update cache
    
    Query params:
        min_cap: Minimum market cap in billions (default: 2.0)
        max_results: Maximum stocks to return (default: 2000)
    
    Example: /api/test/market-cap?min_cap=5.0&max_results=1000
    """
    try:
        min_cap = request.args.get('min_cap', 2.0, type=float)
        max_results = request.args.get('max_results', 2000, type=int)
        
        print(f"🧪 DRY RUN: Testing market cap filter (min=${min_cap}B, max={max_results})")
        
        # Get symbols matching criteria
        symbols = massive.get_stocks_by_market_cap(
            min_market_cap_billions=min_cap,
            max_results=max_results
        )
        
        # Calculate estimated tournament time
        matchup_count = len(symbols) * (len(symbols) - 1) / 2
        estimated_minutes = (matchup_count / 150_000) * 5  # ~5 min per 150k matchups
        
        return jsonify({
            'dry_run': True,
            'parameters': {
                'min_market_cap_billions': min_cap,
                'max_results': max_results
            },
            'results': {
                'stock_count': len(symbols),
                'sample_symbols': symbols[:20],
                'total_matchups': int(matchup_count),
                'estimated_load_time_minutes': round(estimated_minutes, 1),
                'will_timeout': estimated_minutes > 25,
                'recommendation': 'SAFE' if estimated_minutes < 20 else 'RISKY' if estimated_minutes < 30 else 'WILL FAIL'
            },
            'note': 'This is a dry run. No data was loaded. Use /api/update to actually load.'
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'dry_run': True
        }), 500

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
        ip = socket.gethostbyname('api.exchange.binance.com')
        results['binance_dns'] = f'✓ Resolved to {ip}'
    except Exception as e:
        results['binance_dns'] = f'✗ DNS failed: {str(e)}'
    
    # Test HTTP connection
    try:
        response = requests.get('https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-10?apiKey=' + config.MASSIVE_API_KEY, timeout=5)
        results['polygon_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['polygon_http'] = f'✗ HTTP failed: {str(e)}'
    
    try:
        response = requests.get('https://api.exchange.binance.com/products/BTC-USD/candles?granularity=86400', timeout=5)
        results['binance_http'] = f'✓ HTTP {response.status_code}'
    except Exception as e:
        results['binance_http'] = f'✗ HTTP failed: {str(e)}'
    
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
    Trigger background data update (returns immediately)
    
    Parameters:
        test=true - Use limited asset set (70 assets, ~2-3 min)
        type=stocks|etfs|crypto - Update only specific asset type
        symbol=BTC - Update single asset
        skip_crypto=true - Skip crypto loading for faster daily updates (~13 min)
    
    Examples:
        /api/update - Full update (all assets including crypto, ~40 min)
        /api/update?skip_crypto=true - Daily update without crypto (~13 min)
        /api/update?type=crypto - Update only crypto (~20 min)
        /api/update?test=true - Fast test mode
    """
    global update_status
    
    # Check if already running
    with update_lock:
        if update_status['is_running']:
            return jsonify({
                'status': 'already_running',
                'message': 'Update already in progress',
                'started_at': update_status['started_at'],
                'current_task': update_status['current_task'],
                'check_status': '/api/update/status'
            }), 409
    
    # Parse parameters
    test_mode = request.args.get('test', '').lower() == 'true'
    asset_type = request.args.get('type', '').lower() or None
    symbol = request.args.get('symbol', '').upper() or None
    skip_crypto = request.args.get('skip_crypto', '').lower() == 'true'
    
    # Validate asset_type
    if asset_type and asset_type not in ['stocks', 'etfs', 'crypto']:
        return jsonify({'error': 'Invalid type. Must be: stocks, etfs, or crypto'}), 400
    
    # Start background thread
    thread = threading.Thread(
        target=background_update_task,
        args=(test_mode, asset_type, symbol, skip_crypto),
        daemon=True
    )
    thread.start()
    
    # Build response message
    if symbol:
        mode_msg = f'Updating {symbol}'
    elif asset_type:
        mode_msg = f'Updating {asset_type}'
    elif test_mode:
        mode_msg = 'Test mode update (limited assets)'
    else:
        mode_msg = 'Full update (all assets - this may take 30-45 minutes)'
    
    return jsonify({
        'status': 'started',
        'message': f'{mode_msg} started in background',
        'started_at': datetime.now().isoformat(),
        'check_status': '/api/update/status',
        'note': 'This endpoint returns immediately. Check /api/update/status to monitor progress.'
    })

@app.route('/api/update/status', methods=['GET'])
def update_progress():
    """
    Check status of background update
    """
    with update_lock:
        status_copy = update_status.copy()
    
    # Add helpful messages
    if status_copy['is_running']:
        status_copy['message'] = 'Update in progress - check back in a few minutes'
    elif status_copy['error']:
        status_copy['message'] = f"Update failed: {status_copy['error']}"
    elif status_copy['completed_at']:
        status_copy['message'] = 'Update completed successfully'
    else:
        status_copy['message'] = 'No update running'
    
    return jsonify(status_copy)

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
            'commodity': ['GLD', 'SLV', 'USO', 'UNG', 'CORN', 'WEAT', 'SOYB'],
            'crypto': ['BTC', 'ETH'],
            'forex': ['USDEUR', 'USDGBP', 'USDJPY', 'USDAUD', 'USDNZD', 'USDCAD', 'USDCHF', 'EURUSD']  # 8 major currencies
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
    print(f"Binance API: ✓ Ready (~200 crypto)")
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
