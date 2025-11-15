"""
Resource Manager Agent - central view of bed and resource status.
Responds to queries about available beds, occupancy metrics, preemption candidates.
"""

from typing import Dict, Any, List
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class ResourceManagerAgent(BaseAgent):
    """
    Centralized resource tracking for the hospital.
    - Maintains current state of all beds
    - Responds to bed availability queries
    - Identifies preemption candidates
    - Tracks occupancy metrics per ward
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("ResourceManagerAgent", db_session, activity_log_file)
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process queries about resource status.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with query responses
        """
        # Process resource queries (would come from other agents)
        resource_queries = state.get("resource_queries", [])
        
        for query in resource_queries:
            query_type = query.get("query_type")
            transaction_id = query.get("transaction_id")
            
            print(f"\n[RESOURCE_MANAGER] Processing query: {query_type}")
            
            if query_type == "available_beds":
                # Find available beds
                available_beds = [
                    b for b in state.get("beds", [])
                    if b.get("status") == "available"
                ]
                
                print(f"  ℹ Available beds: {len(available_beds)}/{len(state.get('beds', []))}")
                
                # Filter by preferred ward if specified
                preferred_ward = query.get("preferred_ward")
                if preferred_ward:
                    available_beds = [
                        b for b in available_beds
                        if b.get("ward_name") == preferred_ward
                    ]
                    print(f"  ℹ Available in {preferred_ward}: {len(available_beds)}")
                
                # Respond with available beds
                msg_response = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.INFORM,
                    receiver=query.get("requester", "CoordinatorAgent"),
                    content={
                        "query_type": query_type,
                        "available_beds": available_beds,
                        "total_available": len(available_beds),
                    },
                    reason=f"Found {len(available_beds)} available beds"
                )
                self.send(msg_response)
                
                # Update state with available beds for coordinators
                state["available_beds"] = available_beds
            
            elif query_type == "occupancy_metrics":
                # Calculate occupancy metrics
                total_beds = len(state.get("beds", []))
                occupied_beds = len([b for b in state.get("beds", []) if b.get("status") == "occupied"])
                cleaning_beds = len([b for b in state.get("beds", []) if b.get("status") == "cleaning"])
                available_beds_count = len([b for b in state.get("beds", []) if b.get("status") == "available"])
                
                # Metrics per ward
                ward_metrics = {}
                for ward in ["ICU", "GENERAL", "SURGERY", "MATERNITY"]:
                    ward_beds = [b for b in state.get("beds", []) if b.get("ward_name") == ward]
                    ward_occupied = len([b for b in ward_beds if b.get("status") == "occupied"])
                    ward_metrics[ward] = {
                        "total": len(ward_beds),
                        "occupied": ward_occupied,
                        "available": len(ward_beds) - ward_occupied,
                        "occupancy_rate": ward_occupied / len(ward_beds) if ward_beds else 0,
                    }
                
                msg_metrics = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.INFORM,
                    receiver=query.get("requester", "CoordinatorAgent"),
                    content={
                        "total_beds": total_beds,
                        "occupied": occupied_beds,
                        "cleaning": cleaning_beds,
                        "available": available_beds_count,
                        "occupancy_rate": occupied_beds / total_beds if total_beds else 0,
                        "by_ward": ward_metrics,
                    },
                    reason="Occupancy metrics computed"
                )
                self.send(msg_metrics)
            
            elif query_type == "preemption_candidates":
                # Find lowest-severity occupied beds (for emergency preemption)
                occupied_beds = [b for b in state.get("beds", []) if b.get("status") == "occupied"]
                
                # Get patient info for each bed
                candidates = []
                for bed in occupied_beds:
                    patient_id = bed.get("current_patient_id")
                    for patient in state.get("patients", []):
                        if patient.get("id") == patient_id:
                            candidates.append({
                                "bed_id": bed.get("id"),
                                "bed_number": bed.get("bed_number"),
                                "patient_id": patient_id,
                                "patient_name": patient.get("name"),
                                "severity": patient.get("severity_score", 0),
                            })
                            break
                
                # Sort by severity (ascending) - lowest severity first (easiest to preempt)
                candidates.sort(key=lambda x: x["severity"])
                
                msg_candidates = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.INFORM,
                    receiver=query.get("requester", "CriticalPatientAgent"),
                    content={
                        "preemption_candidates": candidates[:3],  # Return top 3 candidates
                        "total_candidates": len(candidates),
                    },
                    reason=f"Found {len(candidates)} preemption candidates"
                )
                self.send(msg_candidates)
        
        # Clear processed queries
        state["resource_queries"] = []
        return state
