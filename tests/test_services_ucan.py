"""
Integration tests for UCAN (User-Controlled Authorization Networks) Service.

Tests the full UCAN capability delegation lifecycle:
1. Key generation (Ed25519)
2. UCAN creation with capabilities
3. Token verification
4. Capability attenuation (sub-delegation)
5. Capability checking
6. Token serialization
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.ucan_service import (
    Capability,
    UCANError,
    UCANService,
    UCANToken,
    get_ucan_service,
    create_ucan_token,
    verify_ucan_token,
    check_capability,
    attenuate_ucan,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Create a fresh UCAN service for each test."""
    return UCANService()


@pytest.fixture
def sample_capabilities():
    """Sample capabilities for testing."""
    return [
        Capability(
            resource="agentauth:consent:*",
            action="create",
            caveats={"max_amount": 500},
        ),
        Capability(
            resource="agentauth:authorize:*",
            action="execute",
        ),
    ]


@pytest.fixture
def keypair(service):
    """Generate a keypair for testing."""
    return service.generate_keypair()


# ============================================================================
# Key Generation Tests
# ============================================================================

class TestKeyGeneration:
    """Tests for Ed25519 key generation."""

    def test_generate_keypair(self, service):
        """Test key pair generation."""
        keypair = service.generate_keypair()

        assert "private_key" in keypair
        assert "public_key" in keypair
        assert "did" in keypair
        assert keypair["did"].startswith("did:key:z")

    def test_key_consistency(self, service):
        """Test that derived DID is consistent."""
        keypair = service.generate_keypair()

        # Generate again with same key should produce same DID
        did2 = service._public_key_to_did(keypair["public_key"])
        assert keypair["did"] == did2

    def test_did_format(self, service):
        """Test DID format follows did:key spec."""
        keypair = service.generate_keypair()
        did = keypair["did"]

        # Should start with did:key:z
        assert did.startswith("did:key:z")
        # Should be base58-like (alphanumeric)
        assert all(c.isalnum() or c == ':' for c in did)


# ============================================================================
# Token Creation Tests
# ============================================================================

