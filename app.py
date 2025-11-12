import streamlit as st
from agents import simulation_tick_agent
from model import HospitalState, Ward, Bed, Patient, WardType, BedStatus, CleaningTeam
from graph import app
import uuid
from typing import Dict, Any

# --- Helper Functions ---
def get_bed_emoji(bed):
    if bed.status == BedStatus.OCCUPIED:
        return "👤" # Patient
    if bed.status == BedStatus.EMPTY:
        return "🛏️" # Empty
    if bed.status == BedStatus.DIRTY:
        return "🧹" # Dirty
    if bed.status == BedStatus.CLEANING:
        return "🧼" # Cleaning
    return "❓"

def initialize_state():
    """Sets up the initial hospital state in st.session_state."""
    if 'hospital_state' not in st.session_state:
        # Create a sample hospital (with objects)
        wards_config = {
            WardType.ICU: Ward(
                ward_id=WardType.ICU, 
                # Pass a list of DICTIONARIES, not Bed objects
                beds=[{"bed_id": f"ICU-{i}"} for i in range(5)] 
            ),
            WardType.SURGICAL: Ward(
                ward_id=WardType.SURGICAL, 
                beds=[{"bed_id": f"SURGICAL-{i}"} for i in range(10)]
            ),
            WardType.GENERAL: Ward(
                ward_id=WardType.GENERAL, 
                beds=[{"bed_id": f"GENERAL-{i}"} for i in range(20)]
            ),
        }
        
        # Make a few beds dirty or occupied
        wards_config[WardType.ICU].beds[0].status = BedStatus.OCCUPIED
        wards_config[WardType.SURGICAL].beds[0].status = BedStatus.OCCUPIED
        wards_config[WardType.SURGICAL].beds[1].status = BedStatus.OCCUPIED
        wards_config[WardType.SURGICAL].beds[2].status = BedStatus.DIRTY
        
        # Create the full state as an object first
        hospital_state_obj = HospitalState(
            wards=wards_config,
            waiting_patients=[],
            cleaning_team=CleaningTeam(cleaners_available=3, cleaners_busy=0),
            log=["--- Hospital Simulation Initialized ---"],
            current_patient_request=None,
        )
        
        # *** THIS IS THE FIX ***
        # Store its DICTIONARY representation, not the object
        st.session_state.hospital_state = hospital_state_obj.model_dump()

# --- UI Layout ---
st.set_page_config(layout="wide")
st.title("🏥 Intelligent Hospital Bed Management (MAS/LangGraph Sim)")

# Initialize
initialize_state()
current_state = st.session_state.hospital_state

# --- Sidebar Controls ---
with st.sidebar:
    st.header("Simulation Controls")
    
    st.subheader("Add Patient")
    patient_name = st.text_input("Patient Name", "John Doe")
    patient_ward = st.selectbox("Required Ward", [WardType.ICU, WardType.SURGICAL, WardType.GENERAL])
    
    if st.button("Add Patient to ED", type="primary"):
        new_patient = Patient(patient_id=str(uuid.uuid4())[:8], name=patient_name, required_ward=patient_ward)
        
        # *** THIS IS THE FIX ***
        # Store the dictionary version, not the object
        current_state['waiting_patients'].append(new_patient.model_dump()) 
        
        current_state['log'].append(f"NEW ADMISSION: {new_patient.name} added to waiting list for {new_patient.required_ward}.")
        st.session_state.hospital_state = current_state
        st.rerun()

    st.subheader("Run Simulation")
    if st.button("Run Next Admission Step", disabled=not current_state['waiting_patients']):
        # This is where you call LangGraph!
        # The input is the current state (a dict)
        inputs = current_state.copy()
        
        # Invoke the graph
        # The result (new_state_dict) is a DICTIONARY,
        # but it contains nested Pydantic objects (which is the problem).
        new_state_dict = app.invoke(inputs)
        
        # *** THIS IS THE FIX ***
        # To ensure we always store a pure, JSON-serializable
        # dictionary in the session_state (which the UI expects),
        # we will re-cast the entire result dict into our 
        # HospitalState Pydantic model, and then immediately
        # dump it back to a pure dictionary.
        
        # 1. Cast the hybrid dict (back) to a Pydantic object
        new_state_object = HospitalState(**new_state_dict)
        
        # 2. Dump the Pydantic object to a pure dict
        st.session_state.hospital_state = new_state_object.model_dump()
        st.rerun()

    # In app.py, in the sidebar
    if st.button("Advance Simulation 1 Tick"):
        # We're manually calling the agent function, not a graph
        state_dict = st.session_state.hospital_state
        state_obj = HospitalState(**state_dict) # Cast to object

        changes = simulation_tick_agent(state_obj) # Run the agent

        # Manually merge the changes
        for key, value in changes.items():
            setattr(state_obj, key, value)

        st.session_state.hospital_state = state_obj.model_dump() # Save
        st.rerun()
# --- Main Dashboard ---
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Hospital Status")
    
    # Display Wards
    for ward_type, ward_data in current_state['wards'].items():
        ward = Ward(**ward_data) # Re-cast to Pydantic model for easier handling
        st.subheader(f"{ward.ward_id.value} Ward")
        
        bed_cols = st.columns(10) # Display 10 beds per row
        col_idx = 0
        for bed in ward.beds:
            with bed_cols[col_idx % 10]:
                st.container(border=True).markdown(f"**{bed.bed_id}**\n\n{get_bed_emoji(bed)}", unsafe_allow_html=True)
                col_idx += 1

# In app.py
with col2:
    st.header("Waiting List")
    
    # --- ADD THIS LINE ---
    st.metric("Simulation Time (Ticks)", current_state.get('simulation_time', 0))
    
    team = CleaningTeam(**current_state['cleaning_team'])
    st.metric("Available Cleaners", team.cleaners_available, f"{team.cleaners_busy} busy")
    
    # ... rest of the code ...




# Log Area
st.header("Event Log")
st.text_area(
    "Log", 
    value="\n".join(current_state['log'][::-1]), # Show newest first
    height=300, 
    disabled=True
)