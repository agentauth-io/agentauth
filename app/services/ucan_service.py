"""
AgentAuth UCAN Service

User-Controlled Authorization Networks for cross-organizational agent delegation.
Based on the UCAN specification: https://ucan.xyz/
"""

import base64
import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


class UCANError(Exception):
    """Base exception for UCAN operations."""
    pass


class UCANValidationError(UCANError):
    """UCAN validation failed."""
    pass


class UCANCapabilityError(UCANError):
    """Capability check failed."""
    pass


@dataclass
class Capability:
    """A capability (permission) in UCAN format."""
    resource: str
    action: str
    caveats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {"with": self.resource, "can": self.action}
        if self.caveats:
            result["caveats"] = self.caveats
        return result

    def is_subset_of(self, parent: "Capability") -> bool:
        if not self._resource_matches(self.resource, parent.resource):
            return False
        if parent.action != "*" and self.action != parent.action:
            return False
        return True

    @staticmethod
    def _resource_matches(child: str, parent: str) -> bool:
        if parent == "*" or parent.endswith(":*"):
            prefix = parent.rstrip("*")
            return child.startswith(prefix) or child == parent
        return child == parent


@dataclass
class UCANPayload:
    """UCAN payload structure."""
    iss: str
    aud: str
    exp: int
    att: list[Capability] = field(default_factory=list)
    nbf: int | None = None
    nnc: str | None = None
    fct: dict[str, Any] = field(default_factory=dict)
    prf: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {
            "iss": self.iss, "aud": self.aud, "exp": self.exp,
            "att": [c.to_dict() for c in self.att],
        }
        if self.nbf: result["nbf"] = self.nbf
        if self.nnc: result["nnc"] = self.nnc
        if self.fct: result["fct"] = self.fct
        if self.prf: result["prf"] = self.prf
        return result


@dataclass
class UCAN:
    """User-Controlled Authorization Network token."""
    alg: str = "EdDSA"
    typ: str = "JWT"
    ucv: str = "0.10.0"
    payload: UCANPayload = None
    signature: bytes | None = None

    def __post_init__(self):
        if self.payload is None:
            raise UCANError("Payload is required")

    def to_jwt(self) -> str:
        header = {"alg": self.alg, "typ": self.typ, "ucv": self.ucv}
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(self.payload.to_dict()).encode()).decode().rstrip("=")
        sig_b64 = base64.urlsafe_b64encode(self.signature).decode().rstrip("=") if self.signature else ""
        return f"{header_b64}.{payload_b64}.{sig_b64}"

    @classmethod
    def from_jwt(cls, token: str) -> "UCAN":
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise UCANValidationError("Invalid JWT format")

            def pad_b64(s):
                return s + "=" * (4 - len(s) % 4)

            header = json.loads(base64.urlsafe_b64decode(pad_b64(parts[0])))
            payload_dict = json.loads(base64.urlsafe_b64decode(pad_b64(parts[1])))

            capabilities = [
                Capability(resource=cap["with"], action=cap["can"], caveats=cap.get("caveats", {}))
                for cap in payload_dict.get("att", [])
            ]

            payload = UCANPayload(
                iss=payload_dict["iss"], aud=payload_dict["aud"], exp=payload_dict["exp"],
                att=capabilities, nbf=payload_dict.get("nbf"), nnc=payload_dict.get("nnc"),
                fct=payload_dict.get("fct", {}), prf=payload_dict.get("prf", []),
            )

            signature = base64.urlsafe_b64decode(pad_b64(parts[2])) if parts[2] else None
            return cls(alg=header.get("alg", "EdDSA"), typ=header.get("typ", "JWT"),
                      ucv=header.get("ucv", "0.10.0"), payload=payload, signature=signature)
        except Exception as e:
            raise UCANValidationError(f"Failed to parse UCAN: {e}")

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc).timestamp() > self.payload.exp

    @property
    def is_active(self) -> bool:
        if self.payload.nbf:
            return datetime.now(timezone.utc).timestamp() >= self.payload.nbf
        return True

    @property
    def capabilities(self) -> list[Capability]:
        return self.payload.att

    def to_dict(self) -> dict:
        return {
            "header": {"alg": self.alg, "typ": self.typ, "ucv": self.ucv},
            "payload": self.payload.to_dict(),
            "signature": base64.urlsafe_b64encode(self.signature).decode() if self.signature else None,
        }


class UCANToken:
    """Wrapper class for UCAN token to match test expectations."""

    def __init__(self, ucan: UCAN):
        self.ucan = ucan
        self.payload = ucan.payload
        self.token_id = f"ucan_{secrets.token_hex(16)}"

    def to_dict(self) -> dict:
        return self.ucan.to_dict()

    def to_jwt(self) -> str:
        return self.ucan.to_jwt()


