"""
AgentAuth Advanced Security API
================================

Unified API for all advanced security components:
- ML Threat Intelligence
- Blockchain Audit Trail
- Vault Secrets Management
- Zero-Trust Mesh
- Distributed Consensus
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

# Import security modules
from core.blockchain_audit import (
    AuditEventType,
    BlockchainAuditTrail,
    get_audit_trail,
)
from core.vault_integration import (
    SecretType,
    VaultClient,
    get_vault_client,
)
from core.zero_trust_mesh import (
    ServiceIdentity,
    ZeroTrustMesh,
    get_zero_trust_mesh,
)
from core.consensus import (
    ConsensusCluster,
    ConsensusRequest,
    get_consensus_cluster,
)
from app.ml.threat_intelligence import (
    ThreatIntelligence,
    get_threat_intelligence,
)


router = APIRouter(prefix="/v1/security", tags=["security"])


# ==================== Request/Response Models ====================

class ThreatAssessmentRequest(BaseModel):
    request_id: Optional[str] = None
    agent_id: str
    action: str
    amount: Optional[float] = None
    merchant: Optional[str] = None
    ip_address: Optional[str] = None
    trust_score: float = 0.8
    new_device: bool = False
    distance_km: float = 0.0


class AuditLogRequest(BaseModel):
    event_type: str
    actor_id: str
    actor_type: str = "agent"
    action: str
    outcome: str = "success"
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecretRequest(BaseModel):
    path: str
    data: Dict[str, Any]
    secret_type: str = "api_key"
    description: str = ""
    ttl_hours: Optional[int] = None


class ServiceRegistrationRequest(BaseModel):
    name: str
    namespace: str = "default"
    labels: Dict[str, str] = Field(default_factory=dict)


class AuthorizationRuleRequest(BaseModel):
    name: str
    source_pattern: str
    destination_pattern: str
    methods: List[str]
    paths: List[str]
    priority: int = 0


class ConsensusOperationRequest(BaseModel):
    operation: str
    data: Dict[str, Any]
    client_id: str = "api-client"


# ==================== Threat Intelligence ====================

@router.post("/threat/assess")
async def assess_threat(request: ThreatAssessmentRequest):
    """
    Perform ML-based threat assessment on a request.
    
    Returns risk score, threat signals, and recommendations.
    """
    ti = get_threat_intelligence()
    
    assessment = ti.assess_threat({
        "request_id": request.request_id,
        "agent_id": request.agent_id,
        "action": request.action,
        "amount": request.amount,
        "merchant": request.merchant,
        "ip_address": request.ip_address,
        "trust_score": request.trust_score,
        "new_device": request.new_device,
        "distance_km": request.distance_km,
    })
    
    return assessment.to_dict()


@router.get("/threat/stats")
async def get_threat_stats():
    """Get threat intelligence statistics."""
    ti = get_threat_intelligence()
    
    return {
        "is_trained": ti.is_trained,
        "training_samples": len(ti.training_data),
        "blocked_ips": len(ti.blocked_ips),
        "thresholds": ti.thresholds,
    }


@router.post("/threat/block-ip/{ip}")
async def block_ip(ip: str):
    """Add an IP to the blocklist."""
    ti = get_threat_intelligence()
    ti.block_ip(ip)
    return {"status": "blocked", "ip": ip}


# ==================== Blockchain Audit Trail ====================

@router.post("/audit/log")
async def create_audit_log(request: AuditLogRequest):
    """
    Create an immutable audit log entry.
    
    Entries are cryptographically chained and can be verified.
    """
    audit = get_audit_trail()
    
    try:
        event_type = AuditEventType(request.event_type)
    except ValueError:
        event_type = AuditEventType.AUTHORIZATION_REQUEST
    
    entry_id = audit.log(
        event_type=event_type,
        actor_id=request.actor_id,
        actor_type=request.actor_type,
        action=request.action,
        outcome=request.outcome,
        resource_id=request.resource_id,
        resource_type=request.resource_type,
        metadata=request.metadata,
    )
    
    return {"entry_id": entry_id, "status": "logged"}


@router.get("/audit/entry/{entry_id}")
async def get_audit_entry(entry_id: str):
    """Get an audit entry by ID."""
    audit = get_audit_trail()
    entry = audit.get_entry(entry_id)
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return entry.to_dict()


@router.get("/audit/entry/{entry_id}/verify")
async def verify_audit_entry(entry_id: str):
    """Verify an audit entry's integrity and get Merkle proof."""
    audit = get_audit_trail()
    return audit.verify_entry(entry_id)


