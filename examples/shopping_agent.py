"""
AgentAuth Shopping Agent Budget Demo
=====================================

Simulates an AI shopping agent that must get authorization for every
purchase through AgentAuth's policy engine.

Demonstrates:
  1. Budget enforcement — daily limit, per-transaction cap
  2. Category restrictions — only approved categories
  3. Geo-fencing — merchant country whitelist
  4. Approval workflows — high-value items need human approval
  5. Real-time spending tracking

Run:
    pip install agentauth-client
    export AGENTAUTH_API_KEY="aa_live_xxx"   # or leave empty for local dev
    python examples/shopping_agent.py
"""

import sys
import os
import time
import json
from dataclasses import dataclass, field
from typing import Optional

# ── Import SDK ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python", "src"))
from agentauth import AgentAuth

# ── Agent Configuration ─────────────────────────────────────────────────

AGENT_ID = "shopping-agent-v1"
USER_ID = "user_alice_001"

SHOPPING_LIST = [
    {"item": "Organic Bananas",      "amount": 4.99,    "merchant": "Whole Foods",  "category": "groceries",    "country": "US"},
    {"item": "Running Shoes",        "amount": 129.99,  "merchant": "Nike",         "category": "clothing",     "country": "US"},
    {"item": "iPhone 16 Pro",        "amount": 1199.00, "merchant": "Apple",        "category": "electronics",  "country": "US"},
    {"item": "Lottery Tickets",      "amount": 50.00,   "merchant": "StateLotto",   "category": "gambling",     "country": "US"},
    {"item": "Espresso Machine",     "amount": 349.00,  "merchant": "BrevilleUK",   "category": "home",         "country": "GB"},
    {"item": "Protein Bars (12pk)",  "amount": 24.99,   "merchant": "Amazon",       "category": "groceries",    "country": "US"},
    {"item": "Crypto Trading Course","amount": 499.00,  "merchant": "SketchyCo",    "category": "crypto",       "country": "KY"},
]

POLICIES = [
    {
        "id": "pol_budget",
        "name": "Daily Budget Limit",
        "effect": "allow",
        "priority": 10,
        "description": "Allow purchases up to $200 each, daily spend capped at $500",
        "constraints": {"daily_limit": 500.0},
        "rules": [{
            "conditions": [
                {"attribute": "amount", "operator": "lte", "value": 200.0},
                {"attribute": "category", "operator": "in", "value": ["groceries", "electronics", "clothing", "home", "health"]},
            ],
            "logic": "and"
        }]
    },
    {
        "id": "pol_block_risk",
        "name": "Block Risky Categories",
        "effect": "deny",
        "priority": 100,
        "description": "Block gambling, crypto, and adult categories outright",
        "constraints": {},
        "rules": [{
            "conditions": [
                {"attribute": "category", "operator": "in", "value": ["gambling", "crypto", "adult"]}
            ],
            "logic": "and"
        }]
    },
    {
        "id": "pol_geo",
        "name": "Geo-Restrict to US",
        "effect": "deny",
        "priority": 90,
        "description": "Only allow purchases from US merchants",
        "constraints": {},
        "rules": [{
            "conditions": [
                {"attribute": "merchant_country", "operator": "not_in", "value": ["US"]}
            ],
            "logic": "and"
        }]
    },
    {
        "id": "pol_high_value",
        "name": "High Value Review",
        "effect": "require_approval",
        "priority": 50,
        "description": "Items over $500 require human approval",
        "constraints": {},
        "rules": [{
            "conditions": [
                {"attribute": "amount", "operator": "gt", "value": 500.0}
            ],
            "logic": "and"
        }]
    },
]

# ── Pretty Print Helpers ────────────────────────────────────────────────

COLORS = {
    "allow":            "\033[92m",  # green
    "deny":             "\033[91m",  # red
    "require_approval": "\033[93m",  # yellow
    "reset":            "\033[0m",
    "dim":              "\033[90m",
    "bold":             "\033[1m",
    "cyan":             "\033[96m",
}

