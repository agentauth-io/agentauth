#!/usr/bin/env python3
"""
AgentAuth Shopping Demo

Simulates an AI shopping agent making purchases through AgentAuth.
Creates consents, requests authorizations, and completes transactions.

Usage:
    python shopping_demo.py
"""
import asyncio
import httpx
import json
import base64
import hashlib
import secrets
from datetime import datetime


# Configuration
API_BASE = "http://localhost:8000"

# Demo products
PRODUCTS = [
    {"id": "prod_001", "name": "Wireless Headphones Pro", "price": 79.99, "category": "electronics"},
    {"id": "prod_002", "name": "Mechanical Keyboard RGB", "price": 149.99, "category": "electronics"},
    {"id": "prod_003", "name": "USB-C Hub 7-in-1", "price": 45.00, "category": "accessories"},
    {"id": "prod_004", "name": "HD Webcam 1080p", "price": 89.00, "category": "electronics"},
    {"id": "prod_005", "name": "Laptop Stand Aluminum", "price": 35.00, "category": "accessories"},
]


def generate_mock_signature(data: dict) -> tuple[str, str]:
    """Generate mock signature and public key for demo purposes."""
    # In production, this would use real cryptographic signing
    content = json.dumps(data, sort_keys=True)
    signature = base64.b64encode(hashlib.sha256(content.encode()).digest()).decode()
    public_key = base64.b64encode(secrets.token_bytes(32)).decode()
    return signature, public_key


async def create_consent(
    client: httpx.AsyncClient,
    user_id: str,
    intent: str,
    max_amount: float,
    currency: str = "USD"
) -> dict:
    """Create a user consent for AI agent shopping."""
    
    intent_data = {"description": intent}
    constraints_data = {"max_amount": max_amount, "currency": currency}
    
    # Generate mock signature
    sign_content = {"intent": intent_data, "constraints": constraints_data}
    signature, public_key = generate_mock_signature(sign_content)
    
    payload = {
        "user_id": user_id,
        "intent": intent_data,
        "constraints": constraints_data,
        "options": {
            "expires_in_seconds": 3600,
            "single_use": False,
            "requires_confirmation": False
        },
        "signature": signature,
        "public_key": public_key
    }
    
    print(f"\n🛒 Creating consent for: {intent}")
    print(f"   Max Amount: ${max_amount} {currency}")
    
    response = await client.post(
        f"{API_BASE}/v1/consents",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        data = response.json()
        print(f"   ✅ Consent created: {data['consent_id'][:20]}...")
        print(f"   🔑 Delegation token received")
        return data
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return None


async def request_authorization(
    client: httpx.AsyncClient,
    delegation_token: str,
    product: dict,
    merchant_id: str = "demo_merchant"
) -> dict:
    """Request authorization for a purchase."""
    
    payload = {
        "delegation_token": delegation_token,
        "action": "payment",
        "transaction": {
            "amount": product["price"],
            "currency": "USD",
            "merchant_id": merchant_id,
            "description": f"Purchase: {product['name']}"
        }
    }
    
    print(f"\n🔐 Requesting authorization for: {product['name']}")
    print(f"   Amount: ${product['price']}")
    
    response = await client.post(
        f"{API_BASE}/v1/authorize",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        decision = data.get("decision", "UNKNOWN")
        
        if decision == "ALLOW":
            print(f"   ✅ AUTHORIZED - Code: {data.get('authorization_code', 'N/A')[:15]}...")
        elif decision == "DENY":
            print(f"   ❌ DENIED - Reason: {data.get('reason', 'N/A')}")
        elif decision == "STEP_UP":
            print(f"   ⚠️ STEP-UP REQUIRED - User confirmation needed")
        
        return data
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return None


async def verify_authorization(
    client: httpx.AsyncClient,
    authorization_code: str,
    amount: float,
    currency: str = "USD",
    merchant_id: str = "demo_merchant"
) -> dict:
    """Merchant verifies the authorization code."""
    
    payload = {
        "authorization_code": authorization_code,
        "transaction": {
            "amount": amount,
            "currency": currency
        },
        "merchant_id": merchant_id
    }
    
    print(f"\n🔍 Merchant verifying authorization...")
    
    response = await client.post(
        f"{API_BASE}/v1/verify",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("valid"):
            print(f"   ✅ VERIFIED - Consent proof received")
            print(f"   📝 Transaction ID: {data.get('transaction_id', 'N/A')}")
        else:
            print(f"   ❌ Invalid authorization")
        return data
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        return None


async def run_demo_scenario(
    client: httpx.AsyncClient,
    scenario_name: str,
    user_id: str,
    intent: str,
    max_amount: float,
    product: dict
):
    """Run a complete demo scenario."""
    print(f"\n{'='*60}")
    print(f"📦 SCENARIO: {scenario_name}")
    print(f"{'='*60}")
    
    # Step 1: Create consent
    consent = await create_consent(client, user_id, intent, max_amount)
    if not consent:
        return
    
    # Step 2: Request authorization
    auth = await request_authorization(
        client, 
        consent["delegation_token"], 
        product
    )
    if not auth:
        return
    
    # Step 3: If allowed, verify with merchant
    if auth.get("decision") == "ALLOW" and auth.get("authorization_code"):
        await verify_authorization(client, auth["authorization_code"], product["price"])
    
    print(f"\n{'='*60}\n")


async def main():
    """Run all demo scenarios."""
    print("\n" + "🤖 " * 20)
    print("    AGENTAUTH SHOPPING DEMO")
    print("    AI Agent Making Purchases")
    print("🤖 " * 20 + "\n")
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Check API health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print("❌ API not healthy")
                return
            print("✅ API is healthy\n")
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return
        
        # Scenario 1: Successful purchase (under limit)
        await run_demo_scenario(
            client,
            "✅ Successful Purchase (Under Limit)",
            user_id="shopper_alice",
            intent="Buy wireless headphones under $100",
            max_amount=100.0,
            product=PRODUCTS[0]  # Headphones $79.99
        )
        
        await asyncio.sleep(1)
        
        # Scenario 2: Denied purchase (over limit)
        await run_demo_scenario(
            client,
            "❌ Denied Purchase (Over Limit)",
            user_id="shopper_bob",
            intent="Buy a cheap keyboard under $100",
            max_amount=100.0,
            product=PRODUCTS[1]  # Keyboard $149.99
        )
        
        await asyncio.sleep(1)
        
        # Scenario 3: Accessory purchase
        await run_demo_scenario(
            client,
            "✅ USB Hub Purchase",
            user_id="shopper_charlie",
            intent="Buy a USB hub for my laptop",
            max_amount=50.0,
            product=PRODUCTS[2]  # USB Hub $45.00
        )
        
        await asyncio.sleep(1)
        
        # Scenario 4: HD Webcam
        await run_demo_scenario(
            client,
            "✅ Webcam Purchase",
            user_id="shopper_diana",
            intent="Buy an HD webcam for video calls",
            max_amount=100.0,
            product=PRODUCTS[3]  # Webcam $89.00
        )
        
        await asyncio.sleep(1)
        
        # Scenario 5: Laptop stand
        await run_demo_scenario(
            client,
            "✅ Laptop Stand Purchase",
            user_id="shopper_eve",
            intent="Buy a laptop stand under $50",
            max_amount=50.0,
            product=PRODUCTS[4]  # Stand $35.00
        )
        
        print("\n" + "✨ " * 20)
        print("    DEMO COMPLETE!")
        print("    Check the Nucleus dashboard for transactions")
        print("    URL: http://localhost:5173/#nucleus")
        print("✨ " * 20 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
