import time
import sys
import requests

BASE_URL = "http://localhost:8000"

def wait_for_backend(timeout=30):
    start_time = time.time()
    print("Waiting for backend to be ready...")
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code in [200, 503]:
                print(f"Backend responded with status {response.status_code}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("Backend did not become ready in time.")
    return False

def test_health_endpoint():
    print("Testing /health ...", end="")
    response = requests.get(f"{BASE_URL}/health")
    
    # Because we injected a dummy GOOGLE_API_KEY into the CI environment, 
    # we expect our graceful degradation logic to mark the status as 'Degraded' 
    # but still return a 200 OK.
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert data['status'] == 'Degraded', f"Expected 'Degraded' status, got {data.get('status')}"
    assert data['components']['llm'] == 'missing_key', "LLM probe should be marked as missing_key"
    assert data['components']['database'] == 'reachable', "Database probe should be reachable"
    print(" PASSED")

def test_traces_endpoint():
    print("Testing /api/traces/ ...", end="")
    # Ensures database migrations ran and the application routing works
    response = requests.get(f"{BASE_URL}/api/traces/")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    print(" PASSED")

def test_analytics_endpoint():
    print("Testing /api/analytics/ ...", end="")
    response = requests.get(f"{BASE_URL}/api/analytics/")
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
    data = response.json()
    assert "total_traces" in data, "Missing 'total_traces' aggregation in response"
    print(" PASSED")

if __name__ == "__main__":
    print("Starting Phase 4 E2E Smoke Tests for CI Pipeline...")
    if not wait_for_backend():
        sys.exit(1)
        
    try:
        test_health_endpoint()
        test_traces_endpoint()
        test_analytics_endpoint()
        print("\nAll E2E smoke tests passed successfully! Containers are healthy and resilient.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nFAILED ASSERTION: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
