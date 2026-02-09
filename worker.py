"""
Background Worker for Daily Data Updates
Runs independently of the web server - no timeout limits
"""
import time
import schedule
from datetime import datetime
import requests

# Import our update logic
import config
from massive_client import MassiveClient
from coincap_client import CoinbaseClient
from cryptocompare_client import CryptoCompareClient
from cache_manager import CacheManager
from name_lookup import NameLookup
from tournament import calculate_tournament_rankings

# Initialize clients
massive = MassiveClient(config.MASSIVE_API_KEY)
coinbase = CoinbaseClient()
cryptocompare = CryptoCompareClient()
cache_manager = CacheManager()
name_lookup = NameLookup()

def update_all_data():
    """
    Full data update - fetches fresh prices for all assets
    Runs without timeout restrictions
    """
    print("\n" + "="*60)
    print(f"🤖 WORKER: Starting daily update - {datetime.now()}")
    print("="*60)
    
    try:
        # Import the update function from main
        from main import update_rankings
        
        # Do full update (all asset types)
        success = update_rankings(test_mode=False)
        
        if success:
            print(f"✅ WORKER: Update completed successfully at {datetime.now()}")
        else:
            print(f"❌ WORKER: Update failed at {datetime.now()}")
            
    except Exception as e:
        print(f"❌ WORKER ERROR: {e}")

def run_worker():
    """
    Main worker loop
    """
    print("\n🚀 Background Worker Started!")
    print("=" * 60)
    print("Schedule: Daily at 2:00 AM UTC")
    print("=" * 60)
    
    # Schedule daily update at 2 AM UTC
    schedule.every().day.at("02:00").do(update_all_data)
    
    # Optional: Also run on startup (comment out if not desired)
    print("\n⚡ Running initial update on startup...")
    update_all_data()
    
    # Keep running and check schedule
    print("\n⏰ Worker now waiting for scheduled updates...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == '__main__':
    run_worker()
