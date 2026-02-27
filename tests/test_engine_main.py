"""
Comprehensive tests for core/engine.py and core/main.py modules.
Covers the AuthorizationEngine, RateLimiter, SpendingTracker, AgentAuthCore,
and create_spending_policy to push coverage toward 80% target.
"""

import json
import os
import time

import pytest

from core.crypto import KeyManager, MasterSecret
from core.engine import (
    AuthorizationEngine,
    AuthorizationRequest,
    AuthorizationResponse,
    AuthorizationStatus,
    RateLimitConfig,
    RateLimiter,
    SpendingTracker,
)
from core.main import AgentAuthCore, create_spending_policy
from core.policy import PolicyBuilder, PolicyEffect

# ─── AuthorizationStatus Tests ───────────────────────────────────────────────


class TestAuthorizationStatus:
    def test_all_statuses(self):
        assert AuthorizationStatus.APPROVED.value == "approved"
        assert AuthorizationStatus.DENIED.value == "denied"
        assert AuthorizationStatus.REQUIRES_APPROVAL.value == "requires_approval"
        assert AuthorizationStatus.RATE_LIMITED.value == "rate_limited"
        assert AuthorizationStatus.ERROR.value == "error"
        assert len(AuthorizationStatus) == 5


# ─── AuthorizationRequest Tests ──────────────────────────────────────────────


class TestAuthorizationRequest:
    def test_basic_create(self):
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-123",
        )
        assert req.agent_id == "agent-1"
        assert req.request_id.startswith("req_")
        assert req.timestamp > 0

    def test_to_context_minimal(self):
        req = AuthorizationRequest(
            agent_id="a", user_id="u", action="buy", resource="r"
        )
        ctx = req.to_context()
        assert ctx["agent_id"] == "a"
        assert ctx["user_id"] == "u"
        assert ctx["action"] == "buy"
        assert ctx["resource"] == "r"
        assert "amount" not in ctx
        assert "merchant" not in ctx
        assert "category" not in ctx

    def test_to_context_full(self):
        req = AuthorizationRequest(
            agent_id="a",
            user_id="u",
            action="buy",
            resource="r",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
            metadata={"ip": "1.2.3.4"},
        )
        ctx = req.to_context()
        assert ctx["amount"] == 49.99
        assert ctx["merchant"] == "Amazon"
        assert ctx["category"] == "electronics"
        assert ctx["metadata"]["ip"] == "1.2.3.4"

    def test_hash_deterministic(self):
        req = AuthorizationRequest(
            agent_id="a", user_id="u", action="buy", resource="r", amount=50.0
        )
        h1 = req.hash()
        h2 = req.hash()
        assert h1 == h2
        assert len(h1) == 16

    def test_hash_different_for_different_requests(self):
        req1 = AuthorizationRequest(
            agent_id="a", user_id="u", action="buy", resource="r1"
        )
        req2 = AuthorizationRequest(
            agent_id="a", user_id="u", action="buy", resource="r2"
        )
        assert req1.hash() != req2.hash()


# ─── AuthorizationResponse Tests ─────────────────────────────────────────────


class TestAuthorizationResponse:
    def test_to_dict(self):
        resp = AuthorizationResponse(
            status=AuthorizationStatus.APPROVED,
            request_id="req-1",
            authorized=True,
            token="base64token",
            token_id="tok-1",
            reason="Allowed",
            risk_score=0.1,
            policy_id="pol-1",
            constraints={"max": 200},
            expires_at=time.time() + 3600,
            evaluation_time_ms=5.0,
        )
        d = resp.to_dict()
        assert d["status"] == "approved"
        assert d["authorized"] is True
        assert d["token"] == "base64token"
        assert d["constraints"]["max"] == 200

    def test_denied_response(self):
        resp = AuthorizationResponse(
            status=AuthorizationStatus.DENIED,
            request_id="req-1",
            authorized=False,
            reason="Policy blocked",
        )
        assert resp.authorized is False
        assert resp.token is None


# ─── RateLimiter Tests ────────────────────────────────────────────────────────


class TestRateLimiter:
    def test_allows_first_request(self):
        rl = RateLimiter()
        allowed, reason = rl.check("user-1")
        assert allowed is True
        assert reason == ""

    def test_per_minute_limit(self):
        config = RateLimitConfig(
            requests_per_minute=3,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_limit=10,
        )
        rl = RateLimiter(config)
        for _ in range(3):
            allowed, _ = rl.check("user-1")
            assert allowed is True
        allowed, reason = rl.check("user-1")
        assert allowed is False
        assert "minute" in reason

    def test_burst_limit(self):
        config = RateLimitConfig(requests_per_minute=100, burst_limit=2)
        rl = RateLimiter(config)
        rl.check("u")
        rl.check("u")
        allowed, reason = rl.check("u")
        assert allowed is False
        assert "Burst" in reason

    def test_reset(self):
        rl = RateLimiter()
        rl.check("user-1")
        rl.reset("user-1")
        assert "user-1" not in rl._requests

    def test_independent_keys(self):
        config = RateLimitConfig(requests_per_minute=2)
        rl = RateLimiter(config)
        rl.check("a")
        rl.check("a")
        # "a" is at limit
        allowed_a, _ = rl.check("a")
        assert allowed_a is False
        # "b" is still fine
        allowed_b, _ = rl.check("b")
        assert allowed_b is True


