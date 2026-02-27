"""
Tests for OPA (Open Policy Agent) service.

Pure Python tests - no external OPA server needed.
"""

import pytest

from app.services.opa_service import (
    AGENTAUTH_POLICIES,
    LocalPolicyEngine,
    OPAService,
    PolicyDecision,
    RegoPolicy,
    check_policy,
)


class TestPolicyDecision:
    def test_to_dict_all_fields(self):
        d = PolicyDecision(
            allowed=True,
            policy_id="test.policy",
            decision_id="dec_123",
            reasons=["reason1"],
            bindings={"key": "val"},
            evaluation_time_ms=1.234,
            policy_version="1.0",
        )
        result = d.to_dict()
        assert result["allowed"] is True
        assert result["policy_id"] == "test.policy"
        assert result["decision_id"] == "dec_123"
        assert result["reasons"] == ["reason1"]
        assert result["evaluation_time_ms"] == 1.23
        assert result["policy_version"] == "1.0"

    def test_to_dict_empty_reasons(self):
        d = PolicyDecision(allowed=True, policy_id="p", decision_id="d")
        result = d.to_dict()
        assert result["reasons"] == []
        assert result["bindings"] == {}


class TestRegoPolicy:
    def test_to_dict(self):
        policy = RegoPolicy(
            policy_id="test.policy",
            rego_code="package test\ndefault allow = true",
            description="Test policy",
        )
        d = policy.to_dict()
        assert d["policy_id"] == "test.policy"
        assert "package test" in d["rego"]
        assert d["description"] == "Test policy"
        assert d["version"] == "1.0"
        assert "created_at" in d

    def test_predefined_policies_exist(self):
        assert "spending_limits" in AGENTAUTH_POLICIES
        assert "merchant_rules" in AGENTAUTH_POLICIES
        assert "category_controls" in AGENTAUTH_POLICIES
        assert "time_based" in AGENTAUTH_POLICIES
        assert "fraud_risk" in AGENTAUTH_POLICIES


