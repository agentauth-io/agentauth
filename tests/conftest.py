"""
Pytest configuration and fixtures for AgentAuth tests.

Handles proper async test isolation and database connection management.
Uses in-memory SQLite for testing so no external PostgreSQL is required.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app as fastapi_app
from app.models.database import Base, get_db

# Import all models so their tables are registered on Base.metadata
import app.models  # noqa: F401

# In-memory SQLite for testing - no external database needed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function.

    This ensures proper isolation between async tests and prevents
    the 'attached to a different loop' errors with SQLAlchemy.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()

    # Allow tasks to complete cancellation
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    loop.close()


@pytest.fixture
def anyio_backend():
    """Configure anyio to use asyncio backend."""
    return "asyncio"


@pytest.fixture
async def test_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Provide a fresh database session for each test.

    Uses in-memory SQLite so no external database is required.
    """
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with proper lifecycle management.

    Uses ASGITransport to test the actual FastAPI app without
    running a real server. Overrides the database dependency to use
    in-memory SQLite. Includes a valid API key for authenticated requests.
    """
    from app.middleware.api_keys import generate_api_key

    # Generate a test API key
    key_data = generate_api_key(owner="test_user")
    test_api_key = key_data["key"]

    # Override get_db to use the test database
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0,
        headers={"X-API-Key": test_api_key},
    ) as ac:
        yield ac

    fastapi_app.dependency_overrides.pop(get_db, None)


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "db: marks tests that require database access"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that are slow"
    )
