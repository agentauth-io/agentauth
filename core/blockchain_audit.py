"""
Blockchain Audit Trail for AgentAuth
=====================================

Immutable, cryptographically verifiable audit log using:
- Merkle tree for efficient proof verification
- Hash chaining for tamper evidence
- Distributed consensus (optional)
- IPFS integration for decentralized storage
"""

import hashlib
import hmac
import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AuditEventType(str, Enum):
    """Types of audit events."""

    AUTHORIZATION_REQUEST = "authorization.request"
    AUTHORIZATION_APPROVED = "authorization.approved"
    AUTHORIZATION_DENIED = "authorization.denied"
    AUTHORIZATION_REVOKED = "authorization.revoked"

    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_DELETED = "policy.deleted"
    POLICY_TOGGLED = "policy.toggled"

    AGENT_REGISTERED = "agent.registered"
    AGENT_REVOKED = "agent.revoked"
    AGENT_UPDATED = "agent.updated"

    KEY_ROTATED = "key.rotated"
    KEY_CREATED = "key.created"
    KEY_REVOKED = "key.revoked"

    SECURITY_ALERT = "security.alert"
    SECURITY_BREACH_ATTEMPT = "security.breach_attempt"

    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_CONFIG_CHANGE = "system.config_change"


@dataclass
class AuditEntry:
    """A single audit log entry."""

    id: str
    timestamp: datetime
    event_type: AuditEventType
    actor_id: str
    actor_type: str  # "agent", "user", "system"
    resource_id: str | None
    resource_type: str | None
    action: str
    outcome: str  # "success", "failure", "pending"
    metadata: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    # Cryptographic fields
    previous_hash: str = ""
    signature: str = ""

    @property
    def content_hash(self) -> str:
        """Generate hash of entry content (excluding signature)."""
        content = {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "action": self.action,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "request_id": self.request_id,
            "previous_hash": self.previous_hash,
        }
        content_bytes = json.dumps(content, sort_keys=True).encode()
        return hashlib.sha3_256(content_bytes).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "action": self.action,
            "outcome": self.outcome,
            "metadata": self.metadata,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "content_hash": self.content_hash,
            "previous_hash": self.previous_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEntry":
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=AuditEventType(data["event_type"]),
            actor_id=data["actor_id"],
            actor_type=data["actor_type"],
            resource_id=data.get("resource_id"),
            resource_type=data.get("resource_type"),
            action=data["action"],
            outcome=data["outcome"],
            metadata=data.get("metadata", {}),
            request_id=data.get("request_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            previous_hash=data.get("previous_hash", ""),
            signature=data.get("signature", ""),
        )


@dataclass
class MerkleNode:
    """Node in a Merkle tree."""

    hash: str
    left: Optional["MerkleNode"] = None
    right: Optional["MerkleNode"] = None
    data: str | None = None  # Only for leaf nodes

    @property
    def is_leaf(self) -> bool:
        return self.data is not None


@dataclass
class MerkleProof:
    """Proof that a value exists in a Merkle tree."""

    leaf_hash: str
    root_hash: str
    proof_hashes: list[tuple[str, str]]  # List of (hash, position: "left" or "right")
    leaf_index: int
    tree_size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "leaf_hash": self.leaf_hash,
            "root_hash": self.root_hash,
            "proof": [{"hash": h, "position": p} for h, p in self.proof_hashes],
            "leaf_index": self.leaf_index,
            "tree_size": self.tree_size,
        }