class TestTokenCreation:
    """Tests for UCAN token creation."""

    def test_create_token(self, service, keypair, sample_capabilities):
        """Test creating a UCAN token."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTestAudience",
            capabilities=sample_capabilities,
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        assert isinstance(token, UCANToken)
        assert token.payload.iss == keypair["did"]
        assert token.payload.aud == "did:key:zTestAudience"
        assert len(token.payload.att) == len(sample_capabilities)

    def test_token_expiration(self, service, keypair):
        """Test token has correct expiration."""
        ttl = 3600

        before_create = datetime.now(timezone.utc)
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTest",
            capabilities=[],
            private_key=keypair["private_key"],
            ttl_seconds=ttl,
        )
        after_create = datetime.now(timezone.utc)

        exp_timestamp = datetime.fromtimestamp(token.payload.exp, timezone.utc)
        expected_exp = before_create + timedelta(seconds=ttl)

        # Should be within a few seconds
        time_diff = abs((exp_timestamp - expected_exp).total_seconds())
        assert time_diff < 5

    def test_token_with_caveats(self, service, keypair):
        """Test token with capability caveats."""
        capabilities = [
            Capability(
                resource="agentauth:consent:*",
                action="create",
                caveats={"max_amount": 500, "allowed_merchants": ["amazon"]},
            ),
        ]

        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTest",
            capabilities=capabilities,
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        # Check caveats are preserved
        cap = token.payload.att[0]
        assert cap.caveats["max_amount"] == 500
        assert "amazon" in cap.caveats["allowed_merchants"]


# ============================================================================
# Token Verification Tests
# ============================================================================

class TestTokenVerification:
    """Tests for UCAN token verification."""

    def test_verify_valid_token(self, service, keypair, sample_capabilities):
        """Test verifying a valid token."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTestAudience",
            capabilities=sample_capabilities,
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        result = service.verify_token(
            token=token,
            public_key=keypair["public_key"],
        )

        assert result["valid"] is True
        assert "issuer" in result
        assert "capabilities" in result

    def test_verify_expired_token(self, service, keypair):
        """Test that expired tokens fail verification."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTest",
            capabilities=[],
            private_key=keypair["private_key"],
            ttl_seconds=1,  # 1 second
        )

        # Wait for expiration
        import time
        time.sleep(2)

        result = service.verify_token(
            token=token,
            public_key=keypair["public_key"],
        )

        assert result["valid"] is False
        assert "expired" in result.get("error", "").lower()

    def test_verify_with_wrong_key(self, service, keypair):
        """Test verification fails with wrong public key."""
        keypair2 = service.generate_keypair()

        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zTest",
            capabilities=[],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        result = service.verify_token(
            token=token,
            public_key=keypair2["public_key"],  # Wrong key
        )

        assert result["valid"] is False


# ============================================================================
# Capability Tests
# ============================================================================

class TestCapabilities:
    """Tests for UCAN capabilities."""

    def test_capability_creation(self):
        """Test creating a capability."""
        cap = Capability(
            resource="agentauth:consent:*",
            action="create",
            caveats={"max_amount": 500},
        )

        assert cap.resource == "agentauth:consent:*"
        assert cap.action == "create"
        assert cap.caveats["max_amount"] == 500

    def test_capability_to_dict(self):
        """Test capability serialization."""
        cap = Capability(
            resource="agentauth:consent:*",
            action="create",
            caveats={"max_amount": 500},
        )

        d = cap.to_dict()
        assert d["with"] == "agentauth:consent:*"
        assert d["can"] == "create"
        assert d["caveats"]["max_amount"] == 500

    def test_capability_subset_exact_match(self):
        """Test exact capability match."""
        parent = Capability(resource="agentauth:consent:123", action="create")
        child = Capability(resource="agentauth:consent:123", action="create")

        assert child.is_subset_of(parent) is True

    def test_capability_subset_wildcard(self):
        """Test wildcard resource matching."""
        parent = Capability(resource="agentauth:consent:*", action="create")
        child = Capability(resource="agentauth:consent:123", action="create")

        assert child.is_subset_of(parent) is True

    def test_capability_subset_action_mismatch(self):
        """Test action mismatch fails."""
        parent = Capability(resource="agentauth:consent:*", action="read")
        child = Capability(resource="agentauth:consent:123", action="create")

        assert child.is_subset_of(parent) is False


# ============================================================================
# Attenuation Tests
# ============================================================================

class TestAttenuation:
    """Tests for UCAN capability attenuation."""

    def test_attenuate_token(self, service, keypair):
        """Test attenuating a token with stricter capabilities."""
        # Create parent token with broad capabilities
        parent_token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAgent",
            capabilities=[
                Capability(resource="agentauth:consent:*", action="create"),
            ],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        # Attenuate with stricter limits
        attenuated = service.attenuate_token(
            token=parent_token,
            capabilities=[
                Capability(
                    resource="agentauth:consent:*",
                    action="create",
                    caveats={"max_amount": 100},
                ),
            ],
        )

        assert len(attenuated.payload.att) == 1
        assert attenuated.payload.att[0].caveats["max_amount"] == 100

    def test_attenuated_token_verification(self, service, keypair):
        """Test that attenuated tokens can still be verified."""
        parent_token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAgent",
            capabilities=[Capability(resource="agentauth:consent:*", action="create")],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        attenuated = service.attenuate_token(
            token=parent_token,
            capabilities=[Capability(resource="agentauth:consent:123", action="create")],
        )

        result = service.verify_token(attenuated, keypair["public_key"])
        assert result["valid"] is True


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_ucan_service_singleton(self):
        """Test service is a singleton."""
        service1 = get_ucan_service()
        service2 = get_ucan_service()
        assert service1 is service2

    def test_create_ucan_token(self):
        """Test create_ucan_token convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.create_token.return_value = MagicMock(
                token_id="test_token",
                payload=MagicMock(att=[]),
            )
            mock_get.return_value = mock_service

            token = create_ucan_token(
                issuer_did="did:key:zIssuer",
                audience_did="did:key:zAudience",
                capabilities=[],
                private_key="test_key",
            )

            assert token is not None
            mock_service.create_token.assert_called_once()

    def test_verify_ucan_token(self):
        """Test verify_ucan_token convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.verify_token.return_value = {"valid": True}
            mock_get.return_value = mock_service

            result = verify_ucan_token(
                token=MagicMock(),
                public_key="test_key",
            )

            assert result["valid"] is True

    def test_check_capability(self):
        """Test check_capability convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.check_capability.return_value = {"has_capability": True}
            mock_get.return_value = mock_service

            result = check_capability(
                token=MagicMock(),
                resource="agentauth:consent:*",
                action="create",
            )

            assert result["has_capability"] is True


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error conditions."""

    def test_invalid_did_format(self, service):
        """Test handling of invalid DID format."""
        keypair = service.generate_keypair()

        with pytest.raises((UCANError, ValueError)):
            service.create_token(
                issuer_did="invalid_did_format",
                audience_did="did:key:zAudience",
                capabilities=[],
                private_key=keypair["private_key"],
                ttl_seconds=3600,
            )

    def test_expired_token(self, service, keypair):
        """Test verification of expired token."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[],
            private_key=keypair["private_key"],
            ttl_seconds=1,  # 1 second
        )

        # Wait for expiration
        import time
        time.sleep(2)

        result = service.verify_token(token, keypair["public_key"])
        assert result["valid"] is False
        assert "expired" in result.get("error", "").lower()

    def test_invalid_signature(self, service, keypair):
        """Test verification with wrong public key."""
        keypair2 = service.generate_keypair()

        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        result = service.verify_token(token, keypair2["public_key"])
        assert result["valid"] is False


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for UCAN operations."""

    def test_token_creation_performance(self, service, keypair):
        """Test token creation is fast (<50ms)."""
        import time

        capabilities = [Capability(resource="agentauth:consent:*", action="create")]

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.create_token(
                issuer_did=keypair["did"],
                audience_did="did:key:zAudience",
                capabilities=capabilities,
                private_key=keypair["private_key"],
                ttl_seconds=3600,
            )
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 50, f"Token creation took {avg_time:.2f}ms, expected <50ms"

    def test_token_verification_performance(self, service, keypair):
        """Test token verification is fast (<20ms)."""
        import time

        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[Capability(resource="agentauth:consent:*", action="create")],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.verify_token(token, keypair["public_key"])
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 20, f"Token verification took {avg_time:.2f}ms, expected <20ms"

    def test_capability_check_performance(self, service, keypair):
        """Test capability checking is fast (<10ms)."""
        import time

        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[
                Capability(resource="agentauth:consent:*", action="create"),
                Capability(resource="agentauth:authorize:*", action="execute"),
            ],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.check_capability(
                token=token,
                resource="agentauth:consent:123",
                action="create",
            )
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 10, f"Capability check took {avg_time:.2f}ms, expected <10ms"


# ============================================================================
# Serialization Tests
# ============================================================================

class TestSerialization:
    """Tests for UCAN token serialization."""

    def test_token_to_dict(self, service, keypair, sample_capabilities):
        """Test token serialization to dict."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=sample_capabilities,
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        d = token.to_dict()

        assert "payload" in d
        assert "signature" in d
        assert d["payload"]["iss"] == keypair["did"]
        assert d["payload"]["aud"] == "did:key:zAudience"

    def test_token_serialize_deserialize(self, service, keypair, sample_capabilities):
        """Test full serialize/deserialize cycle."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=sample_capabilities,
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        # Serialize
        serialized = service.serialize_token(token)
        assert isinstance(serialized, str)

        # Deserialize
        deserialized = service.deserialize_token(serialized)

        assert isinstance(deserialized, UCANToken)
        assert deserialized.payload.iss == token.payload.iss
        assert deserialized.payload.aud == token.payload.aud

    def test_serialize_compact_format(self, service, keypair):
        """Test compact serialization format."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[Capability(resource="agentauth:consent:*", action="create")],
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        serialized = service.serialize_token(token, compact=True)

        # Compact format should be shorter
        full_serialized = service.serialize_token(token, compact=False)
        assert len(serialized) <= len(full_serialized)


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error conditions."""

    def test_invalid_did_format(self, service, keypair):
        """Test handling of invalid DID format."""
        with pytest.raises((UCANError, ValueError)):
            service.create_token(
                issuer_did="invalid_did",
                audience_did="did:key:zAudience",
                capabilities=[],
                private_key=keypair["private_key"],
                ttl_seconds=3600,
            )

    def test_invalid_private_key(self, service):
        """Test handling of invalid private key."""
        with pytest.raises((UCANError, ValueError)):
            service.create_token(
                issuer_did="did:key:zIssuer",
                audience_did="did:key:zAudience",
                capabilities=[],
                private_key="invalid_key",
                ttl_seconds=3600,
            )

    def test_malformed_token(self, service):
        """Test handling of malformed token."""
        with pytest.raises((UCANError, ValueError)):
            service.deserialize_token("not_a_valid_token")

    def test_empty_capabilities(self, service, keypair):
        """Test token with empty capabilities."""
        token = service.create_token(
            issuer_did=keypair["did"],
            audience_did="did:key:zAudience",
            capabilities=[],  # Empty
            private_key=keypair["private_key"],
            ttl_seconds=3600,
        )

        assert isinstance(token, UCANToken)
        assert len(token.payload.att) == 0


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_ucan_service_singleton(self):
        """Test service is a singleton."""
        service1 = get_ucan_service()
        service2 = get_ucan_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_create_ucan_token(self):
        """Test create_ucan_token convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.create_token.return_value = MagicMock(
                token_id="test_token",
                payload=MagicMock(att=[]),
            )
            mock_get.return_value = mock_service

            token = create_ucan_token(
                issuer_did="did:key:zIssuer",
                audience_did="did:key:zAudience",
                capabilities=[],
                private_key="test_key",
            )

            assert token is not None
            mock_service.create_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_ucan_token(self):
        """Test verify_ucan_token convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.verify_token.return_value = {"valid": True}
            mock_get.return_value = mock_service

            result = verify_ucan_token(
                token=MagicMock(),
                public_key="test_key",
            )

            assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_check_capability(self):
        """Test check_capability convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.check_capability.return_value = {"has_capability": True}
            mock_get.return_value = mock_service

            result = check_capability(
                token=MagicMock(),
                resource="agentauth:consent:*",
                action="create",
            )

            assert result["has_capability"] is True

    @pytest.mark.asyncio
    async def test_attenuate_ucan(self):
        """Test attenuate_ucan convenience function."""
        with patch('app.services.ucan_service.get_ucan_service') as mock_get:
            mock_service = MagicMock()
            mock_service.attenuate_token.return_value = MagicMock(
                token_id="attenuated_token",
            )
            mock_get.return_value = mock_service

            result = attenuate_ucan(
                token=MagicMock(),
                capabilities=[],
            )

            assert result is not None
            mock_service.attenuate_token.assert_called_once()
