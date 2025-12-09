"""Health check router."""

from fastapi import APIRouter, Request

from models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns status and counts of loaded data.
    """
    orders_df = request.app.state.orders_df
    inspections_df = request.app.state.inspections_df
    matcher = request.app.state.matcher
    
    return HealthResponse(
        status="ok",
        orders_loaded=len(orders_df) if orders_df is not None else 0,
        inspections_loaded=len(inspections_df) if inspections_df is not None else 0,
        restaurants_mapped=len(matcher._mapping) if matcher else 0,
    )


