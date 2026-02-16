"""
Stooq.com API Client
Handles forex pairs data
"""
import requests
from datetime import datetime
from typing import List
import io
import csv

class StooqClient:
    def __init__(self):
        self.base_url = 'https://stooq.com/q/d/l'
    
    def get_weekly_data(self, pair: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a forex pair
        
        Args:
            pair: Forex pair symbol (e.g., 'EURUSD', 'GBPUSD')
            weeks: Number of weeks to fetch
        
        Returns:
            List of closing prices, most recent first
        """
        # Stooq uses format like EURUSD (no slash)
        symbol = pair.replace('/', '')
        
        url = f"{self.base_url}/?s={symbol}&i=w"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV data
            csv_data = response.text
            reader = csv.DictReader(io.StringIO(csv_data))
            
            closes = []
            for row in reader:
                if 'Close' in row:
                    try:
                        close_price = float(row['Close'])
                        closes.append(close_price)
                    except (ValueError, KeyError):
                        continue
            
            # Stooq returns oldest first, we want newest first
            closes.reverse()
            
            if len(closes) < weeks:
                raise ValueError(f"Insufficient data: {len(closes)} weeks")
            
            return closes[:weeks]
            
        except Exception as e:
            raise Exception(f"Failed to fetch {pair}: {str(e)}")
    
    def get_forex_pairs(self) -> List[str]:
        """
        Get list of forex pairs to track
        Major currency pairs vs USD
        """
        return [
            'EURUSD',  # Euro
            'GBPUSD',  # British Pound
            'JPYUSD',  # Japanese Yen (inverted - use USDJPY in reality)
            'AUDUSD',  # Australian Dollar
            'NZDUSD',  # New Zealand Dollar
            'CADUSD',  # Canadian Dollar (inverted - use USDCAD in reality)
            'CHFUSD',  # Swiss Franc (inverted - use USDCHF in reality)
        ]
    
    def get_major_forex_pairs(self) -> List[str]:
        """
        Get major forex pairs in correct Stooq format
        All vs USD for consistency
        """
        return [
            'EURUSD',   # Euro/USD
            'GBPUSD',   # Pound/USD
            'USDJPY',   # USD/Yen (standard format)
            'AUDUSD',   # Aussie/USD
            'NZDUSD',   # Kiwi/USD
            'USDCAD',   # USD/Canadian (standard format)
            'USDCHF',   # USD/Swiss (standard format)
        ]

if __name__ == '__main__':
    client = StooqClient()
    print("Testing Stooq forex data...")
    
    try:
        data = client.get_weekly_data('EURUSD', weeks=5)
        print(f"✓ EUR/USD: Got {len(data)} weeks")
        print(f"  Recent prices: {data[:3]}")
    except Exception as e:
        print(f"✗ Error: {e}")
