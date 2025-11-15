"""
Database models for Hospital Bed Management System.
Defines Patient, Bed, Ward, WaitingListEntry, ActivityLog, and Booking models.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class Ward(Base):
    """
    Represents a hospital ward (ICU, GENERAL, SURGERY, MATERNITY).
    """
    __tablename__ = "wards"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # ICU, GENERAL, SURGERY, MATERNITY
    capacity = Column(Integer, default=5)
    beds = relationship("Bed", back_populates="ward")
    
    def __repr__(self):
        return f"<Ward(id={self.id}, name={self.name}, capacity={self.capacity})>"


class BedStatus(enum.Enum):
    """Enum for bed status states."""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CLEANING = "cleaning"
    MAINTENANCE = "maintenance"


class Bed(Base):
    """
    Represents a physical bed in the hospital.
    """
    __tablename__ = "beds"
    
    id = Column(Integer, primary_key=True)
    bed_number = Column(String(20), unique=True, nullable=False)  # e.g., "ICU-01"
    ward_id = Column(Integer, ForeignKey("wards.id"), nullable=False)
    status = Column(Enum(BedStatus), default=BedStatus.AVAILABLE)
    current_patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ward = relationship("Ward", back_populates="beds")
    bookings = relationship("Booking", back_populates="bed")
    
    def __repr__(self):
        return f"<Bed(id={self.id}, bed_number={self.bed_number}, status={self.status.value})>"


class PatientStatus(enum.Enum):
    """Enum for patient status states."""
    WAITING = "waiting"
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    CRITICAL = "critical"


class Patient(Base):
    """
    Represents a patient in the hospital.
    """
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    symptoms = Column(Text, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    blood_pressure = Column(String(20), nullable=True)
    oxygen_saturation = Column(Float, nullable=True)
    severity_score = Column(Float, default=0)
    severity_explanation = Column(Text, nullable=True)
    is_emergency = Column(Boolean, default=False)
    preferred_ward = Column(String(50), nullable=True)  # ICU, GENERAL, SURGERY, MATERNITY, or None
    status = Column(Enum(PatientStatus), default=PatientStatus.WAITING)
    admission_time = Column(DateTime, default=datetime.utcnow)
    discharge_time = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)  # UUID of admission transaction
    
    bookings = relationship("Booking", back_populates="patient")
    waiting_list_entries = relationship("WaitingListEntry", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name={self.name}, status={self.status.value}, severity={self.severity_score})>"


class Booking(Base):
    """
    Represents an assignment of a patient to a bed.
    """
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    bed_id = Column(Integer, ForeignKey("beds.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    patient = relationship("Patient", back_populates="bookings")
    bed = relationship("Bed", back_populates="bookings")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, patient_id={self.patient_id}, bed_id={self.bed_id})>"


class WaitingListEntry(Base):
    """
    Represents a patient in the waiting list.
    """
    __tablename__ = "waiting_list"
    
    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    priority_score = Column(Float, default=0)  # Based on severity and wait time
    added_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    transaction_id = Column(String(100), nullable=True)
    
    patient = relationship("Patient", back_populates="waiting_list_entries")
    
    def __repr__(self):
        return f"<WaitingListEntry(id={self.id}, patient_id={self.patient_id}, priority={self.priority_score})>"


class ActivityLog(Base):
    """
    Represents agent communication and activity logs.
    Stores all FIPA-like messages exchanged between agents.
    """
    __tablename__ = "activity_log"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(100), unique=True, nullable=False)  # UUID
    transaction_id = Column(String(100), nullable=False)  # Groups messages by admission/discharge
    timestamp = Column(DateTime, default=datetime.utcnow)
    sender = Column(String(100), nullable=False)
    receiver = Column(String(100), nullable=False)
    performative = Column(String(50), nullable=False)  # request, inform, propose, accept, reject, query
    content = Column(Text, nullable=False)  # JSON string of message content
    reason = Column(Text, nullable=True)  # Human-readable explanation
    
    def __repr__(self):
        return f"<ActivityLog(id={self.id}, from={self.sender} to={self.receiver}, perf={self.performative})>"
