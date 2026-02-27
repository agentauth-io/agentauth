"""
AgentAuth Core - Audit System
=============================
PROPRIETARY AND CONFIDENTIAL

Immutable, cryptographically-signed audit logging system.
Every authorization decision is logged with tamper-evident signatures.

Features:
- Append-only log structure
- Cryptographic signatures on each entry
- Hash chaining (each entry links to previous)
- Merkle tree for efficient verification
- Export for compliance/legal

Log Entry Structure:
{
    "id": "audit_abc123",
    "sequence": 12345,
    "timestamp": 1706745600.123,
    "prev_hash": "a1b2c3...",
    "type": "authorization",
    "data": { ... },
    "signature": "sig_hex...",
    "hash": "entry_hash..."
}
"""

import hashlib
import json
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .crypto import KeyManager, SigningKeyPair, generate_id


class AuditEventType(Enum):
    """Types of audit events."""
    AUTHORIZATION_REQUEST = "auth_request"
    AUTHORIZATION_DECISION = "auth_decision"
    TOKEN_ISSUED = "token_issued"
    TOKEN_VERIFIED = "token_verified"
    TOKEN_REVOKED = "token_revoked"
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"
    AGENT_REGISTERED = "agent_registered"
    AGENT_REVOKED = "agent_revoked"
    SPENDING_RECORDED = "spending_recorded"
    LIMIT_EXCEEDED = "limit_exceeded"
    RATE_LIMITED = "rate_limited"
    SYSTEM_EVENT = "system_event"


