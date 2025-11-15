import requests
import time

base_url = "http://localhost:8000"

print("Testing Waiting List - Multiple Admissions\n")
print("=" * 60)

# Admit 21 patients (more than available beds)
for i in range(5):
    print(f"\nAdmitting patient {i+1}...")
    admission_data = {
        "name": f"Patient {i+13}",
        "age": 50 + i,
        "gender": "Male" if i % 2 == 0 else "Female",
        "symptoms": "General checkup" if i % 2 == 0 else "Fever",
        "heart_rate": 70 + (i * 2),
        "blood_pressure": f"120/{80 + i}",
        "oxygen_saturation": 95 - (i * 0.5),
        "is_emergency": i == 0,  # First one is emergency
        "preferred_ward": ["ICU", "GENERAL", "SURGERY", "MATERNITY"][i % 4]
    }
    
    try:
        resp = requests.post(f"{base_url}/admit", json=admission_data)
        if resp.status_code == 200:
            result = resp.json()
            print(f"  ✓ {result['patient_name']}")
            print(f"    Status: {result['status']}", end="")
            if result['assigned_bed']:
                print(f", Bed: {result['assigned_bed']}")
            else:
                print(f", Position: {result['waiting_list_position']}")
        else:
            print(f"  ✗ Failed: {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    time.sleep(0.5)

# Check final status
print("\n" + "=" * 60)
print("\nFinal Status:\n")

# Waiting list
try:
    resp = requests.get(f"{base_url}/waiting_list")
    waiting = resp.json()
    print(f"Waiting List: {len(waiting)} patients")
    for entry in waiting[:5]:
        print(f"  - {entry['patient_name']}: position {entry['position']}, severity {entry['severity']}")
except Exception as e:
    print(f"Error: {e}")

# Beds
try:
    resp = requests.get(f"{base_url}/beds")
    beds = resp.json()
    occupied = [b for b in beds if b['status'] == 'occupied']
    print(f"\nBeds: {len(occupied)}/20 occupied")
    for bed in occupied:
        print(f"  - {bed['bed_number']}: Patient ID {bed['current_patient_id']}")
except Exception as e:
    print(f"Error: {e}")

# Activity log
try:
    resp = requests.get(f"{base_url}/activity_log")
    activities = resp.json()
    print(f"\nActivity Log: {len(activities)} entries")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
