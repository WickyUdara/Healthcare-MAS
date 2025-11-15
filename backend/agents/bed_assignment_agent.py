"""
Bed Assignment Agent - assigns patients to beds.
Queries available beds from ResourceManagerAgent and finalizes assignments.
"""

from typing import Dict, Any
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class BedAssignmentAgent(BaseAgent):
    """
    Assigns patients to specific beds.
    - Receives assignment proposals from CoordinatorAgent
    - Queries ResourceManagerAgent for available beds
    - Finalizes assignments and updates bed occupancy
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("BedAssignmentAgent", db_session, activity_log_file)
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bed assignment requests.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with assignments
        """
        # Process assignment proposals
        assignments = state.get("pending_assignments", [])
        
        for assignment in assignments:
            transaction_id = assignment.get("transaction_id")
            patient_id = assignment.get("patient_id")
            bed_id = assignment.get("bed_id")
            bed_number = assignment.get("bed_number", "")
            
            print(f"\n[BED_ASSIGNMENT] Finalizing assignment: Patient {patient_id} → Bed {bed_number}")
            
            # Mark bed as occupied in state
            for bed in state.get("beds", []):
                if bed.get("id") == bed_id:
                    bed["status"] = "occupied"
                    bed["current_patient_id"] = patient_id
                    print(f"  ✓ Bed {bed_number} marked as occupied")
                    break
            
            # Mark patient as admitted
            for patient in state.get("patients", []):
                if patient.get("id") == patient_id:
                    patient["status"] = "admitted"
                    patient["current_bed_id"] = bed_id
                    print(f"  ✓ Patient marked as admitted")
                    break
            
            # Send confirmation to CoordinatorAgent
            msg_confirm = self.create_message(
                transaction_id=transaction_id,
                performative=Performative.INFORM,
                receiver="CoordinatorAgent",
                content={
                    "action": "assignment_complete",
                    "patient_id": patient_id,
                    "bed_id": bed_id,
                    "bed_number": bed_number,
                },
                reason=f"Assignment finalized for Patient {patient_id}"
            )
            self.send(msg_confirm)
        
        # Clear pending assignments
        state["pending_assignments"] = []
        return state
