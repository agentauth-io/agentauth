"""
Distributed Consensus Layer for AgentAuth
==========================================

Implements Byzantine Fault Tolerant (BFT) consensus for:
- Multi-node authorization decisions
- Distributed key management
- High-availability deployments
- Cross-region consensus

Based on simplified PBFT (Practical Byzantine Fault Tolerance).
"""

import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Types of consensus messages."""

    # PBFT phases
    REQUEST = "request"
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    REPLY = "reply"

    # View change
    VIEW_CHANGE = "view_change"
    NEW_VIEW = "new_view"

    # Cluster management
    HEARTBEAT = "heartbeat"
    JOIN = "join"
    LEAVE = "leave"
    STATE_SYNC = "state_sync"


class ConsensusState(str, Enum):
    """State of a consensus operation."""

    PENDING = "pending"
    PRE_PREPARED = "pre_prepared"
    PREPARED = "prepared"
    COMMITTED = "committed"
    EXECUTED = "executed"
    FAILED = "failed"


@dataclass
class ConsensusMessage:
    """A message in the consensus protocol."""

    msg_type: MessageType
    view_number: int
    sequence_number: int
    node_id: str
    digest: str
    payload: dict[str, Any]
    timestamp: float
    signature: str = ""

    def to_bytes(self) -> bytes:
        """Serialize for signing/hashing."""
        content = {
            "msg_type": self.msg_type.value,
            "view_number": self.view_number,
            "sequence_number": self.sequence_number,
            "node_id": self.node_id,
            "digest": self.digest,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
        return json.dumps(content, sort_keys=True).encode()

    def compute_hash(self) -> str:
        return hashlib.sha256(self.to_bytes()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "msg_type": self.msg_type.value,
            "view_number": self.view_number,
            "sequence_number": self.sequence_number,
            "node_id": self.node_id,
            "digest": self.digest,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConsensusMessage":
        return cls(
            msg_type=MessageType(data["msg_type"]),
            view_number=data["view_number"],
            sequence_number=data["sequence_number"],
            node_id=data["node_id"],
            digest=data["digest"],
            payload=data["payload"],
            timestamp=data["timestamp"],
            signature=data.get("signature", ""),
        )


@dataclass
class ConsensusRequest:
    """A request to be processed by consensus."""

    request_id: str
    operation: str
    data: dict[str, Any]
    client_id: str
    timestamp: float

    def compute_digest(self) -> str:
        content = json.dumps({
            "request_id": self.request_id,
            "operation": self.operation,
            "data": self.data,
            "client_id": self.client_id,
            "timestamp": self.timestamp,
        }, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()


@dataclass
class ConsensusResult:
    """Result of a consensus operation."""

    request_id: str
    success: bool
    result: Any
    consensus_nodes: list[str]
    view_number: int
    sequence_number: int
    execution_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "consensus_nodes": self.consensus_nodes,
            "view_number": self.view_number,
            "sequence_number": self.sequence_number,
            "execution_time_ms": self.execution_time_ms,
        }


class ConsensusLog:
    """Log of consensus decisions."""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.log: dict[int, dict[str, Any]] = {}  # seq_num -> entry
        self._lock = threading.Lock()

    def append(
        self,
        sequence_number: int,
        request: ConsensusRequest,
        state: ConsensusState,
        messages: dict[MessageType, list[ConsensusMessage]],
    ) -> None:
        with self._lock:
            self.log[sequence_number] = {
                "request": request,
                "state": state,
                "messages": messages,
                "timestamp": time.time(),
            }

            # Cleanup old entries
            if len(self.log) > self.max_size:
                oldest = min(self.log.keys())
                del self.log[oldest]

    def get(self, sequence_number: int) -> dict[str, Any] | None:
        return self.log.get(sequence_number)

    def get_state(self, sequence_number: int) -> ConsensusState | None:
        entry = self.log.get(sequence_number)
        return entry["state"] if entry else None

    def update_state(self, sequence_number: int, state: ConsensusState) -> None:
        with self._lock:
            if sequence_number in self.log:
                self.log[sequence_number]["state"] = state


@dataclass
class NodeInfo:
    """Information about a consensus node."""

    node_id: str
    address: str
    port: int
    public_key: bytes
    is_leader: bool = False
    last_heartbeat: float = 0.0
    sequence_number: int = 0

    @property
    def is_alive(self) -> bool:
        return time.time() - self.last_heartbeat < 30.0


class ConsensusNode:
    """A node participating in consensus."""

    def __init__(
        self,
        node_id: str,
        private_key: bytes | None = None,
        on_execute: Callable[[ConsensusRequest], Any] | None = None,
    ):
        self.node_id = node_id
        self.private_key = private_key or secrets.token_bytes(32)
        self.public_key = hashlib.sha256(self.private_key).digest()

        # Cluster state
        self.nodes: dict[str, NodeInfo] = {}
        self.view_number = 0
        self.sequence_number = 0
        self.is_leader = False

        # Message log
        self.log = ConsensusLog()
        self.pending_requests: dict[str, ConsensusRequest] = {}

        # Message tracking
        self.pre_prepares: dict[int, ConsensusMessage] = {}
        self.prepares: dict[int, list[ConsensusMessage]] = defaultdict(list)
        self.commits: dict[int, list[ConsensusMessage]] = defaultdict(list)

        # Callbacks
        self.on_execute = on_execute or (lambda r: {"status": "executed"})
        self.message_handlers: dict[MessageType, Callable] = {
            MessageType.REQUEST: self._handle_request,
            MessageType.PRE_PREPARE: self._handle_pre_prepare,
            MessageType.PREPARE: self._handle_prepare,
            MessageType.COMMIT: self._handle_commit,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }

        # Message queue for simulation
        self._message_queue: list[tuple[str, ConsensusMessage]] = []
        self._results: dict[str, ConsensusResult] = {}
        self._lock = threading.Lock()

        # Register self
        self.nodes[node_id] = NodeInfo(
            node_id=node_id,
            address="localhost",
            port=8000,
            public_key=self.public_key,
            is_leader=False,
            last_heartbeat=time.time(),
        )

    def sign_message(self, msg: ConsensusMessage) -> str:
        """Sign a message."""
        data = msg.to_bytes()
        signature = hmac.new(self.private_key, data, hashlib.sha256).hexdigest()
        return signature

    def verify_signature(self, msg: ConsensusMessage, sender_key: bytes) -> bool:
        """Verify a message signature."""
        data = msg.to_bytes()
        expected = hmac.new(sender_key, data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, msg.signature)

    @property
    def quorum_size(self) -> int:
        """Calculate quorum size (2f + 1 for 3f + 1 nodes)."""
        n = len(self.nodes)
        f = (n - 1) // 3
        return 2 * f + 1

    @property
    def leader_id(self) -> str:
        """Get current leader based on view number."""
        node_ids = sorted(self.nodes.keys())
        if not node_ids:
            return self.node_id
        return node_ids[self.view_number % len(node_ids)]

    def join_cluster(self, existing_node_id: str, address: str, port: int) -> None:
        """Join an existing cluster."""
        # In real implementation, this would send a JOIN message
        pass

    def add_node(self, node_id: str, address: str, port: int, public_key: bytes) -> None:
        """Add a new node to the cluster."""
        self.nodes[node_id] = NodeInfo(
            node_id=node_id,
            address=address,
            port=port,
            public_key=public_key,
            last_heartbeat=time.time(),
        )

        # Update leadership
        self._update_leadership()

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the cluster."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self._update_leadership()
            return True
        return False

    def _update_leadership(self) -> None:
        """Update leader status."""
        self.is_leader = self.node_id == self.leader_id
        for node in self.nodes.values():
            node.is_leader = node.node_id == self.leader_id

    def submit_request(self, request: ConsensusRequest) -> str:
        """Submit a request for consensus."""
        with self._lock:
            self.pending_requests[request.request_id] = request

            if self.is_leader:
                # Leader initiates consensus
                self._initiate_consensus(request)
            else:
                # Forward to leader
                self._send_to_leader(request)

            return request.request_id

    def _initiate_consensus(self, request: ConsensusRequest) -> None:
        """Leader initiates consensus for a request."""
        self.sequence_number += 1
        seq = self.sequence_number
        digest = request.compute_digest()

        # Create pre-prepare message
        msg = ConsensusMessage(
            msg_type=MessageType.PRE_PREPARE,
            view_number=self.view_number,
            sequence_number=seq,
            node_id=self.node_id,
            digest=digest,
            payload={"request": request.__dict__},
            timestamp=time.time(),
        )
        msg.signature = self.sign_message(msg)

        self.pre_prepares[seq] = msg
        self._broadcast(msg)

        # Leader also prepares
        self._send_prepare(seq, digest)

    def _send_to_leader(self, request: ConsensusRequest) -> None:
        """Send request to leader."""
        msg = ConsensusMessage(
            msg_type=MessageType.REQUEST,
            view_number=self.view_number,
            sequence_number=0,
            node_id=self.node_id,
            digest=request.compute_digest(),
            payload={"request": request.__dict__},
            timestamp=time.time(),
        )
        msg.signature = self.sign_message(msg)

        # In real implementation, send to leader
        self._message_queue.append((self.leader_id, msg))

    def receive_message(self, msg: ConsensusMessage) -> None:
        """Process a received message."""
        handler = self.message_handlers.get(msg.msg_type)
        if handler:
            handler(msg)

    def _handle_request(self, msg: ConsensusMessage) -> None:
        """Handle a REQUEST message (leader only)."""
        if not self.is_leader:
            return

        request_data = msg.payload.get("request", {})
        request = ConsensusRequest(**request_data)
        self.pending_requests[request.request_id] = request
        self._initiate_consensus(request)

    def _handle_pre_prepare(self, msg: ConsensusMessage) -> None:
        """Handle a PRE-PREPARE message."""
        seq = msg.sequence_number

        # Verify message is from leader
        if msg.node_id != self.leader_id:
            return

        # Verify we haven't accepted a different pre-prepare for this seq
        if seq in self.pre_prepares:
            if self.pre_prepares[seq].digest != msg.digest:
                return  # Conflicting pre-prepare

        self.pre_prepares[seq] = msg

        # Extract request
        request_data = msg.payload.get("request", {})
        request = ConsensusRequest(**request_data)
        self.pending_requests[request.request_id] = request

        # Send prepare
        self._send_prepare(seq, msg.digest)

    def _send_prepare(self, seq: int, digest: str) -> None:
        """Send a PREPARE message."""
        msg = ConsensusMessage(
            msg_type=MessageType.PREPARE,
            view_number=self.view_number,
            sequence_number=seq,
            node_id=self.node_id,
            digest=digest,
            payload={},
            timestamp=time.time(),
        )
        msg.signature = self.sign_message(msg)

        self.prepares[seq].append(msg)
        self._broadcast(msg)

        # Check if we have enough prepares
        self._check_prepared(seq)

    def _handle_prepare(self, msg: ConsensusMessage) -> None:
        """Handle a PREPARE message."""
        seq = msg.sequence_number

        # Verify we have a matching pre-prepare
        if seq not in self.pre_prepares:
            return
        if self.pre_prepares[seq].digest != msg.digest:
            return

        # Add to prepares
        self.prepares[seq].append(msg)

        # Check if we have enough prepares
        self._check_prepared(seq)

    def _check_prepared(self, seq: int) -> None:
        """Check if we have enough prepares to move to commit phase."""
        if len(self.prepares[seq]) >= self.quorum_size:
            # Already sent commit?
            for commit in self.commits[seq]:
                if commit.node_id == self.node_id:
                    return

            self._send_commit(seq, self.pre_prepares[seq].digest)

    def _send_commit(self, seq: int, digest: str) -> None:
        """Send a COMMIT message."""
        msg = ConsensusMessage(
            msg_type=MessageType.COMMIT,
            view_number=self.view_number,
            sequence_number=seq,
            node_id=self.node_id,
            digest=digest,
            payload={},
            timestamp=time.time(),
        )
        msg.signature = self.sign_message(msg)

        self.commits[seq].append(msg)
        self._broadcast(msg)

        # Check if we have enough commits
        self._check_committed(seq)

    def _handle_commit(self, msg: ConsensusMessage) -> None:
        """Handle a COMMIT message."""
        seq = msg.sequence_number

        # Verify we're prepared
        if len(self.prepares[seq]) < self.quorum_size:
            return

        # Add to commits
        self.commits[seq].append(msg)

        # Check if we have enough commits
        self._check_committed(seq)

    def _check_committed(self, seq: int) -> None:
        """Check if we have enough commits to execute."""
        if len(self.commits[seq]) >= self.quorum_size:
            self._execute(seq)

    def _execute(self, seq: int) -> None:
        """Execute a committed request."""
        pre_prepare = self.pre_prepares.get(seq)
        if not pre_prepare:
            return

        request_data = pre_prepare.payload.get("request", {})
        request = ConsensusRequest(**request_data)

        # Check if already executed
        if request.request_id in self._results:
            return

        start_time = time.time()

        # Execute the operation
        try:
            result = self.on_execute(request)
            success = True
        except Exception as e:
            result = {"error": str(e)}
            success = False

        execution_time = (time.time() - start_time) * 1000

        # Store result
        consensus_nodes = [msg.node_id for msg in self.commits[seq]]

        self._results[request.request_id] = ConsensusResult(
            request_id=request.request_id,
            success=success,
            result=result,
            consensus_nodes=consensus_nodes,
            view_number=self.view_number,
            sequence_number=seq,
            execution_time_ms=execution_time,
        )

        # Update log
        self.log.append(
            seq,
            request,
            ConsensusState.EXECUTED,
            {
                MessageType.PRE_PREPARE: [pre_prepare],
                MessageType.PREPARE: self.prepares[seq],
                MessageType.COMMIT: self.commits[seq],
            },
        )

        # Cleanup pending
        if request.request_id in self.pending_requests:
            del self.pending_requests[request.request_id]

    def _handle_heartbeat(self, msg: ConsensusMessage) -> None:
        """Handle a HEARTBEAT message."""
        node = self.nodes.get(msg.node_id)
        if node:
            node.last_heartbeat = time.time()
            node.sequence_number = msg.sequence_number

    def send_heartbeat(self) -> None:
        """Send heartbeat to cluster."""
        msg = ConsensusMessage(
            msg_type=MessageType.HEARTBEAT,
            view_number=self.view_number,
            sequence_number=self.sequence_number,
            node_id=self.node_id,
            digest="",
            payload={"leader_id": self.leader_id},
            timestamp=time.time(),
        )
        msg.signature = self.sign_message(msg)
        self._broadcast(msg)

    def _broadcast(self, msg: ConsensusMessage) -> None:
        """Broadcast a message to all nodes."""
        for node_id in self.nodes:
            if node_id != self.node_id:
                self._message_queue.append((node_id, msg))

    def get_result(self, request_id: str) -> ConsensusResult | None:
        """Get the result of a consensus request."""
        return self._results.get(request_id)

    def get_status(self) -> dict[str, Any]:
        """Get node status."""
        return {
            "node_id": self.node_id,
            "is_leader": self.is_leader,
            "leader_id": self.leader_id,
            "view_number": self.view_number,
            "sequence_number": self.sequence_number,
            "cluster_size": len(self.nodes),
            "quorum_size": self.quorum_size,
            "pending_requests": len(self.pending_requests),
            "completed_requests": len(self._results),
            "nodes": [
                {
                    "id": n.node_id,
                    "is_leader": n.is_leader,
                    "is_alive": n.is_alive,
                    "sequence": n.sequence_number,
                }
                for n in self.nodes.values()
            ],
        }


class ConsensusCluster:
    """Manages a cluster of consensus nodes for testing/simulation."""

    def __init__(self, node_count: int = 4):
        self.nodes: dict[str, ConsensusNode] = {}
        self._execution_handler = lambda r: {"status": "executed", "request_id": r.request_id}

        # Create nodes
        for i in range(node_count):
            node_id = f"node-{i}"
            node = ConsensusNode(node_id, on_execute=self._execution_handler)
            self.nodes[node_id] = node

        # Connect all nodes
        for node in self.nodes.values():
            for other in self.nodes.values():
                if node.node_id != other.node_id:
                    node.add_node(
                        other.node_id,
                        "localhost",
                        8000 + int(other.node_id.split("-")[1]),
                        other.public_key,
                    )

    def set_execution_handler(self, handler: Callable[[ConsensusRequest], Any]) -> None:
        """Set the execution handler for all nodes."""
        self._execution_handler = handler
        for node in self.nodes.values():
            node.on_execute = handler

    def submit_request(
        self,
        operation: str,
        data: dict[str, Any],
        client_id: str = "client-1",
    ) -> str:
        """Submit a request through any node."""
        request = ConsensusRequest(
            request_id=f"req-{secrets.token_hex(8)}",
            operation=operation,
            data=data,
            client_id=client_id,
            timestamp=time.time(),
        )

        # Submit to leader
        leader_id = next(iter(self.nodes.values())).leader_id
        leader = self.nodes.get(leader_id)

        if leader:
            leader.submit_request(request)

            # Simulate message passing
            self._process_messages()

            return request.request_id

        return ""

    def _process_messages(self, max_rounds: int = 10) -> None:
        """Simulate message passing between nodes."""
        for _ in range(max_rounds):
            all_messages = []

            # Collect all pending messages
            for node in self.nodes.values():
                while node._message_queue:
                    dest, msg = node._message_queue.pop(0)
                    all_messages.append((dest, msg))

            if not all_messages:
                break

            # Deliver messages
            for dest, msg in all_messages:
                if dest in self.nodes:
                    self.nodes[dest].receive_message(msg)

    def get_result(self, request_id: str) -> ConsensusResult | None:
        """Get result from any node."""
        for node in self.nodes.values():
            result = node.get_result(request_id)
            if result:
                return result
        return None

    def get_status(self) -> dict[str, Any]:
        """Get cluster status."""
        return {
            "nodes": {
                node_id: node.get_status()
                for node_id, node in self.nodes.items()
            },
            "leader_id": next(iter(self.nodes.values())).leader_id if self.nodes else None,
        }


# Singleton cluster instance
_cluster: ConsensusCluster | None = None


def get_consensus_cluster(node_count: int = 4) -> ConsensusCluster:
    """Get or create the consensus cluster singleton."""
    global _cluster
    if _cluster is None:
        _cluster = ConsensusCluster(node_count)
    return _cluster
