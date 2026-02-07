"""
Massive.com (formerly Polygon.io) API Client
Handles stocks, ETFs, and commodity ETFs
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time
import config

class MassiveClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = config.MASSIVE_BASE_URL
        
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a symbol
        Returns list of closes, most recent first
        """
        # Calculate date range (need extra weeks as buffer)
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks + 30)  # Increased buffer from 10 to 30
        
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/week/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        params = {
            'adjusted': 'true',  # Account for splits/dividends
            'sort': 'desc',  # Most recent first
            'limit': 50,  # Increased from weeks + 10
            'apiKey': self.api_key
        }
        
        try:
            print(f"    Fetching {symbol}: {url}")
            
            all_closes = []
            current_url = url
            params_copy = params.copy()
            
            # Fetch with pagination
            while current_url and len(all_closes) < weeks:
                response = requests.get(current_url, params=params_copy, timeout=10)
                print(f"    Response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                print(f"    Response keys: {data.keys()}")
                
                if 'results' not in data or not data['results']:
                    print(f"    Response data: {data}")
                    break
                
                # Extract closing prices from this page
                closes = [bar['c'] for bar in data['results']]
                all_closes.extend(closes)
                print(f"    Got {len(closes)} weeks (total: {len(all_closes)})")
                
                # Check for next page
                if 'next_url' in data and data['next_url'] and len(all_closes) < weeks:
                    current_url = data['next_url']
                    params_copy = {'apiKey': self.api_key}  # next_url already has other params
                    print(f"    Fetching next page...")
                else:
                    break
            
            if len(all_closes) < weeks:
                print(f"    ✗ {symbol}: only {len(all_closes)} weeks total")
                raise ValueError(f"Insufficient data: {len(all_closes)} weeks")
            
            print(f"    ✓ {symbol}: Got {len(all_closes)} weeks total")
            
            # Return most recent N weeks
            return all_closes[:weeks]
            
        except Exception as e:
            print(f"    ✗ {symbol}: ERROR - {str(e)}")
            raise
    
    def get_sp500_symbols(self) -> List[str]:
        """
        Get S&P 500 stock symbols
        For now, using a hardcoded list of major stocks
        In production, would fetch from a maintained list
        """
        # Top 20 most liquid stocks for testing
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
            'UNH', 'JPM', 'V', 'XOM', 'HD', 'PG', 'MA', 
            'COST', 'ABBV', 'AVGO', 'DIS', 'NFLX', 'AMD'
        ]
    
    def get_major_etfs(self) -> List[str]:
        """
        Get major ETF symbols
        """
        return [
            # Broad Market
            'SPY', 'QQQ', 'DIA', 'IWM',
            # Sectors
            'XLE', 'XLF', 'XLK', 'XLV',
            # Commodities
            'GLD', 'SLV', 'USO', 'UNG'
        ]
    
    def test_connection(self) -> bool:
        """
        Test API connection with a simple request
        """
        try:
            data = self.get_weekly_data('AAPL', weeks=5)
            return len(data) >= 5
        except:
            return False

# Test the client
if __name__ == '__main__':
    client = MassiveClient(config.MASSIVE_API_KEY)
    print("Testing Massive API connection...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        print(f"✓ API Key working")
    else:
        print("✗ Connection failed")