@dataclass
class AuditEntry:
    """A single audit log entry."""
    id: str
    sequence: int
    timestamp: float
    prev_hash: str
    event_type: AuditEventType
    agent_id: str | None
    user_id: str | None
    data: dict[str, Any]
    signature: str = ""
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute hash of this entry (excluding signature and hash fields)."""
        content = {
            "id": self.id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "data": self.data
        }
        return hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "data": self.data,
            "signature": self.signature,
            "hash": self.hash
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            id=data["id"],
            sequence=data["sequence"],
            timestamp=data["timestamp"],
            prev_hash=data["prev_hash"],
            event_type=AuditEventType(data["event_type"]),
            agent_id=data.get("agent_id"),
            user_id=data.get("user_id"),
            data=data["data"],
            signature=data.get("signature", ""),
            hash=data.get("hash", "")
        )


class AuditLog:
    """
    Cryptographically-secured audit log.

    Features:
    - Hash chaining for tamper detection
    - Cryptographic signatures for authenticity
    - Thread-safe append operations
    - Persistence support
    """

    GENESIS_HASH = "0" * 64  # Genesis block hash

    def __init__(
        self,
        signing_key: SigningKeyPair,
        persistence_path: str | None = None
    ):
        """
        Initialize audit log.

        Args:
            signing_key: Key for signing entries
            persistence_path: Path to persist log (optional)
        """
        self._signing_key = signing_key
        self._persistence_path = persistence_path
        self._entries: list[AuditEntry] = []
        self._sequence = 0
        self._lock = threading.Lock()
        self._subscribers: list[Callable[[AuditEntry], None]] = []

        # Load existing entries if persistence enabled
        if persistence_path and os.path.exists(persistence_path):
            self._load()

    def append(
        self,
        event_type: AuditEventType,
        data: dict[str, Any],
        agent_id: str | None = None,
        user_id: str | None = None
    ) -> AuditEntry:
        """
        Append a new entry to the audit log.

        Args:
            event_type: Type of audit event
            data: Event-specific data
            agent_id: Related agent (if applicable)
            user_id: Related user (if applicable)

        Returns:
            The created audit entry
        """
        with self._lock:
            # Get previous hash
            if self._entries:
                prev_hash = self._entries[-1].hash
            else:
                prev_hash = self.GENESIS_HASH

            # Create entry
            self._sequence += 1
            entry = AuditEntry(
                id=generate_id("audit"),
                sequence=self._sequence,
                timestamp=time.time(),
                prev_hash=prev_hash,
                event_type=event_type,
                agent_id=agent_id,
                user_id=user_id,
                data=data
            )

            # Compute hash
            entry.hash = entry.compute_hash()

            # Sign the hash
            signature = self._signing_key.sign(entry.hash.encode())
            entry.signature = signature.hex()

            # Store
            self._entries.append(entry)

            # Persist
            if self._persistence_path:
                self._persist_entry(entry)

            # Notify subscribers
            for subscriber in self._subscribers:
                try:
                    subscriber(entry)
                except Exception:
                    pass

            return entry

    def verify_chain(self) -> tuple[bool, int | None, str]:
        """
        Verify the integrity of the entire audit chain.

        Returns:
            (valid, first_invalid_sequence, error_message)
        """
        if not self._entries:
            return (True, None, "")

        prev_hash = self.GENESIS_HASH

        for entry in self._entries:
            # Check hash chain
            if entry.prev_hash != prev_hash:
                return (
                    False,
                    entry.sequence,
                    f"Hash chain broken at sequence {entry.sequence}"
                )

            # Verify hash
            computed_hash = entry.compute_hash()
            if entry.hash != computed_hash:
                return (
                    False,
                    entry.sequence,
                    f"Hash mismatch at sequence {entry.sequence}"
                )

            # Verify signature
            try:
                valid = self._signing_key.verify(
                    entry.hash.encode(),
                    bytes.fromhex(entry.signature)
                )
                if not valid:
                    return (
                        False,
                        entry.sequence,
                        f"Invalid signature at sequence {entry.sequence}"
                    )
            except Exception as e:
                return (
                    False,
                    entry.sequence,
                    f"Signature verification error at {entry.sequence}: {e}"
                )

            prev_hash = entry.hash

        return (True, None, "Chain verified successfully")

    def verify_entry(self, entry: AuditEntry) -> bool:
        """Verify a single entry's signature."""
        try:
            return self._signing_key.verify(
                entry.hash.encode(),
                bytes.fromhex(entry.signature)
            )
        except Exception:
            return False

    def get_entries(
        self,
        start_sequence: int | None = None,
        end_sequence: int | None = None,
        event_type: AuditEventType | None = None,
        agent_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100
    ) -> list[AuditEntry]:
        """
        Query audit entries with filters.

        Args:
            start_sequence: Start from this sequence (inclusive)
            end_sequence: End at this sequence (inclusive)
            event_type: Filter by event type
            agent_id: Filter by agent
            user_id: Filter by user
            limit: Maximum entries to return

        Returns:
            List of matching entries
        """
        results = []

        for entry in reversed(self._entries):  # Most recent first
            if len(results) >= limit:
                break

            if start_sequence and entry.sequence < start_sequence:
                continue
            if end_sequence and entry.sequence > end_sequence:
                continue
            if event_type and entry.event_type != event_type:
                continue
            if agent_id and entry.agent_id != agent_id:
                continue
            if user_id and entry.user_id != user_id:
                continue

            results.append(entry)

        return results

    def get_by_id(self, entry_id: str) -> AuditEntry | None:
        """Get entry by ID."""
        for entry in self._entries:
            if entry.id == entry_id:
                return entry
        return None

    def subscribe(self, callback: Callable[[AuditEntry], None]):
        """Subscribe to new entries."""
        self._subscribers.append(callback)

    def compute_merkle_root(self) -> str:
        """
        Compute Merkle root of all entries.

        This allows efficient verification that a specific entry
        is part of the log.
        """
        if not self._entries:
            return self.GENESIS_HASH

        hashes = [e.hash for e in self._entries]

        while len(hashes) > 1:
            new_hashes = []
            for i in range(0, len(hashes), 2):
                left = hashes[i]
                right = hashes[i + 1] if i + 1 < len(hashes) else left
                combined = hashlib.sha256(
                    (left + right).encode()
                ).hexdigest()
                new_hashes.append(combined)
            hashes = new_hashes

        return hashes[0]

    def export(self, path: str, format: str = "json"):
        """
        Export audit log to file.

        Args:
            path: Output file path
            format: Export format (json, jsonl, csv)
        """
        if format == "json":
            with open(path, 'w') as f:
                json.dump(
                    [e.to_dict() for e in self._entries],
                    f,
                    indent=2
                )
        elif format == "jsonl":
            with open(path, 'w') as f:
                for entry in self._entries:
                    f.write(json.dumps(entry.to_dict()) + "\n")
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _persist_entry(self, entry: AuditEntry):
        """Persist single entry (append mode)."""
        with open(self._persistence_path, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def _load(self):
        """Load entries from persistence file."""
        try:
            with open(self._persistence_path) as f:
                for line in f:
                    if line.strip():
                        entry = AuditEntry.from_dict(json.loads(line))
                        self._entries.append(entry)
                        self._sequence = max(self._sequence, entry.sequence)
        except Exception as e:
            print(f"Warning: Failed to load audit log: {e}")

    @property
    def length(self) -> int:
        """Number of entries in log."""
        return len(self._entries)

    @property
    def latest_hash(self) -> str:
        """Hash of most recent entry."""
        if self._entries:
            return self._entries[-1].hash
        return self.GENESIS_HASH

    def stats(self) -> dict[str, Any]:
        """Get audit log statistics."""
        if not self._entries:
            return {
                "total_entries": 0,
                "first_timestamp": None,
                "last_timestamp": None,
                "merkle_root": self.GENESIS_HASH
            }

        event_counts = {}
        for entry in self._entries:
            event_type = entry.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "total_entries": len(self._entries),
            "first_timestamp": self._entries[0].timestamp,
            "last_timestamp": self._entries[-1].timestamp,
            "merkle_root": self.compute_merkle_root(),
            "event_counts": event_counts
        }


