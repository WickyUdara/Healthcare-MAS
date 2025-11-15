import requests

base_url = "http://localhost:8000"

# Admit a patient
admission_data = {
    "name": "Test Patient",
    "age": 55,
    "gender": "Male",
    "medical_condition": "Fever and cough",
    "severity_score": 60
}

print("Admitting patient...")
resp = requests.post(f"{base_url}/admit", json=admission_data)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}\n")

# Check activity log
print("Checking activity log...")
resp = requests.get(f"{base_url}/activity_log")
activities = resp.json()
print(f"Total activities: {len(activities)}")
if activities:
    print(f"Latest activity: {activities[-1]}\n")

# Check waiting list
print("Checking waiting list...")
resp = requests.get(f"{base_url}/waiting_list")
waiting = resp.json()
print(f"Waiting patients: {len(waiting)}")
if waiting:
    print(f"Sample: {waiting[0]}\n")

# Check beds
print("Checking beds...")
resp = requests.get(f"{base_url}/beds")
beds = resp.json()
occupied = [b for b in beds if b['status'] == 'occupied']
print(f"Occupied beds: {len(occupied)}")
if occupied:
    print(f"Sample occupied: {occupied[0]}")
