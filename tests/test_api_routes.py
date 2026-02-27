"""
Tests for API route endpoints.

Integration tests using the `client` fixture (httpx AsyncClient + ASGI transport).
"""

import pytest


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentAuth"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_health(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_metrics(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "cache" in data
        assert "infrastructure" in data


class TestWebhookEndpoints:
    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self, client):
        response = await client.get("/v1/webhooks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_available_events(self, client):
        response = await client.get("/v1/webhooks/events/available")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        event_names = [e["name"] for e in data["events"]]
        assert "authorization.approved" in event_names
        assert "authorization.denied" in event_names


class TestDashboardEndpoints:
    @pytest.mark.asyncio
    async def test_dashboard_overview(self, client):
        response = await client.get("/v1/dashboard")
        assert response.status_code == 200
        data = response.json()
        # Dashboard returns flat structure with metrics
        assert "total_consents" in data or "active_consents" in data

    @pytest.mark.asyncio
    async def test_dashboard_stats(self, client):
        response = await client.get("/v1/dashboard/stats")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_transactions(self, client):
        response = await client.get("/v1/dashboard/transactions")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_analytics(self, client):
        response = await client.get("/v1/dashboard/analytics")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_health(self, client):
        response = await client.get("/v1/dashboard/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestLimitsEndpoints:
    @pytest.mark.asyncio
    async def test_get_limits(self, client):
        response = await client.get("/v1/limits")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_update_limits(self, client):
        response = await client.put(
            "/v1/limits",
            json={
                "daily_limit": 500.0,
                "monthly_limit": 5000.0,
                "per_transaction_limit": 200.0,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_limits_usage(self, client):
        response = await client.get("/v1/limits/usage")
        assert response.status_code == 200


class TestRulesEndpoints:
    @pytest.mark.asyncio
    async def test_get_merchant_rules(self, client):
        response = await client.get("/v1/rules/merchants")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_merchant_rule(self, client):
        response = await client.post(
            "/v1/rules/merchants",
            json={
                "merchant_pattern": "scam_store",
                "action": "block",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_category_rules(self, client):
        response = await client.get("/v1/rules/categories")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_add_category_rule(self, client):
        response = await client.post(
            "/v1/rules/categories",
            json={
                "category": "gambling",
                "action": "block",
            },
        )
        assert response.status_code == 200


class TestBillingEndpoints:
    @pytest.mark.asyncio
    async def test_get_subscription(self, client):
        response = await client.get("/v1/billing/subscription")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_usage(self, client):
        response = await client.get("/v1/billing/usage")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_check_limit(self, client):
        response = await client.get("/v1/billing/check-limit")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_plans(self, client):
        response = await client.get("/v1/billing/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data


class TestConsentEndpoints:
    @pytest.mark.asyncio
    async def test_create_consent(self, client):
        response = await client.post(
            "/v1/consents",
            json={
                "user_id": "user_123",
                "intent": {"description": "Buy a laptop under $1000"},
                "constraints": {"max_amount": 1000.0, "currency": "USD"},
                "signature": "test_signature_base64",
                "public_key": "test_public_key_base64",
            },
        )
        assert response.status_code in (200, 201)  # 201 Created is also valid
        data = response.json()
        assert "consent_id" in data
        assert "delegation_token" in data

    @pytest.mark.asyncio
    async def test_list_consents(self, client):
        # Create one first
        await client.post(
            "/v1/consents",
            json={
                "user_id": "user_123",
                "intent": {"description": "Test"},
                "constraints": {"max_amount": 100.0, "currency": "USD"},
                "signature": "test_signature_base64",
                "public_key": "test_public_key_base64",
            },
        )
        response = await client.get("/v1/consents")
        assert response.status_code == 200


class TestAuthorizationEndpoints:
    @pytest.mark.asyncio
    async def test_authorize_flow(self, client):
        # Create consent first
        consent_resp = await client.post(
            "/v1/consents",
            json={
                "user_id": "user_123",
                "intent": {"description": "Buy electronics"},
                "constraints": {"max_amount": 500.0, "currency": "USD"},
                "signature": "test_signature_base64",
                "public_key": "test_public_key_base64",
            },
        )
        assert consent_resp.status_code in (200, 201)
        token = consent_resp.json()["delegation_token"]

        # Authorize
        auth_resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "purchase",
                "transaction": {
                    "amount": 99.99,
                    "currency": "USD",
                    "merchant_id": "amazon",
                    "merchant_name": "Amazon",
                },
            },
        )
        assert auth_resp.status_code in (200, 201)
        data = auth_resp.json()
        assert data["decision"] in ("ALLOW", "DENY", "STEP_UP")

    @pytest.mark.asyncio
    async def test_authorize_verify_flow(self, client):
        # Create consent
        consent_resp = await client.post(
            "/v1/consents",
            json={
                "user_id": "user_456",
                "intent": {"description": "Order food"},
                "constraints": {"max_amount": 100.0, "currency": "USD"},
                "signature": "test_signature_base64",
                "public_key": "test_public_key_base64",
            },
        )
        assert consent_resp.status_code in (200, 201)
        token = consent_resp.json()["delegation_token"]

        # Authorize
        auth_resp = await client.post(
            "/v1/authorize",
            json={
                "delegation_token": token,
                "action": "purchase",
                "transaction": {
                    "amount": 25.0,
                    "currency": "USD",
                    "merchant_id": "doordash",
                },
            },
        )

        if (
            auth_resp.status_code in (200, 201)
            and auth_resp.json().get("decision") == "ALLOW"
        ):
            auth_code = auth_resp.json()["authorization_code"]
            # Verify
            verify_resp = await client.post(
                "/v1/verify",
                json={
                    "authorization_code": auth_code,
                    "transaction": {"amount": 25.0, "currency": "USD"},
                },
            )
            assert verify_resp.status_code in (200, 201)