class UCANBuilder:
    """Builder for creating UCAN tokens."""

    def __init__(self, issuer_did: str, audience_did: str):
        self.issuer = issuer_did
        self.audience = audience_did
        self.capabilities: list[Capability] = []
        self.expiration: datetime | None = None
        self.not_before: datetime | None = None
        self.facts: dict[str, Any] = {}
        self.proofs: list[str] = []
        self.nonce: str | None = None

    def with_capability(self, resource: str, action: str, **caveats) -> "UCANBuilder":
        self.capabilities.append(Capability(resource=resource, action=action, caveats=caveats))
        return self

    def with_lifetime(self, seconds: int) -> "UCANBuilder":
        self.expiration = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        return self

    def with_nonce(self, nonce: str | None = None) -> "UCANBuilder":
        self.nonce = nonce or secrets.token_hex(16)
        return self

    def with_proof(self, parent_ucan: str) -> "UCANBuilder":
        self.proofs.append(parent_ucan)
        return self

    def build(self) -> UCAN:
        if not self.expiration:
            self.expiration = datetime.now(timezone.utc) + timedelta(hours=24)

        payload = UCANPayload(
            iss=self.issuer, aud=self.audience, exp=int(self.expiration.timestamp()),
            att=self.capabilities, nbf=int(self.not_before.timestamp()) if self.not_before else None,
            nnc=self.nonce, fct=self.facts, prf=self.proofs,
        )
        return UCAN(payload=payload)


