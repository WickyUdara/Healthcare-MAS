import requests
import time

base_url = "http://localhost:8000"

print("Testing Admission Workflow with Data Persistence\n")
print("=" * 60)

# Admit a patient
print("\nStep 1: Admitting a patient...")
admission_data = {
    "name": "Emergency Patient",
    "age": 58,
    "gender": "Male",
    "symptoms": "Severe chest pain and difficulty breathing",
    "heart_rate": 110,
    "blood_pressure": "160/95",
    "oxygen_saturation": 88,
    "is_emergency": True,
    "preferred_ward": "ICU"
}

try:
    resp = requests.post(f"{base_url}/admit", json=admission_data)
    if resp.status_code == 200:
        result = resp.json()
        print(f"✓ Patient admitted: {result['patient_name']} (ID: {result['patient_id']})")
        print(f"  - Status: {result['status']}")
        print(f"  - Assigned Bed: {result['assigned_bed']}")
        print(f"  - Severity: {result['severity_score']:.0f}/100")
    else:
        print(f"✗ Failed: {resp.status_code}")
        print(f"  Response: {resp.json()}")
except Exception as e:
    print(f"✗ Error: {e}")

# Small delay for database operations
time.sleep(1)

# Check waiting list
print("\nStep 2: Checking waiting list...")
try:
    resp = requests.get(f"{base_url}/waiting_list")
    waiting = resp.json()
    print(f"✓ Waiting list: {len(waiting)} patients")
    if waiting:
        for entry in waiting[:3]:
            print(f"  - Position {entry['position']}: {entry['patient_name']} (severity {entry['severity']})")
except Exception as e:
    print(f"✗ Error: {e}")

# Check activity log
print("\nStep 3: Checking activity log...")
try:
    resp = requests.get(f"{base_url}/activity_log?limit=50")
    activities = resp.json()
    print(f"✓ Activity log: {len(activities)} entries")
    if activities:
        for entry in activities[-3:]:
            print(f"  - {entry['sender']} → {entry['receiver']}: {entry['performative']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Check beds
print("\nStep 4: Checking bed status...")
try:
    resp = requests.get(f"{base_url}/beds")
    beds = resp.json()
    occupied = [b for b in beds if b['status'] == 'occupied']
    available = [b for b in beds if b['status'] == 'available']
    print(f"✓ Beds: {len(occupied)} occupied, {len(available)} available")
    if occupied:
        for bed in occupied[:2]:
            print(f"  - {bed['bed_number']}: Patient ID {bed['current_patient_id']}")
except Exception as e:
    print(f"✗ Error: {e}")

# Check metrics
print("\nStep 5: Checking metrics...")
try:
    resp = requests.get(f"{base_url}/metrics")
    metrics = resp.json()
    print(f"✓ Occupancy: {metrics['occupied']}/{metrics['total_beds']} beds")
    print(f"  - Occupancy rate: {metrics['occupancy_rate']*100:.1f}%")
    print(f"  - Patients waiting: {metrics['patients']['waiting']}")
    print(f"  - Patients admitted: {metrics['patients']['admitted']}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
