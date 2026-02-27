"""
AgentAuth Configuration

All secrets MUST be provided via environment variables.
Auto-generates secure defaults if not set (for easier deployment).
"""
import os
import secrets
from functools import lru_cache

import bcrypt
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings

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

    @field_validator("admin_password")
    @classmethod
    def validate_admin_password_complexity(cls, v: str) -> str:
        """Validate admin password meets minimum security requirements."""
        if v and len(v) < 12:
            raise ValueError("ADMIN_PASSWORD must be at least 12 characters long")
        if v and not any(c.isupper() for c in v):
            raise ValueError("ADMIN_PASSWORD must contain at least one uppercase letter")
        if v and not any(c.isdigit() for c in v):
            raise ValueError("ADMIN_PASSWORD must contain at least one digit")
        if v and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("ADMIN_PASSWORD must contain at least one special character")
        return v

    @field_validator("secret_key", "admin_password", "admin_jwt_secret")
    @classmethod
    def validate_secrets(cls, v: str, info) -> str:
        """Auto-generate secrets if not provided (development only)."""
        if not v:
            # In production, require explicit secrets from environment
            # Check if we're in production mode
            env_is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
            if env_is_production:
                raise ValueError(
                    f"{info.field_name} must be set via environment variable in production. "
                    f"Set {info.field_name.upper()} in your .env file."
                )
            # Development: use runtime-generated secure defaults
            return _RUNTIME_SECRETS.get(info.field_name, secrets.token_urlsafe(32))
        return v

    @field_validator("environment")
    @classmethod
    def validate_production_config(cls, v: str, info) -> str:
        """In production, ensure critical env vars are explicitly set."""
        if v == "production":
            import logging
            logger = logging.getLogger(__name__)
            data = info.data
            db_url = data.get("database_url", "")
            if "localhost" in db_url or not db_url:
                raise ValueError("DATABASE_URL must be set to a real database in production")
            if not data.get("stripe_secret_key"):
                logger.warning(
                    "STRIPE_SECRET_KEY not set in production — billing features disabled"
                )
            if not data.get("sentry_dsn"):
                logger.warning(
                    "SENTRY_DSN not set in production — error tracking disabled"
                )
        return v

    @property
    def admin_password_bcrypt(self) -> bytes:
        """Get bcrypt hash of admin password (computed once, cached)."""
        if not hasattr(self, "_admin_pw_hash"):
            object.__setattr__(
                self, "_admin_pw_hash",
                bcrypt.hashpw(self.admin_password.encode(), bcrypt.gensalt())
            )
        return self._admin_pw_hash

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
