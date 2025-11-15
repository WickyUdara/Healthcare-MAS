import requests
import json

base_url = "http://localhost:8000"

print("Testing Frontend API Calls\n")
print("=" * 50)

# Test 1: Get Beds (for BedAssignment page)
print("\n1. GET /beds")
try:
    resp = requests.get(f"{base_url}/beds")
    beds = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(beds).__name__}")
    print(f"   Count: {len(beds)}")
    print(f"   Sample: {beds[0] if beds else 'No data'}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: Get Patients (for multiple pages)
print("\n2. GET /patients")
try:
    resp = requests.get(f"{base_url}/patients")
    patients = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(patients).__name__}")
    print(f"   Count: {len(patients)}")
    print(f"   Sample: {patients[0] if patients else 'No data'}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Get Waiting List (for BedAssignment page)
print("\n3. GET /waiting_list")
try:
    resp = requests.get(f"{base_url}/waiting_list")
    waiting = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(waiting).__name__}")
    print(f"   Count: {len(waiting)}")
    print(f"   Data: {waiting}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 4: Get Activity Log (for AgentActivityLog page)
print("\n4. GET /activity_log?limit=100")
try:
    resp = requests.get(f"{base_url}/activity_log?limit=100")
    activity = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(activity).__name__}")
    print(f"   Count: {len(activity)}")
    print(f"   Data: {activity}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 5: Get Metrics (for Dashboard page)
print("\n5. GET /metrics")
try:
    resp = requests.get(f"{base_url}/metrics")
    metrics = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(metrics).__name__}")
    print(f"   Keys: {list(metrics.keys()) if isinstance(metrics, dict) else 'Not a dict'}")
    print(f"   Sample: {json.dumps(metrics, indent=2, default=str)[:200]}...")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 6: Get Config (for app setup)
print("\n6. GET /config")
try:
    resp = requests.get(f"{base_url}/config")
    config = resp.json()
    print(f"   Status: {resp.status_code}")
    print(f"   Type: {type(config).__name__}")
    print(f"   Data: {config}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 50)
print("API Test Complete")
