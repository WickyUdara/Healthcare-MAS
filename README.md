# 🏥 Hospital Bed Management Multi-Agent System (MAS)

A complete demonstration of a Multi-Agent System architecture for intelligent hospital bed management. This system showcases **agent communication**, **negotiation**, **situational adaptivity**, and **real-time resource management** in a hospital setting.

## ✨ Features

- ✅ **8 Specialized Agents**: CoordinatorAgent, AdmissionAgent, BedAssignmentAgent, DischargeAgent, CleaningAgent, WaitingListAgent, ResourceManagerAgent, CriticalPatientAgent
- ✅ **Intelligent Severity Scoring**: Uses Gemini API (with deterministic fallback)
- ✅ **Automatic Bed Assignment**: Negotiation-based assignment with 3-round negotiation loop
- ✅ **Waiting List Auto-Assignment**: Automatic assignment when beds become available
- ✅ **Emergency Preemption**: Critical patients can preempt lower-severity occupants
- ✅ **Bed Cleaning Simulation**: 10-second cleaning cycle with state management
- ✅ **Real-Time Activity Logging**: All agent communications persisted and visualized
- ✅ **Sequence Diagrams**: Mermaid-based visualization of agent interactions
- ✅ **Live Dashboard**: Real-time occupancy metrics and patient statistics
- ✅ **REST API**: Complete FastAPI backend with WebSocket support
- ✅ **React Frontend**: Modern UI with real-time updates
- ✅ **Docker Support**: Full containerization with Docker Compose
- ✅ **Pure Python Fallback**: Works without LangGraph if unavailable

## 📋 System Architecture

```
Hospital Layout:
├─ ICU Ward (5 beds)
├─ GENERAL Ward (5 beds)
├─ SURGERY Ward (5 beds)
└─ MATERNITY Ward (5 beds)

Agent Roles:
├─ CoordinatorAgent: Orchestrates admission → assignment workflow
├─ AdmissionAgent: Validates patients, computes severity
├─ BedAssignmentAgent: Finalizes bed assignments
├─ ResourceManagerAgent: Central bed/occupancy tracking
├─ BedAssignmentAgent: Proposes bed matches
├─ DischargeAgent: Handles patient discharge
├─ CleaningAgent: Simulates bed cleaning (10s)
├─ WaitingListAgent: Manages auto-assignment from waiting list
└─ CriticalPatientAgent: Handles emergency preemption
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **Docker & Docker Compose** (optional, for containerized setup)
- **GEMINI_API_KEY** (optional, for AI severity scoring)

### Local Setup

#### 1. Clone and Setup Backend

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Initialize Database

```bash
python -m db.init_db
```

This creates:
- SQLite database at `./data/hospital.db`
- 4 wards with 5 beds each (20 total)
- 3 dummy patients for testing

#### 3. Start Backend Server

```bash
python main.py
```

Backend runs at: http://localhost:8000
API docs: http://localhost:8000/docs

#### 4. Setup & Start Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

### Docker Setup

```bash
# Build and start both services
docker-compose up --build

# Or just start (if already built)
docker-compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173

---

## 🧪 Demo Workflow (Testing Auto-Assignment)

This script demonstrates the full admission → assignment → discharge → cleaning → auto-assign workflow.

### Manual Demo Steps

1. **Admit 3 Patients** (Admission page)
   - Patient 1: Name="Alice Smith", Symptoms="Fever", HR=88, BP="120/80", O2=98%, Ward="GENERAL"
   - Patient 2: Name="Bob Jones", Symptoms="Severe chest pain", HR=105, BP="160/100", O2=90%, Emergency=Yes, Ward="ICU"
   - Patient 3: Name="Carol Davis", Symptoms="Broken arm", HR=75, BP="110/70", O2=99%, Ward="GENERAL"

   **Observation**: 
   - Severity scores computed (Bob=highest due to chest pain + emergency flag)
   - Bob auto-assigned to ICU if available
   - Alice/Carol placed in waiting list

