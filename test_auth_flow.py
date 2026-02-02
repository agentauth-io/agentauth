#!/usr/bin/env python3
"""
AgentAuth Authorization Test - Complete Flow
=============================================
Tests the full authorization pipeline with proper consent-based flow:
1. Create API Key
2. Create Consent (user permission) → gets delegation_token
3. Use delegation_token for authorization requests
"""
import requests
import json
import os
import hashlib
import base64
from datetime import datetime

BASE_URL = "http://localhost:8081"
API_KEY = None
DELEGATION_TOKEN = None

def generate_mock_signature(data: dict) -> tuple[str, str]:
    """Generate mock signature and public key for testing."""
    # In production, this would use real Ed25519 signatures
    data_str = json.dumps(data, sort_keys=True)
    signature = base64.b64encode(hashlib.sha256(data_str.encode()).digest()).decode()
    public_key = base64.b64encode(b"mock_public_key_for_testing_only").decode()
    return signature, public_key

print("=" * 70)
print("       AGENTAUTH AUTHORIZATION TEST")
print("=" * 70)
print()

# Step 1: Create API Key using the test endpoint
print("STEP 1: Creating API Key...")
resp = requests.post(f"{BASE_URL}/v1/test-key", params={"owner": "test-agent"})
if resp.status_code == 200:
    data = resp.json()
    API_KEY = data.get("key")
    print(f"   ✓ API Key created: {API_KEY[:35]}...")
else:
    print(f"   ✗ FAIL: {resp.status_code} - {resp.text[:100]}")
print()

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"} if API_KEY else {"Content-Type": "application/json"}

# Step 2: Create Consent (User Permission)
print("STEP 2: Creating Consent (User Permission)...")
intent = {"description": "Shopping assistant to purchase electronics"}
constraints = {"max_amount": 500, "currency": "USD"}
signature, public_key = generate_mock_signature({**intent, **constraints})

consent_request = {
    "user_id": "user_test_123",
    "intent": intent,
    "constraints": constraints,
    "options": {"expires_in_seconds": 3600},
    "signature": signature,
    "public_key": public_key
}

resp = requests.post(f"{BASE_URL}/v1/consents", json=consent_request, headers=headers)
if resp.status_code in [200, 201]:
    consent_data = resp.json()
    DELEGATION_TOKEN = consent_data.get("delegation_token")
    consent_id = consent_data.get("consent_id", consent_data.get("id"))
    print(f"   ✓ Consent created: {consent_id}")
    if DELEGATION_TOKEN:
        print(f"   ✓ Delegation token received: {DELEGATION_TOKEN[:40]}...")
    else:
        print(f"   ! No delegation_token in response. Keys: {list(consent_data.keys())}")
else:
    print(f"   ✗ Status: {resp.status_code} - {resp.text[:200]}")
print()

# Step 3: Check Spending Limits
print("STEP 3: Checking Spending Limits...")
resp = requests.get(f"{BASE_URL}/v1/limits", headers=headers)
if resp.status_code == 200:
    limits = resp.json()
    print(f"   ✓ Spending limits: {json.dumps(limits)[:150]}...")
else:
    print(f"   Status: {resp.status_code} - {resp.text[:100] if resp.text else 'No response'}")
print()

# Step 4: List Category Rules
print("STEP 4: Checking Category Rules...")
resp = requests.get(f"{BASE_URL}/v1/rules/categories", headers=headers)
if resp.status_code == 200:
    rules = resp.json()
    if isinstance(rules, list):
        print(f"   ✓ Found {len(rules)} category rules")
        for r in rules[:3]:
            print(f"      - {r.get('category', 'unknown')}: {r.get('action', r.get('rule_type', 'N/A'))}")
    else:
        print(f"   ✓ Rules: {rules}")
else:
    print(f"   Status: {resp.status_code}")
print()

