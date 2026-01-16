"""
AgentAuth Framework Integrations

Tools for popular AI agent frameworks.
"""

# LangChain integration
try:
    from agentauth.integrations.langchain import (
        AuthorizedPurchaseTool,
        CheckSpendingLimitsTool,
        create_agentauth_tools,
    )
except ImportError:
    # LangChain not installed
    AuthorizedPurchaseTool = None
    CheckSpendingLimitsTool = None
    create_agentauth_tools = None

# CrewAI integration
try:
    from agentauth.integrations.crewai import (
        AuthorizedPurchaseCrewTool,
        create_crewai_tools,
    )
except ImportError:
    # CrewAI not installed
    AuthorizedPurchaseCrewTool = None
    create_crewai_tools = None

__all__ = [
    # LangChain
    "AuthorizedPurchaseTool",
    "CheckSpendingLimitsTool", 
    "create_agentauth_tools",
    # CrewAI
    "AuthorizedPurchaseCrewTool",
    "create_crewai_tools",
]
