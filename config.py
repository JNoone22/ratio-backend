"""
Configuration for Ratio Backend
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
MASSIVE_API_KEY = os.getenv('MASSIVE_API_KEY', 'YOUR_KEY_HERE')

# API Endpoints
MASSIVE_BASE_URL = 'https://api.polygon.io'
COINCAP_BASE_URL = 'https://api.coincap.io/v2'

# Settings
MA_PERIOD = 20  # 20-week moving average
UPDATE_INTERVAL_HOURS = 1  # Hourly updates
CACHE_TTL_SECONDS = 3600  # 1 hour cache

# Asset Lists
SP500_LIMIT = 500
ETF_LIMIT = 100
COMMODITY_ETF_LIMIT = 20
CRYPTO_LIMIT = 200
CRYPTO_TOP_FOR_BIGBOARD = 20

# Redis (Railway will provide this URL)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Server
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
