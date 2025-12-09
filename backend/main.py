"""FastAPI application entry point for RatChallenge."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import health, analytics, report
from services.data_loader import DataLoader
from services.nyc_api import NYCInspectionAPI
from services.matcher import RestaurantMatcher
from services.analytics import AnalyticsService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    settings = get_settings()
    
    # Initialize services
    data_loader = DataLoader(settings.csv_path)
    nyc_api = NYCInspectionAPI(
        settings.nyc_api_base_url,
        settings.nyc_api_app_token,
        cache_path=settings.cache_path,
    )
    matcher = RestaurantMatcher(settings.mapping_path)
    
    # Load data
    orders_df = data_loader.load_orders()
    
    # Fetch NYC inspection data (will use cache if available)
    inspections_df = await nyc_api.fetch_all_inspections(
        use_cache=True,
        max_age_days=settings.cache_max_age_days,
    )
    
    # Initialize analytics service
    analytics_service = AnalyticsService(orders_df, inspections_df, matcher)
    
    # Store in app state
    app.state.orders_df = orders_df
    app.state.inspections_df = inspections_df
    app.state.matcher = matcher
    app.state.analytics_service = analytics_service
    app.state.nyc_api = nyc_api
    
    yield
    
    # Cleanup
    await nyc_api.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="Food delivery risk analysis combining order data with NYC Restaurant Inspection Results",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # Configure CORS - parse comma-separated origins
    cors_origins_list = [
        origin.strip() for origin in settings.cors_origins.split(",")
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/api", tags=["Health"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
    app.include_router(report.router, prefix="/api/report", tags=["Report"])
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


