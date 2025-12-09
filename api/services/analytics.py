"""Analytics service for food safety risk calculations."""

import logging
from typing import Any

import pandas as pd

from .matcher import RestaurantMatcher
from .nyc_api import NYCInspectionAPI

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for computing food safety analytics."""
    
    # Risk categories
    RISK_GRADES = ["C", "P", "N", "Z"]  # C, Pending, Not Yet Graded, Grade Pending
    RODENT_KEYWORDS = ["RODENT", "RAT", "MICE", "MOUSE", "VERMIN"]
    CLOSURE_KEYWORDS = ["CLOSED", "RE-CLOSED", "RECLOSED"]
    
    def __init__(
        self,
        orders_df: pd.DataFrame,
        inspections_df: pd.DataFrame,
        matcher: RestaurantMatcher,
    ):
        """
        Initialize the analytics service.
        
        Args:
            orders_df: Orders DataFrame
            inspections_df: NYC Inspections DataFrame
            matcher: Restaurant matcher instance
        """
        self.orders_df = orders_df
        self.inspections_df = inspections_df
        self.matcher = matcher
        
        # Pre-compute merged data
        self._merged_df: pd.DataFrame | None = None
        self._latest_grades: pd.DataFrame | None = None
        self._rodent_violations: pd.DataFrame | None = None
    
    @property
    def merged_df(self) -> pd.DataFrame:
        """Get orders merged with inspection data."""
        if self._merged_df is None:
            self._merged_df = self.matcher.match_orders_to_inspections(
                self.orders_df, self.inspections_df
            )
        return self._merged_df
    
    @property
    def latest_grades(self) -> pd.DataFrame:
        """Get latest grade per restaurant."""
        if self._latest_grades is None:
            self._latest_grades = self._compute_latest_grades()
        return self._latest_grades
    
    @property
    def rodent_violations(self) -> pd.DataFrame:
        """Get all rodent violations."""
        if self._rodent_violations is None:
            self._rodent_violations = self._find_rodent_violations()
        return self._rodent_violations
    
    def _compute_latest_grades(self) -> pd.DataFrame:
        """Compute latest grade for each restaurant."""
        if self.inspections_df.empty:
            return pd.DataFrame()
        
        # Filter to graded inspections
        graded = self.inspections_df[
            self.inspections_df["grade"].isin(["A", "B", "C", "Z", "P", "N"])
        ].copy()
        
        if graded.empty:
            return pd.DataFrame()
        
        # Get latest grade per CAMIS
        graded = graded.sort_values("grade_date", ascending=False)
        return graded.groupby("camis").first().reset_index()
    
    def _find_rodent_violations(self) -> pd.DataFrame:
        """Find all rodent-related violations."""
        if self.inspections_df.empty:
            return pd.DataFrame()
        
        pattern = "|".join(self.RODENT_KEYWORDS)
        mask = self.inspections_df["violation_description"].str.contains(
            pattern, case=False, na=False
        )
        return self.inspections_df[mask].copy()
    
    def get_rodent_orders(self) -> dict[str, Any]:
        """
        Get orders from restaurants with rodent violations.
        
        Returns:
            Dict with rodent revenue analysis
        """
        if self.rodent_violations.empty:
            return {
                "total_rodent_revenue": 0.0,
                "order_count": 0,
                "unique_restaurants": 0,
                "orders": [],
            }
        
        # Get CAMIS IDs with rodent violations
        rodent_camis = set(self.rodent_violations["camis"].unique())
        
        # Filter orders to those from rodent-violation restaurants
        merged = self.merged_df
        rodent_orders = merged[merged["camis"].isin(rodent_camis)].copy()
        
        if rodent_orders.empty:
            return {
                "total_rodent_revenue": 0.0,
                "order_count": 0,
                "unique_restaurants": 0,
                "orders": [],
            }
        
        # Get violation details for each order
        rodent_details = self.rodent_violations.groupby("camis").agg({
            "violation_description": "first",
            "inspection_date": "max",
        }).reset_index()
        
        rodent_orders = rodent_orders.merge(
            rodent_details,
            on="camis",
            how="left",
            suffixes=("", "_rodent"),
        )
        
        # Build response
        total_revenue = float(rodent_orders["cost_of_the_order"].sum())
        order_count = len(rodent_orders)
        unique_restaurants = rodent_orders["restaurant_name"].nunique()
        
        # Format order details (limit to 100 for response size)
        orders_list = []
        for _, row in rodent_orders.head(100).iterrows():
            inspection_date = row.get("inspection_date_rodent")
            if pd.notna(inspection_date):
                inspection_date = inspection_date.strftime("%Y-%m-%d")
            else:
                inspection_date = "Unknown"
            
            orders_list.append({
                "order_id": int(row["order_id"]),
                "restaurant_name": row["restaurant_name"],
                "cost": float(row["cost_of_the_order"]),
                "violation_description": row.get("violation_description_rodent", "Unknown"),
                "inspection_date": inspection_date,
                "camis": row["camis"],
            })
        
        return {
            "total_rodent_revenue": round(total_revenue, 2),
            "order_count": order_count,
            "unique_restaurants": unique_restaurants,
            "orders": orders_list,
        }
    
    def get_revenue_by_grade(self) -> dict[str, Any]:
        """
        Get revenue breakdown by NYC inspection grade.
        
        Returns:
            Dict with revenue by grade analysis
        """
        merged = self.merged_df
        total_revenue = float(self.orders_df["cost_of_the_order"].sum())
        
        # Get orders with grades
        graded_orders = merged[merged["grade"].isin(["A", "B", "C", "Z", "P", "N"])].copy()
        
        # Calculate revenue by grade
        grade_stats = graded_orders.groupby("grade").agg({
            "cost_of_the_order": "sum",
            "order_id": "count",
        }).reset_index()
        
        grade_stats.columns = ["grade", "revenue", "order_count"]
        grade_stats["percentage"] = (grade_stats["revenue"] / total_revenue * 100).round(2)
        grade_stats["revenue"] = grade_stats["revenue"].round(2)
        
        # Calculate unmatched
        unmatched_orders = merged[merged["camis"].isna()]
        unmatched_revenue = float(unmatched_orders["cost_of_the_order"].sum())
        unmatched_count = len(unmatched_orders)
        
        # Also count matched but ungraded
        matched_no_grade = merged[
            (merged["camis"].notna()) & 
            (~merged["grade"].isin(["A", "B", "C", "Z", "P", "N"]))
        ]
        unmatched_revenue += float(matched_no_grade["cost_of_the_order"].sum())
        unmatched_count += len(matched_no_grade)
        
        return {
            "total_revenue": round(total_revenue, 2),
            "grades": grade_stats.to_dict(orient="records"),
            "unmatched_revenue": round(unmatched_revenue, 2),
            "unmatched_order_count": unmatched_count,
        }
    
    def get_revenue_at_risk(self) -> dict[str, Any]:
        """
        Calculate Revenue at Risk (RAR).
        
        RAR includes orders from restaurants that:
        - Were closed or re-closed
        - Have grade C, P (Pending), or N (Not Yet Graded)
        - Have critical violations
        
        Returns:
            Dict with RAR analysis
        """
        merged = self.merged_df
        
        # Initialize risk tracking
        risk_categories = {
            "closed": 0.0,
            "grade_c": 0.0,
            "grade_pending": 0.0,
            "critical_violation": 0.0,
        }
        risk_counts = {
            "closed": 0,
            "grade_c": 0,
            "grade_pending": 0,
            "critical_violation": 0,
        }
        
        # Track unique orders at risk (avoid double counting)
        at_risk_orders = set()
        
        # 1. Closed restaurants
        if "action" in merged.columns:
            closure_pattern = "|".join(self.CLOSURE_KEYWORDS)
            closed_mask = merged["action"].str.contains(
                closure_pattern, case=False, na=False
            )
            closed_orders = merged[closed_mask]
            risk_categories["closed"] = float(closed_orders["cost_of_the_order"].sum())
            risk_counts["closed"] = len(closed_orders)
            at_risk_orders.update(closed_orders["order_id"].tolist())
        
        # 2. Grade C
        grade_c_mask = merged["grade"] == "C"
        grade_c_orders = merged[grade_c_mask]
        risk_categories["grade_c"] = float(grade_c_orders["cost_of_the_order"].sum())
        risk_counts["grade_c"] = len(grade_c_orders)
        at_risk_orders.update(grade_c_orders["order_id"].tolist())
        
        # 3. Pending grades (P, N, Z)
        pending_mask = merged["grade"].isin(["P", "N", "Z"])
        pending_orders = merged[pending_mask]
        risk_categories["grade_pending"] = float(pending_orders["cost_of_the_order"].sum())
        risk_counts["grade_pending"] = len(pending_orders)
        at_risk_orders.update(pending_orders["order_id"].tolist())
        
        # 4. Critical violations (from inspection data)
        if "critical_flag" in merged.columns:
            critical_mask = merged["critical_flag"].str.upper() == "CRITICAL"
            critical_orders = merged[critical_mask]
            risk_categories["critical_violation"] = float(
                critical_orders["cost_of_the_order"].sum()
            )
            risk_counts["critical_violation"] = len(critical_orders)
            at_risk_orders.update(critical_orders["order_id"].tolist())
        
        # Calculate total RAR (unique orders only)
        all_at_risk = merged[merged["order_id"].isin(at_risk_orders)]
        total_rar = float(all_at_risk["cost_of_the_order"].sum())
        
        return {
            "total_revenue_at_risk": round(total_rar, 2),
            "order_count": len(at_risk_orders),
            "breakdown": {k: round(v, 2) for k, v in risk_categories.items()},
            "risk_categories": risk_counts,
        }
    
    def get_borough_breakdown(self) -> dict[str, Any]:
        """
        Get revenue breakdown by NYC borough and violation categories.
        
        Returns:
            Dict with borough analysis
        """
        merged = self.merged_df
        total_revenue = float(self.orders_df["cost_of_the_order"].sum())
        
        # Add borough from matcher if not present from inspections
        if "boro" not in merged.columns or merged["boro"].isna().all():
            merged = self.matcher.enrich_orders_with_boro(merged)
        
        # Calculate revenue by borough
        boro_stats = merged.groupby("boro").agg({
            "cost_of_the_order": "sum",
            "order_id": "count",
        }).reset_index()
        
        boro_stats.columns = ["borough", "revenue", "order_count"]
        boro_stats = boro_stats[boro_stats["borough"].notna()]
        boro_stats["percentage"] = (boro_stats["revenue"] / total_revenue * 100).round(2)
        boro_stats["revenue"] = boro_stats["revenue"].round(2)
        
        # Get top violation category per borough
        if "violation_description" in merged.columns:
            def get_top_violation(group):
                violations = group["violation_description"].dropna()
                if violations.empty:
                    return None
                return violations.mode().iloc[0] if not violations.mode().empty else None
            
            top_violations = merged.groupby("boro").apply(
                get_top_violation, include_groups=False
            ).to_dict()
            boro_stats["top_violation_category"] = boro_stats["borough"].map(top_violations)
        else:
            boro_stats["top_violation_category"] = None
        
        # Calculate violation category breakdown
        violation_revenue: dict[str, float] = {}
        if "violation_description" in merged.columns:
            # Categorize violations
            for _, row in merged.iterrows():
                desc = str(row.get("violation_description", "")).upper()
                cost = float(row.get("cost_of_the_order", 0))
                
                if any(kw in desc for kw in self.RODENT_KEYWORDS):
                    violation_revenue["rodent"] = violation_revenue.get("rodent", 0) + cost
                elif "FOOD" in desc and ("TEMPERATURE" in desc or "COLD" in desc or "HOT" in desc):
                    violation_revenue["temperature"] = violation_revenue.get("temperature", 0) + cost
                elif "SANIT" in desc or "CLEAN" in desc:
                    violation_revenue["sanitation"] = violation_revenue.get("sanitation", 0) + cost
                elif "PEST" in desc or "INSECT" in desc or "FLY" in desc or "ROACH" in desc:
                    violation_revenue["pest"] = violation_revenue.get("pest", 0) + cost
        
        violation_revenue = {k: round(v, 2) for k, v in violation_revenue.items()}
        
        return {
            "total_revenue": round(total_revenue, 2),
            "boroughs": boro_stats.to_dict(orient="records"),
            "violation_categories": violation_revenue,
        }
    
    def get_watchlist(self, top_n: int = 10) -> dict[str, Any]:
        """
        Get top N highest-earning restaurants with health risk flags.
        
        Args:
            top_n: Number of restaurants to return
            
        Returns:
            Dict with watchlist data
        """
        merged = self.merged_df
        
        # Calculate revenue per restaurant
        restaurant_stats = merged.groupby(["restaurant_name", "camis"]).agg({
            "cost_of_the_order": "sum",
            "order_id": "count",
            "grade": "first",
            "inspection_date": "max",
        }).reset_index()
        
        restaurant_stats.columns = [
            "restaurant_name", "camis", "revenue", "order_count",
            "latest_grade", "last_inspection_date"
        ]
        
        # Filter to only matched restaurants
        restaurant_stats = restaurant_stats[restaurant_stats["camis"].notna()]
        
        # Calculate risk flags for each restaurant
        def get_risk_flags(camis: str) -> tuple[list[str], int, int]:
            """Get risk flags, critical count, and rodent count for a restaurant."""
            flags = []
            critical_count = 0
            rodent_count = 0
            
            restaurant_inspections = self.inspections_df[
                self.inspections_df["camis"] == camis
            ]
            
            if restaurant_inspections.empty:
                return flags, 0, 0
            
            # Check for critical violations
            critical_mask = restaurant_inspections["critical_flag"].str.upper() == "CRITICAL"
            critical_count = critical_mask.sum()
            if critical_count > 0:
                flags.append(f"{critical_count} critical violations")
            
            # Check for rodent violations
            pattern = "|".join(self.RODENT_KEYWORDS)
            rodent_mask = restaurant_inspections["violation_description"].str.contains(
                pattern, case=False, na=False
            )
            rodent_count = rodent_mask.sum()
            if rodent_count > 0:
                flags.append(f"{rodent_count} rodent violations")
            
            # Check for closures
            closure_pattern = "|".join(self.CLOSURE_KEYWORDS)
            closure_mask = restaurant_inspections["action"].str.contains(
                closure_pattern, case=False, na=False
            )
            if closure_mask.any():
                flags.append("closure history")
            
            # Check for bad grades
            latest_grade = restaurant_inspections.sort_values(
                "grade_date", ascending=False
            )["grade"].iloc[0] if "grade" in restaurant_inspections.columns else None
            
            if latest_grade in ["C", "P", "N", "Z"]:
                flags.append(f"grade {latest_grade}")
            
            return flags, critical_count, rodent_count
        
        # Apply risk flag calculation
        risk_data = restaurant_stats["camis"].apply(get_risk_flags)
        restaurant_stats["risk_flags"] = risk_data.apply(lambda x: x[0])
        restaurant_stats["critical_violations"] = risk_data.apply(lambda x: x[1])
        restaurant_stats["rodent_violations"] = risk_data.apply(lambda x: x[2])
        
        # Filter to restaurants with any risk flags
        at_risk = restaurant_stats[
            restaurant_stats["risk_flags"].apply(len) > 0
        ].copy()
        
        # Sort by revenue descending
        at_risk = at_risk.sort_values("revenue", ascending=False).head(top_n)
        
        # Format response
        watchlist = []
        for rank, (_, row) in enumerate(at_risk.iterrows(), 1):
            inspection_date = row["last_inspection_date"]
            if pd.notna(inspection_date):
                inspection_date = inspection_date.strftime("%Y-%m-%d")
            else:
                inspection_date = None
            
            watchlist.append({
                "rank": rank,
                "restaurant_name": row["restaurant_name"],
                "camis": row["camis"],
                "revenue": round(float(row["revenue"]), 2),
                "order_count": int(row["order_count"]),
                "latest_grade": row["latest_grade"] if pd.notna(row["latest_grade"]) else None,
                "critical_violations": int(row["critical_violations"]),
                "rodent_violations": int(row["rodent_violations"]),
                "last_inspection_date": inspection_date,
                "risk_flags": row["risk_flags"],
            })
        
        total_watchlist_revenue = sum(r["revenue"] for r in watchlist)
        
        return {
            "restaurants": watchlist,
            "total_watchlist_revenue": round(total_watchlist_revenue, 2),
        }
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get combined summary of all analytics.
        
        Returns:
            Dict with complete summary
        """
        merged = self.merged_df
        
        # Basic stats
        total_orders = len(self.orders_df)
        total_revenue = float(self.orders_df["cost_of_the_order"].sum())
        
        matched_orders = merged[merged["camis"].notna()]
        matched_count = len(matched_orders)
        matched_revenue = float(matched_orders["cost_of_the_order"].sum())
        
        # Rodent analysis
        rodent_data = self.get_rodent_orders()
        
        # Revenue at risk
        rar_data = self.get_revenue_at_risk()
        
        # Grade breakdown
        grade_data = self.get_revenue_by_grade()
        grade_breakdown = {
            g["grade"]: g["revenue"]
            for g in grade_data["grades"]
        }
        
        # Borough breakdown
        boro_data = self.get_borough_breakdown()
        boro_breakdown = {
            b["borough"]: b["revenue"]
            for b in boro_data["boroughs"]
        }
        
        # Watchlist
        watchlist_data = self.get_watchlist(10)
        
        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "matched_orders": matched_count,
            "matched_revenue": round(matched_revenue, 2),
            "rodent_revenue": rodent_data["total_rodent_revenue"],
            "rodent_order_count": rodent_data["order_count"],
            "rodent_restaurant_count": rodent_data["unique_restaurants"],
            "revenue_at_risk": rar_data["total_revenue_at_risk"],
            "risk_order_count": rar_data["order_count"],
            "grade_breakdown": grade_breakdown,
            "borough_breakdown": boro_breakdown,
            "top_watchlist": watchlist_data["restaurants"],
        }


