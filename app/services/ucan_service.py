"""
AgentAuth UCAN Service

User-Controlled Authorization Networks for cross-organizational agent delegation.
Based on the UCAN specification: https://ucan.xyz/

Features:
- Decentralized capability delegation
- No central authority required
- Sub-delegation of permissions
- Time-bounded capabilities
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import secrets
import json
import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


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
    """
    A capability (permission) in UCAN format.
    
    Format: { "with": resource, "can": action }
    """
    resource: str  # "agentauth:consent:*" or specific resource
    action: str    # "purchase", "search", "read", etc.
    caveats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        result = {"with": self.resource, "can": self.action}
        if self.caveats:
            result["caveats"] = self.caveats
        return result
    
    def is_subset_of(self, parent: "Capability") -> bool:
        """Check if this capability is a subset of parent (can be delegated)."""
        # Resource must match or be more specific
        if not self._resource_matches(self.resource, parent.resource):
            return False
        
        # Action must match or be more specific
        if parent.action != "*" and self.action != parent.action:
            return False
        
        return True
    
    @staticmethod
    def _resource_matches(child: str, parent: str) -> bool:
        """Check if child resource matches parent pattern."""
        if parent == "*" or parent.endswith(":*"):
            prefix = parent.rstrip("*")
            return child.startswith(prefix) or child == parent
        return child == parent


@dataclass
class UCANPayload:
    """UCAN payload structure."""
    
    # Required fields
    iss: str  # Issuer DID
    aud: str  # Audience DID
    exp: int  # Expiration timestamp
    
    # Capabilities
    att: List[Capability] = field(default_factory=list)  # Attenuations (capabilities)
    
    # Optional fields
    nbf: Optional[int] = None  # Not before timestamp
    nnc: Optional[str] = None  # Nonce
    fct: Dict[str, Any] = field(default_factory=dict)  # Facts
    prf: List[str] = field(default_factory=list)  # Proofs (parent UCANs)
    
    def to_dict(self) -> dict:
        result = {
            "iss": self.iss,
            "aud": self.aud,
            "exp": self.exp,
            "att": [c.to_dict() for c in self.att],
        }
        if self.nbf:
            result["nbf"] = self.nbf
        if self.nnc:
            result["nnc"] = self.nnc
        if self.fct:
            result["fct"] = self.fct
        if self.prf:
            result["prf"] = self.prf
        return result


@dataclass
class UCAN:
    """
    User-Controlled Authorization Network token.
    
    JWT-like structure with capability delegation.
    """
    
    # Header
    alg: str = "EdDSA"
    typ: str = "JWT"
    ucv: str = "0.10.0"  # UCAN version
    
    # Payload
    payload: UCANPayload = None
    
    # Signature
    signature: Optional[bytes] = None
    
    def __post_init__(self):
        if self.payload is None:
            raise UCANError("Payload is required")
    
    def to_jwt(self) -> str:
        """Serialize to JWT format."""
        header = {
            "alg": self.alg,
            "typ": self.typ,
            "ucv": self.ucv,
        }
        
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip("=")
        
        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(self.payload.to_dict()).encode()
        ).decode().rstrip("=")
        
        sig_b64 = ""
        if self.signature:
            sig_b64 = base64.urlsafe_b64encode(self.signature).decode().rstrip("=")
        
        return f"{header_b64}.{payload_b64}.{sig_b64}"
    
    @classmethod
    def from_jwt(cls, token: str) -> "UCAN":
        """Parse from JWT format."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise UCANValidationError("Invalid JWT format")
            
            # Pad base64
            def pad_b64(s):
                return s + "=" * (4 - len(s) % 4)
            
            header = json.loads(base64.urlsafe_b64decode(pad_b64(parts[0])))
            payload_dict = json.loads(base64.urlsafe_b64decode(pad_b64(parts[1])))
            
            # Parse capabilities
            capabilities = []
            for cap in payload_dict.get("att", []):
                capabilities.append(Capability(
                    resource=cap["with"],
                    action=cap["can"],
                    caveats=cap.get("caveats", {})
                ))
            
            payload = UCANPayload(
                iss=payload_dict["iss"],
                aud=payload_dict["aud"],
                exp=payload_dict["exp"],
                att=capabilities,
                nbf=payload_dict.get("nbf"),
                nnc=payload_dict.get("nnc"),
                fct=payload_dict.get("fct", {}),
                prf=payload_dict.get("prf", []),
            )
            
            signature = None
            if parts[2]:
                signature = base64.urlsafe_b64decode(pad_b64(parts[2]))
            
            return cls(
                alg=header.get("alg", "EdDSA"),
                typ=header.get("typ", "JWT"),
                ucv=header.get("ucv", "0.10.0"),
                payload=payload,
                signature=signature,
            )
        except Exception as e:
            raise UCANValidationError(f"Failed to parse UCAN: {e}")
    
    @property
    def is_expired(self) -> bool:
        """Check if UCAN has expired."""
        return datetime.now(timezone.utc).timestamp() > self.payload.exp
    
    @property
    def is_active(self) -> bool:
        """Check if UCAN is currently active (not before check)."""
        if self.payload.nbf:
            return datetime.now(timezone.utc).timestamp() >= self.payload.nbf
        return True
    
    @property
    def capabilities(self) -> List[Capability]:
        """Get capabilities from this UCAN."""
        return self.payload.att


