"""
AgentAuth × LangChain Integration Demo
=======================================

Demonstrates how an AI agent can make budget-controlled purchases
using LangChain tools backed by AgentAuth's policy engine.

The agent is given a shopping task and must:
  1. Check spending limits before buying
  2. Get authorization for each purchase
  3. Handle denials gracefully

Run:
    pip install langchain langchain-core agentauth
    export AGENTAUTH_API_KEY="aa_live_xxx"
    python examples/langchain_demo.py

No LLM key required — this demo simulates the agent loop to
show the tool interface clearly.
"""

import os
import sys
import json
import time
from typing import List

# ── Import SDK ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk", "python", "src"))

try:
    from agentauth.integrations.langchain import (
        create_agentauth_tools,
        AuthorizedPurchaseTool,
        CheckSpendingLimitsTool,
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from agentauth import AgentAuth

# ── Colors ──────────────────────────────────────────────────────────────
C = {
    "cyan": "\033[96m", "green": "\033[92m", "red": "\033[91m",
    "yellow": "\033[93m", "dim": "\033[90m", "bold": "\033[1m",
    "reset": "\033[0m",
}

# ── Demo Configuration ──────────────────────────────────────────────────

API_URL = os.environ.get("AGENTAUTH_API_URL", "https://agentauth-api.koyeb.app")
API_KEY = os.environ.get("AGENTAUTH_API_KEY", "")

AGENT_TASK = """
You are a personal shopping assistant for Alice. She asked you to:

"Buy groceries for the week — bananas, protein bars, and almond milk. 
 Also check if we can get those wireless earbuds we talked about.
 Stay under $100 total."

You have $100 daily budget. Execute the purchases.
"""

SHOPPING_PLAN = [
    {"item": "Organic Bananas (bunch)",  "amount": 4.99,  "merchant": "Whole Foods", "category": "groceries"},
    {"item": "Protein Bars 12-pack",     "amount": 24.99, "merchant": "Amazon",      "category": "groceries"},
    {"item": "Almond Milk (64oz)",       "amount": 5.49,  "merchant": "Whole Foods", "category": "groceries"},
    {"item": "AirPods Pro 2",            "amount": 249.00,"merchant": "Apple",       "category": "electronics"},
]


def print_banner():
    print(f"""
{C['cyan']}╔══════════════════════════════════════════════════════════════╗
║       AgentAuth × LangChain Integration Demo                 ║
╚══════════════════════════════════════════════════════════════╝{C['reset']}
""")


def print_agent_thought(msg: str):
    print(f"  {C['dim']}🤖 Agent: {msg}{C['reset']}")


def print_tool_call(tool: str, args: dict):
    args_str = ", ".join(f"{k}={v!r}" for k, v in args.items() if v is not None)
    print(f"  {C['cyan']}⚡ Tool: {tool}({args_str}){C['reset']}")


def print_tool_result(result: str, success: bool = True):
    color = C['green'] if success else C['red']
    for line in result.strip().split("\n"):
        print(f"  {color}  → {line}{C['reset']}")


def print_step(n: int, total: int, item: dict):
    print(f"\n{C['bold']}━━━ Step {n}/{total}: {item['item']} ━━━{C['reset']}")
    print(f"  ${item['amount']:.2f} · {item['merchant']} · {item['category']}")


def run_simulated_agent():
    """
    Simulates a LangChain-style tool-calling agent loop.
    Shows exactly what tool calls would happen and their results.
    """
    print_banner()
    
    print(f"{C['bold']}📋 Agent Task:{C['reset']}")
    for line in AGENT_TASK.strip().split("\n"):
        print(f"  {line}")
    print()

    client = AgentAuth(api_key=API_KEY, base_url=API_URL)
    spent = 0.0
    results = []

    # Step 0: Agent thinks about the task
    print(f"{C['bold']}━━━ Step 0: Planning ━━━{C['reset']}")
    print_agent_thought("Alice wants groceries + earbuds. Budget is $100.")
    print_agent_thought(f"Shopping list has {len(SHOPPING_PLAN)} items totaling ${sum(i['amount'] for i in SHOPPING_PLAN):.2f}")
    print_agent_thought("Let me check spending limits first, then buy each item.")
    time.sleep(0.5)

    # Step 1: Check budget
    print(f"\n{C['bold']}━━━ Step 1: Check Budget ━━━{C['reset']}")
    print_agent_thought("I should check how much budget Alice has remaining.")
    print_tool_call("check_spending_limits", {})
    
    # Simulate the tool result
    budget_info = {
        "daily_limit": 100.00,
        "daily_spent": 0.00,
        "daily_remaining": 100.00,
        "monthly_limit": 2000.00,
        "monthly_spent": 450.00,
        "monthly_remaining": 1550.00,
    }
    print_tool_result(json.dumps(budget_info, indent=2))
    print_agent_thought(f"Good — ${budget_info['daily_remaining']:.2f} remaining today. Let me start buying.")
    time.sleep(0.3)

    # Steps 2+: Purchase each item
    for idx, item in enumerate(SHOPPING_PLAN, 2):
        print_step(idx, len(SHOPPING_PLAN) + 1, item)
        
        # Check if over budget
        if spent + item["amount"] > budget_info["daily_remaining"]:
            print_agent_thought(f"This would push total to ${spent + item['amount']:.2f}, over my $100 budget.")
            print_agent_thought("I should skip this — telling Alice.")
            print(f"  {C['yellow']}⏭  SKIPPED — over budget{C['reset']}")
            results.append({"item": item, "decision": "skipped", "reason": "Over $100 budget"})
            time.sleep(0.3)
            continue

        print_agent_thought(f"Authorizing ${item['amount']:.2f} at {item['merchant']}...")
        print_tool_call("authorized_purchase", {
            "item_description": item["item"],
            "amount": item["amount"],
            "merchant": item["merchant"],
            "category": item["category"],
        })

        # Use the playground evaluate endpoint to get real policy decisions
        try:
            result = client.evaluate(
                policies=[
                    {
                        "id": "pol_daily",
                        "name": "Daily Budget",
                        "effect": "allow",
                        "priority": 10,
                        "description": "Allow purchases within daily budget",
                        "constraints": {"daily_limit": 100.0},
                        "rules": [{"conditions": [
                            {"attribute": "amount", "operator": "lte", "value": 100.0},
                            {"attribute": "category", "operator": "in", "value": ["groceries", "electronics", "home"]},
                        ], "logic": "and"}],
                    },
                    {
                        "id": "pol_high",
                        "name": "High Value Review",
                        "effect": "require_approval",
                        "priority": 50,
                        "description": "Items over $100 need approval",
                        "constraints": {},
                        "rules": [{"conditions": [
                            {"attribute": "amount", "operator": "gt", "value": 100.0},
                        ], "logic": "and"}],
                    },
                ],
                context={
                    "agent_id": "langchain_shopping_agent",
                    "action": "purchase",
                    "amount": item["amount"],
                    "merchant": item["merchant"],
                    "category": item["category"],
                },
                combine_algorithm="deny_overrides",
            )
            
            decision = result.get("decision", "deny")
            explanation = result.get("explanation", "")
            risk = result.get("risk_score", 0)
            
        except Exception:
            # Fallback: simulate decisions based on rules
            if item["amount"] > 100:
                decision = "require_approval"
                explanation = "Amount exceeds $100 threshold"
                risk = 0.7
            else:
                decision = "allow"
                explanation = "Within budget and approved category"
                risk = 0.1

        if decision == "allow":
            print_tool_result(f"✓ AUTHORIZED — {explanation} (risk: {risk:.0%})")
            spent += item["amount"]
            print_agent_thought(f"Purchased! Running total: ${spent:.2f}")
            results.append({"item": item, "decision": "allow", "reason": explanation})
        elif decision == "require_approval":
            print_tool_result(f"⏳ NEEDS HUMAN APPROVAL — {explanation}", success=False)
            print_agent_thought("I can't complete this purchase without Alice's explicit approval.")
            results.append({"item": item, "decision": "pending", "reason": explanation})
        else:
            print_tool_result(f"✗ DENIED — {explanation}", success=False)
            print_agent_thought("Authorization denied. Moving on.")
            results.append({"item": item, "decision": "deny", "reason": explanation})
        
        time.sleep(0.4)

    # Summary
    allowed = [r for r in results if r["decision"] == "allow"]
    denied = [r for r in results if r["decision"] == "deny"]
    pending = [r for r in results if r["decision"] == "pending"]
    skipped = [r for r in results if r["decision"] == "skipped"]

    print(f"""
{C['cyan']}═══════════════════════════════════════════════════════════════
                    AGENT SESSION SUMMARY
═══════════════════════════════════════════════════════════════{C['reset']}

  {C['bold']}Task:{C['reset']}    Buy groceries + check earbuds (budget: $100)
  {C['bold']}Agent:{C['reset']}   langchain_shopping_agent

  {C['green']}✓ Purchased:{C['reset']}  {len(allowed)} items (${spent:.2f})""")
    for r in allowed:
        print(f"    • {r['item']['item']} — ${r['item']['amount']:.2f}")
    
    if pending:
        print(f"  {C['yellow']}⏳ Pending:{C['reset']}    {len(pending)} items")
        for r in pending:
            print(f"    • {r['item']['item']} — ${r['item']['amount']:.2f} ({r['reason']})")
    
    if skipped:
        print(f"  {C['dim']}⏭ Skipped:{C['reset']}    {len(skipped)} items")
        for r in skipped:
            print(f"    • {r['item']['item']} — ${r['item']['amount']:.2f} ({r['reason']})")
    
    if denied:
        print(f"  {C['red']}✗ Denied:{C['reset']}     {len(denied)} items")
        for r in denied:
            print(f"    • {r['item']['item']} — ${r['item']['amount']:.2f} ({r['reason']})")

    print(f"""
  {C['bold']}Budget:{C['reset']}  ${spent:.2f} / $100.00 ({spent/100*100:.0f}% used)
""")

    # Show the code
    if LANGCHAIN_AVAILABLE:
        print(f"{C['bold']}💡 LangChain Code:{C['reset']}")
        print(f"""
  {C['dim']}from agentauth.integrations.langchain import create_agentauth_tools

  tools = create_agentauth_tools(
      delegation_token="tok_xxx",
      api_key="aa_live_xxx",
      base_url="{API_URL}",
  )

  agent = create_react_agent(llm, tools, prompt)
  agent.invoke({{"input": "Buy groceries under $100"}}){C['reset']}
""")
    else:
        print(f"  {C['yellow']}ℹ Install langchain to use the real tools:{C['reset']}")
        print(f"  {C['dim']}pip install langchain langchain-core{C['reset']}")

    client.close()


if __name__ == "__main__":
    run_simulated_agent()
