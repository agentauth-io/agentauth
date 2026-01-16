"""
AgentAuth CrewAI Integration

Provides CrewAI tools for AI agents to make authorized purchases
with spending controls and human oversight.
"""
from typing import Optional, Any, Type

try:
    from crewai.tools import BaseTool as CrewBaseTool
    from pydantic import BaseModel, Field
    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False
    CrewBaseTool = object
    BaseModel = object
    Field = lambda *args, **kwargs: None

from agentauth.client import AgentAuth


class AuthorizedPurchaseInput(BaseModel if HAS_CREWAI else object):
    """Input schema for authorized purchase tool."""
    item_description: str = Field(
        description="Description of the item or service to purchase"
    )
    amount: float = Field(
        description="Amount in USD to spend"
    )
    merchant: str = Field(
        description="Merchant or store name"
    )
    category: Optional[str] = Field(
        default=None,
        description="Purchase category (e.g., 'ecommerce', 'saas', 'food')"
    )


class AuthorizedPurchaseCrewTool(CrewBaseTool if HAS_CREWAI else object):
    """
    CrewAI tool for making human-authorized purchases.
    
    This tool integrates with AgentAuth to ensure all AI agent purchases
    are pre-authorized by a human with spending limits and controls.
    
    Example:
        ```python
        from crewai import Agent, Task, Crew
        from agentauth.integrations.crewai import AuthorizedPurchaseCrewTool
        
        # Create tool
        purchase_tool = AuthorizedPurchaseCrewTool(
            delegation_token="token_from_user_consent",
            api_key="aa_live_xxx"
        )
        
        # Create agent with tool
        shopping_agent = Agent(
            role="Shopping Assistant",
            goal="Help users find and purchase items",
            tools=[purchase_tool]
        )
        ```
    """
    
    name: str = "Authorized Purchase Tool"
    description: str = """Make a purchase on behalf of the user.
This tool checks spending limits and rules before allowing purchases.
Use this for any transaction that requires spending money.
Inputs:
- item_description: What is being purchased
- amount: Price in USD
- merchant: Store/service name
- category (optional): Type of purchase"""
    
    args_schema: Type[BaseModel] = AuthorizedPurchaseInput
    
    # Configuration
    delegation_token: str = ""
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8000"
    agent_id: str = "crewai_agent"
    
    def __init__(
        self,
        delegation_token: str,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        agent_id: str = "crewai_agent",
        **kwargs
    ):
        """
        Initialize the authorized purchase tool.
        
        Args:
            delegation_token: Token from user consent (required)
            api_key: AgentAuth API key
            base_url: AgentAuth API URL
            agent_id: Identifier for this agent
        """
        super().__init__(**kwargs)
        self.delegation_token = delegation_token
        self.api_key = api_key
        self.base_url = base_url
        self.agent_id = agent_id
        self._client = AgentAuth(api_key=api_key, base_url=base_url)
    
    def _run(
        self,
        item_description: str,
        amount: float,
        merchant: str,
        category: Optional[str] = None,
    ) -> str:
        """Execute the authorized purchase."""
        try:
            # Request authorization
            auth = self._client.authorize(
                token=self.delegation_token,
                amount=amount,
                currency="USD",
                merchant_id=merchant.lower().replace(" ", "_"),
                merchant_name=merchant,
                merchant_category=category,
                raise_on_deny=False
            )
            
            if auth.allowed:
                return f"""PURCHASE AUTHORIZED ✅
Item: {item_description}
Amount: ${amount:.2f}
Merchant: {merchant}
Authorization Code: {auth.authorization_code}

Proceed with the transaction using authorization code: {auth.authorization_code}"""
            
            else:
                return f"""PURCHASE DENIED ❌
Item: {item_description}
Amount: ${amount:.2f}
Merchant: {merchant}
Reason: {auth.reason}

DO NOT proceed with this transaction. Consider alternatives or request higher limits."""
        
        except Exception as e:
            return f"""AUTHORIZATION ERROR ⚠️
Error: {str(e)}

DO NOT proceed with the purchase. Inform the user about this issue."""


class CheckLimitsCrewTool(CrewBaseTool if HAS_CREWAI else object):
    """
    CrewAI tool to check remaining spending budget.
    """
    
    name: str = "Check Spending Limits"
    description: str = """Check remaining spending budget and limits.
Use before making purchases to understand available budget.
No inputs required - just call this tool."""
    
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8000"
    user_id: str = "default"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        user_id: str = "default",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.user_id = user_id
    
    def _run(self) -> str:
        """Check and return spending limits."""
        import httpx
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Get limits
            limits_resp = httpx.get(
                f"{self.base_url}/v1/limits",
                params={"user_id": self.user_id},
                headers=headers
            )
            limits = limits_resp.json()
            
            # Get usage
            usage_resp = httpx.get(
                f"{self.base_url}/v1/limits/usage",
                params={"user_id": self.user_id},
                headers=headers
            )
            usage = usage_resp.json()
            
            return f"""SPENDING LIMITS 💰
Daily: ${usage.get('daily_remaining', '?')} remaining of ${limits.get('daily_limit', '?')}
Monthly: ${usage.get('monthly_remaining', '?')} remaining of ${limits.get('monthly_limit', '?')}
Per Transaction Max: ${limits.get('per_transaction_limit', '?')}
Transactions Today: {usage.get('daily_transaction_count', 0)}"""
        
        except Exception as e:
            return f"Could not fetch limits: {str(e)}"


def create_crewai_tools(
    delegation_token: str,
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    user_id: str = "default",
    agent_id: str = "crewai_agent",
) -> list:
    """
    Create AgentAuth CrewAI tools.
    
    Args:
        delegation_token: User consent token for this agent session
        api_key: AgentAuth API key
        base_url: AgentAuth API URL
        user_id: User ID for limits/rules
        agent_id: Identifier for this agent
        
    Returns:
        List of CrewAI tools
        
    Example:
        ```python
        from crewai import Agent, Task, Crew
        from agentauth.integrations.crewai import create_crewai_tools
        
        tools = create_crewai_tools(
            delegation_token="token_from_consent",
            api_key="aa_live_xxx"
        )
        
        agent = Agent(
            role="Shopping Assistant",
            goal="Help purchase items within budget",
            tools=tools
        )
        ```
    """
    if not HAS_CREWAI:
        raise ImportError(
            "CrewAI is not installed. Install with: pip install crewai"
        )
    
    return [
        AuthorizedPurchaseCrewTool(
            delegation_token=delegation_token,
            api_key=api_key,
            base_url=base_url,
            agent_id=agent_id
        ),
        CheckLimitsCrewTool(
            api_key=api_key,
            base_url=base_url,
            user_id=user_id
        )
    ]
