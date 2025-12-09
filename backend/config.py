"""Configuration settings for the RatChallenge backend."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    app_name: str = "RatChallenge API"
    debug: bool = False
    
    # NYC Open Data API
    nyc_api_base_url: str = "https://data.cityofnewyork.us/resource/43nn-pn8j.json"
    nyc_api_app_token: str | None = None  # Optional, increases rate limit
    
    # Data paths
    csv_path: Path = Path(__file__).parent.parent / "food_orders.csv"
    mapping_path: Path = Path(__file__).parent / "data" / "restaurant_mapping.json"
    cache_path: Path = Path(__file__).parent / "data" / "inspections_cache.parquet"
    
    # Cache settings
    cache_max_age_days: int = 7  # Refresh cache if older than this
    
    # CORS - can be overridden via CORS_ORIGINS env var (comma-separated)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


