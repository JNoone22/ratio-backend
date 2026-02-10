"""
Tournament Ranking Algorithm
Calculates relative strength using synthetic pair ratios vs ratio MAs
"""
from typing import List, Dict, Tuple
import config

def calculate_sma(prices: List[float], period: int) -> float:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return sum(prices[:period]) / period

def wins_matchup(asset_a_prices: List[float], asset_b_prices: List[float]) -> bool:
    """
    Determine if asset A beats asset B using synthetic pair method
    
    Creates A/B ratio, compares current ratio to ratio's 20-week MA
    If ratio > ratio_MA, asset A wins
    If ratio < ratio_MA, asset B wins
    
    Returns: True if asset A wins, False if asset B wins
    """
    if len(asset_a_prices) < config.MA_PERIOD or len(asset_b_prices) < config.MA_PERIOD:
        return False
    
    # Calculate synthetic pair ratio for each week
    ratio_history = []
    for i in range(config.MA_PERIOD):
        if asset_b_prices[i] == 0:
            return False  # Can't calculate ratio, asset B wins by default
        ratio = asset_a_prices[i] / asset_b_prices[i]
        ratio_history.append(ratio)
    
    # Calculate MA of the ratio
    ratio_ma = calculate_sma(ratio_history, config.MA_PERIOD)
    
    # Current ratio (most recent week)
    if asset_b_prices[0] == 0:
        return False  # Can't calculate current ratio
    current_ratio = asset_a_prices[0] / asset_b_prices[0]
    
    # Asset A wins if current ratio > ratio MA
    return current_ratio > ratio_ma

def calculate_individual_ma_distance(prices: List[float]) -> Dict:
    """
    Calculate how far asset is above/below its own 20-week MA
    Used as tiebreaker
    """
    if len(prices) < config.MA_PERIOD:
        return {
            'current_price': 0,
            'ma': 0,
            'percent_above_ma': 0,
            'above_ma': False
        }
    
    current_price = prices[0]
    ma = calculate_sma(prices, config.MA_PERIOD)
    percent_above_ma = ((current_price - ma) / ma) * 100
    
    return {
        'current_price': round(current_price, 2),
        'ma': round(ma, 2),
        'percent_above_ma': round(percent_above_ma, 2),
        'above_ma': current_price > ma
    }

def calculate_tournament_rankings(assets_data: Dict[str, List[float]]) -> List[Dict]:
    """
    Run full tournament: every asset vs every other asset
    
    Args:
        assets_data: Dict of {symbol: [weekly_closes]}
        
    Returns:
        List of assets ranked by tournament wins
    """
    symbols = list(assets_data.keys())
    
    # Initialize win counts
    results = {}
    for symbol in symbols:
        results[symbol] = {
            'symbol': symbol,
            'wins': 0,
            'losses': 0,
            'total_matchups': 0
        }
    
    # Run tournament (all pairwise matchups)
    print(f"\n🏆 Running tournament with {len(symbols)} assets...")
    print(f"Total matchups: {len(symbols) * (len(symbols) - 1):,}")
    
    matchup_count = 0
    for asset_a in symbols:
        for asset_b in symbols:
            # Skip self-matchups
            if asset_a == asset_b:
                continue
            
            # CRITICAL FIX: Only evaluate each pair once!
            # Skip if we've already done this matchup (B vs A)
            if asset_a > asset_b:
                continue
            
            matchup_count += 1
            if matchup_count % 10000 == 0:
                print(f"Processed {matchup_count:,} matchups...")
            
            try:
                if wins_matchup(assets_data[asset_a], assets_data[asset_b]):
                    results[asset_a]['wins'] += 1
                    results[asset_b]['losses'] += 1
                else:
                    results[asset_b]['wins'] += 1
                    results[asset_a]['losses'] += 1
                
                results[asset_a]['total_matchups'] += 1
                results[asset_b]['total_matchups'] += 1
                
            except Exception as e:
                print(f"Error in matchup {asset_a} vs {asset_b}: {e}")
                continue
    
    print(f"✓ Tournament complete! Processed {matchup_count:,} matchups\n")
    
    # Add individual MA data for tiebreaker
    for symbol in symbols:
        ma_data = calculate_individual_ma_distance(assets_data[symbol])
        results[symbol].update(ma_data)
        
        # Calculate win rate
        total = results[symbol]['total_matchups']
        wins = results[symbol]['wins']
        results[symbol]['win_rate'] = round((wins / total * 100), 1) if total > 0 else 0
    
    # Sort by wins (primary), then % above MA (tiebreaker)
    ranked = sorted(
        results.values(),
        key=lambda x: (x['wins'], x['percent_above_ma']),
        reverse=True
    )
    
    # Add rank number
    for i, asset in enumerate(ranked):
        asset['rank'] = i + 1
    
    return ranked

def format_rankings_summary(rankings: List[Dict], top_n: int = 10) -> str:
    """Format top N rankings for display"""
    output = []
    output.append(f"\n{'='*60}")
    output.append(f"TOP {top_n} ASSETS BY RELATIVE STRENGTH")
    output.append(f"{'='*60}")
    output.append(f"{'Rank':<6}{'Symbol':<8}{'Wins':<10}{'Win %':<10}{'vs MA':<10}{'Status'}")
    output.append(f"{'-'*60}")
    
    for asset in rankings[:top_n]:
        status = "✓" if asset['above_ma'] else "✗"
        output.append(
            f"{asset['rank']:<6}"
            f"{asset['symbol']:<8}"
            f"{asset['wins']:<10}"
            f"{asset['win_rate']:<10.1f}"
            f"{asset['percent_above_ma']:+.2f}%    "
            f"{status}"
        )
    
    output.append(f"{'='*60}\n")
    return '\n'.join(output)

# Test the algorithm
if __name__ == '__main__':
    # Mock data for testing
    print("Testing tournament algorithm with mock data...")
    
    mock_data = {
        'AAPL': [180, 175, 170, 165, 160, 155, 150, 145, 140, 135, 
                 130, 125, 120, 115, 110, 105, 100, 95, 90, 85],
        'MSFT': [350, 345, 340, 335, 330, 325, 320, 315, 310, 305,
                 300, 295, 290, 285, 280, 275, 270, 265, 260, 255],
        'GOOGL': [140, 138, 136, 134, 132, 130, 128, 126, 124, 122,
                  120, 118, 116, 114, 112, 110, 108, 106, 104, 102],
    }
    
    rankings = calculate_tournament_rankings(mock_data)
    print(format_rankings_summary(rankings))