@router.get("/audit/query")
async def query_audit_logs(
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    limit: int = 50,
):
    """Query audit logs with filters."""
    audit = get_audit_trail()
    
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = AuditEventType(event_type)
        except ValueError:
            pass
    
    entries = audit.query(
        event_type=event_type_enum,
        actor_id=actor_id,
        resource_id=resource_id,
        limit=limit,
    )
    
    return {
        "entries": [e.to_dict() for e in entries],
        "count": len(entries),
    }


@router.get("/audit/chain/verify")
async def verify_chain():
    """Verify the entire audit chain's integrity."""
    audit = get_audit_trail()
    return audit.verify_chain()


@router.get("/audit/chain/stats")
async def get_chain_stats():
    """Get blockchain statistics."""
    audit = get_audit_trail()
    return audit.get_stats()


@router.post("/audit/flush")
async def flush_audit():
    """Force creation of a new block from pending entries."""
    audit = get_audit_trail()
    block = audit.flush()
    
    if block:
        return {
            "block_created": True,
            "block_index": block.index,
            "entries_count": len(block.entries),
        }
    return {"block_created": False}


# ==================== Vault Secrets Management ====================

@router.post("/vault/secrets")
async def store_secret(request: SecretRequest):
    """Store a secret in the vault."""
    vault = get_vault_client()
    
    try:
        secret_type = SecretType(request.secret_type)
    except ValueError:
        secret_type = SecretType.API_KEY
    
    result = vault.kv_put(
        path=request.path,
        data=request.data,
        secret_type=secret_type,
        description=request.description,
        ttl_hours=request.ttl_hours,
    )
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "path": request.path,
        "version": result.data.get("version"),
        "status": "stored",
    }


@router.get("/vault/secrets/{path:path}")
async def get_secret(path: str, version: Optional[int] = None):
    """Retrieve a secret from the vault."""
    vault = get_vault_client()
    result = vault.kv_get(path, version)
    
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    
    return {
        "path": path,
        "data": result.data,
        "metadata": result.metadata.to_dict() if result.metadata else None,
    }


@router.delete("/vault/secrets/{path:path}")
async def delete_secret(path: str):
    """Delete a secret from the vault."""
    vault = get_vault_client()
    result = vault.kv_delete(path)
    
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    
    return {"status": "deleted", "path": path}


@router.post("/vault/api-keys/generate")
async def generate_api_key(
    name: str,
    tier: str = "standard",
    ttl_hours: int = 720,
):
    """Generate a new dynamic API key."""
    vault = get_vault_client()
    result = vault.generate_api_key(name, tier, ttl_hours)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/vault/api-keys/verify")
async def verify_api_key(api_key: str):
    """Verify an API key."""
    vault = get_vault_client()
    result = vault.verify_api_key(api_key)
    
    return result.data if result.success else {"valid": False}


@router.post("/vault/transit/encrypt/{key_name}")
async def transit_encrypt(key_name: str, plaintext: str):
    """Encrypt data using transit engine."""
    vault = get_vault_client()
    result = vault.transit_encrypt(key_name, plaintext.encode())
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.post("/vault/transit/decrypt/{key_name}")
async def transit_decrypt(key_name: str, ciphertext: str):
    """Decrypt data using transit engine."""
    vault = get_vault_client()
    result = vault.transit_decrypt(key_name, ciphertext)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result.data


@router.get("/vault/health")
async def get_vault_health():
    """Get vault health status."""
    vault = get_vault_client()
    return vault.get_health()


# ==================== Zero-Trust Mesh ====================

@router.post("/mesh/services")
async def register_service(request: ServiceRegistrationRequest):
    """Register a service in the zero-trust mesh."""
    mesh = get_zero_trust_mesh()
    
    identity, cert, private_key = mesh.register_service(
        name=request.name,
        namespace=request.namespace,
        labels=request.labels,
    )
    
    return {
        "identity": identity.to_dict(),
        "certificate": cert.to_dict(),
        "private_key_issued": True,
    }


