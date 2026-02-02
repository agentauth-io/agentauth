"""
AgentAuth Configuration

All secrets MUST be provided via environment variables.
Auto-generates secure defaults if not set (for easier deployment).
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional, List
import os
import secrets


# Generate secure runtime defaults (persists for app lifetime)
_RUNTIME_SECRETS = {
    "secret_key": secrets.token_urlsafe(32),
    "admin_password": secrets.token_urlsafe(24),
    "admin_jwt_secret": secrets.token_urlsafe(32),
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database (REQUIRED)
    database_url: str = "postgresql+asyncpg://localhost:5432/agentauth"
    
    # Security - auto-generated if not set
    secret_key: str = ""
    
    # Token settings
    token_expiry_seconds: int = 3600  # 1 hour
    auth_code_expiry_seconds: int = 300  # 5 minutes
    
    # Application
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"
    log_json: bool = False  # True for production
    
    # CORS - comma-separated list of allowed origins
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,https://agentauth.in,https://www.agentauth.in"
    
    # JWT settings
    jwt_algorithm: str = "HS256"
    
    # Stripe settings (use test keys in development)
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_enterprise: str = ""
    
    # Admin panel settings - auto-generated if not set
    admin_password: str = ""
    admin_jwt_secret: str = ""
    admin_token_expiry: int = 3600  # 1 hour
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_password: str = ""
    redis_db: int = 0
    redis_ssl: bool = False
    
    # Rate limiting
    rate_limit_requests_per_second: int = 100
    rate_limit_burst: int = 200
    
    # Caching
    cache_ttl_seconds: int = 300  # 5 minutes default
    cache_consent_ttl: int = 600  # 10 minutes for consents
    
    # Monitoring
    sentry_dsn: str = ""  # Optional - for error tracking
    
    @field_validator("secret_key", "admin_password", "admin_jwt_secret")
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """Auto-generate secrets if not provided."""
        if not v:
            # Use runtime-generated secure defaults
            return _RUNTIME_SECRETS.get(info.field_name, secrets.token_urlsafe(32))
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars without validation errors


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
