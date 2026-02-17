"""
Agents API endpoints.

Provides CRUD operations for agent registrations.
"""
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.middleware.api_keys import require_api_key

router = APIRouter(prefix="/v1/agents", tags=["agents"])


class Agent(BaseModel):
    """Agent registration model."""
    id: str
    name: str
    description: Optional[str] = None
    status: str = "active"
    permissions: list[str] = []
    created_at: str


class AgentCreate(BaseModel):
    """Request body for creating an agent."""
    name: str
    description: Optional[str] = None
    permissions: list[str] = ["read", "write"]


class AgentList(BaseModel):
    """Response model for listing agents."""
    agents: list[Agent]
    total: int


# In-memory store for demo (replace with DB in production)
_agents: dict[str, Agent] = {}


@router.get("", response_model=AgentList)
async def list_agents(
    api_key: dict = Depends(require_api_key),
):
    """List all registered agents."""
    agents = list(_agents.values())
    return AgentList(agents=agents, total=len(agents))


@router.post("", response_model=Agent)
async def create_agent(
    body: AgentCreate,
    api_key: dict = Depends(require_api_key),
):
    """Register a new agent."""
    import uuid
    agent_id = str(uuid.uuid4())[:8]
    agent = Agent(
        id=agent_id,
        name=body.name,
        description=body.description,
        permissions=body.permissions,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _agents[agent_id] = agent
    return agent


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(
    agent_id: str,
    api_key: dict = Depends(require_api_key),
):
    """Get agent details by ID."""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agents[agent_id]


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: str,
    api_key: dict = Depends(require_api_key),
):
    """Deregister an agent."""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    del _agents[agent_id]
    return {"message": "Agent deleted"}
