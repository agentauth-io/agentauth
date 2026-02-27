"""
Comprehensive API Test Suite for AgentAuth

Production-grade tests covering:
- Core flow (consent → authorize → verify)
- All CRUD operations
- Edge cases and error handling
- Input validation
- Security headers
- Rate limit headers
- API key authentication
- Agent management
"""
import pytest
import uuid
from httpx import AsyncClient


# =============================================================================
# Health & Root
# =============================================================================


class TestHealthEndpoints:
    """Health and root endpoint tests."""

    @pytest.mark.anyio
    async def test_root_returns_api_info(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "AgentAuth"
        assert "version" in data
        assert "docs" in data

    @pytest.mark.anyio
    async def test_health_returns_healthy(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @pytest.mark.anyio
    async def test_health_detailed(self, client: AsyncClient):
        resp = await client.get("/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "api" in data["checks"]


# =============================================================================
# Security Headers
# =============================================================================


class TestSecurityHeaders:
    """Verify security headers on all responses."""

    @pytest.mark.anyio
    async def test_security_headers_present(self, client: AsyncClient):
        resp = await client.get("/health")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "0"
        assert "strict-origin" in resp.headers.get("Referrer-Policy", "")

    @pytest.mark.anyio
    async def test_request_id_header(self, client: AsyncClient):
        resp = await client.get("/health")
        assert "X-Request-ID" in resp.headers

    @pytest.mark.anyio
    async def test_custom_request_id_echoed(self, client: AsyncClient):
        custom_id = str(uuid.uuid4())
        resp = await client.get("/health", headers={"X-Request-ID": custom_id})
        assert resp.headers.get("X-Request-ID") == custom_id


# =============================================================================
# API Key Authentication
# =============================================================================


class TestAPIKeyAuth:
    """API key authentication tests."""

    @pytest.mark.anyio
    async def test_missing_api_key_returns_401(self, client: AsyncClient):
        """Protected endpoints require API key."""
        resp = await client.post(
            "/v1/consents",
            json={
                "user_id": "u1",
                "intent": {"description": "test"},
                "constraints": {"max_amount": 100, "currency": "USD"},
                "signature": "s",
                "public_key": "k",
            },
            headers={"X-API-Key": ""},  # Override the test key
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_invalid_api_key_returns_401(self, client: AsyncClient):
        resp = await client.post(
            "/v1/consents",
            json={
                "user_id": "u1",
                "intent": {"description": "test"},
                "constraints": {"max_amount": 100, "currency": "USD"},
                "signature": "s",
                "public_key": "k",
            },
            headers={"X-API-Key": "aa_live_totally_invalid_key_here"},
        )
        assert resp.status_code == 401

    @pytest.mark.anyio
    async def test_bearer_auth_also_works(self, client: AsyncClient):
        """Authorization: Bearer header should also be accepted."""
        from app.middleware.api_keys import generate_api_key_sync

        key_data = generate_api_key_sync(owner="bearer_test")
        resp = await client.get(
            "/v1/consents",
            headers={
                "X-API-Key": "",
                "Authorization": f"Bearer {key_data['key']}",
            },
        )
        # Should succeed (200) since bearer auth is valid
        assert resp.status_code == 200


# =============================================================================
# Consent CRUD
# =============================================================================


def _consent_payload(user_id: str = None, max_amount: float = 500) -> dict:
    """Helper to build a consent creation payload."""
    return {
        "user_id": user_id or f"user_{uuid.uuid4().hex[:8]}",
        "intent": {"description": "Buy cheapest flight to NYC"},
        "constraints": {"max_amount": max_amount, "currency": "USD"},
        "options": {"expires_in_seconds": 3600, "single_use": True},
        "signature": "sdk_generated",
        "public_key": "sdk_key",
    }


class TestConsentCreation:
    """Consent creation tests."""

    @pytest.mark.anyio
    async def test_create_consent_success(self, client: AsyncClient):
        resp = await client.post("/v1/consents", json=_consent_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["consent_id"].startswith("cons_")
        assert "delegation_token" in data
        assert "expires_at" in data
        assert data["constraints"]["max_amount"] == 500
        assert data["constraints"]["currency"] == "USD"

    @pytest.mark.anyio
    async def test_create_consent_with_merchants(self, client: AsyncClient):
        payload = _consent_payload()
        payload["constraints"]["allowed_merchants"] = ["delta", "united"]
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["constraints"]["allowed_merchants"] == ["delta", "united"]

    @pytest.mark.anyio
    async def test_create_consent_with_categories(self, client: AsyncClient):
        payload = _consent_payload()
        payload["constraints"]["allowed_categories"] = ["4511", "5812"]
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["constraints"]["allowed_categories"] == ["4511", "5812"]

    @pytest.mark.anyio
    async def test_create_consent_custom_expiry(self, client: AsyncClient):
        payload = _consent_payload()
        payload["options"]["expires_in_seconds"] = 300
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 201

    @pytest.mark.anyio
    async def test_create_consent_missing_user_id(self, client: AsyncClient):
        payload = _consent_payload()
        del payload["user_id"]
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422  # Validation error

    @pytest.mark.anyio
    async def test_create_consent_empty_user_id(self, client: AsyncClient):
        payload = _consent_payload()
        payload["user_id"] = ""
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_create_consent_zero_amount(self, client: AsyncClient):
        payload = _consent_payload(max_amount=0)
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_create_consent_negative_amount(self, client: AsyncClient):
        payload = _consent_payload(max_amount=-100)
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_create_consent_invalid_currency(self, client: AsyncClient):
        payload = _consent_payload()
        payload["constraints"]["currency"] = "TOOLONG"
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_create_consent_missing_intent(self, client: AsyncClient):
        payload = _consent_payload()
        del payload["intent"]
        resp = await client.post("/v1/consents", json=payload)
        assert resp.status_code == 422


class TestConsentRetrieval:
    """Consent retrieval and listing tests."""

    @pytest.mark.anyio
    async def test_list_consents_empty(self, client: AsyncClient):
        resp = await client.get("/v1/consents")
        assert resp.status_code == 200
        data = resp.json()
        assert "consents" in data
        assert "total" in data

    @pytest.mark.anyio
    async def test_list_consents_after_creation(self, client: AsyncClient):
        # Create a consent first
        await client.post("/v1/consents", json=_consent_payload())
        resp = await client.get("/v1/consents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.anyio
    async def test_list_consents_pagination(self, client: AsyncClient):
        # Create 3 consents
        for _ in range(3):
            await client.post("/v1/consents", json=_consent_payload())

        resp = await client.get("/v1/consents?limit=2&offset=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["consents"]) <= 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    @pytest.mark.anyio
    async def test_get_consent_by_id(self, client: AsyncClient):
        create_resp = await client.post("/v1/consents", json=_consent_payload())
        consent_id = create_resp.json()["consent_id"]

        resp = await client.get(f"/v1/consents/{consent_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["consent_id"] == consent_id

    @pytest.mark.anyio
    async def test_get_consent_not_found(self, client: AsyncClient):
        resp = await client.get("/v1/consents/cons_nonexistent_xyz")
        assert resp.status_code == 404


class TestConsentRevocation:
    """Consent revocation tests."""

    @pytest.mark.anyio
    async def test_revoke_consent(self, client: AsyncClient):
        create_resp = await client.post("/v1/consents", json=_consent_payload())
        consent_id = create_resp.json()["consent_id"]

        resp = await client.delete(f"/v1/consents/{consent_id}")
        assert resp.status_code == 204

    @pytest.mark.anyio
    async def test_revoke_nonexistent_consent(self, client: AsyncClient):
        resp = await client.delete("/v1/consents/cons_does_not_exist")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_revoked_consent_blocks_authorization(self, client: AsyncClient):
        # Create and revoke
        create_resp = await client.post("/v1/consents", json=_consent_payload())
        data = create_resp.json()
        token = data["delegation_token"]
        consent_id = data["consent_id"]

        await client.delete(f"/v1/consents/{consent_id}")

        # Try to authorize — should be denied
        auth_resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 100, "currency": "USD"},
            },
        )
        assert auth_resp.status_code == 200
        assert auth_resp.json()["decision"] == "DENY"


# =============================================================================
# Authorization
# =============================================================================


class TestAuthorization:
    """Authorization endpoint tests."""

    async def _create_consent_and_get_token(self, client: AsyncClient, **kwargs) -> str:
        payload = _consent_payload(**kwargs)
        resp = await client.post("/v1/consents", json=payload)
        return resp.json()["delegation_token"]

    @pytest.mark.anyio
    async def test_authorize_within_limit(self, client: AsyncClient):
        token = await self._create_consent_and_get_token(client, max_amount=500)
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 347, "currency": "USD", "merchant_id": "delta"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "ALLOW"
        assert data["authorization_code"].startswith("authz_")
        assert "expires_at" in data
        assert "consent_id" in data

    @pytest.mark.anyio
    async def test_authorize_over_limit_denied(self, client: AsyncClient):
        token = await self._create_consent_and_get_token(client, max_amount=500)
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 600, "currency": "USD"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "DENY"
        assert data["reason"] == "amount_exceeded"

    @pytest.mark.anyio
    async def test_authorize_exact_limit(self, client: AsyncClient):
        token = await self._create_consent_and_get_token(client, max_amount=500)
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 500, "currency": "USD"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "ALLOW"

    @pytest.mark.anyio
    async def test_authorize_currency_mismatch(self, client: AsyncClient):
        token = await self._create_consent_and_get_token(client, max_amount=500)
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 100, "currency": "EUR"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "DENY"
        assert resp.json()["reason"] == "currency_mismatch"

    @pytest.mark.anyio
    async def test_authorize_merchant_restriction(self, client: AsyncClient):
        payload = _consent_payload(max_amount=500)
        payload["constraints"]["allowed_merchants"] = ["delta", "united"]
        create_resp = await client.post("/v1/consents", json=payload)
        token = create_resp.json()["delegation_token"]

        # Allowed merchant
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 100, "currency": "USD", "merchant_id": "delta"},
            },
        )
        assert resp.json()["decision"] == "ALLOW"

        # Disallowed merchant
        resp2 = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 100, "currency": "USD", "merchant_id": "southwest"},
            },
        )
        assert resp2.json()["decision"] == "DENY"
        assert resp2.json()["reason"] == "merchant_not_allowed"

    @pytest.mark.anyio
    async def test_authorize_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": "totally.invalid.token",
                "action": "payment",
                "transaction": {"amount": 100, "currency": "USD"},
            },
        )
        assert resp.status_code == 200
        assert resp.json()["decision"] == "DENY"
        assert resp.json()["reason"] == "invalid_token"

    @pytest.mark.anyio
    async def test_authorize_missing_transaction(self, client: AsyncClient):
        resp = await client.post(
            "/v1/authorize",
            json={"delegation_token": "some_token", "action": "payment"},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_authorize_zero_amount(self, client: AsyncClient):
        resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": "some_token",
                "action": "payment",
                "transaction": {"amount": 0, "currency": "USD"},
            },
        )
        assert resp.status_code == 422