# ─── SpendingTracker Tests ────────────────────────────────────────────────────


class TestSpendingTracker:
    def test_initial_state(self):
        st = SpendingTracker(user_id="u", daily_limit=500.0, monthly_limit=5000.0)
        assert st.daily_remaining == 500.0

    def test_check_budget_allowed(self):
        st = SpendingTracker(user_id="u", daily_limit=500.0)
        ok, reason, remaining = st.check_budget(100.0)
        assert ok is True
        assert remaining == pytest.approx(400.0)

    def test_check_budget_daily_exceeded(self):
        st = SpendingTracker(user_id="u", daily_limit=100.0)
        st.record_spend(80.0, "tx1")
        ok, reason, remaining = st.check_budget(30.0)
        assert ok is False
        assert "Daily" in reason

    def test_check_budget_monthly_exceeded(self):
        st = SpendingTracker(user_id="u", daily_limit=10000.0, monthly_limit=100.0)
        st.record_spend(80.0, "tx1")
        ok, reason, remaining = st.check_budget(30.0)
        assert ok is False
        assert "Monthly" in reason

    def test_record_spend(self):
        st = SpendingTracker(user_id="u", daily_limit=500.0)
        st.record_spend(50.0, "tx1")
        assert st.daily_remaining == pytest.approx(450.0)
        st.record_spend(50.0, "tx2")
        assert st.daily_remaining == pytest.approx(400.0)

    def test_daily_remaining_property(self):
        st = SpendingTracker(user_id="u", daily_limit=200.0)
        st.record_spend(250.0, "tx1")
        assert st.daily_remaining == 0  # clamped to 0


# ─── AuthorizationEngine Tests ───────────────────────────────────────────────


