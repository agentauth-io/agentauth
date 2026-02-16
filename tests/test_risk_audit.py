"""
Comprehensive tests for core/risk.py and core/audit.py modules.
Targets the two lowest-coverage core modules to push toward 80% target.
"""
import time
import json
import os
import tempfile
import pytest
from collections import defaultdict

from core.risk import (
    RiskLevel,
    RiskFactor,
    RiskFactorScore,
    RiskAssessment,
    TransactionHistory,
    RiskScoringEngine,
)
from core.audit import (
    AuditEventType,
    AuditEntry,
    AuditLog,
)
from core.crypto import MasterSecret, KeyManager, SigningKeyPair


# ─── Risk Module Tests ───────────────────────────────────────────────────────


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"

    def test_all_levels(self):
        assert len(RiskLevel) == 4


class TestRiskFactor:
    """Tests for RiskFactor enum."""

    def test_all_factors(self):
        assert len(RiskFactor) == 13

    def test_key_factors_exist(self):
        assert RiskFactor.AMOUNT_HIGH.value == "amount_high"
        assert RiskFactor.MERCHANT_NEW.value == "merchant_new"
        assert RiskFactor.CATEGORY_BLOCKED.value == "category_blocked"
        assert RiskFactor.VELOCITY_HIGH.value == "velocity_high"
        assert RiskFactor.AGENT_UNTRUSTED.value == "agent_untrusted"


class TestRiskFactorScore:
    """Tests for RiskFactorScore dataclass."""

    def test_create(self):
        rfs = RiskFactorScore(
            factor=RiskFactor.AMOUNT_HIGH,
            score=0.8,
            weight=0.25,
            description="High amount"
        )
        assert rfs.score == 0.8
        assert rfs.weight == 0.25

    def test_weighted_score(self):
        rfs = RiskFactorScore(
            factor=RiskFactor.AMOUNT_HIGH,
            score=0.8,
            weight=0.25,
            description="test"
        )
        assert rfs.weighted_score == pytest.approx(0.2)

    def test_weighted_score_zero(self):
        rfs = RiskFactorScore(
            factor=RiskFactor.AMOUNT_HIGH,
            score=0.0,
            weight=0.5,
            description="test"
        )
        assert rfs.weighted_score == 0.0


class TestRiskAssessment:
    """Tests for RiskAssessment dataclass."""

    def test_to_dict(self):
        factors = [
            RiskFactorScore(RiskFactor.AMOUNT_HIGH, 0.5, 0.25, "High amount"),
            RiskFactorScore(RiskFactor.MERCHANT_NEW, 0.3, 0.1, "New merchant"),
        ]
        assessment = RiskAssessment(
            overall_score=0.45,
            level=RiskLevel.MEDIUM,
            factors=factors,
            recommendations=["MONITOR: Keep in watchlist"],
            evaluation_time_ms=1.23,
        )
        d = assessment.to_dict()
        assert d["score"] == 0.45
        assert d["level"] == "medium"
        assert len(d["factors"]) == 2
        assert d["factors"][0]["factor"] == "amount_high"
        assert d["recommendations"] == ["MONITOR: Keep in watchlist"]
        assert d["evaluation_time_ms"] == 1.23


