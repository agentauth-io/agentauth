#!/usr/bin/env python3
"""
Phase 3 Integration Test Script

Tests LangChain and CrewAI integrations with the AgentAuth API.
"""
import sys

sys.path.insert(0, '/home/seyominaoto/Videos/AgentAuth/sdk/python/src')

print("=" * 60)
print("    AgentAuth Phase 3 Integration Tests")
print("=" * 60)

# Test 1: Import integrations
print("\n📦 TEST 1: Import Integrations")
print("-" * 40)
try:
    from agentauth.integrations.langchain import (
        HAS_LANGCHAIN,
        AuthorizedPurchaseTool,
        CheckSpendingLimitsTool,
        create_agentauth_tools,
    )
    print("  ✅ LangChain imports: OK")
    print(f"     HAS_LANGCHAIN: {HAS_LANGCHAIN}")
except Exception as e:
    print(f"  ❌ LangChain imports: FAILED - {e}")

try:
    from agentauth.integrations.crewai import (
        HAS_CREWAI,
        AuthorizedPurchaseCrewTool,
        CheckLimitsCrewTool,
    )
    print("  ✅ CrewAI imports: OK")
    print(f"     HAS_CREWAI: {HAS_CREWAI}")
except Exception as e:
    print(f"  ❌ CrewAI imports: FAILED - {e}")

# Test 2: Create a consent and get delegation token
print("\n🔑 TEST 2: Create Consent (get delegation token)")
print("-" * 40)
try:
    from agentauth import AgentAuth

    client = AgentAuth(base_url="http://localhost:8000")
    consent = client.consents.create(
        user_id="test_user_phase3",
        intent="Test purchase for Phase 3 integration testing",
        max_amount=500,
        currency="USD"
    )
    token = consent.delegation_token
    print("  ✅ Consent created")
    print(f"     Token: {token[:30]}...")
except Exception as e:
    print(f"  ❌ Consent creation: FAILED - {e}")
    token = None

# Test 3: Test CheckSpendingLimitsTool
print("\n💰 TEST 3: Check Spending Limits Tool")
print("-" * 40)
try:
    limits_tool = CheckSpendingLimitsTool(
        base_url="http://localhost:8000",
        user_id="default"
    )
    result = limits_tool._run()
    print("  ✅ CheckSpendingLimitsTool executed")
    print("     Result:")
    for line in result.split('\n')[:8]:
        print(f"       {line}")
except Exception as e:
    print(f"  ❌ CheckSpendingLimitsTool: FAILED - {e}")

# Test 4: Test AuthorizedPurchaseTool (should work if we have a token)
print("\n🛒 TEST 4: Authorized Purchase Tool")
print("-" * 40)
if token:
    try:
        purchase_tool = AuthorizedPurchaseTool(
            delegation_token=token,
            base_url="http://localhost:8000",
            agent_id="test_agent"
        )

        # Test a valid purchase
        result = purchase_tool._run(
            item_description="Test Product",
            amount=25.00,
            merchant="Amazon",
            category="ecommerce"
        )

        if "AUTHORIZED" in result:
            print("  ✅ Purchase authorized successfully")
        elif "DENIED" in result:
            print("  ⚠️ Purchase denied (expected if over limits)")
        else:
            print("  ❓ Unexpected result")

        print("     Result snippet:")
        for line in result.split('\n')[:6]:
            print(f"       {line}")
    except Exception as e:
        print(f"  ❌ AuthorizedPurchaseTool: FAILED - {e}")
else:
    print("  ⏭️ Skipped (no token)")

# Test 5: Test CrewAI CheckLimitsCrewTool
print("\n📊 TEST 5: CrewAI Check Limits Tool")
print("-" * 40)
try:
    crew_limits_tool = CheckLimitsCrewTool(
        base_url="http://localhost:8000",
        user_id="default"
    )
    result = crew_limits_tool._run()
    print("  ✅ CheckLimitsCrewTool executed")
    print("     Result:")
    for line in result.split('\n')[:5]:
        print(f"       {line}")
except Exception as e:
    print(f"  ❌ CheckLimitsCrewTool: FAILED - {e}")

# Test 6: Test CrewAI AuthorizedPurchaseCrewTool
print("\n🛍️ TEST 6: CrewAI Authorized Purchase Tool")
print("-" * 40)
if token:
    try:
        crew_purchase_tool = AuthorizedPurchaseCrewTool(
            delegation_token=token,
            base_url="http://localhost:8000",
            agent_id="crewai_test_agent"
        )

        result = crew_purchase_tool._run(
            item_description="Test Service Subscription",
            amount=9.99,
            merchant="Stripe",
            category="saas"
        )

        if "AUTHORIZED" in result:
            print("  ✅ CrewAI purchase authorized")
        elif "DENIED" in result:
            print("  ⚠️ CrewAI purchase denied")

        print("     Result snippet:")
        for line in result.split('\n')[:5]:
            print(f"       {line}")
    except Exception as e:
        print(f"  ❌ AuthorizedPurchaseCrewTool: FAILED - {e}")
else:
    print("  ⏭️ Skipped (no token)")

# Test 7: Test create_agentauth_tools helper
print("\n🔧 TEST 7: create_agentauth_tools helper")
print("-" * 40)
if token:
    try:
        tools = create_agentauth_tools(
            delegation_token=token,
            base_url="http://localhost:8000"
        )
        print(f"  ✅ Created {len(tools)} tools")
        for tool in tools:
            print(f"     - {tool.name}")
    except Exception as e:
        print(f"  ❌ create_agentauth_tools: FAILED - {e}")
else:
    print("  ⏭️ Skipped (no token)")

# Test 8: API endpoints verification
print("\n🌐 TEST 8: API Endpoints Verification")
print("-" * 40)
import httpx

endpoints = [
    ("GET", "/v1/limits", "Spending Limits"),
    ("GET", "/v1/limits/usage", "Usage Stats"),
    ("GET", "/v1/rules/merchants", "Merchant Rules"),
    ("GET", "/v1/rules/categories", "Category Rules"),
    ("GET", "/v1/analytics/summary", "Analytics Summary"),
    ("GET", "/v1/webhooks", "Webhooks"),
]

for method, path, name in endpoints:
    try:
        response = httpx.request(method, f"http://localhost:8000{path}")
        status = "✅" if response.status_code == 200 else "❌"
        print(f"  {status} {name}: {response.status_code}")
    except Exception as e:
        print(f"  ❌ {name}: FAILED - {e}")

print("\n" + "=" * 60)
print("    Phase 3 Tests Complete!")
print("=" * 60)
