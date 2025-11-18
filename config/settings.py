"""
Configuration Management System
Centralized settings for SEC filing analysis pipeline
"""
import os
from typing import Dict, List, Optional
from pydantic import BaseSettings, Field, validator


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_KEY")
    supabase_service_role_key: str = Field(..., env="SUPABASE_SERVICE_ROLE_KEY")

    # DuckDB
    duckdb_path: str = Field(default="./data/sec_filings.duckdb", env="DUCKDB_PATH")
    duckdb_memory_limit: str = Field(default="4GB", env="DUCKDB_MEMORY_LIMIT")

    class Config:
        env_file = ".env"
        case_sensitive = False


class SECEdgarSettings(BaseSettings):
    """SEC EDGAR API configuration"""
    base_url: str = Field(default="https://www.sec.gov/cgi-bin/browse-edgar", env="SEC_BASE_URL")
    user_agent: str = Field(..., env="SEC_USER_AGENT")  # Required by SEC
    rate_limit_requests: int = Field(default=10, env="SEC_RATE_LIMIT")
    rate_limit_period: int = Field(default=1, env="SEC_RATE_PERIOD_SECONDS")
    timeout: int = Field(default=30, env="SEC_TIMEOUT")

    class Config:
        env_file = ".env"


class ModelSettings(BaseSettings):
    """AI Model endpoint configuration"""
    # Primary models
    sonnet_endpoint: str = Field(..., env="SONNET_ENDPOINT")
    sonnet_api_key: str = Field(..., env="SONNET_API_KEY")

    haiku_endpoint: str = Field(..., env="HAIKU_ENDPOINT")
    haiku_api_key: str = Field(..., env="HAIKU_API_KEY")

    opus_endpoint: Optional[str] = Field(None, env="OPUS_ENDPOINT")
    opus_api_key: Optional[str] = Field(None, env="OPUS_API_KEY")

    # Model selection thresholds
    complexity_threshold_high: float = Field(default=0.7, env="COMPLEXITY_THRESHOLD_HIGH")
    complexity_threshold_medium: float = Field(default=0.4, env="COMPLEXITY_THRESHOLD_MEDIUM")

    # Retry settings
    max_retries: int = Field(default=3, env="MODEL_MAX_RETRIES")
    retry_delay: int = Field(default=2, env="MODEL_RETRY_DELAY")

    class Config:
        env_file = ".env"


class CelerySettings(BaseSettings):
    """Celery task queue configuration"""
    broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # Task settings
    task_serializer: str = Field(default="json")
    result_serializer: str = Field(default="json")
    accept_content: List[str] = Field(default=["json"])
    timezone: str = Field(default="UTC")
    enable_utc: bool = Field(default=True)

    # Concurrency
    worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")
    worker_prefetch_multiplier: int = Field(default=4, env="CELERY_PREFETCH_MULTIPLIER")

    # Rate limits
    task_default_rate_limit: str = Field(default="100/m", env="CELERY_RATE_LIMIT")

    class Config:
        env_file = ".env"


class SignalSettings(BaseSettings):
    """Signal extraction configuration"""
    # Financial signals (50 signals)
    enable_financial_signals: bool = Field(default=True)
    financial_signal_count: int = Field(default=50)

    # Sentiment signals (30 signals)
    enable_sentiment_signals: bool = Field(default=True)
    sentiment_signal_count: int = Field(default=30)

    # Risk signals (40 signals)
    enable_risk_signals: bool = Field(default=True)
    risk_signal_count: int = Field(default=40)

    # Management signals (30 signals)
    enable_management_signals: bool = Field(default=True)
    management_signal_count: int = Field(default=30)

    # Total: 150 signals

    class Config:
        env_file = ".env"


class MonitoringSettings(BaseSettings):
    """Monitoring and logging configuration"""
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Metrics
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8000, env="METRICS_PORT")

    # Alerting
    enable_alerts: bool = Field(default=True, env="ENABLE_ALERTS")
    alert_email: Optional[str] = Field(None, env="ALERT_EMAIL")

    class Config:
        env_file = ".env"


class Settings(BaseSettings):
    """Master configuration"""
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    sec_edgar: SECEdgarSettings = SECEdgarSettings()
    models: ModelSettings = ModelSettings()
    celery: CelerySettings = CelerySettings()
    signals: SignalSettings = SignalSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    class Config:
        env_file = ".env"

    @validator("environment")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment"""
    global _settings
    _settings = Settings()
    return _settings
