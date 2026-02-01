"""
AgentAuth Agent Registry
Manages registered agents with permissions and lifecycle
"""

import time
import secrets
import hashlib
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum


class AgentStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"


class AgentPermission(Enum):
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_WRITE = "transaction:write"
    POLICY_READ = "policy:read"
    POLICY_WRITE = "policy:write"
    AUDIT_READ = "audit:read"
    ADMIN = "admin"


@dataclass
class RegisteredAgent:
    """Registered agent with full metadata"""
    agent_id: str
    user_id: str
    name: str
    description: str
    api_key_hash: str
    permissions: List[AgentPermission]
    status: AgentStatus
    created_at: float
    updated_at: float
    last_seen: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    spending_limit_daily: float = 1000.0
    spending_limit_per_tx: float = 200.0
    allowed_merchants: Optional[List[str]] = None
    blocked_merchants: Optional[List[str]] = None


class AgentRegistry:
    """
    Central registry for managing AI agents
    Handles registration, authentication, and lifecycle
    """
    
    def __init__(self):
        self._agents: Dict[str, RegisteredAgent] = {}
        self._api_key_index: Dict[str, str] = {}  # hash -> agent_id
        self._user_agents: Dict[str, List[str]] = {}  # user_id -> [agent_ids]
    
    def register_agent(
        self,
        user_id: str,
        name: str,
        description: str = "",
        permissions: Optional[List[AgentPermission]] = None,
        spending_limit_daily: float = 1000.0,
        spending_limit_per_tx: float = 200.0,
        allowed_merchants: Optional[List[str]] = None,
        blocked_merchants: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> tuple[str, str]:
        """
        Register a new agent
        
        Returns:
            Tuple of (agent_id, api_key)
        """
        # Generate unique IDs
        agent_id = f"agent_{secrets.token_hex(8)}"
        api_key = f"aa_{secrets.token_urlsafe(32)}"
        api_key_hash = self._hash_api_key(api_key)
        
        now = time.time()
        
        agent = RegisteredAgent(
            agent_id=agent_id,
            user_id=user_id,
            name=name,
            description=description,
            api_key_hash=api_key_hash,
            permissions=permissions or [AgentPermission.TRANSACTION_WRITE],
            status=AgentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            spending_limit_daily=spending_limit_daily,
            spending_limit_per_tx=spending_limit_per_tx,
            allowed_merchants=allowed_merchants,
            blocked_merchants=blocked_merchants,
            metadata=metadata or {}
        )
        
        self._agents[agent_id] = agent
        self._api_key_index[api_key_hash] = agent_id
        
        if user_id not in self._user_agents:
            self._user_agents[user_id] = []
        self._user_agents[user_id].append(agent_id)
        
        return agent_id, api_key
    
    def authenticate_agent(self, api_key: str) -> Optional[RegisteredAgent]:
        """
        Authenticate agent by API key
        
        Returns:
            RegisteredAgent if valid, None otherwise
        """
        api_key_hash = self._hash_api_key(api_key)
        agent_id = self._api_key_index.get(api_key_hash)
        
        if not agent_id:
            return None
        
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        
        if agent.status != AgentStatus.ACTIVE:
            return None
        
        # Update last seen
        agent.last_seen = time.time()
        
        return agent
    
    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent by ID"""
        return self._agents.get(agent_id)
    
    def get_user_agents(self, user_id: str) -> List[RegisteredAgent]:
        """Get all agents for a user"""
        agent_ids = self._user_agents.get(user_id, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def update_agent(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[List[AgentPermission]] = None,
        spending_limit_daily: Optional[float] = None,
        spending_limit_per_tx: Optional[float] = None,
        allowed_merchants: Optional[List[str]] = None,
        blocked_merchants: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Update agent properties"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        if name is not None:
            agent.name = name
        if description is not None:
            agent.description = description
        if permissions is not None:
            agent.permissions = permissions
        if spending_limit_daily is not None:
            agent.spending_limit_daily = spending_limit_daily
        if spending_limit_per_tx is not None:
            agent.spending_limit_per_tx = spending_limit_per_tx
        if allowed_merchants is not None:
            agent.allowed_merchants = allowed_merchants
        if blocked_merchants is not None:
            agent.blocked_merchants = blocked_merchants
        if metadata is not None:
            agent.metadata.update(metadata)
        
        agent.updated_at = time.time()
        return True
    
    def suspend_agent(self, agent_id: str) -> bool:
        """Suspend an agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        agent.status = AgentStatus.SUSPENDED
        agent.updated_at = time.time()
        return True
    
    def activate_agent(self, agent_id: str) -> bool:
        """Activate a suspended agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        if agent.status == AgentStatus.REVOKED:
            return False  # Cannot reactivate revoked agents
        
        agent.status = AgentStatus.ACTIVE
        agent.updated_at = time.time()
        return True
    
    def revoke_agent(self, agent_id: str) -> bool:
        """Permanently revoke an agent"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        agent.status = AgentStatus.REVOKED
        agent.updated_at = time.time()
        
        # Remove from API key index
        if agent.api_key_hash in self._api_key_index:
            del self._api_key_index[agent.api_key_hash]
        
        return True
    
    def rotate_api_key(self, agent_id: str) -> Optional[str]:
        """
        Rotate API key for an agent
        
        Returns:
            New API key if successful, None otherwise
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        
        # Remove old key from index
        if agent.api_key_hash in self._api_key_index:
            del self._api_key_index[agent.api_key_hash]
        
        # Generate new key
        new_api_key = f"aa_{secrets.token_urlsafe(32)}"
        new_hash = self._hash_api_key(new_api_key)
        
        agent.api_key_hash = new_hash
        agent.updated_at = time.time()
        
        self._api_key_index[new_hash] = agent_id
        
        return new_api_key
    
    def has_permission(self, agent_id: str, permission: AgentPermission) -> bool:
        """Check if agent has a specific permission"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        if AgentPermission.ADMIN in agent.permissions:
            return True
        
        return permission in agent.permissions
    
    def check_merchant_allowed(self, agent_id: str, merchant: str) -> bool:
        """Check if agent is allowed to transact with merchant"""
        agent = self._agents.get(agent_id)
        if not agent:
            return False
        
        merchant_lower = merchant.lower()
        
        # Check blocklist first
        if agent.blocked_merchants:
            if merchant_lower in [m.lower() for m in agent.blocked_merchants]:
                return False
        
        # Check allowlist if set
        if agent.allowed_merchants:
            return merchant_lower in [m.lower() for m in agent.allowed_merchants]
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        status_counts = {}
        for agent in self._agents.values():
            status = agent.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_agents": len(self._agents),
            "total_users": len(self._user_agents),
            "status_counts": status_counts,
            "active_last_hour": sum(
                1 for a in self._agents.values()
                if a.last_seen and time.time() - a.last_seen < 3600
            )
        }
    
    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
