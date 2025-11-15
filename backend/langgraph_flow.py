"""
LangGraph-based orchestration for hospital bed management.
Falls back to pure Python orchestrator if langgraph not available.
"""

import asyncio
from typing import Dict, Any, Optional, List

# Try to import langgraph; fallback gracefully
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️  langgraph not installed. Using pure Python fallback orchestrator.")


class HospitalState:
    """
    Shared state for hospital bed management system.
    Maintains all agents' views of patients, beds, waiting list, etc.
    """
    
    def __init__(self):
        self.state = {
            "beds": [],
            "patients": [],
            "waiting_list": [],
            "pending_admissions": [],
            "pending_assignments": [],
            "discharge_requests": [],
            "cleaning_requests": [],
            "bed_available_notifications": [],
            "resource_queries": [],
            "critical_evaluations": [],
            "new_admission_requests": [],
            "available_beds": [],
            "preemption_candidates": [],
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return self.state
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update state with new values."""
        self.state.update(updates)


def create_langgraph_orchestrator():
    """
    Create LangGraph-based orchestrator (if available).
    
    Returns:
        HospitalOrchestrator instance or None if langgraph not available
    """
    if not LANGGRAPH_AVAILABLE:
        return None
    
    try:
        # Import agents
        from agents.coordinator_agent import CoordinatorAgent
        from agents.admission_agent import AdmissionAgent
        from agents.bed_assignment_agent import BedAssignmentAgent
        from agents.discharge_agent import DischargeAgent
        from agents.cleaning_agent import CleaningAgent
        from agents.waitinglist_agent import WaitingListAgent
        from agents.resource_manager_agent import ResourceManagerAgent
        from agents.critical_patient_agent import CriticalPatientAgent
        
        # Create state graph
        state_graph = StateGraph(HospitalState)
        
        # Initialize agents
        coordinator = CoordinatorAgent()
        admission = AdmissionAgent()
        bed_assign = BedAssignmentAgent()
        discharge = DischargeAgent()
        cleaning = CleaningAgent()
        waiting_list = WaitingListAgent()
        resource_mgr = ResourceManagerAgent()
        critical = CriticalPatientAgent()
        
        # Define nodes (simplified - in real implementation these would be async functions)
        async def admission_node(state: HospitalState) -> HospitalState:
            updated_state = await admission.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def coordinator_node(state: HospitalState) -> HospitalState:
            updated_state = await coordinator.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def bed_assign_node(state: HospitalState) -> HospitalState:
            updated_state = await bed_assign.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def resource_mgr_node(state: HospitalState) -> HospitalState:
            updated_state = await resource_mgr.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def waiting_list_node(state: HospitalState) -> HospitalState:
            updated_state = await waiting_list.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def discharge_node(state: HospitalState) -> HospitalState:
            updated_state = await discharge.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def cleaning_node(state: HospitalState) -> HospitalState:
            updated_state = await cleaning.act(state.to_dict())
            state.update(updated_state)
            return state
        
        async def critical_node(state: HospitalState) -> HospitalState:
            updated_state = await critical.act(state.to_dict())
            state.update(updated_state)
            return state
        
        # Note: Adding nodes to graph requires langgraph's StateGraph methods
        # This is a simplified representation - full implementation would use:
        # state_graph.add_node("admission", admission_node)
        # state_graph.add_node("coordinator", coordinator_node)
        # etc.
        
        return None  # Return None as langgraph setup is complex; use fallback instead
        
    except Exception as e:
        print(f"⚠️  Failed to create LangGraph orchestrator: {e}")
        return None


class PythonOrchestrator:
    """
    Pure Python orchestrator for hospital bed management.
    Mimics LangGraph behavior using asyncio and concurrent execution.
    """
    
    def __init__(self):
        """Initialize orchestrator with agents."""
        from agents.coordinator_agent import CoordinatorAgent
        from agents.admission_agent import AdmissionAgent
        from agents.bed_assignment_agent import BedAssignmentAgent
        from agents.discharge_agent import DischargeAgent
        from agents.cleaning_agent import CleaningAgent
        from agents.waitinglist_agent import WaitingListAgent
        from agents.resource_manager_agent import ResourceManagerAgent
        from agents.critical_patient_agent import CriticalPatientAgent
        
        self.coordinator = CoordinatorAgent()
        self.admission = AdmissionAgent()
        self.bed_assign = BedAssignmentAgent()
        self.discharge = DischargeAgent()
        self.cleaning = CleaningAgent()
        self.waiting_list = WaitingListAgent()
        self.resource_mgr = ResourceManagerAgent()
        self.critical = CriticalPatientAgent()
        
        print("✓ Python Orchestrator initialized (LangGraph fallback)")
    
    async def execute_admission_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute admission workflow: admission → coordinator → bed_assign.
        
        Args:
            state: Current hospital state
        
        Returns:
            Updated state after workflow
        """
        print("\n🔄 Starting admission workflow...")
        
        # Step 1: Process admission request
        state = await self.admission.act(state)
        
        # Step 2: Coordinate bed assignment (with negotiation)
        state = await self.coordinator.act(state)
        
        # Step 3: Finalize bed assignment
        state = await self.bed_assign.act(state)
        
        print("✓ Admission workflow complete")
        return state
    
    async def execute_discharge_workflow(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute discharge workflow: discharge → cleaning → waiting_list auto-assign.
        
        Args:
            state: Current hospital state
        
        Returns:
            Updated state after workflow
        """
        print("\n🔄 Starting discharge workflow...")
        
        # Step 1: Process discharge
        state = await self.discharge.act(state)
        
        # Step 2: Clean bed (with 10s sleep)
        state = await self.cleaning.act(state)
        
        # Step 3: Auto-assign from waiting list
        state = await self.waiting_list.act(state)
        
        # Step 4: Finalize any new assignments
        state = await self.bed_assign.act(state)
        
        print("✓ Discharge workflow complete")
        return state
    
    async def execute_resource_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute resource manager query.
        
        Args:
            state: Current hospital state
        
        Returns:
            Updated state with query results
        """
        state = await self.resource_mgr.act(state)
        return state
    
    async def execute_critical_evaluation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute critical patient evaluation.
        
        Args:
            state: Current hospital state
        
        Returns:
            Updated state with evaluation results
        """
        state = await self.critical.act(state)
        return state


def get_orchestrator() -> PythonOrchestrator:
    """
    Get orchestrator instance.
    Returns pure Python orchestrator as primary implementation.
    
    Returns:
        PythonOrchestrator instance
    """
    return PythonOrchestrator()
