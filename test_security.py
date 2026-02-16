

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app
from app.models.database import Base, get_db
import app.models

# Use an in-memory SQLite database for testing, compatible with asyncio
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session():
    """
    Fixture to create an in-memory SQLite database for each test function.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session: AsyncSession):
    """
    Fixture to create a test client with an overridden database session.
    """
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    del fastapi_app.dependency_overrides[get_db]


@pytest.mark.asyncio
async def test_single_use_token_race_condition(client: AsyncClient):
    """
    Tests if a single-use token can be used multiple times concurrently.
    This test simulates a race condition using asyncio.
    """
    # Step 0: Create an API Key
    response = await client.post("/v1/test-key?owner=race_test")
    assert response.status_code == 200
    api_key = response.json()["key"]
    headers = {"X-API-Key": api_key}

    # Step 1: Create a single-use consent and get the delegation token
    consent_request = {
        "user_id": "race_user",
        "intent": {"description": "Test race condition"},
        "constraints": {"max_amount": 100, "currency": "USD"},
        "options": {"single_use": True, "expires_in_seconds": 60},
        "signature": "mock_sig",
        "public_key": "mock_pk"
    }
    response = await client.post("/v1/consents", json=consent_request, headers=headers)
    assert response.status_code == 201
    consent_data = response.json()
    delegation_token = consent_data["delegation_token"]

    # Step 2: Prepare concurrent authorization requests
    auth_request = {
        "delegation_token": delegation_token,
        "action": "payment",
        "transaction": {
            "amount": 10,
            "currency": "USD",
            "merchant_id": "race_merchant"
        }
    }

    # Step 3: Send 5 requests concurrently using asyncio.gather
    tasks = [client.post("/v1/authorize", json=auth_request, headers=headers) for _ in range(5)]
    responses = await asyncio.gather(*tasks)

    # Step 4: Analyze the results
    results = [res.json() for res in responses]
    successful_requests = [r for r in results if r.get("decision") == "ALLOW"]
    
    # In a vulnerable system, more than one of these might succeed.
    # A secure system should only allow one.
    assert len(successful_requests) == 1, f"Expected 1 successful request, but got {len(successful_requests)}"
    
    denied_requests = [r for r in results if r.get("decision") == "DENY"]
    assert len(denied_requests) == 4, f"Expected 4 denied requests, but got {len(denied_requests)}"



