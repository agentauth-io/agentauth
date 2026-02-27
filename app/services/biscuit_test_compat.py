"""
Test Compatibility Module for Biscuit Service

This module provides test-compatible classes and functions that wrap
the main BiscuitService implementation.
"""

import base64
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from app.services.biscuit_service import (
    Biscuit,
    BiscuitCheck,
    BiscuitFact,
    get_biscuit_service,
)
from app.services.biscuit_service import (
    BiscuitService as BaseBiscuitService,
)


class BiscuitToken:
    """Wrapper class for Biscuit token to match test expectations."""

    def __init__(self, biscuit: Biscuit, root_key_id: str = "default"):
        self.biscuit = biscuit
        self.root_key_id = root_key_id
        self.blocks = [biscuit.authority] + biscuit.blocks
        self.token_id = biscuit.token_id
        self.created_at = biscuit.created_at
        self.expires_at = None

        # Extract expiration from authority facts
        for fact in biscuit.authority.facts:
            if fact.name == "expires_at" and fact.terms:
                try:
                    self.expires_at = datetime.fromisoformat(fact.terms[0])
                except (ValueError, TypeError):
                    pass

    def serialize(self) -> str:
        """Serialize token to string."""
        return f"{self.root_key_id}:{self.biscuit.serialize()}"

    @classmethod
    def deserialize(
        cls, token_str: str, root_key_id: str = "default"
    ) -> "BiscuitToken":
        """Deserialize token from string."""
        if ":" in token_str:
            parts = token_str.split(":", 1)
            stored_key_id = parts[0]
            biscuit_data = parts[1]
            biscuit = Biscuit.deserialize(biscuit_data)
            return cls(biscuit, root_key_id=stored_key_id)
        else:
            biscuit = Biscuit.deserialize(token_str)
            return cls(biscuit, root_key_id=root_key_id)


# Extend BiscuitService with test-compatible methods
def _generate_keypair(self) -> dict:
    """Generate a new Ed25519 keypair."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    private_b64 = base64.b64encode(private_bytes).decode()
    public_b64 = base64.b64encode(public_bytes).decode()
    key_id = hashlib.sha256(public_bytes).hexdigest()[:16]

    return {"private_key": private_b64, "public_key": public_b64, "key_id": key_id}


BaseBiscuitService.generate_keypair = _generate_keypair


# Token revocation storage
BaseBiscuitService._revoked_tokens = set()


def _revoke_token(self, token_or_id) -> None:
    """Revoke a token."""
    if isinstance(token_or_id, str):
        self._revoked_tokens.add(token_or_id)
    else:
        self._revoked_tokens.add(token_or_id.token_id)


def _is_token_revoked(self, token_or_id) -> bool:
    """Check if a token is revoked."""
    if isinstance(token_or_id, str):
        return token_or_id in self._revoked_tokens
    return token_or_id.token_id in self._revoked_tokens


BaseBiscuitService.revoke_token = _revoke_token
BaseBiscuitService.is_token_revoked = _is_token_revoked


# Convenience functions for test compatibility
def create_biscuit_token(
    root_key: str,
    facts: list[BiscuitFact],
    checks: list[BiscuitCheck] | None = None,
    ttl_seconds: int = 3600,
) -> BiscuitToken:
    """Create a Biscuit token."""
    service = get_biscuit_service()
    return service.create_token(root_key, facts, checks, ttl_seconds)


def verify_biscuit_token(
    token: BiscuitToken,
    public_key: str,
) -> dict:
    """Verify a Biscuit token."""
    service = get_biscuit_service()
    return service.verify_token(token, public_key)


def authorize_with_biscuit(
    token: BiscuitToken,
    public_key: str,
    query_facts: list[BiscuitFact],
) -> dict:
    """Authorize with Biscuit token."""
    service = get_biscuit_service()
    return service.authorize(token, public_key, query_facts)
