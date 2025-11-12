from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class BedStatus(str, Enum):
    EMPTY = "EMPTY"        # Clean and available
    OCCUPIED = "OCCUPIED"  # Has a patient
    DIRTY = "DIRTY"        # Needs cleaning
    CLEANING = "CLEANING"  # Cleaner is en-route/busy

class WardType(str, Enum):
    ICU = "ICU"
    SURGICAL = "SURGICAL"
    MATERNITY = "MATERNITY"
    GENERAL = "GENERAL"

class Patient(BaseModel):
    patient_id: str
    name: str
    required_ward: WardType
    status: str = "WAITING" # WAITING, ADMITTED, DISCHARGED

class Bed(BaseModel):
    bed_id: str
    status: BedStatus = BedStatus.EMPTY
    patient_id: Optional[str] = None

class Ward(BaseModel):
    ward_id: WardType
    beds: List[Bed]

class CleaningTeam(BaseModel):
    cleaners_available: int = 5
    cleaners_busy: int = 0


class Bed(BaseModel):
    bed_id: str
    status: BedStatus = BedStatus.EMPTY
    patient_id: Optional[str] = None
    
    # --- ADD THIS LINE ---
    time_to_clean: int = 0

# ... (other classes) ...

class HospitalState(BaseModel):
    wards: Dict[WardType, Ward]
    waiting_patients: List[Patient]
    cleaning_team: CleaningTeam
    log: List[str] = Field(default_factory=list)
    current_patient_request: Optional[Patient] = None
    bed_found_status: Optional[str] = None
    
    # --- ADD THIS LINE ---
    simulation_time: int = 0