def banner():
    print(f"""
{COLORS['cyan']}╔══════════════════════════════════════════════════════════╗
║  AgentAuth Shopping Agent — Budget Enforcement Demo      ║
╚══════════════════════════════════════════════════════════╝{COLORS['reset']}

Agent:   {AGENT_ID}
User:    {USER_ID}
Items:   {len(SHOPPING_LIST)} purchases to attempt
Budget:  $500/day, $200/item cap
""")

def print_item(idx: int, item: dict):
    print(f"{COLORS['bold']}[{idx+1}/{len(SHOPPING_LIST)}] {item['item']}{COLORS['reset']}")
    print(f"  ${item['amount']:.2f} · {item['merchant']} · {item['category']} · {item['country']}")

def print_decision(result: dict):
    decision = result.get("decision", "unknown")
    color = COLORS.get(decision, COLORS["reset"])
    badge = {"allow": "✓ ALLOWED", "deny": "✗ DENIED", "require_approval": "⏳ NEEDS APPROVAL"}.get(decision, decision.upper())
    
    print(f"  {color}{COLORS['bold']}{badge}{COLORS['reset']}")
    print(f"  {COLORS['dim']}Risk: {result.get('risk_score', 0)*100:.0f}% · "
          f"Eval: {result.get('evaluation_time_ms', 0):.2f}ms · "
          f"Policy: {result.get('deciding_policy_name', 'N/A')}{COLORS['reset']}")
    
    if result.get("explanation"):
        print(f"  {COLORS['dim']}→ {result['explanation']}{COLORS['reset']}")
    print()

def print_summary(results: list):
    allowed = sum(1 for r in results if r["decision"] == "allow")
    denied = sum(1 for r in results if r["decision"] == "deny")
    pending = sum(1 for r in results if r["decision"] == "require_approval")
    total_spent = sum(r["amount"] for r in results if r["decision"] == "allow")
    
    print(f"""
{COLORS['cyan']}═══════════════════════════════════════════════════════════
                    SESSION SUMMARY
═══════════════════════════════════════════════════════════{COLORS['reset']}
  {COLORS['bold']}Allowed:{COLORS['reset']}  {COLORS['allow']}{allowed}{COLORS['reset']}    "
  {COLORS['bold']}Denied:{COLORS['reset']}   {COLORS['deny']}{denied}{COLORS['reset']}
  {COLORS['bold']}Pending:{COLORS['reset']}  {COLORS['require_approval']}{pending}{COLORS['reset']}
  {COLORS['bold']}Spent:{COLORS['reset']}    ${total_spent:.2f} / $500.00 daily budget
""")

# ── Main Loop ───────────────────────────────────────────────────────────

def main():
    api_url = os.environ.get("AGENTAUTH_API_URL", "https://agentauth-api.koyeb.app")
    api_key = os.environ.get("AGENTAUTH_API_KEY", "")
    
    client = AgentAuth(api_key=api_key, base_url=api_url)
    banner()

    results = []
    
    for idx, item in enumerate(SHOPPING_LIST):
        print_item(idx, item)
        
        context = {
            "agent_id": AGENT_ID,
            "action": "purchase",
            "amount": item["amount"],
            "merchant": item["merchant"],
            "category": item["category"],
            "merchant_country": item["country"],
        }
        
        try:
            result = client.evaluate(
                policies=POLICIES,
                context=context,
                combine_algorithm="deny_overrides",
            )
            result["amount"] = item["amount"]
            results.append(result)
            print_decision(result)
        except Exception as e:
            print(f"  {COLORS['deny']}⚠ Error: {e}{COLORS['reset']}\n")
            results.append({"decision": "deny", "amount": item["amount"]})
        
        time.sleep(0.3)  # simulate agent thinking

    print_summary(results)
    client.close()

if __name__ == "__main__":
    main()
