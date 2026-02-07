"""
CoinCap API Client
Handles cryptocurrency data (free, unlimited)
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import config

class CoinCapClient:
    def __init__(self):
        self.base_url = config.COINCAP_BASE_URL
        
        # CoinCap ID mapping for major crypto
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binance-coin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'AVAX': 'avalanche',
            'DOT': 'polkadot',
            'MATIC': 'polygon',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FTM': 'fantom',
            'NEAR': 'near-protocol',
            'HBAR': 'hedera-hashgraph',
            'ICP': 'internet-computer',
            'APT': 'aptos',
            'ARB': 'arbitrum',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'PEPE': 'pepe',
            'WIF': 'dogwifhat',
            'BONK': 'bonk',
        }
    
    def get_top_crypto_symbols(self, limit: int = 200) -> List[str]:
        """
        Get top N crypto symbols by market cap
        """
        # For testing, just return top 20
        return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOT', 
                'MATIC', 'LINK', 'UNI', 'ATOM', 'DOGE', 'SHIB', 'ALGO',
                'VET', 'FTM', 'NEAR', 'HBAR', 'ICP']
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto
        Returns list of closes, most recent first
        """
        # Get CoinCap ID
        coin_id = self.symbol_to_id.get(symbol, symbol.lower())
        
        # Calculate time range
        end_time = int(datetime.now().timestamp() * 1000)
        days = weeks * 7 + 30  # Extra buffer
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        url = f"{self.base_url}/assets/{coin_id}/history"
        params = {
            'interval': 'd1',  # Daily interval
            'start': start_time,
            'end': end_time
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data or not data['data']:
                raise ValueError(f"No data for {symbol}")
            
            # Extract daily prices
            daily_prices = [float(item['priceUsd']) for item in data['data']]
            
            # Convert daily to weekly (take every 7th day)
            weekly_prices = []
            for i in range(0, len(daily_prices), 7):
                if i < len(daily_prices):
                    weekly_prices.append(daily_prices[i])
            
            # Reverse to get most recent first
            weekly_prices.reverse()
            
            # Return first N weeks
            return weekly_prices[:weeks]
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
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
    client = CoinCapClient()
    print("Testing CoinCap API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print("✓ CoinCap working")
    else:
        print("✗ Connection failed")
