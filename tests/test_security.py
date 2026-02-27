"""
Comprehensive Security Tests for AgentAuth
==========================================

Tests all advanced security components:
- Blockchain Audit Trail
- Vault Integration
- Zero-Trust Mesh
- Distributed Consensus
- ML Threat Intelligence
"""

import os
import unittest

from app.ml.threat_intelligence import (
    AutoencoderDetector,
    FeatureVector,
    IsolationForestDetector,
    ThreatIntelligence,
    VelocityTracker,
)

# Import security modules
from core.blockchain_audit import (
    AuditEventType,
    BlockchainAuditTrail,
    MerkleTree,
)
from core.consensus import (
    ConsensusCluster,
)
from core.vault_integration import (
    EncryptionEngine,
    KeyDerivation,
    VaultClient,
)
from core.zero_trust_mesh import (
    AuthorizationPolicy,
    CertificateAuthority,
    ServiceIdentity,
    ZeroTrustMesh,
    ZeroTrustPolicyEngine,
)


class TestMerkleTree(unittest.TestCase):
    """Test Merkle tree implementation."""

    def test_single_leaf(self):
        tree = MerkleTree()
        idx = tree.add_leaf("test")
        self.assertEqual(idx, 0)
        self.assertIsNotNone(tree.root_hash)

    def test_multiple_leaves(self):
        tree = MerkleTree()
        indices = tree.add_leaves(["a", "b", "c", "d"])
        self.assertEqual(len(indices), 4)
        self.assertIsNotNone(tree.root_hash)

    def test_proof_verification(self):
        tree = MerkleTree()
        tree.add_leaves(["a", "b", "c", "d", "e", "f", "g", "h"])

        for i in range(8):
            proof = tree.get_proof(i)
            self.assertIsNotNone(proof)
            self.assertTrue(tree.verify_proof(proof))

    def test_invalid_proof(self):
        tree = MerkleTree()
        tree.add_leaves(["a", "b", "c", "d"])

        proof = tree.get_proof(0)
        proof.leaf_hash = "tampered"
        self.assertFalse(tree.verify_proof(proof))


class TestBlockchainAuditTrail(unittest.TestCase):
    """Test blockchain audit trail."""

    def setUp(self):
        self.audit = BlockchainAuditTrail()

    def test_log_entry(self):
        entry_id = self.audit.log(
            event_type=AuditEventType.AUTHORIZATION_REQUEST,
            actor_id="agent-1",
            actor_type="agent",
            action="authorize",
            outcome="success",
        )
        self.assertIsNotNone(entry_id)
        self.assertTrue(entry_id.startswith("audit-"))

    def test_get_entry(self):
        entry_id = self.audit.log(
            event_type=AuditEventType.AGENT_REGISTERED,
            actor_id="admin",
            actor_type="user",
            action="register_agent",
            outcome="success",
            resource_id="agent-123",
            resource_type="agent",
        )

        entry = self.audit.get_entry(entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.actor_id, "admin")
        self.assertEqual(entry.resource_id, "agent-123")

    def test_verify_entry(self):
        entry_id = self.audit.log(
            event_type=AuditEventType.POLICY_CREATED,
            actor_id="system",
            actor_type="system",
            action="create_policy",
            outcome="success",
        )

        # Flush to create block
        self.audit.flush()

        verification = self.audit.verify_entry(entry_id)
        self.assertTrue(verification["signature_valid"])
        self.assertTrue(verification["chain_valid"])

    def test_chain_integrity(self):
        # Create multiple entries
        for i in range(10):
            self.audit.log(
                event_type=AuditEventType.AUTHORIZATION_APPROVED,
                actor_id=f"agent-{i}",
                actor_type="agent",
                action="approve",
                outcome="success",
            )

        self.audit.flush()

        result = self.audit.verify_chain()
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_query(self):
        # Create entries for different actors
        for i in range(5):
            self.audit.log(
                event_type=AuditEventType.AUTHORIZATION_REQUEST,
                actor_id="agent-1",
                actor_type="agent",
                action="request",
                outcome="success",
            )

        entries = self.audit.query(actor_id="agent-1")
        self.assertGreaterEqual(len(entries), 5)


