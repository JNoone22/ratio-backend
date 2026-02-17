"""
CryptoCompare API Client
Handles cryptocurrencies not available on Coinbase
Free tier: 100,000 calls/month, ~50 calls/minute
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time

# Coins CryptoCompare doesn't carry - use CoinGecko as fallback
# Format: {symbol: coingecko_id}
COINGECKO_FALLBACK = {
    'HYPE': 'hyperliquid',
    'LEO':  'leo-token',
    'SUI':  'sui',
    'MNT':  'mantle',
    'TAO':  'bittensor',
    'ASTR': 'astar',
    'POL':  'matic-network',
}

COINGECKO_BASE = 'https://api.coingecko.com/api/v3'


def fetch_from_coingecko(coingecko_id: str, weeks: int = 20) -> List[float]:
    """
    Fetch weekly price data from CoinGecko for a specific coin.
    Only used as fallback for coins CryptoCompare doesn't carry.
    Rate limit: called sparingly, only for ~7 coins.
    """
    days = weeks * 7 + 30
    url = f"{COINGECKO_BASE}/coins/{coingecko_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    prices = data.get('prices', [])
    if not prices:
        raise ValueError(f"No price data from CoinGecko for {coingecko_id}")

    # Sample every 7th day to get weekly closes
    weekly = [prices[i][1] for i in range(0, len(prices), 7)]
    weekly.reverse()  # newest first

    if len(weekly) < weeks:
        raise ValueError(f"Only {len(weekly)} weeks of data from CoinGecko")

    return weekly[:weeks]

class CryptoCompareClient:
    def __init__(self):
        self.base_url = 'https://min-api.cryptocompare.com/data/v2'
        # Free tier: 100,000 calls/month, ~50 calls/minute - MUCH better than CoinGecko!
        
    def get_top_coins(self, limit: int = 200) -> List[str]:
        """
        Get top cryptocurrencies by market cap from CryptoCompare
        """
        try:
            url = 'https://min-api.cryptocompare.com/data/top/mktcapfull'
            params = {
                'limit': min(limit, 100),  # CryptoCompare max is 100 per call
                'tsym': 'USD'
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'Success' and 'Data' in data:
                symbols = [coin['CoinInfo']['Name'] for coin in data['Data']]
                print(f"    ✓ Got {len(symbols)} coins from CryptoCompare API")
            else:
                raise Exception(f"API error: {data.get('Message', 'Unknown error')}")
                
        except Exception as e:
            print(f"    ✗ CryptoCompare API error: {e}")
            print(f"    Using fallback top 100 list...")
            symbols = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'USDC', 'XRP', 'DOGE', 'ADA', 'TRX',
                       'AVAX', 'SHIB', 'TON', 'LINK', 'DOT', 'LTC', 'BCH', 'UNI', 'NEAR',
                       'ICP', 'PEPE', 'HBAR', 'APT', 'FET', 'ETC', 'STX', 'XLM', 'INJ', 'CRO',
                       'RNDR', 'ATOM', 'ARB', 'IMX', 'OP', 'MKR', 'FIL', 'VET', 'RUNE', 'XMR',
                       'ALGO', 'AAVE', 'GRT', 'THETA', 'FTM', 'SAND', 'MANA', 'EOS', 'FLOW', 'XTZ',
                       'AXS', 'EGLD', 'FLOKI', 'CHZ', 'NEO', 'MINA', 'KAVA', 'SNX', 'GALA', 'QNT']
        
        # Coins CryptoCompare misses or mislabels - force include these
        must_include = [
            'HYPE',   # Hyperliquid
            'LEO',    # UNUS SED LEO
            'SUI',    # Sui
            'MNT',    # Mantle
            'TAO',    # Bittensor
            'ASTR',   # Astar (not ASTER)
            'POL',    # Polygon (rebranded from MATIC)
            'CC',     # Canton
        ]
        
        # Remove POLY (wrong symbol) and MATIC (old symbol) if present
        symbols = [s for s in symbols if s not in ['POLY', 'IOTA']]
        
        # Add must-include coins that aren't already in the list
        for coin in must_include:
            if coin not in symbols:
                symbols.append(coin)
        
        print(f"    Final list: {len(symbols)} coins (including forced additions)")
        return symbols[:limit]
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols - deprecated, use get_top_coins instead"""
        return self.get_top_coins(100)
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto.
        Tries CryptoCompare first, falls back to CoinGecko for known missing coins.
        """
        # Check if we should go straight to CoinGecko for this coin
        if symbol in COINGECKO_FALLBACK:
            try:
                print(f"  → {symbol}: Using CoinGecko fallback...")
                time.sleep(15)  # CoinGecko rate limit - wait before each call
                prices = fetch_from_coingecko(COINGECKO_FALLBACK[symbol], weeks)
                print(f"  ✓ {symbol}: Loaded {len(prices)} weeks from CoinGecko")
                return prices
            except Exception as e:
                print(f"  ✗ {symbol}: CoinGecko also failed - {str(e)}")
                raise

        # CryptoCompare uses daily data, we'll convert to weekly
        days = weeks * 7 + 30  # Extra buffer
        
        url = f"{self.base_url}/histoday"
        params = {
            'fsym': symbol,
            'tsym': 'USD',
            'limit': days,
            'toTs': int(datetime.now().timestamp())
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get('Response') == 'Error':
                raise ValueError(f"API Error: {data.get('Message', 'Unknown error')}")
            
            if 'Data' not in data or 'Data' not in data['Data']:
                raise ValueError(f"No data for {symbol}")
            
            # Extract daily closing prices
            daily_data = data['Data']['Data']
            daily_closes = [day['close'] for day in daily_data if day['close'] > 0]
            
            # Convert daily to weekly (take every 7th day)
            weekly_prices = []
            for i in range(0, len(daily_closes), 7):
                if i < len(daily_closes):
                    weekly_prices.append(daily_closes[i])
            
            # Reverse to get most recent first
            weekly_prices.reverse()
            
            # Return first N weeks
            return weekly_prices[:weeks]
            
        except Exception as e:
            print(f"    ✗ {symbol}: ERROR - {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            data = self.get_weekly_data('BNB', weeks=5)
            return len(data) >= 5
        except:
            return False

# Test the client
if __name__ == '__main__':
    client = CryptoCompareClient()
    print("Testing CryptoCompare API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print("✓ CryptoCompare working")
    else:
        print("✗ Connection failed")