2. **View Bed Assignment** (Bed Assignment page)
   - See all 20 beds grouped by ward
   - Observe occupancy rates and waiting list

3. **Discharge First Admitted Patient** (Discharge page)
   - Click "Discharge" for the admitted patient
   - Bed status changes to "Cleaning"

   **Observation**:
   - DischargeAgent marks patient as discharged
   - CleaningAgent simulates 10-second cleaning
   - Bed status: "occupied" → "cleaning" (⏳ 10s) → "available" (✓)

4. **Watch Auto-Assignment** (Bed Assignment page - Real-time polling)
   - After cleaning completes, WaitingListAgent auto-assigns
   - Top-priority patient from waiting list auto-assigned
   - New bed status updates in real-time

5. **View Agent Communications** (Activity Log page)
   - See all FIPA-like messages exchanged between agents
   - Click transaction ID to expand sequence diagram
   - Mermaid diagram shows agent communication flow

### Automated Test Script

```bash
cd tests
pytest test_agents.py -v
```

Tests validate:
- ✓ Admission creates patient with severity scoring
- ✓ Cleaning agent simulates 10s cleaning
- ✓ Auto-assignment selects highest-priority patient
- ✓ Message format compliance

---

## 📡 API Endpoints

### Admission & Discharge

```bash
# Admit a patient
curl -X POST http://localhost:8000/admit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 65,
    "gender": "Male",
    "symptoms": "Chest pain, SOB",
    "heart_rate": 95,
    "blood_pressure": "160/100",
    "oxygen_saturation": 92,
    "is_emergency": true,
    "preferred_ward": "ICU"
  }'

# Discharge a patient
curl -X POST http://localhost:8000/discharge/1
```

### Status & Monitoring

```bash
# Get all beds
curl http://localhost:8000/beds

# Get all patients
curl http://localhost:8000/patients

# Get waiting list
curl http://localhost:8000/waiting_list

# Get occupancy metrics
curl http://localhost:8000/metrics

# Get activity log (last 50)
curl http://localhost:8000/activity_log

# Get sequence diagram for transaction
curl http://localhost:8000/sequence_diagram/{transaction_id}
```

---

## 🔍 Understanding Agent Communication

### Message Format (FIPA-like)

All agent messages follow this structure:

```json
{
  "id": "uuid-string",
  "timestamp": "2025-01-15T10:30:45.123456",
  "transaction_id": "admission-workflow-uuid",
  "performative": "request|inform|propose|accept|reject|query",
  "sender": "AdmissionAgent",
  "receiver": "CoordinatorAgent",
  "content": {
    "patient_id": 1,
    "name": "John Doe",
    "severity": 75
  },
  "reason": "Human-readable explanation"
}
```

### Where to Find Agent Communication Code

1. **Message Creation** (with explicit comments):
   - `backend/agents/base_agent.py` → `create_message()` method
   - Each agent file shows message creation at key decision points

2. **Message Consumption**:
   - `backend/agents/base_agent.py` → `send()` and `receive()` methods
   - Activity log persisted in `activity_log.json` and database

3. **Sequence Diagram Generation**:
   - `backend/utils/mermaid_builder.py` → `build_sequence_diagram()`
   - Frontend renders via `frontend/src/components/SequenceDiagram.jsx`

### Negotiation Loop (Coordinator)

Located in `backend/agents/coordinator_agent.py`:

```python
# Lines ~50-120: 3-round negotiation
for round_num in range(1, 4):
    # Round 1-3:
    # 1. Query ResourceManager for available beds
    # 2. Propose assignment to BedAssignmentAgent
    # 3. Accept or try alternative strategies
    # If no beds: ask WaitingListAgent to reorder or CriticalPatientAgent for preemption
```

---

## 🧹 Cleaning Simulation

Located in `backend/agents/cleaning_agent.py`:

```python
# Simulates 10-second cleaning with asyncio
await asyncio.sleep(10)  # Line ~50

# After cleaning:
# 1. Bed status: "cleaning" → "available"
# 2. Notify WaitingListAgent
# 3. Trigger auto-assignment
```

To observe in UI:
1. Go to **Cleaning & Turnaround** page
2. Discharge a patient → bed enters "cleaning" state
3. Watch countdown (updates every 1 second)
4. After 10 seconds, bed becomes "available"
5. Go to **Bed Assignment** → waiting list auto-assign happens immediately

---

## 🔐 Severity Scoring

### With Gemini API (Recommended)

1. Set `GEMINI_API_KEY` in `.env`:
   ```bash
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

2. Backend uses `gemini-2.5-flash` to score severity (0-100) based on:
   - Patient vitals (HR, BP, O2)
   - Symptoms (keyword matching)
   - Age and emergency flag

### Without Gemini (Fallback)

Automatically used if `GEMINI_API_KEY` not set. Uses weighted calculation:

```
Score = Age_factor + Heart_rate_factor + BP_factor + O2_factor + Symptoms_keywords
Result: 0-100 (clamped)
```

Located in `backend/utils/gemini_client.py` → `_score_severity_fallback()`

---

## 📊 Frontend Pages

| Page | Purpose | Real-Time? |
|------|---------|-----------|
| **Home** | System overview & feature navigation | No |
| **Admission** | Patient admission form & results | No |
| **Bed Assignment** | View all beds, occupancy, waiting list | Yes (2s) |
| **Cleaning & Turnaround** | Monitor bed cleaning progress | Yes (1s) |
| **Discharge** | Discharge admitted patients | Yes (2s) |
| **Activity Log** | View & filter agent messages, sequence diagrams | Yes (2s) |
| **Dashboard** | Occupancy metrics, charts, ward statistics | Yes (3s) |

---

## 🗂️ Project Structure

```
hospital-mas/
├─ backend/
│  ├─ agents/                      # 8 Agent implementations
│  │  ├─ base_agent.py            # BaseAgent class & messaging
│  │  ├─ coordinator_agent.py      # Orchestration & negotiation
│  │  ├─ admission_agent.py        # Patient admission & severity
│  │  ├─ bed_assignment_agent.py   # Bed allocation
│  │  ├─ discharge_agent.py        # Patient discharge
│  │  ├─ cleaning_agent.py         # Bed cleaning simulation
│  │  ├─ waitinglist_agent.py      # Auto-assignment
│  │  ├─ resource_manager_agent.py # Occupancy tracking
│  │  └─ critical_patient_agent.py # Emergency preemption
│  ├─ db/
│  │  ├─ models.py               # SQLAlchemy ORM models
│  │  └─ init_db.py              # Database initialization
│  ├─ utils/
│  │  ├─ gemini_client.py        # Gemini API + fallback
│  │  ├─ message_schema.py       # Pydantic models
│  │  └─ mermaid_builder.py      # Sequence diagram generation
│  ├─ langgraph_flow.py           # LangGraph + Python fallback
│  ├─ main.py                     # FastAPI server (8000)
│  ├─ requirements.txt            # Python dependencies
│  ├─ Dockerfile                  # Backend container
│  └─ activity_log.json          # Agent communication log
│
├─ frontend/
│  ├─ src/
│  │  ├─ pages/                   # 7 main pages
│  │  │  ├─ Home.jsx
│  │  │  ├─ Admission.jsx
│  │  │  ├─ BedAssignment.jsx
│  │  │  ├─ CleaningTurnaround.jsx
│  │  │  ├─ Discharge.jsx
│  │  │  ├─ AgentActivityLog.jsx
│  │  │  └─ Dashboard.jsx
│  │  ├─ components/              # Reusable UI components
│  │  │  ├─ BedCard.jsx
│  │  │  ├─ PatientCard.jsx
│  │  │  ├─ MessageBubble.jsx
│  │  │  └─ SequenceDiagram.jsx
│  │  ├─ api/
│  │  │  └─ apiClient.js         # Axios API wrapper
│  │  ├─ App.jsx                  # Main app component
│  │  └─ main.jsx
│  ├─ package.json               # Node dependencies
│  ├─ vite.config.js             # Vite configuration
│  ├─ Dockerfile                 # Frontend container
│  └─ index.html
│
├─ tests/
│  └─ test_agents.py             # Unit tests (pytest)
│
├─ docker-compose.yml            # Multi-container orchestration
├─ .env.example                  # Environment template
└─ README.md                      # This file
```

---

## 🛠️ Technologies Used

### Backend
- **FastAPI** - RESTful API framework
- **SQLAlchemy** - ORM for database
- **Pydantic** - Data validation
- **SQLite** - Persistent storage
- **google-generativeai** - Gemini API (optional)
- **asyncio** - Async operations
- **LangGraph** - Graph-based orchestration (optional)

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **React Router** - Navigation
- **Axios** - HTTP client
- **Recharts** - Charts & visualizations
- **Mermaid** - Sequence diagrams

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Pytest** - Testing framework

---

## 📝 Demonstrated MAS Concepts

### 1. **Agent Communication**
- FIPA-like message format with performatives
- Asynchronous message passing
- Activity log persistence for audit trail
- Sequence diagrams for visualization

### 2. **Negotiation**
- 3-round negotiation loop in CoordinatorAgent
- Dynamic strategy adjustment based on resource availability
- Fallback strategies when primary options unavailable

### 3. **Situational Adaptivity**
- Severity-based prioritization
- Emergency preemption capabilities
- Auto-assignment based on preferences and availability
- Waiting list reordering based on urgency

### 4. **Resource Management**
- Centralized ResourceManagerAgent for bed tracking
- Real-time occupancy metrics per ward
- Efficient bed utilization

### 5. **Real-Time Visualization**
- Live message bubbles showing agent communications
- Mermaid sequence diagrams per transaction
- Real-time dashboard with metrics
- WebSocket support for live updates

---

## ✅ Feature Checklist

- [x] 8 specialized agents with distinct roles
- [x] FIPA-like messaging with transaction tracking
- [x] 3-round negotiation loop
- [x] Severity scoring (Gemini + fallback)
- [x] Waiting list auto-assignment
- [x] Emergency preemption logic
- [x] Bed cleaning simulation (10s)
- [x] SQLite persistence
- [x] REST API with full endpoints
- [x] WebSocket support (framework ready)
- [x] React frontend with 7 pages
- [x] Mermaid sequence diagrams
- [x] Real-time message bubbles
- [x] Docker Compose setup
- [x] Unit tests
- [x] Pure Python fallback orchestrator
- [x] Comprehensive README & demo instructions

---

## 🎯 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Database file not created | Run `python -m db.init_db` from backend directory |
| Port 8000 already in use | Change `API_PORT` in `.env` or kill process: `lsof -ti:8000 \| xargs kill -9` |
| Frontend can't reach backend | Ensure backend is running and check `VITE_API_URL` |
| Gemini API errors | Leave `GEMINI_API_KEY` empty to use fallback scoring |
| Tests fail with import errors | Run from project root: `pytest tests/test_agents.py -v` |
| Docker permission denied | Run `docker-compose` with `sudo` or add user to docker group |

---

## 📞 Support

For viva/demo purposes:
1. Follow the **Quick Start** section to set up locally
2. Run the **Demo Workflow** to see all features in action
3. Refer to **Understanding Agent Communication** to explain architecture
4. Check **Demonstrated MAS Concepts** to highlight learning objectives

---

## 📄 License

This project is created for demonstration and educational purposes.

---

**Made with ❤️ for Multi-Agent Systems demonstration**
