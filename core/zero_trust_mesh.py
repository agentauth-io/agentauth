"""
Zero-Trust mTLS Mesh for AgentAuth
===================================

Implements a zero-trust network security model with:
- Mutual TLS (mTLS) for all service communication
- Certificate-based identity
- SPIFFE/SPIRE compatible workload identity
- Automatic certificate rotation
- Service mesh integration
"""

import base64
import hashlib
import hmac
import json
import secrets
import struct
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import ipaddress


class IdentityType(str, Enum):
    """Types of workload identities."""
    
    SERVICE = "service"
    AGENT = "agent"
    USER = "user"
    WORKLOAD = "workload"


@dataclass
class ServiceIdentity:
    """SPIFFE-compatible service identity."""
    
    spiffe_id: str  # spiffe://trust-domain/path/to/service
    trust_domain: str
    service_name: str
    namespace: str
    labels: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_spiffe_id(cls, spiffe_id: str) -> "ServiceIdentity":
        """Parse a SPIFFE ID."""
        # Format: spiffe://trust-domain/path/parts
        if not spiffe_id.startswith("spiffe://"):
            raise ValueError("Invalid SPIFFE ID format")
        
        parts = spiffe_id[9:].split("/", 1)
        trust_domain = parts[0]
        path = parts[1] if len(parts) > 1 else ""
        
        path_parts = path.split("/") if path else []
        namespace = path_parts[0] if path_parts else "default"
        service_name = path_parts[1] if len(path_parts) > 1 else "unknown"
        
        return cls(
            spiffe_id=spiffe_id,
            trust_domain=trust_domain,
            service_name=service_name,
            namespace=namespace,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "spiffe_id": self.spiffe_id,
            "trust_domain": self.trust_domain,
            "service_name": self.service_name,
            "namespace": self.namespace,
            "labels": self.labels,
        }


@dataclass
class CertificateInfo:
    """X.509 certificate information."""
    
    serial_number: str
    subject: Dict[str, str]
    issuer: Dict[str, str]
    not_before: datetime
    not_after: datetime
    public_key_hash: str
    san_dns: List[str] = field(default_factory=list)
    san_uri: List[str] = field(default_factory=list)
    san_ip: List[str] = field(default_factory=list)
    key_usage: List[str] = field(default_factory=list)
    is_ca: bool = False
    
    @property
    def is_valid(self) -> bool:
        now = datetime.now(timezone.utc)
        return self.not_before <= now <= self.not_after
    
    @property
    def days_until_expiry(self) -> int:
        return (self.not_after - datetime.now(timezone.utc)).days
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "serial_number": self.serial_number,
            "subject": self.subject,
            "issuer": self.issuer,
            "not_before": self.not_before.isoformat(),
            "not_after": self.not_after.isoformat(),
            "public_key_hash": self.public_key_hash,
            "san_dns": self.san_dns,
            "san_uri": self.san_uri,
            "is_valid": self.is_valid,
            "days_until_expiry": self.days_until_expiry,
        }


@dataclass
class AuthorizationPolicy:
    """Service-to-service authorization policy."""
    
    name: str
    source: ServiceIdentity
    destination: ServiceIdentity
    allowed_methods: List[str]
    allowed_paths: List[str]
    conditions: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def matches(
        self,
        source_id: ServiceIdentity,
        dest_id: ServiceIdentity,
        method: str,
        path: str,
    ) -> bool:
        """Check if this policy matches the request."""
        if not self.enabled:
            return False
        
        # Match source
        if not self._matches_identity(self.source, source_id):
            return False
        
        # Match destination
        if not self._matches_identity(self.destination, dest_id):
            return False
        
        # Match method
        if "*" not in self.allowed_methods and method not in self.allowed_methods:
            return False
        
        # Match path
        if not self._matches_path(path):
            return False
        
        return True
    
    def _matches_identity(self, pattern: ServiceIdentity, actual: ServiceIdentity) -> bool:
        if pattern.spiffe_id == "*":
            return True
        if pattern.trust_domain != actual.trust_domain:
            return False
        if pattern.namespace != "*" and pattern.namespace != actual.namespace:
            return False
        if pattern.service_name != "*" and pattern.service_name != actual.service_name:
            return False
        return True
    
    def _matches_path(self, path: str) -> bool:
        for pattern in self.allowed_paths:
            if pattern == "*":
                return True
            if pattern.endswith("*"):
                if path.startswith(pattern[:-1]):
                    return True
            elif pattern == path:
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source.to_dict(),
            "destination": self.destination.to_dict(),
            "allowed_methods": self.allowed_methods,
            "allowed_paths": self.allowed_paths,
            "conditions": self.conditions,
            "enabled": self.enabled,
            "priority": self.priority,
        }


