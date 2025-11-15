"""
Coordinator Agent - orchestrates the admission and bed assignment workflow.
Implements negotiation loops and decision-making for patient-to-bed assignment.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class CoordinatorAgent(BaseAgent):
    """
    Central coordinator for hospital bed management.
    - Receives admission requests from AdmissionAgent
    - Orchestrates parallel queries to BedAssignmentAgent, ResourceManagerAgent, WaitingListAgent
    - Manages negotiation rounds (up to 3)
    - Makes final assignment or places patient in waiting list
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("CoordinatorAgent", db_session, activity_log_file)
        self.negotiation_round = {}  # Track negotiation rounds per transaction
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process pending admission requests and manage assignment workflow.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state
        """
        # Process each admission request in the state
        pending_admissions = state.get("pending_admissions", [])
        
        for admission in pending_admissions:
            transaction_id = admission.get("transaction_id")
            patient = admission.get("patient")
            
            print(f"\n[COORDINATOR] Processing admission for {patient.get('name')} (TX: {transaction_id[:8]}...)")
            
            # NEGOTIATION LOOP - up to 3 rounds
            assignment_made = False
            for round_num in range(1, 4):
                print(f"  └─ Negotiation round {round_num}/3")
                
                # Request bed availability from ResourceManager
                msg_query = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.QUERY,
                    receiver="ResourceManagerAgent",
                    content={
                        "query_type": "available_beds",
                        "patient_id": patient.get("id"),
                        "preferred_ward": patient.get("preferred_ward"),
                        "severity": patient.get("severity_score", 0),
                    },
                    reason=f"Query for bed availability (round {round_num})"
                )
                self.send(msg_query)
                
                # MOCK: Simulate resource manager response
                available_beds = state.get("available_beds", [])
                if available_beds:
                    # Select best bed for patient
                    selected_bed = available_beds[0]
                    
                    # Send assignment proposal to BedAssignmentAgent
                    msg_propose = self.create_message(
                        transaction_id=transaction_id,
                        performative=Performative.PROPOSE,
                        receiver="BedAssignmentAgent",
                        content={
                            "patient_id": patient.get("id"),
                            "bed_id": selected_bed.get("id"),
                            "bed_number": selected_bed.get("bed_number"),
                            "ward_name": selected_bed.get("ward_name"),
                        },
                        reason=f"Proposed bed assignment: {selected_bed.get('bed_number')}"
                    )
                    self.send(msg_propose)
                    
                    # Simulate acceptance
                    msg_accept = self.create_message(
                        transaction_id=transaction_id,
                        performative=Performative.ACCEPT,
                        receiver="BedAssignmentAgent",
                        content={
                            "patient_id": patient.get("id"),
                            "bed_id": selected_bed.get("id"),
                        },
                        reason="Assignment accepted and finalized"
                    )
                    self.send(msg_accept)
                    
                    assignment_made = True
                    print(f"    ✓ Assignment made: {patient.get('name')} → {selected_bed.get('bed_number')}")
                    break
                else:
                    print(f"    ✗ No available beds in round {round_num}")
                    
                    # If this is not the final round, try negotiation strategies
                    if round_num < 3:
                        # Strategy 1: Ask WaitingListAgent for reordering
                        msg_reorder = self.create_message(
                            transaction_id=transaction_id,
                            performative=Performative.REQUEST,
                            receiver="WaitingListAgent",
                            content={
                                "request_type": "reorder_priority",
                                "patient_id": patient.get("id"),
                            },
                            reason="Request waiting list reordering"
                        )
                        self.send(msg_reorder)
                        
                        # Strategy 2: Query for preemption possibilities (if critical)
                        if patient.get("is_emergency"):
                            msg_preempt = self.create_message(
                                transaction_id=transaction_id,
                                performative=Performative.REQUEST,
                                receiver="CriticalPatientAgent",
                                content={
                                    "request_type": "evaluate_preemption",
                                    "patient_id": patient.get("id"),
                                    "severity": patient.get("severity_score", 0),
                                },
                                reason="Request preemption evaluation for emergency patient"
                            )
                            self.send(msg_preempt)
            
            if not assignment_made:
                # Place in waiting list
                msg_waitlist = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.INFORM,
                    receiver="WaitingListAgent",
                    content={
                        "action": "add_to_list",
                        "patient_id": patient.get("id"),
                        "patient_name": patient.get("name"),
                        "severity": patient.get("severity_score", 0),
                    },
                    reason="No beds available; patient added to waiting list"
                )
                self.send(msg_waitlist)
                
                # Update patient status in state
                for p in state.get("patients", []):
                    if p.get("id") == patient.get("id"):
                        p["status"] = "waiting"
                        break
        
        # Clear processed admissions
        state["pending_admissions"] = []
        return state
