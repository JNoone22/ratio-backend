"""
CryptoCompare API Client
Handles cryptocurrencies not available on Coinbase
Free tier: 100,000 calls/month, ~50 calls/minute
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time

class CryptoCompareClient:
    def __init__(self):
        self.base_url = 'https://min-api.cryptocompare.com/data/v2'
        
        # Symbols for top 50 coins NOT on Coinbase
        self.symbols = {
            'BNB': 'BNB',      # Binance Coin - #4 market cap!
            'TRX': 'TRX',      # Tron
            'TON': 'TON',      # Telegram
            'HBAR': 'HBAR',    # Hedera
            'VET': 'VET',      # VeChain
            'FTM': 'FTM',      # Fantom
            'ARB': 'ARB',      # Arbitrum
            'OP': 'OP',        # Optimism
            'PEPE': 'PEPE',    # Pepe
            'WIF': 'WIF',      # dogwifhat
            'BONK': 'BONK',    # Bonk
        }
    
    def get_symbols(self) -> List[str]:
        """Get list of symbols this client handles"""
        return list(self.symbols.keys())
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto
        Returns list of closes, most recent first
        """
        if symbol not in self.symbols:
            raise ValueError(f"Symbol {symbol} not supported by CryptoCompare client")
        
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
            print(f"    Fetching {symbol} from CryptoCompare...")
            response = requests.get(url, params=params, timeout=15)
            print(f"    Response status: {response.status_code}")
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
            
            print(f"    ✓ {symbol}: Got {len(weekly_prices)} weeks")
            
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
