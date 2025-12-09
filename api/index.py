"""
Vercel Serverless Function Entry Point.
Exposes the FastAPI app for Vercel's Python runtime.
"""

import sys
from pathlib import Path

# Add the api directory to the path for imports
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import health, analytics, report

# Global state for caching data between requests (within same instance)
# Cache by days parameter to avoid re-fetching for same time range
_analytics_services: dict[int, any] = {}
_orders_df = None
_matcher = None
_nyc_api = None


async def get_analytics_service(days: int = 90):
    """Get or initialize the analytics service for a specific time range."""
    global _analytics_services, _orders_df, _matcher, _nyc_api
    
    # Return cached service if available for this time range
    if days in _analytics_services:
        return _analytics_services[days]
    
    from services.data_loader import DataLoader
    from services.nyc_api import NYCInspectionAPI
    from services.matcher import RestaurantMatcher
    from services.analytics import AnalyticsService
    
    settings = get_settings()
    
    # Initialize shared services (only once)
    if _orders_df is None:
        data_loader = DataLoader(settings.csv_path)
        _orders_df = data_loader.load_orders()
    
    if _nyc_api is None:
        _nyc_api = NYCInspectionAPI(
            settings.nyc_api_base_url,
            settings.nyc_api_key_id,
            settings.nyc_api_key_secret,
        )
    
    if _matcher is None:
        _matcher = RestaurantMatcher(settings.mapping_path)
    
    # Fetch NYC inspection data for the specified time range
    inspections_df = await _nyc_api.fetch_all_inspections(days=days)
    
    # Initialize analytics service for this time range
    analytics_service = AnalyticsService(_orders_df, inspections_df, _matcher)
    
    # Cache for future requests with same time range
    _analytics_services[days] = analytics_service
    
    return analytics_service


# Create FastAPI app
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

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(report.router, prefix="/api/report", tags=["Report"])

# Export app for Vercel
__all__ = ["app"]