class TestLocalPolicyEngine:
    def test_spending_limits_allows_within_limits(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=100.0,
            daily_spent=200.0,
            monthly_spent=500.0,
            limits={"per_transaction": 200.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is True
        assert decision.reasons == []

    def test_spending_limits_denies_per_transaction(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=300.0,
            daily_spent=0.0,
            monthly_spent=0.0,
            limits={"per_transaction": 200.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is False
        assert any("per-transaction" in r for r in decision.reasons)

    def test_spending_limits_denies_daily(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=100.0,
            daily_spent=950.0,
            monthly_spent=950.0,
            limits={"per_transaction": 500.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is False
        assert any("daily" in r for r in decision.reasons)

    def test_spending_limits_denies_monthly(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=100.0,
            daily_spent=0.0,
            monthly_spent=4950.0,
            limits={"per_transaction": 500.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is False
        assert any("monthly" in r for r in decision.reasons)

    def test_spending_limits_multiple_violations(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=600.0,
            daily_spent=900.0,
            monthly_spent=4800.0,
            limits={"per_transaction": 500.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is False
        assert len(decision.reasons) == 3

    def test_spending_limits_no_limits_set(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_spending_limits(
            amount=99999.0,
            daily_spent=0.0,
            monthly_spent=0.0,
            limits={},
        )
        assert decision.allowed is True

    def test_merchant_rules_allows_not_blacklisted(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_merchant_rules(
            merchant_id="amazon",
            whitelist=[],
            blacklist=["scam_store"],
        )
        assert decision.allowed is True

    def test_merchant_rules_denies_blacklisted(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_merchant_rules(
            merchant_id="scam_store",
            whitelist=[],
            blacklist=["scam_store"],
        )
        assert decision.allowed is False
        assert any("blacklisted" in r for r in decision.reasons)

    def test_merchant_rules_whitelist_allows_listed(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_merchant_rules(
            merchant_id="amazon",
            whitelist=["amazon", "walmart"],
            blacklist=[],
        )
        assert decision.allowed is True

    def test_merchant_rules_whitelist_denies_not_listed(self):
        engine = LocalPolicyEngine()
        decision = engine.evaluate_merchant_rules(
            merchant_id="unknown_store",
            whitelist=["amazon", "walmart"],
            blacklist=[],
        )
        assert decision.allowed is False
        assert any("not in whitelist" in r for r in decision.reasons)

    def test_register_policy(self):
        engine = LocalPolicyEngine()
        policy = RegoPolicy("test.policy", "package test")
        engine.register_policy(policy)
        assert "test.policy" in engine.policies


class TestOPAService:
    @pytest.mark.asyncio
    async def test_evaluate_spending_limits_local(self):
        service = OPAService()
        decision = await service.evaluate(
            "agentauth.spending_limits",
            input_data={"amount": 50.0, "daily_spent": 100.0, "monthly_spent": 200.0},
            data={
                "limits": {"per_transaction": 200.0, "daily": 1000.0, "monthly": 5000.0}
            },
        )
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_evaluate_merchant_rules_local(self):
        service = OPAService()
        decision = await service.evaluate(
            "agentauth.merchant_rules",
            input_data={"merchant_id": "bad_store"},
            data={"whitelist": [], "blacklist": ["bad_store"]},
        )
        assert decision.allowed is False

    @pytest.mark.asyncio
    async def test_evaluate_unknown_policy_allows(self):
        service = OPAService()
        decision = await service.evaluate(
            "agentauth.unknown_policy",
            input_data={},
        )
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_check_authorization(self):
        service = OPAService()
        decisions = await service.check_authorization(
            consent_id="c_1",
            amount=50.0,
            merchant_id="amazon",
            limits={"per_transaction": 200.0, "daily": 1000.0, "monthly": 5000.0},
            rules={"merchant_blacklist": []},
        )
        assert "spending_limits" in decisions
        assert "merchant_rules" in decisions
        assert decisions["spending_limits"].allowed is True
        assert decisions["merchant_rules"].allowed is True

    @pytest.mark.asyncio
    async def test_check_authorization_denied(self):
        service = OPAService()
        decisions = await service.check_authorization(
            consent_id="c_1",
            amount=500.0,
            merchant_id="bad_store",
            limits={"per_transaction": 200.0},
            rules={"merchant_blacklist": ["bad_store"]},
        )
        assert decisions["spending_limits"].allowed is False
        assert decisions["merchant_rules"].allowed is False

    def test_get_combined_decision_all_allowed(self):
        service = OPAService()
        decisions = {
            "p1": PolicyDecision(allowed=True, policy_id="p1", decision_id="d1"),
            "p2": PolicyDecision(allowed=True, policy_id="p2", decision_id="d2"),
        }
        combined = service.get_combined_decision(decisions)
        assert combined.allowed is True
        assert combined.reasons == []

    def test_get_combined_decision_one_denied(self):
        service = OPAService()
        decisions = {
            "p1": PolicyDecision(allowed=True, policy_id="p1", decision_id="d1"),
            "p2": PolicyDecision(
                allowed=False,
                policy_id="p2",
                decision_id="d2",
                reasons=["limit exceeded"],
            ),
        }
        combined = service.get_combined_decision(decisions)
        assert combined.allowed is False
        assert "limit exceeded" in combined.reasons


class TestCheckPolicyConvenience:
    @pytest.mark.asyncio
    async def test_check_policy_allowed(self):
        import app.services.opa_service as omod

        omod._opa_service = None

        decision = await check_policy(
            amount=50.0,
            merchant_id="amazon",
            limits={"per_transaction": 200.0, "daily": 1000.0, "monthly": 5000.0},
        )
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_check_policy_denied(self):
        import app.services.opa_service as omod

        omod._opa_service = None

        decision = await check_policy(
            amount=500.0,
            merchant_id="amazon",
            limits={"per_transaction": 200.0},
        )
        assert decision.allowed is False