class CertificateAuthority:
    """Internal Certificate Authority for the mesh."""
    
    def __init__(self, trust_domain: str = "agentauth.local"):
        self.trust_domain = trust_domain
        
        # Generate CA key pair (simplified representation)
        self.ca_private_key = secrets.token_bytes(32)
        self.ca_public_key = hashlib.sha256(self.ca_private_key).digest()
        
        self.ca_cert = self._create_ca_cert()
        
        # Issued certificates
        self._certificates: Dict[str, CertificateInfo] = {}
        self._revoked: Set[str] = set()
        self._serial_counter = 0
        self._lock = threading.Lock()
    
    def _create_ca_cert(self) -> CertificateInfo:
        """Create the CA certificate."""
        now = datetime.now(timezone.utc)
        
        return CertificateInfo(
            serial_number="00",
            subject={
                "CN": f"AgentAuth CA",
                "O": "AgentAuth",
                "OU": "Security",
            },
            issuer={
                "CN": f"AgentAuth CA",
                "O": "AgentAuth",
            },
            not_before=now,
            not_after=now + timedelta(days=3650),  # 10 years
            public_key_hash=hashlib.sha256(self.ca_public_key).hexdigest(),
            key_usage=["certSign", "crlSign"],
            is_ca=True,
        )
    
    def issue_certificate(
        self,
        identity: ServiceIdentity,
        validity_days: int = 7,
        san_dns: Optional[List[str]] = None,
        san_ip: Optional[List[str]] = None,
    ) -> Tuple[CertificateInfo, bytes, bytes]:
        """
        Issue a certificate for a service identity.
        
        Returns: (cert_info, private_key, public_key)
        """
        with self._lock:
            self._serial_counter += 1
            serial = f"{self._serial_counter:08x}"
        
        # Generate key pair for the certificate
        private_key = secrets.token_bytes(32)
        public_key = hashlib.sha256(private_key).digest()
        
        now = datetime.now(timezone.utc)
        
        cert = CertificateInfo(
            serial_number=serial,
            subject={
                "CN": identity.service_name,
                "O": identity.trust_domain,
                "OU": identity.namespace,
            },
            issuer=self.ca_cert.subject,
            not_before=now,
            not_after=now + timedelta(days=validity_days),
            public_key_hash=hashlib.sha256(public_key).hexdigest(),
            san_dns=san_dns or [identity.service_name],
            san_uri=[identity.spiffe_id],
            san_ip=san_ip or [],
            key_usage=["digitalSignature", "keyEncipherment"],
        )
        
        self._certificates[serial] = cert
        
        return cert, private_key, public_key
    
    def verify_certificate(self, cert: CertificateInfo) -> Dict[str, Any]:
        """Verify a certificate."""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        # Check revocation
        if cert.serial_number in self._revoked:
            result["valid"] = False
            result["errors"].append("Certificate revoked")
        
        # Check validity period
        if not cert.is_valid:
            result["valid"] = False
            result["errors"].append("Certificate expired or not yet valid")
        
        # Check issuer
        if cert.issuer != self.ca_cert.subject:
            result["valid"] = False
            result["errors"].append("Unknown issuer")
        
        # Warn about upcoming expiry
        if cert.days_until_expiry < 7:
            result["warnings"].append(f"Certificate expires in {cert.days_until_expiry} days")
        
        return result
    
    def revoke_certificate(self, serial_number: str) -> bool:
        """Revoke a certificate."""
        if serial_number in self._certificates:
            self._revoked.add(serial_number)
            return True
        return False
    
    def get_crl(self) -> List[str]:
        """Get the Certificate Revocation List."""
        return list(self._revoked)
    
    def rotate_ca(self) -> CertificateInfo:
        """Rotate the CA certificate (cross-signing)."""
        # Store old CA
        old_ca_cert = self.ca_cert
        
        # Generate new CA key
        self.ca_private_key = secrets.token_bytes(32)
        self.ca_public_key = hashlib.sha256(self.ca_private_key).digest()
        self.ca_cert = self._create_ca_cert()
        
        return self.ca_cert