@router.delete("/mesh/services/{spiffe_id:path}")
async def deregister_service(spiffe_id: str):
    """Deregister a service from the mesh."""
    mesh = get_zero_trust_mesh()
    
    if mesh.deregister_service(spiffe_id):
        return {"status": "deregistered", "spiffe_id": spiffe_id}
    
    raise HTTPException(status_code=404, detail="Service not found")


@router.get("/mesh/services")
async def list_services():
    """List all registered services."""
    mesh = get_zero_trust_mesh()
    return {"services": mesh.list_services()}


@router.post("/mesh/policies")
async def add_authorization_rule(request: AuthorizationRuleRequest):
    """Add a service-to-service authorization rule."""
    mesh = get_zero_trust_mesh()
    
    policy = mesh.add_authorization_rule(
        name=request.name,
        source_pattern=request.source_pattern,
        destination_pattern=request.destination_pattern,
        methods=request.methods,
        paths=request.paths,
        priority=request.priority,
    )
    
    return {"policy": policy.to_dict(), "status": "created"}


@router.get("/mesh/policies")
async def list_authorization_policies():
    """List all authorization policies."""
    mesh = get_zero_trust_mesh()
    return {"policies": mesh.policy_engine.list_policies()}


@router.delete("/mesh/policies/{name}")
async def delete_authorization_policy(name: str):
    """Delete an authorization policy."""
    mesh = get_zero_trust_mesh()
    
    if mesh.policy_engine.remove_policy(name):
        return {"status": "deleted", "name": name}
    
    raise HTTPException(status_code=404, detail="Policy not found")


@router.get("/mesh/status")
async def get_mesh_status():
    """Get mesh status."""
    mesh = get_zero_trust_mesh()
    return mesh.get_mesh_status()


@router.get("/mesh/ca/certificate")
async def get_ca_certificate():
    """Get the mesh CA certificate."""
    mesh = get_zero_trust_mesh()
    return mesh.ca.ca_cert.to_dict()


@router.get("/mesh/ca/crl")
async def get_certificate_revocation_list():
    """Get the certificate revocation list."""
    mesh = get_zero_trust_mesh()
    return {"revoked_serials": mesh.ca.get_crl()}


# ==================== Distributed Consensus ====================

@router.post("/consensus/submit")
async def submit_consensus_operation(request: ConsensusOperationRequest):
    """Submit an operation for distributed consensus."""
    cluster = get_consensus_cluster()
    
    request_id = cluster.submit_request(
        operation=request.operation,
        data=request.data,
        client_id=request.client_id,
    )
    
    # Get result (already processed in simulation mode)
    result = cluster.get_result(request_id)
    
    if result:
        return result.to_dict()
    
    return {
        "request_id": request_id,
        "status": "submitted",
    }


@router.get("/consensus/result/{request_id}")
async def get_consensus_result(request_id: str):
    """Get the result of a consensus operation."""
    cluster = get_consensus_cluster()
    result = cluster.get_result(request_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    return result.to_dict()


@router.get("/consensus/status")
async def get_consensus_status():
    """Get consensus cluster status."""
    cluster = get_consensus_cluster()
    return cluster.get_status()


# ==================== Unified Security Dashboard ====================

@router.get("/dashboard")
async def get_security_dashboard():
    """Get unified security dashboard data."""
    ti = get_threat_intelligence()
    audit = get_audit_trail()
    vault = get_vault_client()
    mesh = get_zero_trust_mesh()
    cluster = get_consensus_cluster()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threat_intelligence": {
            "is_trained": ti.is_trained,
            "training_samples": len(ti.training_data),
            "blocked_ips": len(ti.blocked_ips),
        },
        "audit_trail": audit.get_stats(),
        "vault": vault.get_health(),
        "mesh": mesh.get_mesh_status(),
        "consensus": cluster.get_status(),
    }


# ==================== Health Check ====================

@router.get("/health")
async def security_health_check():
    """Health check for security components."""
    return {
        "status": "healthy",
        "components": {
            "threat_intelligence": "ok",
            "audit_trail": "ok",
            "vault": "ok",
            "mesh": "ok",
            "consensus": "ok",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
