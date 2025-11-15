import sqlite3
import time

db_path = "./data/hospital.db"

print("Checking database state after admission\n")

# Connect to database
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check waiting list entries
print("1. Waiting List Entries:")
cursor.execute("SELECT * FROM waiting_list_entry")
entries = cursor.fetchall()
print(f"   Count: {len(entries)}")
for row in entries:
    print(f"   - Patient {row['patient_id']}: position {row['position']}")

# Check activity log
print("\n2. Activity Log Entries:")
cursor.execute("SELECT * FROM activity_log")
activities = cursor.fetchall()
print(f"   Count: {len(activities)}")
for row in activities:
    print(f"   - {row['sender']} -> {row['receiver']}: {row['action']}")

# Check beds
print("\n3. Bed Status:")
cursor.execute("SELECT status, COUNT(*) FROM bed GROUP BY status")
status_counts = cursor.fetchall()
for row in status_counts:
    print(f"   {row[0]}: {row[1]}")

# Check patients
print("\n4. Patients:")
cursor.execute("SELECT id, name, status, severity_score FROM patient ORDER BY id DESC LIMIT 5")
patients = cursor.fetchall()
for row in patients:
    print(f"   - {row['name']} (ID {row['id']}): {row['status']}, severity {row['severity_score']}")

conn.close()