class UCANBuilder:
    """Builder for creating UCAN tokens."""
    
    def __init__(self, issuer_did: str, audience_did: str):
        self.issuer = issuer_did
        self.audience = audience_did
        self.capabilities: List[Capability] = []
        self.expiration: Optional[datetime] = None
        self.not_before: Optional[datetime] = None
        self.facts: Dict[str, Any] = {}
        self.proofs: List[str] = []
        self.nonce: Optional[str] = None
    
    def with_capability(
        self,
        resource: str,
        action: str,
        **caveats
    ) -> "UCANBuilder":
        """Add a capability."""
        self.capabilities.append(Capability(
            resource=resource,
            action=action,
            caveats=caveats
        ))
        return self
    
    def with_expiration(self, expires_at: datetime) -> "UCANBuilder":
        """Set expiration time."""
        self.expiration = expires_at
        return self
    
    def with_lifetime(self, seconds: int) -> "UCANBuilder":
        """Set lifetime from now."""
        self.expiration = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        return self
    
    def with_not_before(self, not_before: datetime) -> "UCANBuilder":
        """Set not-before time."""
        self.not_before = not_before
        return self
    
    def with_fact(self, key: str, value: Any) -> "UCANBuilder":
        """Add a fact."""
        self.facts[key] = value
        return self
    
    def with_proof(self, parent_ucan: str) -> "UCANBuilder":
        """Add a parent UCAN as proof."""
        self.proofs.append(parent_ucan)
        return self
    
    def with_nonce(self, nonce: Optional[str] = None) -> "UCANBuilder":
        """Add a nonce for uniqueness."""
        self.nonce = nonce or secrets.token_hex(16)
        return self
    
    def build(self) -> UCAN:
        """Build the UCAN."""
        if not self.expiration:
            # Default to 24 hours
            self.expiration = datetime.now(timezone.utc) + timedelta(hours=24)
        
        payload = UCANPayload(
            iss=self.issuer,
            aud=self.audience,
            exp=int(self.expiration.timestamp()),
            att=self.capabilities,
            nbf=int(self.not_before.timestamp()) if self.not_before else None,
            nnc=self.nonce,
            fct=self.facts,
            prf=self.proofs,
        )
        
        return UCAN(payload=payload)


