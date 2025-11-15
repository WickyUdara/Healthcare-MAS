#!/usr/bin/env python3
"""
Demo script for Hospital Bed Management MAS
Simulates the complete workflow: admission → assignment → discharge → cleaning → auto-assign
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Patient test data
TEST_PATIENTS = [
    {
        "name": "Alice Smith",
        "age": 45,
        "gender": "Female",
        "symptoms": "Fever, body aches",
        "heart_rate": 88,
        "blood_pressure": "120/80",
        "oxygen_saturation": 98,
        "is_emergency": False,
        "preferred_ward": "GENERAL",
    },
    {
        "name": "Bob Johnson",
        "age": 72,
        "gender": "Male",
        "symptoms": "Severe chest pain, shortness of breath",
        "heart_rate": 105,
        "blood_pressure": "160/100",
        "oxygen_saturation": 90,
        "is_emergency": True,
        "preferred_ward": "ICU",
    },
    {
        "name": "Carol Williams",
        "age": 35,
        "gender": "Female",
        "symptoms": "Broken arm, laceration",
        "heart_rate": 75,
        "blood_pressure": "115/75",
        "oxygen_saturation": 99,
        "is_emergency": False,
        "preferred_ward": "GENERAL",
    },
]


def log_step(step_num, title, details=""):
    """Print a formatted step."""
    print(f"\n{'=' * 70}")
    print(f"STEP {step_num}: {title}")
    print(f"{'=' * 70}")
    if details:
        print(details)


def wait_input(msg="Press Enter to continue..."):
    """Wait for user input."""
    input(f"\n⏸️  {msg}")


def check_api():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✓ API is running and healthy")
            return True
    except Exception as e:
        print(f"✗ API is not responding: {e}")
        return False


def admit_patients():
    """Admit multiple test patients."""
    print("\n📋 ADMITTING TEST PATIENTS...")
    admitted = []
    
    for i, patient_data in enumerate(TEST_PATIENTS, 1):
        print(f"\n  {i}. Admitting {patient_data['name']}...")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/admit",
                json=patient_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                admitted.append(result)
                
                status = result['status'].upper()
                severity = result['severity_score']
                bed_info = f"Bed: {result['assigned_bed']}" if result['assigned_bed'] else "Waiting List"
                
                print(f"    ✓ {status} | Severity: {severity:.0f}/100 | {bed_info}")
                print(f"    TX ID: {result['transaction_id'][:12]}...")
                
            else:
                print(f"    ✗ Error: {response.text}")
                
        except Exception as e:
            print(f"    ✗ Exception: {e}")
        
        time.sleep(1)  # Small delay between admissions
    
    return admitted


def get_occupancy():
    """Get current occupancy metrics."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            metrics = response.json()
            print(f"  Total Beds: {metrics['total_beds']}")
            print(f"  Occupied: {metrics['occupied']}")
            print(f"  Available: {metrics['available']}")
            print(f"  Cleaning: {metrics['cleaning']}")
            print(f"  Occupancy Rate: {metrics['occupancy_rate']*100:.1f}%")
            
            print("\n  By Ward:")
            for ward, data in metrics['by_ward'].items():
                print(f"    {ward}: {data['occupied']}/{data['total']} occupied ({data['occupancy_rate']*100:.0f}%)")
            
            return metrics
    except Exception as e:
        print(f"  Error fetching metrics: {e}")
    
    return None


def get_waiting_list():
    """Get current waiting list."""
    try:
        response = requests.get(f"{API_BASE_URL}/waiting_list", timeout=5)
        if response.status_code == 200:
            waiting = response.json()
            print(f"  Total Waiting: {len(waiting)}")
            for item in waiting[:5]:
                print(f"    #{item['position']}: {item['patient_name']} (severity {item['severity']:.0f})")
            return waiting
    except Exception as e:
        print(f"  Error fetching waiting list: {e}")
    
    return None


