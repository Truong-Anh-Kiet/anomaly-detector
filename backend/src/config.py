"""Configuration and settings for Anomaly Detector API"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Application
    app_name: str = "Anomaly Detection Dashboard API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./anomaly_detector.db"
    database_echo: bool = False
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Batch Processing
    batch_job_hour: int = 2  # 2 AM UTC
    batch_job_minute: int = 0
    batch_window_minutes: int = 60  # 1 hour window
    
    # Model
    model_path: str = "./models/anomaly_model.pkl"
    model_check_interval_minutes: int = 60  # Check for new model every hour

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or plain

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

    # Pagination
    default_page_size: int = 50
    max_page_size: int = 500

    class Config:
        """Pydantic settings configuration"""
        env_file = ".env"
        case_sensitive = False
        # Allow both snake_case and camelCase
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
