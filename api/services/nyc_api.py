"""NYC Restaurant Inspection API client with Vercel Blob storage caching."""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


class NYCInspectionAPI:
    """Client for NYC DOHMH Restaurant Inspection Results API."""
    
    # Socrata API pagination limit
    BATCH_SIZE = 50000
    MAX_RECORDS = 500000  # Safety limit
    CACHE_BLOB_KEY = "nyc-inspections-cache.json"
    CACHE_MAX_AGE_DAYS = 7
    
    def __init__(self, base_url: str, app_token: str | None = None):
        """
        Initialize the NYC API client.
        
        Args:
            base_url: Base URL for the NYC Open Data API
            app_token: Optional Socrata app token for higher rate limits
        """
        self.base_url = base_url
        self.app_token = app_token
        self._client: httpx.AsyncClient | None = None
        self.blob_token = os.environ.get("BLOB_READ_WRITE_TOKEN")
        self.blob_store_id = os.environ.get("BLOB_STORE_ID")
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            if self.app_token:
                headers["X-App-Token"] = self.app_token
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def fetch_inspections(
        self,
        limit: int = 50000,
        offset: int = 0,
        where: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch inspection records from the API.
        
        Args:
            limit: Maximum number of records to fetch
            offset: Offset for pagination
            where: Optional SoQL WHERE clause
            
        Returns:
            List of inspection records
        """
        params = {
            "$limit": limit,
            "$offset": offset,
            "$order": "inspection_date DESC",
        }
        
        if where:
            params["$where"] = where
        
        try:
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching inspections: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching inspections: {e}")
            raise
    
    async def load_from_cache(self) -> pd.DataFrame | None:
        """
        Load inspection data from Vercel Blob storage if available and fresh.
        
        Returns:
            DataFrame if cache exists and is fresh, None otherwise
        """
        if not self.blob_token or not self.blob_store_id:
            logger.info("Vercel Blob credentials not available, skipping cache")
            return None
        
        try:
            # Use Vercel Blob REST API to check and fetch
            blob_url = f"https://{self.blob_store_id}.public.blob.vercel-storage.com/{self.CACHE_BLOB_KEY}"
            
            async with httpx.AsyncClient() as blob_client:
                # Try to fetch the blob
                response = await blob_client.get(
                    blob_url,
                    headers={"Authorization": f"Bearer {self.blob_token}"},
                    timeout=10.0,
                )
                
                if response.status_code == 404:
                    logger.info("No cache blob found")
                    return None
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch cache: {response.status_code}")
                    return None
                
                # Check cache age from headers
                last_modified = response.headers.get("last-modified")
                if last_modified:
                    cache_time = datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                    cache_age = datetime.now(cache_time.tzinfo) - cache_time
                    if cache_age > timedelta(days=self.CACHE_MAX_AGE_DAYS):
                        logger.info(f"Cache is {cache_age.days} days old, will refresh")
                        return None
                
                # Parse JSON and convert to DataFrame
                records = response.json()
                df = pd.DataFrame(records)
                
                # Convert date columns back
                date_cols = ["inspection_date", "grade_date"]
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                
                logger.info(f"Loaded {len(df)} records from Vercel Blob cache")
                return df
        except Exception as e:
            logger.warning(f"Failed to load cache from Vercel Blob: {e}, will fetch from API")
            return None
    
    async def save_to_cache(self, df: pd.DataFrame) -> None:
        """
        Save inspection data to Vercel Blob storage.
        
        Args:
            df: DataFrame to cache
        """
        if not self.blob_token or not self.blob_store_id:
            logger.info("Vercel Blob credentials not available, skipping cache save")
            return
        
        try:
            # Convert DataFrame to JSON-serializable format
            # Convert dates to ISO strings for JSON serialization
            df_copy = df.copy()
            date_cols = ["inspection_date", "grade_date"]
            for col in date_cols:
                if col in df_copy.columns:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: x.isoformat() if pd.notna(x) else None
                    )
            
            # Convert to records (list of dicts)
            records = df_copy.to_dict(orient="records")
            json_data = json.dumps(records)
            
            # Upload to Vercel Blob using REST API
            blob_url = f"https://blob.vercel-storage.com/{self.CACHE_BLOB_KEY}"
            
            async with httpx.AsyncClient() as blob_client:
                response = await blob_client.put(
                    blob_url,
                    content=json_data.encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self.blob_token}",
                        "Content-Type": "application/json",
                        "x-store-id": self.blob_store_id,
                    },
                    timeout=60.0,
                )
                
                if response.status_code == 200:
                    logger.info(f"Saved {len(df)} records to Vercel Blob cache")
                else:
                    logger.warning(f"Failed to save cache: {response.status_code} {response.text}")
        except Exception as e:
            logger.warning(f"Failed to save cache to Vercel Blob: {e}")
    
    async def fetch_all_inspections(self, use_cache: bool = True) -> pd.DataFrame:
        """
        Fetch all inspection records with pagination, using Vercel Blob cache if available.
        
        Args:
            use_cache: Whether to use cache if available
            
        Returns:
            DataFrame with all inspection records
        """
        # Try to load from cache first
        if use_cache:
            cached_df = await self.load_from_cache()
            if cached_df is not None:
                return cached_df
        
        # Fetch from API
        all_records: list[dict[str, Any]] = []
        offset = 0
        
        logger.info("Starting to fetch NYC inspection data from API...")
        
        while offset < self.MAX_RECORDS:
            batch = await self.fetch_inspections(
                limit=self.BATCH_SIZE,
                offset=offset,
            )
            
            if not batch:
                break
            
            all_records.extend(batch)
            logger.info(f"Fetched {len(all_records)} records so far...")
            
            if len(batch) < self.BATCH_SIZE:
                break
            
            offset += self.BATCH_SIZE
        
        logger.info(f"Total inspection records fetched: {len(all_records)}")
        
        if not all_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        df = self._clean_inspection_data(df)
        
        # Save to cache
        await self.save_to_cache(df)
        
        return df
    
    async def fetch_inspections_by_camis(self, camis_ids: list[str]) -> pd.DataFrame:
        """
        Fetch inspection records for specific CAMIS IDs.
        
        Args:
            camis_ids: List of CAMIS IDs to fetch
            
        Returns:
            DataFrame with inspection records for the specified restaurants
        """
        if not camis_ids:
            return pd.DataFrame()
        
        # Build SoQL WHERE clause for CAMIS IDs
        camis_list = ",".join(f"'{c}'" for c in camis_ids)
        where = f"camis IN ({camis_list})"
        
        all_records: list[dict[str, Any]] = []
        offset = 0
        
        while True:
            batch = await self.fetch_inspections(
                limit=self.BATCH_SIZE,
                offset=offset,
                where=where,
            )
            
            if not batch:
                break
            
            all_records.extend(batch)
            
            if len(batch) < self.BATCH_SIZE:
                break
            
            offset += self.BATCH_SIZE
        
        if not all_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        df = self._clean_inspection_data(df)
        
        return df
    
    def _clean_inspection_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and normalize inspection data.
        
        Args:
            df: Raw inspection DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Ensure required columns exist
        required_cols = [
            "camis", "dba", "boro", "building", "street", "zipcode",
            "cuisine_description", "inspection_date", "action",
            "violation_code", "violation_description", "critical_flag",
            "score", "grade", "grade_date", "inspection_type",
        ]
        
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Convert CAMIS to string (preserve leading zeros)
        df["camis"] = df["camis"].astype(str)
        
        # Convert dates
        date_cols = ["inspection_date", "grade_date"]
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        # Normalize text fields
        text_cols = ["dba", "boro", "violation_description", "action"]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.upper().str.strip()
        
        # Convert score to numeric
        if "score" in df.columns:
            df["score"] = pd.to_numeric(df["score"], errors="coerce")
        
        # Normalize grade
        if "grade" in df.columns:
            df["grade"] = df["grade"].fillna("").astype(str).str.upper().str.strip()
        
        return df
    
    def identify_rodent_violations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter for rodent-related violations.
        
        Args:
            df: Inspection DataFrame
            
        Returns:
            DataFrame with only rodent violations
        """
        if df.empty or "violation_description" not in df.columns:
            return pd.DataFrame()
        
        rodent_keywords = ["RODENT", "RAT", "MICE", "MOUSE", "VERMIN"]
        pattern = "|".join(rodent_keywords)
        
        mask = df["violation_description"].str.contains(pattern, case=False, na=False)
        return df[mask].copy()
    
    def identify_critical_violations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter for critical violations.
        
        Args:
            df: Inspection DataFrame
            
        Returns:
            DataFrame with only critical violations
        """
        if df.empty or "critical_flag" not in df.columns:
            return pd.DataFrame()
        
        mask = df["critical_flag"].str.upper() == "CRITICAL"
        return df[mask].copy()
    
    def get_latest_grades(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the latest grade for each restaurant.
        
        Args:
            df: Inspection DataFrame
            
        Returns:
            DataFrame with one row per restaurant showing latest grade
        """
        if df.empty:
            return pd.DataFrame()
        
        # Filter to only graded inspections
        graded = df[df["grade"].isin(["A", "B", "C", "Z", "P", "N"])].copy()
        
        if graded.empty:
            return pd.DataFrame()
        
        # Sort by grade_date descending and take first per CAMIS
        graded = graded.sort_values("grade_date", ascending=False)
        latest = graded.groupby("camis").first().reset_index()
        
        return latest[["camis", "dba", "boro", "grade", "grade_date", "score"]]
    
    def identify_closed_restaurants(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Identify restaurants that were closed or re-closed.
        
        Args:
            df: Inspection DataFrame
            
        Returns:
            DataFrame with restaurants that have closure actions
        """
        if df.empty or "action" not in df.columns:
            return pd.DataFrame()
        
        closure_keywords = ["CLOSED", "RE-CLOSED", "RECLOSED"]
        pattern = "|".join(closure_keywords)
        
        mask = df["action"].str.contains(pattern, case=False, na=False)
        return df[mask].copy()
