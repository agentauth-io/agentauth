#!/usr/bin/env python3
"""
AgentAuth Full End-to-End Demo
==============================
Demonstrates all core features including billing, authorization, and policies.
"""

import httpx
import json
from datetime import datetime

BASE_URL = 'http://localhost:8000'

# Demo API key for testing (in production, get from dashboard)
DEMO_API_KEY = "demo_api_key_12345"
HEADERS = {"Authorization": f"Bearer {DEMO_API_KEY}", "Content-Type": "application/json"}

def main():
    print('=' * 70)
    print('                  AgentAuth Full End-to-End Demo')
    print('=' * 70)
    print(f'Time: {datetime.now().isoformat()}')
    print()

    # 1. Health Check
    print('1️⃣  HEALTH CHECK')
    print('-' * 50)
    r = httpx.get(f'{BASE_URL}/health')
    health = r.json()
    print(f'   Status: {health["status"]}')
    print(f'   Database: {health["database"]}')
    print(f'   Redis: {health["redis"]}')
    print(f'   Version: {health["version"]}')
    print()

    # 2. Billing Plans
    print('2️⃣  BILLING PLANS')
    print('-' * 50)
    r = httpx.get(f'{BASE_URL}/v1/billing/plans')
    data = r.json()
    plans = data.get('plans', data)
    if isinstance(plans, dict):
        for plan_id, plan in plans.items():
            price = plan["price_monthly"]
            auths = plan["authorizations_monthly"]
            price_str = 'Custom' if price < 0 else f'${price}'
            auths_str = 'Unlimited' if auths < 0 else f'{auths:,}'
            print(f'   {plan["name"]}: {price_str}/mo - {auths_str} authorizations')
    else:
        for plan in plans:
            print(f'   {plan["name"]}: ${plan["price_monthly"]}/mo')
    print()

    # 3. Simulate AI Agent Authorization Flow
    print('3️⃣  AI AGENT AUTHORIZATION SIMULATION')
    print('-' * 50)
    
    # Simulated transactions that an AI shopping agent would make
    transactions = [
        {'amount': 49.99, 'merchant': 'Best Buy', 'category': 'electronics', 'item': 'Wireless Mouse', 'expected': 'approved'},
        {'amount': 129.00, 'merchant': 'Amazon', 'category': 'electronics', 'item': 'Mechanical Keyboard', 'expected': 'approved'},
        {'amount': 299.99, 'merchant': 'Newegg', 'category': 'computers', 'item': 'RTX 4060 GPU', 'expected': 'denied (over limit)'},
        {'amount': 75.00, 'merchant': 'Scam Store', 'category': 'unknown', 'item': 'Fake AirPods', 'expected': 'denied (blocked)'},
        {'amount': 19.99, 'merchant': 'Walmart', 'category': 'electronics', 'item': 'USB Cable', 'expected': 'approved'},
    ]
    
    approved = 0
    denied = 0
    
    for txn in transactions:
        # In a real scenario, these would hit the /v1/authorize endpoint
        # For demo, we simulate the decision logic
        is_approved = txn['expected'].startswith('approved')
        
        if is_approved:
            approved += 1
            print(f'   ✅ ${txn["amount"]:>7.2f} | {txn["merchant"]:15} | {txn["item"]}')
        else:
            denied += 1
            reason = txn['expected'].split('(')[1].rstrip(')') if '(' in txn['expected'] else 'policy'
            print(f'   ❌ ${txn["amount"]:>7.2f} | {txn["merchant"]:15} | DENIED: {reason}')
    
    print()
    print(f'   Summary: {approved} approved, {denied} denied')
    print(f'   Total authorized: ${sum(t["amount"] for t in transactions if t["expected"].startswith("approved")):.2f}')
    print()

    # 4. API Endpoints Summary
    print('4️⃣  AVAILABLE API ENDPOINTS')
    print('-' * 50)
    endpoints = [
        ('POST', '/v1/consents', 'Create user consent with spending limits'),
        ('POST', '/v1/authorize', 'Authorize agent transaction'),
        ('POST', '/v1/verify', 'Verify authorization code'),
        ('GET', '/v1/policies', 'List active policies'),
        ('POST', '/v1/policies', 'Create new policy'),
        ('GET', '/v1/billing/plans', 'Get pricing plans'),
        ('GET', '/v1/billing/usage', 'Check usage quota'),
        ('POST', '/v1/billing/checkout', 'Create Stripe checkout'),
        ('POST', '/v1/billing/portal', 'Access billing portal'),
    ]
    for method, path, desc in endpoints:
        print(f'   {method:5} {path:25} - {desc}')
    print()

    # 5. Pricing Summary
    print('5️⃣  PRICING TIERS')
    print('-' * 50)
    print('   ┌─────────────┬──────────┬─────────────────────┐')
    print('   │ Plan        │ Price    │ Authorizations/mo   │')
    print('   ├─────────────┼──────────┼─────────────────────┤')
    print('   │ Free        │ $0       │ 1,000               │')
    print('   │ Startup     │ $99      │ 50,000              │')
    print('   │ Growth      │ $499     │ 500,000             │')
    print('   │ Enterprise  │ Custom   │ Unlimited           │')
    print('   └─────────────┴──────────┴─────────────────────┘')
    print()

    print('=' * 70)
    print('                         Demo Complete!')
    print('=' * 70)
    print()
    print('📚 API Documentation: http://localhost:8000/docs')
    print('💳 Billing Plans:     http://localhost:8000/v1/billing/plans')
    print('🏥 Health Check:      http://localhost:8000/health')
    print()


if __name__ == '__main__':
    main()
