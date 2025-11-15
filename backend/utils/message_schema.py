"""
Pydantic message schemas for FIPA-like agent communication.
Defines message structure and validation for all agent communications.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class Performative(str, Enum):
    """FIPA performative types."""
    REQUEST = "request"
    INFORM = "inform"
    PROPOSE = "propose"
    ACCEPT = "accept"
    REJECT = "reject"
    QUERY = "query"
    CANCEL = "cancel"


class Message(BaseModel):
    """
    FIPA-like message format for agent communication.
    All agent messages follow this structure.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    transaction_id: str  # UUID that groups all messages for an admission/discharge
    performative: Performative
    sender: str  # Agent name (e.g., "AdmissionAgent")
    receiver: str  # Agent name (e.g., "CoordinatorAgent")
    content: Dict[str, Any]  # Message payload (patient, bed, etc.)
    reason: Optional[str] = None  # Human-readable explanation
    
    class Config:
        use_enum_values = True


class AdmissionRequest(BaseModel):
    """Admission request payload."""
    name: str
    age: int
    gender: str
    symptoms: str
    heart_rate: int
    blood_pressure: str
    oxygen_saturation: float
    is_emergency: bool = False
    preferred_ward: Optional[str] = None  # ICU, GENERAL, SURGERY, MATERNITY


class BedAssignmentProposal(BaseModel):
    """Bed assignment proposal from BedAssignmentAgent."""
    patient_id: int
    bed_id: int
    bed_number: str
    ward_name: str
    reason: str
    confidence: float  # 0-1


class BedState(BaseModel):
    """Current state of a bed."""
    id: int
    bed_number: str
    ward_name: str
    status: str  # available, occupied, cleaning, maintenance
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None
    patient_severity: Optional[float] = None


class PatientInfo(BaseModel):
    """Patient information summary."""
    id: int
    name: str
    age: int
    gender: str
    status: str  # waiting, admitted, discharged, critical
    severity_score: float
    is_emergency: bool
    current_bed: Optional[str] = None
    admission_time: Optional[str] = None


class ActivityLogEntry(BaseModel):
    """Activity log entry for display."""
    id: int
    message_id: str
    transaction_id: str
    timestamp: str
    sender: str
    receiver: str
    performative: str
    content: Dict[str, Any]
    reason: Optional[str] = None


class SequenceDiagramData(BaseModel):
    """Data for rendering a sequence diagram."""
    transaction_id: str
    messages: List[Message]
    title: str
    mermaid_text: str  # Ready-to-render Mermaid diagram text
