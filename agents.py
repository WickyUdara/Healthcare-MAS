import os
import time
import database as db
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
llm = genai.GenerativeModel('gemini-2.5-flash')

# --- Agent State Definition ---
class HospitalAgentState(TypedDict):
    new_patient_id: Optional[int]
    patient_to_discharge_id: Optional[int]
    bed_to_clean: Optional[str]
    trigger_suggestion_check: bool
    agent_messages: List[str] # To hold messages for this run

# --- Agent Nodes ---

def admission_agent(state: HospitalAgentState):
    patient_id = state['new_patient_id']
    patient = db.get_patient_details(patient_id)
    db.log_message('AdmissionAgent', f"Processing new patient: {patient['name']} (Severity: {patient['severity']})")

    # 1. Try to find a bed
    bed = db.find_available_bed('Any') # Keeping it simple
    
    if bed:
        bed_id = bed['bed_id']
        db.assign_bed_to_patient(patient_id, bed_id)
        db.log_message('AdmissionAgent', f"Assigned Patient {patient['name']} to Bed {bed_id}.")
        state['trigger_suggestion_check'] = False
    else:
        db.log_message('AdmissionAgent', f"No beds available for Patient {patient['name']}. Patient remains on waiting list.")
        # Check if this waiting patient is critical
        if patient['severity'] >= 4: # 4 or 5 is critical
            state['trigger_suggestion_check'] = True
        else:
            state['trigger_suggestion_check'] = False
            
    return state

def discharge_agent(state: HospitalAgentState):
    patient_id = state['patient_to_discharge_id']
    patient = db.get_patient_details(patient_id)
    db.log_message('DischargeAgent', f"Processing discharge for Patient {patient['name']}.")
    
    bed_id = db.discharge_patient(patient_id)
    
    if bed_id:
        db.log_message('DischargeAgent', f"Patient {patient['name']} discharged from Bed {bed_id}. Bed now cleaning.")
        state['bed_to_clean'] = bed_id
    else:
        db.log_message('DischargeAgent', f"Error: Could not discharge Patient {patient['name']}.")
        state['bed_to_clean'] = None
        
    return state

def cleaning_agent(state: HospitalAgentState):
    bed_id = state['bed_to_clean']
    if not bed_id:
        return state
        
    db.log_message('CleaningAgent', f"Starting to clean Bed {bed_id}...")
    
    # Simulate a 10-second clean
    time.sleep(10) 
    
    db.set_bed_status(bed_id, 'Available')
    db.log_message('CleaningAgent', f"Bed {bed_id} is now clean and Available.")
    
    return state

def waiting_list_agent(state: HospitalAgentState):
    db.log_message('WaitingListAgent', "Checking waiting list for available beds...")
    
    # Check for the highest priority patient
    patient = db.get_highest_priority_waiting_patient()
    
    if not patient:
        db.log_message('WaitingListAgent', "Waiting list is empty. No action taken.")
        return state

    # Check for an available bed
    bed = db.find_available_bed('Any')
    
    if bed and patient:
        patient_id = patient['patient_id']
        bed_id = bed['bed_id']
        db.assign_bed_to_patient(patient_id, bed_id)
        db.log_message('WaitingListAgent', f"Assigned high-priority Patient {patient['name']} (Severity: {patient['severity']}) from waiting list to Bed {bed_id}.")
    else:
        db.log_message('WaitingListAgent', "No available beds for waiting list patients.")
        
    return state

def suggestion_agent(state: HospitalAgentState):
    db.log_message('SuggestionAgent', "Critical patient is waiting. Analyzing admitted patients for discharge potential...")
    
    low_sev_patients = db.get_low_severity_admitted_patients()
    
    if not low_sev_patients:
        db.log_message('SuggestionAgent', "No low-severity patients found to suggest for discharge.")
        return state
        
    # Format for LLM
    patient_list_str = "\n".join([f"- Bed {p['assigned_bed_id']}: Patient {p['name']} (Severity: {p['severity']})" for p in low_sev_patients])
    
    prompt = f"""
    You are a hospital management assistant. A new, critical-severity patient is on the waiting list, but all beds are full.
    Review this list of currently admitted, low-severity patients and provide a brief, one-sentence suggestion for the hospital manager.
    Do not suggest discharging anyone, only suggest they be "reviewed".

    Low-Severity Patients:
    {patient_list_str}

    Provide one suggestion.
    """
    
    try:
        response = llm.generate_content(prompt)
        suggestion = response.text.strip()
        db.log_message('SuggestionAgent (LLM)', f"SUGGESTION: {suggestion}")
    except Exception as e:
        db.log_message('SuggestionAgent (LLM)', f"Error contacting LLM: {e}")
        
    return state

# --- Graph Definition ---

def build_graph():
    workflow = StateGraph(HospitalAgentState)

    # Add Nodes
    workflow.add_node("admission_agent", admission_agent)
    workflow.add_node("discharge_agent", discharge_agent)
    workflow.add_node("cleaning_agent", cleaning_agent)
    workflow.add_node("waiting_list_agent", waiting_list_agent)
    workflow.add_node("suggestion_agent", suggestion_agent)

    # --- Define Edges ---
    
    # 1. Router: Decide if we are admitting or discharging
    def router(state: HospitalAgentState):
        if state.get('new_patient_id'):
            return 'admission_agent'
        if state.get('patient_to_discharge_id'):
            return 'discharge_agent'
        return END # Should not happen

    workflow.set_conditional_entry_point(router)

    # 2. Admission Path
    def after_admission(state: HospitalAgentState):
        if state.get('trigger_suggestion_check', False):
            return 'suggestion_agent'
        return END

    workflow.add_conditional_edges("admission_agent", after_admission, {
        "suggestion_agent": "suggestion_agent",
        END: END
    })
    workflow.add_edge("suggestion_agent", END)

    # 3. Discharge Path
    workflow.add_edge("discharge_agent", "cleaning_agent")
    workflow.add_edge("cleaning_agent", "waiting_list_agent")
    workflow.add_edge("waiting_list_agent", END)

    # Compile the graph
    app = workflow.compile()
    return app

if __name__ == "__main__":
    # Test the graph
    db.init_db()
    graph = build_graph()
    
    # Test 1: Add a patient
    new_patient_id = db.add_patient("Test Patient 1", 3)
    state = {"new_patient_id": new_patient_id}
    graph.invoke(state)
    
    # Test 2: Add another patient
    new_patient_id_2 = db.add_patient("Test Patient 2 (Critical)", 5)
    state = {"new_patient_id": new_patient_id_2}
    graph.invoke(state)

    # Test 3: Discharge first patient
    state = {"patient_to_discharge_id": 1}
    graph.invoke(state)
    
    print("\n--- Final Bed Status ---")
    print(db.get_all_bed_statuses())
    print("\n--- Agent Logs ---")
    print(db.get_all_logs())