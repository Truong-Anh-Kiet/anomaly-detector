"""Configuration and settings for Anomaly Detector API"""

from functools import lru_cache

from pydantic_settings import BaseSettings


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
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5000"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

    # Pagination
    default_page_size: int = 50
    max_page_size: int = 500

    # Audit Logging
    audit_log_retention_days: int = 365
    audit_log_archive_threshold: int = 365
    audit_log_hard_delete_threshold: int = 730

    # Anomaly Detection Thresholds
    default_anomaly_threshold: float = 0.7
    default_sensitivity: float = 0.8
    min_sequence_length: int = 5
    max_sequence_length: int = 100
    detection_batch_size: int = 32

    # API Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_period_seconds: int = 60

    # Monitoring & Metrics
    enable_prometheus_metrics: bool = True
    metrics_port: int = 8001
    enable_performance_monitoring: bool = True

    # Data Export
    max_export_records: int = 100000
    export_batch_size: int = 5000

    # Email (for alerts)
    email_enabled: bool = False
    email_host: str = ""
    email_port: int = 587
    email_user: str = ""
    email_password: str = ""
    alert_emails: list = []

    # Environment
    environment: str = "development"  # development, staging, production

    class Config:
        """Pydantic settings configuration"""
        env_file = ".env"
        case_sensitive = False
        # Allow both snake_case and camelCase
        populate_by_name = True


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


class ApprovedThresholds:
    """Pre-approved threshold configurations by category"""

    THRESHOLDS = {
        "payment": {
            "min": 0.5,
            "max": 0.95,
            "default": 0.75,
            "description": "Payment transaction anomalies",
        },
        "network": {
            "min": 0.6,
            "max": 0.95,
            "default": 0.80,
            "description": "Network/login anomalies",
        },
        "behavioral": {
            "min": 0.55,
            "max": 0.95,
            "default": 0.70,
            "description": "User behavior anomalies",
        },
        "system": {
            "min": 0.65,
            "max": 0.95,
            "default": 0.85,
            "description": "System performance anomalies",
        },
    }

    @staticmethod
    def get_threshold_range(category: str) -> dict:
        """Get valid threshold range for a category"""
        return ApprovedThresholds.THRESHOLDS.get(
            category,
            {
                "min": 0.5,
                "max": 0.95,
                "default": 0.7,
                "description": "Default category",
            },
        )

    @staticmethod
    def validate_threshold(category: str, threshold: float) -> bool:
        """Check if threshold is within approved range"""
        range_config = ApprovedThresholds.get_threshold_range(category)
        return range_config["min"] <= threshold <= range_config["max"]


class FeatureFlags:
    """Feature toggles for experimental features"""

    FLAGS = {
        "advanced_ml_features": False,
        "real_time_detection": False,
        "predictive_alerts": False,
        "export_to_s3": False,
        "email_notifications": False,
        "audit_log_archival": True,
    }

    @staticmethod
    def is_enabled(flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return FeatureFlags.FLAGS.get(flag_name, False)

    @staticmethod
    def enable_flag(flag_name: str):
        """Enable a feature flag"""
        if flag_name in FeatureFlags.FLAGS:
            FeatureFlags.FLAGS[flag_name] = True

    @staticmethod
    def disable_flag(flag_name: str):
        """Disable a feature flag"""
        if flag_name in FeatureFlags.FLAGS:
            FeatureFlags.FLAGS[flag_name] = False
