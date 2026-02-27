"""
Audit model for comprehensive security logging.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Index, String, Text

from app.models.database import Base


class AuditEntry(Base):
    """
    Audit log entry for security and compliance.

    All sensitive operations are logged with cryptographic signatures
    for tamper evidence.
    """
    __tablename__ = "audit_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(64), unique=True, nullable=False, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    actor_id = Column(String(255), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False)  # user, agent, system, admin
    action = Column(String(100), nullable=False)

    # Resource details
    resource_id = Column(String(255), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True)

    # Outcome
    outcome = Column(String(20), nullable=False)  # success, failure, denied
    reason = Column(String(255), nullable=True)

    # Additional context
    event_metadata = Column(JSON, nullable=False, default=dict)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)

    # Cryptographic signature for tamper evidence
    signature = Column(String(128), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_audit_event_type_created", "event_type", "created_at"),
        Index("ix_audit_actor_created", "actor_id", "created_at"),
        Index("ix_audit_outcome_created", "outcome", "created_at"),
    )
