"""
Audit Service - Comprehensive security logging

Provides tamper-evident audit logging for all sensitive operations.
"""
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.audit import AuditEntry

logger = logging.getLogger(__name__)
settings = get_settings()


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return f"evt_{uuid.uuid4().hex}"


def sign_audit_entry(event_data: dict[str, Any]) -> str:
    """
    Create a cryptographic signature for an audit entry.

    The signature covers all critical fields to ensure tamper evidence.
    """
    # Create a canonical string representation
    canonical = "|".join([
        event_data.get("event_type", ""),
        event_data.get("actor_id", ""),
        event_data.get("action", ""),
        event_data.get("resource_id", ""),
        event_data.get("outcome", ""),
        event_data.get("created_at", ""),
    ])

    # Sign with HMAC-SHA256 using the secret key
    signature = hmac.new(
        settings.secret_key.encode(),
        canonical.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature


async def create_audit_entry(
    db: AsyncSession,
    event_type: str,
    actor_id: str,
    actor_type: str,
    action: str,
    outcome: str,
    resource_id: str | None = None,
    resource_type: str | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEntry:
    """
    Create a tamper-evident audit entry.

    Args:
        db: Database session
        event_type: Type of event (e.g., "consent_created", "authorization_allowed")
        actor_id: ID of the actor (user, agent, system)
        actor_type: Type of actor (user, agent, system, admin)
        action: Action performed (e.g., "create", "authorize", "revoke")
        outcome: Outcome (success, failure, denied)
        resource_id: ID of the affected resource
        resource_type: Type of resource (consent, authorization, api_key)
        reason: Reason for failure/denial
        metadata: Additional context data
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        The created AuditEntry
    """
    event_id = generate_event_id()
    created_at = datetime.now(timezone.utc).isoformat()

    event_data = {
        "event_type": event_type,
        "actor_id": actor_id,
        "action": action,
        "resource_id": resource_id or "",
        "outcome": outcome,
        "created_at": created_at,
    }

    signature = sign_audit_entry(event_data)

    entry = AuditEntry(
        event_id=event_id,
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        resource_id=resource_id,
        resource_type=resource_type,
        outcome=outcome,
        reason=reason,
        event_metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
        signature=signature,
        created_at=datetime.now(timezone.utc),
    )

    db.add(entry)
    await db.flush()

    logger.info(
        f"Audit: {event_type} | {actor_type}:{actor_id} | {action} | {outcome} | {resource_type}:{resource_id}"
    )

    return entry


def verify_audit_entry(entry: AuditEntry) -> bool:
    """
    Verify the integrity of an audit entry.

    Returns True if the signature is valid (not tampered).
    """
    event_data = {
        "event_type": entry.event_type,
        "actor_id": entry.actor_id,
        "action": entry.action,
        "resource_id": entry.resource_id or "",
        "outcome": entry.outcome,
        "created_at": entry.created_at.isoformat(),
    }

    expected_signature = sign_audit_entry(event_data)
    return hmac.compare_digest(expected_signature, entry.signature)


async def query_audit_entries(
    db: AsyncSession,
    event_type: str | None = None,
    actor_id: str | None = None,
    resource_id: str | None = None,
    outcome: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Query audit entries with filters.

    Args:
        db: Database session
        event_type: Filter by event type
        actor_id: Filter by actor ID
        resource_id: Filter by resource ID
        outcome: Filter by outcome
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        List of AuditEntry objects
    """
    from sqlalchemy import and_, select

    query = select(AuditEntry)

    conditions = []
    if event_type:
        conditions.append(AuditEntry.event_type == event_type)
    if actor_id:
        conditions.append(AuditEntry.actor_id == actor_id)
    if resource_id:
        conditions.append(AuditEntry.resource_id == resource_id)
    if outcome:
        conditions.append(AuditEntry.outcome == outcome)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(AuditEntry.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()
