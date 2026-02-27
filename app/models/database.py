"""
Database connection and session management

OPTIMIZED for low-latency authorization:
- Connection pooling (5-20 connections)
- Pool pre-ping for connection health
- Fast timeout settings
"""
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Create SSL context for PostgreSQL connections
ssl_context = ssl.create_default_context()
if settings.environment == "development":
    # Relaxed SSL for local/Neon dev poolers
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
# In production, ssl_context uses system CA certs with full verification by default

# Process DATABASE_URL for asyncpg compatibility
db_url = settings.database_url

# Remove query params (we'll handle SSL via connect_args)
db_url = db_url.split("?")[0]

# Convert various URL formats to postgresql+asyncpg://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif not db_url.startswith("postgresql+asyncpg://"):
    # If it's already asyncpg format, use as-is
    pass

# Log at debug level - never print DB URLs
import logging as _db_logging

_db_logging.getLogger(__name__).debug(f"Database URL configured (length={len(db_url)})")

# Create async engine with OPTIMIZED connection pooling
engine = create_async_engine(
    db_url,
    echo=settings.debug,
    future=True,
    connect_args={"ssl": ssl_context},
    # Connection pool settings for low latency
    pool_size=5,           # Minimum connections to keep ready
    max_overflow=15,       # Allow up to 20 total connections
    pool_pre_ping=False,   # Disabled - causes issues with Neon pooler
    pool_recycle=300,      # Recycle connections every 5 mins
    pool_timeout=10,       # Wait max 10s for connection
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for backward compatibility (health check imports this name)
async_engine = engine


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
