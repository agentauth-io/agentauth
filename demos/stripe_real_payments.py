#!/usr/bin/env python3
"""
AgentAuth + Stripe Real Payment Demo

This demo actually processes payments through Stripe using test cards.
You'll see transactions appear in both AgentAuth dashboard AND Stripe dashboard.

Usage:
    python demos/stripe_real_payments.py
"""
import asyncio
import httpx
import os
import stripe
from datetime import datetime

# Load Stripe key from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

if not stripe.api_key:
    # Try loading from .env file manually
    try:
        with open(".env") as f:
            for line in f:
                if line.startswith("STRIPE_SECRET_KEY="):
                    stripe.api_key = line.split("=", 1)[1].strip()
                    break
    except:
        pass

API_BASE = "http://localhost:8000"

# Stripe test card tokens
# See: https://stripe.com/docs/testing
TEST_CARDS = {
    "visa": "pm_card_visa",
    "mastercard": "pm_card_mastercard",
    "amex": "pm_card_amex",
    "declined": "pm_card_chargeDeclined",
}

# Test scenarios
SCENARIOS = [
    {
        "name": "Notion Subscription",
        "description": "SaaS monthly subscription",
        "amount": 1000,  # $10.00 in cents
        "card": "visa",
        "consent_max": 15.00,
    },
    {
        "name": "DigitalOcean Droplet",
        "description": "Cloud hosting payment",
        "amount": 2400,  # $24.00
        "card": "mastercard",
        "consent_max": 50.00,
    },
    {
        "name": "GitHub Copilot",
        "description": "AI coding assistant subscription",
        "amount": 1900,  # $19.00
        "card": "visa",
        "consent_max": 25.00,
    },
    {
        "name": "AWS Services",
        "description": "Amazon Web Services bill",
        "amount": 4599,  # $45.99
        "card": "amex",
        "consent_max": 100.00,
    },
]


async def create_agentauth_consent(
    client: httpx.AsyncClient,
    description: str,
    max_amount: float
) -> dict:
    """Create AgentAuth consent for the transaction."""
    payload = {
        "user_id": f"stripe_demo_{datetime.now().strftime('%H%M%S')}",
        "intent": {"description": description},
        "constraints": {"max_amount": max_amount, "currency": "USD"},
        "signature": "demo_sig",
        "public_key": "demo_pk"
    }
    
    resp = await client.post(f"{API_BASE}/v1/consents", json=payload)
    if resp.status_code == 201:
        return resp.json()
    return None


async def authorize_with_agentauth(
    client: httpx.AsyncClient,
    token: str,
    amount: int,
    description: str
) -> dict:
    """Get AgentAuth authorization for the payment."""
    payload = {
        "delegation_token": token,
        "action": "payment",
        "transaction": {
            "amount": amount / 100,  # Convert cents to dollars
            "currency": "USD",
            "merchant_id": "stripe.com",
            "merchant_name": "Stripe Payment",
            "description": description
        }
    }
    
    resp = await client.post(f"{API_BASE}/v1/authorize", json=payload)
    if resp.status_code == 200:
        return resp.json()
    return {"decision": "ERROR"}


def create_stripe_payment(amount: int, description: str, card_type: str) -> dict:
    """Create actual Stripe PaymentIntent and confirm it."""
    try:
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            description=description,
            payment_method=TEST_CARDS.get(card_type, "pm_card_visa"),
            confirm=True,  # Immediately confirm/charge
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            metadata={
                "source": "agentauth_demo",
                "demo_time": datetime.now().isoformat()
            }
        )
        
        return {
            "success": intent.status in ["succeeded", "requires_capture"],
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount / 100,
        }
    except stripe.error.CardError as e:
        return {"success": False, "error": str(e), "status": "declined"}
    except Exception as e:
        return {"success": False, "error": str(e), "status": "error"}


