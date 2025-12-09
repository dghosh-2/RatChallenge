"""Data loader for food orders CSV."""

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DataLoader:
    """Loader for food order CSV data with name normalization."""
    
    # Suffixes to strip from restaurant names for matching
    NAME_SUFFIXES = [
        r"\s*-\s*CLOSED\s*$",
        r"\s*-\s*\$\d+(\.\d+)?\s+off.*$",
        r"\s*\$\d+(\.\d+)?\s+Delivery\s*(Fee)?\s*$",
        r"\s*\(archived\)\s*$",
        r"\s*-\s*Midtown\s*$",
        r"\s*-\s*Downtown\s*$",
        r"\s*-\s*UES\s*$",
        r"\s*-\s*UWS\s*$",
        r"\s*-\s*Brooklyn\s*$",
        r"\s*-\s*Manhattan\s*$",
        r"\s+Broadway\s*$",
        r"\s+Hudson\s*$",
    ]
    
    def __init__(self, csv_path: Path | str):
        """
        Initialize the data loader.
        
        Args:
            csv_path: Path to the food orders CSV file
        """
        self.csv_path = Path(csv_path)
        self._orders_df: pd.DataFrame | None = None
    
    def load_orders(self) -> pd.DataFrame:
        """
        Load and process the food orders CSV.
        
        Returns:
            DataFrame with processed order data
        """
        if self._orders_df is not None:
            return self._orders_df
        
        logger.info(f"Loading orders from {self.csv_path}")
        
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Orders CSV not found: {self.csv_path}")
        
        df = pd.read_csv(self.csv_path)
        
        # Clean and process
        df = self._clean_orders(df)
        
        # Add normalized restaurant name for matching
        df["restaurant_name_normalized"] = df["restaurant_name"].apply(
            self.normalize_restaurant_name
        )
        
        self._orders_df = df
        logger.info(f"Loaded {len(df)} orders from {df['restaurant_name'].nunique()} restaurants")
        
        return df
    
    def _clean_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and validate order data.
        
        Args:
            df: Raw orders DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Ensure required columns exist
        required_cols = [
            "order_id", "customer_id", "restaurant_name", "cuisine_type",
            "cost_of_the_order", "day_of_the_week", "rating",
            "food_preparation_time", "delivery_time"
        ]
        
        missing = set(required_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Convert cost to float
        df["cost_of_the_order"] = pd.to_numeric(df["cost_of_the_order"], errors="coerce")
        
        # Clean restaurant names (strip whitespace, handle quotes)
        df["restaurant_name"] = (
            df["restaurant_name"]
            .astype(str)
            .str.strip()
            .str.strip('"')
            .str.strip()
        )
        
        # Clean cuisine type
        df["cuisine_type"] = df["cuisine_type"].astype(str).str.strip()
        
        # Convert rating to numeric (handle "Not given")
        df["rating_numeric"] = pd.to_numeric(
            df["rating"].replace("Not given", None),
            errors="coerce"
        )
        
        # Convert time columns to numeric
        for col in ["food_preparation_time", "delivery_time"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        # Drop rows with invalid cost
        invalid_cost = df["cost_of_the_order"].isna()
        if invalid_cost.any():
            logger.warning(f"Dropping {invalid_cost.sum()} rows with invalid cost")
            df = df[~invalid_cost].copy()
        
        return df
    
    @classmethod
    def normalize_restaurant_name(cls, name: str) -> str:
        """
        Normalize a restaurant name for matching.
        
        Removes common suffixes like "- CLOSED", "$0 Delivery Fee", etc.
        
        Args:
            name: Raw restaurant name
            
        Returns:
            Normalized name for matching
        """
        if not name or not isinstance(name, str):
            return ""
        
        # Strip whitespace and quotes
        normalized = name.strip().strip('"').strip()
        
        # Remove common suffixes
        for pattern in cls.NAME_SUFFIXES:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)
        
        # Final cleanup
        normalized = normalized.strip()
        
        return normalized
    
    def get_unique_restaurants(self) -> pd.DataFrame:
        """
        Get unique restaurants with their order statistics.
        
        Returns:
            DataFrame with one row per restaurant
        """
        if self._orders_df is None:
            self.load_orders()
        
        df = self._orders_df
        
        stats = df.groupby("restaurant_name").agg({
            "order_id": "count",
            "cost_of_the_order": "sum",
            "cuisine_type": "first",
            "rating_numeric": "mean",
            "restaurant_name_normalized": "first",
        }).reset_index()
        
        stats.columns = [
            "restaurant_name", "order_count", "total_revenue",
            "cuisine_type", "avg_rating", "normalized_name"
        ]
        
        return stats.sort_values("total_revenue", ascending=False)
    
    def get_orders_by_restaurant(self, restaurant_name: str) -> pd.DataFrame:
        """
        Get all orders for a specific restaurant.
        
        Args:
            restaurant_name: Name of the restaurant
            
        Returns:
            DataFrame with orders for that restaurant
        """
        if self._orders_df is None:
            self.load_orders()
        
        return self._orders_df[
            self._orders_df["restaurant_name"] == restaurant_name
        ].copy()
    
    def get_total_revenue(self) -> float:
        """Get total revenue across all orders."""
        if self._orders_df is None:
            self.load_orders()
        
        return float(self._orders_df["cost_of_the_order"].sum())
    
    def get_total_orders(self) -> int:
        """Get total number of orders."""
        if self._orders_df is None:
            self.load_orders()
        
        return len(self._orders_df)


