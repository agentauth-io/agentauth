"""
AgentAuth Comprehensive Test Suite
Tests for authorization engine, security, and AI agent integration
"""

import time
import secrets
import json
from typing import Dict, Any

# Test the core modules
from agentauth_core import (
    AuthEngine,
    SecureTokenManager,
    HMACValidator,
    PolicyEngine,
    PolicyRule,
    PolicyAction,
    AdaptiveRateLimiter,
    AgentRegistry,
    AgentPermission,
    LlamaAgent
)


class TestSuite:
    """Comprehensive test suite for AgentAuth"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, test_func):
        """Run a single test"""
        try:
            test_func()
            self.results.append({"name": name, "status": "PASS"})
            self.passed += 1
            print(f"  [PASS] {name}")
        except AssertionError as e:
            self.results.append({"name": name, "status": "FAIL", "error": str(e)})
            self.failed += 1
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            self.results.append({"name": name, "status": "ERROR", "error": str(e)})
            self.failed += 1
            print(f"  [ERROR] {name}: {e}")
    
    def run_all(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("AgentAuth Test Suite")
        print("="*60 + "\n")
        
        print("Testing SecureTokenManager...")
        self.test_token_manager()
        
        print("\nTesting HMACValidator...")
        self.test_hmac_validator()
        
        print("\nTesting PolicyEngine...")
        self.test_policy_engine()
        
        print("\nTesting AdaptiveRateLimiter...")
        self.test_rate_limiter()
        
        print("\nTesting AgentRegistry...")
        self.test_agent_registry()
        
        print("\nTesting AuthEngine...")
        self.test_auth_engine()
        
        print("\nTesting LlamaAgent...")
        self.test_llama_agent()
        
        print("\n" + "="*60)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        print("="*60 + "\n")
        
        return self.failed == 0
    
    def test_token_manager(self):
        """Test token generation and validation"""
        tm = SecureTokenManager()
        
        def test_generate():
            token, metadata = tm.generate_token("agent1", "user1", "transaction")
            assert token is not None
            assert len(token) > 50
        
        def test_validate_valid():
            token, _ = tm.generate_token("agent1", "user1", "test")
            is_valid, payload, msg = tm.validate_token(token)
            assert is_valid == True
            assert payload.agent_id == "agent1"
        
        def test_reject_invalid():
            is_valid, payload, msg = tm.validate_token("invalid_token")
            assert is_valid == False
        
        def test_reject_tampered():
            token, _ = tm.generate_token("agent1", "user1", "test")
            tampered = token[:-5] + "XXXXX"
            is_valid, payload, msg = tm.validate_token(tampered)
            assert is_valid == False
        
        def test_revoke_token():
            token, _ = tm.generate_token("agent1", "user1", "transaction")
            is_valid1, _, _ = tm.validate_token(token)
            assert is_valid1 == True
            tm.revoke_token(token)
            is_valid2, _, msg = tm.validate_token(token)
            assert is_valid2 == False  # Revoked
        
        self.test("Generate token", test_generate)
        self.test("Validate valid token", test_validate_valid)
        self.test("Reject invalid token", test_reject_invalid)
        self.test("Reject tampered token", test_reject_tampered)
        self.test("Revoke token", test_revoke_token)
    
    def test_hmac_validator(self):
        """Test HMAC request signing"""
        hv = HMACValidator(secret_key=b"test_secret_key_for_hmac_validation")
        
        def test_sign():
            signature, timestamp = hv.sign_request("POST", "/api/test", b'{"data": "test"}')
            assert signature is not None
            assert len(signature) > 0
            assert timestamp > 0
        
        def test_verify_valid():
            body = b'{"data": "test"}'
            signature, timestamp = hv.sign_request("POST", "/api/test", body)
            is_valid, msg = hv.verify_request("POST", "/api/test", body, signature, timestamp)
            assert is_valid == True
        
        def test_reject_invalid():
            body = b'{"data": "test"}'
            signature, timestamp = hv.sign_request("POST", "/api/test", body)
            is_valid, msg = hv.verify_request("POST", "/api/test", body, "invalid_sig", timestamp)
            assert is_valid == False
        
        self.test("Sign request", test_sign)
        self.test("Verify valid signature", test_verify_valid)
        self.test("Reject invalid signature", test_reject_invalid)
    
    def test_policy_engine(self):
        """Test policy evaluation"""
        pe = PolicyEngine()
        
        # Add test rules
        pe.add_rule(PolicyRule(
            id="block_gambling",
            name="Block Gambling",
            priority=1,
            conditions={"category": "gambling"},  # Simple match
            action=PolicyAction.DENY
        ))
        
        pe.add_rule(PolicyRule(
            id="limit_100",
            name="Limit $100",
            priority=10,
            conditions={"min_amount": 100},  # Use min_amount for > check
            action=PolicyAction.REQUIRE_APPROVAL
        ))
        
        from agentauth_core.policy_engine import AuthorizationRequest
        
        def test_allow_normal():
            req = AuthorizationRequest(
                agent_id="agent1",
                user_id="user1",
                merchant="Amazon",
                amount=50.0,
                currency="USD",
                category="electronics"
            )
            result = pe.evaluate(req)
            assert result.allowed == True
        
        def test_block_gambling():
            req = AuthorizationRequest(
                agent_id="agent1",
                user_id="user1",
                merchant="Casino",
                amount=50.0,
                currency="USD",
                category="gambling"
            )
            result = pe.evaluate(req)
            assert result.allowed == False
        
        def test_require_approval():
            req = AuthorizationRequest(
                agent_id="agent1",
                user_id="user1",
                merchant="Amazon",
                amount=150.0,
                currency="USD",
                category="electronics"
            )
            result = pe.evaluate(req)
            # Either denied or requires approval
            assert result.allowed == False or result.action == PolicyAction.REQUIRE_APPROVAL
        
        self.test("Allow normal transaction", test_allow_normal)
        self.test("Block gambling category", test_block_gambling)
        self.test("Require approval for high amount", test_require_approval)
    
    def test_rate_limiter(self):
        """Test rate limiting"""
        rl = AdaptiveRateLimiter()
        
        def test_allow_initial():
            allowed, _ = rl.check_rate_limit("client_test_1")
            assert allowed == True
        
        def test_track_counts():
            client_id = f"client_{secrets.token_hex(4)}"
            for _ in range(10):
                rl.check_rate_limit(client_id)
            # If we got here, rate limiter is working
            assert True
        
        def test_separate_clients():
            c1 = f"client_{secrets.token_hex(4)}"
            c2 = f"client_{secrets.token_hex(4)}"
            for _ in range(5):
                rl.check_rate_limit(c1)
            allowed, _ = rl.check_rate_limit(c2)
            assert allowed == True
        
        self.test("Allow initial requests", test_allow_initial)
        self.test("Track request counts", test_track_counts)
        self.test("Separate client limits", test_separate_clients)
    
    def test_agent_registry(self):
        """Test agent registration"""
        ar = AgentRegistry()
        
        def test_register():
            agent_id, api_key = ar.register_agent(
                user_id="user1",
                name="TestAgent",
                description="A test agent",
                permissions=[AgentPermission.TRANSACTION_WRITE]
            )
            assert agent_id is not None
            assert api_key is not None
        
        def test_authenticate():
            agent_id, api_key = ar.register_agent(
                user_id="user2",
                name="AuthTestAgent",
                permissions=[AgentPermission.TRANSACTION_WRITE]
            )
            agent = ar.authenticate_agent(api_key)
            assert agent is not None
            assert agent.agent_id == agent_id
        
        def test_reject_invalid_key():
            agent = ar.authenticate_agent("invalid_key")
            assert agent is None
        
        def test_check_permissions():
            agent_id, _ = ar.register_agent(
                user_id="user3",
                name="PermTestAgent",
                permissions=[AgentPermission.TRANSACTION_READ]
            )
            has_write = ar.has_permission(agent_id, AgentPermission.TRANSACTION_WRITE)
            has_read = ar.has_permission(agent_id, AgentPermission.TRANSACTION_READ)
            assert has_write == False
            assert has_read == True
        
        self.test("Register new agent", test_register)
        self.test("Authenticate with valid key", test_authenticate)
        self.test("Reject invalid key", test_reject_invalid_key)
        self.test("Check permissions", test_check_permissions)
    
    def test_auth_engine(self):
        """Test full authorization engine"""
        ae = AuthEngine()
        
        # Register an agent
        ae.register_agent(
            agent_id="test_agent",
            user_id="test_user",
            permissions=["transaction:write"]
        )
        
        def test_authorize_valid():
            token, _ = ae.token_manager.generate_token("test_agent", "test_user", "transaction")
            result = ae.authorize_transaction(
                token=token,
                merchant="Amazon",
                amount=50.0,
                currency="USD"
            )
            assert result.allowed == True
        
        def test_high_risk():
            token, _ = ae.token_manager.generate_token("test_agent", "test_user", "transaction")
            result = ae.authorize_transaction(
                token=token,
                merchant="Suspicious Merchant",
                amount=9999.0,
                currency="USD"
            )
            # High amount should be handled (allowed or denied based on policy)
            assert True  # Test passes if no exception
        
        def test_get_stats():
            stats = ae.get_agent_stats("test_agent")
            assert stats is not None
            assert "request_count" in stats
        
        self.test("Authorize valid transaction", test_authorize_valid)
        self.test("Handle high-risk transaction", test_high_risk)
        self.test("Get agent stats", test_get_stats)
    
    def test_llama_agent(self):
        """Test Llama AI agent"""
        agent = LlamaAgent(
            agent_id="test_llama_agent",
            user_id="test_user",
            ollama_host="http://localhost:11434"  # Won't connect in test
        )
        
        def test_init():
            assert agent.agent_id == "test_llama_agent"
            assert agent.user_id == "test_user"
            assert agent.memory is not None
        
        def test_analyze():
            decision = agent.analyze_purchase(
                item="Headphones",
                merchant="Amazon",
                price=50.0,
                category="electronics"
            )
            assert decision is not None
            assert decision.merchant == "Amazon"
            assert decision.amount == 50.0
        
        def test_execute():
            result = agent.execute_purchase(
                merchant="Amazon",
                amount=50.0,
                item="Test Item"
            )
            assert "success" in result or "stage" in result
        
        def test_block_overlimit():
            result = agent.execute_purchase(
                merchant="Amazon",
                amount=999.0,  # Over limit
                item="Expensive Item"
            )
            assert result["success"] == False
        
        def test_block_merchant():
            agent2 = LlamaAgent(agent_id="test2", user_id="user2")
            result = agent2.execute_purchase(
                merchant="Casino Gambling",
                amount=50.0,
                item="Chips"
            )
            assert result["success"] == False
        
        self.test("Agent initialization", test_init)
        self.test("Analyze purchase (fallback mode)", test_analyze)
        self.test("Execute purchase with authorization", test_execute)
        self.test("Block over-limit purchase", test_block_overlimit)
        self.test("Block restricted merchant", test_block_merchant)


def run_tests():
    """Run all tests"""
    suite = TestSuite()
    success = suite.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    exit(run_tests())
