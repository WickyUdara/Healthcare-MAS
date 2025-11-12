from model import HospitalState, BedStatus, WardType, Patient, CleaningTeam, Ward
from typing import Dict, Any

# Note the new type hint: state: HospitalState
def admissions_agent(state: HospitalState) -> Dict[str, Any]:
    """Picks the next patient from the waiting list to process."""
    
    # Use dot notation: state.log
    state.log.append("--- Admissions Agent finding next patient ---")
    
    # Use dot notation: state.waiting_patients
    if not state.waiting_patients:
        state.log.append("No patients in waiting list.")
        # Return only the keys that changed
        return {"current_patient_request": None, "log": state.log}

    # Get the next patient (it's already a Patient object)
    next_patient = state.waiting_patients.pop(0)
    
    state.log.append(f"Processing {next_patient.name} (ID: {next_patient.patient_id})")
    
    # Return a dictionary of the changes
    return {
        "current_patient_request": next_patient,
        "waiting_patients": state.waiting_patients,
        "log": state.log
    }

# Note the new type hint: state: HospitalState
def ward_agent(state: HospitalState) -> Dict[str, Any]:
    """Finds a clean bed in the required ward."""
    
    # Use dot notation
    patient = state.current_patient_request
    if not patient:
        return {} 

    ward_type = patient.required_ward
    ward = state.wards[ward_type] # Accessing the dict key is still fine
    state.log.append(f"Ward Agent checking {ward_type} for a bed...")

    # The ward object and bed objects are all Pydantic models now
    for bed in ward.beds:
        if bed.status == BedStatus.EMPTY:
            bed.status = BedStatus.OCCUPIED
            bed.patient_id = patient.patient_id
            patient.status = "ADMITTED"
            
            state.log.append(f"SUCCESS: Found EMPTY bed {bed.bed_id} for {patient.name}.")
            # Return only the keys that changed
            return {"wards": state.wards, "current_patient_request": patient, "log": state.log, "bed_found_status": "FOUND_CLEAN"}

    state.log.append(f"No EMPTY beds in {ward_type}.")
    return {"log": state.log, "bed_found_status": "NO_CLEAN_BED"}


# Note the new type hint: state: HospitalState
# In agents.py
def cleaning_service_agent(state: HospitalState) -> Dict[str, Any]:
    """Finds a dirty bed and DISPATCHES a cleaner. Does NOT assign the bed."""
    patient = state.current_patient_request
    ward_type = patient.required_ward
    ward = state.wards[ward_type]
    team = state.cleaning_team
    
    state.log.append(f"Cleaning Agent checking {ward_type} for DIRTY beds...")

    if team.cleaners_available <= 0:
        state.log.append("No available cleaners. Patient must wait.")
        return {"log": state.log, "bed_found_status": "NO_CLEANER"}

    for bed in ward.beds:
        if bed.status == BedStatus.DIRTY:
            team.cleaners_available -= 1
            team.cleaners_busy += 1
            bed.status = BedStatus.CLEANING
            
            # --- THIS IS THE KEY CHANGE ---
            # Set a timer instead of instantly cleaning
            bed.time_to_clean = 3 # It will take 3 "ticks"
            
            state.log.append(f"Found DIRTY bed {bed.bed_id}. Dispatching cleaner. Will be ready in 3 ticks.")
            
            # This agent now FAILS to find a bed for the patient
            # The patient MUST wait until the simulation ticks
            return {
                "wards": state.wards,
                "cleaning_team": team,
                "log": state.log,
                "bed_found_status": "CLEANING_STARTED" # New status
            }

    state.log.append(f"No DIRTY beds available to clean in {ward_type}.")
    return {"log": state.log, "bed_found_status": "NO_DIRTY_BEDS"}


# Note the new type hint: state: HospitalState
def waitlist_agent(state: HospitalState) -> Dict[str, Any]:
    """If no bed can be found or cleaned, put patient back on list."""
    patient = state.current_patient_request
    state.log.append(f"FAILURE: No beds for {patient.name}. Returning to waiting list.")
    
    # Use dot notation
    state.waiting_patients.insert(0, patient)
    
    return {"waiting_patients": state.waiting_patients, "log": state.log}

# In agents.py
def simulation_tick_agent(state: HospitalState) -> Dict[str, Any]:
    """Advances the simulation by one time-step AND updates all timed processes."""
    state.simulation_time += 1
    state.log.append(f"--- Simulation Tick {state.simulation_time} ---")
    
    team = state.cleaning_team
    
    # --- THIS IS THE NEW LOGIC ---
    # Iterate over all wards and all beds to update their status
    for ward in state.wards.values():
        for bed in ward.beds:
            if bed.status == BedStatus.CLEANING:
                bed.time_to_clean -= 1
                state.log.append(f"Cleaning Bed {bed.bed_id}... {bed.time_to_clean} ticks remaining.")
                
                if bed.time_to_clean <= 0:
                    bed.status = BedStatus.EMPTY
                    team.cleaners_available += 1
                    team.cleaners_busy -= 1
                    state.log.append(f"SUCCESS: Bed {bed.bed_id} is now CLEAN and available.")
                    
    # Return all the state slices that have been modified
    return {
        "wards": state.wards, 
        "cleaning_team": team, 
        "log": state.log, 
        "simulation_time": state.simulation_time
    }
