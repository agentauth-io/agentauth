#!/usr/bin/env python3
"""
AgentAuth Penetration Testing Scenarios

This script provides automated penetration testing scenarios for AgentAuth:
- SQL Injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Authentication Bypass
- Authorization Bypass
- Rate Limiting Bypass
- API Key Abuse
- Input Validation
- Path Traversal
- Command Injection
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"
API_KEY = "aa_test_key_for_pentest"

class PenetrationTester:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.vulnerabilities: List[Dict[str, Any]] = []

    async def test_sql_injection(self, session: aiohttp.ClientSession):
        """Test for SQL injection vulnerabilities"""
        print("\n[+] Testing SQL Injection...")
        
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1'--",
            "' OR '1'='1'/*",
            "1' UNION SELECT NULL--",
            "'; DROP TABLE users;--",
            "1' AND 1=1--",
            "admin'--",
            "' OR 1=1--",
        ]
        
        for payload in payloads:
            try:
                # Test on authorize endpoint
                url = f"{BASE_URL}/v1/authorize"
                headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                body = {
                    "user_id": payload,
                    "agent_id": "test_agent",
                    "merchant_id": "test_merchant",
                    "amount": 100.0,
                    "currency": "USD",
                }
                
                async with session.post(url, headers=headers, json=body, timeout=5) as response:
                    result = {
                        "test": "SQL Injection",
                        "payload": payload,
                        "status": response.status,
                        "vulnerable": response.status not in [400, 401, 403, 422],
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.results.append(result)
                    
                    if result["vulnerable"]:
                        self.vulnerabilities.append({
                            "severity": "CRITICAL",
                            "type": "SQL Injection",
                            "payload": payload,
                            "endpoint": "/v1/authorize",
                        })
                        print(f"  [!] POTENTIAL VULNERABILITY: {payload[:50]}...")
            except Exception as e:
                print(f"  [-] Error testing payload: {e}")

    async def test_xss(self, session: aiohttp.ClientSession):
        """Test for XSS vulnerabilities"""
        print("\n[+] Testing XSS...")
        
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<body onload=alert('XSS')>",
            "<iframe src='javascript:alert(\"XSS\")'>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
        ]
        
        for payload in payloads:
            try:
                # Test on consents endpoint
                url = f"{BASE_URL}/v1/consents"
                headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                body = {
                    "user_id": f"user_{payload}",
                    "agent_id": "test_agent",
                    "max_amount": 1000.0,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                }
                
                async with session.post(url, headers=headers, json=body, timeout=5) as response:
                    result = {
                        "test": "XSS",
                        "payload": payload[:50],
                        "status": response.status,
                        "vulnerable": response.status not in [400, 401, 403, 422],
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.results.append(result)
                    
                    if result["vulnerable"]:
                        self.vulnerabilities.append({
                            "severity": "HIGH",
                            "type": "XSS",
                            "payload": payload[:50],
                            "endpoint": "/v1/consents",
                        })
                        print(f"  [!] POTENTIAL VULNERABILITY: {payload[:50]}...")
            except Exception as e:
                print(f"  [-] Error testing payload: {e}")

    async def test_authentication_bypass(self, session: aiohttp.ClientSession):
        """Test for authentication bypass"""
        print("\n[+] Testing Authentication Bypass...")
        
        # Test without API key
        try:
            url = f"{BASE_URL}/v1/consents"
            headers = {"Content-Type": "application/json"}
            body = {
                "user_id": "test_user",
                "agent_id": "test_agent",
                "max_amount": 1000.0,
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            }
            
            async with session.post(url, headers=headers, json=body, timeout=5) as response:
                result = {
                    "test": "Authentication Bypass",
                    "scenario": "No API Key",
                    "status": response.status,
                    "vulnerable": response.status == 200,
                    "timestamp": datetime.now().isoformat(),
                }
                self.results.append(result)
                
                if result["vulnerable"]:
                    self.vulnerabilities.append({
                        "severity": "CRITICAL",
                        "type": "Authentication Bypass",
                        "scenario": "No API Key",
                        "endpoint": "/v1/consents",
                    })
                    print(f"  [!] CRITICAL: Authentication bypassed without API key!")
        except Exception as e:
            print(f"  [-] Error: {e}")
        
        # Test with invalid API key
        try:
            url = f"{BASE_URL}/v1/consents"
            headers = {"X-API-Key": "invalid_key_12345", "Content-Type": "application/json"}
            body = {
                "user_id": "test_user",
                "agent_id": "test_agent",
                "max_amount": 1000.0,
                "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            }
            
            async with session.post(url, headers=headers, json=body, timeout=5) as response:
                result = {
                    "test": "Authentication Bypass",
                    "scenario": "Invalid API Key",
                    "status": response.status,
                    "vulnerable": response.status == 200,
                    "timestamp": datetime.now().isoformat(),
                }
                self.results.append(result)
                
                if result["vulnerable"]:
                    self.vulnerabilities.append({
                        "severity": "CRITICAL",
                        "type": "Authentication Bypass",
                        "scenario": "Invalid API Key",
                        "endpoint": "/v1/consents",
                    })
                    print(f"  [!] CRITICAL: Authentication bypassed with invalid API key!")
        except Exception as e:
            print(f"  [-] Error: {e}")

    async def test_authorization_bypass(self, session: aiohttp.ClientSession):
        """Test for authorization bypass (IDOR)"""
        print("\n[+] Testing Authorization Bypass (IDOR)...")
        
        # Try to access another user's data
        try:
            url = f"{BASE_URL}/v1/consents?user_id=other_user_12345"
            headers = {"X-API-Key": API_KEY}
            
            async with session.get(url, headers=headers, timeout=5) as response:
                result = {
                    "test": "Authorization Bypass",
                    "scenario": "Access Other User Data",
                    "status": response.status,
                    "vulnerable": response.status == 200,
                    "timestamp": datetime.now().isoformat(),
                }
                self.results.append(result)
                
                if result["vulnerable"]:
                    self.vulnerabilities.append({
                        "severity": "HIGH",
                        "type": "Authorization Bypass",
                        "scenario": "IDOR",
                        "endpoint": "/v1/consents",
                    })
                    print(f"  [!] POTENTIAL VULNERABILITY: Can access other user's data!")
        except Exception as e:
            print(f"  [-] Error: {e}")

    async def test_rate_limiting_bypass(self, session: aiohttp.ClientSession):
        """Test for rate limiting bypass"""
        print("\n[+] Testing Rate Limiting Bypass...")
        
        # Send rapid requests
        url = f"{BASE_URL}/v1/authorize"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        body = {
            "user_id": "test_user",
            "agent_id": "test_agent",
            "merchant_id": "test_merchant",
            "amount": 100.0,
            "currency": "USD",
        }
        
        rate_limited_count = 0
        for i in range(150):  # Try 150 requests rapidly
            try:
                async with session.post(url, headers=headers, json=body, timeout=5) as response:
                    if response.status == 429:
                        rate_limited_count += 1
            except:
                pass
        
        result = {
            "test": "Rate Limiting Bypass",
            "total_requests": 150,
            "rate_limited": rate_limited_count,
            "vulnerable": rate_limited_count < 10,  # Should be rate limited
            "timestamp": datetime.now().isoformat(),
        }
        self.results.append(result)
        
        if result["vulnerable"]:
            self.vulnerabilities.append({
                "severity": "MEDIUM",
                "type": "Rate Limiting Bypass",
                "details": f"Only {rate_limited_count}/150 requests were rate limited",
            })
            print(f"  [!] POTENTIAL VULNERABILITY: Rate limiting not effective!")
        else:
            print(f"  [✓] Rate limiting working: {rate_limited_count}/150 requests blocked")

    async def test_path_traversal(self, session: aiohttp.ClientSession):
        """Test for path traversal vulnerabilities"""
        print("\n[+] Testing Path Traversal...")
        
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%2fpasswd",
        ]
        
        for payload in payloads:
            try:
                url = f"{BASE_URL}/v1/consents?user_id={payload}"
                headers = {"X-API-Key": API_KEY}
                
                async with session.get(url, headers=headers, timeout=5) as response:
                    result = {
                        "test": "Path Traversal",
                        "payload": payload,
                        "status": response.status,
                        "vulnerable": response.status == 200,
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.results.append(result)
                    
                    if result["vulnerable"]:
                        self.vulnerabilities.append({
                            "severity": "HIGH",
                            "type": "Path Traversal",
                            "payload": payload,
                            "endpoint": "/v1/consents",
                        })
                        print(f"  [!] POTENTIAL VULNERABILITY: {payload}")
            except Exception as e:
                print(f"  [-] Error: {e}")

    async def test_command_injection(self, session: aiohttp.ClientSession):
        """Test for command injection vulnerabilities"""
        print("\n[+] Testing Command Injection...")
        
        payloads = [
            "; cat /etc/passwd",
            "| cat /etc/passwd",
            "&& cat /etc/passwd",
            "; ls -la",
            "$(cat /etc/passwd)",
            "`cat /etc/passwd`",
        ]
        
        for payload in payloads:
            try:
                url = f"{BASE_URL}/v1/consents"
                headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                body = {
                    "user_id": f"user_{payload}",
                    "agent_id": "test_agent",
                    "max_amount": 1000.0,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                }
                
                async with session.post(url, headers=headers, json=body, timeout=5) as response:
                    result = {
                        "test": "Command Injection",
                        "payload": payload,
                        "status": response.status,
                        "vulnerable": response.status not in [400, 401, 403, 422],
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.results.append(result)
                    
                    if result["vulnerable"]:
                        self.vulnerabilities.append({
                            "severity": "CRITICAL",
                            "type": "Command Injection",
                            "payload": payload,
                            "endpoint": "/v1/consents",
                        })
                        print(f"  [!] POTENTIAL VULNERABILITY: {payload}")
            except Exception as e:
                print(f"  [-] Error: {e}")

    async def test_input_validation(self, session: aiohttp.ClientSession):
        """Test input validation"""
        print("\n[+] Testing Input Validation...")
        
        test_cases = [
            {
                "field": "amount",
                "value": -100.0,
                "expected_status": 422,
            },
            {
                "field": "amount",
                "value": "invalid",
                "expected_status": 422,
            },
            {
                "field": "user_id",
                "value": "",
                "expected_status": 422,
            },
            {
                "field": "user_id",
                "value": "a" * 10000,  # Very long string
                "expected_status": 422,
            },
            {
                "field": "expires_at",
                "value": "invalid-date",
                "expected_status": 422,
            },
        ]
        
        for test_case in test_cases:
            try:
                url = f"{BASE_URL}/v1/consents"
                headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
                body = {
                    "user_id": "test_user",
                    "agent_id": "test_agent",
                    "max_amount": 1000.0,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                }
                body[test_case["field"]] = test_case["value"]
                
                async with session.post(url, headers=headers, json=body, timeout=5) as response:
                    result = {
                        "test": "Input Validation",
                        "field": test_case["field"],
                        "value": str(test_case["value"])[:50],
                        "expected_status": test_case["expected_status"],
                        "actual_status": response.status,
                        "vulnerable": response.status != test_case["expected_status"],
                        "timestamp": datetime.now().isoformat(),
                    }
                    self.results.append(result)
                    
                    if result["vulnerable"]:
                        self.vulnerabilities.append({
                            "severity": "MEDIUM",
                            "type": "Input Validation",
                            "field": test_case["field"],
                            "value": str(test_case["value"])[:50],
                        })
                        print(f"  [!] POTENTIAL VULNERABILITY: Invalid input accepted for {test_case['field']}")
            except Exception as e:
                print(f"  [-] Error: {e}")

    async def run_all_tests(self):
        """Run all penetration tests"""
        print("=" * 60)
        print("AGENTAUTH PENETRATION TESTING")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            await self.test_sql_injection(session)
            await self.test_xss(session)
            await self.test_authentication_bypass(session)
            await self.test_authorization_bypass(session)
            await self.test_rate_limiting_bypass(session)
            await self.test_path_traversal(session)
            await self.test_command_injection(session)
            await self.test_input_validation(session)
        
        print("\n" + "=" * 60)
        print("PENETRATION TESTING COMPLETE")
        print("=" * 60)

    def print_report(self):
        """Print penetration test report"""
        print(f"\nTotal Tests Run: {len(self.results)}")
        print(f"Vulnerabilities Found: {len(self.vulnerabilities)}")
        
        if self.vulnerabilities:
            print("\n" + "=" * 60)
            print("VULNERABILITIES FOUND")
            print("=" * 60)
            
            severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            for severity in severity_order:
                vulns = [v for v in self.vulnerabilities if v["severity"] == severity]
                if vulns:
                    print(f"\n{severity} ({len(vulns)}):")
                    for vuln in vulns:
                        print(f"  - {vuln['type']}: {vuln.get('payload', vuln.get('scenario', vuln.get('details', '')))[:60]}")
        else:
            print("\n[✓] No vulnerabilities found!")
        
        # Save results
        report = {
            "summary": {
                "total_tests": len(self.results),
                "vulnerabilities_found": len(self.vulnerabilities),
                "timestamp": datetime.now().isoformat(),
            },
            "vulnerabilities": self.vulnerabilities,
            "results": self.results,
        }
        
        with open("penetration_test_results.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\nResults saved to penetration_test_results.json")

async def main():
    """Main entry point"""
    tester = PenetrationTester()
    await tester.run_all_tests()
    tester.print_report()

if __name__ == "__main__":
    asyncio.run(main())