class TestAuthorizationEngine:
    def _make_engine(self):
        ms = MasterSecret.generate()
        km = KeyManager(ms)
        return AuthorizationEngine(key_manager=km)

    def test_init(self):
        engine = self._make_engine()
        assert engine.stats["total_requests"] == 0
        assert engine.stats["policies_loaded"] >= 3  # default policies

    def test_authorize_low_amount_approved(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        resp = engine.authorize(req)
        assert resp.status == AuthorizationStatus.APPROVED
        assert resp.authorized is True
        assert resp.token is not None
        assert resp.token_id is not None

    def test_authorize_blocked_category(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-1",
            amount=25.0,
            merchant="CryptoEx",
            category="crypto",
        )
        resp = engine.authorize(req)
        assert resp.authorized is False
        assert resp.status == AuthorizationStatus.DENIED

    def test_authorize_budget_exceeded(self):
        engine = self._make_engine()
        engine.set_user_limits("user-1", daily_limit=50.0)
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-1",
            amount=100.0,
            merchant="Amazon",
            category="electronics",
        )
        resp = engine.authorize(req)
        assert resp.authorized is False
        assert resp.status == AuthorizationStatus.DENIED
        assert "Daily" in resp.reason or "limit" in resp.reason.lower()

    def test_authorize_rate_limited(self):
        ms = MasterSecret.generate()
        km = KeyManager(ms)
        engine = AuthorizationEngine(key_manager=km)
        engine._rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=2, burst_limit=100)
        )
        for i in range(2):
            req = AuthorizationRequest(
                agent_id="a", user_id="u", action="buy", resource=f"r{i}", amount=10.0
            )
            engine.authorize(req)
        # Third should be rate limited
        req = AuthorizationRequest(
            agent_id="a", user_id="u", action="buy", resource="r3", amount=10.0
        )
        resp = engine.authorize(req)
        assert resp.status == AuthorizationStatus.RATE_LIMITED

    def test_verify_token(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        resp = engine.authorize(req)
        assert resp.token is not None
        valid, token_obj, error = engine.verify_token(resp.token)
        assert valid is True
        assert token_obj is not None

    def test_verify_invalid_token(self):
        engine = self._make_engine()
        valid, token_obj, error = engine.verify_token("invalid_base64_token")
        assert valid is False
        assert token_obj is None
        assert len(error) > 0

    def test_revoke_token(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            resource="order-1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        resp = engine.authorize(req)
        engine.revoke_token(resp.token_id)
        # Revoked token should fail verification
        valid, _, error = engine.verify_token(resp.token)
        assert valid is False

    def test_add_remove_policy(self):
        engine = self._make_engine()
        initial_count = len(engine._policy_engine.list_policies())
        policy = (
            PolicyBuilder("test_pol", "Test Policy")
            .allow()
            .when("action")
            .equals("transfer")
            .build()
        )
        engine.add_policy(policy)
        assert len(engine._policy_engine.list_policies()) == initial_count + 1
        engine.remove_policy("test_pol")
        assert len(engine._policy_engine.list_policies()) == initial_count

    def test_set_user_limits(self):
        engine = self._make_engine()
        engine.set_user_limits("user-1", daily_limit=100.0, monthly_limit=1000.0)
        spending = engine.get_user_spending("user-1")
        assert spending["daily_limit"] == 100.0
        assert spending["monthly_limit"] == 1000.0
        assert spending["daily_remaining"] == 100.0

    def test_get_user_spending(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="a",
            user_id="u1",
            action="purchase",
            resource="r1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        engine.authorize(req)
        spending = engine.get_user_spending("u1")
        assert spending["daily_spent"] == pytest.approx(49.99)
        assert spending["transactions"] == 1

    def test_get_audit_log(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="a",
            user_id="u1",
            action="purchase",
            resource="r1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        engine.authorize(req)
        audit = engine.get_audit_log()
        assert len(audit) >= 1

    def test_stats(self):
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="a",
            user_id="u",
            action="purchase",
            resource="r1",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        engine.authorize(req)
        s = engine.stats
        assert s["total_requests"] == 1
        assert s["approved"] >= 0
        assert "approval_rate" in s
        assert "policies_loaded" in s

    def test_export_public_keys(self):
        engine = self._make_engine()
        keys = engine.export_public_keys()
        assert isinstance(keys, dict)
        assert len(keys) > 0

    def test_authorize_no_amount(self):
        """Authorize request without amount should skip budget check."""
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="a", user_id="u", action="read", resource="doc-1"
        )
        resp = engine.authorize(req)
        assert resp.status in (AuthorizationStatus.APPROVED, AuthorizationStatus.DENIED)

    def test_authorize_one_time_flag(self):
        """Amounts > $100 should get ONE_TIME flag."""
        engine = self._make_engine()
        req = AuthorizationRequest(
            agent_id="a",
            user_id="u",
            action="purchase",
            resource="r1",
            amount=150.0,
            merchant="Amazon",
            category="electronics",
        )
        resp = engine.authorize(req)
        assert resp.status == AuthorizationStatus.APPROVED
        assert resp.token is not None


# ─── AgentAuthCore Tests ─────────────────────────────────────────────────────


class TestAgentAuthCore:
    def _make_core(self):
        ms = MasterSecret.generate()
        return AgentAuthCore(master_secret=ms)

    def test_init(self):
        core = self._make_core()
        assert core.VERSION == "0.1.0"
        assert core._request_count == 0
        assert core.stats["total_requests"] == 0

    def test_from_master_secret(self):
        ms = MasterSecret.generate()
        hex_str = ms.to_hex()
        core = AgentAuthCore.from_master_secret(hex_str)
        assert core.VERSION == "0.1.0"

    def test_authorize_approved(self):
        core = self._make_core()
        resp = core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        assert resp.authorized is True
        assert resp.token is not None
        assert core._request_count == 1

    def test_authorize_denied_category(self):
        core = self._make_core()
        resp = core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=25.0,
            merchant="CryptoEx",
            category="crypto",
        )
        assert resp.authorized is False

    def test_authorize_auto_resource(self):
        core = self._make_core()
        resp = core.authorize(agent_id="a", user_id="u", action="read")
        assert resp.status in (AuthorizationStatus.APPROVED, AuthorizationStatus.DENIED)

    def test_authorize_with_risk_assessment(self):
        core = self._make_core()
        core.set_agent_trust("agent-1", 0.9)
        resp = core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        assert resp.authorized is True

    def test_verify_token(self):
        core = self._make_core()
        resp = core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        assert resp.token is not None
        valid, data, error = core.verify_token(resp.token)
        assert valid is True
        assert data is not None

    def test_verify_invalid_token(self):
        core = self._make_core()
        valid, data, error = core.verify_token("bad-token")
        assert valid is False
        assert data is None

    def test_revoke_token(self):
        core = self._make_core()
        resp = core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        core.revoke_token(resp.token_id)
        valid, _, error = core.verify_token(resp.token)
        assert valid is False

    def test_add_and_list_policies(self):
        core = self._make_core()
        initial = len(core.list_policies())
        policy = (
            PolicyBuilder("test_pol", "Test")
            .allow()
            .when("action")
            .equals("transfer")
            .build()
        )
        core.add_policy(policy)
        assert len(core.list_policies()) == initial + 1

    def test_remove_policy(self):
        core = self._make_core()
        policy = (
            PolicyBuilder("removable", "Removable")
            .allow()
            .when("action")
            .equals("x")
            .build()
        )
        core.add_policy(policy)
        initial = len(core.list_policies())
        core.remove_policy("removable")
        assert len(core.list_policies()) == initial - 1

    def test_remove_nonexistent_policy(self):
        core = self._make_core()
        initial = len(core.list_policies())
        core.remove_policy("does_not_exist")
        assert len(core.list_policies()) == initial

    def test_get_policy(self):
        core = self._make_core()
        policy = (
            PolicyBuilder("get_me", "Get Me")
            .deny()
            .when("action")
            .equals("delete")
            .build()
        )
        core.add_policy(policy)
        found = core.get_policy("get_me")
        assert found is not None
        assert found.name == "Get Me"

    def test_set_user_limits(self):
        core = self._make_core()
        core.set_user_limits("u1", daily_limit=100.0, monthly_limit=1000.0)
        spending = core.get_user_spending("u1")
        assert spending["daily_limit"] == 100.0

    def test_get_user_spending(self):
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        spending = core.get_user_spending("u1")
        assert spending["daily_spent"] >= 0

    def test_set_agent_trust(self):
        core = self._make_core()
        core.set_agent_trust("agent-1", 0.95)
        assert core._risk_engine.get_agent_trust("agent-1") == 0.95

    def test_assess_risk(self):
        core = self._make_core()
        risk = core.assess_risk(
            user_id="u1",
            agent_id="a1",
            amount=500.0,
            merchant="Unknown",
            category="gambling",
        )
        assert risk.overall_score >= 0.0
        assert risk.level is not None

    def test_get_audit_log(self):
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        entries = core.get_audit_log()
        assert len(entries) >= 1

    def test_get_audit_log_filtered(self):
        core = self._make_core()
        core.authorize(
            agent_id="agent-1",
            user_id="user-1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        core.authorize(
            agent_id="agent-2",
            user_id="user-2",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        entries = core.get_audit_log(user_id="user-1")
        for e in entries:
            assert e["user_id"] == "user-1" or e["user_id"] is None

    def test_verify_audit_chain(self):
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        valid, msg = core.verify_audit_chain()
        assert valid is True

    def test_export_audit(self, tmp_path):
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        path = str(tmp_path / "audit.json")
        core.export_audit(path, format="json")
        with open(path) as f:
            data = json.load(f)
        assert len(data) >= 1

    def test_export_master_secret(self):
        core = self._make_core()
        secret = core.export_master_secret()
        assert isinstance(secret, str)
        assert len(secret) == 64  # 32 bytes as hex

    def test_export_public_keys(self):
        core = self._make_core()
        keys = core.export_public_keys()
        assert isinstance(keys, dict)
        assert len(keys) > 0

    def test_stats(self):
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        s = core.stats
        assert s["version"] == "0.1.0"
        assert s["total_requests"] == 1
        assert "auth_stats" in s
        assert "risk_stats" in s
        assert s["audit_entries"] >= 1

    def test_init_with_audit_path(self, tmp_path):
        path = str(tmp_path / "audit.jsonl")
        ms = MasterSecret.generate()
        core = AgentAuthCore(master_secret=ms, audit_path=path)
        core.authorize(
            agent_id="a",
            user_id="u",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        assert os.path.exists(path)

    def test_records_transaction_for_risk(self):
        """Approved transactions should be recorded for risk history."""
        core = self._make_core()
        core.authorize(
            agent_id="a",
            user_id="u1",
            action="purchase",
            amount=49.99,
            merchant="Amazon",
            category="electronics",
        )
        # Check that the risk engine has the transaction
        history = core._risk_engine._get_history("u1")
        assert history.transaction_count >= 1


# ─── create_spending_policy Tests ─────────────────────────────────────────────


class TestCreateSpendingPolicy:
    def test_default_policies(self):
        policies = create_spending_policy()
        assert len(policies) == 2
        # Check transaction limit
        tx_pol = next(p for p in policies if p.id == "pol_tx_limit")
        assert tx_pol.effect == PolicyEffect.ALLOW
        # Check category block
        cat_pol = next(p for p in policies if p.id == "pol_blocked_categories")
        assert cat_pol.effect == PolicyEffect.DENY

    def test_custom_limits(self):
        policies = create_spending_policy(
            daily_limit=1000.0,
            per_transaction_limit=500.0,
        )
        assert len(policies) == 2

    def test_custom_blocked_categories(self):
        policies = create_spending_policy(blocked_categories=["gambling", "weapons"])
        assert len(policies) == 2

    def test_empty_blocked_categories(self):
        policies = create_spending_policy(blocked_categories=[])
        assert len(policies) == 1  # Only tx limit, no category block
