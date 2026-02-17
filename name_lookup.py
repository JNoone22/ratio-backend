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
        # For crypto: always use the hardcoded dict, never trust cached stock names
        if asset_type == 'crypto':
            return self._fetch_name(symbol, asset_type, api_key)
        
        # Check cache first for non-crypto
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
        
        # Crypto names - if asset_type is crypto, ONLY use this dict, never hit stock API
        crypto_names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum',
            'USDT': 'Tether',
            'BNB': 'Binance Coin',
            'SOL': 'Solana',
            'USDC': 'USD Coin',
            'XRP': 'XRP',
            'DOGE': 'Dogecoin',
            'ADA': 'Cardano',
            'TRX': 'TRON',
            'AVAX': 'Avalanche',
            'SHIB': 'Shiba Inu',
            'TON': 'Toncoin',
            'LINK': 'Chainlink',
            'DOT': 'Polkadot',
            'BCH': 'Bitcoin Cash',
            'LTC': 'Litecoin',
            'UNI': 'Uniswap',
            'NEAR': 'NEAR Protocol',
            'ICP': 'Internet Computer',
            'PEPE': 'Pepe',
            'HBAR': 'Hedera',
            'APT': 'Aptos',
            'FET': 'Fetch.ai',
            'ETC': 'Ethereum Classic',
            'STX': 'Stacks',
            'XLM': 'Stellar',
            'INJ': 'Injective',
            'CRO': 'Cronos',
            'RNDR': 'Render',
            'ATOM': 'Cosmos',
            'ARB': 'Arbitrum',
            'IMX': 'Immutable',
            'OP': 'Optimism',
            'MKR': 'Maker',
            'FIL': 'Filecoin',
            'VET': 'VeChain',
            'RUNE': 'THORChain',
            'XMR': 'Monero',
            'ALGO': 'Algorand',
            'AAVE': 'Aave',
            'GRT': 'The Graph',
            'THETA': 'Theta Network',
            'FTM': 'Fantom',
            'SAND': 'The Sandbox',
            'MANA': 'Decentraland',
            'EOS': 'EOS',
            'FLOW': 'Flow',
            'XTZ': 'Tezos',
            'AXS': 'Axie Infinity',
            'EGLD': 'MultiversX',
            'FLOKI': 'Floki',
            'CHZ': 'Chiliz',
            'NEO': 'NEO',
            'MINA': 'Mina Protocol',
            'KAVA': 'Kava',
            'SNX': 'Synthetix',
            'GALA': 'Gala',
            'QNT': 'Quant',
            'CFX': 'Conflux',
            'FLR': 'Flare',
            'ZEC': 'Zcash',
            'DASH': 'Dash',
            'COMP': 'Compound',
            'LDO': 'Lido DAO',
            'ENJ': 'Enjin Coin',
            'CAKE': 'PancakeSwap',
            'BAT': 'Basic Attention Token',
            'ZIL': 'Zilliqa',
            'CRV': 'Curve DAO',
            'YFI': 'Yearn Finance',
            'GMT': 'STEPN',
            'HNT': 'Helium',
            'SUSHI': 'SushiSwap',
            'CVX': 'Convex Finance',
            'DYDX': 'dYdX',
            'KSM': 'Kusama',
            'MASK': 'Mask Network',
            'RAY': 'Raydium',
            'HYPE': 'Hyperliquid',
            'LEO': 'UNUS SED LEO',
            'SUI': 'Sui',
            'MNT': 'Mantle',
            'TAO': 'Bittensor',
            'ASTR': 'Astar',
            'POL': 'Polygon',
            'MATIC': 'Polygon',
            'WIF': 'dogwifhat',
            'BONK': 'Bonk',
            'TIA': 'Celestia',
            'SEI': 'Sei',
            'JUP': 'Jupiter',
            'WLD': 'Worldcoin',
            'PYTH': 'Pyth Network',
            'STRK': 'Starknet',
            'BLUR': 'Blur',
            'ENS': 'Ethereum Name Service',
            'LRC': 'Loopring',
            '1INCH': '1inch',
            'OCEAN': 'Ocean Protocol',
        }
        
        if asset_type == 'crypto':
            # Never hit stock API for crypto - return from dict or fallback to symbol
            return crypto_names.get(symbol, symbol)
        
        # Also check dict for any symbol that happens to be in it
        if symbol in crypto_names and asset_type != 'stock':
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