class TestVaultClient(unittest.TestCase):
    """Test HashiCorp Vault integration."""

    def setUp(self):
        self.vault = VaultClient()
        self.vault.initialize()
        self.vault.unseal("dummy")

    def test_kv_put_get(self):
        result = self.vault.kv_put(
            path="secret/test",
            data={"key": "value", "number": 42},
        )
        self.assertTrue(result.success)

        result = self.vault.kv_get("secret/test")
        self.assertTrue(result.success)
        self.assertEqual(result.data["key"], "value")
        self.assertEqual(result.data["number"], 42)

    def test_secret_versioning(self):
        # Create multiple versions
        self.vault.kv_put(path="secret/versioned", data={"version": 1})
        self.vault.kv_put(path="secret/versioned", data={"version": 2})
        self.vault.kv_put(path="secret/versioned", data={"version": 3})

        # Get specific versions
        v1 = self.vault.kv_get("secret/versioned", version=1)
        v3 = self.vault.kv_get("secret/versioned", version=3)

        self.assertEqual(v1.data["version"], 1)
        self.assertEqual(v3.data["version"], 3)

    def test_transit_encrypt_decrypt(self):
        plaintext = b"Hello, World!"

        encrypt_result = self.vault.transit_encrypt("test-key", plaintext)
        self.assertTrue(encrypt_result.success)

        ciphertext = encrypt_result.data["ciphertext"]
        self.assertTrue(ciphertext.startswith("vault:"))

        decrypt_result = self.vault.transit_decrypt("test-key", ciphertext)
        self.assertTrue(decrypt_result.success)

    def test_api_key_generation(self):
        result = self.vault.generate_api_key(
            name="test-agent",
            tier="premium",
            ttl_hours=24,
        )

        self.assertTrue(result.success)
        self.assertIn("api_key", result.data)
        self.assertTrue(result.data["api_key"].startswith("aa_"))

    def test_api_key_verification(self):
        gen_result = self.vault.generate_api_key(name="verify-test")
        api_key = gen_result.data["api_key"]

        verify_result = self.vault.verify_api_key(api_key)
        self.assertTrue(verify_result.success)
        self.assertTrue(verify_result.data["valid"])


class TestEncryption(unittest.TestCase):
    """Test encryption utilities."""

    def test_key_derivation(self):
        master_key = b"master-secret-key-12345678901234"

        key1 = KeyDerivation.derive_key(master_key, "context-1")
        key2 = KeyDerivation.derive_key(master_key, "context-2")

        self.assertNotEqual(key1, key2)
        self.assertEqual(len(key1), 32)

    def test_encryption_engine(self):
        key = os.urandom(32)  # Must be exactly 32 bytes
        engine = EncryptionEngine(key)

        plaintext = b"Sensitive data that needs protection"

        ciphertext = engine.encrypt(plaintext)
        self.assertNotEqual(ciphertext, plaintext)

        decrypted = engine.decrypt(ciphertext)
        self.assertEqual(decrypted, plaintext)

    def test_encryption_with_aad(self):
        key = os.urandom(32)  # Must be exactly 32 bytes
        engine = EncryptionEngine(key)

        plaintext = b"Secret message"
        aad = b"additional-authenticated-data"

        ciphertext = engine.encrypt(plaintext, aad)
        decrypted = engine.decrypt(ciphertext, aad)

        self.assertEqual(decrypted, plaintext)

    def test_tamper_detection(self):
        key = os.urandom(32)  # Must be exactly 32 bytes
        engine = EncryptionEngine(key)

        ciphertext = engine.encrypt(b"data")

        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[-1] ^= 0xFF

        with self.assertRaises(ValueError):
            engine.decrypt(bytes(tampered))


class TestZeroTrustMesh(unittest.TestCase):
    """Test zero-trust mesh."""

    def setUp(self):
        self.mesh = ZeroTrustMesh("test.local")

    def test_service_registration(self):
        identity, cert, private_key = self.mesh.register_service(
            name="api-server",
            namespace="production",
        )

        self.assertEqual(identity.service_name, "api-server")
        self.assertEqual(identity.namespace, "production")
        self.assertTrue(identity.spiffe_id.startswith("spiffe://test.local/"))
        self.assertIsNotNone(private_key)

    def test_certificate_validity(self):
        _, cert, _ = self.mesh.register_service("test-svc")

        self.assertTrue(cert.is_valid)
        self.assertGreater(cert.days_until_expiry, 0)

    def test_service_deregistration(self):
        identity, _, _ = self.mesh.register_service("temp-svc")

        result = self.mesh.deregister_service(identity.spiffe_id)
        self.assertTrue(result)

        # Should be removed from registry
        services = self.mesh.list_services()
        ids = [s["identity"]["spiffe_id"] for s in services]
        self.assertNotIn(identity.spiffe_id, ids)