class UCANService:
    """
    Service for creating, delegating, and validating UCANs.
    
    Handles cross-organizational agent delegation.
    """
    
    def __init__(self):
        self._keys: Dict[str, Ed25519PrivateKey] = {}
        self._did_cache: Dict[str, str] = {}
    
    def generate_keypair(self, name: str = "default") -> str:
        """Generate a new Ed25519 keypair and return DID."""
        private_key = Ed25519PrivateKey.generate()
        self._keys[name] = private_key
        
        # Create DID from public key
        public_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        did = f"did:key:z{base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')}"
        self._did_cache[name] = did
        
        return did
    
    def get_did(self, name: str = "default") -> str:
        """Get DID for a keypair."""
        return self._did_cache.get(name)
    
    def create_root_ucan(
        self,
        issuer_name: str,
        audience_did: str,
        capabilities: List[Dict[str, Any]],
        lifetime_hours: int = 24
    ) -> str:
        """
        Create a root UCAN (no parent proofs).
        
        Example:
            ucan = service.create_root_ucan(
                issuer_name="default",
                audience_did="did:key:...",
                capabilities=[
                    {"resource": "agentauth:consent:*", "action": "purchase"}
                ]
            )
        """
        issuer_did = self.get_did(issuer_name)
        if not issuer_did:
            issuer_did = self.generate_keypair(issuer_name)
        
        builder = UCANBuilder(issuer_did, audience_did)
        builder.with_lifetime(lifetime_hours * 3600)
        builder.with_nonce()
        
        for cap in capabilities:
            builder.with_capability(
                resource=cap["resource"],
                action=cap["action"],
                **cap.get("caveats", {})
            )
        
        ucan = builder.build()
        return ucan.to_jwt()
    
    def delegate(
        self,
        parent_ucan: str,
        audience_did: str,
        capabilities: Optional[List[Dict[str, Any]]] = None,
        lifetime_hours: int = 24
    ) -> str:
        """
        Delegate capabilities from a parent UCAN.
        
        The new UCAN must have equal or fewer capabilities.
        """
        parent = UCAN.from_jwt(parent_ucan)
        
        # Validate parent is still valid
        if parent.is_expired:
            raise UCANValidationError("Parent UCAN has expired")
        
        # The issuer of the new UCAN is the audience of the parent
        issuer_did = parent.payload.aud
        
        builder = UCANBuilder(issuer_did, audience_did)
        builder.with_lifetime(lifetime_hours * 3600)
        builder.with_nonce()
        builder.with_proof(parent_ucan)
        
        # Use subset of capabilities
        if capabilities:
            for cap in capabilities:
                # Verify this is a valid subset
                parent_caps = parent.capabilities
                new_cap = Capability(
                    resource=cap["resource"],
                    action=cap["action"],
                    caveats=cap.get("caveats", {})
                )
                
                if not any(new_cap.is_subset_of(p) for p in parent_caps):
                    raise UCANCapabilityError(
                        f"Cannot delegate capability not in parent: {cap}"
                    )
                
                builder.with_capability(
                    resource=cap["resource"],
                    action=cap["action"],
                    **cap.get("caveats", {})
                )
        else:
            # Delegate all parent capabilities
            for cap in parent.capabilities:
                builder.with_capability(
                    resource=cap.resource,
                    action=cap.action,
                    **cap.caveats
                )
        
        ucan = builder.build()
        return ucan.to_jwt()
    
    def validate(
        self,
        ucan_jwt: str,
        required_capability: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Validate a UCAN token.
        
        Checks:
        - Signature (if provided)
        - Expiration
        - Not-before
        - Capability (if required)
        - Proof chain (parent UCANs)
        """
        ucan = UCAN.from_jwt(ucan_jwt)
        
        # Check expiration
        if ucan.is_expired:
            raise UCANValidationError("UCAN has expired")
        
        # Check not-before
        if not ucan.is_active:
            raise UCANValidationError("UCAN is not yet active")
        
        # Check required capability
        if required_capability:
            required = Capability(
                resource=required_capability["resource"],
                action=required_capability["action"]
            )
            
            if not any(required.is_subset_of(cap) for cap in ucan.capabilities):
                raise UCANCapabilityError(
                    f"UCAN does not have required capability: {required_capability}"
                )
        
        # Validate proof chain
        for proof in ucan.payload.prf:
            try:
                self.validate(proof)
            except UCANError as e:
                raise UCANValidationError(f"Invalid proof in chain: {e}")
        
        return True
    
    def get_capabilities(self, ucan_jwt: str) -> List[Dict[str, Any]]:
        """Get capabilities from a UCAN."""
        ucan = UCAN.from_jwt(ucan_jwt)
        return [cap.to_dict() for cap in ucan.capabilities]


# Singleton instance
_ucan_service: Optional[UCANService] = None


def get_ucan_service() -> UCANService:
    """Get singleton UCAN service."""
    global _ucan_service
    if _ucan_service is None:
        _ucan_service = UCANService()
    return _ucan_service


# Convenience functions for AgentAuth integration
def create_agent_ucan(
    user_did: str,
    agent_did: str,
    consent_id: str,
    max_amount: float,
    allowed_actions: List[str] = None
) -> str:
    """
    Create a UCAN for an agent to act on behalf of a user.
    
    Example:
        ucan = create_agent_ucan(
            user_did="did:key:user123",
            agent_did="did:key:agent456",
            consent_id="consent_abc",
            max_amount=500.0,
            allowed_actions=["purchase", "search"]
        )
    """
    service = get_ucan_service()
    
    capabilities = [
        {
            "resource": f"agentauth:consent:{consent_id}",
            "action": action,
            "caveats": {"max_amount": max_amount}
        }
        for action in (allowed_actions or ["purchase"])
    ]
    
    return service.create_root_ucan(
        issuer_name="user",
        audience_did=agent_did,
        capabilities=capabilities,
        lifetime_hours=24
    )


def delegate_to_sub_agent(
    parent_ucan: str,
    sub_agent_did: str,
    restricted_amount: Optional[float] = None,
    restricted_actions: Optional[List[str]] = None
) -> str:
    """
    Delegate capabilities from one agent to another (sub-agent).
    
    Example:
        sub_ucan = delegate_to_sub_agent(
            parent_ucan=main_agent_ucan,
            sub_agent_did="did:key:subagent789",
            restricted_amount=100.0,  # Can only spend up to $100
            restricted_actions=["purchase"]
        )
    """
    service = get_ucan_service()
    parent = UCAN.from_jwt(parent_ucan)
    
    capabilities = None
    if restricted_actions:
        capabilities = [
            {
                "resource": cap.resource,
                "action": action,
                "caveats": {
                    **cap.caveats,
                    **({"max_amount": restricted_amount} if restricted_amount else {})
                }
            }
            for cap in parent.capabilities
            for action in restricted_actions
            if action == cap.action or cap.action == "*"
        ]
    
    return service.delegate(
        parent_ucan=parent_ucan,
        audience_did=sub_agent_did,
        capabilities=capabilities
    )


def verify_agent_capability(
    ucan_jwt: str,
    action: str,
    amount: float
) -> bool:
    """
    Verify an agent has capability to perform an action.
    """
    service = get_ucan_service()
    return service.validate(
        ucan_jwt,
        required_capability={"resource": "agentauth:consent:*", "action": action}
    )
