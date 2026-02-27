"""
Integration tests for Biscuit Token Service.

Tests the full Biscuit token lifecycle:
1. Key generation
2. Token creation (attenuation)
3. Token verification
4. Authorization checks
5. Token serialization
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.biscuit_service import (
    BiscuitCheck,
    BiscuitError,
    BiscuitFact,
    BiscuitService,
    BiscuitToken,
    authorize_with_biscuit,
    create_biscuit_token,
    get_biscuit_service,
    verify_biscuit_token,
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service():
    """Create a fresh Biscuit service for each test."""
    return BiscuitService()


@pytest.fixture
def sample_facts():
    """Sample facts for testing."""
    return [
        BiscuitFact("user_id", ["user_123"]),
        BiscuitFact("max_amount", [500]),
        BiscuitFact("allowed_merchant", ["amazon"]),
    ]


@pytest.fixture
def sample_checks():
    """Sample checks for testing."""
    return [
        BiscuitCheck("time($t), $t <= 1704067200"),
        BiscuitCheck("merchant($m), $m in [\"amazon\", \"walmart\"]"),
    ]


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
        assert "key_id" in keypair
        assert len(keypair["public_key"]) > 0
        assert len(keypair["private_key"]) > 0

    def test_key_id_generation(self, service):
        """Test key ID is derived from public key."""
        keypair1 = service.generate_keypair()
        keypair2 = service.generate_keypair()

        # Different keys should have different IDs
        assert keypair1["key_id"] != keypair2["key_id"]

        # Key ID should be consistent (derived from public key)
        assert len(keypair1["key_id"]) == 16  # First 16 chars of hash

    def test_key_serialization(self, service):
        """Test keys can be serialized and deserialized."""
        keypair = service.generate_keypair()

        # Should be base64-encoded strings
        import base64
        try:
            base64.b64decode(keypair["public_key"])
            base64.b64decode(keypair["private_key"])
        except Exception:
            pytest.fail("Keys should be base64-encoded")


# ============================================================================
# Token Creation Tests
# ============================================================================

class TestTokenCreation:
    """Tests for Biscuit token creation."""

    def test_create_root_token(self, service, sample_facts):
        """Test creating a root token."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=sample_facts,
            ttl_seconds=3600,
        )

        assert isinstance(token, BiscuitToken)
        assert token.root_key_id == keypair["key_id"]
        assert len(token.blocks) == 1
        # Check that all sample facts are present (expires_at is auto-added)
        for fact in sample_facts:
            assert fact in token.blocks[0].facts

    def test_token_with_checks(self, service, sample_facts, sample_checks):
        """Test creating token with authorization checks."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=sample_facts,
            checks=sample_checks,
            ttl_seconds=3600,
        )

        assert len(token.blocks[0].checks) == len(sample_checks)

    def test_token_expiration(self, service):
        """Test token has correct expiration."""
        keypair = service.generate_keypair()
        ttl = 3600

        before_create = datetime.now(timezone.utc)
        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[],
            ttl_seconds=ttl,
        )
        after_create = datetime.now(timezone.utc)

        # Expiration should be approximately ttl seconds from now
        expected_exp = before_create + timedelta(seconds=ttl)
        time_diff = abs((token.expires_at - expected_exp).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_token_serialization(self, service, sample_facts):
        """Test token can be serialized and deserialized."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=sample_facts,
            ttl_seconds=3600,
        )

        # Serialize
        serialized = service.serialize_token(token)
        assert isinstance(serialized, str)
        assert len(serialized) > 0

        # Deserialize
        deserialized = service.deserialize_token(serialized)
        assert isinstance(deserialized, BiscuitToken)
        # root_key_id should match (extracted from serialized token)
        assert deserialized.root_key_id == token.root_key_id


# ============================================================================
# Token Attenuation Tests
# ============================================================================

