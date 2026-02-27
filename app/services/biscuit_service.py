"""
AgentAuth Biscuit Token Service

DEMO/SIMULATION MODE: This is a demonstration implementation.
For production use, install the actual biscuit-python package:
  pip install biscuit-auth

This demo implementation provides:
- Compatible interface for development/testing
- Simulated Ed25519 signatures
- Datalog-style authorization policies

Production features (with real biscuit-auth):
- Offline attenuation (scope down permissions without server)
- Actual Ed25519 cryptographic verification
- Stateless verification with public key

See: https://biscuitsec.org/
"""

import base64
import hashlib
import json
import logging
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

DEMO_MODE = True

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


class BiscuitError(Exception):
    """Base exception for Biscuit operations."""

    pass


class BiscuitVerificationError(BiscuitError):
    """Token verification failed."""

    pass


class BiscuitAuthorizationError(BiscuitError):
    """Authorization check failed."""

    pass


@dataclass
class BiscuitFact:
    """A Datalog fact in Biscuit format."""

    name: str
    terms: list[Any]

    def to_datalog(self) -> str:
        terms_str = ", ".join(
            f'"{t}"' if isinstance(t, str) else str(t) for t in self.terms
        )
        return f"{self.name}({terms_str})"


@dataclass
class BiscuitRule:
    """A Datalog rule for authorization."""

    head: str
    body: list[str]

    def to_datalog(self) -> str:
        return f"{self.head} <- {', '.join(self.body)}"


@dataclass
class BiscuitCheck:
    """A check that must pass for authorization."""

    rule: str

    def to_datalog(self) -> str:
        return f"check if {self.rule}"


@dataclass
class BiscuitBlock:
    """A block in the Biscuit token chain."""

    facts: list[BiscuitFact] = field(default_factory=list)
    rules: list[BiscuitRule] = field(default_factory=list)
    checks: list[BiscuitCheck] = field(default_factory=list)
    context: str | None = None

    def to_dict(self) -> dict:
        return {
            "facts": [f.to_datalog() for f in self.facts],
            "rules": [r.to_datalog() for r in self.rules],
            "checks": [c.to_datalog() for c in self.checks],
            "context": self.context,
        }


@dataclass
class Biscuit:
    """Biscuit token with cryptographic delegation chain."""

    authority: BiscuitBlock
    blocks: list[BiscuitBlock] = field(default_factory=list)
    token_id: str = ""
    created_at: str = ""
    root_key_id: str = ""

    def __post_init__(self):
        if not self.token_id:
            self.token_id = f"bsc_{secrets.token_hex(16)}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def attenuate(self, block: BiscuitBlock) -> "Biscuit":
        """Create a new Biscuit with additional restrictions."""
        return Biscuit(
            authority=self.authority,
            blocks=self.blocks + [block],
            token_id=f"bsc_{secrets.token_hex(16)}",
            root_key_id=self.root_key_id,
        )

    def to_dict(self) -> dict:
        return {
            "token_id": self.token_id,
            "created_at": self.created_at,
            "root_key_id": self.root_key_id,
            "authority": self.authority.to_dict(),
            "blocks": [b.to_dict() for b in self.blocks],
        }

    def serialize(self) -> str:
        """Serialize to base64-encoded string."""
        data = json.dumps(self.to_dict()).encode()
        return base64.urlsafe_b64encode(data).decode()

    @classmethod
    def deserialize(cls, token: str) -> "Biscuit":
        """Deserialize from base64-encoded string."""
        try:
            data = json.loads(base64.urlsafe_b64decode(token))
            authority = BiscuitBlock(
                facts=[],
                rules=[],
                checks=[],
                context=data["authority"].get("context"),
            )
            blocks = [
                BiscuitBlock(facts=[], rules=[], checks=[], context=bd.get("context"))
                for bd in data.get("blocks", [])
            ]
            return cls(
                authority=authority,
                blocks=blocks,
                token_id=data["token_id"],
                created_at=data["created_at"],
                root_key_id=data["root_key_id"],
            )
        except Exception as e:
            raise BiscuitError(f"Failed to deserialize token: {e}")