# Step 5: Authorization Request (Normal - $150)
print("STEP 5: Testing Authorization Request ($150 purchase)...")
if DELEGATION_TOKEN:
    auth_request = {
        "delegation_token": DELEGATION_TOKEN,
        "action": "payment",
        "transaction": {
            "amount": 150.00,
            "currency": "USD",
            "merchant_id": "amazon_electronics",
            "merchant_name": "Amazon Electronics"
        }
    }
    resp = requests.post(f"{BASE_URL}/v1/authorize", json=auth_request, headers=headers)
    if resp.status_code == 200:
        auth_result = resp.json()
        decision = auth_result.get('decision', auth_result.get('approved', 'UNKNOWN'))
        print(f"   ✓ Authorization Decision: {decision}")
        if 'authorization_code' in auth_result:
            print(f"      - Auth Code: {auth_result['authorization_code'][:30]}...")
        if 'reason' in auth_result:
            print(f"      - Reason: {auth_result['reason']}")
    else:
        print(f"   ✗ Status: {resp.status_code} - {resp.text[:200]}")
else:
    print("   ⚠ Skipped - No delegation token available")
print()

# Step 6: High-Value Authorization ($600 - exceeds limit)
print("STEP 6: Testing HIGH-VALUE Authorization ($600 - exceeds $500 limit)...")
if DELEGATION_TOKEN:
    high_value_request = {
        "delegation_token": DELEGATION_TOKEN,
        "action": "payment",
        "transaction": {
            "amount": 600.00,
            "currency": "USD",
            "merchant_id": "luxury_store",
            "merchant_name": "Luxury Goods Store"
        }
    }
    resp = requests.post(f"{BASE_URL}/v1/authorize", json=high_value_request, headers=headers)
    if resp.status_code == 200:
        auth_result = resp.json()
        decision = auth_result.get('decision', auth_result.get('approved', 'UNKNOWN'))
        print(f"   ✓ Authorization Decision: {decision}")
        if decision in ['DENY', 'STEP_UP']:
            print(f"      - EXPECTED: Amount exceeds consent limit")
        if 'reason' in auth_result:
            print(f"      - Reason: {auth_result['reason']}")
    else:
        print(f"   ✗ Status: {resp.status_code} - {resp.text[:200]}")
else:
    print("   ⚠ Skipped - No delegation token available")
print()

# Step 7: Fetch Consent Details
print("STEP 7: Verifying Consent Details...")
resp = requests.get(f"{BASE_URL}/v1/consents", headers=headers)
if resp.status_code == 200:
    consents = resp.json()
    if isinstance(consents, list):
        print(f"   ✓ Found {len(consents)} active consents")
        for c in consents[:2]:
            print(f"      - User: {c.get('user_id', 'N/A')}, Max: ${c.get('constraints', {}).get('max_amount', 'N/A')}")
    else:
        print(f"   ✓ Consents: {consents}")
else:
    print(f"   Status: {resp.status_code}")
print()

# Step 8: Dashboard Analytics
print("STEP 8: Checking Dashboard Analytics...")
resp = requests.get(f"{BASE_URL}/v1/analytics/summary", headers=headers)
if resp.status_code == 200:
    summary = resp.json()
    print(f"   ✓ Analytics Summary:")
    for key, value in list(summary.items())[:4]:
        print(f"      - {key}: {value}")
else:
    print(f"   Status: {resp.status_code}")
print()

# Step 9: Check Metrics endpoint
print("STEP 9: Checking System Metrics...")
resp = requests.get(f"{BASE_URL}/metrics")  # Prometheus metrics endpoint
if resp.status_code == 200:
    # Count some metrics
    metrics_text = resp.text
    metric_count = metrics_text.count('\n')
    print(f"   ✓ Prometheus metrics available ({metric_count} lines)")
else:
    print(f"   Status: {resp.status_code}")
print()

print("=" * 70)
print("   TEST COMPLETE")
print("=" * 70)