# =============================================================================
# Verification
# =============================================================================


class TestVerification:
    """Verification endpoint tests."""

    async def _get_auth_code(self, client: AsyncClient, amount: float = 347) -> tuple:
        """Helper: create consent → authorize → return (auth_code, amount)."""
        payload = _consent_payload(max_amount=500)
        create_resp = await client.post("/v1/consents", json=payload)
        token = create_resp.json()["delegation_token"]

        auth_resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": amount, "currency": "USD", "merchant_id": "test_merchant"},
            },
        )
        return auth_resp.json()["authorization_code"], amount

    @pytest.mark.anyio
    async def test_verify_valid_code(self, client: AsyncClient):
        auth_code, amount = await self._get_auth_code(client)
        resp = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth_code,
                "transaction": {"amount": amount, "currency": "USD"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["consent_proof"] is not None
        assert data["proof_token"] is not None
        assert data["consent_proof"]["signature_valid"] is True

    @pytest.mark.anyio
    async def test_verify_already_used(self, client: AsyncClient):
        auth_code, amount = await self._get_auth_code(client)

        # First verification
        resp1 = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth_code,
                "transaction": {"amount": amount, "currency": "USD"},
            },
        )
        assert resp1.json()["valid"] is True

        # Second verification — should fail
        resp2 = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth_code,
                "transaction": {"amount": amount, "currency": "USD"},
            },
        )
        assert resp2.json()["valid"] is False
        assert resp2.json()["error"] == "authorization_already_used"

    @pytest.mark.anyio
    async def test_verify_amount_mismatch(self, client: AsyncClient):
        auth_code, _ = await self._get_auth_code(client, amount=347)
        resp = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth_code,
                "transaction": {"amount": 999, "currency": "USD"},
            },
        )
        assert resp.json()["valid"] is False
        assert resp.json()["error"] == "amount_mismatch"

    @pytest.mark.anyio
    async def test_verify_currency_mismatch(self, client: AsyncClient):
        auth_code, amount = await self._get_auth_code(client)
        resp = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth_code,
                "transaction": {"amount": amount, "currency": "EUR"},
            },
        )
        assert resp.json()["valid"] is False
        assert resp.json()["error"] == "currency_mismatch"

    @pytest.mark.anyio
    async def test_verify_invalid_code(self, client: AsyncClient):
        resp = await client.post(
            "/v1/verify",
            json={
                "authorization_code": "authz_does_not_exist",
                "transaction": {"amount": 100, "currency": "USD"},
            },
        )
        assert resp.json()["valid"] is False
        assert resp.json()["error"] == "authorization_not_found"

    @pytest.mark.anyio
    async def test_verify_missing_code(self, client: AsyncClient):
        resp = await client.post(
            "/v1/verify",
            json={"transaction": {"amount": 100, "currency": "USD"}},
        )
        assert resp.status_code == 422


