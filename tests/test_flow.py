"""
End-to-end flow tests for AgentAuth

Tests the complete flow:
1. Create consent
2. Authorize transaction
3. Verify authorization

Fixtures are defined in conftest.py for proper test isolation.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime
import uuid

# Note: app import moved to conftest.py to avoid module-level side effects
# Fixtures (client, event_loop, db_session) are in conftest.py


class TestHealthCheck:
    """Test health endpoint."""
    
    @pytest.mark.anyio
    async def test_health(self, client: AsyncClient):
        """Test health check returns healthy."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    @pytest.mark.anyio
    async def test_root(self, client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentAuth"
        assert "version" in data


class TestTokenService:
    """Test token generation and verification."""
    
    def test_create_and_verify_token(self):
        """Test creating and verifying a delegation token."""
        from app.services.token_service import token_service
        
        # Create token
        token = token_service.create_delegation_token(
            consent_id="cons_test123",
            user_id="user_123",
            intent_description="Buy flight to NYC",
            max_amount=500.0,
            currency="USD",
        )
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token without transaction
        result = token_service.verify_token(token)
        assert result.valid is True
        assert result.payload.consent_id == "cons_test123"
        assert result.payload.max_amount == 500.0
    
    def test_token_amount_check(self):
        """Test that amount constraint is enforced."""
        from app.services.token_service import token_service
        
        token = token_service.create_delegation_token(
            consent_id="cons_test123",
            user_id="user_123",
            intent_description="Buy flight",
            max_amount=500.0,
            currency="USD",
        )
        
        # Under limit - should pass
        result = token_service.verify_token(
            token,
            request_amount=300.0,
            request_currency="USD"
        )
        assert result.valid is True
        
        # Over limit - should fail
        result = token_service.verify_token(
            token,
            request_amount=600.0,
            request_currency="USD"
        )
        assert result.valid is False
        assert result.reason == "amount_exceeded"
    
    def test_token_currency_check(self):
        """Test that currency constraint is enforced."""
        from app.services.token_service import token_service
        
        token = token_service.create_delegation_token(
            consent_id="cons_test123",
            user_id="user_123",
            intent_description="Buy flight",
            max_amount=500.0,
            currency="USD",
        )
        
        # Matching currency - should pass
        result = token_service.verify_token(
            token,
            request_amount=300.0,
            request_currency="USD"
        )
        assert result.valid is True
        
        # Different currency - should fail
        result = token_service.verify_token(
            token,
            request_amount=300.0,
            request_currency="EUR"
        )
        assert result.valid is False
        assert result.reason == "currency_mismatch"
    
    def test_token_merchant_check(self):
        """Test that merchant constraint is enforced."""
        from app.services.token_service import token_service
        
        token = token_service.create_delegation_token(
            consent_id="cons_test123",
            user_id="user_123",
            intent_description="Buy flight",
            max_amount=500.0,
            currency="USD",
            allowed_merchants=["delta", "united"],
        )
        
        # Allowed merchant - should pass
        result = token_service.verify_token(
            token,
            request_amount=300.0,
            request_currency="USD",
            request_merchant_id="delta"
        )
        assert result.valid is True
        
        # Not allowed merchant - should fail
        result = token_service.verify_token(
            token,
            request_amount=300.0,
            request_currency="USD",
            request_merchant_id="southwest"
        )
        assert result.valid is False
        assert result.reason == "merchant_not_allowed"


class TestConsentFlow:
    """Test consent creation endpoint (requires database)."""
    
    @pytest.mark.anyio
    async def test_create_consent(self, client: AsyncClient):
        """Test creating a consent."""
        response = await client.post(
            "/v1/consents",
            json={
                "user_id": "user_123",
                "intent": {
                    "description": "Buy cheapest flight to NYC"
                },
                "constraints": {
                    "max_amount": 500,
                    "currency": "USD"
                },
                "options": {
                    "expires_in_seconds": 3600
                },
                "signature": "test_signature",
                "public_key": "test_public_key"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "consent_id" in data
        assert "delegation_token" in data
        assert data["consent_id"].startswith("cons_")


class TestFullFlow:
    """Test the complete consent → authorize → verify flow."""
    
    @pytest.mark.anyio
    async def test_full_flow(self, client: AsyncClient):
        """Test complete flow: consent → authorize → verify."""
        
        # Step 1: Create consent
        test_user = f"user_flow_{uuid.uuid4().hex[:8]}"
        consent_response = await client.post(
            "/v1/consents",
            json={
                "user_id": test_user,
                "intent": {"description": "Buy flight to NYC"},
                "constraints": {"max_amount": 500, "currency": "USD"},
                "options": {"expires_in_seconds": 3600},
                "signature": "sig",
                "public_key": "key"
            }
        )
        assert consent_response.status_code == 201
        consent_data = consent_response.json()
        delegation_token = consent_data["delegation_token"]
        
        # Step 2: Authorize transaction
        auth_response = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": delegation_token,
                "action": "payment",
                "transaction": {
                    "amount": 347,
                    "currency": "USD",
                    "merchant_id": "delta_airlines"
                }
            }
        )
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert auth_data["decision"] == "ALLOW"
        authorization_code = auth_data["authorization_code"]
        
        # Step 3: Verify authorization
        verify_response = await client.post(
            "/v1/verify",
            json={
                "authorization_code": authorization_code,
                "transaction": {
                    "amount": 347,
                    "currency": "USD"
                }
            }
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["valid"] is True
        assert verify_data["consent_proof"] is not None
    
    @pytest.mark.anyio
    async def test_denial_over_limit(self, client: AsyncClient):
        """Test that over-limit transactions are denied."""
        
        # Create consent with $500 limit
        test_user = f"user_deny_{uuid.uuid4().hex[:8]}"
        consent_response = await client.post(
            "/v1/consents",
            json={
                "user_id": test_user,
                "intent": {"description": "Buy flight"},
                "constraints": {"max_amount": 500, "currency": "USD"},
                "options": {"expires_in_seconds": 3600},
                "signature": "sig",
                "public_key": "key"
            }
        )
        delegation_token = consent_response.json()["delegation_token"]
        
        # Try to authorize $600 - should be denied
        auth_response = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": delegation_token,
                "action": "payment",
                "transaction": {
                    "amount": 600,
                    "currency": "USD"
                }
            }
        )
        assert auth_response.status_code == 200
        auth_data = auth_response.json()
        assert auth_data["decision"] == "DENY"
        assert auth_data["reason"] == "amount_exceeded"
