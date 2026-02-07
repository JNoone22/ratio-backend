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
        Top 100 US stocks by market capitalization
        """
        return [
            # Top 10 (Mega cap >$1T)
            'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'BRK.B', 'LLY', 'AVGO',
            
            # 11-20
            'JPM', 'V', 'UNH', 'XOM', 'WMT', 'MA', 'PG', 'JNJ', 'HD', 'ORCL',
            
            # 21-30
            'COST', 'ABBV', 'BAC', 'NFLX', 'CRM', 'CVX', 'AMD', 'MRK', 'KO', 'ADBE',
            
            # 31-40
            'PEP', 'TMO', 'CSCO', 'MCD', 'ACN', 'ABT', 'INTC', 'WFC', 'LIN', 'QCOM',
            
            # 41-50
            'DIS', 'IBM', 'DHR', 'VZ', 'CMCSA', 'TXN', 'NEE', 'AMGN', 'PM', 'COP',
            
            # 51-60
            'RTX', 'INTU', 'UNP', 'HON', 'SPGI', 'LOW', 'GE', 'NKE', 'MS', 'UBER',
            
            # 61-70
            'UPS', 'CAT', 'AXP', 'ELV', 'BA', 'BLK', 'AMAT', 'PLD', 'GS', 'BKNG',
            
            # 71-80
            'GILD', 'DE', 'NOW', 'SYK', 'ADI', 'ISRG', 'SCHW', 'VRTX', 'MDLZ', 'TJX',
            
            # 81-90
            'LMT', 'CI', 'ADP', 'REGN', 'MMC', 'PGR', 'CB', 'C', 'BMY', 'LRCX',
            
            # 91-100
            'MO', 'ETN', 'SO', 'BSX', 'TMUS', 'BDX', 'SBUX', 'AMT', 'EQIX', 'ZTS'
        ]
    
    def get_major_etfs(self) -> List[str]:
        """
        Get major ETF symbols covering all asset classes
        """
        return [
            # Broad Market Equity
            'SPY', 'QQQ', 'DIA', 'IWM', 'VOO', 'VTI', 'IVV', 'VEA', 'IEFA',
            
            # Sector ETFs
            'XLE',   # Energy
            'XLF',   # Financials
            'XLK',   # Technology
            'XLV',   # Healthcare
            'XLI',   # Industrials
            'XLP',   # Consumer Staples
            'XLY',   # Consumer Discretionary
            'XLU',   # Utilities
            'XLB',   # Materials
            'XLRE',  # Real Estate
            'XLC',   # Communication Services
            
            # International
            'EFA', 'EEM', 'VWO', 'IEMG', 'FXI', 'EWJ', 'EWZ', 'EWU', 'EWG', 'INDA',
            
            # Fixed Income
            'TLT', 'AGG', 'LQD', 'HYG', 'TIP', 'BND', 'SHY', 'IEF',
            
            # Commodities
            'GLD',   # Gold
            'SLV',   # Silver
            'USO',   # Oil
            'UNG',   # Natural Gas
            'DBC',   # Broad Commodities
            'CORN',  # Corn
            'WEAT',  # Wheat
            'SOYB',  # Soybeans
            
            # Thematic/Strategy
            'ARKK',  # Innovation
            'XBI',   # Biotech
            'SMH',   # Semiconductors
            'IBB',   # Biotech
            'VNQ',   # REITs
            'GDX',   # Gold Miners
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