def discharge_patient(patient_id):
    """Discharge a patient."""
    try:
        response = requests.post(f"{API_BASE_URL}/discharge/{patient_id}", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Discharge initiated for {result['patient_name']}")
            print(f"    Status: {result['status']}")
            print(f"    Message: {result['message']}")
            return result
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return None


def run_demo():
    """Run the complete demo workflow."""
    
    print("\n" + "=" * 70)
    print("🏥 HOSPITAL BED MANAGEMENT MAS - DEMO")
    print("=" * 70)
    
    # Check API
    log_step(1, "Check API Health")
    if not check_api():
        print("\n✗ Cannot proceed: API is not running")
        print("  Start the backend with: python backend/main.py")
        return
    
    # Show initial state
    log_step(2, "Initial System State")
    print("\nCurrent Occupancy:")
    get_occupancy()
    
    wait_input("Ready to admit 3 test patients?")
    
    # Admit patients
    log_step(3, "Admit Test Patients", 
             f"Will admit {len(TEST_PATIENTS)} patients with varying severities")
    admitted = admit_patients()
    
    if not admitted:
        print("\n✗ No patients admitted successfully")
        return
    
    wait_input("Patients admitted. Check Activity Log page to see messages. Continue?")
    
    # Check occupancy after admission
    log_step(4, "Post-Admission System State")
    print("\nCurrent Occupancy After Admission:")
    metrics = get_occupancy()
    
    print("\nWaiting List:")
    waiting = get_waiting_list()
    
    # Find an admitted patient to discharge
    admitted_patients = [p for p in admitted if p['status'] == 'admitted']
    
    if admitted_patients:
        # Get patient IDs from first admitted
        first_admitted = admitted_patients[0]
        print(f"\n  Will discharge first admitted patient: {first_admitted['patient_name']}")
        
        wait_input("Ready to discharge and trigger cleaning cycle?")
        
        log_step(5, "Discharge & Cleaning Cycle",
                "Patient discharge → Bed cleaning (10s simulation) → Bed available")
        
        # Discharge
        print("\nDischarging patient...")
        discharge_result = discharge_patient(first_admitted['patient_id'])
        
        if discharge_result:
            print(f"\n⏳ Bed is now in CLEANING state (10 second simulation)...")
            
            # Monitor cleaning progress
            for i in range(11):
                print(f"  Cleaning progress: {i}/10 seconds", end="\r")
                time.sleep(1)
            
            print(f"  Cleaning complete! ✓                         ")
            
            wait_input("Cleaning complete. Bed should now be available. Check for auto-assignment?")
            
            log_step(6, "Post-Discharge System State",
                    "Auto-assignment should have triggered")
            
            print("\nCurrent Occupancy After Cleaning:")
            get_occupancy()
            
            print("\nUpdated Waiting List:")
            get_waiting_list()
            
            print("\n✓ Auto-assignment may have occurred!")
            print("  Check Bed Assignment page for updated assignments")
            print("  Check Activity Log page to see all agent messages")
    else:
        print("  No admitted patients to discharge (all on waiting list)")
    
    # Final instructions
    log_step(7, "Demo Complete!",
            "Recommended next steps:")
    print("""
1. Open http://localhost:5173 in your browser (Frontend)

2. Visit each page to see different aspects:
   - Bed Assignment: View all beds and occupancy
   - Activity Log: See all agent communications and sequence diagrams
   - Dashboard: View metrics and charts
   - Cleaning & Turnaround: Monitor bed cleaning progress

3. To see sequence diagrams:
   - Go to Activity Log page
   - Click a transaction ID to expand
   - View the Mermaid sequence diagram

4. Key points to highlight for viva:
   - Agent communication via FIPA-like messages
   - Negotiation loops in Coordinator
   - Auto-assignment from waiting list
   - 10-second cleaning simulation
   - Message tracking for audit trail
   - Severity-based prioritization
    """)
    
    wait_input("Press Enter to end demo")
    print("\n✓ Demo Complete!\n")


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n✗ Demo interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
