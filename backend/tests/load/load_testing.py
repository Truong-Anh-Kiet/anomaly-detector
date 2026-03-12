"""Load testing script for Phase 9 performance testing"""

import asyncio
import time
import requests
import json
import statistics
from typing import List, Dict
from datetime import datetime
import concurrent.futures


class LoadTestConfig:
    """Configuration for load testing"""
    
    BASE_URL = "http://localhost:8000"
    
    # Test parameters
    NUM_USERS = 10
    NUM_REQUESTS_PER_USER = 100
    CONCURRENT_USERS = 5
    
    # Endpoints to test
    ENDPOINTS = {
        "GET_HEALTH": ("GET", "/health"),
        "GET_USERS": ("GET", "/users?skip=0&limit=10"),
        "GET_CATEGORIES": ("GET", "/categories?skip=0&limit=10"),
        "GET_ANOMALIES": ("GET", "/anomalies?skip=0&limit=10"),
        "GET_AUDIT_LOGS": ("GET", "/audit-logs?skip=0&limit=10"),
        "WS_STATS": ("GET", "/ws/stats"),
        "WS_HEALTH": ("GET", "/ws/health"),
    }


class LoadTestMetrics:
    """Container for test metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.errors: List[str] = []
        self.success_count: int = 0
        self.failure_count: int = 0
        self.endpoint_metrics: Dict[str, Dict] = {}
    
    def add_response_time(self, endpoint: str, response_time: float, status_code: int):
        """Record a response time"""
        self.response_times.append(response_time)
        
        if endpoint not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint] = {
                "times": [],
                "status_codes": {},
                "success": 0,
                "failure": 0
            }
        
        self.endpoint_metrics[endpoint]["times"].append(response_time)
        
        status_key = str(status_code)
        if status_key not in self.endpoint_metrics[endpoint]["status_codes"]:
            self.endpoint_metrics[endpoint]["status_codes"][status_key] = 0
        self.endpoint_metrics[endpoint]["status_codes"][status_key] += 1
        
        if 200 <= status_code < 300:
            self.success_count += 1
            self.endpoint_metrics[endpoint]["success"] += 1
        else:
            self.failure_count += 1
            self.endpoint_metrics[endpoint]["failure"] += 1
    
    def add_error(self, endpoint: str, error: str):
        """Record an error"""
        self.errors.append(f"{endpoint}: {error}")
        self.failure_count += 1
        
        if endpoint not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint] = {
                "times": [],
                "status_codes": {},
                "success": 0,
                "failure": 0
            }
        self.endpoint_metrics[endpoint]["failure"] += 1
    
    def get_summary(self) -> Dict:
        """Get summary statistics"""
        if not self.response_times:
            return {
                "total_requests": 0,
                "status": "NO_DATA"
            }
        
        return {
            "total_requests": self.success_count + self.failure_count,
            "successful": self.success_count,
            "failed": self.failure_count,
            "success_rate": f"{(self.success_count / (self.success_count + self.failure_count) * 100):.2f}%",
            "avg_response_time": f"{statistics.mean(self.response_times):.3f}s",
            "median_response_time": f"{statistics.median(self.response_times):.3f}s",
            "min_response_time": f"{min(self.response_times):.3f}s",
            "max_response_time": f"{max(self.response_times):.3f}s",
            "std_dev": f"{statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0:.3f}s" if len(self.response_times) > 1 else "N/A",
            "errors": len(self.errors),
        }


class APILoadTester:
    """Load tester for API endpoints"""
    
    def __init__(self, config: LoadTestConfig = None):
        self.config = config or LoadTestConfig()
        self.metrics = LoadTestMetrics()
        self.session = requests.Session()
    
    def make_request(self, method: str, endpoint: str, timeout: float = 5.0) -> tuple:
        """Make a single HTTP request"""
        url = f"{self.config.BASE_URL}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(url, timeout=timeout)
            elif method == "POST":
                response = self.session.post(url, json={}, timeout=timeout)
            elif method == "PUT":
                response = self.session.put(url, json={}, timeout=timeout)
            else:
                return None, None
            
            response_time = time.time() - start_time
            return response.status_code, response_time
            
        except requests.exceptions.Timeout:
            return None, None
        except requests.exceptions.ConnectionError:
            return None, None
        except Exception as e:
            return None, None
    
    def test_single_endpoint(self, endpoint_name: str, num_requests: int = 100):
        """Test a single endpoint with multiple requests"""
        method, path = self.config.ENDPOINTS[endpoint_name]
        
        print(f"\nTesting {endpoint_name}...")
        
        for i in range(num_requests):
            status_code, response_time = self.make_request(method, path)
            
            if status_code is not None:
                self.metrics.add_response_time(endpoint_name, response_time, status_code)
                if i % 10 == 0:
                    print(f"  {i}/{num_requests} requests completed")
            else:
                self.metrics.add_error(endpoint_name, "Connection failed or timeout")
    
    def test_all_endpoints(self, num_requests: int = 10):
        """Test all configured endpoints"""
        print("=" * 60)
        print("API LOAD TEST STARTING")
        print("=" * 60)
        print(f"Base URL: {self.config.BASE_URL}")
        print(f"Requests per endpoint: {num_requests}")
        print(f"Total endpoints: {len(self.config.ENDPOINTS)}")
        print()
        
        for endpoint_name in self.config.ENDPOINTS:
            self.test_single_endpoint(endpoint_name, num_requests)
        
        self.print_results()
    
    def print_results(self):
        """Print test results"""
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        
        summary = self.metrics.get_summary()
        
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']}")
        print()
        print("Response Time Statistics:")
        print(f"  Average: {summary['avg_response_time']}")
        print(f"  Median: {summary['median_response_time']}")
        print(f"  Min: {summary['min_response_time']}")
        print(f"  Max: {summary['max_response_time']}")
        if summary.get('std_dev') != 'N/A':
            print(f"  Std Dev: {summary['std_dev']}")
        print()
        
        print("Endpoint Breakdown:")
        for endpoint, metrics in self.metrics.endpoint_metrics.items():
            if metrics['times']:
                avg_time = statistics.mean(metrics['times'])
                print(f"  {endpoint}:")
                print(f"    Requests: {metrics['success'] + metrics['failure']}")
                print(f"    Success: {metrics['success']}")
                print(f"    Failed: {metrics['failure']}")
                print(f"    Avg Response Time: {avg_time:.3f}s")
                print(f"    Status Codes: {metrics['status_codes']}")
        
        if self.metrics.errors:
            print()
            print("Errors (first 10):")
            for error in self.metrics.errors[:10]:
                print(f"  - {error}")


class ConcurrencyLoadTester:
    """Load tester for concurrent request handling"""
    
    def __init__(self, config: LoadTestConfig = None):
        self.config = config or LoadTestConfig()
        self.metrics = LoadTestMetrics()
    
    def make_request_worker(self, endpoint_name: str, num_requests: int):
        """Worker function for concurrent requests"""
        method, path = self.config.ENDPOINTS[endpoint_name]
        url = f"{self.config.BASE_URL}{path}"
        
        times = []
        for _ in range(num_requests):
            try:
                start = time.time()
                if method == "GET":
                    response = requests.get(url, timeout=5)
                response_time = time.time() - start
                
                self.metrics.add_response_time(endpoint_name, response_time, response.status_code)
                times.append(response_time)
            except Exception as e:
                self.metrics.add_error(endpoint_name, str(e))
        
        return times
    
    def run_concurrent_test(self, endpoint_name: str, num_concurrent: int = 5, requests_each: int = 20):
        """Run concurrent requests to an endpoint"""
        print(f"\nConcurrency Test: {endpoint_name}")
        print(f"Concurrent Users: {num_concurrent}")
        print(f"Requests per user: {requests_each}")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(self.make_request_worker, endpoint_name, requests_each)
                for _ in range(num_concurrent)
            ]
            
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        
        print(f"Completed in {total_time:.2f}s")
        print(f"Total requests: {num_concurrent * requests_each}")
        print(f"Requests per second: {(num_concurrent * requests_each) / total_time:.2f}")
    
    def print_results(self):
        """Print concurrency test results"""
        print("\n" + "=" * 60)
        print("CONCURRENCY TEST RESULTS")
        print("=" * 60)
        
        summary = self.metrics.get_summary()
        
        print(f"Total Requests: {summary['total_requests']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Average Response Time: {summary['avg_response_time']}")
        print(f"Max Response Time: {summary['max_response_time']}")


class StressTest:
    """Stress test for system limits"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.metrics = LoadTestMetrics()
    
    def test_increasing_load(self, endpoint: str = "/health", max_concurrent: int = 50):
        """Test with increasing concurrent load"""
        print("\n" + "=" * 60)
        print("STRESS TEST - INCREASING LOAD")
        print("=" * 60)
        
        url = f"{self.base_url}{endpoint}"
        
        for num_concurrent in [5, 10, 20, 30, 40, 50]:
            print(f"\nTesting with {num_concurrent} concurrent connections...")
            
            start = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
                futures = [
                    executor.submit(self._single_request, url)
                    for _ in range(num_concurrent)
                ]
                
                results = [f.result() for f in concurrent.futures.as_completed(futures)]
            
            elapsed = time.time() - start
            success_count = len([r for r in results if r[0] == 200])
            
            print(f"  Completed: {num_concurrent} requests in {elapsed:.2f}s")
            print(f"  Success: {success_count}/{num_concurrent}")
            print(f"  Avg time: {statistics.mean([r[1] for r in results if r[1]]):.3f}s")
    
    def _single_request(self, url: str) -> tuple:
        """Make a single request and return (status_code, response_time)"""
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            return (response.status_code, elapsed)
        except Exception as e:
            return (None, None)


def run_load_tests():
    """Run all load tests"""
    
    print("\n🚀 Starting Anomaly Detector Load Test Suite\n")
    
    # Test 1: API Load Test
    print("TEST 1: API Endpoint Load Testing")
    api_tester = APILoadTester()
    api_tester.test_all_endpoints(num_requests=20)
    
    # Test 2: Concurrency Test
    print("\n\nTEST 2: Concurrency Testing")
    concurrency_tester = ConcurrencyLoadTester()
    for endpoint in ["GET_HEALTH", "GET_USERS", "WS_STATS"]:
        concurrency_tester.run_concurrent_test(endpoint, num_concurrent=5, requests_each=10)
    concurrency_tester.print_results()
    
    # Test 3: Stress Test
    print("\n\nTEST 3: Stress Testing")
    stress_tester = StressTest()
    stress_tester.test_increasing_load(endpoint="/health", max_concurrent=30)
    
    print("\n" + "=" * 60)
    print("LOAD TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_load_tests()
