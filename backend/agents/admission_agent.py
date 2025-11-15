"""
Admission Agent - handles patient admission requests.
Validates patient data, computes severity using Gemini API (or fallback),
and initiates the bed assignment workflow.
"""

import uuid
from typing import Dict, Any, Optional
from utils.message_schema import Performative, AdmissionRequest
from utils.gemini_client import get_gemini_client
from agents.base_agent import BaseAgent


class AdmissionAgent(BaseAgent):
    """
    Handles patient admission requests.
    - Validates admission data
    - Computes severity score (using Gemini or fallback)
    - Persists patient to database
    - Triggers CoordinatorAgent to assign bed
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("AdmissionAgent", db_session, activity_log_file)
        self.gemini_client = get_gemini_client()
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process admission requests from the state.
        
        Args:
            state: Shared system state with new admissions
        
        Returns:
            Updated state with processed admissions
        """
        # Check for new admission requests
        admission_requests = state.get("new_admission_requests", [])
        
        for request_data in admission_requests:
            # Generate unique transaction ID for this admission
            transaction_id = str(uuid.uuid4())
            
            print(f"\n[ADMISSION] Processing admission request for {request_data.get('name')} (TX: {transaction_id[:8]}...)")
            
            try:
                # Validate request
                admission_req = AdmissionRequest(**request_data)
                print(f"  ✓ Request validated")
                
                # Compute severity score using Gemini (or fallback)
                severity_score, severity_explanation = self.gemini_client.score_severity({
                    "age": admission_req.age,
                    "symptoms": admission_req.symptoms,
                    "heart_rate": admission_req.heart_rate,
                    "blood_pressure": admission_req.blood_pressure,
                    "oxygen_saturation": admission_req.oxygen_saturation,
                    "is_emergency": admission_req.is_emergency,
                })
                
                print(f"  ✓ Severity computed: {severity_score:.1f}/100 - {severity_explanation}")
                
                # Create patient record in state (will be persisted by caller)
                patient = {
                    "id": len(state.get("patients", [])) + 1,
                    "name": admission_req.name,
                    "age": admission_req.age,
                    "gender": admission_req.gender,
                    "symptoms": admission_req.symptoms,
                    "heart_rate": admission_req.heart_rate,
                    "blood_pressure": admission_req.blood_pressure,
                    "oxygen_saturation": admission_req.oxygen_saturation,
                    "severity_score": severity_score,
                    "severity_explanation": severity_explanation,
                    "is_emergency": admission_req.is_emergency,
                    "preferred_ward": admission_req.preferred_ward,
                    "status": "waiting",
                    "transaction_id": transaction_id,
                }
                
                if "patients" not in state:
                    state["patients"] = []
                state["patients"].append(patient)
                
                # Send request to CoordinatorAgent to begin assignment cycle
                msg = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.REQUEST,
                    receiver="CoordinatorAgent",
                    content={
                        "action": "assign_bed",
                        "patient_id": patient["id"],
                        "patient_name": patient["name"],
                        "severity": severity_score,
                        "preferred_ward": patient["preferred_ward"],
                        "is_emergency": patient["is_emergency"],
                    },
                    reason=f"Admit {patient['name']} with severity {severity_score:.0f}/100"
                )
                self.send(msg)
                
                # Mark admission as processed
                if "pending_admissions" not in state:
                    state["pending_admissions"] = []
                state["pending_admissions"].append({
                    "transaction_id": transaction_id,
                    "patient": patient,
                })
                
            except Exception as e:
                print(f"  ✗ Admission processing failed: {e}")
        
        # Clear new requests
        state["new_admission_requests"] = []
        return state
