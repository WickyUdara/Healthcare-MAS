from langgraph.graph import StateGraph, END
from typing import Dict, Any
from model import HospitalState # Use this for the schema
from agents import admissions_agent, ward_agent, cleaning_service_agent, waitlist_agent

# Define the router logic
def router(state: HospitalState) -> str:
    """Decides the next step after checking for a bed."""
    
    if state.bed_found_status == "FOUND_CLEAN":
        return "end_admission"
    
    if state.bed_found_status == "NO_CLEAN_BED":
        return "call_cleaning_agent"
    
    # --- NEW LOGIC ---
    # If we just started cleaning, or there are no cleaners,
    # or no dirty beds, the patient must wait.
    if state.bed_found_status in ("CLEANING_STARTED", "NO_CLEANER", "NO_DIRTY_BEDS"):
        return "call_waitlist_agent"

    # Failsafe
    return "call_waitlist_agent"

# This function just cleans up the state for the next run
def finish_admission(state: HospitalState) -> Dict[str, Any]:
    
    # --- THIS FUNCTION IS FIXED ---
    # Use dot notation (state.log)
    state.log.append("--- Admission process complete ---")
    
    # Return a dictionary of the changes
    return {
        "current_patient_request": None, 
        "bed_found_status": None, # Reset the status
        "log": state.log
    }
# Create the graph
workflow = StateGraph(HospitalState)

# Add Nodes
workflow.add_node("admissions_agent", admissions_agent)
workflow.add_node("ward_agent", ward_agent)
workflow.add_node("cleaning_service_agent", cleaning_service_agent)
workflow.add_node("waitlist_agent", waitlist_agent)
workflow.add_node("finish_admission", finish_admission)

# Define Edges
workflow.set_entry_point("admissions_agent")
workflow.add_edge("admissions_agent", "ward_agent")

# The main router
workflow.add_conditional_edges(
    "ward_agent",
    router,
    {
        "end_admission": "finish_admission",
        "call_cleaning_agent": "cleaning_service_agent",
        "call_waitlist_agent": "waitlist_agent",
    }
)

# After cleaning, check again
workflow.add_conditional_edges(
    "cleaning_service_agent",
    router, # Use the same router
    {
        "end_admission": "finish_admission", # Success after cleaning
        "call_waitlist_agent": "waitlist_agent", # Failed to clean (e.g., no dirty beds)
        # Add a placeholder for "call_cleaning_agent" in case router defaults
        "call_cleaning_agent": "waitlist_agent", # Failsafe
    }
)

# After waitlisting, the process for this patient ends
workflow.add_edge("waitlist_agent", "finish_admission")

# The end of the line
workflow.add_edge("finish_admission", END)

# Compile the graph
app = workflow.compile()