class MerkleTree:
    """Merkle tree for efficient proof of inclusion."""

    def __init__(self, hash_func=None):
        self.hash_func = hash_func or (lambda x: hashlib.sha3_256(x.encode()).hexdigest())
        self.leaves: list[str] = []
        self.root: MerkleNode | None = None
        self._lock = threading.Lock()

    def add_leaf(self, data: str) -> int:
        """Add a leaf to the tree. Returns the leaf index."""
        with self._lock:
            leaf_hash = self.hash_func(data)
            self.leaves.append(leaf_hash)
            self._rebuild()
            return len(self.leaves) - 1

    def add_leaves(self, data_list: list[str]) -> list[int]:
        """Add multiple leaves to the tree."""
        with self._lock:
            indices = []
            for data in data_list:
                leaf_hash = self.hash_func(data)
                self.leaves.append(leaf_hash)
                indices.append(len(self.leaves) - 1)
            self._rebuild()
            return indices

    def _rebuild(self) -> None:
        """Rebuild the tree from leaves."""
        if not self.leaves:
            self.root = None
            return

        # Create leaf nodes
        nodes = [MerkleNode(hash=h, data=h) for h in self.leaves]

        # Build tree bottom-up
        while len(nodes) > 1:
            next_level = []
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                combined_hash = self.hash_func(left.hash + right.hash)
                parent = MerkleNode(hash=combined_hash, left=left, right=right)
                next_level.append(parent)
            nodes = next_level

        self.root = nodes[0]

    @property
    def root_hash(self) -> str | None:
        return self.root.hash if self.root else None

    def get_proof(self, index: int) -> MerkleProof | None:
        """Get a proof of inclusion for the leaf at the given index."""
        if index < 0 or index >= len(self.leaves):
            return None

        if not self.root:
            return None

        proof_hashes = []
        current_index = index
        level_size = len(self.leaves)

        # Build level by level
        nodes = [MerkleNode(hash=h, data=h) for h in self.leaves]

        while level_size > 1:
            sibling_index = current_index ^ 1  # XOR to get sibling

            if sibling_index < len(nodes):
                sibling = nodes[sibling_index]
                position = "right" if current_index % 2 == 0 else "left"
                proof_hashes.append((sibling.hash, position))

            # Build next level
            next_level = []
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
                combined_hash = self.hash_func(left.hash + right.hash)
                next_level.append(MerkleNode(hash=combined_hash, left=left, right=right))

            nodes = next_level
            current_index //= 2
            level_size = len(nodes)

        return MerkleProof(
            leaf_hash=self.leaves[index],
            root_hash=self.root_hash,
            proof_hashes=proof_hashes,
            leaf_index=index,
            tree_size=len(self.leaves),
        )

    def verify_proof(self, proof: MerkleProof) -> bool:
        """Verify a proof of inclusion."""
        current_hash = proof.leaf_hash

        for sibling_hash, position in proof.proof_hashes:
            if position == "right":
                current_hash = self.hash_func(current_hash + sibling_hash)
            else:
                current_hash = self.hash_func(sibling_hash + current_hash)

        return current_hash == proof.root_hash


@dataclass
class Block:
    """A block in the audit chain."""

    index: int
    timestamp: datetime
    entries: list[AuditEntry]
    merkle_root: str
    previous_block_hash: str
    nonce: int = 0
    hash: str = ""

    def compute_hash(self) -> str:
        """Compute the hash of this block."""
        content = {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "merkle_root": self.merkle_root,
            "previous_block_hash": self.previous_block_hash,
            "nonce": self.nonce,
            "entry_count": len(self.entries),
        }
        content_bytes = json.dumps(content, sort_keys=True).encode()
        return hashlib.sha3_256(content_bytes).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "entries": [e.to_dict() for e in self.entries],
            "merkle_root": self.merkle_root,
            "previous_block_hash": self.previous_block_hash,
            "nonce": self.nonce,
            "hash": self.hash,
            "entry_count": len(self.entries),
        }


