"""
AgentAuth SDK Unit Tests

Tests for client construction, models, exceptions, and retry logic.
Does NOT require a running server — all HTTP calls are mocked.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import httpx

# ---------------------------------------------------------------------------
# We need the SDK package on sys.path
# ---------------------------------------------------------------------------
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from agentauth.client import AgentAuth, AsyncAgentAuth, SDK_VERSION, _USER_AGENT
from agentauth.models import (
    Consent,
    Authorization,
    Verification,
    ConsentProof,
    ConsentConstraints,
    Transaction,
)
from agentauth.exceptions import (
    AgentAuthError,
    AuthorizationDenied,
    InvalidToken,
    VerificationFailed,
    RateLimitExceeded,
    APIError,
)


# ============================================================================
# Client Construction
# ============================================================================


class TestClientConstruction:
    """Tests for AgentAuth client initialization."""

    def test_default_base_url(self):
        client = AgentAuth()
        assert client.base_url == "http://localhost:8000"
        client.close()

    def test_custom_base_url(self):
        client = AgentAuth(base_url="https://api.agentauth.in")
        assert client.base_url == "https://api.agentauth.in"
        client.close()

    def test_trailing_slash_stripped(self):
        client = AgentAuth(base_url="https://api.agentauth.in/")
        assert client.base_url == "https://api.agentauth.in"
        client.close()

    def test_api_key_stored(self):
        client = AgentAuth(api_key="aa_live_test123")
        assert client.api_key == "aa_live_test123"
        client.close()

    def test_timeout_configurable(self):
        client = AgentAuth(timeout=60.0)
        assert client.timeout == 60.0
        client.close()

    def test_retry_defaults(self):
        client = AgentAuth()
        assert client.max_retries == 3
        assert client.base_delay == 0.5
        assert client.max_delay == 4.0
        client.close()

    def test_sub_apis_initialized(self):
        client = AgentAuth()
        assert client.consents is not None
        assert client.agents is not None
        assert client.limits is not None
        assert client.webhooks is not None
        assert client.analytics is not None
        client.close()

    def test_context_manager(self):
        with AgentAuth() as client:
            assert client.base_url == "http://localhost:8000"

    def test_user_agent_header(self):
        client = AgentAuth(api_key="aa_live_test")
        assert client._http.headers["User-Agent"] == _USER_AGENT
        client.close()

    def test_auth_header_set(self):
        client = AgentAuth(api_key="aa_live_xyz")
        assert client._http.headers["Authorization"] == "Bearer aa_live_xyz"
        client.close()

    def test_no_auth_header_without_key(self):
        client = AgentAuth()
        assert "Authorization" not in client._http.headers
        client.close()


class TestAsyncClientConstruction:
    """Tests for AsyncAgentAuth client initialization."""

    def test_default_values(self):
        client = AsyncAgentAuth()
        assert client.base_url == "http://localhost:8000"
        assert client.max_retries == 3

    def test_sub_apis_initialized(self):
        client = AsyncAgentAuth()
        assert client.consents is not None
        assert client.agents is not None
        assert client.limits is not None

    def test_user_agent_header(self):
        client = AsyncAgentAuth(api_key="aa_live_test")
        assert client._http.headers["User-Agent"] == _USER_AGENT


# ============================================================================
# Models
# ============================================================================


class TestConsentModel:
    """Tests for the Consent model."""

    def test_consent_creation(self):
        c = Consent(
            consent_id="cons_test123",
            delegation_token="eyJ0eXAi...",
            expires_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
            constraints=ConsentConstraints(
                max_amount=500.0, currency="USD"
            ),
        )
        assert c.consent_id == "cons_test123"
        assert c.token == "eyJ0eXAi..."

    def test_consent_token_alias(self):
        c = Consent(
            consent_id="c1",
            delegation_token="tok",
            expires_at=datetime.now(timezone.utc),
            constraints=ConsentConstraints(max_amount=100, currency="USD"),
        )
        assert c.token == c.delegation_token


class TestAuthorizationModel:
    """Tests for the Authorization model."""

    def test_allowed(self):
        a = Authorization(decision="ALLOW", authorization_code="authz_123")
        assert a.allowed is True
        assert a.denied is False
        assert a.requires_step_up is False

    def test_denied(self):
        a = Authorization(decision="DENY", reason="amount_exceeded")
        assert a.allowed is False
        assert a.denied is True

    def test_step_up(self):
        a = Authorization(
            decision="STEP_UP", step_up_url="https://example.com/confirm"
        )
        assert a.requires_step_up is True
        assert a.allowed is False


class TestVerificationModel:
    """Tests for the Verification model."""

    def test_valid_verification(self):
        v = Verification(
            valid=True,
            authorization_id="auth_1",
            verification_timestamp=datetime.now(timezone.utc),
            proof_token="eyJ...",
        )
        assert v.valid is True

    def test_invalid_verification(self):
        v = Verification(
            valid=False,
            verification_timestamp=datetime.now(timezone.utc),
            error="authorization_not_found",
        )
        assert v.valid is False
        assert v.error == "authorization_not_found"


class TestConsentProofModel:
    def test_consent_proof(self):
        p = ConsentProof(
            consent_id="cons_1",
            user_authorized_at=datetime.now(timezone.utc),
            user_intent="Buy flight",
            max_authorized_amount=500,
            actual_amount=347,
            currency="USD",
            signature_valid=True,
        )
        assert p.signature_valid is True


class TestTransactionModel:
    def test_transaction(self):
        t = Transaction(
            amount=99.99,
            currency="USD",
            merchant_id="acme",
            merchant_name="ACME Corp",
            merchant_category="5411",
        )
        assert t.amount == 99.99


# ============================================================================
# Exceptions
# ============================================================================


class TestExceptions:
    """Tests for exception hierarchy."""

    def test_base_exception(self):
        e = AgentAuthError("Something failed")
        assert str(e) == "Something failed"
        assert e.code is None
        assert e.details == {}

    def test_authorization_denied(self):
        e = AuthorizationDenied(reason="amount_exceeded")
        assert e.reason == "amount_exceeded"
        assert e.code == "authorization_denied"
        assert "amount_exceeded" in str(e)

    def test_invalid_token(self):
        e = InvalidToken()
        assert e.code == "invalid_token"

    def test_invalid_token_custom_message(self):
        e = InvalidToken("Token was revoked")
        assert "Token was revoked" in str(e)

    def test_verification_failed(self):
        e = VerificationFailed("authorization_expired")
        assert e.code == "verification_failed"
        assert "authorization_expired" in str(e)

    def test_rate_limit_exceeded(self):
        e = RateLimitExceeded(retry_after=30)
        assert e.retry_after == 30
        assert e.code == "rate_limit_exceeded"

    def test_api_error(self):
        e = APIError(status_code=500, message="Internal server error")
        assert e.status_code == 500
        assert e.code == "api_error"

    def test_exception_inheritance(self):
        """All custom exceptions inherit from AgentAuthError."""
        assert issubclass(AuthorizationDenied, AgentAuthError)
        assert issubclass(InvalidToken, AgentAuthError)
        assert issubclass(VerificationFailed, AgentAuthError)
        assert issubclass(RateLimitExceeded, AgentAuthError)
        assert issubclass(APIError, AgentAuthError)


# ============================================================================
# SDK Version
# ============================================================================


class TestSDKVersion:
    def test_version_format(self):
        parts = SDK_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_user_agent_contains_version(self):
        assert SDK_VERSION in _USER_AGENT
        assert "agentauth-python" in _USER_AGENT


# ============================================================================
# Request building (mock transport)
# ============================================================================


class TestRequestBuilding:
    """Test that the client builds requests correctly."""

    def test_authorize_request_body(self):
        """Verify the authorize method builds the correct JSON body."""
        client = AgentAuth(api_key="aa_live_test")

        # Mock the _request method
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {
                "decision": "ALLOW",
                "authorization_code": "authz_test",
            }
            auth = client.authorize(
                token="test_token",
                amount=100.0,
                currency="USD",
                merchant_id="acme",
                merchant_name="ACME Corp",
                merchant_category="5411",
            )

            mock_req.assert_called_once()
            call_args = mock_req.call_args
            body = call_args.kwargs["json"]
            assert body["delegation_token"] == "test_token"
            assert body["transaction"]["amount"] == 100.0
            assert body["transaction"]["merchant_id"] == "acme"
            assert body["transaction"]["merchant_category"] == "5411"
            assert auth.allowed is True
        client.close()

    def test_verify_request_body(self):
        """Verify the verify method builds the correct JSON body."""
        client = AgentAuth(api_key="aa_live_test")

        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {
                "valid": True,
                "verification_timestamp": "2026-01-01T00:00:00Z",
            }
            v = client.verify(
                authorization_code="authz_xyz",
                amount=347.0,
                currency="USD",
                merchant_id="delta",
            )

            body = mock_req.call_args.kwargs["json"]
            assert body["authorization_code"] == "authz_xyz"
            assert body["transaction"]["amount"] == 347.0
            assert body["merchant_id"] == "delta"
            assert v.valid is True
        client.close()

    def test_authorize_raise_on_deny(self):
        """Test raise_on_deny flag."""
        client = AgentAuth(api_key="aa_live_test")

        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {
                "decision": "DENY",
                "reason": "amount_exceeded",
                "message": "Over limit",
            }
            with pytest.raises(AuthorizationDenied) as exc_info:
                client.authorize(
                    token="tok", amount=999, raise_on_deny=True
                )
            assert exc_info.value.reason == "amount_exceeded"
        client.close()

    def test_verify_raise_on_invalid(self):
        """Test raise_on_invalid flag."""
        client = AgentAuth(api_key="aa_live_test")

        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {
                "valid": False,
                "verification_timestamp": "2026-01-01T00:00:00Z",
                "error": "authorization_expired",
            }
            with pytest.raises(VerificationFailed):
                client.verify(
                    authorization_code="authz_old",
                    amount=100,
                    raise_on_invalid=True,
                )
        client.close()

    def test_consents_list_params(self):
        """Test consents.list passes pagination params."""
        client = AgentAuth(api_key="aa_live_test")

        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {"consents": [], "total": 0}
            client.consents.list(limit=5, offset=10)
            mock_req.assert_called_once_with(
                "GET", "/v1/consents", params={"limit": 5, "offset": 10}
            )
        client.close()

    def test_agents_create(self):
        """Test agents.create passes correct body."""
        client = AgentAuth()

        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = {"id": "a1", "name": "Bot"}
            client.agents.create("Bot", description="Test bot")
            body = mock_req.call_args.kwargs["json"]
            assert body["name"] == "Bot"
            assert body["description"] == "Test bot"
        client.close()
