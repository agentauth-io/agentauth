# AgentAuth

![AgentAuth](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-Proprietary-red)

**The authorization layer for AI agent purchases.**

Cryptographic proof that a human authorized every AI agent transaction. Set spending limits, approve purchases, defend against chargebacks.

🌐 **Website:** [agentauth.in](https://agentauth.in)  
📖 **API Docs:** [api.agentauth.in/docs](https://api.agentauth.in/docs)  
🎮 **Live Demo:** [api.agentauth.in/demo](https://api.agentauth.in/demo)

---

## The Problem

AI agents are starting to make purchases on behalf of users. But when an agent buys something:

| Issue | Impact |
|-------|--------|
| ❌ No proof of user authorization | Users dispute charges they "didn't authorize" |
| ❌ No spending controls | Agents can overspend or buy wrong items |
| ❌ No merchant protection | 100% chargeback liability falls on merchants |

**Result:** $31B annual chargeback losses, growing as AI agents proliferate.

---

## The Solution

AgentAuth issues **delegation tokens** that cryptographically bind user consent to agent actions. Merchants verify these tokens to prove authorization.

```
User: "Buy me a flight under $500"
  ↓
AgentAuth: Issues delegation token with $500 limit
  ↓
Agent: Finds $347 flight, requests authorization
  ↓
AgentAuth: Checks constraints → ALLOW + authorization code
  ↓
Merchant: Verifies code → Gets cryptographic proof for chargeback defense
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| 💰 **Spending Controls** | Set per-transaction limits, daily caps, merchant restrictions |
| ⚡ **Instant Authorization** | Sub-second ALLOW/DENY decisions |
| 🔐 **Cryptographic Proof** | JWT-based consent tokens with tamper-proof audit trail |
| 🛡️ **Chargeback Defense** | Consent proofs for merchant protection |
| 🔗 **Universal Compatibility** | Works with LangChain, CrewAI, AutoGPT, any AI agent |
| 🐍 **Python SDK** | `pip install agentauth-client` |

---

## Quick Start

### Using the SDK

```bash
pip install agentauth-client
```

```python
from agentauth import AgentAuthClient

client = AgentAuthClient(
    api_url="https://api.agentauth.in",
    api_key="your_api_key"
)

# User creates consent
consent = client.create_consent(
    user_id="user_123",
    intent="Buy cheapest flight to NYC",
    max_amount=500,
    currency="USD"
)

# Agent requests authorization
auth = client.authorize(
    delegation_token=consent.delegation_token,
    amount=347,
    merchant_id="delta_airlines"
)

if auth.decision == "ALLOW":
    # Proceed with purchase
    print(f"Authorized: {auth.authorization_code}")
```

### LangChain Integration

```python
from agentauth.langchain import AgentAuthTool

# Add to your agent's tools
tools = [
    AgentAuthTool(api_key="your_api_key"),
    # ... other tools
]
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/consents` | Create user consent, get delegation token |
| `POST` | `/v1/authorize` | Agent requests authorization for transaction |
| `POST` | `/v1/verify` | Merchant verifies authorization code |
| `GET` | `/v1/consents` | List all consents (dashboard) |
| `GET` | `/health` | Health check |

Full API documentation: [api.agentauth.in/docs](https://api.agentauth.in/docs)

---

## How It Works

### 1. User Creates Consent

```bash
POST /v1/consents
{
  "user_id": "user_123",
  "agent_id": "agent_456",
  "intent": {
    "description": "Buy cheapest flight to NYC",
    "category": "travel"
  },
  "constraints": {
    "max_amount": 500,
    "currency": "USD"
  }
}
```

**Response:**
```json
{
  "consent_id": "cons_abc123",
  "delegation_token": "eyJ0eXAi...",
  "expires_at": "2026-01-12T20:00:00Z"
}
```

### 2. Agent Requests Authorization

```bash
POST /v1/authorize
{
  "delegation_token": "eyJ0eXAi...",
  "action": "payment",
  "transaction": {
    "amount": 347,
    "currency": "USD",
    "merchant_id": "delta_airlines"
  }
}
```

**Response (Authorized):**
```json
{
  "decision": "ALLOW",
  "authorization_code": "authz_xyz789",
  "consent_id": "cons_abc123"
}
```

**Response (Denied):**
```json
{
  "decision": "DENY",
  "reason": "amount_exceeded",
  "message": "Transaction $600 exceeds limit of $500"
}
```

### 3. Merchant Verifies

```bash
POST /v1/verify
{
  "authorization_code": "authz_xyz789",
  "transaction": {
    "amount": 347,
    "currency": "USD"
  }
}
```

**Response:**
```json
{
  "valid": true,
  "consent_proof": {
    "user_authorized_at": "2026-01-12T14:00:00Z",
    "user_intent": "Buy cheapest flight to NYC",
    "max_authorized_amount": 500,
    "actual_amount": 347
  },
  "proof_token": "eyJ..."
}
```

Store `proof_token` for chargeback defense.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│  AgentAuth  │◀────│   Agent     │
│  (Consent)  │     │    API      │     │ (LangChain) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Merchant   │
                    │  (Verify)   │
                    └─────────────┘
```

---

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SECRET_KEY` | JWT signing key (32+ chars) | ✅ |
| `DEBUG` | Enable debug mode | No |
| `TOKEN_EXPIRY_SECONDS` | Token expiry (default: 3600) | No |

---

## Deployment

### Railway (Production)

The application is deployed on Railway with automatic CI/CD from GitHub.

### Local Development

```bash
# Clone repository
git clone <repo-url>
cd agentauth

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

---

## Monitoring

### Terminal Dashboard

```bash
source venv/bin/activate
python dashboard.py
```

Real-time monitoring of consents and authorizations.

---

## Security

- **JWT Tokens:** All delegation tokens use RS256/HS256 signing
- **Encryption:** All data encrypted at rest and in transit
- **No Payment Data:** We never see card numbers or bank details
- **Audit Trail:** Complete, tamper-proof transaction history

---

## Roadmap

- [x] Core API (3 endpoints)
- [x] Python SDK
- [x] LangChain integration
- [x] Demo UI
- [x] Railway deployment
- [ ] Webhook notifications
- [ ] MCC (merchant category) validation
- [ ] Multi-currency support
- [ ] TypeScript/JavaScript SDK
- [ ] React components

---

## Support

📧 Email: hello@agentauth.in  
🌐 Website: [agentauth.in](https://agentauth.in)

---

## License

Proprietary. All rights reserved.

© 2026 AgentAuth
