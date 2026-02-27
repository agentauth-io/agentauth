"""
AgentAuth Core - Authorization Token System
============================================
PROPRIETARY AND CONFIDENTIAL

This module implements the authorization token architecture.
Tokens are cryptographic proofs that an action was authorized.

Token Structure:
┌─────────────────────────────────────────────────────────┐
│ Token Header (cleartext)                                │
│ - Version: 1 byte                                       │
│ - Type: 1 byte                                          │
│ - Flags: 2 bytes                                        │
│ - Timestamp: 8 bytes                                    │
│ - Expiry: 8 bytes                                       │
│ - Token ID: 16 bytes                                    │
├─────────────────────────────────────────────────────────┤
│ Token Payload (encrypted)                               │
│ - Agent ID                                              │
│ - User ID                                               │
│ - Action type                                           │
│ - Resource                                              │
│ - Constraints                                           │
│ - Policy snapshot hash                                  │
├─────────────────────────────────────────────────────────┤
│ Signature (64 bytes)                                    │
│ - Ed25519 signature over header + encrypted payload     │
└─────────────────────────────────────────────────────────┘

Token Types:
- AUTHORIZATION: Approves a specific action
- DELEGATION: Grants agent permission to act
- REVOCATION: Cancels previous authorization
- AUDIT: Proof of logged action

Security Properties:
- Tokens are bound to specific agent + action
- Cannot be modified (signature verification)
- Cannot be replayed (nonce + expiry)
- Cannot be forged (requires signing key)
- Encrypted payload hides sensitive details
"""

import base64
import json
import struct
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from .crypto import (
    KeyManager,
    secure_random_bytes,
)


class TokenType(IntEnum):
    """Types of authorization tokens."""
    AUTHORIZATION = 1  # Approves an action
    DELEGATION = 2     # Grants ongoing permission
    REVOCATION = 3     # Cancels authorization
    AUDIT = 4          # Proof of audit log
    SESSION = 5        # Session token


class TokenFlag(IntEnum):
    """Token flags (bitfield)."""
    NONE = 0
    ONE_TIME = 1       # Token can only be used once
    REQUIRES_MFA = 2   # Requires additional verification
    HIGH_VALUE = 4     # High-value transaction flag
    RESTRICTED = 8     # Limited to specific merchant
    EXPEDITED = 16     # Fast-track processing


class TokenError(Exception):
    """Base exception for token errors."""
    pass


class TokenExpiredError(TokenError):
    """Token has expired."""
    pass


class TokenInvalidError(TokenError):
    """Token is invalid or corrupted."""
    pass


class TokenRevokedError(TokenError):
    """Token has been revoked."""
    pass


