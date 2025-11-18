"""
Security Configuration
Centralized security settings for the application
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
from enum import Enum
import os


class Environment(str, Enum):
    """Deployment environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityConfig(BaseSettings):
    """Security configuration settings"""

    # Environment
    environment: Environment = Environment.DEVELOPMENT

    # JWT Configuration
    jwt_secret_key: str = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # API Key Configuration
    api_key_secret: str = os.environ.get("API_KEY_SECRET", "your-api-key-secret")
    api_key_prefix: str = "sk_"
    api_key_default_expiry_days: int = 90

    # Encryption Configuration
    encryption_master_key: Optional[str] = os.environ.get("ENCRYPTION_MASTER_KEY")

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 120

    # Custom rate limits per endpoint
    rate_limit_filings: int = 100
    rate_limit_predictions: int = 60
    rate_limit_signals: int = 120

    # CORS Configuration
    cors_allow_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_max_age: int = 600

    # Security Headers
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    frame_options: str = "DENY"
    content_type_options_enabled: bool = True
    xss_protection_enabled: bool = True
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Content Security Policy
    csp_enabled: bool = True
    csp_default_src: List[str] = ["'self'"]
    csp_script_src: List[str] = ["'self'", "'unsafe-inline'"]
    csp_style_src: List[str] = ["'self'", "'unsafe-inline'"]

    # Audit Logging
    audit_log_enabled: bool = True
    audit_log_file: str = "logs/audit.log"
    audit_log_json_format: bool = True

    # Secrets Management
    secrets_provider: str = "environment"  # environment, vault, aws_secrets_manager
    vault_addr: Optional[str] = os.environ.get("VAULT_ADDR")
    vault_token: Optional[str] = os.environ.get("VAULT_TOKEN")
    vault_mount_point: str = "secret"

    # AWS Secrets Manager
    aws_region: str = "us-east-1"

    # TLS Configuration
    tls_enabled: bool = False  # Enable in production
    tls_cert_file: Optional[str] = None
    tls_key_file: Optional[str] = None
    tls_min_version: str = "TLSv1.3"

    # IP Whitelisting
    ip_whitelist_enabled: bool = False
    ip_whitelist: List[str] = []

    # Security Monitoring
    failed_login_threshold: int = 5
    failed_login_lockout_minutes: int = 15
    suspicious_activity_threshold: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global security config instance
_config: Optional[SecurityConfig] = None


def get_security_config() -> SecurityConfig:
    """
    Get security configuration

    Returns:
        SecurityConfig instance
    """
    global _config
    if _config is None:
        _config = SecurityConfig()
    return _config


def reload_security_config():
    """Reload security configuration from environment"""
    global _config
    _config = SecurityConfig()


# Validation on module import
config = get_security_config()

# Validate production settings
if config.environment == Environment.PRODUCTION:
    warnings = []

    if config.jwt_secret_key == "your-secret-key-change-in-production":
        warnings.append("JWT_SECRET_KEY not set for production")

    if config.api_key_secret == "your-api-key-secret":
        warnings.append("API_KEY_SECRET not set for production")

    if not config.encryption_master_key:
        warnings.append("ENCRYPTION_MASTER_KEY not set for production")

    if not config.tls_enabled:
        warnings.append("TLS not enabled for production")

    if "*" in config.cors_allow_origins:
        warnings.append("CORS allows all origins in production")

    if warnings:
        import logging
        logger = logging.getLogger(__name__)
        for warning in warnings:
            logger.warning(f"SECURITY WARNING: {warning}")
