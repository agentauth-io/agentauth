"""
AgentAuth Llama AI Agent
Integrates local Llama model for intelligent transaction decisions
"""

import json
import time
import random
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, field
import subprocess
import requests


@dataclass
class AgentDecision:
    """Decision made by the AI agent"""
    action: str
    merchant: str
    amount: float
    reasoning: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMemory:
    """Agent's memory of past decisions"""
    decisions: List[AgentDecision] = field(default_factory=list)
    total_spent: float = 0.0
    successful_transactions: int = 0
    failed_transactions: int = 0
    learned_preferences: Dict[str, Any] = field(default_factory=dict)


class LlamaAgent:
    """
    AI Shopping Agent powered by local Llama model
    Makes intelligent purchase decisions with AgentAuth authorization
    """
    
    def __init__(
        self,
        agent_id: str,
        user_id: str,
        ollama_host: str = "http://localhost:11434",
        model: str = "llama3.2",
        agentauth_url: str = "http://localhost:8000"
    ):
        self.agent_id = agent_id
        self.user_id = user_id
        self.ollama_host = ollama_host
        self.model = model
        self.agentauth_url = agentauth_url
        self.memory = AgentMemory()
        self.api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self._session_start = time.time()
        
        # User preferences (would be loaded from profile)
        self.preferences = {
            "budget_conscious": True,
            "preferred_categories": ["electronics", "groceries", "entertainment"],
            "max_single_purchase": 200.0,
            "daily_budget": 500.0,
            "blocked_categories": ["gambling", "adult"]
        }
    
    def _call_llama(self, prompt: str, system: str = None) -> str:
        """Call local Llama model via Ollama"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system:
                payload["system"] = system
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return self._fallback_decision(prompt)
                
        except Exception as e:
            print(f"[Agent] Llama unavailable, using fallback: {e}")
            return self._fallback_decision(prompt)
    
    def _fallback_decision(self, prompt: str) -> str:
        """Fallback decision logic when Llama is unavailable"""
        import random
        
        # Parse out amount from prompt if possible
        amount = 0.0
        if "Price: $" in prompt:
            try:
                price_str = prompt.split("Price: $")[1].split("\n")[0]
                amount = float(price_str)
            except:
                pass
        
        # Smart rule-based fallback
        remaining_budget = self.preferences['daily_budget'] - self.memory.total_spent
        
        # Check if within budget
        if amount > remaining_budget:
            return json.dumps({
                "decision": "skip",
                "confidence": 0.9,
                "reasoning": f"Would exceed remaining budget of ${remaining_budget:.2f}"
            })
        
        # Check single purchase limit
        if amount > self.preferences['max_single_purchase']:
            return json.dumps({
                "decision": "skip",
                "confidence": 0.85,
                "reasoning": f"Exceeds per-transaction limit of ${self.preferences['max_single_purchase']}"
            })
        
        # Check blocked categories
        for blocked in self.preferences.get('blocked_categories', []):
            if blocked.lower() in prompt.lower():
                return json.dumps({
                    "decision": "skip",
                    "confidence": 0.95,
                    "reasoning": f"Category '{blocked}' is blocked"
                })
        
        # Check preferred categories
        is_preferred = any(cat in prompt.lower() for cat in self.preferences['preferred_categories'])
        
        # Value-based decision
        if amount < 50:
            confidence = 0.85
            decision = "buy"
            reasoning = "Small purchase within budget"
        elif amount < 100 and is_preferred:
            confidence = 0.75
            decision = "buy"
            reasoning = "Good value in preferred category"
        elif amount < 150:
            confidence = 0.65
            decision = "buy"
            reasoning = "Moderate purchase, proceed with caution"
        else:
            confidence = 0.55
            decision = random.choice(["buy", "defer"])
            reasoning = "Large purchase - AI recommends careful consideration"
        
        return json.dumps({
            "decision": decision,
            "confidence": confidence,
            "reasoning": reasoning
        })
    
    def analyze_purchase(
        self,
        item: str,
        merchant: str,
        price: float,
        category: str = "general"
    ) -> AgentDecision:
        """
        Use AI to analyze whether a purchase should be made
        """
        system_prompt = """You are an AI shopping assistant. Your job is to help users make smart purchasing decisions.
        
