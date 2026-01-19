"""
Pytest configuration and fixtures for AgentAuth tests.

Handles proper async test isolation and database connection management.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Import app factory - we'll create fresh instances per test
from app.main import app
from app.models.database import engine


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
async def db_session():
    """Provide a fresh database session for each test.
    
    Properly closes the session after the test completes.
    """
    from app.models.database import async_session_maker
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with proper lifecycle management.
    
    Uses ASGITransport to test the actual FastAPI app without
    running a real server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        timeout=30.0  # Increase timeout for DB operations
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
async def reset_db_connections():
    """Reset database connection pool between tests.
    
    This helps prevent connection pool exhaustion and ensures
    each test starts with fresh connections.
    """
    yield
    # After each test, dispose of connections to reset pool
    await engine.dispose()


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "db: marks tests that require database access"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that are slow"
    )
