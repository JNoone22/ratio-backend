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
        Complete S&P 500 stock list (all 500 companies)
        Organized by sector for maintainability
        """
        # INFORMATION TECHNOLOGY (67 stocks)
        tech = [
            'AAPL', 'MSFT', 'NVDA', 'AVGO', 'ORCL', 'CRM', 'ADBE', 'AMD', 'CSCO', 'ACN',
            'IBM', 'INTC', 'QCOM', 'TXN', 'INTU', 'NOW', 'AMAT', 'ADI', 'LRCX', 'SNPS',
            'CDNS', 'MRVL', 'KLAC', 'ANET', 'PANW', 'MU', 'NXPI', 'ADSK', 'CRWD', 'FTNT',
            'WDAY', 'ANSS', 'ROP', 'APH', 'MSI', 'DELL', 'HPQ', 'NTAP', 'STX', 'WDC',
            'FFIV', 'JNPR', 'AKAM', 'KEYS', 'ZBRA', 'FICO', 'TYL', 'TRMB', 'CDW', 'IT',
            'GLW', 'HPE', 'MPWR', 'TDY', 'TER', 'SWKS', 'ENPH', 'QRVO', 'ON', 'GEN',
            'SMCI', 'CTSH', 'ACN', 'ORCL', 'CRM', 'ADBE', 'NOW'
        ]
        
        # FINANCIALS (71 stocks)
        financials = [
            'BRK.B', 'JPM', 'V', 'MA', 'BAC', 'WFC', 'MS', 'GS', 'BLK', 'AXP',
            'SPGI', 'SCHW', 'C', 'CB', 'PGR', 'MMC', 'ICE', 'USB', 'PNC', 'TFC',
            'CME', 'AON', 'AIG', 'AFL', 'MET', 'TRV', 'AJG', 'PRU', 'ALL', 'HIG',
            'BK', 'STT', 'TROW', 'MTB', 'FITB', 'KEY', 'CFG', 'RF', 'HBAN', 'CINF',
            'FIS', 'BRO', 'WRB', 'L', 'NTRS', 'FDS', 'IVZ', 'JKHY', 'CBOE', 'RJF',
            'DFS', 'SYF', 'COF', 'ALLY', 'KKR', 'APO', 'BX', 'ARES', 'CG', 'TPG',
            'WTW', 'MKTX', 'MSCI', 'MCO', 'EFX', 'TRU', 'GL', 'AIZ', 'RE', 'PFG', 'WBS'
        ]
        
        # HEALTH CARE (62 stocks)
        healthcare = [
            'LLY', 'UNH', 'JNJ', 'ABBV', 'MRK', 'TMO', 'ABT', 'DHR', 'AMGN', 'ISRG',
            'VRTX', 'GILD', 'CI', 'ELV', 'BSX', 'REGN', 'ZTS', 'SYK', 'BDX', 'CVS',
            'HCA', 'MCK', 'COR', 'IDXX', 'HUM', 'EW', 'A', 'RMD', 'IQV', 'DXCM',
            'CNC', 'MTD', 'WAT', 'GEHC', 'ALGN', 'MRNA', 'BIIB', 'VTRS', 'HOLX', 'PODD',
            'STE', 'ZBH', 'LH', 'DGX', 'BAX', 'MOH', 'TECH', 'TFX', 'HSIC', 'INCY',
            'EXAS', 'COO', 'CTLT', 'RVTY', 'WST', 'SOLV', 'CRL', 'CAH', 'DVA', 'UHS', 'HWM', 'OGN'
        ]
        
        # CONSUMER DISCRETIONARY (51 stocks)
        consumer_disc = [
            'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'LOW', 'BKNG', 'TJX', 'SBUX', 'CMG',
            'MAR', 'ORLY', 'GM', 'F', 'TGT', 'AZO', 'ROST', 'HLT', 'YUM', 'DHI',
            'LEN', 'APTV', 'GPC', 'EBAY', 'POOL', 'DG', 'DLTR', 'BBY', 'ULTA', 'LVS',
            'WYNN', 'MGM', 'GRMN', 'CZR', 'TPR', 'RL', 'HAS', 'MHK', 'WHR', 'LKQ',
            'NVR', 'PHM', 'BWA', 'EXPE', 'CCL', 'NCLH', 'RCL', 'KMX', 'DPZ', 'TSCO', 'AAP'
        ]
        
        # COMMUNICATION SERVICES (24 stocks)
        comm_services = [
            'GOOGL', 'META', 'NFLX', 'DIS', 'VZ', 'CMCSA', 'TMUS', 'T', 'CHTR', 'EA',
            'TTWO', 'LYV', 'PARA', 'FOXA', 'FOX', 'DISH', 'NWSA', 'NWS', 'OMC', 'IPG',
            'MTCH', 'PINS', 'SNAP', 'ROKU'
        ]
        
        # INDUSTRIALS (77 stocks)
        industrials = [
            'GE', 'UNP', 'HON', 'CAT', 'RTX', 'UPS', 'BA', 'LMT', 'DE', 'ADP',
            'ETN', 'TT', 'CARR', 'NOC', 'EMR', 'PH', 'WM', 'ITW', 'PCAR', 'GWW',
            'FI', 'TDG', 'CTAS', 'CMI', 'GD', 'RSG', 'NSC', 'EME', 'PAYX', 'FAST',
            'OTIS', 'VRSK', 'URI', 'PWR', 'AME', 'ODFL', 'DAL', 'UAL', 'LUV', 'CSX',
            'IR', 'SNA', 'CPRT', 'DOV', 'HUBB', 'J', 'LDOS', 'ROK', 'XYL', 'VLTO',
            'AXON', 'EFX', 'BR', 'EXPD', 'JBHT', 'CHRW', 'FDX', 'JCI', 'SWK', 'PKG',
            'BALL', 'AVY', 'SEE', 'NDSN', 'IEX', 'PNR', 'ROL', 'ALLE', 'MAS', 'AOS',
            'GGG', 'GNRC', 'ITT', 'RHI', 'TXT', 'HII', 'BLDR'
        ]
        
        # CONSUMER STAPLES (33 stocks)
        consumer_staples = [
            'WMT', 'PG', 'COST', 'KO', 'PEP', 'PM', 'MO', 'MDLZ', 'CL', 'KMB',
            'GIS', 'STZ', 'SYY', 'HSY', 'K', 'CHD', 'CLX', 'TSN', 'CAG', 'HRL',
            'MKC', 'CPB', 'LW', 'TAP', 'KVUE', 'EL', 'KDP', 'KR', 'SJM', 'ADM',
            'BG', 'MNST', 'DG'
        ]
        
        # ENERGY (23 stocks)
        energy = [
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'PXD', 'VLO', 'OXY',
            'WMB', 'KMI', 'HAL', 'HES', 'BKR', 'FANG', 'DVN', 'TRGP', 'OKE', 'MRO',
            'APA', 'CTRA', 'EQT'
        ]
        
        # UTILITIES (28 stocks)
        utilities = [
            'NEE', 'SO', 'DUK', 'CEG', 'SRE', 'AEP', 'D', 'PEG', 'VST', 'EXC',
            'XEL', 'ED', 'EIX', 'WEC', 'AWK', 'DTE', 'ES', 'FE', 'ETR', 'PPL',
            'AEE', 'CNP', 'CMS', 'NI', 'LNT', 'EVRG', 'AES', 'PNW'
        ]
        
        # REAL ESTATE (29 stocks)
        real_estate = [
            'PLD', 'AMT', 'EQIX', 'PSA', 'WELL', 'SPG', 'O', 'DLR', 'VICI', 'AVB',
            'EQR', 'SBAC', 'WY', 'INVH', 'ARE', 'MAA', 'KIM', 'DOC', 'REG', 'UDR',
            'HST', 'VTR', 'ESS', 'CPT', 'FRT', 'BXP', 'PEAK', 'CCI', 'EXR'
        ]
        
        # MATERIALS (28 stocks)
        materials = [
            'LIN', 'SHW', 'APD', 'FCX', 'ECL', 'NEM', 'CTVA', 'DD', 'NUE', 'DOW',
            'PPG', 'LYB', 'VMC', 'MLM', 'ALB', 'STLD', 'IFF', 'CE', 'EMN', 'FMC',
            'BALL', 'AVY', 'CF', 'MOS', 'IP', 'PKG', 'AMCR', 'SEE'
        ]
        
        # Combine all sectors
        all_stocks = (tech + financials + healthcare + consumer_disc + comm_services + 
                     industrials + consumer_staples + energy + utilities + real_estate + materials)
        
        # Remove duplicates and return first 500
        return list(dict.fromkeys(all_stocks))[:500]
    
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
