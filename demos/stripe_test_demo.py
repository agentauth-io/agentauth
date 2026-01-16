#!/usr/bin/env python3
"""
AgentAuth Stripe Test Transactions Demo

Simulates an AI agent making real-looking transactions through AgentAuth
with Stripe payment simulation. Tests spending limits, rules, and analytics.

Usage:
    python demos/stripe_test_demo.py
"""
import asyncio
import httpx
import json
from datetime import datetime
from typing import Optional

# Configuration
API_BASE = "http://localhost:8000"

# Test scenarios with Stripe merchants
STRIPE_SCENARIOS = [
    {
        "name": "SaaS Subscription - Notion",
        "user_id": "user_stripe_001",
        "intent": "Subscribe to Notion Plus plan",
        "max_amount": 15.00,
        "purchase": {
            "amount": 10.00,
            "merchant_id": "notion.so",
            "merchant_name": "Notion",
            "category": "saas"
        },
        "expected": "ALLOW"
    },
    {
        "name": "Cloud Hosting - DigitalOcean",
        "user_id": "user_stripe_002",
        "intent": "Pay for cloud server hosting",
        "max_amount": 50.00,
        "purchase": {
            "amount": 24.00,
            "merchant_id": "digitalocean.com",
            "merchant_name": "DigitalOcean",
            "category": "saas"
        },
        "expected": "ALLOW"
    },
    {
        "name": "Over Limit - Expensive Tool",
        "user_id": "user_stripe_003",
        "intent": "Buy cheap analytics tool",
        "max_amount": 25.00,
        "purchase": {
            "amount": 99.00,
            "merchant_id": "analytics.io",
            "merchant_name": "Analytics.io",
            "category": "saas"
        },
        "expected": "DENY"
    },
    {
        "name": "E-commerce - Amazon AWS",
        "user_id": "user_stripe_004",
        "intent": "Pay AWS bill for this month",
        "max_amount": 200.00,
        "purchase": {
            "amount": 127.50,
            "merchant_id": "amazon.com",
            "merchant_name": "Amazon Web Services",
            "category": "ecommerce"
        },
        "expected": "ALLOW"
    },
    {
        "name": "Food Delivery - DoorDash",
        "user_id": "user_stripe_005",
        "intent": "Order team lunch",
        "max_amount": 100.00,
        "purchase": {
            "amount": 45.99,
            "merchant_id": "doordash.com",
            "merchant_name": "DoorDash",
            "category": "food"
        },
        "expected": "ALLOW"
    },
    {
        "name": "Per-Transaction Limit Test",
        "user_id": "user_stripe_006",
        "intent": "Buy software license",
        "max_amount": 500.00,  # High consent limit
        "purchase": {
            "amount": 75.00,  # Over $50 per-transaction limit
            "merchant_id": "jetbrains.com",
            "merchant_name": "JetBrains",
            "category": "saas"
        },
        "expected": "DENY"  # Should be denied due to per-transaction limit
    },
]


async def print_header():
    """Print demo header."""
    print("\n" + "═" * 60)
    print("  💳 AGENTAUTH STRIPE TEST TRANSACTIONS")
    print("  Testing AI Agent Authorization with Stripe Merchants")
    print("═" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60 + "\n")


async def get_current_limits(client: httpx.AsyncClient) -> dict:
    """Fetch current spending limits."""
    resp = await client.get(f"{API_BASE}/v1/limits")
    if resp.status_code == 200:
        return resp.json()
    return {}


async def create_consent(
    client: httpx.AsyncClient,
    user_id: str,
    intent: str,
    max_amount: float
) -> Optional[str]:
    """Create a consent and return delegation token."""
    payload = {
        "user_id": user_id,
        "intent": {"description": intent},
        "constraints": {"max_amount": max_amount, "currency": "USD"},
        "options": {"expires_in_seconds": 3600, "single_use": True},
        "signature": "test_sig",
        "public_key": "test_pk"
    }
    
    resp = await client.post(f"{API_BASE}/v1/consents", json=payload)
    if resp.status_code == 201:
        return resp.json().get("delegation_token")
    return None


async def authorize_purchase(
    client: httpx.AsyncClient,
    token: str,
    purchase: dict
) -> dict:
    """Request authorization for a purchase."""
    payload = {
        "delegation_token": token,
        "action": "payment",
        "transaction": {
            "amount": purchase["amount"],
            "currency": "USD",
            "merchant_id": purchase["merchant_id"],
            "merchant_name": purchase["merchant_name"],
            "merchant_category": purchase.get("category")
        }
    }
    
    resp = await client.post(f"{API_BASE}/v1/authorize", json=payload)
    if resp.status_code == 200:
        return resp.json()
    return {"decision": "ERROR", "reason": f"HTTP {resp.status_code}"}


