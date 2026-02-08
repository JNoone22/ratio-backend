"""
Coinbase Public API Client
Handles cryptocurrency data (free, generous rate limits)
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import config

class CoinbaseClient:
    def __init__(self):
        self.base_url = 'https://api.coinbase.com/v2'
        self.exchange_url = 'https://api.exchange.coinbase.com'
        
        # Coinbase product IDs for major crypto
        self.symbol_to_product = {
            'BTC': 'BTC-USD',
            'ETH': 'ETH-USD',
            'SOL': 'SOL-USD',
            'XRP': 'XRP-USD',
            'ADA': 'ADA-USD',
            'AVAX': 'AVAX-USD',
            'DOT': 'DOT-USD',
            'MATIC': 'MATIC-USD',
            'LINK': 'LINK-USD',
            'UNI': 'UNI-USD',
            'ATOM': 'ATOM-USD',
            'ALGO': 'ALGO-USD',
            'NEAR': 'NEAR-USD',
            'ICP': 'ICP-USD',
            'APT': 'APT-USD',
            'DOGE': 'DOGE-USD',
            'SHIB': 'SHIB-USD',
        }
    
    def get_top_crypto_symbols(self, limit: int = 200) -> List[str]:
        """
        Get top crypto symbols available on Coinbase
        """
        return list(self.symbol_to_product.keys())
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto
        Returns list of closes, most recent first
        """
        product_id = self.symbol_to_product.get(symbol)
        if not product_id:
            raise ValueError(f"Unknown crypto symbol: {symbol}")
        
        # Use Coinbase Exchange API for historical data
        # Get daily candles, then convert to weekly
        url = f"{self.exchange_url}/products/{product_id}/candles"
        
        # Calculate time range (get extra days for buffer)
        days = weeks * 7 + 30
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        params = {
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'granularity': 86400  # 1 day in seconds
        }
        
        try:
            print(f"    Fetching {symbol} from Coinbase...")
            response = requests.get(url, params=params, timeout=15)
            print(f"    Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            
            if not data or len(data) == 0:
                raise ValueError(f"No data for {symbol}")
            
            # Coinbase returns: [time, low, high, open, close, volume]
            # Sort by time (oldest first)
            data.sort(key=lambda x: x[0])
            
            # Extract closing prices
            daily_closes = [candle[4] for candle in data]
            
            # Convert daily to weekly (take every 7th day)
            weekly_prices = []
            for i in range(0, len(daily_closes), 7):
                if i < len(daily_closes):
                    weekly_prices.append(daily_closes[i])
            
            # Reverse to get most recent first
            weekly_prices.reverse()
            
            print(f"    ✓ {symbol}: Got {len(weekly_prices)} weeks")
            
            # Return first N weeks
            return weekly_prices[:weeks]
            
        except Exception as e:
            print(f"    ✗ {symbol}: ERROR - {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test API connection
        """
        try:
            data = self.get_weekly_data('BTC', weeks=5)
            return len(data) >= 5
        except:
            return False

# Test the client
if __name__ == '__main__':
    client = CoinbaseClient()
    print("Testing Coinbase API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print("✓ Coinbase working")
    else:
        print("✗ Connection failed")
