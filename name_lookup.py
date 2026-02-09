"""
Asset Name Lookup
Fetches and caches asset names from APIs
"""
import requests
import json
import os

class NameLookup:
    def __init__(self, cache_file='asset_names.json'):
        self.cache_file = cache_file
        self.names = {}
        self.load()
    
    def load(self):
        """Load cached names from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.names = json.load(f)
                print(f"✓ Loaded {len(self.names)} asset names from cache")
            except:
                pass
    
    def save(self):
        """Save names to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.names, f, indent=2)
        except:
            pass
    
    def get_name(self, symbol: str, asset_type: str = None, api_key: str = None) -> str:
        """
        Get asset name for symbol
        Returns cached name or fetches from API
        """
        # Check cache first
        if symbol in self.names:
            return self.names[symbol]
        
        # Fetch from API
        name = self._fetch_name(symbol, asset_type, api_key)
        
        # Cache it
        if name:
            self.names[symbol] = name
            self.save()
        
        return name or symbol  # Return symbol if no name found
    
    def _fetch_name(self, symbol: str, asset_type: str = None, api_key: str = None) -> str:
        """Fetch name from appropriate API"""
        
        # Crypto names (hardcoded - no API needed)
        crypto_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'BNB': 'Binance Coin',
            'SOL': 'Solana',
            'XRP': 'XRP',
            'ADA': 'Cardano',
            'AVAX': 'Avalanche',
            'DOT': 'Polkadot',
            'MATIC': 'Polygon',
            'LINK': 'Chainlink',
            'UNI': 'Uniswap',
            'ATOM': 'Cosmos',
            'DOGE': 'Dogecoin',
            'SHIB': 'Shiba Inu',
        }
        
        if symbol in crypto_names:
            return crypto_names[symbol]
        
        # Stocks/ETFs - use Polygon API
        if api_key:
            try:
                url = f"https://api.polygon.io/v3/reference/tickers/{symbol}"
                params = {'apiKey': api_key}
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'results' in data and 'name' in data['results']:
                        return data['results']['name']
            except:
                pass
        
        return None
    
    def bulk_fetch(self, symbols: list, api_key: str = None):
        """
        Fetch names for multiple symbols
        Only fetches uncached ones
        """
        to_fetch = [s for s in symbols if s not in self.names]
        
        print(f"Fetching names for {len(to_fetch)} assets...")
        
        for i, symbol in enumerate(to_fetch):
            name = self._fetch_name(symbol, api_key=api_key)
            if name:
                self.names[symbol] = name
            
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(to_fetch)}...")
                self.save()  # Save periodically
        
        self.save()
        print(f"✓ Fetched {len(to_fetch)} names")