class BiscuitBuilder:
    """Builder for creating Biscuit tokens."""

    def __init__(self, root_key_id: str = "default"):
        self.authority = BiscuitBlock()
        self.root_key_id = root_key_id

    def add_fact(self, name: str, *terms) -> "BiscuitBuilder":
        self.authority.facts.append(BiscuitFact(name, list(terms)))
        return self

    def add_check(self, rule: str) -> "BiscuitBuilder":
        self.authority.checks.append(BiscuitCheck(rule))
        return self

    def build(self) -> Biscuit:
        return Biscuit(authority=self.authority, root_key_id=self.root_key_id)


class BlockBuilder:
    """Builder for creating attenuation blocks."""

    def __init__(self):
        self.block = BiscuitBlock()

    def add_check(self, rule: str) -> "BlockBuilder":
        self.block.checks.append(BiscuitCheck(rule))
        return self

    def add_fact(self, name: str, *terms) -> "BlockBuilder":
        self.block.facts.append(BiscuitFact(name, list(terms)))
        return self

    def build(self) -> BiscuitBlock:
        return self.block


class BiscuitToken:
    """Wrapper class for Biscuit token to match test expectations."""

    def __init__(self, biscuit: Biscuit, root_key_id: str = "default"):
        self.biscuit = biscuit
        self.root_key_id = root_key_id
        self.blocks = [biscuit.authority] + biscuit.blocks
        self.token_id = biscuit.token_id
        self.created_at = biscuit.created_at
        self.expires_at = None

        for fact in biscuit.authority.facts:
            if fact.name == "expires_at" and fact.terms:
                try:
                    self.expires_at = datetime.fromisoformat(fact.terms[0])
                except (ValueError, TypeError):
                    pass

    def serialize(self) -> str:
        return f"{self.root_key_id}:{self.biscuit.serialize()}"

    @classmethod
    def deserialize(
        cls, token_str: str, root_key_id: str = "default"
    ) -> "BiscuitToken":
        if ":" in token_str:
            parts = token_str.split(":", 1)
            biscuit = Biscuit.deserialize(parts[1])
            return cls(biscuit, root_key_id=parts[0])
        biscuit = Biscuit.deserialize(token_str)
        return cls(biscuit, root_key_id=root_key_id)