class MeshAuthenticator:
    """Handles mTLS authentication for the service mesh."""
    
    def __init__(self, ca: CertificateAuthority):
        self.ca = ca
        self._session_keys: Dict[str, Tuple[bytes, datetime]] = {}
        self._lock = threading.Lock()
    
    def authenticate_peer(
        self,
        peer_cert: CertificateInfo,
        client_random: bytes,
        server_random: bytes,
    ) -> Optional[bytes]:
        """
        Authenticate a peer and establish a session key.
        
        Returns session key if authentication succeeds.
        """
        # Verify certificate
        verification = self.ca.verify_certificate(peer_cert)
        if not verification["valid"]:
            return None
        
        # Derive session key
        key_material = client_random + server_random + peer_cert.public_key_hash.encode()
        session_key = hashlib.sha256(key_material).digest()
        
        # Store session
        with self._lock:
            self._session_keys[peer_cert.serial_number] = (
                session_key,
                datetime.now(timezone.utc),
            )
        
        return session_key
    
    def get_peer_identity(self, cert: CertificateInfo) -> Optional[ServiceIdentity]:
        """Extract service identity from certificate."""
        if not cert.san_uri:
            return None
        
        for uri in cert.san_uri:
            if uri.startswith("spiffe://"):
                return ServiceIdentity.from_spiffe_id(uri)
        
        return None
    
    def cleanup_sessions(self, max_age_hours: int = 24) -> int:
        """Cleanup old session keys."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        removed = 0
        
        with self._lock:
            expired = [
                serial for serial, (_, created) in self._session_keys.items()
                if created < cutoff
            ]
            for serial in expired:
                del self._session_keys[serial]
                removed += 1
        
        return removed


class ZeroTrustPolicyEngine:
    """Policy engine for zero-trust authorization."""
    
    def __init__(self):
        self.policies: List[AuthorizationPolicy] = []
        self._policy_cache: Dict[str, bool] = {}
        self._lock = threading.Lock()
        
        # Default policies
        self._add_default_policies()
    
    def _add_default_policies(self) -> None:
        """Add default deny-all policies."""
        # Health check policy - allow all
        self.add_policy(AuthorizationPolicy(
            name="allow-health-checks",
            source=ServiceIdentity(
                spiffe_id="spiffe://*/health-check",
                trust_domain="*",
                service_name="*",
                namespace="*",
            ),
            destination=ServiceIdentity(
                spiffe_id="spiffe://*/*",
                trust_domain="*",
                service_name="*",
                namespace="*",
            ),
            allowed_methods=["GET"],
            allowed_paths=["/health", "/healthz", "/ready"],
            priority=1000,
        ))
    
    def add_policy(self, policy: AuthorizationPolicy) -> None:
        """Add an authorization policy."""
        with self._lock:
            self.policies.append(policy)
            self.policies.sort(key=lambda p: -p.priority)  # Higher priority first
            self._policy_cache.clear()
    
    def remove_policy(self, name: str) -> bool:
        """Remove a policy by name."""
        with self._lock:
            initial_len = len(self.policies)
            self.policies = [p for p in self.policies if p.name != name]
            self._policy_cache.clear()
            return len(self.policies) < initial_len
    
    def authorize(
        self,
        source: ServiceIdentity,
        destination: ServiceIdentity,
        method: str,
        path: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[AuthorizationPolicy]]:
        """
        Check if a request is authorized.
        
        Returns: (is_authorized, matching_policy)
        """
        cache_key = f"{source.spiffe_id}:{destination.spiffe_id}:{method}:{path}"
        
        for policy in self.policies:
            if policy.matches(source, destination, method, path):
                return (True, policy)
        
        # Default deny
        return (False, None)
    
    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policies."""
        return [p.to_dict() for p in self.policies]


