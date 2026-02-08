"""
CoinGecko API Client
Handles cryptocurrency data (free tier)
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import config

class CoinGeckoClient:
    def __init__(self):
        self.base_url = 'https://api.coingecko.com/api/v3'
        
        # CoinGecko ID mapping for major crypto
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'AVAX': 'avalanche-2',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'ALGO': 'algorand',
            'VET': 'vechain',
            'FTM': 'fantom',
            'NEAR': 'near',
            'HBAR': 'hedera-hashgraph',
            'ICP': 'internet-computer',
            'APT': 'aptos',
            'ARB': 'arbitrum',
            'DOGE': 'dogecoin',
            'SHIB': 'shiba-inu',
            'PEPE': 'pepe',
        }
    
    def get_top_crypto_symbols(self, limit: int = 200) -> List[str]:
        """
        Get top N crypto symbols by market cap
        """
        # For now, return known list
        return list(self.symbol_to_id.keys())
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a crypto
        Returns list of closes, most recent first
        """
        # Get CoinGecko ID
        coin_id = self.symbol_to_id.get(symbol)
        if not coin_id:
            raise ValueError(f"Unknown crypto symbol: {symbol}")
        
        # Calculate days needed
        days = weeks * 7 + 10  # Extra buffer
        
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        try:
            print(f"    Fetching {symbol} from CoinGecko...")
            response = requests.get(url, params=params, timeout=15)
            print(f"    Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            
            if 'prices' not in data or not data['prices']:
                raise ValueError(f"No data for {symbol}")
            
            # Extract daily prices [timestamp, price]
            daily_prices = [price[1] for price in data['prices']]
            
            # Convert daily to weekly (take every 7th day)
            weekly_prices = []
            for i in range(0, len(daily_prices), 7):
                if i < len(daily_prices):
                    weekly_prices.append(daily_prices[i])
            
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
    client = CoinGeckoClient()
    print("Testing CoinGecko API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print("✓ CoinGecko working")
    else:
        print("✗ Connection failed")
