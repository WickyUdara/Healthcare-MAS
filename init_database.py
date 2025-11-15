#!/usr/bin/env python
"""
Manual database initialization script.
Run this to initialize the hospital database.
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db.init_db import init_db

db_path = "./data/hospital.db"

print(f"Initializing database at {db_path}...")
init_db(db_path)
print("✓ Database initialized successfully!")

# Verify
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM bed")
bed_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM ward")
ward_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM patient")
patient_count = cursor.fetchone()[0]

print(f"\n✓ Database contents:")
print(f"  - Wards: {ward_count}")
print(f"  - Beds: {bed_count}")
print(f"  - Patients: {patient_count}")

conn.close()
