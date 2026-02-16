"""
CoinGecko Public API Client
Handles cryptocurrency data (free, no API key required)
Covers ALL major cryptocurrencies
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import time

class CoinGeckoClient:
    def __init__(self):
        self.base_url = 'https://api.coingecko.com/api/v3'
        self._coins_cache = None
        
        # Map common symbols to CoinGecko IDs
        self.symbol_to_id = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
            'AVAX': 'avalanche-2',
            'DOGE': 'dogecoin',
            'DOT': 'polkadot',
            'MATIC': 'matic-network',
            'LINK': 'chainlink',
            'UNI': 'uniswap',
            'ATOM': 'cosmos',
            'LTC': 'litecoin',
            'BCH': 'bitcoin-cash',
            'NEAR': 'near',
            'ICP': 'internet-computer',
            'APT': 'aptos',
            'FIL': 'filecoin',
            'ARB': 'arbitrum',
            'OP': 'optimism',
            'STX': 'blockstack',
            'IMX': 'immutable-x',
            'INJ': 'injective-protocol',
            'CRO': 'crypto-com-chain',
            'VET': 'vechain',
            'HBAR': 'hedera-hashgraph',
            'MKR': 'maker',
            'RNDR': 'render-token',
            'GRT': 'the-graph',
            'ALGO': 'algorand',
            'AAVE': 'aave',
            'ETC': 'ethereum-classic',
            'XLM': 'stellar',
            'RUNE': 'thorchain',
            'SAND': 'the-sandbox',
            'MANA': 'decentraland',
            'AXS': 'axie-infinity',
            'THETA': 'theta-token',
            'FTM': 'fantom',
            'EOS': 'eos',
            'XTZ': 'tezos',
            'EGLD': 'elrond-erd-2',
            'TRX': 'tron',
            'TON': 'the-open-network',
            'SHIB': 'shiba-inu',
            'DAI': 'dai',
            'USDC': 'usd-coin',
        }
    
    def get_top_coins(self, limit: int = 200) -> List[str]:
        """
        Get top cryptocurrencies by market cap
        Returns list of symbols
        """
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': min(limit, 250),
                'page': 1,
                'sparkline': False
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            coins = response.json()
            
            # Build symbol to ID mapping from response
            for coin in coins:
                symbol = coin.get('symbol', '').upper()
                coin_id = coin.get('id')
                if symbol and coin_id:
                    self.symbol_to_id[symbol] = coin_id
            
            # Extract symbols
            symbols = [coin.get('symbol', '').upper() for coin in coins if coin.get('symbol')]
            
            print(f"    ✓ Got {len(symbols)} coins from CoinGecko")
            print(f"    Top 10: {', '.join(symbols[:10])}")
            
            return symbols[:limit]
            
        except Exception as e:
            print(f"    ✗ Error fetching CoinGecko top coins: {e}")
            # Return hardcoded top coins
            return list(self.symbol_to_id.keys())[:limit]
    
    def get_weekly_data(self, symbol: str, weeks: int = 20) -> List[float]:
        """
        Get weekly closing prices for a cryptocurrency
        
        Args:
            symbol: Symbol (e.g., 'BTC', 'ETH')
            weeks: Number of weeks to fetch
        
        Returns:
            List of weekly closing prices, most recent first
        """
        # Get CoinGecko ID for this symbol
        coin_id = self.symbol_to_id.get(symbol)
        if not coin_id:
            raise ValueError(f"Unknown symbol: {symbol}")
        
        # Calculate days needed (weeks * 7 + buffer)
        days = weeks * 7 + 30
        
        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': days,
            'interval': 'daily'
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extract prices (timestamp, price pairs)
            prices = data.get('prices', [])
            if not prices:
                raise ValueError(f"No price data returned for {symbol}")
            
            # Convert to weekly by sampling every 7 days
            weekly_prices = []
            for i in range(0, len(prices), 7):
                if prices[i]:
                    weekly_prices.append(prices[i][1])  # [timestamp, price]
            
            # Reverse to get newest first
            weekly_prices.reverse()
            
            if len(weekly_prices) < weeks:
                raise ValueError(f"Insufficient data: {len(weekly_prices)} weeks")
            
            return weekly_prices[:weeks]
            
        except Exception as e:
            raise Exception(f"Failed to fetch {symbol}: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test CoinGecko API connection"""
        try:
            url = f"{self.base_url}/ping"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


if __name__ == '__main__':
    client = CoinGeckoClient()
    print("Testing CoinGecko API...")
    
    if client.test_connection():
        print("✓ Connection successful!")
        
        # Test fetching BTC
        try:
            btc_data = client.get_weekly_data('BTC', weeks=5)
            print(f"✓ BTC: Got {len(btc_data)} weeks")
            print(f"  Recent prices: ${btc_data[0]:,.2f}, ${btc_data[1]:,.2f}, ${btc_data[2]:,.2f}")
        except Exception as e:
            print(f"✗ BTC error: {e}")
        
        # Get top coins
        top = client.get_top_coins(20)
        print(f"✓ Top 20 by market cap: {', '.join(top[:10])}...")
        
    else:
        print("✗ Connection failed")
