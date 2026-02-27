"""
Multi-Party Authorization Service

Supports hierarchical authorization flows:
- Family accounts (parent/child approvals)
- Business accounts (manager approval chains)
- Shared accounts (multi-user consensus)

Types:
1. PARENT_APPROVAL - Requires parent/guardian for minors
2. MANAGER_APPROVAL - Requires manager for business expenses
3. CONSENSUS - Requires multiple parties to approve
4. ESCROW - Funds held until conditions met
"""

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import get_settings

settings = get_settings()


class ApprovalType(Enum):
    """Type of multi-party approval required."""

    PARENT_APPROVAL = "parent_approval"  # Family/guardian
    MANAGER_APPROVAL = "manager_approval"  # Business hierarchy
    CONSENSUS = "consensus"  # Multiple required
    ESCROW = "escrow"  # Conditional hold


class ApprovalStatus(Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Request for multi-party approval."""

    request_id: str
    approval_type: ApprovalType

    # Requester info
    requester_id: str
    requester_type: str  # "child", "employee", "user"
    requester_name: str

    # Transaction details
    amount: float
    currency: str
    merchant_name: str
    description: str

    # Approval chain
    approvers: list[str]  # List of approver IDs required
    required_approvals: int = 1  # How many need to approve

    # Context
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400)  # 24h


@dataclass
class ApprovalResult:
    """Result of an approval request."""

    request_id: str
    status: ApprovalStatus

    # Approval details
    approvals_received: list[str] = field(default_factory=list)  # Who approved
    denials_received: list[str] = field(default_factory=list)  # Who denied

    # Decision
    decision: str  # "approved", "denied", "pending", "expired"
    reason: str = ""

    # Timing
    created_at: float = 0.0
    completed_at: float | None = None
    elapsed_seconds: float = 0.0


class MultiPartyAuthService:
    """
    Multi-party authorization service.

    Handles:
    - Parent approval for family accounts
    - Manager approval for business expenses
    - Consensus for shared accounts
    - Escrow for conditional payments
    """

    def __init__(self):
        # In-memory storage for approval requests
        self._approval_requests: dict[str, ApprovalRequest] = {}
        self._approval_results: dict[str, ApprovalResult] = {}

        # Approval chains (business hierarchy)
        self._approval_chains: dict[str, list[str]] = {}  # user_id -> [approver_ids]

        # Statistics
        self._stats = {
            "total_requests": 0,
            "approved": 0,
            "denied": 0,
            "pending": 0,
            "expired": 0,
        }

    # ==================== Configuration ====================

    def set_approval_chain(self, user_id: str, approver_ids: list[str]):
        """Set approval chain for a user (business hierarchy)."""
        self._approval_chains[user_id] = approver_ids

    def get_approval_chain(self, user_id: str) -> list[str]:
        """Get approval chain for a user."""
        return self._approval_chains.get(user_id, [])

    # ==================== Create Approval Request ====================

    def create_approval_request(
        self,
        approval_type: ApprovalType,
        requester_id: str,
        requester_type: str,
        requester_name: str,
        amount: float,
        currency: str,
        merchant_name: str,
        description: str,
        approvers: list[str] | None = None,
        required_approvals: int = 1,
        metadata: dict | None = None,
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Returns:
            ApprovalRequest with request_id
        """
        # Generate request ID
        request_id = self._generate_request_id(requester_id, amount, merchant_name)

        # Determine approvers based on type
        if approvers is None:
            approvers = self._get_default_approvers(approval_type, requester_id)

        request = ApprovalRequest(
            request_id=request_id,
            approval_type=approval_type,
            requester_id=requester_id,
            requester_type=requester_type,
            requester_name=requester_name,
            amount=amount,
            currency=currency,
            merchant_name=merchant_name,
            description=description,
            approvers=approvers,
            required_approvals=required_approvals,
            metadata=metadata or {},
        )

        # Store request
        self._approval_requests[request_id] = request

        # Initialize result
        self._approval_results[request_id] = ApprovalResult(
            request_id=request_id,
            status=ApprovalStatus.PENDING,
            decision="pending",
            created_at=request.created_at,
        )

        self._stats["total_requests"] += 1
        self._stats["pending"] += 1

        return request

    def _generate_request_id(
        self, requester_id: str, amount: float, merchant: str
    ) -> str:
        """Generate unique request ID."""
        data = f"{requester_id}:{amount}:{merchant}:{time.time()}"
        hash_val = hashlib.sha256(data.encode()).hexdigest()[:16]
        return f"apr_{hash_val}"

    def _get_default_approvers(
        self, approval_type: ApprovalType, requester_id: str
    ) -> list[str]:
        """Get default approvers based on type."""
        if approval_type == ApprovalType.PARENT_APPROVAL:
            # Parent approval - look up in user metadata
            return [f"parent_{requester_id}"]

        elif approval_type == ApprovalType.MANAGER_APPROVAL:
            # Manager approval - use approval chain
            return self._approval_chains.get(requester_id, [])

        elif approval_type == ApprovalType.CONSENSUS:
            # Consensus - all account members
            return [f"member_{requester_id}"]

        elif approval_type == ApprovalType.ESCROW:
            # Escrow - neutral third party or system
            return ["escrow_service"]

        return []

    # ==================== Process Approval ====================

    def approve(
        self,
        request_id: str,
        approver_id: str,
        reason: str = "",
    ) -> ApprovalResult:
        """
        Process an approval from an approver.

        Returns:
            ApprovalResult with updated status
        """
        # Get request
        request = self._approval_requests.get(request_id)
        if not request:
            return ApprovalResult(
                request_id=request_id,
                status=ApprovalStatus.EXPIRED,
                decision="expired",
                reason="Request not found",
            )

        # Check if expired
        if time.time() > request.expires_at:
            self._expire_request(request_id)
            return self._approval_results[request_id]

        # Check if approver is valid
        if approver_id not in request.approvers:
            return self._approval_results[request_id]

        # Check if already responded
        result = self._approval_results[request_id]
        if (
            approver_id in result.approvals_received
            or approver_id in result.denials_received
        ):
            return result  # Already processed

        # Record approval
        result.approvals_received.append(approver_id)

        # Check if required approvals met
        if len(result.approvals_received) >= request.required_approvals:
            result.status = ApprovalStatus.APPROVED
            result.decision = "approved"
            result.completed_at = time.time()
            result.elapsed_seconds = result.completed_at - result.created_at
            self._stats["pending"] -= 1
            self._stats["approved"] += 1

        return result

    def deny(
        self,
        request_id: str,
        approver_id: str,
        reason: str = "",
    ) -> ApprovalResult:
        """
        Process a denial from an approver.

        Returns:
            ApprovalResult with updated status
        """
        # Get request
        request = self._approval_requests.get(request_id)
        if not request:
            return ApprovalResult(
                request_id=request_id,
                status=ApprovalStatus.EXPIRED,
                decision="expired",
                reason="Request not found",
            )

        # Check if expired
        if time.time() > request.expires_at:
            self._expire_request(request_id)
            return self._approval_results[request_id]

        # Check if approver is valid
        if approver_id not in request.approvers:
            return self._approval_results[request_id]

        # Record denial
        result = self._approval_results[request_id]
        result.denials_received.append(approver_id)

        # Any denial = denied (for simple cases)
        if request.required_approvals == 1:
            result.status = ApprovalStatus.DENIED
            result.decision = "denied"
            result.reason = reason
            result.completed_at = time.time()
            result.elapsed_seconds = result.completed_at - result.created_at
            self._stats["pending"] -= 1
            self._stats["denied"] += 1

        return result

    def _expire_request(self, request_id: str):
        """Mark a request as expired."""
        if request_id in self._approval_results:
            result = self._approval_results[request_id]
            result.status = ApprovalStatus.EXPIRED
            result.decision = "expired"
            result.completed_at = time.time()
            result.elapsed_seconds = result.completed_at - result.created_at
            self._stats["pending"] -= 1
            self._stats["expired"] += 1

    # ==================== Query ====================

    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Get approval request by ID."""
        return self._approval_requests.get(request_id)

    def get_result(self, request_id: str) -> ApprovalResult | None:
        """Get approval result by ID."""
        return self._approval_results.get(request_id)

    def get_pending_for_approver(self, approver_id: str) -> list[ApprovalRequest]:
        """Get all pending requests for an approver."""
        pending = []
        for request_id, request in self._approval_requests.items():
            result = self._approval_results.get(request_id)
            if result and result.status == ApprovalStatus.PENDING:
                if approver_id in request.approvers:
                    if approver_id not in result.approvals_received:
                        if approver_id not in result.denials_received:
                            pending.append(request)
        return pending

    def get_pending_for_requester(self, requester_id: str) -> list[ApprovalRequest]:
        """Get all pending requests from a requester."""
        pending = []
        for request in self._approval_requests.values():
            if request.requester_id == requester_id:
                result = self._approval_results.get(request.request_id)
                if result and result.status == ApprovalStatus.PENDING:
                    pending.append(request)
        return pending

    # ==================== Business Logic ====================

    def requires_approval(
        self,
        amount: float,
        user_age: int | None = None,
        user_role: str = "user",
        category: str = "",
    ) -> tuple[bool, ApprovalType | None]:
        """
        Determine if a transaction requires multi-party approval.

        Returns:
            (requires_approval, approval_type)
        """
        # Age-based (family accounts)
        if user_age is not None and user_age < 18:
            # Minor - check amount thresholds
            if amount > 50:  # Over $50 needs parent
                return (True, ApprovalType.PARENT_APPROVAL)

        # Role-based (business accounts)
        if user_role == "employee":
            # Employee expenses over $100 need manager
            if amount > 100:
                return (True, ApprovalType.MANAGER_APPROVAL)

        # Category-based
        high_risk_categories = {"electronics", "jewelry", "gift_cards", "crypto"}
        if category.lower() in high_risk_categories and amount > 200:
            return (True, ApprovalType.MANAGER_APPROVAL)

        # Amount threshold for consensus
        if amount > 1000:
            return (True, ApprovalType.CONSENSUS)

        return (False, None)

    # ==================== Statistics ====================

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self._stats,
            "pending_requests": len(
                [
                    r
                    for r in self._approval_results.values()
                    if r.status == ApprovalStatus.PENDING
                ]
            ),
        }


# Singleton instance
_multi_party_service: MultiPartyAuthService | None = None


def get_multi_party_service() -> MultiPartyAuthService:
    """Get singleton multi-party auth service."""
    global _multi_party_service
    if _multi_party_service is None:
        _multi_party_service = MultiPartyAuthService()
    return _multi_party_service


# Convenience functions
def create_approval(
    approval_type: ApprovalType,
    requester_id: str,
    amount: float,
    merchant: str,
    **kwargs,
) -> ApprovalRequest:
    """Create an approval request."""
    service = get_multi_party_service()
    return service.create_approval_request(
        approval_type=approval_type,
        requester_id=requester_id,
        amount=amount,
        merchant_name=merchant,
        **kwargs,
    )


def approve_request(request_id: str, approver_id: str) -> ApprovalResult:
    """Approve a request."""
    service = get_multi_party_service()
    return service.approve(request_id, approver_id)


def get_pending_approvals(approver_id: str) -> list[ApprovalRequest]:
    """Get pending approvals for an approver."""
    service = get_multi_party_service()
    return service.get_pending_for_approver(approver_id)
