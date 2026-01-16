# AgentAuth - Authorization Infrastructure for AI Commerce

## What is AgentAuth?

AgentAuth is the **authorization layer for AI agent purchases**. As AI agents become capable of making autonomous transactions on behalf of users, AgentAuth provides the critical infrastructure to ensure every purchase is:

- **Human-authorized** — Cryptographic proof that a real person approved the transaction
- **Controlled** — Spending limits, merchant restrictions, and time-based controls
- **Auditable** — Complete transaction history for compliance and dispute resolution
- **Secure** — Protection against unauthorized agent actions and fraud

---

## The Problem We Solve

### The AI Commerce Gap

AI agents (like those built with LangChain, AutoGPT, or custom LLMs) are increasingly capable of taking actions on behalf of users — booking flights, ordering food, purchasing software. But there's a fundamental problem:

> **How do you prove a human authorized an AI agent's purchase?**

Current payment systems weren't designed for autonomous agents. When an AI agent makes a purchase:
- Merchants can't verify the human actually authorized it
- Users have no fine-grained control over what agents can spend
- Chargebacks become impossible to defend against
- There's no audit trail linking agents to human consent

### AgentAuth Fills This Gap

We provide the authorization infrastructure that sits between AI agents and payment systems:

```
User → AgentAuth (consent + limits) → AI Agent → Merchant → Payment
                     ↓
            Cryptographic proof of human authorization
```

---

## How It Works

### 1. User Creates Consent
Users define what their AI agents are allowed to do:
- Maximum spending per transaction
- Allowed merchant categories (SaaS, food, travel, etc.)
- Time-based limits (daily, weekly, monthly caps)
- Specific merchant allowlists/blocklists

### 2. Agent Requests Authorization
When an AI agent wants to make a purchase, it calls the AgentAuth API:

```python
from agentauth import AgentAuth

client = AgentAuth(api_key="your_key")

auth = client.authorize(
    consent_id="consent_abc123",
    amount=49.99,
    merchant="stripe.com",
    category="saas"
)

if auth.approved:
    # Proceed with purchase
    process_payment(auth.token)
```

### 3. Instant Decision
AgentAuth validates the request against user-defined rules:
- ✅ **ALLOW** — Within limits, authorized merchant
- ❌ **DENY** — Exceeds limits, blocked category, or expired consent

Response time: **< 100ms**

### 4. Cryptographic Proof
Each authorization includes a cryptographic signature that proves:
- The user consented to this type of purchase
- The transaction was within approved limits
- The authorization is valid and hasn't been tampered with

---

## Key Features

### For Users

| Feature | Description |
|---------|-------------|
| **Spending Controls** | Set per-transaction, daily, and monthly limits |
| **Merchant Restrictions** | Allow or block specific merchants or categories |
| **Real-time Visibility** | See all agent transactions instantly |
| **Instant Revocation** | Disable any agent's access immediately |
| **Audit History** | Complete log of all authorizations |

### For Developers

| Feature | Description |
|---------|-------------|
| **Python SDK** | Native Python integration, pip installable |
| **REST API** | Full HTTP API for any language |
| **LangChain Integration** | Drop-in tool for LangChain agents |
| **Webhook Support** | Real-time notifications for transactions |
| **Sub-100ms Latency** | Fast enough for real-time agent workflows |

### For Merchants

| Feature | Description |
|---------|-------------|
| **Chargeback Protection** | Cryptographic proof of authorization |
| **Fraud Reduction** | Verify agent transactions are human-approved |
| **Easy Integration** | Simple API to validate AgentAuth tokens |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AgentAuth                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Consent   │    │   Authz     │    │   Verify    │     │
│  │   Service   │────│   Engine    │────│   Service   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            │                               │
│                    ┌───────────────┐                       │
│                    │   PostgreSQL  │                       │
│                    │   Database    │                       │
│                    └───────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
            ▲                              ▲
            │                              │
    ┌───────────────┐              ┌───────────────┐
    │   AI Agents   │              │   Merchants   │
    │  (LangChain,  │              │   (Verify     │
    │   AutoGPT)    │              │    tokens)    │
    └───────────────┘              └───────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend API** | Python, FastAPI |
| **Database** | PostgreSQL |
| **Auth** | HMAC signatures, API keys |
| **SDK** | Python (pip installable) |
| **Hosting** | Railway (API), Netlify (Landing) |
| **Email** | Resend |

---

## Use Cases

### 1. AI Shopping Assistants
Personal AI agents that can purchase items on behalf of users — groceries, household items, subscriptions — with clear spending limits.

### 2. Autonomous SaaS Agents
AI agents that manage software subscriptions, upgrade plans, or purchase API credits when needed.

### 3. Travel Booking Agents
AI travel agents that can book flights, hotels, and activities within user-defined budgets.

### 4. Business Expense Agents
Corporate AI agents that handle routine purchases with per-employee spending controls.

### 5. Developer Tool Agents
AI coding assistants that can purchase dev tools, domains, or cloud resources.

---

## Competitive Advantage

| Competitor Approach | AgentAuth Approach |
|---------------------|-------------------|
| Virtual cards (limited control) | Fine-grained consent rules |
| Manual approval (slow) | Instant automated decisions |
| No audit trail | Full cryptographic audit log |
| No merchant protection | Chargeback-proof tokens |

---

## Current Status

| Milestone | Status |
|-----------|--------|
| Core API | ✅ Live |
| Python SDK | ✅ Published |
| Demo UI | ✅ Available |
| Landing Page | ✅ agentauth.in |
| Waitlist | ✅ Collecting signups |
| Private Beta | 🔜 Coming soon |

---

## Links

- **Website**: https://agentauth.in
- **API Demo**: https://agentauth-production.up.railway.app/demo
- **API Docs**: https://agentauth-production.up.railway.app/docs
- **GitHub**: (Private repository)

---

## Contact

- **Email**: hello@agentauth.in

---

*AgentAuth — Let AI Agents Buy For You, Safely.*
