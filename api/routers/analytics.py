"""Analytics router for food safety metrics."""

from enum import Enum
from fastapi import APIRouter, Query

from models.schemas import (
    RevenueByGradeResponse,
    RodentOrdersResponse,
    RevenueAtRiskResponse,
    BoroughBreakdownResponse,
    WatchlistResponse,
    SummaryResponse,
)

router = APIRouter()


class DateRange(int, Enum):
    """Supported date ranges for analysis."""
    WEEK = 7
    MONTH = 30
    QUARTER = 90


async def get_analytics_service(days: int = 90):
    """Get analytics service for a specific time range."""
    from index import get_analytics_service as _get_service
    return await _get_service(days=days)


@router.get("/rodent-orders", response_model=RodentOrdersResponse)
async def get_rodent_orders(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> RodentOrdersResponse:
    """
    Get orders from restaurants with rodent violations.
    
    Identifies all orders from restaurants that have had rodent-related
    violations (rats, mice, vermin) and calculates total revenue.
    """
    service = await get_analytics_service(days=days)
    data = service.get_rodent_orders()
    return RodentOrdersResponse(**data)


@router.get("/revenue-by-grade", response_model=RevenueByGradeResponse)
async def get_revenue_by_grade(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> RevenueByGradeResponse:
    """
    Get revenue breakdown by NYC inspection grade.
    
    Shows total order revenue split by the latest NYC inspection
    grade (A/B/C/Z/P/N) for matched restaurants.
    """
    service = await get_analytics_service(days=days)
    data = service.get_revenue_by_grade()
    return RevenueByGradeResponse(**data)


@router.get("/revenue-at-risk", response_model=RevenueAtRiskResponse)
async def get_revenue_at_risk(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> RevenueAtRiskResponse:
    """
    Calculate Revenue at Risk (RAR).
    
    Estimates revenue at risk from orders at restaurants that:
    - Were closed or re-closed
    - Have grade C, P (Pending), or N (Not Yet Graded)
    - Have critical violations
    """
    service = await get_analytics_service(days=days)
    data = service.get_revenue_at_risk()
    return RevenueAtRiskResponse(**data)


@router.get("/borough-breakdown", response_model=BoroughBreakdownResponse)
async def get_borough_breakdown(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> BoroughBreakdownResponse:
    """
    Get revenue breakdown by NYC borough.
    
    Shows order revenue mix across NYC boroughs and violation categories.
    """
    service = await get_analytics_service(days=days)
    data = service.get_borough_breakdown()
    return BoroughBreakdownResponse(**data)


@router.get("/watchlist", response_model=WatchlistResponse)
async def get_watchlist(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)"),
    top_n: int = Query(default=10, description="Number of restaurants to return")
) -> WatchlistResponse:
    """
    Get top N highest-earning restaurants with health risk flags.
    
    Lists restaurants ranked by revenue that have any open health
    risk flags (critical violations, rodent issues, closures, bad grades).
    """
    service = await get_analytics_service(days=days)
    data = service.get_watchlist(top_n=top_n)
    return WatchlistResponse(**data)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    days: int = Query(default=90, description="Number of days to analyze (7, 30, or 90)")
) -> SummaryResponse:
    """
    Get combined summary of all analytics.
    
    Returns a complete overview including rodent analysis, revenue at risk,
    grade breakdown, borough breakdown, and top watchlist items.
    """
    service = await get_analytics_service(days=days)
    data = service.get_summary()
    return SummaryResponse(**data)