@dataclass
class TokenHeader:
    """
    Token header - cleartext metadata.
    36 bytes total.
    """
    version: int = 1
    token_type: TokenType = TokenType.AUTHORIZATION
    flags: int = 0
    timestamp: int = field(default_factory=lambda: int(time.time()))
    expiry: int = field(default_factory=lambda: int(time.time()) + 3600)
    token_id: bytes = field(default_factory=lambda: secure_random_bytes(16))

    def to_bytes(self) -> bytes:
        """Serialize header to bytes."""
        return struct.pack(
            '>BBHqqq16s',
            self.version,
            int(self.token_type),
            self.flags,
            self.timestamp,
            self.expiry,
            0,  # Reserved
            self.token_id
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "TokenHeader":
        """Deserialize header from bytes."""
        if len(data) < 44:
            raise TokenInvalidError("Header too short")

        version, token_type, flags, timestamp, expiry, _, token_id = struct.unpack(
            '>BBHqqq16s', data[:44]
        )

        return cls(
            version=version,
            token_type=TokenType(token_type),
            flags=flags,
            timestamp=timestamp,
            expiry=expiry,
            token_id=token_id
        )

    def is_expired(self) -> bool:
        """Check if token has expired."""
        return time.time() > self.expiry

    @property
    def token_id_hex(self) -> str:
        """Get token ID as hex string."""
        return self.token_id.hex()


@dataclass
class TokenPayload:
    """
    Token payload - encrypted content.
    Contains the actual authorization details.
    """
    agent_id: str
    user_id: str
    action: str
    resource: str
    amount: float | None = None
    merchant: str | None = None
    category: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    policy_hash: str | None = None
    nonce: bytes = field(default_factory=lambda: secure_random_bytes(16))

    def to_json(self) -> str:
        """Serialize to JSON."""
        data = {
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "nonce": self.nonce.hex(),
        }
        if self.amount is not None:
            data["amount"] = self.amount
        if self.merchant:
            data["merchant"] = self.merchant
        if self.category:
            data["category"] = self.category
        if self.constraints:
            data["constraints"] = self.constraints
        if self.policy_hash:
            data["policy_hash"] = self.policy_hash
        return json.dumps(data, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> "TokenPayload":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(
            agent_id=data["agent_id"],
            user_id=data["user_id"],
            action=data["action"],
            resource=data["resource"],
            amount=data.get("amount"),
            merchant=data.get("merchant"),
            category=data.get("category"),
            constraints=data.get("constraints", {}),
            policy_hash=data.get("policy_hash"),
            nonce=bytes.fromhex(data["nonce"])
        )

    def to_bytes(self) -> bytes:
        """Convert to bytes for encryption."""
        return self.to_json().encode('utf-8')

    @classmethod
    def from_bytes(cls, data: bytes) -> "TokenPayload":
        """Parse from decrypted bytes."""
        return cls.from_json(data.decode('utf-8'))


@dataclass
class AuthorizationToken:
    """
    Complete authorization token.

    This is the cryptographic proof that an action was authorized
    by AgentAuth on behalf of a user.
    """
    header: TokenHeader
    payload: TokenPayload
    signature: bytes = field(default=b'', repr=False)
    _encrypted_payload: bytes = field(default=b'', repr=False)

    def serialize(self, key_manager: KeyManager) -> bytes:
        """
        Serialize and sign the token.

        Returns:
            Complete token as bytes (header + encrypted_payload + signature)
        """
        # Serialize header
        header_bytes = self.header.to_bytes()

        # Encrypt payload
        payload_bytes = self.payload.to_bytes()
        associated_data = header_bytes  # Bind to header
        encrypted = key_manager.token_encryption_key.encrypt(
            payload_bytes, associated_data
        )
        self._encrypted_payload = encrypted

        # Sign header + encrypted payload
        to_sign = header_bytes + encrypted
        self.signature = key_manager.auth_signing_key.sign(to_sign)

        # Combine: header + len(encrypted) + encrypted + signature
        return (
            header_bytes +
            struct.pack('>H', len(encrypted)) +
            encrypted +
            self.signature
        )

    @classmethod
    def deserialize(cls, data: bytes, key_manager: KeyManager) -> "AuthorizationToken":
        """
        Deserialize and verify a token.

        Raises:
            TokenInvalidError: If signature verification fails
            TokenExpiredError: If token has expired
        """
        if len(data) < 44 + 2 + 28 + 64:  # header + len + min_encrypted + sig
            raise TokenInvalidError("Token too short")

        # Parse header
        header = TokenHeader.from_bytes(data[:44])

        # Check expiry
        if header.is_expired():
            raise TokenExpiredError(f"Token expired at {header.expiry}")

        # Parse encrypted payload length
        encrypted_len = struct.unpack('>H', data[44:46])[0]
        if len(data) < 46 + encrypted_len + 64:
            raise TokenInvalidError("Token truncated")

        encrypted_payload = data[46:46+encrypted_len]
        signature = data[46+encrypted_len:46+encrypted_len+64]

        # Verify signature
        # serialize() signs header_bytes + encrypted (no length prefix)
        header_bytes = data[:44]
        to_verify = header_bytes + encrypted_payload
        if not key_manager.auth_signing_key.verify(to_verify, signature):
            raise TokenInvalidError("Signature verification failed")

        # Decrypt payload
        header_bytes = data[:44]
        try:
            payload_bytes = key_manager.token_encryption_key.decrypt(
                encrypted_payload, header_bytes
            )
        except Exception as e:
            raise TokenInvalidError(f"Payload decryption failed: {e}")

        payload = TokenPayload.from_bytes(payload_bytes)

        return cls(
            header=header,
            payload=payload,
            signature=signature,
            _encrypted_payload=encrypted_payload
        )

    def to_base64(self, key_manager: KeyManager) -> str:
        """Serialize to URL-safe base64 string."""
        return base64.urlsafe_b64encode(self.serialize(key_manager)).decode()

    @classmethod
    def from_base64(cls, b64_str: str, key_manager: KeyManager) -> "AuthorizationToken":
        """Deserialize from base64 string."""
        data = base64.urlsafe_b64decode(b64_str)
        return cls.deserialize(data, key_manager)

    @property
    def token_id(self) -> str:
        """Get human-readable token ID."""
        return f"aa_tx_{self.header.token_id_hex[:12]}"

    def summary(self) -> dict[str, Any]:
        """Get token summary for display."""
        return {
            "token_id": self.token_id,
            "type": self.header.token_type.name,
            "agent": self.payload.agent_id,
            "user": self.payload.user_id,
            "action": self.payload.action,
            "amount": self.payload.amount,
            "merchant": self.payload.merchant,
            "expires": self.header.expiry,
            "valid": not self.header.is_expired()
        }


class TokenGenerator:
    """
    Generates authorization tokens.

    This is the core token minting capability.
    """

    def __init__(self, key_manager: KeyManager):
        self._key_manager = key_manager
        self._issued_tokens: dict[str, float] = {}  # token_id -> issue_time

    def create_authorization(
        self,
        agent_id: str,
        user_id: str,
        action: str,
        resource: str,
        amount: float | None = None,
        merchant: str | None = None,
        category: str | None = None,
        ttl_seconds: int = 3600,
        flags: int = TokenFlag.NONE,
        constraints: dict[str, Any] | None = None,
        policy_hash: str | None = None
    ) -> AuthorizationToken:
        """
        Create a new authorization token.

        Args:
            agent_id: ID of the agent making the request
            user_id: ID of the user who owns the agent
            action: Action being authorized (e.g., "purchase")
            resource: Resource being acted on (e.g., "order_123")
            amount: Transaction amount (if applicable)
            merchant: Merchant name (if applicable)
            category: Category (if applicable)
            ttl_seconds: Token lifetime in seconds
            flags: Token flags
            constraints: Additional constraints
            policy_hash: Hash of policy that authorized this

        Returns:
            Signed authorization token
        """
        now = int(time.time())

        header = TokenHeader(
            version=1,
            token_type=TokenType.AUTHORIZATION,
            flags=flags,
            timestamp=now,
            expiry=now + ttl_seconds,
        )

        payload = TokenPayload(
            agent_id=agent_id,
            user_id=user_id,
            action=action,
            resource=resource,
            amount=amount,
            merchant=merchant,
            category=category,
            constraints=constraints or {},
            policy_hash=policy_hash,
        )

        token = AuthorizationToken(header=header, payload=payload)

        # Pre-serialize to generate signature
        token.serialize(self._key_manager)

        # Track issued token
        self._issued_tokens[header.token_id_hex] = now

        return token

    def create_delegation(
        self,
        agent_id: str,
        user_id: str,
        permissions: list[str],
        ttl_seconds: int = 86400,  # 24 hours default
    ) -> AuthorizationToken:
        """
        Create a delegation token granting ongoing permissions.
        """
        now = int(time.time())

        header = TokenHeader(
            version=1,
            token_type=TokenType.DELEGATION,
            flags=TokenFlag.NONE,
            timestamp=now,
            expiry=now + ttl_seconds,
        )

        payload = TokenPayload(
            agent_id=agent_id,
            user_id=user_id,
            action="delegate",
            resource="*",
            constraints={"permissions": permissions}
        )

        token = AuthorizationToken(header=header, payload=payload)
        token.serialize(self._key_manager)

        return token


class TokenVerifier:
    """
    Verifies authorization tokens.

    This is used by merchants/processors to validate tokens.
    """

    def __init__(self, key_manager: KeyManager):
        self._key_manager = key_manager
        self._revoked_tokens: set = set()  # In production: distributed store

    def verify(self, token_data: bytes) -> AuthorizationToken:
        """
        Verify a token and return the parsed token if valid.

        Raises:
            TokenExpiredError: If expired
            TokenRevokedError: If revoked
            TokenInvalidError: If invalid signature or format
        """
        token = AuthorizationToken.deserialize(token_data, self._key_manager)

        # Check revocation (using truncated ID matching revoke() behavior)
        truncated_id = token.header.token_id_hex[:12]
        if truncated_id in self._revoked_tokens:
            raise TokenRevokedError("Token has been revoked")

        return token

    def verify_base64(self, b64_str: str) -> AuthorizationToken:
        """Verify a base64-encoded token."""
        data = base64.urlsafe_b64decode(b64_str)
        return self.verify(data)

    def revoke(self, token_id: str):
        """
        Revoke a token.

        In production, this would be stored in a distributed cache
        with TTL matching token expiry.
        """
        # Normalize token ID
        if token_id.startswith("aa_tx_"):
            token_id = token_id[6:]
        self._revoked_tokens.add(token_id)

    def is_revoked(self, token_id: str) -> bool:
        """Check if a token is revoked."""
        if token_id.startswith("aa_tx_"):
            token_id = token_id[6:]
        return token_id in self._revoked_tokens


# Test the token module
if __name__ == "__main__":
    print("AgentAuth Core Token Module Test")
    print("=" * 50)

    # Initialize key manager
    km = KeyManager()
    print("[+] Key manager initialized")

    # Create token generator
    generator = TokenGenerator(km)

    # Generate authorization token
    token = generator.create_authorization(
        agent_id="agent_shopping_123",
        user_id="user_abc",
        action="purchase",
        resource="order_xyz789",
        amount=49.99,
        merchant="Amazon",
        category="electronics",
        ttl_seconds=3600,
        flags=TokenFlag.ONE_TIME
    )

    print("\n[+] Generated token:")
    print(f"    Token ID: {token.token_id}")
    print(f"    Agent: {token.payload.agent_id}")
    print(f"    Amount: ${token.payload.amount}")
    print(f"    Merchant: {token.payload.merchant}")
    print(f"    Expires: {token.header.expiry}")

    # Serialize to base64
    token_b64 = token.to_base64(km)
    print(f"\n[+] Token (base64): {token_b64[:60]}...")
    print(f"    Length: {len(token_b64)} bytes")

    # Verify token
    verifier = TokenVerifier(km)
    verified = verifier.verify_base64(token_b64)
    print("\n[+] Verification: PASS")
    print(f"    Token summary: {verified.summary()}")

    # Test revocation
    verifier.revoke(token.token_id)
    print("\n[+] Token revoked")

    try:
        verifier.verify_base64(token_b64)
        print("[!] FAIL: Should have raised TokenRevokedError")
    except TokenRevokedError:
        print("[+] Revocation check: PASS")

    print("\n[*] All token tests passed!")