Analyze the purchase request and respond with a JSON object:
{
    "decision": "buy" or "skip" or "defer",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation",
    "alternatives": ["optional alternative suggestions"]
}

Consider:
- User's budget and preferences
- Value for money
- Urgency and necessity
- Past purchase patterns"""

        user_prompt = f"""User preferences:
- Budget conscious: {self.preferences['budget_conscious']}
- Daily budget remaining: ${self.preferences['daily_budget'] - self.memory.total_spent:.2f}
- Max single purchase: ${self.preferences['max_single_purchase']}
- Preferred categories: {', '.join(self.preferences['preferred_categories'])}

Purchase request:
- Item: {item}
- Merchant: {merchant}
- Price: ${price:.2f}
- Category: {category}

Past decisions today: {len(self.memory.decisions)}
Total spent today: ${self.memory.total_spent:.2f}

Should the user buy this item?"""

        response = self._call_llama(user_prompt, system_prompt)
        
        try:
            result = json.loads(response)
        except:
            # Parse as text if JSON fails
            result = {
                "decision": "buy" if "buy" in response.lower() else "skip",
                "confidence": 0.6,
                "reasoning": response[:200]
            }
        
        decision = AgentDecision(
            action=result.get("decision", "skip"),
            merchant=merchant,
            amount=price,
            reasoning=result.get("reasoning", "AI analysis"),
            confidence=result.get("confidence", 0.5),
            metadata={
                "item": item,
                "category": category,
                "alternatives": result.get("alternatives", [])
            }
        )
        
        return decision
    
    def execute_purchase(
        self,
        merchant: str,
        amount: float,
        item: str = "item",
        category: str = "general"
    ) -> Dict[str, Any]:
        """
        Execute a purchase with AgentAuth authorization
        """
        print(f"\n{'='*60}")
        print(f"[Agent] Analyzing purchase: {item} from {merchant} for ${amount:.2f}")
        
        # Step 1: AI Analysis
        decision = self.analyze_purchase(item, merchant, amount, category)
        print(f"[Agent] AI Decision: {decision.action.upper()} (confidence: {decision.confidence:.0%})")
        print(f"[Agent] Reasoning: {decision.reasoning}")
        
        if decision.action == "skip":
            print(f"[Agent] Skipping purchase based on AI recommendation")
            return {
                "success": False,
                "stage": "ai_analysis",
                "reason": decision.reasoning
            }
        
        # Step 2: Request AgentAuth Authorization
        print(f"\n[Agent] Requesting AgentAuth authorization...")
        
        auth_result = self._request_authorization(merchant, amount, category)
        
        if not auth_result["authorized"]:
            print(f"[AgentAuth] DENIED: {auth_result['reason']}")
            print(f"[Agent] Purchase blocked by AgentAuth")
            self.memory.failed_transactions += 1
            return {
                "success": False,
                "stage": "authorization",
                "reason": auth_result["reason"],
                "risk_score": auth_result.get("risk_score", 0)
            }
        
        print(f"[AgentAuth] AUTHORIZED (Risk: {auth_result.get('risk_score', 0):.0%})")
        print(f"[AgentAuth] Token: {auth_result['token'][:20]}...")
        
        # Step 3: Execute Transaction
        print(f"\n[Agent] Executing transaction...")
        time.sleep(0.5)  # Simulate processing
        
        # Record success
        self.memory.decisions.append(decision)
        self.memory.total_spent += amount
        self.memory.successful_transactions += 1
        
        print(f"[Agent] Purchase completed!")
        print(f"[Agent] Session total: ${self.memory.total_spent:.2f}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "transaction_id": auth_result.get("transaction_id", "tx_demo"),
            "amount": amount,
            "merchant": merchant,
            "token": auth_result["token"]
        }
    
    def _request_authorization(
        self,
        merchant: str,
        amount: float,
        category: str
    ) -> Dict[str, Any]:
        """
        Request authorization from AgentAuth API
        Falls back to simulation if API unavailable
        """
        try:
            # Try real API first
            response = requests.post(
                f"{self.agentauth_url}/api/v1/authorize",
                json={
                    "agent_id": self.agent_id,
                    "user_id": self.user_id,
                    "merchant": merchant,
                    "amount": amount,
                    "currency": "USD",
                    "category": category
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Agent-Token": self.access_token or ""
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
                
        except Exception:
            pass
        
        # Simulation mode
        return self._simulate_authorization(merchant, amount)
    
    def _simulate_authorization(
        self,
        merchant: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Simulate AgentAuth authorization for demo
        """
        import secrets
        
        # Check blocked merchants
        blocked_merchants = ["casino", "gambling", "adult", "blocked merchant"]
        if any(b in merchant.lower() for b in blocked_merchants):
            return {
                "authorized": False,
                "reason": "Merchant is blocked",
                "risk_score": 1.0
            }
        
        # Check per-transaction limit
        if amount > self.preferences["max_single_purchase"]:
            return {
                "authorized": False,
                "reason": f"Amount ${amount:.2f} exceeds limit ${self.preferences['max_single_purchase']}",
                "risk_score": 0.8
            }
        
        # Check daily budget
        if self.memory.total_spent + amount > self.preferences["daily_budget"]:
            return {
                "authorized": False,
                "reason": f"Would exceed daily budget of ${self.preferences['daily_budget']}",
                "risk_score": 0.7
            }
        
        # Calculate risk score
        risk = 0.1
        if amount > 100:
            risk += 0.1
        if amount > 150:
            risk += 0.1
        if self.memory.successful_transactions > 5:
            risk += 0.05
        
        return {
            "authorized": True,
            "token": f"aa_tx_{secrets.token_hex(16)}",
            "transaction_id": f"tx_{secrets.token_hex(8)}",
            "risk_score": risk,
            "reason": "Authorized by AgentAuth"
        }
    
    def run_shopping_session(
        self,
        shopping_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Run a complete shopping session
        """
        print("\n" + "="*60)
        print("AgentAuth AI Shopping Agent - Demo Session")
        print(f"User: {self.user_id}")
        print(f"Agent: {self.agent_id}")
        print(f"Daily Budget: ${self.preferences['daily_budget']:.2f}")
        print("="*60)
        
        results = []
        
        for item in shopping_list:
            result = self.execute_purchase(
                merchant=item["merchant"],
                amount=item["amount"],
                item=item.get("item", "item"),
                category=item.get("category", "general")
            )
            results.append(result)
            time.sleep(0.2)  # Pacing for demo
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        total_amount = sum(r.get("amount", 0) for r in results if r["success"])
        
        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(f"Successful: {successful}/{len(results)}")
        print(f"Blocked: {len(results) - successful}/{len(results)}")
        print(f"Total Spent: ${total_amount:.2f}")
        print(f"Budget Remaining: ${self.preferences['daily_budget'] - total_amount:.2f}")
        print("="*60 + "\n")
        
        return {
            "successful": successful,
            "failed": len(results) - successful,
            "total_spent": total_amount,
            "results": results
        }


def run_demo():
    """Run a demo shopping session"""
    agent = LlamaAgent(
        agent_id="agent_demo_001",
        user_id="user_demo_001"
    )
    
    # Sample shopping list
    shopping_list = [
        {"merchant": "Amazon", "amount": 89.99, "item": "Wireless Headphones", "category": "electronics"},
        {"merchant": "Uber", "amount": 24.50, "item": "Ride to Airport", "category": "transportation"},
        {"merchant": "Netflix", "amount": 15.99, "item": "Monthly Subscription", "category": "entertainment"},
        {"merchant": "Apple Store", "amount": 199.00, "item": "AirPods Pro", "category": "electronics"},
        {"merchant": "Blocked Merchant", "amount": 50.00, "item": "Suspicious Item", "category": "unknown"},
        {"merchant": "Whole Foods", "amount": 156.78, "item": "Weekly Groceries", "category": "groceries"},
        {"merchant": "Best Buy", "amount": 349.99, "item": "4K Monitor", "category": "electronics"},  # Should be blocked - over limit
    ]
    
    agent.run_shopping_session(shopping_list)


if __name__ == "__main__":
    run_demo()
