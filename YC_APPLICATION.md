# AgentAuth - YC Application

## One-Liner
**AgentAuth is Stripe for AI agent payments** — authorization infrastructure that lets users control how their AI agents spend money.

---

## What do you make?

AgentAuth is the authorization layer for AI agent transactions. We sit between AI agents and payment providers, enabling:
- Users to set spending limits and rules for their AI agents
- Merchants to verify that payments are authorized by real humans
- Developers to integrate agent payments in minutes with our SDK

**Think of it like a corporate card for AI** — but with programmable controls.

---

## The Problem

AI agents (like Claude, GPT-4, etc.) are starting to make purchases autonomously:
- Shopping assistants buying groceries
- Coding agents paying for cloud services  
- Business agents procuring software licenses

**But there's no authorization layer.** Today, you either:
1. Give the agent full access to your payment method (dangerous)
2. Don't let agents transact at all (limiting)

Neither works at scale.

---

## The Solution

AgentAuth provides:

| Feature | What it does |
|---------|--------------|
| **Spending Limits** | Daily/monthly/per-transaction caps |
| **Merchant Rules** | Whitelist/blacklist specific merchants |
| **Category Controls** | Block gambling, adult content, etc. |
| **Real-time Authorization** | Approve or deny in milliseconds |
| **Audit Trail** | Every transaction logged with consent proof |

### How It Works
```
1. User creates consent: "Buy groceries under $50"
2. AI agent finds item and requests authorization
3. AgentAuth checks limits, rules, and consent → APPROVE/DENY
4. Merchant verifies authorization code
5. Payment processes via Stripe
```

---

## Demo

🔗 **Live Demo:** https://agentauth.dev/#demo

### What the demo shows:
- Set a spending limit → Click a product → Watch real-time authorization
- See approved purchases (within limits)
- See denied purchases (over budget or blocked merchants)

![Demo Store](/home/seyominaoto/.gemini/antigravity/brain/b4aa3ab2-b0cf-42a8-ad44-5ef243c2fd5c/demo_store_initial_1768576739098.png)

![Authorization Flow](/home/seyominaoto/.gemini/antigravity/brain/b4aa3ab2-b0cf-42a8-ad44-5ef243c2fd5c/demo_store_authorized_1768576780593.png)

---

## Traction

| Metric | Value |
|--------|-------|
| **Status** | Functional MVP with live Stripe integration |
| **API Endpoints** | 15+ production-ready endpoints |
| **SDK** | Python SDK with LangChain & CrewAI integrations |
| **Test Transactions** | Real Stripe payments working |
| **Dashboard** | Full admin panel for monitoring |

---

## Business Model

**Stripe-like pricing:**
- 0.5% per authorized transaction + $0.10 flat fee
- Enterprise: Custom pricing with SLAs

**Why this works:**
- We only make money when agents spend money
- As agent commerce grows, we grow
- No upfront cost for developers

---

## Market

### Current State
- OpenAI, Anthropic, Google all building agent capabilities
- Agent frameworks (LangChain, CrewAI) have 100K+ stars on GitHub
- E-commerce is $6T+ globally

### Why Now
- GPT-4, Claude 3.5 can reliably execute multi-step tasks
- Function calling makes API interactions trivial
- No authorization standard exists yet — we can become it

### TAM Calculation
- 100M AI agent users × 10 transactions/month × $0.10 = **$1.2B/year**

---

## Competition

| Competitor | What they do | Why we're different |
|------------|--------------|---------------------|
| Stripe | Payment processing | No AI-specific authorization |
| Plaid | Bank connections | Read-only, no spending controls |
| Skyfire.xyz | Agent payments | No user consent layer |

**Our moat:** We're the only solution that puts the **user** in control of their AI agents' spending.

---

## Team

> [Fill in your team details]

- **Founder 1**: [Role, background, relevant experience]
- **Founder 2**: [Role, background, relevant experience]

---

## Ask

We're looking for:
1. **10 beta customers** building AI agents that need payment capabilities
2. **$500K seed** to hire 2 engineers and scale infrastructure
3. **Introductions** to AI agent framework teams (LangChain, CrewAI, AutoGPT)

---

## Links

- **Live Demo:** https://agentauth.dev/#demo
- **Dashboard:** https://agentauth.dev/#nucleus (password: agentauth2026)
- **GitHub:** https://github.com/Ashok-kumar290/agentauth
- **API Docs:** https://agentauth.dev/docs

---

## 2-Minute Demo Script

> **Opening (10s):** "AI agents are starting to spend money. But right now, there's no way for users to control them."

> **Problem (20s):** "Imagine giving your AI assistant a credit card with no limits. It could spend $10,000 before you notice."

> **Solution (30s):** "AgentAuth is the authorization layer for AI payments. Watch this..."
> - Show dashboard with spending limits
> - Show purchase being approved
> - Show purchase being denied

> **Demo (45s):** 
> - Run live demo at #demo
> - Set budget to $50
> - Click Notion ($10) → APPROVED ✓
> - Click Keyboard ($149) → DENIED ✗

> **Ask (15s):** "We're looking for 10 beta customers building AI agents that need payment capabilities."
