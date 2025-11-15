import requests

base_url = "http://localhost:8000"

print("Frontend Data Display Test\n")
print("=" * 60)

# Test each page's required data

pages_tests = {
    "Home": {
        "endpoint": "/config",
        "description": "Static page - no API needed"
    },
    "Admission": {
        "endpoint": "/config", 
        "description": "Form page - displays OK after fix"
    },
    "BedAssignment": {
        "endpoints": ["/beds", "/patients", "/waiting_list", "/activity_log?limit=15"],
        "description": "Requires: Beds, Patients, Waiting List, Activity Log"
    },
    "Discharge": {
        "endpoint": "/patients",
        "description": "Requires: Patients list"
    },
    "ActivityLog": {
        "endpoint": "/activity_log",
        "description": "Requires: Activity log entries"
    },
    "Dashboard": {
        "endpoints": ["/metrics", "/patients", "/waiting_list", "/beds"],
        "description": "Requires: Metrics, Patients, Waiting List, Beds"
    },
    "CleaningTurnaround": {
        "endpoint": "/metrics",
        "description": "Requires: Metrics (bed statuses)"
    }
}

for page_name, test_info in pages_tests.items():
    print(f"\n{page_name}:")
    print(f"  Description: {test_info['description']}")
    
    endpoints = test_info.get("endpoints", [test_info.get("endpoint")])
    if isinstance(endpoints, str):
        endpoints = [endpoints]
    
    for endpoint in endpoints:
        try:
            resp = requests.get(f"{base_url}{endpoint}")
            data = resp.json()
            
            if isinstance(data, list):
                count = len(data)
                status = "✓" if count > 0 else "⚠" 
                print(f"  {status} {endpoint:30s} -> {count} items")
            elif isinstance(data, dict):
                keys = len(data)
                status = "✓" if keys > 0 else "⚠"
                print(f"  {status} {endpoint:30s} -> dict with {keys} keys")
            else:
                print(f"  ✓ {endpoint:30s} -> {type(data).__name__}")
        except Exception as e:
            print(f"  ✗ {endpoint:30s} -> ERROR: {str(e)[:30]}")

print("\n" + "=" * 60)
print("\n⚠️  Note: Waiting List and Activity Log are empty because workflows")
print("    don't persist to database tables yet (backend issue, not frontend)")