class TestTokenAttenuation:
    """Tests for offline token attenuation."""

    def test_attenuate_token(self, service, sample_facts):
        """Test attenuating a token with additional restrictions."""
        keypair = service.generate_keypair()

        # Create root token
        root_token = service.create_token(
            root_key=keypair["private_key"],
            facts=sample_facts,
            ttl_seconds=3600,
        )

        # Attenuate with new fact
        new_fact = BiscuitFact("merchant", ["amazon"])
        attenuated = service.attenuate_token(
            token=root_token,
            facts=[new_fact],
        )

        assert len(attenuated.blocks) == 2  # Root + attenuation block
        assert any(f.name == "merchant" for f in attenuated.blocks[1].facts)

    def test_attenuate_with_check(self, service):
        """Test attenuating with additional checks."""
        keypair = service.generate_keypair()

        root_token = service.create_token(
            root_key=keypair["private_key"],
            facts=[BiscuitFact("user_id", ["user_123"])],
            ttl_seconds=3600,
        )

        # Add stricter check
        strict_check = BiscuitCheck("amount($a), $a <= 100")
        attenuated = service.attenuate_token(
            token=root_token,
            checks=[strict_check],
        )

        assert len(attenuated.blocks[1].checks) == 1

    def test_attenuated_token_verification(self, service):
        """Test that attenuated tokens can still be verified."""
        keypair = service.generate_keypair()

        root_token = service.create_token(
            root_key=keypair["private_key"],
            facts=[BiscuitFact("user_id", ["user_123"])],
            ttl_seconds=3600,
        )

        attenuated = service.attenuate_token(
            token=root_token,
            facts=[BiscuitFact("merchant", ["amazon"])],
        )

        # Should verify successfully
        result = service.verify_token(
            token=attenuated,
            public_key=keypair["public_key"],
        )

        assert result["valid"] is True


# ============================================================================
# Token Verification Tests
# ============================================================================

class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_token(self, service, sample_facts):
        """Test verifying a valid token."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=sample_facts,
            ttl_seconds=3600,
        )

        result = service.verify_token(
            token=token,
            public_key=keypair["public_key"],
        )

        assert result["valid"] is True
        assert "facts" in result
        assert result["revoked"] is False

    def test_verify_expired_token(self, service):
        """Test that expired tokens fail verification."""
        keypair = service.generate_keypair()

        # Create token with very short TTL
        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[],
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
        assert "expired" in result["error"].lower()

    def test_verify_with_wrong_key(self, service):
        """Test that tokens fail verification with wrong public key."""
        keypair1 = service.generate_keypair()
        keypair2 = service.generate_keypair()

        token = service.create_token(
            root_key=keypair1["private_key"],
            facts=[],
            ttl_seconds=3600,
        )

        result = service.verify_token(
            token=token,
            public_key=keypair2["public_key"],
        )

        assert result["valid"] is False

    def test_verify_revoked_token(self, service):
        """Test that revoked tokens fail verification."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[],
            ttl_seconds=3600,
        )

        # Revoke the token
        service.revoke_token(token.token_id)

        result = service.verify_token(
            token=token,
            public_key=keypair["public_key"],
        )

        assert result["valid"] is False
        assert result["revoked"] is True


# ============================================================================
# Authorization Tests
# ============================================================================

