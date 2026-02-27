# AgentAuth API Reference

> Version: 0.2.0
> Base URL: `https://agentauth-api.koyeb.app` (Production) or `http://localhost:8000` (Development)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Payments](#payments)
5. [Dashboard](#dashboard)
6. [Admin](#admin)
7. [Error Handling](#error-handling)

---

## Overview

AgentAuth provides cryptographic proof that a human authorized an AI agent's purchase. The API enables developers to set policies, budgets, and approval flows for AI agents making purchases on behalf of users.

### Core Flows

| Step | Endpoint | Description |
|------|----------|-------------|
| 1. Consent | `POST /v1/consents` | User authorizes agent with spending limits |
| 2. Authorize | `POST /v1/authorize` | Agent requests permission for specific transaction |
| 3. Verify | `POST /v1/verify` | Merchant verifies authorization code |

---

## Authentication

AgentAuth uses API key authentication. Include your API key in the request header:

### Option 1: X-API-Key Header (Recommended)

```http
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Option 2: Authorization Bearer Token

```http
Authorization: Bearer aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Getting an API Key

To obtain an API key, use the Admin endpoints:

```bash
# Step 1: Login as admin
curl -X POST http://localhost:8000/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_admin_password"}'

# Response:
# {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "token_type": "bearer"}

# Step 2: Create API key (use the access_token)
curl -X POST "http://localhost:8000/v1/admin/api-keys?owner=my_app" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Important:** The API key is only shown once at creation time. Store it securely.

---

## Core Endpoints

### Consents

#### Create a New Consent

Create a new user consent and receive a delegation token.

```http
POST /v1/consents
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "user_id": "user_123",
  "agent_id": "agent_shopping_bot",
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

**Response (201 Created):**

```json
{
  "consent_id": "cons_abc123xyz",
  "delegation_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "status": "active",
  "expires_at": "2026-02-27T10:00:00Z"
}
```

#### List Consents

```http
GET /v1/consents?limit=20&offset=0
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Get Consent Details

```http
GET /v1/consents/cons_abc123xyz
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### Revoke a Consent

```http
DELETE /v1/consents/cons_abc123xyz
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### Authorization

Request authorization for an agent action (typically a payment).

```http
POST /v1/authorize
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "delegation_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "action": "payment",
  "transaction": {
    "amount": 34700,
    "currency": "USD",
    "merchant_id": "delta_airlines"
  }
}
```

**Response - Authorized (200 OK):**

```json
{
  "decision": "ALLOW",
  "authorization_code": "authz_xyz789abc",
  "consent_id": "cons_abc123xyz"
}
```

**Response - Denied (200 OK):**

```json
{
  "decision": "DENY",
  "reason": "amount_exceeded",
  "message": "Transaction exceeds limit"
}
```

**Decision Types:**

| Decision | Description |
|----------|-------------|
| `ALLOW` | Authorization granted - proceed with transaction |
| `DENY` | Authorization denied - do not proceed |
| `STEP_UP` | User confirmation required |

---

### Verification

Verify an authorization code and get consent proof for chargeback defense.

```http
POST /v1/verify
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "authorization_code": "authz_xyz789abc",
  "transaction": {
    "amount": 34700,
    "currency": "USD"
  }
}
```

**Response - Valid (200 OK):**

```json
{
  "valid": true,
  "consent_proof": {
    "consent_id": "cons_abc123xyz",
    "user_authorized_at": "2026-02-26T10:30:00Z",
    "user_intent": "Buy cheapest flight to NYC",
    "max_authorized_amount": 50000,
    "actual_amount": 34700
  },
  "proof_token": "proof_eyJ0eXAiOiJKV1Qi..."
}
```

**Important:** Store the `proof_token` for chargeback defense.

---

## Payments

### Get Pricing

```http
GET /v1/payments/pricing
```

### Create Payment Intent

```http
POST /v1/payments/create-intent
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "amount": 4900,
  "currency": "USD",
  "customer_email": "customer@example.com"
}
```

### Create Agent Purchase

```http
POST /v1/payments/agent-purchase?authorization_code=authz_xyz789abc&amount=34700&currency=USD
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Create Subscription

```http
POST /v1/payments/subscribe
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Content-Type: application/json

{
  "price_id": "price_pro_monthly",
  "customer_email": "customer@example.com",
  "success_url": "https://yourapp.com/success",
  "cancel_url": "https://yourapp.com/cancel"
}
```

### Get/Cancel Subscription

```http
GET /v1/payments/subscriptions/sub_xxx
DELETE /v1/payments/subscriptions/sub_xxx
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Stripe Webhook

```http
POST /v1/payments/webhook
Stripe-Signature: t=xxx,v1=yyy
```

---

## Dashboard

### Get Dashboard

```http
GET /v1/dashboard
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Get Stats

```http
GET /v1/dashboard/stats
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Get Transactions

```http
GET /v1/dashboard/transactions?limit=50&offset=0
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Get Analytics

```http
GET /v1/dashboard/analytics?days=7
X-API-Key: aa_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Health Check

```http
GET /v1/dashboard/health
```

---

## Admin

### Admin Login

```http
POST /v1/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_admin_password"
}
```

**Response:**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Verify Token

```http
GET /v1/admin/verify
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Admin Logout

```http
POST /v1/admin/logout
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Create API Key

```http
POST /v1/admin/api-keys?owner=my_app
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### List API Keys

```http
GET /v1/admin/api-keys
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Rotate API Key

```http
POST /v1/admin/api-keys/key_abc123/rotate
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

---

## Error Handling

The API uses standard HTTP status codes:

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

Error responses include:

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Rate Limits

| Tier | Requests/min |
|------|--------------|
| Starter | 60 |
| Professional | 300 |
| Enterprise | 1000 |

---

## Quick Start with cURL

```bash
# 1. Login as admin
TOKEN=$(curl -s -X POST http://localhost:8000/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}' | jq -r '.access_token')

# 2. Create API key
API_KEY=$(curl -s -X POST "http://localhost:8000/v1/admin/api-keys?owner=myapp" \
  -H "Authorization: Bearer $TOKEN" | jq -r '.api_key')

# 3. Create consent
curl -X POST http://localhost:8000/v1/consents \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "intent": {"description": "Buy flight"}, "constraints": {"max_amount": 500}}'

# 4. Request authorization
curl -X POST http://localhost:8000/v1/authorize \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"delegation_token": "eyJ...", "action": "payment", "transaction": {"amount": 34700}}'

# 5. Verify (for merchants)
curl -X POST http://localhost:8000/v1/verify \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"authorization_code": "authz_...", "transaction": {"amount": 34700}}'
```