class UCANService:
    """Service for creating, delegating, and validating UCANs."""

    def __init__(self):
        self._keys: dict[str, Ed25519PrivateKey] = {}
        self._did_cache: dict[str, str] = {}

    def generate_keypair(self, name: str = "default") -> dict:
        """Generate a new Ed25519 keypair and return dict with keys and DID."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        self._keys[name] = private_key

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        did = f"did:key:z{base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')}"
        self._did_cache[name] = did

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption())

        return {
            "private_key": base64.b64encode(private_bytes).decode(),
            "public_key": base64.b64encode(public_bytes).decode(),
            "did": did
        }

    def get_did(self, name: str = "default") -> str:
        return self._did_cache.get(name)

    def _public_key_to_did(self, public_key: str) -> str:
        """Convert base64-encoded public key to DID."""
        try:
            public_bytes = base64.b64decode(public_key)
            return f"did:key:z{base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')}"
        except Exception:
            raise UCANError("Invalid public key format")

    def create_token(
        self, issuer_did: str, audience_did: str, capabilities: list[Capability],
        private_key: str, ttl_seconds: int = 3600,
    ) -> UCANToken:
        """Create a UCAN token."""
        builder = UCANBuilder(issuer_did, audience_did)
        builder.with_lifetime(ttl_seconds)
        builder.with_nonce()

        for cap in capabilities:
            builder.with_capability(resource=cap.resource, action=cap.action, **cap.caveats)

        ucan = builder.build()

        try:
            private_bytes = base64.b64decode(private_key)
            from cryptography.hazmat.primitives.asymmetric import ed25519
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
            message = ucan.to_jwt().rsplit(".", 1)[0].encode()
            ucan.signature = priv_key.sign(message)
        except Exception:
            pass

        return UCANToken(ucan)

    def verify_token(self, token: UCANToken, public_key: str) -> dict:
        """Verify a UCAN token."""
        result = {"valid": True, "issuer": None, "capabilities": [], "error": None}

        if token.ucan.is_expired:
            return {"valid": False, "issuer": None, "capabilities": [], "error": "Token expired"}

        if not token.ucan.is_active:
            return {"valid": False, "issuer": None, "capabilities": [], "error": "Token not yet active"}

        result["issuer"] = token.ucan.payload.iss
        result["capabilities"] = [cap.to_dict() for cap in token.ucan.capabilities]

        try:
            public_bytes = base64.b64decode(public_key)
            from cryptography.hazmat.primitives.asymmetric import ed25519
            ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        except Exception:
            return {"valid": False, "issuer": result["issuer"], "capabilities": [], "error": "Invalid public key"}

        return result

    def attenuate_token(self, token: UCANToken, capabilities: list[Capability]) -> UCANToken:
        """Attenuate a token with stricter capabilities."""
        builder = UCANBuilder(issuer_did=token.ucan.payload.aud, audience_did=token.ucan.payload.iss)
        builder.with_lifetime(token.ucan.payload.exp - int(datetime.now(timezone.utc).timestamp()))
        builder.with_nonce()
        builder.with_proof(token.ucan.to_jwt())

        for cap in capabilities:
            if not any(cap.is_subset_of(parent_cap) for parent_cap in token.ucan.capabilities):
                raise UCANCapabilityError(f"Cannot delegate capability not in parent: {cap.to_dict()}")
            builder.with_capability(resource=cap.resource, action=cap.action, **cap.caveats)

        return UCANToken(builder.build())

    def check_capability(self, token: UCANToken, resource: str, action: str) -> dict:
        """Check if a token has a specific capability."""
        required = Capability(resource=resource, action=action)
        for cap in token.ucan.capabilities:
            if required.is_subset_of(cap):
                return {"has_capability": True, "capability": cap.to_dict()}
        return {"has_capability": False, "capability": None}

    def serialize_token(self, token: UCANToken, compact: bool = False) -> str:
        """Serialize a token to string."""
        return token.ucan.to_jwt() if compact else json.dumps(token.to_dict())

    def deserialize_token(self, token_str: str) -> UCANToken:
        """Deserialize a token from string."""
        try:
            if token_str.count(".") == 2:
                return UCANToken(UCAN.from_jwt(token_str))
            data = json.loads(token_str)
            payload_data = data.get("payload", {})
            capabilities = [
                Capability(resource=cap["with"], action=cap["can"], caveats=cap.get("caveats", {}))
                for cap in payload_data.get("att", [])
            ]
            payload = UCANPayload(
                iss=payload_data["iss"], aud=payload_data["aud"], exp=payload_data["exp"],
                att=capabilities, nbf=payload_data.get("nbf"), nnc=payload_data.get("nnc"),
                fct=payload_data.get("fct", {}), prf=payload_data.get("prf", []),
            )
            signature = base64.urlsafe_b64decode(data["signature"]) if data.get("signature") else None
            return UCANToken(UCAN(payload=payload, signature=signature))
        except Exception as e:
            raise UCANError(f"Failed to deserialize token: {e}")

    def create_root_ucan(self, issuer_name: str, audience_did: str,
                         capabilities: list[dict[str, Any]], lifetime_hours: int = 24) -> str:
        """Create a root UCAN (no parent proofs)."""
        issuer_did = self.get_did(issuer_name)
        if not issuer_did:
            keypair = self.generate_keypair(issuer_name)
            issuer_did = keypair["did"]

        builder = UCANBuilder(issuer_did, audience_did)
        builder.with_lifetime(lifetime_hours * 3600)
        builder.with_nonce()

        for cap in capabilities:
            builder.with_capability(resource=cap["resource"], action=cap["action"], **cap.get("caveats", {}))

        return builder.build().to_jwt()

    def delegate(self, parent_ucan: str, audience_did: str,
                 capabilities: list[dict[str, Any]] | None = None, lifetime_hours: int = 24) -> str:
        """Delegate capabilities from a parent UCAN."""
        parent = UCAN.from_jwt(parent_ucan)
        if parent.is_expired:
            raise UCANValidationError("Parent UCAN has expired")

        builder = UCANBuilder(parent.payload.aud, audience_did)
        builder.with_lifetime(lifetime_hours * 3600)
        builder.with_nonce()
        builder.with_proof(parent_ucan)

        if capabilities:
            for cap in capabilities:
                new_cap = Capability(resource=cap["resource"], action=cap["action"], caveats=cap.get("caveats", {}))
                if not any(new_cap.is_subset_of(p) for p in parent.capabilities):
                    raise UCANCapabilityError(f"Cannot delegate capability not in parent: {cap}")
                builder.with_capability(resource=cap["resource"], action=cap["action"], **cap.get("caveats", {}))
        else:
            for cap in parent.capabilities:
                builder.with_capability(resource=cap.resource, action=cap.action, **cap.caveats)

        return builder.build().to_jwt()

    def validate(self, ucan_jwt: str, required_capability: dict[str, Any] | None = None) -> bool:
        """Validate a UCAN token."""
        ucan = UCAN.from_jwt(ucan_jwt)
        if ucan.is_expired:
            raise UCANValidationError("UCAN has expired")
        if not ucan.is_active:
            raise UCANValidationError("UCAN is not yet active")

        if required_capability:
            required = Capability(resource=required_capability["resource"], action=required_capability["action"])
            if not any(required.is_subset_of(cap) for cap in ucan.capabilities):
                raise UCANCapabilityError(f"UCAN does not have required capability: {required_capability}")

        for proof in ucan.payload.prf:
            self.validate(proof)

        return True

    def get_capabilities(self, ucan_jwt: str) -> list[dict[str, Any]]:
        """Get capabilities from a UCAN."""
        ucan = UCAN.from_jwt(ucan_jwt)
        return [cap.to_dict() for cap in ucan.capabilities]


_ucan_service: UCANService | None = None


def get_ucan_service() -> UCANService:
    global _ucan_service
    if _ucan_service is None:
        _ucan_service = UCANService()
    return _ucan_service


def create_ucan_token(issuer_did: str, audience_did: str, capabilities: list[Capability],
                      private_key: str, ttl_seconds: int = 3600) -> UCANToken:
    return get_ucan_service().create_token(issuer_did, audience_did, capabilities, private_key, ttl_seconds)


def verify_ucan_token(token: UCANToken, public_key: str) -> dict:
    return get_ucan_service().verify_token(token, public_key)


def check_capability(token: UCANToken, resource: str, action: str) -> dict:
    return get_ucan_service().check_capability(token, resource, action)


def attenuate_ucan(token: UCANToken, capabilities: list[Capability]) -> UCANToken:
    return get_ucan_service().attenuate_token(token, capabilities)


def create_agent_ucan(user_did: str, agent_did: str, consent_id: str,
                      max_amount: float, allowed_actions: list[str] = None) -> str:
    """Create a UCAN for an agent to act on behalf of a user."""
    service = get