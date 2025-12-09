"""Health check router."""

from fastapi import APIRouter, Query

from models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    days: int = Query(default=90, description="Number of days to check data for")
) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns status and counts of loaded data.
    """
    from index import get_analytics_service, _orders_df, _matcher, _analytics_services
    
    # Try to get service for the requested time range
    service = _analytics_services.get(days)
    inspections_count = 0
    
    if service is not None:
        inspections_count = len(service.inspections_df) if service.inspections_df is not None else 0
    
    return HealthResponse(
        status="ok",
        orders_loaded=len(_orders_df) if _orders_df is not None else 0,
        inspections_loaded=inspections_count,
        restaurants_mapped=len(_matcher._mapping) if _matcher else 0,
    )
