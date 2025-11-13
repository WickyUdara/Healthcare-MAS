import streamlit as st
import database as db
from agents import build_graph
import time

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Hospital Bed Management")
st.title("🏥 Multi-Agent Hospital Bed Management System")

# --- Initialize ---
# Build the graph once and store in session state
if 'graph' not in st.session_state:
    st.session_state.graph = build_graph()

# Initialize DB on first run
if 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state.db_initialized = True

# --- Helper to run graph and refresh ---
def run_graph_action(state, action_message="Processing..."):
    with st.spinner(action_message):
        st.session_state.graph.invoke(state)
    # Use st.rerun() to force a complete reload of the page,
    # which will query the DB for the new state.
    st.rerun()

# --- Main Layout ---
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Control Panel")
    
    # --- 1. Admit Patient ---
    with st.form("admit_form", clear_on_submit=True):
        st.subheader("Admit New Patient")
        name = st.text_input("Patient Name")
        severity = st.slider("Severity", 1, 5, 3)
        
        admit_button = st.form_submit_button("Admit Patient", type="primary")
        
    if admit_button and name:
        new_patient_id = db.add_patient(name, severity)
        run_graph_action({"new_patient_id": new_patient_id}, 
                         f"Admitting Patient {name}...")

    # --- 2. Discharge Patient ---
    st.subheader("Discharge Patient")
    admitted_patients = db.get_admitted_patients()
    patient_options = {p['patient_id']: f"{p['name']} (Bed: {p['assigned_bed_id']})" for p in admitted_patients}
    
    if not patient_options:
        st.info("No patients are currently admitted.")
    else:
        patient_to_discharge_id = st.selectbox(
            "Select Patient to Discharge",
            options=patient_options.keys(),
            format_func=lambda x: patient_options[x]
        )
        discharge_button = st.button("Discharge Patient", type="secondary")
        
        if discharge_button:
            run_graph_action({"patient_to_discharge_id": patient_to_discharge_id},
                             f"Discharging Patient...")

    # --- 3. Waiting List ---
    st.subheader("Waiting List")
    waiting_list = db.get_waiting_list()
    if not waiting_list:
        st.text("Waiting list is empty.")
    else:
        st.markdown("**Patient (Severity)**")
        for p in waiting_list:
            st.text(f"- {p['name']} (Severity: {p['severity']})")

with col2:
    st.header("Hospital Dashboard")

    # --- 1. Bed Status Grid ---
    st.subheader(f"Ward A (5 Beds)")
    cols_a = st.columns(5)
    st.subheader(f"Ward B (5 Beds)")
    cols_b = st.columns(5)
    
    all_beds = db.get_all_bed_statuses()
    
    for i, bed in enumerate(all_beds):
        col = cols_a[i] if bed['ward'] == 'A' else cols_b[i - 5]
        
        with col.container(border=True):
            st.markdown(f"**Bed {bed['bed_id']}**")
            if bed['status'] == 'Available':
                st.success(f"Available", icon="✅")
            elif bed['status'] == 'Occupied':
                st.error(f"Occupied", icon="🛏️")
                st.caption(f"Patient: {bed['name']} (Sev: {bed['severity']})")
            elif bed['status'] == 'Cleaning':
                st.warning(f"Cleaning", icon="🧹")

    # --- 2. Agent Communication Log (NEW) ---
    st.subheader("Agent Communication Log")

    AGENT_ICONS = {
        "AdmissionAgent": "📥",
        "DischargeAgent": "📤",
        "CleaningAgent": "🧹",
        "WaitingListAgent": "📋",
        "SuggestionAgent (LLM)": "💡",
        "System": "⚙️",
        "AdmissionForm": "📝"
    }

    logs = db.get_all_logs()
    log_container = st.container(height=400, border=True)

    for log in logs:
        agent_name = log['agent_name']
        message = log['message']
        timestamp = log['timestamp'].split('T')[1].split('.')[0]

        # Get the icon from our dictionary, with a default
        icon = AGENT_ICONS.get(agent_name, "🤖")

        # Still show a toast for important suggestions
        if "**SUGGESTION:**" in message:
            st.toast(message, icon="💡")

        # Use the chat_message component for the log
        with log_container.chat_message(name=agent_name, avatar=icon):
            st.markdown(message)
            st.caption(f"_{timestamp}_")