"""
Binance Public API Client
Handles cryptocurrency data (free, no API key required)
Covers ALL major cryptocurrencies including BNB, XRP, TON, TRX, etc.
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time

class BinanceClient:
    def __init__(self):
        self.base_url = 'https://api.binance.com/api/v3'
        self._symbols_cache = None
    
    def get_all_symbols(self) -> List[str]:
        """
        Get all USDT trading pairs from Binance
        Returns list of base symbols (BTC, ETH, BNB, etc.)
        """
        if self._symbols_cache is not None:
            return self._symbols_cache
        
        try:
            url = f"{self.base_url}/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            symbols = []
            for symbol_info in data['symbols']:
                symbol = symbol_info['symbol']
                # Only USDT pairs that are actively trading
                if symbol.endswith('USDT') and symbol_info['status'] == 'TRADING':
                    base = symbol.replace('USDT', '')
                    symbols.append(base)
            
            self._symbols_cache = symbols
            print(f"    ✓ Found {len(symbols)} USDT trading pairs on Binance")
            return symbols
            
        except Exception as e:
            print(f"    ✗ Error fetching Binance symbols: {e}")
            # Fallback to major coins
            return ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOT', 
                    'MATIC', 'LINK', 'UNI', 'ATOM', 'TON', 'TRX', 'DOGE', 'SHIB']
    
    def get_top_by_volume(self, limit: int = 200) -> List[str]:
        """
        Get top cryptocurrencies by 24h trading volume
        This naturally gives us the top coins by market cap/activity
        """
        try:
            url = f"{self.base_url}/ticker/24hr"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            tickers = response.json()
            
            # Filter for USDT pairs only
            usdt_tickers = [
                t for t in tickers 
                if t['symbol'].endswith('USDT')
            ]
            
            # Sort by volume (quoteVolume = volume in USDT)
            usdt_tickers.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
            
            # Extract base symbols
            top_symbols = [
                t['symbol'].replace('USDT', '') 
                for t in usdt_tickers[:limit]
            ]
            
            return top_symbols
            
        except Exception as e:
            print(f"    ✗ Error fetching top volume coins: {e}")
            print(f"    Using hardcoded top {limit} crypto list...")
            
            # Hardcoded top 200 crypto by market cap (fallback if API fails)
            top_200 = [
                'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'USDC', 'ADA', 'AVAX', 'DOGE', 'TRX',
                'DOT', 'MATIC', 'LINK', 'TON', 'SHIB', 'DAI', 'UNI', 'ATOM', 'LTC', 'BCH',
                'NEAR', 'ICP', 'APT', 'FIL', 'ARB', 'OP', 'STX', 'IMX', 'INJ', 'CRO',
                'VET', 'HBAR', 'MKR', 'RNDR', 'GRT', 'ALGO', 'AAVE', 'ETC', 'XLM', 'RUNE',
                'SAND', 'MANA', 'AXS', 'THETA', 'FTM', 'EOS', 'XTZ', 'ZEC', 'EGLD', 'CAKE',
                'FLOW', 'CHZ', 'XMR', 'NEO', 'KCS', 'GALA', 'KAVA', 'DASH', 'ENJ', 'MINA',
                'LDO', 'CFX', 'FLR', 'OSMO', 'GMT', 'HNT', 'QNT', 'SNX', '1INCH', 'COMP',
                'ZIL', 'BAT', 'CRV', 'YFI', 'SUSHI', 'IOTA', 'LRC', 'ENS', 'AR', 'WAVES',
                'JST', 'OMG', 'ANT', 'AUDIO', 'BAL', 'BAND', 'BNT', 'CELR', 'CHR', 'COTI',
                'CVX', 'DYDX', 'GNO', 'ICX', 'KLAY', 'KNC', 'KSM', 'LQTY', 'MAGA', 'MASK',
                'OXT', 'PERP', 'POLY', 'PROM', 'RAY', 'REN', 'REQ', 'RLC', 'RSR', 'SKL',
                'SRM', 'STORJ', 'SXP', 'TLM', 'TORN', 'TRB', 'TRU', 'UMA', 'UNFI', 'WOO',
                'XVS', 'YGG', 'ZRX', 'AGIX', 'ALICE', 'ALPHA', 'ANKR', 'API3', 'ARPA', 'ASR',
                'ATA', 'ATM', 'AUCTION', 'AVA', 'AXL', 'BADGER', 'BAKE', 'BCH', 'BETA', 'BICO',
                'BLZ', 'BOBA', 'BTT', 'C98', 'CELO', 'CFG', 'CHESS', 'CTSI', 'CTK', 'CTXC',
                'CVP', 'DATA', 'DCR', 'DENT', 'DGB', 'DIA', 'DODO', 'DOGE', 'DUSK', 'EDU',
                'ELF', 'ETHW', 'FET', 'FIDA', 'FIO', 'FIRO', 'FOR', 'FORTH', 'FRONT', 'FTT',
                'FUN', 'GAL', 'GHST', 'GLMR', 'GNS', 'GTC', 'HARD', 'HIGH', 'HIVE', 'HOOK',
                'HOT', 'ID', 'ILV', 'IQ', 'IRIS', 'JASMY', 'JOE', 'JUV', 'KEY', 'LAZIO',
                'LEVER', 'LINA', 'LIT', 'LOOM', 'LOOKS', 'LUNA', 'MAGIC', 'MBOX', 'MC', 'MDT'
            ]
            
            return top_200[:limit]
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a cryptocurrency
        
        Args:
            symbol: Base symbol (e.g., 'BTC', 'ETH', 'BNB')
            weeks: Number of weeks to fetch
        
        Returns:
            List of weekly closing prices, most recent first
        """
        pair = f"{symbol}USDT"
        
        # Binance klines endpoint
        # Interval: 1w (1 week)
        url = f"{self.base_url}/klines"
        
        params = {
            'symbol': pair,
            'interval': '1w',
            'limit': weeks + 5  # Extra buffer for safety
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            klines = response.json()
            
            # Extract close prices
            # Kline format: [open_time, open, high, low, close, volume, close_time, ...]
            closes = [float(k[4]) for k in klines]
            
            # Binance returns oldest first, we want newest first
            closes.reverse()
            
            if len(closes) < weeks:
                raise ValueError(f"Insufficient data: {len(closes)} weeks")
            
            return closes[:weeks]
            
        except Exception as e:
            raise Exception(f"Failed to fetch {symbol}: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Binance API connection"""
        try:
            url = f"{self.base_url}/ping"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


if __name__ == '__main__':
    client = BinanceClient()
    print("Testing Binance API...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        
        # Test fetching BTC
        try:
            btc_data = client.get_weekly_data('BTC', weeks=5)
            print(f"✓ BTC: Got {len(btc_data)} weeks")
            print(f"  Recent prices: {btc_data[:3]}")
        except Exception as e:
            print(f"✗ BTC error: {e}")
        
        # Test fetching BNB (Coinbase doesn't have this)
        try:
            bnb_data = client.get_weekly_data('BNB', weeks=5)
            print(f"✓ BNB: Got {len(bnb_data)} weeks")
            print(f"  Recent prices: {bnb_data[:3]}")
        except Exception as e:
            print(f"✗ BNB error: {e}")
        
        # Get top coins
        top = client.get_top_by_volume(20)
        print(f"✓ Top 20 by volume: {', '.join(top[:10])}...")
        
    else:
        print("✗ Connection failed")
