"""
Vercel Serverless Function Entry Point.
Exposes the FastAPI app for Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add the api directory to the path for imports
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import io

# Import services
from services.data_loader import DataLoader
from services.nyc_api import NYCInspectionAPI
from services.matcher import RestaurantMatcher
from services.analytics import AnalyticsService
from services.pdf_generator import PDFReportGenerator
from models.schemas import (
    HealthResponse,
    RevenueByGradeResponse,
    RodentOrdersResponse,
    RevenueAtRiskResponse,
    BoroughBreakdownResponse,
    WatchlistResponse,
    SummaryResponse,
)

# Configuration
NYC_API_BASE_URL = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"

# Initialize FastAPI app
app = FastAPI(
    title="RatChallenge API",
    description="Food delivery risk analysis combining order data with NYC Restaurant Inspection Results",
    version="1.0.0",
)

# Configure CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Vercel handles this at the edge
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for caching data between requests (within same instance)
_analytics_service: AnalyticsService | None = None
_orders_df = None
_inspections_df = None
_matcher = None


async def get_analytics_service() -> AnalyticsService:
    """Get or initialize the analytics service."""
    global _analytics_service, _orders_df, _inspections_df, _matcher
    
    if _analytics_service is not None:
        return _analytics_service
    
    # Initialize services
    csv_path = api_dir / "data" / "food_orders.csv"
    mapping_path = api_dir / "data" / "restaurant_mapping.json"
    
    data_loader = DataLoader(csv_path)
    nyc_api = NYCInspectionAPI(NYC_API_BASE_URL)
    matcher = RestaurantMatcher(mapping_path)
    
    # Load data
    _orders_df = data_loader.load_orders()
    
    # Fetch NYC inspection data (will use bundled cache if available)
    cache_path = api_dir / "data" / "inspections_cache.parquet"
    if cache_path.exists():
        import pandas as pd
        _inspections_df = pd.read_parquet(cache_path)
    else:
        # Fallback to API fetch (slower, may timeout on cold start)
        _inspections_df = await nyc_api.fetch_all_inspections(use_cache=False)
    
    await nyc_api.close()
    
    # Initialize analytics service
    _matcher = matcher
    _analytics_service = AnalyticsService(_orders_df, _inspections_df, matcher)
    
    return _analytics_service


@app.get("/api/health")
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    try:
        service = await get_analytics_service()
        return HealthResponse(
            status="ok",
            orders_loaded=len(service.orders_df) if service.orders_df is not None else 0,
            inspections_loaded=len(service.inspections_df) if service.inspections_df is not None else 0,
            restaurants_mapped=len(_matcher._mapping) if _matcher else 0,
        )
    except Exception as e:
        return HealthResponse(
            status=f"error: {str(e)}",
            orders_loaded=0,
            inspections_loaded=0,
            restaurants_mapped=0,
        )


@app.get("/api/analytics/summary")
async def get_summary() -> SummaryResponse:
    """Get combined summary of all analytics."""
    service = await get_analytics_service()
    data = service.get_summary()
    return SummaryResponse(**data)


@app.get("/api/analytics/rodent-orders")
async def get_rodent_orders() -> RodentOrdersResponse:
    """Get orders from restaurants with rodent violations."""
    service = await get_analytics_service()
    data = service.get_rodent_orders()
    return RodentOrdersResponse(**data)


@app.get("/api/analytics/revenue-by-grade")
async def get_revenue_by_grade() -> RevenueByGradeResponse:
    """Get revenue breakdown by NYC inspection grade."""
    service = await get_analytics_service()
    data = service.get_revenue_by_grade()
    return RevenueByGradeResponse(**data)


@app.get("/api/analytics/revenue-at-risk")
async def get_revenue_at_risk() -> RevenueAtRiskResponse:
    """Calculate Revenue at Risk (RAR)."""
    service = await get_analytics_service()
    data = service.get_revenue_at_risk()
    return RevenueAtRiskResponse(**data)


@app.get("/api/analytics/borough-breakdown")
async def get_borough_breakdown() -> BoroughBreakdownResponse:
    """Get revenue breakdown by NYC borough."""
    service = await get_analytics_service()
    data = service.get_borough_breakdown()
    return BoroughBreakdownResponse(**data)


@app.get("/api/analytics/watchlist")
async def get_watchlist(top_n: int = 10) -> WatchlistResponse:
    """Get top N highest-earning restaurants with health risk flags."""
    service = await get_analytics_service()
    data = service.get_watchlist(top_n=top_n)
    return WatchlistResponse(**data)


@app.get("/api/report/pdf")
async def generate_pdf_report() -> StreamingResponse:
    """Generate and download PDF report."""
    service = await get_analytics_service()
    generator = PDFReportGenerator(service)
    pdf_buffer = generator.generate()
    
    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=rat_challenge_report.pdf"
        }
    )


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

