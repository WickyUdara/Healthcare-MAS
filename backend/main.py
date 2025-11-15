"""
FastAPI backend server for Hospital Bed Management MAS.
Provides REST endpoints for admission, discharge, bed status, activity logging, and sequence diagrams.
Includes WebSocket support for real-time agent activity updates.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import database models
from db.models import Base, Patient, Bed, Ward, WaitingListEntry, ActivityLog, BedStatus, PatientStatus, Booking
from db.init_db import init_db

# Import agents and orchestrator
from agents.admission_agent import AdmissionAgent
from langgraph_flow import PythonOrchestrator, HospitalState
from utils.gemini_client import get_gemini_client
from utils.mermaid_builder import MermaidBuilder
from utils.message_schema import Message, AdmissionRequest

# ============================================================================
# CONFIGURATION
# ============================================================================

DB_PATH = os.getenv("DB_PATH", "./data/hospital.db")
ACTIVITY_LOG_FILE = "activity_log.json"

# Initialize database
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

# Initialize orchestrator
orchestrator = PythonOrchestrator()
gemini_client = get_gemini_client()

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AdmissionRequestPayload(BaseModel):
    """Request body for patient admission."""
    name: str
    age: int
    gender: str
    symptoms: str
    heart_rate: int
    blood_pressure: str
    oxygen_saturation: float
    is_emergency: bool = False
    preferred_ward: Optional[str] = None


class DischargeRequestPayload(BaseModel):
    """Request body for patient discharge."""
    patient_id: int


class BedResponse(BaseModel):
    """Response model for bed information."""
    id: int
    bed_number: str
    ward_name: str
    status: str
    current_patient_id: Optional[int] = None
    current_patient_name: Optional[str] = None


class PatientResponse(BaseModel):
    """Response model for patient information."""
    id: int
    name: str
    age: int
    gender: str
    status: str
    severity_score: float
    is_emergency: bool
    current_bed: Optional[str] = None
    admission_time: Optional[str] = None


class AdmissionResponse(BaseModel):
    """Response model for admission result."""
    patient_id: int
    patient_name: str
    status: str  # "admitted" or "waiting_list"
    assigned_bed: Optional[str] = None
    severity_score: float
    severity_explanation: str
    waiting_list_position: Optional[int] = None
    transaction_id: str


class ActivityLogResponse(BaseModel):
    """Response model for activity log entry."""
    id: int
    timestamp: str
    sender: str
    receiver: str
    performative: str
    reason: Optional[str] = None


class OccupancyMetricsResponse(BaseModel):
    """Response model for occupancy metrics."""
    total_beds: int
    occupied: int
    available: int
    occupancy_rate: float
    by_ward: Dict[str, Any]


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Hospital Bed Management MAS",
    description="Multi-Agent System for hospital bed management",
    version="1.0.0"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db() -> Session:
    """Get database session."""
    return SessionLocal()


def load_activity_log() -> List[Dict[str, Any]]:
    """Load activity log from JSON file."""
    try:
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading activity log: {e}")
    return []


def init_hospital_state(db: Session) -> Dict[str, Any]:
    """
    Initialize hospital state from database.
    
    Args:
        db: Database session
    
    Returns:
        State dictionary with all hospital data
    """
    state = {
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
    
    # Load beds
    beds = db.query(Bed).all()
    for bed in beds:
        ward = db.query(Ward).filter_by(id=bed.ward_id).first()
        state["beds"].append({
            "id": bed.id,
            "bed_number": bed.bed_number,
            "ward_name": ward.name if ward else "Unknown",
            "status": bed.status.value,
            "current_patient_id": bed.current_patient_id,
        })
    
    # Load patients
    patients = db.query(Patient).all()
    for patient in patients:
        state["patients"].append({
            "id": patient.id,
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "symptoms": patient.symptoms,
            "heart_rate": patient.heart_rate,
            "blood_pressure": patient.blood_pressure,
            "oxygen_saturation": patient.oxygen_saturation,
            "severity_score": patient.severity_score,
            "severity_explanation": patient.severity_explanation,
            "is_emergency": patient.is_emergency,
            "preferred_ward": patient.preferred_ward,
            "status": patient.status.value,
            "current_bed_id": booking.bed_id if (booking := db.query(Booking).filter_by(patient_id=patient.id, released_at=None).first()) else None,
            "admission_time": patient.admission_time.isoformat() if patient.admission_time else None,
            "transaction_id": patient.transaction_id,
        })
    
    # Load waiting list
    waiting = db.query(WaitingListEntry).all()
    for entry in waiting:
        patient = db.query(Patient).filter_by(id=entry.patient_id).first()
        if patient:
            state["waiting_list"].append({
                "id": entry.id,
                "patient_id": entry.patient_id,
                "patient_name": patient.name,
                "priority_score": entry.priority_score,
                "added_at": entry.added_at.isoformat() if entry.added_at else None,
            })
    
    return state


def sync_state_to_db(state: Dict[str, Any], db: Session) -> None:
    """
    Sync in-memory state back to database.
    
    Args:
        state: In-memory hospital state
        db: Database session
    """
    try:
        # Update bed statuses
        for bed_state in state.get("beds", []):
            bed = db.query(Bed).filter_by(id=bed_state["id"]).first()
            if bed:
                bed.status = BedStatus(bed_state["status"])
                bed.current_patient_id = bed_state.get("current_patient_id")
                bed.updated_at = datetime.utcnow()
        
        # Update patient statuses
        for patient_state in state.get("patients", []):
            patient = db.query(Patient).filter_by(id=patient_state["id"]).first()
            if patient:
                patient.status = PatientStatus(patient_state["status"])
                # current_bed_id is now tracked via Booking table, not as direct attribute
        
        db.commit()
    except Exception as e:
        print(f"Error syncing state to DB: {e}")
        db.rollback()


# ============================================================================
# REST ENDPOINTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    db_path = os.getenv("DB_PATH", "./data/hospital.db")
    if not os.path.exists(db_path):
        init_db(db_path)
        print("✓ Database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/config")
async def get_config():
    """Get server configuration."""
    return {
        "db_path": DB_PATH,
        "gemini_available": gemini_client.use_gemini,
        "activity_log_file": ACTIVITY_LOG_FILE,
        "version": "1.0.0",
    }


@app.post("/admit", response_model=AdmissionResponse)
async def admit_patient(request: AdmissionRequestPayload, background_tasks: BackgroundTasks):
    """
    Admit a new patient.
    
    - Validates admission data
    - Computes severity using Gemini
    - Creates patient in database
    - Triggers admission workflow
    
    Args:
        request: Admission request payload
    
    Returns:
        AdmissionResponse with patient status and assigned bed (if available)
    """
    db = get_db()
    transaction_id = str(uuid.uuid4())
    
    try:
        print(f"\n📋 New admission request: {request.name} (TX: {transaction_id[:8]}...)")
        
        # Validate request
        admission_req = AdmissionRequest(**request.dict())
        
        # Compute severity
        severity_score, severity_explanation = gemini_client.score_severity({
            "age": admission_req.age,
            "symptoms": admission_req.symptoms,
            "heart_rate": admission_req.heart_rate,
            "blood_pressure": admission_req.blood_pressure,
            "oxygen_saturation": admission_req.oxygen_saturation,
            "is_emergency": admission_req.is_emergency,
        })
        
        print(f"  Severity: {severity_score:.0f}/100")
        
        # Create patient in database
        patient = Patient(
            name=admission_req.name,
            age=admission_req.age,
            gender=admission_req.gender,
            symptoms=admission_req.symptoms,
            heart_rate=admission_req.heart_rate,
            blood_pressure=admission_req.blood_pressure,
            oxygen_saturation=admission_req.oxygen_saturation,
            severity_score=severity_score,
            severity_explanation=severity_explanation,
            is_emergency=admission_req.is_emergency,
            preferred_ward=admission_req.preferred_ward,
            status=PatientStatus.WAITING,
            transaction_id=transaction_id,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        print(f"  Patient created with ID {patient.id}")
        
        # Add patient to waiting list immediately
        waiting_entry = WaitingListEntry(
            patient_id=patient.id,
            priority_score=severity_score + (100 if admission_req.is_emergency else 0),
            added_at=datetime.utcnow(),
            transaction_id=transaction_id,
        )
        db.add(waiting_entry)
        db.commit()
        print(f"  Added to waiting list with priority {waiting_entry.priority_score:.0f}")
        
        # Log admission to activity log
        try:
            admission_activity = ActivityLog(
                message_id=str(uuid.uuid4()),
                transaction_id=transaction_id,
                timestamp=datetime.utcnow(),
                sender="AdmissionEndpoint",
                receiver="WaitingListAgent",
                performative="inform",
                content=json.dumps({
                    "action": "patient_admitted",
                    "patient_id": patient.id,
                    "patient_name": patient.name,
                    "severity": severity_score,
                    "is_emergency": admission_req.is_emergency,
                }),
                reason=f"Patient {patient.name} admitted with severity {severity_score:.0f}/100"
            )
            db.add(admission_activity)
            db.commit()
        except Exception as e:
            print(f"  ⚠️  Error logging activity: {e}")
        
        # Try to assign a bed if available
        assigned_bed = None
        status = "waiting_list"
        try:
            # Look for an available bed in preferred ward (or any ward if emergency)
            preferred_wards = [admission_req.preferred_ward] if admission_req.preferred_ward else []
            
            # Add emergency wards to search
            if admission_req.is_emergency:
                preferred_wards = ["ICU"] + [w for w in ["GENERAL", "SURGERY", "MATERNITY"] if w not in preferred_wards]
            
            available_bed = None
            for ward_name in preferred_wards:
                available_bed = db.query(Bed).filter(
                    Bed.status == BedStatus.AVAILABLE,
                    Bed.ward.has(Ward.name == ward_name)
                ).first()
                if available_bed:
                    break
            
            # If no preferred ward bed, get any available bed
            if not available_bed:
                available_bed = db.query(Bed).filter_by(status=BedStatus.AVAILABLE).first()
            
            # If bed found, assign it
            if available_bed:
                available_bed.status = BedStatus.OCCUPIED
                available_bed.current_patient_id = patient.id
                available_bed.updated_at = datetime.utcnow()
                
                patient.status = PatientStatus.ADMITTED
                # Create booking entry instead of setting current_bed_id
                booking = Booking(
                    patient_id=patient.id,
                    bed_id=available_bed.id,
                    assigned_at=datetime.utcnow(),
                    transaction_id=transaction_id,
                )
                db.add(booking)
                
                # Remove from waiting list since admitted
                db.query(WaitingListEntry).filter_by(patient_id=patient.id).delete()
                
                db.commit()
                assigned_bed = available_bed.bed_number
                status = "admitted"
                print(f"  ✓ Assigned to bed {assigned_bed}")
                
                # Log bed assignment
                try:
                    assignment_activity = ActivityLog(
                        message_id=str(uuid.uuid4()),
                        transaction_id=transaction_id,
                        timestamp=datetime.utcnow(),
                        sender="BedAssignmentAgent",
                        receiver="ResourceManagerAgent",
                        performative="inform",
                        content=json.dumps({
                            "action": "bed_assigned",
                            "patient_id": patient.id,
                            "bed_id": available_bed.id,
                            "bed_number": available_bed.bed_number,
                        }),
                        reason=f"Bed {available_bed.bed_number} assigned to {patient.name}"
                    )
                    db.add(assignment_activity)
                    db.commit()
                except Exception as e:
                    print(f"  ⚠️  Error logging assignment: {e}")
            else:
                print(f"  ⚠️  No available beds - patient on waiting list")
        except Exception as e:
            print(f"  ⚠️  Error during bed assignment: {e}")
            # Still on waiting list if assignment fails
        
        # Initialize hospital state
        initial_state = init_hospital_state(db)
        
        # Add admission request to state
        initial_state["new_admission_requests"] = [request.dict()]
        
        # Run admission workflow in background
        async def run_admission_workflow():
            try:
                updated_state = await orchestrator.execute_admission_workflow(initial_state)
                sync_state_to_db(updated_state, db)
            except Exception as e:
                print(f"Error in admission workflow: {e}")
        
        background_tasks.add_task(run_admission_workflow)
        
        # Determine waiting list position
        waiting_list_position = None
        if status == "waiting_list":
            count = db.query(WaitingListEntry).filter(
                WaitingListEntry.priority_score >= (severity_score + (100 if admission_req.is_emergency else 0))
            ).count()
            waiting_list_position = count
        
        return AdmissionResponse(
            patient_id=patient.id,
            patient_name=patient.name,
            status=status,
            assigned_bed=assigned_bed,
            severity_score=severity_score,
            severity_explanation=severity_explanation,
            waiting_list_position=waiting_list_position,
            transaction_id=transaction_id,
        )
        
    except Exception as e:
        print(f"Error in admission: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.post("/discharge/{patient_id}")
async def discharge_patient(patient_id: int, background_tasks: BackgroundTasks):
    """
    Discharge a patient.
    
    - Marks patient as discharged
    - Triggers bed cleaning
    - Initiates waiting list auto-assignment
    
    Args:
        patient_id: ID of patient to discharge
    
    Returns:
        Status confirmation
    """
    db = get_db()
    transaction_id = str(uuid.uuid4())
    
    try:
        print(f"\n🏥 Discharge request: Patient {patient_id}")
        
        # Get patient
        patient = db.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Initialize hospital state
        initial_state = init_hospital_state(db)
        
        # Add discharge request to state
        initial_state["discharge_requests"] = [{
            "transaction_id": transaction_id,
            "patient_id": patient_id,
        }]
        
        # Run discharge workflow in background
        async def run_discharge_workflow():
            try:
                updated_state = await orchestrator.execute_discharge_workflow(initial_state)
                sync_state_to_db(updated_state, db)
            except Exception as e:
                print(f"Error in discharge workflow: {e}")
        
        background_tasks.add_task(run_discharge_workflow)
        
        return {
            "patient_id": patient_id,
            "patient_name": patient.name,
            "status": "discharge_initiated",
            "transaction_id": transaction_id,
            "message": f"Discharge initiated for {patient.name}. Cleaning in progress..."
        }
        
    except Exception as e:
        print(f"Error in discharge: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@app.get("/beds", response_model=List[BedResponse])
async def get_beds():
    """
    Get all beds and their status.
    
    Returns:
        List of bed information
    """
    db = get_db()
    try:
        beds = db.query(Bed).all()
        result = []
        
        for bed in beds:
            ward = db.query(Ward).filter_by(id=bed.ward_id).first()
            patient_name = None
            if bed.current_patient_id:
                patient = db.query(Patient).filter_by(id=bed.current_patient_id).first()
                patient_name = patient.name if patient else None
            
            result.append(BedResponse(
                id=bed.id,
                bed_number=bed.bed_number,
                ward_name=ward.name if ward else "Unknown",
                status=bed.status.value,
                current_patient_id=bed.current_patient_id,
                current_patient_name=patient_name,
            ))
        
        return result
    finally:
        db.close()


@app.get("/patients", response_model=List[PatientResponse])
async def get_patients():
    """
    Get all patients.
    
    Returns:
        List of patient information
    """
    db = get_db()
    try:
        patients = db.query(Patient).all()
        result = []
        
        for patient in patients:
            current_bed = None
            try:
                # Get current bed info if assigned
                booking = db.query(Booking).filter_by(patient_id=patient.id, released_at=None).first()
                if booking:
                    bed = db.query(Bed).filter_by(id=booking.bed_id).first()
                    if bed:
                        current_bed = bed.bed_number
            except Exception as e:
                print(f"Error getting bed for patient {patient.id}: {e}")
            
            result.append(PatientResponse(
                id=patient.id,
                name=patient.name,
                age=patient.age,
                gender=patient.gender,
                status=patient.status.value,
                severity_score=patient.severity_score,
                is_emergency=patient.is_emergency,
                current_bed=current_bed,
                admission_time=patient.admission_time.isoformat() if patient.admission_time else None,
            ))
        
        return result
    finally:
        db.close()


@app.get("/waiting_list")
async def get_waiting_list():
    """
    Get current waiting list.
    
    Returns:
        Waiting list entries sorted by priority
    """
    db = get_db()
    try:
        waiting = db.query(WaitingListEntry).order_by(WaitingListEntry.priority_score.desc()).all()
        result = []
        
        for i, entry in enumerate(waiting, 1):
            patient = db.query(Patient).filter_by(id=entry.patient_id).first()
            if patient:
                result.append({
                    "position": i,
                    "patient_id": patient.id,
                    "patient_name": patient.name,
                    "severity": patient.severity_score,
                    "is_emergency": patient.is_emergency,
                    "wait_time_seconds": (datetime.utcnow() - entry.added_at).total_seconds() if entry.added_at else 0,
                })
        
        return result
    finally:
        db.close()


@app.get("/activity_log")
async def get_activity_log(limit: int = 50):
    """
    Get recent activity log entries.
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        Recent activity log entries
    """
    db = get_db()
    try:
        logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        result = []
        
        for log in reversed(logs):  # Reverse to get chronological order
            result.append({
                "id": log.id,
                "message_id": log.message_id,
                "transaction_id": log.transaction_id,
                "timestamp": log.timestamp.isoformat(),
                "sender": log.sender,
                "receiver": log.receiver,
                "performative": log.performative,
                "reason": log.reason,
            })
        
        return result
    finally:
        db.close()


@app.get("/sequence_diagram/{transaction_id}")
async def get_sequence_diagram(transaction_id: str):
    """
    Generate Mermaid sequence diagram for a transaction.
    
    Args:
        transaction_id: Transaction ID to visualize
    
    Returns:
        Mermaid diagram text and metadata
    """
    db = get_db()
    try:
        # Get all messages for transaction
        logs = db.query(ActivityLog).filter_by(transaction_id=transaction_id).order_by(ActivityLog.timestamp).all()
        
        if not logs:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Convert to message dicts
        messages = []
        for log in logs:
            messages.append({
                "sender": log.sender,
                "receiver": log.receiver,
                "performative": log.performative,
                "reason": log.reason or f"{log.performative.upper()} message",
                "timestamp": log.timestamp.isoformat(),
            })
        
        # Build Mermaid diagram
        title = f"Admission Workflow - {transaction_id[:8]}..."
        mermaid_text = MermaidBuilder.build_sequence_diagram(transaction_id, messages, title)
        timeline_text = MermaidBuilder.build_timeline(messages)
        
        return {
            "transaction_id": transaction_id,
            "mermaid_text": mermaid_text,
            "timeline_text": timeline_text,
            "message_count": len(messages),
            "messages": messages,
        }
    finally:
        db.close()


@app.get("/metrics")
async def get_occupancy_metrics():
    """
    Get occupancy metrics and statistics.
    
    Returns:
        Detailed occupancy metrics
    """
    db = get_db()
    try:
        beds = db.query(Bed).all()
        patients = db.query(Patient).all()
        waiting = db.query(WaitingListEntry).all()
        
        total_beds = len(beds)
        occupied_beds = len([b for b in beds if b.status == BedStatus.OCCUPIED])
        available_beds = len([b for b in beds if b.status == BedStatus.AVAILABLE])
        cleaning_beds = len([b for b in beds if b.status == BedStatus.CLEANING])
        
        # Metrics per ward
        wards = db.query(Ward).all()
        ward_metrics = {}
        for ward in wards:
            ward_beds = [b for b in beds if b.ward_id == ward.id]
            ward_occupied = len([b for b in ward_beds if b.status == BedStatus.OCCUPIED])
            ward_metrics[ward.name] = {
                "total": len(ward_beds),
                "occupied": ward_occupied,
                "available": len(ward_beds) - ward_occupied,
                "occupancy_rate": ward_occupied / len(ward_beds) if ward_beds else 0,
            }
        
        # Patient statistics
        admitted_patients = len([p for p in patients if p.status == PatientStatus.ADMITTED])
        waiting_patients = len([p for p in patients if p.status == PatientStatus.WAITING])
        critical_patients = len([p for p in patients if p.is_emergency])
        
        # Average severity
        avg_severity = sum([p.severity_score for p in patients]) / len(patients) if patients else 0
        
        return {
            "total_beds": total_beds,
            "occupied": occupied_beds,
            "available": available_beds,
            "cleaning": cleaning_beds,
            "occupancy_rate": occupied_beds / total_beds if total_beds else 0,
            "by_ward": ward_metrics,
            "patients": {
                "total": len(patients),
                "admitted": admitted_patients,
                "waiting": waiting_patients,
                "critical": critical_patients,
                "avg_severity": avg_severity,
            },
            "waiting_list": {
                "count": len(waiting),
            },
        }
    finally:
        db.close()


@app.post("/run_assignment_cycle")
async def run_assignment_cycle(background_tasks: BackgroundTasks):
    """
    Debug endpoint to manually trigger assignment cycle.
    Useful for testing waiting list auto-assignment.
    
    Returns:
        Confirmation
    """
    db = get_db()
    transaction_id = str(uuid.uuid4())
    
    try:
        state = init_hospital_state(db)
        
        # Simulate bed availability for testing
        available_beds = [b for b in state["beds"] if b["status"] == "available"]
        if available_beds:
            state["available_beds"] = available_beds
            state["bed_available_notifications"] = [{
                "transaction_id": transaction_id,
                "bed_id": available_beds[0]["id"],
                "bed_number": available_beds[0]["bed_number"],
            }]
        
        async def run_cycle():
            try:
                state = await orchestrator.waiting_list.act(state)
                state = await orchestrator.bed_assign.act(state)
                sync_state_to_db(state, db)
            except Exception as e:
                print(f"Error in assignment cycle: {e}")
        
        background_tasks.add_task(run_cycle)
        
        return {
            "status": "cycle_initiated",
            "transaction_id": transaction_id,
            "available_beds": len(available_beds),
        }
    finally:
        db.close()


# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

connected_clients: List[WebSocket] = []


@app.websocket("/ws/activity")
async def websocket_activity(websocket: WebSocket):
    """
    WebSocket endpoint for real-time activity updates.
    Clients connected here receive activity log updates as they occur.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)


async def broadcast_activity_update(message: Dict[str, Any]) -> None:
    """
    Broadcast activity update to all connected WebSocket clients.
    
    Args:
        message: Message to broadcast
    """
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            disconnected.append(client)
    
    for client in disconnected:
        connected_clients.remove(client)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("🚀 Starting Hospital Bed Management MAS Backend")
    print(f"📊 Database: {DB_PATH}")
    print(f"📝 Activity Log: {ACTIVITY_LOG_FILE}")
    print(f"🤖 Gemini API: {'Enabled' if gemini_client.use_gemini else 'Disabled (using fallback)'}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
