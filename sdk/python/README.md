# AgentAuth Python SDK

Official Python SDK for [AgentAuth](https://agentauth-production.up.railway.app) - the authorization layer for AI agent purchases.

## Installation

```bash
pip install agentauth-client
```

With LangChain support:
```bash
pip install agentauth-client[langchain]
```

## Quick Start

```python
from agentauth import AgentAuth

# Initialize client
client = AgentAuth(
    api_key="aa_live_xxx",
    base_url="https://api.agentauth.io"  # or your self-hosted URL
)

# 1. Create a consent (user expresses intent)
consent = client.consents.create(
    user_id="user_123",
    intent="Buy flight to NYC under $500",
    max_amount=500.0,
    currency="USD"
)
print(f"Token: {consent.delegation_token}")


# 2. Authorize a transaction (agent requests approval)
auth = client.authorize(
    token=consent.delegation_token,
    amount=347.0,
    currency="USD",
    merchant_id="delta_airlines"
)

if auth.allowed:
    print(f"✅ Authorized! Code: {auth.authorization_code}")
else:
    print(f"❌ Denied: {auth.reason}")

# 3. Verify authorization (merchant confirms)
verification = client.verify(
    authorization_code=auth.authorization_code,
    amount=347.0,
    currency="USD"
)

if verification.valid:
    print(f"✅ Valid! Proof: {verification.proof_token}")
```

## Async Support

```python
from agentauth import AsyncAgentAuth

async def main():
    client = AsyncAgentAuth(api_key="aa_live_xxx")
    
    consent = await client.consents.create(
        user_id="user_123",
        intent="Buy flight",
        max_amount=500.0,
        currency="USD"
    )
    
    auth = await client.authorize(
        token=consent.delegation_token,
        amount=347.0,
        currency="USD"
    )
```

## LangChain Integration

```python
from agentauth.langchain import AgentAuthTool

# Create tool for LangChain agents
tool = AgentAuthTool(api_key="aa_live_xxx")

# Use in your agent
from langchain.agents import initialize_agent
agent = initialize_agent(tools=[tool], llm=llm)
```

## Billing API

Manage subscriptions and usage programmatically:

```python
from agentauth import AgentAuth

client = AgentAuth(api_key="aa_live_xxx")

# Get available billing plans
plans = client.get_billing_plans()
for plan in plans:
    print(f"{plan['name']}: ${plan['price_monthly']}/mo - {plan['requests_per_month']} requests")

# Check your organization's current usage
usage = client.get_billing_usage()
print(f"Plan: {usage['plan']}")
print(f"Used: {usage['current_usage']} / {usage['limit']} requests")
print(f"Remaining: {usage['remaining']}")

# Create a checkout session to upgrade
checkout = client.create_checkout_session(
    plan="growth",
    success_url="https://yourapp.com/billing/success",
    cancel_url="https://yourapp.com/billing/cancel"
)
print(f"Redirect user to: {checkout['checkout_url']}")

# Get billing portal for managing subscription
portal = client.get_billing_portal_url(
    return_url="https://yourapp.com/dashboard"
)
print(f"Portal URL: {portal['portal_url']}")
```

### Available Plans

| Plan | Price | Requests/month |
|------|-------|----------------|
| Free | $0 | 1,000 |
| Startup | $99 | 50,000 |
| Growth | $499 | 500,000 |
| Enterprise | Custom | Unlimited |

## License

MIT