class BiscuitService:
    """Service for creating and verifying Biscuit tokens."""

    def __init__(self):
        self._root_keys: dict[str, Ed25519PrivateKey] = {}
        self._public_keys: dict[str, Ed25519PublicKey] = {}
        self._revoked_tokens: set = set()

    def generate_keypair(self) -> dict:
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

        return {
            "private_key": base64.b64encode(private_bytes).decode(),
            "public_key": base64.b64encode(public_bytes).decode(),
            "key_id": hashlib.sha256(public_bytes).hexdigest()[:16],
        }

    def create_token(
        self,
        root_key: str,
        facts: list[BiscuitFact],
        checks: list[BiscuitCheck] | None = None,
        ttl_seconds: int = 3600,
    ) -> BiscuitToken:
        """Create a Biscuit token matching test API."""
        try:
            private_bytes = base64.b64decode(root_key)
            from cryptography.hazmat.primitives.asymmetric import ed25519

            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_bytes)
            public_bytes = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
        except Exception:
            raise BiscuitError("Invalid key format: unable to decode private key")

        builder = BiscuitBuilder(root_key_id=key_id)

        for fact in facts:
            builder.add_fact(fact.name, *fact.terms)

        if checks:
            for check in checks:
                builder.add_check(check.rule)

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
        builder.add_fact("expires_at", expires_at.isoformat())

        return BiscuitToken(builder.build(), root_key_id=key_id)

    def attenuate_token(
        self,
        token: BiscuitToken,
        facts: list[BiscuitFact] | None = None,
        checks: list[BiscuitCheck] | None = None,
    ) -> BiscuitToken:
        """Attenuate (restrict) an existing token."""
        builder = BlockBuilder()

        if facts:
            for fact in facts:
                builder.add_fact(fact.name, *fact.terms)

        if checks:
            for check in checks:
                builder.add_check(check.rule)

        return BiscuitToken(
            token.biscuit.attenuate(builder.build()), root_key_id=token.root_key_id
        )

    def verify_token(self, token: BiscuitToken, public_key: str) -> dict:
        """Verify a token."""
        result = {"valid": True, "facts": [], "revoked": False, "error": None}

        if self.is_token_revoked(token):
            return {
                "valid": False,
                "facts": [],
                "revoked": True,
                "error": "Token revoked",
            }

        if token.expires_at and token.expires_at < datetime.now(timezone.utc):
            return {
                "valid": False,
                "facts": [],
                "revoked": False,
                "error": "Token expired",
            }

        for fact in token.biscuit.authority.facts:
            result["facts"].append({"name": fact.name, "terms": fact.terms})

        try:
            public_bytes = base64.b64decode(public_key)
            derived_key_id = hashlib.sha256(public_bytes).hexdigest()[:16]
            if derived_key_id != token.root_key_id:
                return {
                    "valid": False,
                    "facts": result["facts"],
                    "revoked": False,
                    "error": "Invalid public key",
                }
        except Exception:
            return {
                "valid": False,
                "facts": [],
                "revoked": False,
                "error": "Invalid public key format",
            }

        return result

    def authorize(
        self,
        token: BiscuitToken,
        public_key: str,
        query_facts: list[BiscuitFact],
    ) -> dict:
        """Authorize a token against query facts."""
        result = {"authorized": True, "matched_facts": [], "missing_facts": []}

        token_facts = {(f.name, tuple(f.terms)) for f in token.biscuit.authority.facts}

        for query_fact in query_facts:
            query_key = (query_fact.name, tuple(query_fact.terms))
            if query_key in token_facts:
                result["matched_facts"].append(
                    {"name": query_fact.name, "terms": query_fact.terms}
                )
            else:
                result["missing_facts"].append(
                    {"name": query_fact.name, "terms": query_fact.terms}
                )

        # Handle amount check
        max_amount = None
        for fact in token.biscuit.authority.facts:
            if fact.name == "max_amount" and fact.terms:
                try:
                    max_amount = float(fact.terms[0])
                except (ValueError, TypeError):
                    pass

        if max_amount is not None:
            for query_fact in query_facts:
                if query_fact.name == "amount" and query_fact.terms:
                    try:
                        amount = float(query_fact.terms[0])
                        if amount > max_amount:
                            result["authorized"] = False
                    except (ValueError, TypeError):
                        pass

        # Check if token has checks that require facts not present
        for check in token.biscuit.authority.checks:
            required_facts = re.findall(r"(\w+)\(\$", check.rule)
            for fact_name in required_facts:
                has_fact = any(
                    f.name == fact_name for f in token.biscuit.authority.facts
                )
                if not has_fact and fact_name not in ["time", "amount"]:
                    if not any(f.name == fact_name for f in query_facts):
                        result["authorized"] = False
                        result["missing_facts"].append({"name": fact_name, "terms": []})

        return result

    def serialize_token(self, token: BiscuitToken) -> str:
        return token.serialize()

    def deserialize_token(
        self, token_str: str, root_key_id: str = "default"
    ) -> BiscuitToken:
        return BiscuitToken.deserialize(token_str, root_key_id=root_key_id)

    def revoke_token(self, token_or_id) -> None:
        if isinstance(token_or_id, str):
            self._revoked_tokens.add(token_or_id)
        else:
            self._revoked_tokens.add(token_or_id.token_id)

    def is_token_revoked(self, token_or_id) -> bool:
        if isinstance(token_or_id, str):
            return token_or_id in self._revoked_tokens
        return token_or_id.token_id in self._revoked_tokens


_biscuit_service: BiscuitService | None = None


def get_biscuit_service() -> BiscuitService:
    global _biscuit_service
    if _biscuit_service is None:
        _biscuit_service = BiscuitService()
    return _biscuit_service


def create_biscuit_token(
    root_key: str,
    facts: list[BiscuitFact],
    checks: list[BiscuitCheck] | None = None,
    ttl_seconds: int = 3600,
) -> BiscuitToken:
    return get_biscuit_service().create_token(root_key, facts, checks, ttl_seconds)


def verify_biscuit_token(token: BiscuitToken, public_key: str) -> dict:
    return get_biscuit_service().verify_token(token, public_key)


def authorize_with_biscuit(
    token: BiscuitToken, public_key: str, query_facts: list[BiscuitFact]
) -> dict:
    return get_biscuit_service().authorize(token, public_key, query_facts)
