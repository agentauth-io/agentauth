#!/usr/bin/env python3
"""
AgentAuth Load Testing Script

Simulates production-like traffic to test:
- API performance under load
- Rate limiting effectiveness
- Database connection pooling
- Error handling
- Resource utilization
"""

import asyncio
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "aa_test_key_for_load_testing"
CONCURRENT_REQUESTS = 100
TOTAL_REQUESTS = 10000
TEST_DURATION_SECONDS = 60

# Endpoints to test
ENDPOINTS = [
    {"path": "/health", "method": "GET", "weight": 10},
    {"path": "/v1/consents", "method": "POST", "weight": 3},
    {"path": "/v1/authorize", "method": "POST", "weight": 5},
    {"path": "/v1/verify", "method": "POST", "weight": 5},
    {"path": "/v1/limits", "method": "GET", "weight": 2},
    {"path": "/v1/rules", "method": "GET", "weight": 2},
    {"path": "/v1/analytics", "method": "GET", "weight": 1},
]

class LoadTester:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    async def make_request(self, session: aiohttp.ClientSession, endpoint: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single API request"""
        url = f"{BASE_URL}{endpoint['path']}"
        headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
        
        # Prepare request body based on endpoint
        body = None
        if endpoint["method"] == "POST":
            if endpoint["path"] == "/v1/consents":
                body = {
                    "user_id": f"user_{random.randint(1, 1000)}",
                    "agent_id": f"agent_{random.randint(1, 100)}",
                    "max_amount": random.uniform(100, 10000),
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
                }
            elif endpoint["path"] == "/v1/authorize":
                body = {
                    "user_id": f"user_{random.randint(1, 1000)}",
                    "agent_id": f"agent_{random.randint(1, 100)}",
                    "merchant_id": f"merchant_{random.randint(1, 50)}",
                    "amount": random.uniform(10, 500),
                    "currency": "USD",
                }
            elif endpoint["path"] == "/v1/verify":
                body = {
                    "authorization_code": f"auth_code_{random.randint(1, 10000)}",
                    "merchant_id": f"merchant_{random.randint(1, 50)}",
                }

        start = time.time()
        try:
            async with session.request(
                endpoint["method"],
                url,
                headers=headers,
                json=body,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                duration = time.time() - start
                result = {
                    "endpoint": endpoint["path"],
                    "method": endpoint["method"],
                    "status": response.status,
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                }
                
                # Check for rate limiting
                if response.status == 429:
                    result["rate_limited"] = True
                    retry_after = response.headers.get("Retry-After", "0")
                    result["retry_after"] = retry_after
                
                return result
        except Exception as e:
            duration = time.time() - start
            return {
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "status": 0,
                "duration": duration,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_concurrent_requests(self, session: aiohttp.ClientSession, count: int):
        """Run multiple concurrent requests"""
        tasks = []
        for _ in range(count):
            # Select endpoint based on weight
            endpoint = random.choices(
                ENDPOINTS,
                weights=[e["weight"] for e in ENDPOINTS],
                k=1
            )[0]
            tasks.append(self.make_request(session, endpoint))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.errors.append({"error": str(result), "timestamp": datetime.now().isoformat()})
            else:
                self.results.append(result)

    async def run_load_test(self):
        """Run the full load test"""
        print(f"Starting load test...")
        print(f"Base URL: {BASE_URL}")
        print(f"Concurrent requests: {CONCURRENT_REQUESTS}")
        print(f"Total requests: {TOTAL_REQUESTS}")
        print(f"Test duration: {TEST_DURATION_SECONDS}s")
        print("-" * 60)
        
        self.start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            # Run requests in batches
            batch_size = CONCURRENT_REQUESTS
            num_batches = TOTAL_REQUESTS // batch_size
            
            for i in range(num_batches):
                if time.time() - self.start_time >= TEST_DURATION_SECONDS:
                    break
                
                await self.run_concurrent_requests(session, batch_size)
                
                # Progress update
                completed = len(self.results)
                elapsed = time.time() - self.start_time
                rate = completed / elapsed if elapsed > 0 else 0
                print(f"Progress: {completed}/{TOTAL_REQUESTS} requests | Rate: {rate:.0f} req/sec")
                
                # Small delay between batches
                await asyncio.sleep(0.01)
        
        self.end_time = time.time()
        print("-" * 60)
        print("Load test completed!")

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze the load test results"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        durations = [r["duration"] for r in self.results]
        status_codes = [r["status"] for r in self.results]
        
        # Calculate statistics
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if 200 <= r["status"] < 300)
        failed_requests = total_requests - successful_requests
        rate_limited = sum(1 for r in self.results if r.get("rate_limited", False))
        
        duration_stats = {
            "min": min(durations),
            "max": max(durations),
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "p95": statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations),
            "p99": statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else max(durations),
        }
        
        # Status code distribution
        status_distribution = {}
        for status in status_codes:
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Endpoint performance
        endpoint_stats = {}
        for endpoint in ENDPOINTS:
            path = endpoint["path"]
            endpoint_results = [r for r in self.results if r["endpoint"] == path]
            if endpoint_results:
                endpoint_durations = [r["duration"] for r in endpoint_results]
                endpoint_stats[path] = {
                    "count": len(endpoint_results),
                    "mean_duration": statistics.mean(endpoint_durations),
                    "p95_duration": statistics.quantiles(endpoint_durations, n=20)[18] if len(endpoint_durations) >= 20 else max(endpoint_durations),
                }
        
        # Calculate throughput
        elapsed_time = self.end_time - self.start_time
        throughput = total_requests / elapsed_time if elapsed_time > 0 else 0
        
        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "rate_limited": rate_limited,
                "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                "throughput": throughput,
                "elapsed_time": elapsed_time,
            },
            "duration_stats": duration_stats,
            "status_distribution": status_distribution,
            "endpoint_stats": endpoint_stats,
            "errors": self.errors[:10],  # First 10 errors
        }

    def print_report(self, analysis: Dict[str, Any]):
        """Print a formatted report"""
        print("\n" + "=" * 60)
        print("LOAD TEST REPORT")
        print("=" * 60)
        
        summary = analysis["summary"]
        print(f"\nSummary:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Successful: {summary['successful_requests']} ({summary['success_rate']:.1f}%)")
        print(f"  Failed: {summary['failed_requests']}")
        print(f"  Rate Limited: {summary['rate_limited']}")
        print(f"  Throughput: {summary['throughput']:.0f} req/sec")
        print(f"  Elapsed Time: {summary['elapsed_time']:.2f}s")
        
        duration = analysis["duration_stats"]
        print(f"\nResponse Times (seconds):")
        print(f"  Min: {duration['min']:.4f}s")
        print(f"  Max: {duration['max']:.4f}s")
        print(f"  Mean: {duration['mean']:.4f}s")
        print(f"  Median: {duration['median']:.4f}s")
        print(f"  P95: {duration['p95']:.4f}s")
        print(f"  P99: {duration['p99']:.4f}s")
        
        print(f"\nStatus Code Distribution:")
        for status, count in sorted(analysis["status_distribution"].items()):
            percentage = (count / summary['total_requests'] * 100)
            print(f"  {status}: {count} ({percentage:.1f}%)")
        
        print(f"\nEndpoint Performance:")
        for path, stats in analysis["endpoint_stats"].items():
            print(f"  {path}:")
            print(f"    Count: {stats['count']}")
            print(f"    Mean: {stats['mean_duration']:.4f}s")
            print(f"    P95: {stats['p95_duration']:.4f}s")
        
        if analysis["errors"]:
            print(f"\nErrors (first 10):")
            for error in analysis["errors"]:
                print(f"  - {error}")
        
        print("\n" + "=" * 60)

async def main():
    """Main entry point"""
    tester = LoadTester()
    await tester.run_load_test()
    analysis = tester.analyze_results()
    tester.print_report(analysis)
    
    # Save results to file
    with open("load_test_results.json", "w") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nResults saved to load_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