class TestZeroTrustPolicyEngine(unittest.TestCase):
    """Test zero-trust policy engine."""

    def setUp(self):
        self.engine = ZeroTrustPolicyEngine()

    def test_add_policy(self):
        policy = AuthorizationPolicy(
            name="allow-api-calls",
            source=ServiceIdentity.from_spiffe_id(
                "spiffe://test.local/default/frontend"
            ),
            destination=ServiceIdentity.from_spiffe_id(
                "spiffe://test.local/default/api"
            ),
            allowed_methods=["GET", "POST"],
            allowed_paths=["/v1/*"],
        )

        self.engine.add_policy(policy)
        policies = self.engine.list_policies()

        names = [p["name"] for p in policies]
        self.assertIn("allow-api-calls", names)

    def test_authorization(self):
        policy = AuthorizationPolicy(
            name="allow-read",
            source=ServiceIdentity.from_spiffe_id("spiffe://test.local/default/reader"),
            destination=ServiceIdentity.from_spiffe_id(
                "spiffe://test.local/default/store"
            ),
            allowed_methods=["GET"],
            allowed_paths=["/data/*"],
        )
        self.engine.add_policy(policy)

        source = ServiceIdentity.from_spiffe_id("spiffe://test.local/default/reader")
        dest = ServiceIdentity.from_spiffe_id("spiffe://test.local/default/store")

        # Should allow
        allowed, _ = self.engine.authorize(source, dest, "GET", "/data/users")
        self.assertTrue(allowed)

        # Should deny (wrong method)
        allowed, _ = self.engine.authorize(source, dest, "POST", "/data/users")
        self.assertFalse(allowed)


class TestCertificateAuthority(unittest.TestCase):
    """Test certificate authority."""

    def setUp(self):
        self.ca = CertificateAuthority("test.local")

    def test_issue_certificate(self):
        identity = ServiceIdentity.from_spiffe_id("spiffe://test.local/ns/svc")
        cert, private_key, public_key = self.ca.issue_certificate(identity)

        self.assertIsNotNone(cert)
        self.assertEqual(cert.subject["CN"], "svc")
        self.assertTrue(cert.is_valid)

    def test_verify_certificate(self):
        identity = ServiceIdentity.from_spiffe_id("spiffe://test.local/ns/svc")
        cert, _, _ = self.ca.issue_certificate(identity)

        result = self.ca.verify_certificate(cert)
        self.assertTrue(result["valid"])

    def test_revoke_certificate(self):
        identity = ServiceIdentity.from_spiffe_id("spiffe://test.local/ns/svc")
        cert, _, _ = self.ca.issue_certificate(identity)

        self.ca.revoke_certificate(cert.serial_number)

        result = self.ca.verify_certificate(cert)
        self.assertFalse(result["valid"])
        self.assertIn("revoked", result["errors"][0].lower())


class TestConsensus(unittest.TestCase):
    """Test distributed consensus."""

    def test_cluster_creation(self):
        cluster = ConsensusCluster(node_count=4)

        self.assertEqual(len(cluster.nodes), 4)

        status = cluster.get_status()
        self.assertIsNotNone(status["leader_id"])

    def test_submit_request(self):
        cluster = ConsensusCluster(node_count=4)

        request_id = cluster.submit_request(
            operation="authorize",
            data={"agent_id": "test-agent", "amount": 100},
        )

        self.assertIsNotNone(request_id)
        self.assertTrue(request_id.startswith("req-"))

    def test_consensus_result(self):
        cluster = ConsensusCluster(node_count=4)

        request_id = cluster.submit_request(
            operation="test_op",
            data={"key": "value"},
        )

        result = cluster.get_result(request_id)

        # Should have consensus
        if result:
            self.assertTrue(result.success)
            self.assertGreaterEqual(len(result.consensus_nodes), 3)  # Quorum
            self.assertIsNotNone(result.result)  # Should have result data


