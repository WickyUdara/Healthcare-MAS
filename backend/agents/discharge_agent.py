"""
Discharge Agent - handles patient discharge requests.
Updates patient and bed status, notifies CleaningAgent to clean the bed.
"""

from typing import Dict, Any
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class DischargeAgent(BaseAgent):
    """
    Handles patient discharges.
    - Receives discharge requests
    - Updates patient status to discharged
    - Notifies CleaningAgent to clean the bed
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("DischargeAgent", db_session, activity_log_file)
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process discharge requests.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with discharges processed
        """
        # Process discharge requests
        discharge_requests = state.get("discharge_requests", [])
        
        for discharge_req in discharge_requests:
            transaction_id = discharge_req.get("transaction_id")
            patient_id = discharge_req.get("patient_id")
            
            print(f"\n[DISCHARGE] Processing discharge for Patient {patient_id} (TX: {transaction_id[:8]}...)")
            
            # Find patient and bed
            patient = None
            bed_id = None
            bed_number = None
            
            for p in state.get("patients", []):
                if p.get("id") == patient_id:
                    patient = p
                    bed_id = p.get("current_bed_id")
                    break
            
            if patient and bed_id:
                # Update patient status
                patient["status"] = "discharged"
                print(f"  ✓ Patient {patient['name']} marked as discharged")
                
                # Find bed and mark for cleaning
                for bed in state.get("beds", []):
                    if bed.get("id") == bed_id:
                        bed_number = bed.get("bed_number", "")
                        bed["status"] = "cleaning"
                        bed["cleaning_start_time"] = __import__('time').time()
                        print(f"  ✓ Bed {bed_number} marked for cleaning")
                        break
                
                # Notify CleaningAgent to clean the bed
                msg_clean = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.REQUEST,
                    receiver="CleaningAgent",
                    content={
                        "action": "clean_bed",
                        "bed_id": bed_id,
                        "bed_number": bed_number,
                        "patient_id": patient_id,
                    },
                    reason=f"Cleaning requested for bed {bed_number} after discharge"
                )
                self.send(msg_clean)
            else:
                print(f"  ✗ Patient {patient_id} or bed not found")
        
        # Clear discharge requests
        state["discharge_requests"] = []
        return state