class TestAuthorization:
    """Tests for Datalog-based authorization."""

    def test_authorize_with_matching_facts(self, service):
        """Test authorization with matching facts."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[
                BiscuitFact("user_id", ["user_123"]),
                BiscuitFact("max_amount", [500]),
            ],
            checks=[
                BiscuitCheck("user_id($u)"),
            ],
            ttl_seconds=3600,
        )

        # Should authorize
        result = service.authorize(
            token=token,
            public_key=keypair["public_key"],
            query_facts=[
                BiscuitFact("user_id", ["user_123"]),
            ],
        )

        assert result["authorized"] is True

    def test_authorize_with_missing_fact(self, service):
        """Test authorization fails with missing required facts."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[
                BiscuitFact("user_id", ["user_123"]),
            ],
            checks=[
                BiscuitCheck("merchant($m)"),  # Requires merchant fact
            ],
            ttl_seconds=3600,
        )

        # Should fail - no merchant fact provided
        result = service.authorize(
            token=token,
            public_key=keypair["public_key"],
            query_facts=[],
        )

        assert result["authorized"] is False

    def test_authorize_with_amount_check(self, service):
        """Test amount-based authorization."""
        keypair = service.generate_keypair()

        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[
                BiscuitFact("user_id", ["user_123"]),
                BiscuitFact("max_amount", [500]),
            ],
            checks=[
                BiscuitCheck("amount($a), $a <= 500"),
            ],
            ttl_seconds=3600,
        )

        # Should authorize amount within limit
        result = service.authorize(
            token=token,
            public_key=keypair["public_key"],
            query_facts=[
                BiscuitFact("amount", [300]),
            ],
        )

        assert result["authorized"] is True


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_get_biscuit_service_singleton(self):
        """Test service is a singleton."""
        service1 = get_biscuit_service()
        service2 = get_biscuit_service()
        assert service1 is service2

    def test_create_biscuit_token(self):
        """Test create_biscuit_token convenience function."""
        with patch('app.services.biscuit_service.get_biscuit_service') as mock_get:
            mock_service = MagicMock()
            mock_service.create_token.return_value = MagicMock(
                token_id="test_token",
                blocks=[],
            )
            mock_get.return_value = mock_service

            token = create_biscuit_token(
                root_key="test_key",
                facts=[],
            )

            assert token is not None
            mock_service.create_token.assert_called_once()

    def test_verify_biscuit_token(self):
        """Test verify_biscuit_token convenience function."""
        with patch('app.services.biscuit_service.get_biscuit_service') as mock_get:
            mock_service = MagicMock()
            mock_service.verify_token.return_value = {"valid": True}
            mock_get.return_value = mock_service

            result = verify_biscuit_token(
                token=MagicMock(),
                public_key="test_key",
            )

            assert result["valid"] is True

    def test_authorize_with_biscuit(self):
        """Test authorize_with_biscuit convenience function."""
        with patch('app.services.biscuit_service.get_biscuit_service') as mock_get:
            mock_service = MagicMock()
            mock_service.authorize.return_value = {"authorized": True}
            mock_get.return_value = mock_service

            result = authorize_with_biscuit(
                token=MagicMock(),
                public_key="test_key",
                query_facts=[],
            )

            assert result["authorized"] is True


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error conditions."""

    def test_invalid_key_format(self, service):
        """Test handling of invalid key format."""
        with pytest.raises((BiscuitError, ValueError)):
            service.create_token(
                root_key="invalid_key_format",
                facts=[],
                ttl_seconds=3600,
            )

    def test_empty_facts(self, service):
        """Test token creation with empty facts."""
        keypair = service.generate_keypair()

        # Should work with empty facts
        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[],
            ttl_seconds=3600,
        )

        assert isinstance(token, BiscuitToken)
        # The service auto-adds expires_at fact, so check user facts are empty
        user_facts = [f for f in token.blocks[0].facts if f.name != "expires_at"]
        assert len(user_facts) == 0

    def test_malformed_token_deserialization(self, service):
        """Test handling of malformed token data."""
        with pytest.raises((BiscuitError, ValueError)):
            service.deserialize_token("not_a_valid_token")


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Performance tests for Biscuit operations."""

    def test_token_creation_performance(self, service):
        """Test token creation is fast (<50ms)."""
        import time

        keypair = service.generate_keypair()
        facts = [BiscuitFact("user_id", ["user_123"])]

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.create_token(
                root_key=keypair["private_key"],
                facts=facts,
                ttl_seconds=3600,
            )
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 50, f"Token creation took {avg_time:.2f}ms, expected <50ms"

    def test_token_verification_performance(self, service):
        """Test token verification is fast (<20ms)."""
        import time

        keypair = service.generate_keypair()
        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[BiscuitFact("user_id", ["user_123"])],
            ttl_seconds=3600,
        )

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.verify_token(token, keypair["public_key"])
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 20, f"Token verification took {avg_time:.2f}ms, expected <20ms"

    def test_authorization_performance(self, service):
        """Test authorization check is fast (<30ms)."""
        import time

        keypair = service.generate_keypair()
        token = service.create_token(
            root_key=keypair["private_key"],
            facts=[
                BiscuitFact("user_id", ["user_123"]),
                BiscuitFact("max_amount", [500]),
            ],
            checks=[BiscuitCheck("amount($a), $a <= 500")],
            ttl_seconds=3600,
        )

        times = []
        for _ in range(10):
            start = time.perf_counter()
            service.authorize(
                token=token,
                public_key=keypair["public_key"],
                query_facts=[BiscuitFact("amount", [300])],
            )
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        assert avg_time < 30, f"Authorization took {avg_time:.2f}ms, expected <30ms"