# =============================================================================
# Full Flow (Integration)
# =============================================================================


class TestFullFlowIntegration:
    """End-to-end integration tests for the core 3-step flow."""

    @pytest.mark.anyio
    async def test_complete_flow_consent_authorize_verify(self, client: AsyncClient):
        """consent → authorize → verify full happy path."""
        # 1. Create consent
        consent_resp = await client.post("/v1/consents", json=_consent_payload(max_amount=1000))
        assert consent_resp.status_code == 201
        consent = consent_resp.json()
        token = consent["delegation_token"]

        # 2. Authorize
        auth_resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {
                    "amount": 499.99,
                    "currency": "USD",
                    "merchant_id": "acme_corp",
                    "merchant_name": "ACME Corp",
                },
            },
        )
        assert auth_resp.status_code == 200
        auth = auth_resp.json()
        assert auth["decision"] == "ALLOW"

        # 3. Verify
        verify_resp = await client.post(
            "/v1/verify",
            json={
                "authorization_code": auth["authorization_code"],
                "transaction": {"amount": 499.99, "currency": "USD"},
                "merchant_id": "acme_corp",
            },
        )
        assert verify_resp.status_code == 200
        verification = verify_resp.json()
        assert verification["valid"] is True
        assert verification["consent_proof"]["user_intent"] == "Buy cheapest flight to NYC"
        assert verification["consent_proof"]["max_authorized_amount"] == 1000
        assert verification["consent_proof"]["actual_amount"] == 499.99

    @pytest.mark.anyio
    async def test_flow_multiple_authorizations_same_consent(self, client: AsyncClient):
        """Multiple authorization requests against the same consent token."""
        consent_resp = await client.post("/v1/consents", json=_consent_payload(max_amount=500))
        token = consent_resp.json()["delegation_token"]

        # First auth — should work
        resp1 = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 100, "currency": "USD"},
            },
        )
        assert resp1.json()["decision"] == "ALLOW"

        # Second auth — should also work (token still valid)
        resp2 = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "payment",
                "transaction": {"amount": 200, "currency": "USD"},
            },
        )
        assert resp2.json()["decision"] == "ALLOW"


