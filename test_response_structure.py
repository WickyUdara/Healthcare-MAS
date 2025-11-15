import requests

base_url = "http://localhost:8000"

print("Testing API Response Structures:\n")

# Test beds
resp = requests.get(f"{base_url}/beds")
print(f"Beds Response Type: {type(resp.json())}")
print(f"Beds Response: {resp.json()}\n")

# Test patients
resp = requests.get(f"{base_url}/patients")
print(f"Patients Response Type: {type(resp.json())}")
print(f"Patients Response: {resp.json()}\n")

# Test waiting list
resp = requests.get(f"{base_url}/waiting_list")
print(f"Waiting List Response Type: {type(resp.json())}")
print(f"Waiting List Response: {resp.json()}\n")

# Test activity log
resp = requests.get(f"{base_url}/activity_log")
print(f"Activity Log Response Type: {type(resp.json())}")
print(f"Activity Log Length: {len(resp.json())}\n")
