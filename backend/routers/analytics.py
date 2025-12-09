"""Analytics router for food safety metrics."""

from fastapi import APIRouter, Request, HTTPException

from models.schemas import (
    RevenueByGradeResponse,
    RodentOrdersResponse,
    RevenueAtRiskResponse,
    BoroughBreakdownResponse,
    WatchlistResponse,
    SummaryResponse,
)

router = APIRouter()


def get_analytics_service(request: Request):
    """Get analytics service from app state."""
    service = request.app.state.analytics_service
    if service is None:
        raise HTTPException(status_code=503, detail="Analytics service not initialized")
    return service


@router.get("/rodent-orders", response_model=RodentOrdersResponse)
async def get_rodent_orders(request: Request) -> RodentOrdersResponse:
    """
    Get orders from restaurants with rodent violations.
    
    Identifies all orders from restaurants that have had rodent-related
    violations (rats, mice, vermin) and calculates total revenue.
    """
    service = get_analytics_service(request)
    data = service.get_rodent_orders()
    return RodentOrdersResponse(**data)


@router.get("/revenue-by-grade", response_model=RevenueByGradeResponse)
async def get_revenue_by_grade(request: Request) -> RevenueByGradeResponse:
    """
    Get revenue breakdown by NYC inspection grade.
    
    Shows total order revenue split by the latest NYC inspection
    grade (A/B/C/Z/P/N) for matched restaurants.
    """
    service = get_analytics_service(request)
    data = service.get_revenue_by_grade()
    return RevenueByGradeResponse(**data)


@router.get("/revenue-at-risk", response_model=RevenueAtRiskResponse)
async def get_revenue_at_risk(request: Request) -> RevenueAtRiskResponse:
    """
    Calculate Revenue at Risk (RAR).
    
    Estimates revenue at risk from orders at restaurants that:
    - Were closed or re-closed
    - Have grade C, P (Pending), or N (Not Yet Graded)
    - Have critical violations
    """
    service = get_analytics_service(request)
    data = service.get_revenue_at_risk()
    return RevenueAtRiskResponse(**data)


@router.get("/borough-breakdown", response_model=BoroughBreakdownResponse)
async def get_borough_breakdown(request: Request) -> BoroughBreakdownResponse:
    """
    Get revenue breakdown by NYC borough.
    
    Shows order revenue mix across NYC boroughs and violation categories.
    """
    service = get_analytics_service(request)
    data = service.get_borough_breakdown()
    return BoroughBreakdownResponse(**data)


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(request: Request, top_n: int = 10) -> WatchlistResponse:
    """
    Get top N highest-earning restaurants with health risk flags.
    
    Lists restaurants ranked by revenue that have any open health
    risk flags (critical violations, rodent issues, closures, bad grades).
    
    Args:
        top_n: Number of restaurants to return (default 10)
    """
    service = get_analytics_service(request)
    data = service.get_watchlist(top_n=top_n)
    return WatchlistResponse(**data)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(request: Request) -> SummaryResponse:
    """
    Get combined summary of all analytics.
    
    Returns a complete overview including rodent analysis, revenue at risk,
    grade breakdown, borough breakdown, and top watchlist items.
    """
    service = get_analytics_service(request)
    data = service.get_summary()
    return SummaryResponse(**data)


