"""
AgentAuth Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/agentauth"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    
    # Token settings
    token_expiry_seconds: int = 3600  # 1 hour
    auth_code_expiry_seconds: int = 300  # 5 minutes
    
    # Application
    debug: bool = False
    environment: str = "development"
    
    # JWT settings
    jwt_algorithm: str = "HS256"
    
    # Stripe settings (use test keys in development)
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_enterprise: str = ""
    
    # Admin panel settings
    admin_password: str = "agentauth2026"  # Change in production!
    admin_jwt_secret: str = "admin-secret-change-in-production"
    admin_token_expiry: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