# =============================================================================
# Agents CRUD
# =============================================================================


class TestAgentsCRUD:
    """Agent registration and management tests."""

    @pytest.mark.anyio
    async def test_list_agents_empty(self, client: AsyncClient):
        resp = await client.get("/v1/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert "total" in data

    @pytest.mark.anyio
    async def test_create_agent(self, client: AsyncClient):
        resp = await client.post(
            "/v1/agents",
            json={"name": "ShoppingBot", "description": "Helps users shop"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ShoppingBot"
        assert data["status"] == "active"
        assert "id" in data

    @pytest.mark.anyio
    async def test_get_agent(self, client: AsyncClient):
        create_resp = await client.post(
            "/v1/agents", json={"name": "TestBot"}
        )
        agent_id = create_resp.json()["id"]

        resp = await client.get(f"/v1/agents/{agent_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "TestBot"

    @pytest.mark.anyio
    async def test_get_agent_not_found(self, client: AsyncClient):
        resp = await client.get("/v1/agents/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_delete_agent(self, client: AsyncClient):
        create_resp = await client.post(
            "/v1/agents", json={"name": "DeleteMe"}
        )
        agent_id = create_resp.json()["id"]

        resp = await client.delete(f"/v1/agents/{agent_id}")
        assert resp.status_code == 200

        # Should be gone
        resp2 = await client.get(f"/v1/agents/{agent_id}")
        assert resp2.status_code == 404

    @pytest.mark.anyio
    async def test_delete_agent_not_found(self, client: AsyncClient):
        resp = await client.delete("/v1/agents/nonexistent")
        assert resp.status_code == 404


# =============================================================================
# API Key Management
# =============================================================================


class TestAPIKeyManagement:
    """API key generation endpoint tests (dev mode only)."""

    @pytest.mark.anyio
    async def test_create_api_key(self, client: AsyncClient):
        resp = await client.post("/v1/api-keys?owner=test_owner")
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("aa_live_")
        assert "key_id" in data
        assert data["owner"] == "test_owner"

    @pytest.mark.anyio
    async def test_get_demo_key(self, client: AsyncClient):
        resp = await client.get("/v1/demo-key")
        assert resp.status_code == 200
        data = resp.json()
        assert "key" in data
        assert "key_id" in data

    @pytest.mark.anyio
    async def test_create_test_key(self, client: AsyncClient):
        resp = await client.post("/v1/test-key?owner=sdk_tests")
        assert resp.status_code == 200
        data = resp.json()
        assert data["key"].startswith("aa_live_")


# =============================================================================
# Billing Plans (public endpoint)
# =============================================================================


class TestBillingPlans:
    """Billing plan listing."""

    @pytest.mark.anyio
    async def test_get_plans(self, client: AsyncClient):
        resp = await client.get("/v1/billing/plans")
        assert resp.status_code == 200
        data = resp.json()
        assert "plans" in data


# =============================================================================
# Metrics
# =============================================================================


class TestMetrics:
    """Metrics endpoint tests."""

    @pytest.mark.anyio
    async def test_metrics_endpoint(self, client: AsyncClient):
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "infrastructure" in data
        assert data["infrastructure"]["rate_limiting"] == "enabled"
