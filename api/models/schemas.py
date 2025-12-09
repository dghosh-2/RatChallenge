"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    orders_loaded: int
    inspections_loaded: int
    restaurants_mapped: int


class GradeRevenue(BaseModel):
    """Revenue breakdown by grade."""
    grade: str
    revenue: float = Field(..., description="Total revenue in dollars")
    order_count: int
    percentage: float = Field(..., description="Percentage of total revenue")


class RevenueByGradeResponse(BaseModel):
    """Response for revenue by grade endpoint."""
    total_revenue: float
    grades: list[GradeRevenue]
    unmatched_revenue: float = Field(..., description="Revenue from restaurants not matched to inspections")
    unmatched_order_count: int


class RodentOrder(BaseModel):
    """Order from a restaurant with rodent violations."""
    order_id: int
    restaurant_name: str
    cost: float
    violation_description: str
    inspection_date: str
    camis: str


class RodentOrdersResponse(BaseModel):
    """Response for rodent orders endpoint."""
    total_rodent_revenue: float
    order_count: int
    unique_restaurants: int
    orders: list[RodentOrder]


class RevenueAtRiskResponse(BaseModel):
    """Response for revenue at risk calculation."""
    total_revenue_at_risk: float
    order_count: int
    breakdown: dict[str, float] = Field(..., description="Revenue breakdown by risk category")
    risk_categories: dict[str, int] = Field(..., description="Order count by risk category")


class BoroughRevenue(BaseModel):
    """Revenue breakdown by borough."""
    borough: str
    revenue: float
    order_count: int
    percentage: float
    top_violation_category: str | None = None


class BoroughBreakdownResponse(BaseModel):
    """Response for borough breakdown endpoint."""
    total_revenue: float
    boroughs: list[BoroughRevenue]
    violation_categories: dict[str, float] = Field(..., description="Revenue by violation category")


class WatchlistRestaurant(BaseModel):
    """Restaurant on the health risk watchlist."""
    rank: int
    restaurant_name: str
    camis: str
    revenue: float
    order_count: int
    latest_grade: str | None
    critical_violations: int
    rodent_violations: int
    last_inspection_date: str | None
    risk_flags: list[str]


class WatchlistResponse(BaseModel):
    """Response for watchlist endpoint."""
    restaurants: list[WatchlistRestaurant]
    total_watchlist_revenue: float


class SummaryResponse(BaseModel):
    """Combined summary of all analytics."""
    total_orders: int
    total_revenue: float
    matched_orders: int
    matched_revenue: float
    
    # Rodent analysis
    rodent_revenue: float
    rodent_order_count: int
    rodent_restaurant_count: int
    
    # Revenue at risk
    revenue_at_risk: float
    risk_order_count: int
    
    # Grade breakdown
    grade_breakdown: dict[str, float]
    
    # Borough breakdown
    borough_breakdown: dict[str, float]
    
    # Top watchlist
    top_watchlist: list[WatchlistRestaurant]


