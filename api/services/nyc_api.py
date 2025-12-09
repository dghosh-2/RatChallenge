"""NYC Restaurant Inspection API client - Direct API calls, no caching."""

import logging
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger(__name__)


class NYCInspectionAPI:
    """Client for NYC DOHMH Restaurant Inspection Results API using SODA API."""
    
    # SODA API pagination limit
    BATCH_SIZE = 10000  # Smaller batches for serverless timeout limits
    MAX_RECORDS = 200000  # Limit for serverless function timeout
    
    def __init__(self, base_url: str, app_token: str | None = None):
        """
        Initialize the NYC API client.
        
        Args:
            base_url: Base URL for the NYC Open Data SODA API
            app_token: Optional Socrata app token for higher rate limits
        """
        self.base_url = base_url
        self.app_token = app_token
        self._client: httpx.AsyncClient | None = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            headers = {}
            if self.app_token:
                headers["X-App-Token"] = self.app_token
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
    
    async def fetch_inspections(
        self,
        limit: int = 10000,
        offset: int = 0,
        where: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch inspection records from the SODA API.
        
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
            data = response.json()
            
            # SODA API returns a list directly
            if isinstance(data, list):
                return data
            
            logger.warning(f"Unexpected API response format: {type(data)}")
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching inspections: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error fetching inspections: {e}")
            raise
    
    async def fetch_all_inspections(self) -> pd.DataFrame:
        """
        Fetch inspection records with pagination.
        No caching - calls API directly every time.
        Limited to avoid serverless timeout.
        
        Returns:
            DataFrame with inspection records
        """
        all_records: list[dict[str, Any]] = []
        offset = 0
        
        logger.info("Starting to fetch NYC inspection data from SODA API...")
        
        while offset < self.MAX_RECORDS:
            try:
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
            except Exception as e:
                logger.error(f"Error fetching batch at offset {offset}: {e}")
                break
        
        logger.info(f"Total inspection records fetched: {len(all_records)}")
        
        if not all_records:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_records)
        df = self._clean_inspection_data(df)
        
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