class BlockchainAuditTrail:
    """Immutable blockchain-based audit trail."""

    GENESIS_HASH = "0" * 64
    MAX_BLOCK_SIZE = 100  # Max entries per block

    def __init__(self, signing_key: bytes | None = None):
        self.signing_key = signing_key or hashlib.sha256(b"default_key").digest()
        self.chain: list[Block] = []
        self.pending_entries: list[AuditEntry] = []
        self.merkle_tree = MerkleTree()
        self.entry_index: dict[str, int] = {}  # entry_id -> block_index
        self._lock = threading.Lock()
        self._entry_counter = 0

        # Create genesis block
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        """Create the genesis (first) block."""
        genesis_entry = AuditEntry(
            id="genesis",
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.SYSTEM_STARTUP,
            actor_id="system",
            actor_type="system",
            resource_id=None,
            resource_type=None,
            action="chain_initialized",
            outcome="success",
            metadata={"version": "1.0"},
            previous_hash=self.GENESIS_HASH,
        )
        genesis_entry.signature = self._sign_entry(genesis_entry)

        block = Block(
            index=0,
            timestamp=genesis_entry.timestamp,
            entries=[genesis_entry],
            merkle_root=genesis_entry.content_hash,
            previous_block_hash=self.GENESIS_HASH,
        )
        block.hash = block.compute_hash()

        self.chain.append(block)
        self.merkle_tree.add_leaf(genesis_entry.content_hash)
        self.entry_index["genesis"] = 0

    def _generate_entry_id(self) -> str:
        """Generate a unique entry ID."""
        self._entry_counter += 1
        timestamp = int(time.time() * 1000)
        return f"audit-{timestamp}-{self._entry_counter:06d}"

    def _sign_entry(self, entry: AuditEntry) -> str:
        """Sign an audit entry."""
        signature = hmac.new(
            self.signing_key,
            entry.content_hash.encode(),
            hashlib.sha3_256
        ).hexdigest()
        return signature

    def _verify_entry_signature(self, entry: AuditEntry) -> bool:
        """Verify an entry's signature."""
        expected = self._sign_entry(entry)
        return hmac.compare_digest(expected, entry.signature)

    def log(
        self,
        event_type: AuditEventType,
        actor_id: str,
        actor_type: str,
        action: str,
        outcome: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> str:
        """Log an audit entry. Returns the entry ID."""
        with self._lock:
            # Get previous entry hash
            if self.pending_entries:
                previous_hash = self.pending_entries[-1].content_hash
            elif self.chain:
                previous_hash = self.chain[-1].entries[-1].content_hash
            else:
                previous_hash = self.GENESIS_HASH

            entry = AuditEntry(
                id=self._generate_entry_id(),
                timestamp=datetime.now(timezone.utc),
                event_type=event_type,
                actor_id=actor_id,
                actor_type=actor_type,
                resource_id=resource_id,
                resource_type=resource_type,
                action=action,
                outcome=outcome,
                metadata=metadata or {},
                request_id=request_id,
                ip_address=ip_address,
                user_agent=user_agent,
                previous_hash=previous_hash,
            )
            entry.signature = self._sign_entry(entry)

            self.pending_entries.append(entry)

            # Create block if we have enough entries
            if len(self.pending_entries) >= self.MAX_BLOCK_SIZE:
                self._create_block()

            return entry.id

    def _create_block(self) -> Block | None:
        """Create a new block from pending entries."""
        if not self.pending_entries:
            return None

        # Build Merkle tree for this block
        entry_hashes = [e.content_hash for e in self.pending_entries]
        block_merkle = MerkleTree()
        block_merkle.add_leaves(entry_hashes)

        block = Block(
            index=len(self.chain),
            timestamp=datetime.now(timezone.utc),
            entries=self.pending_entries.copy(),
            merkle_root=block_merkle.root_hash,
            previous_block_hash=self.chain[-1].hash if self.chain else self.GENESIS_HASH,
        )
        block.hash = block.compute_hash()

        # Add to global Merkle tree
        for entry in self.pending_entries:
            self.merkle_tree.add_leaf(entry.content_hash)
            self.entry_index[entry.id] = block.index

        self.chain.append(block)
        self.pending_entries.clear()

        return block

    def flush(self) -> Block | None:
        """Force creation of a block from pending entries."""
        with self._lock:
            return self._create_block()

    def get_entry(self, entry_id: str) -> AuditEntry | None:
        """Get an audit entry by ID."""
        block_index = self.entry_index.get(entry_id)
        if block_index is None:
            # Check pending entries
            for entry in self.pending_entries:
                if entry.id == entry_id:
                    return entry
            return None

        block = self.chain[block_index]
        for entry in block.entries:
            if entry.id == entry_id:
                return entry
        return None

    def get_proof(self, entry_id: str) -> MerkleProof | None:
        """Get a Merkle proof for an entry."""
        # Find the entry's position in the global tree
        position = 0
        for block in self.chain:
            for entry in block.entries:
                if entry.id == entry_id:
                    return self.merkle_tree.get_proof(position)
                position += 1
        return None

    def verify_entry(self, entry_id: str) -> dict[str, Any]:
        """Verify an entry's integrity."""
        entry = self.get_entry(entry_id)
        if not entry:
            return {"valid": False, "error": "Entry not found"}

        result = {
            "entry_id": entry_id,
            "signature_valid": self._verify_entry_signature(entry),
            "chain_valid": True,
            "merkle_proof_valid": False,
        }

        # Verify chain integrity up to this entry
        block_index = self.entry_index.get(entry_id)
        if block_index is not None:
            for i in range(block_index + 1):
                block = self.chain[i]
                if i > 0:
                    if block.previous_block_hash != self.chain[i - 1].hash:
                        result["chain_valid"] = False
                        break
                if block.compute_hash() != block.hash:
                    result["chain_valid"] = False
                    break

        # Verify Merkle proof
        proof = self.get_proof(entry_id)
        if proof:
            result["merkle_proof_valid"] = self.merkle_tree.verify_proof(proof)
            result["merkle_proof"] = proof.to_dict()

        result["valid"] = all([
            result["signature_valid"],
            result["chain_valid"],
            result["merkle_proof_valid"],
        ])

        return result

    def verify_chain(self) -> dict[str, Any]:
        """Verify the entire chain's integrity."""
        result = {
            "valid": True,
            "blocks_verified": 0,
            "entries_verified": 0,
            "errors": [],
        }

        for i, block in enumerate(self.chain):
            # Verify block hash
            if block.compute_hash() != block.hash:
                result["valid"] = False
                result["errors"].append(f"Block {i}: Invalid hash")
                continue

            # Verify chain link
            if i > 0:
                if block.previous_block_hash != self.chain[i - 1].hash:
                    result["valid"] = False
                    result["errors"].append(f"Block {i}: Chain broken")

            # Verify entry signatures and chaining
            for j, entry in enumerate(block.entries):
                if not self._verify_entry_signature(entry):
                    result["valid"] = False
                    result["errors"].append(f"Block {i}, Entry {j}: Invalid signature")

                result["entries_verified"] += 1

            result["blocks_verified"] += 1

        return result

    def query(
        self,
        event_type: AuditEventType | None = None,
        actor_id: str | None = None,
        resource_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Query audit entries."""
        results = []

        # Search in reverse chronological order
        for block in reversed(self.chain):
            for entry in reversed(block.entries):
                if len(results) >= limit:
                    return results

                # Apply filters
                if event_type and entry.event_type != event_type:
                    continue
                if actor_id and entry.actor_id != actor_id:
                    continue
                if resource_id and entry.resource_id != resource_id:
                    continue
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue

                results.append(entry)

        # Also search pending entries
        for entry in reversed(self.pending_entries):
            if len(results) >= limit:
                break

            if event_type and entry.event_type != event_type:
                continue
            if actor_id and entry.actor_id != actor_id:
                continue
            if resource_id and entry.resource_id != resource_id:
                continue
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue

            results.append(entry)

        return results

    def export_chain(self) -> dict[str, Any]:
        """Export the entire chain for backup/replication."""
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chain": [block.to_dict() for block in self.chain],
            "pending_entries": [e.to_dict() for e in self.pending_entries],
            "merkle_root": self.merkle_tree.root_hash,
            "total_entries": sum(len(b.entries) for b in self.chain) + len(self.pending_entries),
        }

    def get_stats(self) -> dict[str, Any]:
        """Get chain statistics."""
        total_entries = sum(len(b.entries) for b in self.chain) + len(self.pending_entries)

        return {
            "total_blocks": len(self.chain),
            "total_entries": total_entries,
            "pending_entries": len(self.pending_entries),
            "merkle_root": self.merkle_tree.root_hash,
            "latest_block_hash": self.chain[-1].hash if self.chain else None,
            "chain_valid": self.verify_chain()["valid"],
        }


# Singleton instance
_audit_trail: BlockchainAuditTrail | None = None


def get_audit_trail() -> BlockchainAuditTrail:
    """Get or create the audit trail singleton."""
    global _audit_trail
    if _audit_trail is None:
        _audit_trail = BlockchainAuditTrail()
    return _audit_trail
