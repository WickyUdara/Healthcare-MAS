"""
Database initialization script.
Creates tables and seeds with 20 beds (4 wards x 5 beds) and dummy patients.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Ward, Bed, Patient, WaitingListEntry, BedStatus, PatientStatus
from datetime import datetime

def init_db(db_path: str = "./data/hospital.db"):
    """
    Initialize the database with schema and seed data.
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create engine and tables
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Seed wards if they don't exist
    wards_data = [
        {"name": "ICU", "capacity": 5},
        {"name": "GENERAL", "capacity": 5},
        {"name": "SURGERY", "capacity": 5},
        {"name": "MATERNITY", "capacity": 5},
    ]
    
    for ward_data in wards_data:
        if not session.query(Ward).filter_by(name=ward_data["name"]).first():
            ward = Ward(**ward_data)
            session.add(ward)
    
    session.commit()
    
    # Seed beds if they don't exist
    wards = session.query(Ward).all()
    for ward in wards:
        for bed_idx in range(1, 6):
            bed_number = f"{ward.name}-{bed_idx:02d}"
            if not session.query(Bed).filter_by(bed_number=bed_number).first():
                bed = Bed(
                    bed_number=bed_number,
                    ward_id=ward.id,
                    status=BedStatus.AVAILABLE
                )
                session.add(bed)
    
    session.commit()
    
    # Seed dummy patients if they don't exist
    dummy_patients = [
        {
            "name": "John Doe",
            "age": 65,
            "gender": "Male",
            "symptoms": "Chest pain, shortness of breath",
            "heart_rate": 95,
            "blood_pressure": "160/100",
            "oxygen_saturation": 92.0,
            "severity_score": 0,
            "is_emergency": True,
            "preferred_ward": "ICU",
            "status": PatientStatus.WAITING,
        },
        {
            "name": "Jane Smith",
            "age": 45,
            "gender": "Female",
            "symptoms": "Broken arm",
            "heart_rate": 72,
            "blood_pressure": "120/80",
            "oxygen_saturation": 98.0,
            "severity_score": 0,
            "is_emergency": False,
            "preferred_ward": "GENERAL",
            "status": PatientStatus.WAITING,
        },
        {
            "name": "Bob Johnson",
            "age": 72,
            "gender": "Male",
            "symptoms": "Appendicitis",
            "heart_rate": 88,
            "blood_pressure": "135/85",
            "oxygen_saturation": 96.0,
            "severity_score": 0,
            "is_emergency": False,
            "preferred_ward": "SURGERY",
            "status": PatientStatus.WAITING,
        },
    ]
    
    for patient_data in dummy_patients:
        if not session.query(Patient).filter_by(name=patient_data["name"]).first():
            patient = Patient(**patient_data)
            session.add(patient)
    
    session.commit()
    
    print(f"✓ Database initialized at {db_path}")
    print(f"✓ Created 4 wards with 5 beds each (20 total)")
    print(f"✓ Seeded 3 dummy patients")
    
    session.close()
    return engine


if __name__ == "__main__":
    db_path = os.getenv("DB_PATH", "./data/hospital.db")
    init_db(db_path)
