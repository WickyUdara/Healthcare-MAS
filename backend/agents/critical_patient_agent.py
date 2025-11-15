"""
Critical Patient Agent - handles emergency patients and bed preemption.
For critical patients, can propose preempting lower-severity occupants.
Negotiates with CoordinatorAgent and DischargeAgent.
"""

from typing import Dict, Any
from utils.message_schema import Performative
from agents.base_agent import BaseAgent


class CriticalPatientAgent(BaseAgent):
    """
    Handles critical/emergency patient cases.
    - Evaluates preemption requests
    - Negotiates with other agents for priority assignment
    - Proposes preempting lower-severity patients if necessary
    """
    
    def __init__(self, db_session=None, activity_log_file: str = "activity_log.json"):
        super().__init__("CriticalPatientAgent", db_session, activity_log_file)
        self.preemption_threshold = 70  # Only preempt for patients with severity >= 70
    
    async def act(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate and handle critical patient cases.
        
        Args:
            state: Shared system state
        
        Returns:
            Updated state with preemption decisions
        """
        # Process critical patient evaluations
        critical_evaluations = state.get("critical_evaluations", [])
        
        for evaluation in critical_evaluations:
            patient_id = evaluation.get("patient_id")
            severity = evaluation.get("severity", 0)
            transaction_id = evaluation.get("transaction_id")
            
            print(f"\n[CRITICAL_PATIENT] Evaluating preemption for patient {patient_id} (severity: {severity:.0f})")
            
            # Check if preemption is justified (severity >= threshold)
            if severity >= self.preemption_threshold:
                print(f"  ✓ Patient qualifies for preemption (severity {severity:.0f} >= {self.preemption_threshold})")
                
                # Query ResourceManager for preemption candidates
                msg_query = self.create_message(
                    transaction_id=transaction_id,
                    performative=Performative.QUERY,
                    receiver="ResourceManagerAgent",
                    content={
                        "query_type": "preemption_candidates",
                        "critical_patient_severity": severity,
                        "requester": "CriticalPatientAgent",
                    },
                    reason="Query for preemption candidates"
                )
                self.send(msg_query)
                
                # Get candidates from state (set by ResourceManager)
                candidates = state.get("preemption_candidates", [])
                
                if candidates:
                    # Select lowest-severity candidate
                    candidate = candidates[0]
                    candidate_patient_id = candidate.get("patient_id")
                    candidate_severity = candidate.get("severity", 0)
                    candidate_bed = candidate.get("bed_number", "")
                    
                    print(f"  ✓ Selected preemption candidate: {candidate['patient_name']} (severity {candidate_severity:.0f})")
                    
                    # Request preemption via CoordinatorAgent
                    msg_preempt = self.create_message(
                        transaction_id=transaction_id,
                        performative=Performative.REQUEST,
                        receiver="CoordinatorAgent",
                        content={
                            "action": "evaluate_preemption",
                            "critical_patient_id": patient_id,
                            "critical_severity": severity,
                            "target_patient_id": candidate_patient_id,
                            "target_bed_id": candidate.get("bed_id"),
                            "target_bed_number": candidate_bed,
                            "target_severity": candidate_severity,
                        },
                        reason=f"Request preemption: {candidate['patient_name']} (sev={candidate_severity:.0f}) for critical patient (sev={severity:.0f})"
                    )
                    self.send(msg_preempt)
                else:
                    print(f"  ✗ No preemption candidates available")
            else:
                print(f"  ℹ Severity {severity:.0f} below preemption threshold {self.preemption_threshold}")
        
        # Clear processed evaluations
        state["critical_evaluations"] = []
        return state