class TestTransactionHistory:
    """Tests for TransactionHistory."""

    def test_empty_history(self):
        th = TransactionHistory(user_id="user-1")
        assert th.transaction_count == 0
        assert th.average_amount() == 0.0
        assert th.is_new_merchant("Amazon")
        assert th.merchant_frequency("Amazon") == 0

    def test_record_transaction(self):
        th = TransactionHistory(user_id="user-1")
        th.record(49.99, "Amazon", "electronics", timestamp=1700000000.0)
        assert th.transaction_count == 1
        assert th.total_amount == 49.99
        assert not th.is_new_merchant("Amazon")
        assert th.merchant_frequency("Amazon") == 1
        assert th.is_new_merchant("Apple")

    def test_average_amount(self):
        th = TransactionHistory(user_id="user-1")
        th.record(100.0, "A", "cat", timestamp=1700000000.0)
        th.record(200.0, "B", "cat", timestamp=1700001000.0)
        assert th.average_amount() == 150.0

    def test_recent_velocity(self):
        th = TransactionHistory(user_id="user-1")
        now = time.time()
        # Record 5 transactions within last hour
        for i in range(5):
            th.record(10.0, "M", "cat", timestamp=now - i * 60)
        # Record 2 old transactions
        th.record(10.0, "M", "cat", timestamp=now - 7200)
        th.record(10.0, "M", "cat", timestamp=now - 7300)
        assert th.recent_velocity(3600) == 5

    def test_typical_hour_range_default(self):
        th = TransactionHistory(user_id="user-1")
        start, end = th.typical_hour_range()
        assert start == 9
        assert end == 21

    def test_typical_hour_range_with_data(self):
        th = TransactionHistory(user_id="user-1")
        # Record 20 transactions at hour 14 UTC (50400 seconds into day)
        for i in range(20):
            th.record(10.0, "M", "cat", timestamp=50400 + i)
        start, end = th.typical_hour_range()
        assert start <= 14
        assert end >= 14

    def test_cap_at_1000(self):
        th = TransactionHistory(user_id="user-1")
        for i in range(1100):
            th.record(1.0, "M", "cat", timestamp=1700000000.0 + i)
        assert len(th.transactions) == 1000
        assert th.transaction_count == 1100

    def test_category_tracking(self):
        th = TransactionHistory(user_id="user-1")
        th.record(10.0, "M", "electronics", timestamp=1700000000.0)
        th.record(20.0, "M", "electronics", timestamp=1700001000.0)
        th.record(30.0, "M", "food", timestamp=1700002000.0)
        assert th.categories["electronics"] == 2
        assert th.categories["food"] == 1