async def run_scenario(client: httpx.AsyncClient, scenario: dict, index: int):
    """Run a payment scenario through AgentAuth + Stripe."""
    print(f"\n{'─' * 55}")
    print(f"  SCENARIO {index}: {scenario['name']}")
    print(f"{'─' * 55}")
    print(f"  💳 Amount: ${scenario['amount'] / 100:.2f}")
    print(f"  📝 Description: {scenario['description']}")
    print(f"  🎫 Card: {scenario['card'].upper()}")
    
    # Step 1: Create AgentAuth consent
    print(f"\n  ① Creating AgentAuth consent...")
    consent = await create_agentauth_consent(
        client, 
        scenario["description"],
        scenario["consent_max"]
    )
    if not consent:
        print(f"  ❌ Failed to create consent")
        return False
    print(f"     ✓ Consent: {consent['consent_id'][:20]}...")
    
    # Step 2: Get authorization
    print(f"\n  ② Requesting authorization...")
    auth = await authorize_with_agentauth(
        client,
        consent["delegation_token"],
        scenario["amount"],
        scenario["description"]
    )
    
    if auth.get("decision") != "ALLOW":
        print(f"     ❌ Authorization denied: {auth.get('reason', 'Unknown')}")
        return False
    
    print(f"     ✓ Authorized: {auth.get('authorization_code', '')[:20]}...")
    
    # Step 3: Process Stripe payment
    print(f"\n  ③ Processing Stripe payment...")
    result = create_stripe_payment(
        scenario["amount"],
        f"AgentAuth Demo: {scenario['description']}",
        scenario["card"]
    )
    
    if result.get("success"):
        print(f"     ✅ PAYMENT SUCCESSFUL!")
        print(f"     💳 PaymentIntent: {result.get('payment_intent_id', 'N/A')}")
        print(f"     📊 Status: {result.get('status', 'N/A')}")
        return True
    else:
        print(f"     ❌ Payment failed: {result.get('error', 'Unknown error')}")
        return False


async def main():
    """Run all payment scenarios."""
    print("\n" + "═" * 55)
    print("  💳 AGENTAUTH + STRIPE REAL PAYMENTS DEMO")
    print("  Transactions will appear in your Stripe Dashboard!")
    print("═" * 55)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check Stripe API key
    if not stripe.api_key or not stripe.api_key.startswith("sk_test_"):
        print("\n  ❌ ERROR: STRIPE_SECRET_KEY not configured!")
        print("     Add it to your .env file:")
        print("     STRIPE_SECRET_KEY=sk_test_your_key_here")
        return
    
    print(f"  Stripe Key: {stripe.api_key[:12]}...{stripe.api_key[-4:]}")
    print("═" * 55)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Check API health
        try:
            health = await client.get(f"{API_BASE}/health")
            if health.status_code != 200:
                print("\n  ❌ AgentAuth API not healthy")
                return
            print("\n  ✅ AgentAuth API: Connected")
        except Exception as e:
            print(f"\n  ❌ Cannot connect to API: {e}")
            return
        
        # Run scenarios
        results = []
        for i, scenario in enumerate(SCENARIOS, 1):
            success = await run_scenario(client, scenario, i)
            results.append({"name": scenario["name"], "success": success})
            await asyncio.sleep(1)  # Small delay between payments
        
        # Summary
        print("\n" + "═" * 55)
        print("  📊 PAYMENT SUMMARY")
        print("═" * 55)
        
        total_success = sum(1 for r in results if r["success"])
        for r in results:
            status = "✅" if r["success"] else "❌"
            print(f"  {status} {r['name']}")
        
        print(f"\n  Total: {total_success}/{len(results)} successful payments")
        print("\n  🔗 View in Stripe Dashboard:")
        print("     https://dashboard.stripe.com/test/payments")
        print("\n  🔗 View in AgentAuth Dashboard:")
        print("     http://localhost:5173/#nucleus")
        print("═" * 55 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
