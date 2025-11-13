import sqlite3
import datetime

# --- Database Initialization ---
def get_db_connection():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Drop tables if they exist for a clean start
    cursor.execute('DROP TABLE IF EXISTS beds')
    cursor.execute('DROP TABLE IF EXISTS patients')
    cursor.execute('DROP TABLE IF EXISTS agent_logs')

    # --- Create Tables ---
    # Bed Status: Available, Occupied, Cleaning
    cursor.execute('''
    CREATE TABLE beds (
        bed_id TEXT PRIMARY KEY,
        ward TEXT NOT NULL,
        status TEXT NOT NULL,
        current_patient_id INTEGER
    )
    ''')

    # Patient Status: Waiting, Admitted, Discharged
    cursor.execute('''
    CREATE TABLE patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        severity INTEGER NOT NULL,
        status TEXT NOT NULL,
        assigned_bed_id TEXT
    )
    ''')

    # Agent Log
    cursor.execute('''
    CREATE TABLE agent_logs (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        message TEXT NOT NULL
    )
    ''')

    # --- Populate Initial Beds ---
    # 5 beds for Ward A, 5 for Ward B
    beds_to_add = []
    for ward in ['A', 'B']:
        for i in range(1, 6):
            beds_to_add.append((f'{ward}-{i}', ward, 'Available', None))
    
    cursor.executemany('INSERT INTO beds (bed_id, ward, status, current_patient_id) VALUES (?, ?, ?, ?)', beds_to_add)

    conn.commit()
    conn.close()
    log_message('System', 'Database initialized with 10 beds.')

# --- Utility Functions ---
def log_message(agent_name, message):
    conn = get_db_connection()
    timestamp = datetime.datetime.now().isoformat()
    conn.execute('INSERT INTO agent_logs (timestamp, agent_name, message) VALUES (?, ?, ?)',
                 (timestamp, agent_name, message))
    conn.commit()
    conn.close()

# --- Patient Management Functions ---
def add_patient(name, severity):
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO patients (name, severity, status) VALUES (?, ?, ?)',
                          (name, severity, 'Waiting'))
    patient_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_message('AdmissionForm', f'New patient {name} (Severity: {severity}) added to waiting list.')
    return patient_id

def get_patient_details(patient_id):
    conn = get_db_connection()
    patient = conn.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,)).fetchone()
    conn.close()
    return dict(patient) if patient else None

def get_highest_priority_waiting_patient():
    conn = get_db_connection()
    # Highest severity, then earliest admission (lowest patient_id)
    patient = conn.execute('SELECT * FROM patients WHERE status = ? ORDER BY severity DESC, patient_id ASC LIMIT 1',
                           ('Waiting',)).fetchone()
    conn.close()
    return dict(patient) if patient else None

def assign_bed_to_patient(patient_id, bed_id):
    conn = get_db_connection()
    # Update bed
    conn.execute('UPDATE beds SET status = ?, current_patient_id = ? WHERE bed_id = ?',
                 ('Occupied', patient_id, bed_id))
    # Update patient
    conn.execute('UPDATE patients SET status = ?, assigned_bed_id = ? WHERE patient_id = ?',
                 ('Admitted', bed_id, patient_id))
    conn.commit()
    conn.close()

def discharge_patient(patient_id):
    conn = get_db_connection()
    patient = get_patient_details(patient_id)
    if not patient or patient['assigned_bed_id'] is None:
        return None
    
    bed_id = patient['assigned_bed_id']
    
    # Update patient
    conn.execute('UPDATE patients SET status = ?, assigned_bed_id = ? WHERE patient_id = ?',
                 ('Discharged', None, patient_id))
    # Update bed
    conn.execute('UPDATE beds SET status = ?, current_patient_id = ? WHERE bed_id = ?',
                 ('Cleaning', None, bed_id))
    conn.commit()
    conn.close()
    return bed_id # Return the bed that needs cleaning

# --- Bed Management Functions ---
def find_available_bed(ward_preference):
    conn = get_db_connection()
    query = 'SELECT * FROM beds WHERE status = ?'
    params = ['Available']
    
    if ward_preference != 'Any':
        query += ' AND ward = ?'
        params.append(ward_preference)
        
    query += ' LIMIT 1'
    
    bed = conn.execute(query, params).fetchone()
    
    # If no preference-matching bed, try any
    if not bed and ward_preference != 'Any':
        bed = conn.execute('SELECT * FROM beds WHERE status = ? LIMIT 1', ('Available',)).fetchone()
        
    conn.close()
    return dict(bed) if bed else None

def set_bed_status(bed_id, status):
    conn = get_db_connection()
    conn.execute('UPDATE beds SET status = ? WHERE bed_id = ?', (status, bed_id))
    conn.commit()
    conn.close()

# --- Dashboard Query Functions ---
def get_all_bed_statuses():
    conn = get_db_connection()
    beds = conn.execute('SELECT b.*, p.name, p.severity FROM beds b LEFT JOIN patients p ON b.current_patient_id = p.patient_id ORDER BY b.bed_id').fetchall()
    conn.close()
    return [dict(bed) for bed in beds]

def get_admitted_patients():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients WHERE status = ? ORDER BY name', ('Admitted',)).fetchall()
    conn.close()
    return [dict(p) for p in patients]

def get_waiting_list():
    conn = get_db_connection()
    patients = conn.execute('SELECT * FROM patients WHERE status = ? ORDER BY severity DESC, patient_id ASC', ('Waiting',)).fetchall()
    conn.close()
    return [dict(p) for p in patients]

def get_low_severity_admitted_patients():
    conn = get_db_connection()
    # Get patients with severity 1 or 2
    patients = conn.execute('SELECT p.name, p.severity, p.assigned_bed_id FROM patients p WHERE p.status = ? AND p.severity <= ?', ('Admitted', 2)).fetchall()
    conn.close()
    return [dict(p) for p in patients]

def get_all_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM agent_logs ORDER BY log_id DESC LIMIT 100').fetchall()
    conn.close()
    return [dict(log) for log in logs]

if __name__ == '__main__':
    init_db()
    print("Database initialized.")