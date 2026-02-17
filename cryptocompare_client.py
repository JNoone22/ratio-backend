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
                print(f"    ✓ Got {len(symbols)} coins from CryptoCompare")
                return symbols
            else:
                raise Exception(f"API error: {data.get('Message', 'Unknown error')}")
                
        except Exception as e:
            print(f"    ✗ CryptoCompare API error: {e}")
            print(f"    Using fallback top 100 list...")
            
            # Hardcoded top 100 (fallback)
            return ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'USDC', 'XRP', 'DOGE', 'ADA', 'TRX',
                    'AVAX', 'SHIB', 'TON', 'LINK', 'DOT', 'MATIC', 'LTC', 'BCH', 'UNI', 'NEAR',
                    'ICP', 'PEPE', 'HBAR', 'APT', 'FET', 'ETC', 'STX', 'XLM', 'INJ', 'CRO',
                    'RNDR', 'ATOM', 'ARB', 'IMX', 'OP', 'MKR', 'FIL', 'VET', 'RUNE', 'XMR',
                    'ALGO', 'AAVE', 'GRT', 'THETA', 'FTM', 'SAND', 'MANA', 'EOS', 'FLOW', 'XTZ',
                    'AXS', 'EGLD', 'FLOKI', 'CHZ', 'NEO', 'MINA', 'KAVA', 'SNX', 'GALA', 'QNT',
                    'CFX', 'FLR', 'IOTA', 'ZEC', 'DASH', 'COMP', 'LDO', '1INCH', 'ENJ', 'CAKE',
                    'BAT', 'ZIL', 'WAVES', 'CRV', 'YFI', 'GMT', 'HNT', 'SUSHI', 'OMG', 'ANT',
                    'AUDIO', 'BAL', 'BAND', 'BNT', 'CELR', 'CHR', 'COTI', 'CVX', 'DYDX', 'GNO',
                    'ICX', 'KLAY', 'KNC', 'KSM', 'LQTY', 'MASK', 'OXT', 'PERP', 'POLY', 'RAY'][:limit]
    
    def get_symbols(self) -> List[str]:
        """Get list of available symbols - deprecated, use get_top_coins instead"""
        return self.get_top_coins(100)
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto
        Returns list of closes, most recent first
        Works for ANY cryptocurrency symbol
        """
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
