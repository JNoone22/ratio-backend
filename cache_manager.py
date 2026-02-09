"""
Cache Manager - Persistent storage for asset data and rankings
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class CacheManager:
    def __init__(self, cache_file='data_cache.json'):
        self.cache_file = cache_file
        self.data = {
            'assets': {},           # {symbol: [weekly_prices]}
            'big_board': [],        # Ranked assets
            'crypto_explorer': [],  # Crypto-only rankings
            'last_update': None,
            'metadata': {
                'total_assets': 0,
                'stocks': 0,
                'etfs': 0,
                'crypto': 0
            }
        }
        self.load()
    
    def load(self):
        """Load cache from disk"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.data = json.load(f)
                print(f"✓ Loaded cache from disk: {len(self.data.get('assets', {}))} assets")
                return True
            except Exception as e:
                print(f"✗ Error loading cache: {e}")
                return False
        else:
            print("No cache file found - starting fresh")
            return False
    
    def save(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            print(f"✓ Saved cache to disk: {len(self.data.get('assets', {}))} assets")
            return True
        except Exception as e:
            print(f"✗ Error saving cache: {e}")
            return False
    
    def get_assets(self) -> Dict[str, List[float]]:
        """Get all asset price data"""
        return self.data.get('assets', {})
    
    def get_asset(self, symbol: str) -> Optional[List[float]]:
        """Get single asset price data"""
        return self.data.get('assets', {}).get(symbol)
    
    def add_asset(self, symbol: str, prices: List[float]):
        """Add or update single asset"""
        self.data['assets'][symbol] = prices
    
    def remove_asset(self, symbol: str):
        """Remove single asset"""
        if symbol in self.data['assets']:
            del self.data['assets'][symbol]
    
    def get_assets_by_type(self, asset_type: str) -> Dict[str, List[float]]:
        """Get all assets of a specific type (from rankings metadata)"""
        # This will be populated by the rankings
        assets = {}
        for asset in self.data.get('big_board', []) + self.data.get('crypto_explorer', []):
            if asset.get('type') == asset_type:
                symbol = asset['symbol']
                if symbol in self.data['assets']:
                    assets[symbol] = self.data['assets'][symbol]
        return assets
    
    def update_rankings(self, big_board: List[dict], crypto_explorer: List[dict]):
        """Update rankings and metadata"""
        self.data['big_board'] = big_board
        self.data['crypto_explorer'] = crypto_explorer
        self.data['last_update'] = datetime.now().isoformat()
        
        # Update metadata
        all_assets = big_board + crypto_explorer
        self.data['metadata'] = {
            'total_assets': len(self.data['assets']),
            'stocks': len([a for a in all_assets if a.get('type') == 'stock']),
            'etfs': len([a for a in all_assets if a.get('type') == 'etf']),
            'crypto': len([a for a in all_assets if a.get('type') == 'crypto'])
        }
    
    def clear(self):
        """Clear all cache data"""
        self.data = {
            'assets': {},
            'big_board': [],
            'crypto_explorer': [],
            'last_update': None,
            'metadata': {'total_assets': 0, 'stocks': 0, 'etfs': 0, 'crypto': 0}
        }
        self.save()
