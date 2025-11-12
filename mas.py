import os
from dotenv import load_dotenv  # <-- ADD THIS IMPORT
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
import operator

load_dotenv()  # <-- ADD THIS LINE to load variables from .env

# --- 1. State Definition ---

class State(TypedDict):
    # history will be merged by concatenation
    history: Annotated[list[dict], operator.add]
    patient_request: str
    doctor_slots: list[str]
    scheduled_slot: str


# --- 2. Agent Nodes ---

# Get the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")  # <-- ADD THIS
if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Make sure it's in your .env file.")

# Pass the api_key to the model instance
llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)  # <-- MODIFY THIS LINE

def patient_agent(state: State) -> dict:
    # Patient requests an appointment
    req = state["patient_request"]
    message = (
        f"Patient: I’d like an appointment for {req}. "
        f"Please check availability."
    )
    return {"history": state["history"] + [{"role":"patient","content":message}]}

def scheduler_agent(state: State) -> dict:
    # Scheduler queries doctor slots and proposes one
    slots = state["doctor_slots"]
    message = (
        f"Scheduler: The doctor is available at {slots}. "
        f"Which slot works for you?"
    )
    return {"history": state["history"] + [{"role":"scheduler","content":message}]}

def doctor_agent(state: State) -> dict:
    # Doctor confirms a slot (or offers an alternative)
    slots = state["doctor_slots"]
    # simplistic logic: pick first
    chosen = slots[0] if slots else "No slot available"
    message = f"Doctor: Confirming appointment at {chosen}."
    return {"scheduled_slot": chosen,
            "history": state["history"] + [{"role":"doctor","content":message}]}

def confirmation_node(state: State) -> dict:
    # Final confirmation to patient
    slot = state["scheduled_slot"]
    message = f"Patient: Thank you — confirmed for {slot}!"
    return {"history": state["history"] + [{"role":"patient","content":message}]}

# --- 3. Graph Construction ---
builder = StateGraph(State)

builder.add_node("PatientAgent", patient_agent)
builder.add_node("SchedulerAgent", scheduler_agent)
builder.add_node("DoctorAgent", doctor_agent)
builder.add_node("Confirmation", confirmation_node)

builder.add_edge(START, "PatientAgent")
builder.add_edge("PatientAgent", "SchedulerAgent")
builder.add_edge("SchedulerAgent", "DoctorAgent")
builder.add_edge("DoctorAgent", "Confirmation")
builder.add_edge("Confirmation", END)

graph = builder.compile()

# --- 4. Run the Graph ---
initial_state: State = {
    "history": [],
    "patient_request": "Tuesday morning",
    "doctor_slots": ["10:00 AM", "11:30 AM", "2:00 PM"],
    "scheduled_slot": ""
}

result = graph.invoke(initial_state)

# Print conversational history
for turn in result["history"]:
    print(f'{turn["role"]}: {turn["content"]}')
print("Scheduled Slot:", result["scheduled_slot"])