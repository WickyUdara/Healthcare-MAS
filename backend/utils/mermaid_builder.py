"""
Mermaid sequence diagram builder.
Generates Mermaid diagram text from agent activity log messages.
"""

from typing import List, Dict, Any, Set
from utils.message_schema import Message


class MermaidBuilder:
    """
    Builds Mermaid sequence diagrams from transaction messages.
    """
    
    @staticmethod
    def build_sequence_diagram(
        transaction_id: str,
        messages: List[Dict[str, Any]],
        title: str = "Agent Communication"
    ) -> str:
        """
        Build a Mermaid sequence diagram from a list of messages.
        
        Args:
            transaction_id: Transaction ID for context
            messages: List of message dicts with sender, receiver, performative, reason
            title: Title for the diagram
        
        Returns:
            Mermaid diagram text (ready to render)
        """
        lines = [
            "sequenceDiagram",
            f"    Title: {title}",
            "    participant CoordAgent as Coordinator",
            "    participant AdmitAgent as Admission",
            "    participant BedAgent as BedAssignment",
            "    participant DisAgent as Discharge",
            "    participant CleanAgent as Cleaning",
            "    participant WaitAgent as WaitingList",
            "    participant ResAgent as ResourceMgr",
            "    participant CritAgent as CriticalPatient",
        ]
        
        # Get unique agents in messages to determine active participants
        agents_used = set()
        for msg in messages:
            agents_used.add(msg.get("sender", ""))
            agents_used.add(msg.get("receiver", ""))
        
        # Map agent names to diagram participant names
        agent_map = {
            "CoordinatorAgent": "CoordAgent",
            "AdmissionAgent": "AdmitAgent",
            "BedAssignmentAgent": "BedAgent",
            "DischargeAgent": "DisAgent",
            "CleaningAgent": "CleanAgent",
            "WaitingListAgent": "WaitAgent",
            "ResourceManagerAgent": "ResAgent",
            "CriticalPatientAgent": "CritAgent",
        }
        
        # Add messages
        for i, msg in enumerate(messages, 1):
            sender = msg.get("sender", "")
            receiver = msg.get("receiver", "")
            performative = msg.get("performative", "")
            reason = msg.get("reason", "")
            
            sender_display = agent_map.get(sender, sender)
            receiver_display = agent_map.get(receiver, receiver)
            
            # Determine arrow style based on performative
            arrow_style = "-->"
            if performative == "request":
                arrow_style = "->>"
            elif performative == "propose":
                arrow_style = "->"
            elif performative == "accept":
                arrow_style = "->>"
            elif performative == "reject":
                arrow_style = "-.->>"
            elif performative == "inform":
                arrow_style = "-->"
            elif performative == "query":
                arrow_style = "->>"
            
            # Build message label
            label = f"{performative.upper()}"
            if reason and len(reason) < 40:
                label = f"{label}: {reason[:30]}"
            
            lines.append(f"    {sender_display} {arrow_style} {receiver_display}: {label}")
        
        return "\n".join(lines)
    
    @staticmethod
    def build_timeline(messages: List[Dict[str, Any]]) -> str:
        """
        Build a simple text timeline of messages.
        
        Args:
            messages: List of message dicts
        
        Returns:
            Formatted timeline string
        """
        lines = ["TIMELINE:\n"]
        for i, msg in enumerate(messages, 1):
            timestamp = msg.get("timestamp", "")
            sender = msg.get("sender", "")
            receiver = msg.get("receiver", "")
            performative = msg.get("performative", "")
            reason = msg.get("reason", "")
            
            time_str = timestamp[11:19] if len(timestamp) > 10 else timestamp
            lines.append(f"  {i}. [{time_str}] {sender} -> {receiver}: {performative.upper()}")
            if reason:
                lines.append(f"     └─ {reason}")
        
        return "\n".join(lines)