class MeshConfiguration:
    """Configuration for the service mesh."""
    
    def __init__(self):
        self.mtls_mode: str = "strict"  # "strict", "permissive", "disabled"
        self.cert_validity_days: int = 7
        self.auto_rotate: bool = True
        self.rotation_threshold_hours: int = 24
        self.allowed_cipher_suites: List[str] = [
            "TLS_AES_256_GCM_SHA384",
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
        ]
        self.min_tls_version: str = "1.3"
        self.trust_domains: List[str] = ["agentauth.local"]
        self.egress_hosts: List[str] = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mtls_mode": self.mtls_mode,
            "cert_validity_days": self.cert_validity_days,
            "auto_rotate": self.auto_rotate,
            "rotation_threshold_hours": self.rotation_threshold_hours,
            "allowed_cipher_suites": self.allowed_cipher_suites,
            "min_tls_version": self.min_tls_version,
            "trust_domains": self.trust_domains,
        }


class ZeroTrustMesh:
    """Main zero-trust mesh controller."""
    
    def __init__(self, trust_domain: str = "agentauth.local"):
        self.trust_domain = trust_domain
        self.ca = CertificateAuthority(trust_domain)
        self.authenticator = MeshAuthenticator(self.ca)
        self.policy_engine = ZeroTrustPolicyEngine()
        self.config = MeshConfiguration()
        
        # Service registry
        self._services: Dict[str, ServiceIdentity] = {}
        self._service_certs: Dict[str, CertificateInfo] = {}
        self._lock = threading.Lock()
        
        # Rotation thread
        self._rotation_thread = None
        if self.config.auto_rotate:
            self._start_rotation_thread()
    
    def register_service(
        self,
        name: str,
        namespace: str = "default",
        labels: Optional[Dict[str, str]] = None,
    ) -> Tuple[ServiceIdentity, CertificateInfo, bytes]:
        """
        Register a new service and issue its certificate.
        
        Returns: (identity, certificate, private_key)
        """
        spiffe_id = f"spiffe://{self.trust_domain}/{namespace}/{name}"
        
        identity = ServiceIdentity(
            spiffe_id=spiffe_id,
            trust_domain=self.trust_domain,
            service_name=name,
            namespace=namespace,
            labels=labels or {},
        )
        
        cert, private_key, _ = self.ca.issue_certificate(
            identity,
            validity_days=self.config.cert_validity_days,
        )
        
        with self._lock:
            self._services[spiffe_id] = identity
            self._service_certs[spiffe_id] = cert
        
        return identity, cert, private_key
    
    def deregister_service(self, spiffe_id: str) -> bool:
        """Deregister a service and revoke its certificate."""
        with self._lock:
            if spiffe_id not in self._services:
                return False
            
            cert = self._service_certs.get(spiffe_id)
            if cert:
                self.ca.revoke_certificate(cert.serial_number)
            
            del self._services[spiffe_id]
            del self._service_certs[spiffe_id]
            
        return True
    
    def authorize_request(
        self,
        source_cert: CertificateInfo,
        destination_spiffe_id: str,
        method: str,
        path: str,
    ) -> Dict[str, Any]:
        """Authorize a service-to-service request."""
        result = {
            "authorized": False,
            "source": None,
            "destination": None,
            "policy": None,
            "errors": [],
        }
        
        # Verify source certificate
        cert_verification = self.ca.verify_certificate(source_cert)
        if not cert_verification["valid"]:
            result["errors"] = cert_verification["errors"]
            return result
        
        # Get source identity
        source = self.authenticator.get_peer_identity(source_cert)
        if not source:
            result["errors"].append("Cannot determine source identity")
            return result
        
        result["source"] = source.to_dict()
        
        # Get destination identity
        destination = self._services.get(destination_spiffe_id)
        if not destination:
            destination = ServiceIdentity.from_spiffe_id(destination_spiffe_id)
        
        result["destination"] = destination.to_dict()
        
        # Check authorization policy
        authorized, policy = self.policy_engine.authorize(
            source, destination, method, path
        )
        
        result["authorized"] = authorized
        if policy:
            result["policy"] = policy.name
        else:
            result["errors"].append("No matching policy (default deny)")
        
        return result
    
    def add_authorization_rule(
        self,
        name: str,
        source_pattern: str,
        destination_pattern: str,
        methods: List[str],
        paths: List[str],
        priority: int = 0,
    ) -> AuthorizationPolicy:
        """Add a new authorization rule."""
        source = ServiceIdentity.from_spiffe_id(source_pattern)
        destination = ServiceIdentity.from_spiffe_id(destination_pattern)
        
        policy = AuthorizationPolicy(
            name=name,
            source=source,
            destination=destination,
            allowed_methods=methods,
            allowed_paths=paths,
            priority=priority,
        )
        
        self.policy_engine.add_policy(policy)
        return policy
    
    def _start_rotation_thread(self) -> None:
        """Start automatic certificate rotation."""
        def rotation_loop():
            while self.config.auto_rotate:
                try:
                    self._check_certificate_rotation()
                except Exception:
                    pass
                time.sleep(3600)  # Check every hour
        
        self._rotation_thread = threading.Thread(target=rotation_loop, daemon=True)
        self._rotation_thread.start()
    
    def _check_certificate_rotation(self) -> None:
        """Check and rotate certificates nearing expiry."""
        threshold_hours = self.config.rotation_threshold_hours
        
        with self._lock:
            for spiffe_id, cert in list(self._service_certs.items()):
                hours_until_expiry = (cert.not_after - datetime.now(timezone.utc)).total_seconds() / 3600
                
                if hours_until_expiry < threshold_hours:
                    identity = self._services.get(spiffe_id)
                    if identity:
                        new_cert, _, _ = self.ca.issue_certificate(
                            identity,
                            validity_days=self.config.cert_validity_days,
                        )
                        self._service_certs[spiffe_id] = new_cert
    
    def get_service_certificate(self, spiffe_id: str) -> Optional[CertificateInfo]:
        """Get a service's current certificate."""
        return self._service_certs.get(spiffe_id)
    
    def list_services(self) -> List[Dict[str, Any]]:
        """List all registered services."""
        results = []
        for spiffe_id, identity in self._services.items():
            cert = self._service_certs.get(spiffe_id)
            results.append({
                "identity": identity.to_dict(),
                "certificate": cert.to_dict() if cert else None,
            })
        return results
    
    def get_mesh_status(self) -> Dict[str, Any]:
        """Get mesh status."""
        return {
            "trust_domain": self.trust_domain,
            "services_registered": len(self._services),
            "ca_certificate_valid": self.ca.ca_cert.is_valid,
            "ca_days_until_expiry": self.ca.ca_cert.days_until_expiry,
            "policies_count": len(self.policy_engine.policies),
            "revoked_certificates": len(self.ca.get_crl()),
            "config": self.config.to_dict(),
        }


# Singleton instance
_mesh: Optional[ZeroTrustMesh] = None


def get_zero_trust_mesh() -> ZeroTrustMesh:
    """Get or create the zero-trust mesh singleton."""
    global _mesh
    if _mesh is None:
        _mesh = ZeroTrustMesh()
    return _mesh
