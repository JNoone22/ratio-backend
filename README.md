# Ratio - Asset Strength Rankings Backend

Tournament-style asset rankings using 20-week moving average relative strength analysis.

## Overview

Ranks 600+ assets (stocks, ETFs, commodities, crypto) by comparing synthetic pair ratios against their 20-week moving averages.

### How It Works

1. **Data Collection**: Fetches weekly closing prices for all assets
2. **Tournament Calculation**: Every asset vs every other asset
   - Creates synthetic pair (NVDA/AAPL)
   - Compares current ratio to ratio's 20-week MA
   - Winner = asset whose ratio is above the ratio's MA
3. **Ranking**: Sort by total wins, tiebreak by % above own MA

## Architecture

```
Data Sources:
├── Massive.com API (Stocks/ETFs)
└── CoinCap API (Crypto)

Backend:
├── Flask REST API
├── Tournament Algorithm
└── In-memory cache (hourly updates)

Deployment:
├── Railway (hosting)
└── GitHub (code repository)
```

## Setup

### Prerequisites

- Python 3.9+
- Massive.com API key
- Railway account (for deployment)

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your MASSIVE_API_KEY
```

3. **Run server:**
```bash
python main.py
```

Server starts on `http://localhost:5000`

### API Endpoints

**Health Check:**
```
GET /api/health
```

**Big Board (640 assets):**
```
GET /api/big-board
GET /api/big-board?limit=50
```

**Crypto Explorer (200 crypto):**
```
GET /api/crypto-explorer
GET /api/crypto-explorer?limit=100
```

**Individual Asset:**
```
GET /api/asset/NVDA
GET /api/asset/BTC
```

**Manual Update (testing):**
```
POST /api/update
```

## Deployment to Railway

1. **Create Railway project:**
   - Go to railway.app
   - Click "New Project"
   - Connect GitHub repository

2. **Configure environment variables:**
   ```
   MASSIVE_API_KEY=your_key_here
   PORT=5000
   ```

3. **Deploy:**
   - Railway auto-deploys on git push
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn main:app`

## Project Structure

```
ratio-backend/
├── main.py                 # Flask application
├── massive_client.py       # Massive API client
├── coincap_client.py       # CoinCap API client
├── tournament.py           # Ranking algorithm
├── config.py               # Configuration
├── requirements.txt        # Dependencies
├── Procfile               # Railway config
├── .env.example           # Environment template
└── README.md              # This file
```

## Configuration

Edit `config.py` to adjust:

- `MA_PERIOD`: Moving average period (default: 20 weeks)
- `UPDATE_INTERVAL_HOURS`: Update frequency (default: 1 hour)
- Asset counts (S&P 500 size, ETF count, crypto count)

## Performance

**Computation Time:**
- 640 assets = 408,960 pairwise matchups
- ~10 seconds to calculate on standard server
- Results cached for 1 hour

**API Calls:**
- Massive: ~120 calls per update (stocks + ETFs)
- CoinCap: ~200 calls per update (crypto)
- Total: ~320 calls per hour

**Memory Usage:**
- ~200 KB for price data
- ~500 KB for cached rankings
- <1 MB total

## Cost Breakdown

**Monthly:**
- Massive Stocks Starter: $29/month
- CoinCap API: $0/month (free)
- Railway Hosting: $5/month
- **Total: $34/month**

## Next Steps

- [x] Core backend built
- [ ] Deploy to Railway
- [ ] Build frontend (React/HTML)
- [ ] Add user authentication
- [ ] Implement Stripe payments
- [ ] PWA setup for mobile

## Support

Questions? Contact: [your email]

## License

Proprietary - All rights reserved
