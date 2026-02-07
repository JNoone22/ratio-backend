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
        start_date = end_date - timedelta(weeks=weeks + 10)
        
        url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/week/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        
        params = {
            'adjusted': 'true',  # Account for splits/dividends
            'sort': 'desc',  # Most recent first
            'limit': weeks + 10,
            'apiKey': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'results' not in data or not data['results']:
                raise ValueError(f"No data for {symbol}")
            
            # Extract closing prices
            closes = [bar['c'] for bar in data['results']]
            
            # Return most recent N weeks
            return closes[:weeks]
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            raise
    
    def get_sp500_symbols(self) -> List[str]:
        """
        Get S&P 500 stock symbols
        For now, using a hardcoded list of major stocks
        In production, would fetch from a maintained list
        """
        # Top stocks by market cap (simplified for MVP)
        # In production, fetch full S&P 500 from a reliable source
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B',
            'UNH', 'JNJ', 'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'ABBV',
            'PFE', 'AVGO', 'COST', 'DIS', 'MRK', 'KO', 'ADBE', 'PEP', 'TMO',
            'CSCO', 'ACN', 'LLY', 'NKE', 'ABT', 'ORCL', 'WMT', 'CRM', 'VZ',
            'NFLX', 'DHR', 'INTC', 'CMCSA', 'TXN', 'AMD', 'QCOM', 'NEE', 'PM',
            'UPS', 'RTX', 'HON', 'INTU', 'UNP', 'IBM', 'SPGI', 'LOW', 'CAT',
            'BA', 'AMGN', 'GS', 'SBUX', 'BLK', 'AXP', 'DE', 'MDLZ', 'GILD',
            'BKNG', 'ADI', 'TGT', 'MMC', 'CVS', 'LMT', 'SYK', 'ISRG', 'CI',
            'MO', 'ZTS', 'VRTX', 'CB', 'PLD', 'DUK', 'SO', 'BDX', 'REGN',
            'TJX', 'SCHW', 'BSX', 'ATVI', 'BMY', 'USB', 'TMUS', 'CL', 'MMM',
            'SLB', 'GE', 'EOG', 'NOC', 'FDX', 'APD', 'MU', 'CSX', 'FISV'
            # ... would extend to full 500
        ]
    
    def get_major_etfs(self) -> List[str]:
        """
        Get major ETF symbols
        """
        return [
            # Broad Market
            'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'ARKK',
            # Sectors
            'XLE', 'XLF', 'XLK', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLB', 'XLRE',
            # International
            'EFA', 'EEM', 'VWO', 'FXI', 'EWJ', 'EWZ', 'EWU', 'EWG',
            # Bonds
            'TLT', 'AGG', 'LQD', 'HYG', 'TIP', 'BND',
            # Commodities (included here)
            'GLD', 'SLV', 'USO', 'UNG', 'PPLT', 'PALL', 'CORN', 'WEAT', 'SOYB',
            'JO', 'CANE', 'CPER', 'DBC', 'GSG', 'PDBC', 'GCC', 'UGA'
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
