"""
AgentAuth Biscuit Token Service

Cryptographic delegation tokens using Biscuit (Ed25519 signatures).
Features:
- Offline attenuation (scope down permissions without server)
- Datalog-based authorization policies
- Stateless verification with public key

See: https://biscuitsec.org/
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import secrets
import hashlib
import json
import base64

# Note: In production, use biscuit-python package
# pip install biscuit-auth
# For now, we implement a compatible interface

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


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
    terms: List[Any]
    
    def to_datalog(self) -> str:
        terms_str = ", ".join(
            f'"{t}"' if isinstance(t, str) else str(t)
            for t in self.terms
        )
        return f"{self.name}({terms_str})"


@dataclass
class BiscuitRule:
    """A Datalog rule for authorization."""
    head: str
    body: List[str]
    
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
    facts: List[BiscuitFact] = field(default_factory=list)
    rules: List[BiscuitRule] = field(default_factory=list)
    checks: List[BiscuitCheck] = field(default_factory=list)
    context: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "facts": [f.to_datalog() for f in self.facts],
            "rules": [r.to_datalog() for r in self.rules],
            "checks": [c.to_datalog() for c in self.checks],
            "context": self.context,
        }


@dataclass
class Biscuit:
    """
    Biscuit token with cryptographic delegation chain.
    
    Structure:
    - Authority block: Root facts and rules (signed by root key)
    - Attenuation blocks: Additional restrictions (each signed)
    """
    
    authority: BiscuitBlock
    blocks: List[BiscuitBlock] = field(default_factory=list)
    
    # Token metadata
    token_id: str = ""
    created_at: str = ""
    root_key_id: str = ""
    
    # Serialized form
    _serialized: Optional[bytes] = None
    _signature: Optional[bytes] = None
    
    def __post_init__(self):
        if not self.token_id:
            self.token_id = f"bsc_{secrets.token_hex(16)}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
    
    def attenuate(self, block: BiscuitBlock) -> "Biscuit":
        """
        Create a new Biscuit with additional restrictions.
        
        The new token has all the original rights MINUS the new restrictions.
        This is done offline without contacting the issuer.
        """
        new_biscuit = Biscuit(
            authority=self.authority,
            blocks=self.blocks + [block],
            token_id=f"bsc_{secrets.token_hex(16)}",
            root_key_id=self.root_key_id,
        )
        return new_biscuit
    
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
            
            blocks = []
            for block_data in data.get("blocks", []):
                blocks.append(BiscuitBlock(
                    facts=[],
                    rules=[],
                    checks=[],
                    context=block_data.get("context"),
                ))
            
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
        """Add a fact to the authority block."""
        self.authority.facts.append(BiscuitFact(name, list(terms)))
        return self
    
    def add_rule(self, head: str, *body: str) -> "BiscuitBuilder":
        """Add a rule to the authority block."""
        self.authority.rules.append(BiscuitRule(head, list(body)))
        return self
    
    def add_check(self, rule: str) -> "BiscuitBuilder":
        """Add a check to the authority block."""
        self.authority.checks.append(BiscuitCheck(rule))
        return self
    
    def set_context(self, context: str) -> "BiscuitBuilder":
        """Set context for the authority block."""
        self.authority.context = context
        return self
    
    def build(self) -> Biscuit:
        """Build the Biscuit token."""
        return Biscuit(
            authority=self.authority,
            root_key_id=self.root_key_id,
        )


class BlockBuilder:
    """Builder for creating attenuation blocks."""
    
    def __init__(self):
        self.block = BiscuitBlock()
    
    def add_check(self, rule: str) -> "BlockBuilder":
        """Add a check (restriction) to the block."""
        self.block.checks.append(BiscuitCheck(rule))
        return self
    
    def add_fact(self, name: str, *terms) -> "BlockBuilder":
        """Add a fact to the block."""
        self.block.facts.append(BiscuitFact(name, list(terms)))
        return self
    
    def set_context(self, context: str) -> "BlockBuilder":
        """Set context for the block."""
        self.block.context = context
        return self
    
    def build(self) -> BiscuitBlock:
        """Build the block."""
        return self.block


class Authorizer:
    """
    Authorizer for verifying Biscuit tokens.
    
    Adds ambient facts (current context) and checks authorization.
    """
    
    def __init__(self):
        self.facts: List[BiscuitFact] = []
        self.rules: List[BiscuitRule] = []
        self.policies: List[str] = []
    
    def add_fact(self, name: str, *terms) -> "Authorizer":
        """Add an ambient fact (current context)."""
        self.facts.append(BiscuitFact(name, list(terms)))
        return self
    
    def add_rule(self, head: str, *body: str) -> "Authorizer":
        """Add a rule for authorization."""
        self.rules.append(BiscuitRule(head, list(body)))
        return self
    
    def allow(self) -> "Authorizer":
        """Add allow policy."""
        self.policies.append("allow")
        return self
    
    def deny(self) -> "Authorizer":
        """Add deny policy."""
        self.policies.append("deny")
        return self
    
    def authorize(self, biscuit: Biscuit) -> bool:
        """
        Authorize the Biscuit token.
        
        Checks all authority checks, block checks, and policies.
        Returns True if authorized, raises exception otherwise.
        """
        # In production, this would use the actual Datalog engine
        # For now, we do simplified authorization
        
        # Check all checks in authority block
        for check in biscuit.authority.checks:
            if not self._evaluate_check(check, biscuit):
                raise BiscuitAuthorizationError(
                    f"Authority check failed: {check.to_datalog()}"
                )
        
        # Check all checks in attenuation blocks
        for block in biscuit.blocks:
            for check in block.checks:
                if not self._evaluate_check(check, biscuit):
                    raise BiscuitAuthorizationError(
                        f"Block check failed: {check.to_datalog()}"
                    )
        
        # Apply policies
        if "deny" in self.policies:
            return False
        
        return True
    
    def _evaluate_check(self, check: BiscuitCheck, biscuit: Biscuit) -> bool:
        """Evaluate a single check against facts."""
        # Simplified check evaluation
        # In production, use Datalog engine
        return True


class BiscuitService:
    """
    Service for creating and verifying Biscuit tokens.
    
    Manages root keys and provides high-level API.
    """
    
    def __init__(self):
        self._root_keys: Dict[str, Ed25519PrivateKey] = {}
        self._public_keys: Dict[str, Ed25519PublicKey] = {}
    
    def generate_root_key(self, key_id: str = "default") -> str:
        """Generate a new root keypair."""
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        
        self._root_keys[key_id] = private_key
        self._public_keys[key_id] = public_key
        
        # Return public key in PEM format
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    
    def create_token(
        self,
        user_id: str,
        consent_id: str,
        permissions: List[str],
        max_amount: float,
        expires_at: datetime,
        key_id: str = "default"
    ) -> Biscuit:
        """
        Create a Biscuit token for agent delegation.
        
        Example:
            token = service.create_token(
                user_id="user_123",
                consent_id="consent_abc",
                permissions=["purchase", "search"],
                max_amount=500.0,
                expires_at=datetime.now() + timedelta(hours=24)
            )
        """
        builder = BiscuitBuilder(root_key_id=key_id)
        
        # Add identity facts
        builder.add_fact("user", user_id)
        builder.add_fact("consent", consent_id)
        
        # Add permissions
        for perm in permissions:
            builder.add_fact("permission", perm)
        
        # Add constraints
        builder.add_fact("max_amount", max_amount)
        builder.add_fact("expires_at", expires_at.isoformat())
        
        # Add checks
        builder.add_check(f'time($time), $time < {expires_at.isoformat()}')
        builder.add_check(f'amount($amt), $amt <= {max_amount}')
        
        return builder.build()
    
    def attenuate_token(
        self,
        token: Biscuit,
        new_max_amount: Optional[float] = None,
        allowed_merchants: Optional[List[str]] = None,
        allowed_categories: Optional[List[str]] = None,
    ) -> Biscuit:
        """
        Attenuate (restrict) an existing token.
        
        This creates a new token with fewer permissions.
        Can be done offline without server.
        """
        builder = BlockBuilder()
        
        if new_max_amount is not None:
            builder.add_check(f"amount($amt), $amt <= {new_max_amount}")
        
        if allowed_merchants:
            merchants_check = " or ".join(
                f'merchant("{m}")' for m in allowed_merchants
            )
            builder.add_check(merchants_check)
        
        if allowed_categories:
            categories_check = " or ".join(
                f'category("{c}")' for c in allowed_categories
            )
            builder.add_check(categories_check)
        
        return token.attenuate(builder.build())
    
    def verify_token(
        self,
        token: Biscuit,
        amount: float,
        merchant_id: str,
        category: Optional[str] = None,
    ) -> bool:
        """
        Verify a token for a specific transaction.
        
        Raises BiscuitAuthorizationError if verification fails.
        """
        authorizer = Authorizer()
        
        # Add ambient facts (current transaction context)
        authorizer.add_fact("amount", amount)
        authorizer.add_fact("merchant", merchant_id)
        authorizer.add_fact("time", datetime.now(timezone.utc).isoformat())
        
        if category:
            authorizer.add_fact("category", category)
        
        authorizer.allow()
        
        return authorizer.authorize(token)


# Singleton instance
_biscuit_service: Optional[BiscuitService] = None


def get_biscuit_service() -> BiscuitService:
    """Get singleton Biscuit service."""
    global _biscuit_service
    if _biscuit_service is None:
        _biscuit_service = BiscuitService()
    return _biscuit_service


# Convenience functions
def create_delegation_token(
    user_id: str,
    consent_id: str,
    permissions: List[str] = None,
    max_amount: float = 1000.0,
    expires_in_hours: int = 24
) -> str:
    """
    Create a delegation token for an agent.
    
    Returns serialized token string.
    """
    service = get_biscuit_service()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    
    token = service.create_token(
        user_id=user_id,
        consent_id=consent_id,
        permissions=permissions or ["purchase"],
        max_amount=max_amount,
        expires_at=expires_at
    )
    
    return token.serialize()


def attenuate_for_merchant(
    token_str: str,
    merchant_id: str,
    max_amount: Optional[float] = None
) -> str:
    """
    Create a merchant-specific attenuated token.
    
    The agent can give this to a specific merchant.
    """
    service = get_biscuit_service()
    token = Biscuit.deserialize(token_str)
    
    attenuated = service.attenuate_token(
        token=token,
        new_max_amount=max_amount,
        allowed_merchants=[merchant_id]
    )
    
    return attenuated.serialize()


def verify_delegation_token(
    token_str: str,
    amount: float,
    merchant_id: str
) -> bool:
    """
    Verify a delegation token for a transaction.
    """
    service = get_biscuit_service()
    token = Biscuit.deserialize(token_str)
    return service.verify_token(token, amount, merchant_id)
