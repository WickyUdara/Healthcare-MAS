import requests

base_url = "http://localhost:8000"
endpoints = ["health", "beds", "patients", "waiting_list", "activity_log", "metrics", "config"]

print("Testing API Endpoints:\n")
for endpoint in endpoints:
    try:
        response = requests.get(f"{base_url}/{endpoint}")
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} {endpoint:20s} -> {response.status_code}")
        if response.status_code == 200 and endpoint in ["waiting_list", "activity_log"]:
            data = response.json()
            count = len(data) if isinstance(data, list) else 1
            print(f"   └─ Records: {count}")
    except Exception as e:
        print(f"✗ {endpoint:20s} -> ERROR: {str(e)}")
