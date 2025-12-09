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
_analytics_service = None
_orders_df = None
_inspections_df = None
_matcher = None
_nyc_api = None


async def get_analytics_service():
    """Get or initialize the analytics service."""
    global _analytics_service, _orders_df, _inspections_df, _matcher, _nyc_api
    
    if _analytics_service is not None:
        return _analytics_service
    
    from services.data_loader import DataLoader
    from services.nyc_api import NYCInspectionAPI
    from services.matcher import RestaurantMatcher
    from services.analytics import AnalyticsService
    
    settings = get_settings()
    
    # Initialize services
    data_loader = DataLoader(settings.csv_path)
    _nyc_api = NYCInspectionAPI(
        settings.nyc_api_base_url,
        settings.nyc_api_app_token,
    )
    _matcher = RestaurantMatcher(settings.mapping_path)
    
    # Load data
    _orders_df = data_loader.load_orders()
    
    # Fetch NYC inspection data directly from API (no caching)
    _inspections_df = await _nyc_api.fetch_all_inspections()
    
    # Initialize analytics service
    _analytics_service = AnalyticsService(_orders_df, _inspections_df, _matcher)
    
    return _analytics_service


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
