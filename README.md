# 🐀 Is There a Rat in My Food?

A full-stack data application that combines food delivery order data with NYC Restaurant Inspection Results to uncover financial risks tied to food safety.

## 📊 Features

- **Rodent Violation Analysis**: Identify all orders from restaurants with documented rodent violations and calculate total revenue impact
- **Revenue by Health Grade**: View order revenue breakdown by NYC inspection grades (A/B/C/Z/P/N)
- **Revenue at Risk (RAR)**: Estimate revenue from restaurants with closures, poor grades, or critical violations
- **Borough Breakdown**: Analyze order revenue distribution across NYC boroughs with violation categories
- **Top 10 Watchlist**: Track highest-earning restaurants with open health risk flags
- **PDF Report Generation**: Download comprehensive PDF reports with all analytics

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js 14    │────▶│    FastAPI      │────▶│  NYC Open Data  │
│   Frontend      │     │    Backend      │     │      API        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  food_orders.csv │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** On first startup, the backend will download NYC inspection data (this may take a few minutes). The data is cached locally in `backend/data/inspections_cache.parquet` for faster subsequent startups. The cache refreshes automatically if it's older than 7 days.

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📁 Project Structure

```
RatChallenge/
├── .cursorrules                    # Coding standards
├── README.md                       # This file
├── food_orders.csv                 # Order data
│
├── backend/
│   ├── requirements.txt            # Python dependencies
│   ├── main.py                     # FastAPI application
│   ├── config.py                   # Configuration settings
│   ├── data/
│   │   └── restaurant_mapping.json # CAMIS ID mappings
│   ├── services/
│   │   ├── nyc_api.py              # NYC API client
│   │   ├── data_loader.py          # CSV loader
│   │   ├── matcher.py              # Restaurant matcher
│   │   ├── analytics.py            # Business calculations
│   │   └── pdf_generator.py        # PDF report generator
│   ├── routers/
│   │   ├── health.py               # Health check endpoint
│   │   ├── analytics.py            # Analytics endpoints
│   │   └── report.py               # PDF generation endpoint
│   └── models/
│       └── schemas.py              # Pydantic models
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   ├── providers.tsx
        │   └── globals.css
        ├── components/
        │   ├── Dashboard.tsx
        │   ├── RevenueByGrade.tsx
        │   ├── RodentOrders.tsx
        │   ├── RevenueAtRisk.tsx
        │   ├── BoroughBreakdown.tsx
        │   └── Watchlist.tsx
        └── lib/
            └── api.ts
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check with data counts |
| GET | `/api/analytics/summary` | Combined analytics summary |
| GET | `/api/analytics/rodent-orders` | Orders from rodent-violation restaurants |
| GET | `/api/analytics/revenue-by-grade` | Revenue breakdown by grade |
| GET | `/api/analytics/revenue-at-risk` | RAR calculation |
| GET | `/api/analytics/borough-breakdown` | Borough revenue analysis |
| GET | `/api/analytics/watchlist?top_n=10` | Top risky restaurants |
| GET | `/api/report/pdf` | Download PDF report |

## 📈 Analytics Methodology

### Data Matching

1. Restaurant names from orders are normalized (removing suffixes like "- CLOSED", "$0 Delivery Fee")
2. A manual mapping file links restaurant names to NYC CAMIS IDs
3. Orders are matched to inspection records via CAMIS ID

### Risk Definitions

- **Rodent Violations**: Inspections mentioning "rodent", "rat", "mice", "mouse", or "vermin"
- **Critical Violations**: Violations flagged as "Critical" in inspection records
- **Revenue at Risk**: Orders from restaurants with:
  - Closure or re-closure actions
  - Grade C
  - Pending grades (P, N, Z)
  - Critical violations

### Limitations

- Not all restaurants could be matched to inspection records
- Order dates are not available in the CSV; all orders treated as within analysis period
- Inspection data reflects historical records, not necessarily current conditions

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Optional: NYC Open Data app token for higher rate limits
NYC_API_APP_TOKEN=your_token_here

# Debug mode
DEBUG=false
```

### Restaurant Mapping

The `backend/data/restaurant_mapping.json` file maps restaurant names to NYC CAMIS IDs. To add new mappings:

```json
{
  "Restaurant Name": {
    "camis": "12345678",
    "dba": "RESTAURANT NAME",
    "boro": "MANHATTAN"
  }
}
```

## 📊 Data Sources

- **Internal Data**: `food_orders.csv` with ~20,000 orders
- **External Data**: [NYC DOHMH Restaurant Inspection Results](https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j)

## 🚀 Deployment

### Frontend Deployment

1. **Set the backend API URL**:
   ```bash
   # In your deployment platform (Vercel, Netlify, etc.)
   NEXT_PUBLIC_API_URL=https://your-backend-api.com
   ```

2. **Build and deploy**:
   ```bash
   cd frontend
   npm run build
   # Deploy the .next folder to your hosting platform
   ```

### Backend Deployment

1. **Set environment variables**:
   ```bash
   # .env file or platform environment variables
   CORS_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
   NYC_API_APP_TOKEN=your_token_here  # Optional but recommended
   ```

2. **Ensure cache directory exists**:
   ```bash
   mkdir -p backend/data
   ```

3. **Deploy**:
   - The cache file (`inspections_cache.parquet`) will be created automatically on first run
   - Consider pre-populating the cache in your deployment process for faster cold starts

### Important Notes

- **PDF Download**: The download button works in production. Ensure:
  - Backend CORS allows your frontend domain
  - Frontend has `NEXT_PUBLIC_API_URL` set correctly
  - Backend has sufficient timeout for PDF generation (may take 10-30 seconds)

- **Cache**: The inspection data cache speeds up startup significantly. On first deployment, the backend will download data (takes a few minutes), then subsequent restarts are fast.

## 🧪 Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

- Python: PEP 8, type hints, Google-style docstrings
- TypeScript: Strict mode, named exports, Tailwind CSS

## 📄 License

MIT License