async def run_scenario(client: httpx.AsyncClient, scenario: dict, index: int):
    """Run a single test scenario."""
    print(f"\n{'─' * 50}")
    print(f"📋 SCENARIO {index}: {scenario['name']}")
    print(f"{'─' * 50}")
    
    # Show setup
    print(f"   User: {scenario['user_id']}")
    print(f"   Intent: {scenario['intent']}")
    print(f"   Consent Limit: ${scenario['max_amount']:.2f}")
    print(f"   Purchase: ${scenario['purchase']['amount']:.2f} @ {scenario['purchase']['merchant_name']}")
    print(f"   Expected: {scenario['expected']}")
    
    # Step 1: Create consent
    print(f"\n   ① Creating consent...")
    token = await create_consent(
        client,
        scenario["user_id"],
        scenario["intent"],
        scenario["max_amount"]
    )
    
    if not token:
        print(f"   ❌ Failed to create consent")
        return False
    
    print(f"   ✓ Token: {token[:40]}...")
    
    # Step 2: Authorize purchase
    print(f"\n   ② Requesting authorization...")
    result = await authorize_purchase(client, token, scenario["purchase"])
    
    decision = result.get("decision", "UNKNOWN")
    
    # Step 3: Check result
    if decision == "ALLOW":
        auth_code = result.get("authorization_code", "N/A")
        print(f"   ✅ AUTHORIZED")
        print(f"      Code: {auth_code}")
    elif decision == "DENY":
        reason = result.get("reason", "N/A")
        message = result.get("message", "")
        print(f"   ❌ DENIED")
        print(f"      Reason: {reason}")
        if message:
            print(f"      Details: {message}")
    else:
        print(f"   ⚠️ Unknown decision: {decision}")
    
    # Step 4: Validate expectation
    passed = decision == scenario["expected"]
    if passed:
        print(f"\n   🎯 TEST PASSED (got {decision}, expected {scenario['expected']})")
    else:
        print(f"\n   ⚠️ TEST MISMATCH (got {decision}, expected {scenario['expected']})")
    
    return passed


async def get_analytics(client: httpx.AsyncClient) -> dict:
    """Fetch analytics summary."""
    resp = await client.get(f"{API_BASE}/v1/analytics/summary")
    if resp.status_code == 200:
        return resp.json()
    return {}


async def main():
    """Run all Stripe test scenarios."""
    await print_header()
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Check API health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print("❌ API not healthy")
                return
            print("✅ API Connection: OK")
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
        
        # Show current limits
        limits = await get_current_limits(client)
        print(f"\n📊 Current Spending Limits:")
        print(f"   Daily: ${limits.get('daily_limit', 'N/A')}")
        print(f"   Monthly: ${limits.get('monthly_limit', 'N/A')}")
        print(f"   Per-Transaction: ${limits.get('per_transaction_limit', 'N/A')}")
        
        # Run all scenarios
        results = []
        for i, scenario in enumerate(STRIPE_SCENARIOS, 1):
            passed = await run_scenario(client, scenario, i)
            results.append({"name": scenario["name"], "passed": passed})
            await asyncio.sleep(0.5)  # Small delay between tests
        
        # Summary
        print("\n" + "═" * 60)
        print("  📈 TEST SUMMARY")
        print("═" * 60)
        
        passed_count = sum(1 for r in results if r["passed"])
        total_count = len(results)
        
        for r in results:
            status = "✅" if r["passed"] else "❌"
            print(f"   {status} {r['name']}")
        
        print(f"\n   Total: {passed_count}/{total_count} tests passed")
        
        # Show analytics
        analytics = await get_analytics(client)
        print(f"\n📊 Analytics After Tests:")
        print(f"   Total Authorizations: {analytics.get('total_authorizations', 0)}")
        print(f"   Approved: {analytics.get('total_approved', 0)}")
        print(f"   Denied: {analytics.get('total_denied', 0)}")
        print(f"   Approval Rate: {analytics.get('approval_rate', 0)}%")
        
        print("\n" + "═" * 60)
        print("  ✨ STRIPE TEST DEMO COMPLETE")
        print("  Check dashboard: http://localhost:5173/#nucleus")
        print("═" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
