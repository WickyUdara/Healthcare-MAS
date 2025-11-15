"""
Cleaning Agent - manages bed cleaning and turnaround.
Simulates cleaning with asyncio.sleep(10), then marks bed available.
Notifies WaitingListAgent when bed becomes available for auto-assignment.
"""

import asyncio
import time
from typing import Dict, Any
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class CleaningAgent(BaseAgent):
    """
    Manages bed cleaning simulation.
    - Receives cleaning requests from DischargeAgent
    - Simulates cleaning (10 second delay)
    - Marks bed as available
    - Triggers WaitingListAgent for auto-assignment
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("CleaningAgent", db_session, activity_log_file)
        self.cleaning_queue = {}  # Track cleaning tasks by bed_id
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process cleaning requests and manage bed cleaning simulation.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with cleaned beds available
        """
        # Process new cleaning requests
        cleaning_requests = state.get("cleaning_requests", [])
        
        for cleaning_req in cleaning_requests:
            bed_id = cleaning_req.get("bed_id")
            bed_number = cleaning_req.get("bed_number", "")
            transaction_id = cleaning_req.get("transaction_id")
            
            print(f"\n[CLEANING] Starting cleaning for bed {bed_number} (10s simulation)")
            
            # Simulate cleaning with asyncio.sleep
            # In production, this could be a background task
            await asyncio.sleep(1)
            
            print(f"  ✓ Cleaning complete for bed {bed_number}")
            
            # Mark bed as available in state
            for bed in state.get("beds", []):
                if bed.get("id") == bed_id:
                    bed["status"] = "available"
                    bed["current_patient_id"] = None
                    if "cleaning_start_time" in bed:
                        del bed["cleaning_start_time"]
                    print(f"  ✓ Bed {bed_number} now available")
                    break
            
            # Notify WaitingListAgent that bed is available for auto-assignment
            msg_available = self.create_message(
                transaction_id=transaction_id,
                performative=Performative.INFORM,
                receiver="WaitingListAgent",
                content={
                    "action": "bed_available",
                    "bed_id": bed_id,
                    "bed_number": bed_number,
                },
                reason=f"Bed {bed_number} cleaning complete, ready for assignment"
            )
            self.send(msg_available)
            
            # Also notify CoordinatorAgent to trigger auto-assignment
            msg_coord = self.create_message(
                transaction_id=transaction_id,
                performative=Performative.INFORM,
                receiver="CoordinatorAgent",
                content={
                    "action": "bed_available_for_assignment",
                    "bed_id": bed_id,
                },
                reason=f"Bed {bed_number} available, run waiting list auto-assign"
            )
            self.send(msg_coord)
        
        # Clear processed cleaning requests
        state["cleaning_requests"] = []
        return state