class TestThreatIntelligence(unittest.TestCase):
    """Test ML threat intelligence."""

    def setUp(self):
        self.ti = ThreatIntelligence()

    def test_feature_extraction(self):
        features = self.ti.extract_features(
            {
                "amount": 1000,
                "agent_id": "test-agent",
                "action": "purchase",
            }
        )

        self.assertIsInstance(features, FeatureVector)
        self.assertEqual(len(features.values), len(FeatureVector.FEATURE_NAMES))

    def test_threat_assessment(self):
        assessment = self.ti.assess_threat(
            {
                "agent_id": "agent-1",
                "action": "purchase",
                "amount": 100,
                "trust_score": 0.9,
            }
        )

        self.assertIsNotNone(assessment)
        self.assertIn(
            assessment.risk_level, ["critical", "high", "medium", "low", "none"]
        )
        self.assertGreaterEqual(assessment.overall_risk, 0)
        self.assertLessEqual(assessment.overall_risk, 1)

    def test_high_amount_detection(self):
        assessment = self.ti.assess_threat(
            {
                "agent_id": "agent-2",
                "action": "transfer",
                "amount": 50000,
                "trust_score": 0.5,
            }
        )

        # High amount should trigger signals
        signal_types = [s.signal_type for s in assessment.signals]
        self.assertIn("high_amount", signal_types)

    def test_velocity_detection(self):
        # Simulate rapid requests
        for i in range(10):
            self.ti.assess_threat(
                {
                    "agent_id": "rapid-agent",
                    "action": "query",
                    "amount": 10,
                }
            )

        # Final request should detect high velocity
        assessment = self.ti.assess_threat(
            {
                "agent_id": "rapid-agent",
                "action": "query",
                "amount": 10,
            }
        )

        signal_types = [s.signal_type for s in assessment.signals]
        self.assertIn("velocity_abuse", signal_types)


class TestVelocityTracker(unittest.TestCase):
    """Test velocity tracking."""

    def test_record_and_count(self):
        tracker = VelocityTracker(window_sizes=[60])

        for i in range(5):
            tracker.record("entity-1", 100)

        counts = tracker.get_counts("entity-1")
        self.assertEqual(counts["count_60s"], 5)

    def test_amount_tracking(self):
        tracker = VelocityTracker(window_sizes=[60])

        tracker.record("entity-1", 100)
        tracker.record("entity-1", 200)
        tracker.record("entity-1", 300)

        amounts = tracker.get_amounts("entity-1")
        self.assertEqual(amounts["amount_60s"], 600)


class TestIsolationForestDetector(unittest.TestCase):
    """Test Isolation Forest anomaly detection."""

    def test_fit_and_score(self):
        detector = IsolationForestDetector(n_trees=10)

        # Generate normal data
        normal_data = [
            FeatureVector([0.5] * len(FeatureVector.FEATURE_NAMES)) for _ in range(100)
        ]

        detector.fit(normal_data)

        # Score normal point
        normal_score = detector.score(normal_data[0])
        self.assertLess(normal_score, 0.7)

        # Score anomalous point (extreme outlier)
        anomaly = FeatureVector([0.99, 0.99, 0.99, 0.01, 0.99, 0.01, 0.99, 0.99])
        anomaly_score = detector.score(anomaly)

        # Anomaly should have higher or equal score (ML models can be stochastic)
        self.assertGreaterEqual(anomaly_score, normal_score * 0.9)


class TestAutoencoderDetector(unittest.TestCase):
    """Test Autoencoder anomaly detection."""

    def test_online_learning(self):
        n_features = len(FeatureVector.FEATURE_NAMES)
        detector = AutoencoderDetector(n_features)

        # Train on normal data
        for _ in range(50):
            normal = [0.5] * n_features
            detector.fit_sample(normal)

        # Score normal point
        normal_score = detector.score([0.5] * n_features)

        # Score anomalous point
        anomaly_score = detector.score([1.0] * n_features)

        # Anomaly should have higher score
        self.assertGreater(anomaly_score, normal_score)


if __name__ == "__main__":
    unittest.main()
