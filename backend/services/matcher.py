"""Restaurant matching service using manual mapping file."""

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .data_loader import DataLoader

logger = logging.getLogger(__name__)


class RestaurantMatcher:
    """Match restaurant names from orders to NYC CAMIS IDs."""
    
    def __init__(self, mapping_path: Path | str):
        """
        Initialize the matcher with a mapping file.
        
        Args:
            mapping_path: Path to the restaurant_mapping.json file
        """
        self.mapping_path = Path(mapping_path)
        self._mapping: dict[str, dict[str, Any]] = {}
        self._normalized_mapping: dict[str, dict[str, Any]] = {}
        self._load_mapping()
    
    def _load_mapping(self) -> None:
        """Load the mapping file and build normalized lookup."""
        if not self.mapping_path.exists():
            logger.warning(f"Mapping file not found: {self.mapping_path}")
            return
        
        with open(self.mapping_path, "r") as f:
            data = json.load(f)
        
        # Remove metadata key if present
        self._mapping = {k: v for k, v in data.items() if not k.startswith("_")}
        
        # Build normalized name lookup
        for name, info in self._mapping.items():
            normalized = DataLoader.normalize_restaurant_name(name)
            self._normalized_mapping[normalized.lower()] = {
                "original_name": name,
                **info,
            }
        
        logger.info(f"Loaded {len(self._mapping)} restaurant mappings")
    
    def get_camis(self, restaurant_name: str) -> str | None:
        """
        Get CAMIS ID for a restaurant name.
        
        Args:
            restaurant_name: Restaurant name from orders
            
        Returns:
            CAMIS ID or None if not found
        """
        # Try exact match first
        if restaurant_name in self._mapping:
            return self._mapping[restaurant_name].get("camis")
        
        # Try normalized match
        normalized = DataLoader.normalize_restaurant_name(restaurant_name).lower()
        if normalized in self._normalized_mapping:
            return self._normalized_mapping[normalized].get("camis")
        
        return None
    
    def get_restaurant_info(self, restaurant_name: str) -> dict[str, Any] | None:
        """
        Get full restaurant info from mapping.
        
        Args:
            restaurant_name: Restaurant name from orders
            
        Returns:
            Restaurant info dict or None if not found
        """
        # Try exact match first
        if restaurant_name in self._mapping:
            return {"name": restaurant_name, **self._mapping[restaurant_name]}
        
        # Try normalized match
        normalized = DataLoader.normalize_restaurant_name(restaurant_name).lower()
        if normalized in self._normalized_mapping:
            return self._normalized_mapping[normalized]
        
        return None
    
    def match_orders_to_inspections(
        self,
        orders_df: pd.DataFrame,
        inspections_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Match orders to inspection data via CAMIS IDs.
        
        Args:
            orders_df: Orders DataFrame with restaurant_name column
            inspections_df: Inspections DataFrame with camis column
            
        Returns:
            Merged DataFrame with matched data
        """
        if orders_df.empty:
            return pd.DataFrame()
        
        # Add CAMIS to orders
        orders_with_camis = orders_df.copy()
        orders_with_camis["camis"] = orders_with_camis["restaurant_name"].apply(
            self.get_camis
        )
        
        # Log matching stats
        matched = orders_with_camis["camis"].notna()
        logger.info(
            f"Matched {matched.sum()} of {len(orders_with_camis)} orders "
            f"({matched.mean()*100:.1f}%)"
        )
        
        if inspections_df.empty:
            return orders_with_camis
        
        # Get latest inspection per restaurant
        latest_inspections = self._get_latest_inspections(inspections_df)
        
        # Merge orders with latest inspection data
        merged = orders_with_camis.merge(
            latest_inspections,
            on="camis",
            how="left",
            suffixes=("", "_inspection"),
        )
        
        return merged
    
    def _get_latest_inspections(self, inspections_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the most recent inspection record per restaurant.
        
        Args:
            inspections_df: Full inspections DataFrame
            
        Returns:
            DataFrame with one row per CAMIS
        """
        if inspections_df.empty:
            return pd.DataFrame()
        
        # Sort by inspection date descending
        sorted_df = inspections_df.sort_values("inspection_date", ascending=False)
        
        # Take first record per CAMIS
        latest = sorted_df.groupby("camis").first().reset_index()
        
        # Select relevant columns
        cols_to_keep = [
            "camis", "dba", "boro", "grade", "grade_date", "score",
            "inspection_date", "action", "violation_code", "violation_description",
            "critical_flag", "inspection_type",
        ]
        
        available_cols = [c for c in cols_to_keep if c in latest.columns]
        return latest[available_cols]
    
    def get_matched_restaurant_count(self, orders_df: pd.DataFrame) -> int:
        """
        Count unique restaurants that can be matched.
        
        Args:
            orders_df: Orders DataFrame
            
        Returns:
            Number of unique matched restaurants
        """
        unique_names = orders_df["restaurant_name"].unique()
        matched = sum(1 for name in unique_names if self.get_camis(name) is not None)
        return matched
    
    def get_unmatched_restaurants(self, orders_df: pd.DataFrame) -> list[str]:
        """
        Get list of restaurant names that couldn't be matched.
        
        Args:
            orders_df: Orders DataFrame
            
        Returns:
            List of unmatched restaurant names
        """
        unique_names = orders_df["restaurant_name"].unique()
        return [name for name in unique_names if self.get_camis(name) is None]
    
    def get_all_mapped_camis(self) -> list[str]:
        """Get list of all CAMIS IDs in the mapping."""
        return [
            info["camis"]
            for info in self._mapping.values()
            if "camis" in info
        ]
    
    def enrich_orders_with_boro(self, orders_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add borough information to orders from mapping.
        
        Args:
            orders_df: Orders DataFrame
            
        Returns:
            DataFrame with boro column added
        """
        df = orders_df.copy()
        
        def get_boro(name: str) -> str | None:
            info = self.get_restaurant_info(name)
            return info.get("boro") if info else None
        
        df["boro"] = df["restaurant_name"].apply(get_boro)
        return df