class TestRiskScoringEngine:
    """Tests for RiskScoringEngine."""

    def test_init_default_weights(self):
        engine = RiskScoringEngine()
        assert engine._evaluation_count == 0
        assert len(engine._weights) == 13

    def test_init_custom_weights(self):
        custom = {RiskFactor.AMOUNT_HIGH: 0.5}
        engine = RiskScoringEngine(weights=custom)
        assert engine._weights[RiskFactor.AMOUNT_HIGH] == 0.5

    def test_set_get_agent_trust(self):
        engine = RiskScoringEngine()
        engine.set_agent_trust("agent-1", 0.9)
        assert engine.get_agent_trust("agent-1") == 0.9
        assert engine.get_agent_trust("unknown") == 0.5  # Default

    def test_agent_trust_clamped(self):
        engine = RiskScoringEngine()
        engine.set_agent_trust("a1", 1.5)
        assert engine.get_agent_trust("a1") == 1.0
        engine.set_agent_trust("a2", -0.5)
        assert engine.get_agent_trust("a2") == 0.0

    def test_assess_first_transaction(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="new-user", agent_id="agent-1",
            amount=25.0, merchant="Amazon", category="electronics"
        )
        assert isinstance(result, RiskAssessment)
        assert result.overall_score >= 0.0
        assert result.overall_score <= 1.0
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.FIRST_TRANSACTION in factor_names

    def test_assess_low_risk(self):
        engine = RiskScoringEngine()
        engine.set_agent_trust("trusted-agent", 0.9)
        # Build history
        for i in range(10):
            engine.record_transaction("user-1", 50.0, "Amazon", "electronics")
        result = engine.assess(
            user_id="user-1", agent_id="trusted-agent",
            amount=45.0, merchant="Amazon", category="electronics"
        )
        assert result.level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_assess_high_amount(self):
        engine = RiskScoringEngine()
        for i in range(10):
            engine.record_transaction("user-1", 50.0, "Amazon", "electronics")
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=999.99, merchant="Amazon", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.AMOUNT_HIGH in factor_names

    def test_assess_moderate_amount(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=300.0, merchant="Amazon", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.AMOUNT_HIGH in factor_names

    def test_assess_unusual_amount(self):
        engine = RiskScoringEngine()
        # Build history with low amounts
        for i in range(10):
            engine.record_transaction("user-1", 20.0, "Amazon", "electronics")
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=200.0, merchant="Amazon", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.AMOUNT_UNUSUAL in factor_names

    def test_assess_risky_category(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=50.0, merchant="CryptoExchange", category="crypto"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.CATEGORY_BLOCKED in factor_names

    def test_assess_medium_risk_category(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=50.0, merchant="JewelryStore", category="jewelry"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.CATEGORY_RISKY in factor_names

    def test_assess_new_merchant(self):
        engine = RiskScoringEngine()
        for i in range(5):
            engine.record_transaction("user-1", 50.0, "Amazon", "electronics")
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=50.0, merchant="NewStore", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.MERCHANT_NEW in factor_names

    def test_assess_risky_merchant(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=50.0, merchant="UnknownSketchyShop", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.MERCHANT_RISKY in factor_names

    def test_assess_untrusted_agent(self):
        engine = RiskScoringEngine()
        engine.set_agent_trust("shady-agent", 0.2)
        result = engine.assess(
            user_id="user-1", agent_id="shady-agent",
            amount=50.0, merchant="Amazon", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.AGENT_UNTRUSTED in factor_names

    def test_assess_new_agent(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="never-seen-before",
            amount=50.0, merchant="Amazon", category="electronics"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.AGENT_NEW in factor_names

    def test_assess_high_velocity(self):
        engine = RiskScoringEngine()
        now = time.time()
        # Simulate 15 recent transactions
        history = engine._get_history("user-1")
        for i in range(15):
            history.record(10.0, "M", "cat", timestamp=now - i * 60)
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=10.0, merchant="M", category="cat"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.VELOCITY_HIGH in factor_names

    def test_assess_elevated_velocity(self):
        engine = RiskScoringEngine()
        now = time.time()
        history = engine._get_history("user-1")
        for i in range(7):
            history.record(10.0, "M", "cat", timestamp=now - i * 60)
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=10.0, merchant="M", category="cat"
        )
        factor_names = [f.factor for f in result.factors]
        assert RiskFactor.VELOCITY_HIGH in factor_names

    def test_record_transaction(self):
        engine = RiskScoringEngine()
        engine.record_transaction("user-1", 50.0, "Amazon", "electronics")
        history = engine._get_history("user-1")
        assert history.transaction_count == 1

    def test_stats(self):
        engine = RiskScoringEngine()
        engine.set_agent_trust("a1", 0.8)
        engine.assess("u1", "a1", 50.0, "Amazon", "electronics")
        s = engine.stats
        assert s["evaluation_count"] == 1
        assert s["users_tracked"] == 1
        assert s["agents_tracked"] == 1

    def test_risk_level_boundaries(self):
        """Verify risk level classification thresholds."""
        engine = RiskScoringEngine()
        # Critical: score >= 0.8
        result = engine.assess(
            user_id="user-1", agent_id="untrusted",
            amount=5000.0, merchant="SketchyShop", category="gambling"
        )
        assert result.level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_recommendations_high_risk(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=5000.0, merchant="Unknown", category="gambling"
        )
        # Should have at least one recommendation
        assert len(result.recommendations) > 0

    def test_evaluation_time(self):
        engine = RiskScoringEngine()
        result = engine.assess(
            user_id="user-1", agent_id="agent-1",
            amount=50.0, merchant="Amazon", category="electronics"
        )
        assert result.evaluation_time_ms >= 0


# ─── Audit Module Tests ──────────────────────────────────────────────────────


class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_all_types(self):
        assert len(AuditEventType) == 14

    def test_key_types(self):
        assert AuditEventType.AUTHORIZATION_REQUEST.value == "auth_request"
        assert AuditEventType.TOKEN_ISSUED.value == "token_issued"
        assert AuditEventType.POLICY_CREATED.value == "policy_created"
        assert AuditEventType.SYSTEM_EVENT.value == "system_event"


class TestAuditEntry:
    """Tests for AuditEntry dataclass."""

    def _make_entry(self, **kwargs):
        defaults = dict(
            id="audit_test_123",
            sequence=1,
            timestamp=1700000000.0,
            prev_hash="0" * 64,
            event_type=AuditEventType.TOKEN_ISSUED,
            agent_id="agent-1",
            user_id="user-1",
            data={"action": "purchase"},
        )
        defaults.update(kwargs)
        return AuditEntry(**defaults)

    def test_create(self):
        entry = self._make_entry()
        assert entry.id == "audit_test_123"
        assert entry.sequence == 1
        assert entry.event_type == AuditEventType.TOKEN_ISSUED

    def test_compute_hash(self):
        entry = self._make_entry()
        h = entry.compute_hash()
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_hash_deterministic(self):
        entry = self._make_entry()
        h1 = entry.compute_hash()
        h2 = entry.compute_hash()
        assert h1 == h2

    def test_hash_changes_with_data(self):
        e1 = self._make_entry(data={"a": 1})
        e2 = self._make_entry(data={"a": 2})
        assert e1.compute_hash() != e2.compute_hash()

    def test_to_dict(self):
        entry = self._make_entry()
        entry.hash = entry.compute_hash()
        entry.signature = "abc123"
        d = entry.to_dict()
        assert d["id"] == "audit_test_123"
        assert d["event_type"] == "token_issued"
        assert d["signature"] == "abc123"

    def test_from_dict_roundtrip(self):
        entry = self._make_entry()
        entry.hash = entry.compute_hash()
        entry.signature = "abc123"
        d = entry.to_dict()
        restored = AuditEntry.from_dict(d)
        assert restored.id == entry.id
        assert restored.event_type == entry.event_type
        assert restored.data == entry.data


class TestAuditLog:
    """Tests for AuditLog."""

    def _make_log(self):
        ms = MasterSecret.generate()
        key = SigningKeyPair.from_master(ms, "audit-test")
        return AuditLog(key), key

    def test_init_empty(self):
        log, _ = self._make_log()
        assert log.length == 0
        assert log.latest_hash == AuditLog.GENESIS_HASH

    def test_append_entry(self):
        log, _ = self._make_log()
        entry = log.append(
            AuditEventType.TOKEN_ISSUED,
            {"token_id": "test123"},
            agent_id="agent-1",
            user_id="user-1",
        )
        assert log.length == 1
        assert entry.sequence == 1
        assert entry.prev_hash == AuditLog.GENESIS_HASH
        assert len(entry.hash) == 64
        assert len(entry.signature) > 0

    def test_append_multiple(self):
        log, _ = self._make_log()
        e1 = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        e2 = log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        assert log.length == 2
        assert e2.prev_hash == e1.hash
        assert e2.sequence == 2

    def test_verify_chain_empty(self):
        log, _ = self._make_log()
        valid, seq, msg = log.verify_chain()
        assert valid is True

    def test_verify_chain_valid(self):
        log, _ = self._make_log()
        for i in range(5):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        valid, seq, msg = log.verify_chain()
        assert valid is True
        assert "verified" in msg.lower() or msg == ""

    def test_verify_chain_tampered_hash(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        # Tamper with first entry's hash
        log._entries[0].hash = "f" * 64
        valid, seq, msg = log.verify_chain()
        assert valid is False

    def test_verify_chain_tampered_data(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        # Tamper with data
        log._entries[0].data = {"a": 999}
        valid, seq, msg = log.verify_chain()
        assert valid is False

    def test_verify_entry(self):
        log, _ = self._make_log()
        entry = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        assert log.verify_entry(entry) is True

    def test_verify_entry_tampered(self):
        log, _ = self._make_log()
        entry = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        entry.hash = "bad" * 20 + "abcd"
        assert log.verify_entry(entry) is False

    def test_get_entries_all(self):
        log, _ = self._make_log()
        for i in range(5):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        entries = log.get_entries()
        assert len(entries) == 5

    def test_get_entries_by_event_type(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        log.append(AuditEventType.TOKEN_ISSUED, {"c": 3})
        entries = log.get_entries(event_type=AuditEventType.TOKEN_ISSUED)
        assert len(entries) == 2

    def test_get_entries_by_agent(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1}, agent_id="agent-1")
        log.append(AuditEventType.TOKEN_ISSUED, {"b": 2}, agent_id="agent-2")
        entries = log.get_entries(agent_id="agent-1")
        assert len(entries) == 1

    def test_get_entries_by_user(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1}, user_id="user-1")
        log.append(AuditEventType.TOKEN_ISSUED, {"b": 2}, user_id="user-2")
        entries = log.get_entries(user_id="user-1")
        assert len(entries) == 1

    def test_get_entries_with_limit(self):
        log, _ = self._make_log()
        for i in range(10):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        entries = log.get_entries(limit=3)
        assert len(entries) == 3

    def test_get_entries_by_sequence_range(self):
        log, _ = self._make_log()
        for i in range(10):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        entries = log.get_entries(start_sequence=3, end_sequence=5)
        for e in entries:
            assert 3 <= e.sequence <= 5

    def test_get_by_id(self):
        log, _ = self._make_log()
        entry = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        found = log.get_by_id(entry.id)
        assert found is not None
        assert found.id == entry.id

    def test_get_by_id_not_found(self):
        log, _ = self._make_log()
        assert log.get_by_id("nonexistent") is None

    def test_subscribe(self):
        log, _ = self._make_log()
        received = []
        log.subscribe(lambda e: received.append(e))
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        assert len(received) == 1
        assert received[0].event_type == AuditEventType.TOKEN_ISSUED

    def test_subscribe_error_handling(self):
        """Subscriber errors should not crash append."""
        log, _ = self._make_log()
        def bad_subscriber(entry):
            raise ValueError("oops")
        log.subscribe(bad_subscriber)
        entry = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        assert entry is not None
        assert log.length == 1

    def test_compute_merkle_root_empty(self):
        log, _ = self._make_log()
        root = log.compute_merkle_root()
        assert root == AuditLog.GENESIS_HASH

    def test_compute_merkle_root_single(self):
        log, _ = self._make_log()
        entry = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        root = log.compute_merkle_root()
        assert root == entry.hash

    def test_compute_merkle_root_multiple(self):
        log, _ = self._make_log()
        for i in range(4):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        root = log.compute_merkle_root()
        assert isinstance(root, str)
        assert len(root) == 64

    def test_compute_merkle_root_odd_count(self):
        log, _ = self._make_log()
        for i in range(3):
            log.append(AuditEventType.SYSTEM_EVENT, {"i": i})
        root = log.compute_merkle_root()
        assert len(root) == 64

    def test_latest_hash(self):
        log, _ = self._make_log()
        e1 = log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        assert log.latest_hash == e1.hash
        e2 = log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        assert log.latest_hash == e2.hash

    def test_stats_empty(self):
        log, _ = self._make_log()
        s = log.stats()
        assert s["total_entries"] == 0
        assert s["first_timestamp"] is None
        assert s["merkle_root"] == AuditLog.GENESIS_HASH

    def test_stats_with_entries(self):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log.append(AuditEventType.TOKEN_ISSUED, {"b": 2})
        log.append(AuditEventType.TOKEN_VERIFIED, {"c": 3})
        s = log.stats()
        assert s["total_entries"] == 3
        assert s["first_timestamp"] is not None
        assert "event_counts" in s
        assert s["event_counts"]["token_issued"] == 2
        assert s["event_counts"]["token_verified"] == 1

    def test_export_json(self, tmp_path):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        path = str(tmp_path / "audit.json")
        log.export(path, format="json")
        with open(path) as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["event_type"] == "token_issued"

    def test_export_jsonl(self, tmp_path):
        log, _ = self._make_log()
        log.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        path = str(tmp_path / "audit.jsonl")
        log.export(path, format="jsonl")
        with open(path) as f:
            lines = [l for l in f.readlines() if l.strip()]
        assert len(lines) == 2

    def test_export_unsupported_format(self, tmp_path):
        log, _ = self._make_log()
        with pytest.raises(ValueError, match="Unsupported format"):
            log.export(str(tmp_path / "out.csv"), format="csv")

    def test_persistence_roundtrip(self, tmp_path):
        ms = MasterSecret.generate()
        key = SigningKeyPair.from_master(ms, "persistence-test")
        path = str(tmp_path / "audit.jsonl")

        # Write entries
        log1 = AuditLog(key, persistence_path=path)
        log1.append(AuditEventType.TOKEN_ISSUED, {"a": 1})
        log1.append(AuditEventType.TOKEN_VERIFIED, {"b": 2})
        assert log1.length == 2

        # Reload
        log2 = AuditLog(key, persistence_path=path)
        assert log2.length == 2
        assert log2._entries[0].event_type == AuditEventType.TOKEN_ISSUED