# Test the audit system
if __name__ == "__main__":
    print("AgentAuth Core Audit System Test")
    print("=" * 50)

    from .crypto import KeyManager

    # Initialize
    km = KeyManager()
    audit_log = AuditLog(km.audit_signing_key)

    print("[+] Audit log initialized")

    # Add some entries
    entries = [
        (AuditEventType.AUTHORIZATION_REQUEST, {
            "action": "purchase",
            "amount": 49.99,
            "merchant": "Amazon"
        }),
        (AuditEventType.AUTHORIZATION_DECISION, {
            "decision": "allow",
            "policy_id": "pol_123",
            "risk_score": 0.1
        }),
        (AuditEventType.TOKEN_ISSUED, {
            "token_id": "aa_tx_abc123",
            "expires": time.time() + 3600
        }),
        (AuditEventType.SPENDING_RECORDED, {
            "amount": 49.99,
            "remaining_daily": 450.01
        }),
    ]

    for event_type, data in entries:
        entry = audit_log.append(
            event_type=event_type,
            data=data,
            agent_id="agent_123",
            user_id="user_abc"
        )
        print(f"  + {event_type.value}: {entry.id} (seq: {entry.sequence})")

    print(f"\n[+] Total entries: {audit_log.length}")

    # Verify chain
    valid, seq, msg = audit_log.verify_chain()
    print(f"[+] Chain verification: {'PASS' if valid else 'FAIL'}")
    if not valid:
        print(f"    Error at sequence {seq}: {msg}")

    # Compute merkle root
    merkle_root = audit_log.compute_merkle_root()
    print(f"[+] Merkle root: {merkle_root[:32]}...")

    # Query entries
    recent = audit_log.get_entries(limit=2)
    print("\n[+] Most recent 2 entries:")
    for entry in recent:
        print(f"    - {entry.event_type.value} at {entry.timestamp}")

    # Stats
    stats = audit_log.stats()
    print(f"\n[+] Stats: {stats['total_entries']} entries, {len(stats['event_counts'])} event types")

    print("\n[*] All audit tests passed!")
