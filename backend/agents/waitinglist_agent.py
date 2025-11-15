"""
Waiting List Agent - manages the waiting list and auto-assignment.
Maintains waiting list in priority order (severity + wait time).
Auto-assigns most suitable patient when bed becomes available.
"""

from typing import Dict, Any
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class WaitingListAgent(BaseAgent):
    """
    Manages patient waiting list.
    - Maintains waiting list sorted by priority (severity + wait time)
    - Auto-assigns top waiting patient when bed becomes available
    - Reorders list based on urgency changes
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("WaitingListAgent", db_session, activity_log_file)
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage waiting list and auto-assignment.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with waiting list processed
        """
        # Handle bed availability notifications (trigger auto-assignment)
        bed_available_notifications = state.get("bed_available_notifications", [])
        
        for notification in bed_available_notifications:
            bed_id = notification.get("bed_id")
            bed_number = notification.get("bed_number", "")
            transaction_id = notification.get("transaction_id")
            
            print(f"\n[WAITING_LIST] Auto-assign triggered for available bed {bed_number}")
            
            # Get highest priority waiting patient
            waiting_patients = [p for p in state.get("patients", []) if p.get("status") == "waiting"]
            
            if waiting_patients:
                # Sort by severity (descending) and then by admission time (ascending)
                waiting_patients.sort(
                    key=lambda p: (-p.get("severity_score", 0), p.get("admission_time", ""))
                )
                top_patient = waiting_patients[0]
                
                print(f"  ✓ Auto-assigning patient {top_patient['name']} (severity: {top_patient.get('severity_score', 0):.0f})")
                
                # Find available bed matching patient preferences
                suitable_bed = None
                preferred_ward = top_patient.get("preferred_ward")
                
                for bed in state.get("beds", []):
                    if bed.get("status") == "available":
                        # Prefer beds in patient's preferred ward
                        if preferred_ward and bed.get("ward_name") == preferred_ward:
                            suitable_bed = bed
                            break
                
                # Fallback to any available bed
                if not suitable_bed:
                    for bed in state.get("beds", []):
                        if bed.get("status") == "available":
                            suitable_bed = bed
                            break
                
                if suitable_bed:
                    # Create assignment request
                    if "pending_assignments" not in state:
                        state["pending_assignments"] = []
                    
                    state["pending_assignments"].append({
                        "transaction_id": transaction_id,
                        "patient_id": top_patient["id"],
                        "bed_id": suitable_bed["id"],
                        "bed_number": suitable_bed["bed_number"],
                    })
                    
                    # Notify CoordinatorAgent
                    msg_assign = self.create_message(
                        transaction_id=transaction_id,
                        performative=Performative.REQUEST,
                        receiver="CoordinatorAgent",
                        content={
                            "action": "auto_assign_waiting_patient",
                            "patient_id": top_patient["id"],
                            "bed_id": suitable_bed["id"],
                        },
                        reason=f"Auto-assign from waiting list: {top_patient['name']} → {suitable_bed['bed_number']}"
                    )
                    self.send(msg_assign)
                    
                    print(f"    ✓ Assignment queued: {top_patient['name']} → {suitable_bed['bed_number']}")
                else:
                    print(f"    ✗ No suitable beds available")
            else:
                print(f"  ℹ No waiting patients to assign")
        
        # Clear notifications
        state["bed_available_notifications"] = []
        return state
