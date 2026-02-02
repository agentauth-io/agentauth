#!/usr/bin/env python3
"""
AgentAuth Quick Demo - AI Agent Authorization in Action
"""
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8080"
API_KEY = None

# Test scenarios
SCENARIOS = [
    {"name": "☕ Coffee Purchase", "action": "purchase", "amount": 5.99, "merchant": "Starbucks", "category": "food", "expected": True},
    {"name": "📚 Book Order", "action": "purchase", "amount": 29.99, "merchant": "Amazon", "category": "retail", "expected": True},
    {"name": "💻 SaaS Subscription", "action": "purchase", "amount": 49.00, "merchant": "Notion", "category": "saas", "expected": True},
    {"name": "📖 Read User Data", "action": "read", "resource": "user_profile", "expected": True},
    {"name": "✏️ Update Settings", "action": "write", "resource": "settings", "expected": True},
    {"name": "🎰 Casino Bet", "action": "bet", "amount": 100, "merchant": "Vegas Casino", "category": "gambling", "expected": False},
    {"name": "💸 Large Transfer", "action": "transfer", "amount": 15000, "resource": "bank_account", "expected": False},
    {"name": "🗑️ Delete Account", "action": "delete", "resource": "user_account", "expected": False},
    {"name": "🛒 Over-limit Purchase", "action": "purchase", "amount": 999, "merchant": "Apple", "category": "electronics", "expected": False},
]

def get_api_key():
    """Bootstrap an API key"""
    global API_KEY
    resp = httpx.post(
        f"{API_BASE}/v1/bootstrap",
        params={"bootstrap_secret": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456", "owner": "demo"}
    )
    if resp.status_code == 200:
        API_KEY = resp.json()["key"]
        return True
    return False

def authorize(scenario: dict, user_num: int) -> dict:
    """Call authorize endpoint"""
    payload = {
        "agent_id": "demo-agent",
        "user_id": f"user_{user_num:03d}",
        "action": scenario.get("action", "purchase"),
    }
    if "amount" in scenario:
        payload["amount"] = scenario["amount"]
    if "merchant" in scenario:
        payload["merchant"] = scenario["merchant"]
    if "category" in scenario:
        payload["category"] = scenario["category"]
    if "resource" in scenario:
        payload["resource"] = scenario["resource"]
    
    resp = httpx.post(
        f"{API_BASE}/v1/authorize",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload,
        timeout=10
    )
    return resp.json()

def main():
    print("\n" + "═" * 60)
    print("  🤖 AGENTAUTH DEMO - AI Agent Authorization")
    print("═" * 60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 60 + "\n")
    
    # Get API key
    print("🔑 Getting API key...")
    if not get_api_key():
        print("❌ Failed to get API key")
        return
    print(f"   Key: {API_KEY[:20]}...\n")
    
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"─" * 60)
        print(f"📋 TEST {i}: {scenario['name']}")
        print(f"─" * 60)
        
        # Build description
        if "amount" in scenario:
            print(f"   Amount: ${scenario['amount']:.2f}")
        if "merchant" in scenario:
            print(f"   Merchant: {scenario['merchant']}")
        if "action" in scenario:
            print(f"   Action: {scenario['action']}")
        if "category" in scenario:
            print(f"   Category: {scenario['category']}")
        
        expected = "✅ APPROVE" if scenario["expected"] else "❌ DENY"
        print(f"   Expected: {expected}")
        
        # Authorize
        result = authorize(scenario, i)
        authorized = result.get("authorized", False)
        status = result.get("status", "unknown")
        reason = result.get("reason", "No reason")
        policy = result.get("policy_id", "none")
        
        actual = "✅ APPROVED" if authorized else "❌ DENIED"
        print(f"\n   Result: {actual}")
        print(f"   Reason: {reason}")
        print(f"   Policy: {policy}")
        
        # Check if matches expected
        if authorized == scenario["expected"]:
            print(f"   ✓ Test PASSED")
            passed += 1
        else:
            print(f"   ✗ Test FAILED (expected {scenario['expected']})")
            failed += 1
        print()
    
    # Summary
    print("═" * 60)
    print("  📊 DEMO SUMMARY")
    print("═" * 60)
    print(f"   ✅ Passed: {passed}/{len(SCENARIOS)}")
    print(f"   ❌ Failed: {failed}/{len(SCENARIOS)}")
    rate = 100 * passed / len(SCENARIOS)
    print(f"   📈 Success Rate: {rate:.0f}%")
    print("═" * 60 + "\n")

if __name__ == "__main__":
    main()
