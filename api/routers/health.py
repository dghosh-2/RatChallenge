"""Health check router."""

from fastapi import APIRouter, Request

from models.schemas import HealthResponse

router = APIRouter()


async def get_analytics_service():
    """Get analytics service - lazy initialization."""
    from index import get_analytics_service as _get_service
    return await _get_service()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns status and counts of loaded data.
    """
    from index import _orders_df, _inspections_df, _matcher
    
    return HealthResponse(
        status="ok",
        orders_loaded=len(_orders_df) if _orders_df is not None else 0,
        inspections_loaded=len(_inspections_df) if _inspections_df is not None else 0,
        restaurants_mapped=len(_matcher._mapping) if _matcher else 0,
    )
