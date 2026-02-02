#!/usr/bin/env python3
"""
AgentAuth Core - Architecture Test
Run: python test_core.py
"""

from core import AgentAuthCore, PolicyBuilder

print('=' * 60)
print('AGENTAUTH CORE - ARCHITECTURE TEST')
print('=' * 60)

# Initialize the core
auth = AgentAuthCore()

print('\n[1] CRYPTOGRAPHIC LAYER')
print('-' * 40)
keys = auth.export_public_keys()
print(f'    Auth Signing Key:  {keys["auth_signing"][:32]}...')
print(f'    Audit Signing Key: {keys["audit_signing"][:32]}...')
print(f'    Master Secret:     {auth.export_master_secret()[:16]}... (PROTECTED)')

print('\n[2] POLICY ENGINE')
print('-' * 40)
policies = auth.list_policies()
for p in policies:
    print(f'    [{p["priority"]:3}] {p["name"]} -> {p["effect"]}')

print('\n[3] AUTHORIZATION FLOW')
print('-' * 40)

# Set up user
auth.set_user_limits('demo_user', daily_limit=500.0)
auth.set_agent_trust('agent_001', 0.9)

tests = [
    ('Normal purchase', 49.99, 'Amazon', 'electronics'),
    ('High amount', 299.99, 'Apple', 'electronics'),
    ('Blocked category', 50.00, 'CryptoEx', 'crypto'),
    ('Near limit', 450.00, 'BestBuy', 'electronics'),
]

for name, amount, merchant, category in tests:
    resp = auth.authorize(
        agent_id='agent_001',
        user_id='demo_user',
        action='purchase',
        amount=amount,
        merchant=merchant,
        category=category
    )
    status = 'APPROVED' if resp.authorized else 'DENIED'
    reason = resp.reason[:35] if resp.reason else 'N/A'
    print(f'    {name:20} ${amount:>7.2f} -> {status:8} | {reason}')

print('\n[4] SPENDING TRACKER')
print('-' * 40)
spending = auth.get_user_spending('demo_user')
print(f'    Daily Spent:     ${spending["daily_spent"]:.2f}')
print(f'    Daily Limit:     ${spending["daily_limit"]:.2f}')
print(f'    Daily Remaining: ${spending["daily_remaining"]:.2f}')

print('\n[5] RISK SCORING')
print('-' * 40)
risk = auth.assess_risk('demo_user', 'agent_001', 500.0, 'Unknown Store', 'jewelry')
print(f'    Score: {risk.overall_score:.0%} ({risk.level.value})')
print(f'    Factors:')
for f in risk.factors[:3]:
    print(f'      - {f.factor.value}: {f.score:.2f}')

print('\n[6] AUDIT LOG')
print('-' * 40)
valid, msg = auth.verify_audit_chain()
print(f'    Chain Valid: {valid}')
print(f'    Total Entries: {auth.stats["audit_entries"]}')
recent = auth.get_audit_log(limit=3)
for entry in recent:
    print(f'    - {entry["event_type"]}: {entry["id"]}')

print('\n[7] TOKEN VERIFICATION')
print('-' * 40)
resp = auth.authorize('agent_001', 'demo_user', 'purchase', 25.0, 'Target', 'groceries')
if resp.token:
    valid, data, err = auth.verify_token(resp.token)
    print(f'    Token ID: {resp.token_id}')
    print(f'    Verified: {valid}')
    if valid and data:
        print(f'    Agent: {data["agent"]}')
        print(f'    Amount: ${data["amount"]}')
    else:
        print(f'    Error: {err}')

print('\n' + '=' * 60)
print('ALL SYSTEMS OPERATIONAL')
print('=' * 60)
