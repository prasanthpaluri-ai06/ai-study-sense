# AI StudySense

> **"An AI-powered study companion that helps students improve academic performance, focus, consistency, study habits, and learning efficiency."**

AI StudySense is an integrated hardware + software + AI academic platform where:
- The **laptop is the computational brain** running computer vision and AI services.
- The **laptop camera** is the primary visual sensing device (face authentication, posture analysis, focus/presence estimation).
- The **FastAPI backend** acts as the core database and state decision engine.
- The **React + Vite dashboard** serves as the central student interface.
- The **ESP32 microcontroller** acts as the wireless IoT hardware bridge, driving a 0.96-inch OLED face display and physical Traffic Light module.

---

## 🏗️ Architecture & Modular Structure

```
Study_helper/
├── AI_StudySense_Detailed_Project_Specification.md   # Primary functional specification
├── README.md                                         # Project documentation & runbook
├── requirements.txt                                  # Backend Python dependencies
├── .env.example / .env                               # Environment configurations
├── pytest.ini                                        # Test configuration
│
├── backend/                                          # FastAPI REST & WebSocket Backend
│   └── app/
│       ├── api/v1/                                   # REST route endpoints
│       │   ├── endpoints/                            # health, auth, users, academic, syllabus, sessions, hardware, ai
│       │   └── api.py                                # API aggregator router
│       ├── core/                                     # config, security (bcrypt + JWT), websocket_manager
│       ├── db/                                       # session, base (SQLAlchemy async engine & metadata)
│       ├── models/                                   # User, Subject, Mark, Assignment, Syllabus, StudySession, etc.
│       ├── schemas/                                  # Pydantic data schemas & contracts
│       └── main.py                                   # FastAPI entrypoint & WebSocket handlers
│
├── ai/                                               # Python AI & Computer Vision Subsystem
│   ├── academic/                                     # Coach, Syllabus Parser, Quiz & Revision Generator, Weakness Detector
│   ├── vision/                                       # Posture Analyzer (Hysteresis Buffer), Face Auth, Focus Tracker
│   └── config.py                                     # Posture thresholds, timing buffers, and parameters
│
├── hardware/                                         # ESP32 Firmware & Hardware Documentation
│   ├── README.md                                     # Pinouts and wiring diagram
│   └── esp32_studysense/
│       ├── esp32_studysense.ino                      # ESP32 Arduino C++ firmware (Wi-Fi + WebSocket + GPIOs)
│       └── display_animations.h                      # OLED animation engine (SSD1306 128x64)
│
├── frontend/                                         # React + Vite Central Application
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── api/                                      # REST fetch client & WebSocket telemetry manager
│       ├── components/                               # Navbar, HardwareStatusBadge, StatCards
│       ├── pages/                                    # Dashboard, StudySession, Academics, Roadmap, AICoach, Auth
│       ├── App.jsx                                   # Root layout & real-time telemetry wiring
│       └── main.jsx
│
├── docs/                                             # Specifications & Guides
│   ├── ARCHITECTURE.md                               # System design, data flows & hardware state machine
│   ├── HARDWARE_SETUP.md                             # Breadboard wiring instructions & LED mapping
│   └── API_SPECIFICATION.md                          # REST and WebSocket API documentation
│
└── tests/                                            # Unit and Integration Test Suite
    ├── test_health.py                                # Backend health endpoints
    ├── test_auth.py                                  # User registration, login, and profile
    ├── test_posture_logic.py                         # Posture buffer state machine (Good -> Buffer -> Bad)
    ├── test_academic.py                              # Subjects, marks, and syllabus roadmaps
    └── test_websocket.py                             # Real-time WebSocket communication for ESP32 & web dashboard
```

---

## 🚦 Hardware Mapping & Posture Feedback Loop

| Posture State | Traffic Light LED | OLED Expression | Description |
|---|---|---|---|
| **Good Posture** | 🟢 **GREEN** | `^_^` `POSTURE GOOD` | Upright spinal alignment |
| **Buffer Warning** | 🟡 **YELLOW** | `-_-` `[!] WARNING` | Slouch detected temporarily (< 10s buffer) |
| **Bad Posture** | 🔴 **RED** | `>_<` `POSTURE ALERT` | Poor posture confirmed (> 10s threshold) |
| **Break / Idle** | ⚪ Off / Green | `~_~` / `o_o` | Session rest or standby |

---

## 🚀 Quick Start Guide

### 1. Backend Setup & Run

```bash
# 1. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1    # On Windows PowerShell
# source .venv/bin/activate     # On Linux / macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start FastAPI server with live reload
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **WebSocket Endpoint:** `ws://localhost:8000/ws/dashboard` & `ws://localhost:8000/ws/esp32`

---

### 2. Frontend Setup & Run

```bash
cd frontend
npm install
npm run dev
```

- Access the web application at [http://localhost:5173](http://localhost:5173).

---

### 3. Run Test Suite

```bash
pytest -v
```

All 5 unit and integration tests verify:
- ✅ Authentication flow (User ID + password + profile creation)
- ✅ Service health check and hardware status
- ✅ Posture state transitions & LED hysteresis buffer logic
- ✅ Academic management & syllabus parsing into checklist roadmaps
- ✅ WebSocket bidirectional synchronization for ESP32 and dashboard

---

### 4. ESP32 Hardware Deployment
1. Connect ESP32, 0.96-inch SSD1306 OLED (I2C SDA=GPIO 21, SCL=GPIO 22), and Traffic Light module (Red=GPIO 18, Yellow=GPIO 19, Green=GPIO 23).
2. Configure Wi-Fi credentials and laptop IP in `hardware/esp32_studysense/esp32_studysense.ino`.
3. Flash the sketch to the ESP32 using Arduino IDE.
