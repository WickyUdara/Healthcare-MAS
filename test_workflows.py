import requests
import json

base_url = "http://localhost:8000"

print("Testing Full Hospital Workflows\n")
print("=" * 60)

# Step 1: Admit a patient to generate activity and waiting list
print("\nStep 1: Admitting a patient...")
admission_data = {
    "name": "Alice Johnson",
    "age": 55,
    "gender": "Female",
    "symptoms": "Severe abdominal pain",
    "heart_rate": 105,
    "blood_pressure": "140/85",
    "oxygen_saturation": 95,
    "is_emergency": True,
    "preferred_ward": "GENERAL"
}
try:
    resp = requests.post(f"{base_url}/admit", json=admission_data)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✓ Patient admitted: {result['patient_name']}")
        print(f"  - ID: {result['patient_id']}")
        print(f"  - Status: {result['status']}")
        print(f"  - Severity: {result['severity_score']}")
        patient_id = result['patient_id']
    else:
        print(f"✗ Failed: {resp.status_code}")
        print(f"  Response: {resp.json()}")
        patient_id = None
except Exception as e:
    print(f"✗ Error: {e}")
    patient_id = None

# Step 2: Check waiting list
print("\nStep 2: Checking waiting list...")
try:
    resp = requests.get(f"{base_url}/waiting_list")
    waiting = resp.json()
    print(f"✓ Waiting list count: {len(waiting)}")
    if waiting:
        print(f"  - Sample: {waiting[0]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Step 3: Check activity log
print("\nStep 3: Checking activity log...")
try:
    resp = requests.get(f"{base_url}/activity_log?limit=50")
    activities = resp.json()
    print(f"✓ Activity log entries: {len(activities)}")
    if activities:
        print(f"  - Latest: {activities[-1]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Step 4: Check metrics
print("\nStep 4: Checking metrics...")
try:
    resp = requests.get(f"{base_url}/metrics")
    metrics = resp.json()
    print(f"✓ Metrics retrieved")
    print(f"  - Total beds: {metrics['total_beds']}")
    print(f"  - Occupied: {metrics['occupied']}")
    print(f"  - Available: {metrics['available']}")
    print(f"  - Occupancy rate: {metrics['occupancy_rate']*100:.1f}%")
    print(f"  - Patients total: {metrics['patients']['total']}")
    print(f"  - Patients waiting: {metrics['patients']['waiting']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Step 5: Run assignment cycle
print("\nStep 5: Running assignment cycle...")
try:
    resp = requests.post(f"{base_url}/run_assignment_cycle")
    if resp.status_code == 200:
        result = resp.json()
        print(f"✓ Assignment cycle completed")
        print(f"  - Assigned: {result.get('assigned_count', 0)}")
    else:
        print(f"✗ Failed: {resp.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Step 6: Check beds after assignment
print("\nStep 6: Checking beds after assignment...")
try:
    resp = requests.get(f"{base_url}/beds")
    beds = resp.json()
    occupied = [b for b in beds if b['status'] == 'occupied']
    print(f"✓ Beds update: {len(occupied)}/{len(beds)} occupied")
    if occupied:
        print(f"  - Sample occupied: {occupied[0]}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Workflow Test Complete")
