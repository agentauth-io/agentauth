"""
AgentAuth LangChain Integration

Provides LangChain tools for AI agents to make authorized purchases
with spending controls and human oversight.
"""
from typing import Optional, Type, Any
from pydantic import BaseModel, Field

try:
    from langchain_core.tools import BaseTool
    from langchain_core.callbacks import CallbackManagerForToolRun
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    BaseTool = object
    CallbackManagerForToolRun = None

from agentauth.client import AgentAuth


class AuthorizedPurchaseInput(BaseModel):
    """Input schema for authorized purchase tool."""
    item_description: str = Field(
        description="Description of the item or service to purchase"
    )
    amount: float = Field(
        description="Amount in USD to spend", 
        gt=0
    )
    merchant: str = Field(
        description="Merchant or store name (e.g., 'Amazon', 'Stripe', 'DoorDash')"
    )
    category: Optional[str] = Field(
        default=None,
        description="Purchase category (e.g., 'ecommerce', 'saas', 'food')"
    )


class AuthorizedPurchaseTool(BaseTool if HAS_LANGCHAIN else object):
    """
    LangChain tool for making human-authorized purchases.
    
    This tool integrates with AgentAuth to ensure all AI agent purchases
    are pre-authorized by a human with spending limits and controls.
    
    Example:
        ```python
        from langchain.agents import AgentExecutor
        from agentauth.integrations.langchain import AuthorizedPurchaseTool
        
        # Create tool with user's delegation token
        purchase_tool = AuthorizedPurchaseTool(
            delegation_token="token_from_user_consent",
            api_key="aa_live_xxx"
        )
        
        # Add to agent
        agent = AgentExecutor(
            agent=...,
            tools=[purchase_tool, ...]
        )
        ```
    """
    
    name: str = "authorized_purchase"
    description: str = """Make a purchase on behalf of the user.
This tool checks spending limits and rules before allowing purchases.
Use this for any transaction that requires spending money.
Required inputs: item_description, amount, merchant.
Optional: category (helps with spending categorization)."""
    
    args_schema: Type[BaseModel] = AuthorizedPurchaseInput
    
    # Configuration
    api_key: Optional[str] = None
    base_url: str = "http://localhost:8000"
    delegation_token: str = ""
    agent_id: str = "langchain_agent"
    
    # Internal client
    _client: Optional[AgentAuth] = None
    
    def __init__(
        self,
        delegation_token: str,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost:8000",
        agent_id: str = "langchain_agent",
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
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        Execute the authorized purchase.
        
        Returns a string describing the result for the LLM to understand.
        """
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
                return f"""✅ PURCHASE AUTHORIZED

Item: {item_description}
Amount: ${amount:.2f}
Merchant: {merchant}
Authorization Code: {auth.authorization_code}

The purchase has been authorized. You may proceed with the transaction.
Provide this authorization code to the merchant: {auth.authorization_code}"""
            
            else:
                return f"""❌ PURCHASE DENIED

Item: {item_description}
Amount: ${amount:.2f}
Merchant: {merchant}
Reason: {auth.reason}
Details: {auth.message or 'No additional details'}

The purchase was NOT authorized. Do NOT proceed with this transaction.
You may want to:
1. Try a lower amount
2. Choose a different merchant
3. Ask the user for additional authorization"""
        
        except Exception as e:
            return f"""⚠️ AUTHORIZATION ERROR

Failed to check authorization: {str(e)}

Do NOT proceed with the purchase. The authorization system may be unavailable.
Inform the user about this issue."""
    
    async def _arun(
        self,
        item_description: str,
        amount: float,
        merchant: str,
        category: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Async version - delegates to sync for now."""
        return self._run(item_description, amount, merchant, category, run_manager)


class CheckSpendingLimitsInput(BaseModel):
    """Input for checking spending limits."""
    pass  # No inputs needed


class CheckSpendingLimitsTool(BaseTool if HAS_LANGCHAIN else object):
    """
    LangChain tool to check remaining spending budget.
    
    Useful before attempting purchases to understand available budget.
    """
    
    name: str = "check_spending_limits"
    description: str = """Check the remaining spending budget.
Use this before making purchases to understand how much can be spent.
No inputs required."""
    
    args_schema: Type[BaseModel] = CheckSpendingLimitsInput
    
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
    
    def _run(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Check and return spending limits."""
        import httpx
        
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            # Get limits
            limits_response = httpx.get(
                f"{self.base_url}/v1/limits",
                params={"user_id": self.user_id},
                headers=headers
            )
            limits = limits_response.json()
            
            # Get usage
            usage_response = httpx.get(
                f"{self.base_url}/v1/limits/usage",
                params={"user_id": self.user_id},
                headers=headers
            )
            usage = usage_response.json()
            
            return f"""💰 SPENDING LIMITS

Daily Budget:
  - Limit: ${limits.get('daily_limit', 'Unknown')}
  - Spent Today: ${usage.get('daily_spent', '0.00')}
  - Remaining: ${usage.get('daily_remaining', 'Unknown')}

Monthly Budget:
  - Limit: ${limits.get('monthly_limit', 'Unknown')}
  - Spent This Month: ${usage.get('monthly_spent', '0.00')}
  - Remaining: ${usage.get('monthly_remaining', 'Unknown')}

Per-Transaction Limit: ${limits.get('per_transaction_limit', 'Unknown')}

Transactions: {usage.get('daily_transaction_count', 0)} today, {usage.get('monthly_transaction_count', 0)} this month"""
        
        except Exception as e:
            return f"⚠️ Could not fetch spending limits: {str(e)}"
    
    async def _arun(self, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        return self._run(run_manager)


def create_agentauth_tools(
    delegation_token: str,
    api_key: Optional[str] = None,
    base_url: str = "http://localhost:8000",
    user_id: str = "default",
    agent_id: str = "langchain_agent",
) -> list:
    """
    Create AgentAuth LangChain tools.
    
    Args:
        delegation_token: User consent token for this agent session
        api_key: AgentAuth API key
        base_url: AgentAuth API URL
        user_id: User ID for limits/rules
        agent_id: Identifier for this agent
        
    Returns:
        List of LangChain tools: [AuthorizedPurchaseTool, CheckSpendingLimitsTool]
        
    Example:
        ```python
        from agentauth.integrations.langchain import create_agentauth_tools
        
        tools = create_agentauth_tools(
            delegation_token="token_from_consent",
            api_key="aa_live_xxx"
        )
        
        agent = create_react_agent(llm, tools)
        ```
    """
    if not HAS_LANGCHAIN:
        raise ImportError(
            "LangChain is not installed. Install with: pip install langchain-core"
        )
    
    return [
        AuthorizedPurchaseTool(
            delegation_token=delegation_token,
            api_key=api_key,
            base_url=base_url,
            agent_id=agent_id
        ),
        CheckSpendingLimitsTool(
            api_key=api_key,
            base_url=base_url,
            user_id=user_id
        )
    ]
