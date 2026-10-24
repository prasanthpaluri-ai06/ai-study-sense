# AI StudySense - System Architecture & Design

## 1. High-Level Architecture

```
                                  AI STUDYSENSE
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
          WEB APPLICATION                                  AI ENGINE
     (React + Vite Dashboard)                       (Laptop Brain - Python)
                 |                                             |
                 |                                     +-------+-------+
                 |                                     |               |
                 |                                  Camera         Analytics
                 |                                     |               |
                 |                                     v               |
                 |                              Computer Vision        |
                 |                              (Face / Posture)       |
                 |                                     |               |
                 |                                     +-------+-------+
                 |                                             |
                 +----------------------+----------------------+
                                        |
                                 Decision Engine
                                 (FastAPI Backend)
                                        |
                         +--------------+--------------+
                         |                             |
                         v                             v
                   Web Dashboard                 ESP32 Hardware
             (Telemetry & Analytics)             (Wi-Fi / WebSocket)
                                                       |
                                         +-------------+-------------+
                                         |                           |
                                         v                           v
                                     0.96" OLED                Traffic Light
                                  (Animated Bot Face)       (Green / Yellow / Red)
```

## 2. API & Component Boundaries

### Frontend (React + Vite)
- **Port:** `5173`
- **Role:** Central academic management, live study sessions with real-time posture indicators, syllabus roadmaps, and AI coach tools.
- **Protocols:** REST (HTTP) for CRUD operations and WebSocket (`/ws/dashboard`) for real-time telemetry.

### Backend (FastAPI + SQLAlchemy)
- **Port:** `8000`
- **Role:** Authentication, academic database, roadmap generation, AI orchestration, and WebSocket synchronization.
- **Database:** SQLite (async via `aiosqlite`) during development, ready for PostgreSQL.

### AI & Vision Engine (Python)
- **Role:** Laptop camera processing for posture analysis with temporal buffer hysteresis (Good -> Buffer -> Bad), face verification, focus estimation, and academic AI tools (quiz generator, revision generator, weakness detector, AI study coach).

### Hardware Subsystem (ESP32)
- **Role:** Physical visual & LED feedback.
- **Traffic Light Mapping:**
  - **GREEN:** Good posture
  - **YELLOW:** Posture buffer warning (temporary deviation)
  - **RED:** Confirmed poor posture (> threshold)
- **OLED Display:** Expressive facial animations (`^_^`, `-_-`, `>_<`) and status notices.
