# AI StudySense — Comprehensive Project Technical Reference (`algo_use.md`)

This document outlines the complete technology stack, core innovations, AI algorithms, APIs, and key architectural highlights powering **AI StudySense**.

---

## 1. Tech Stack for the Entire Project

### A. Frontend (Web Application)
- **Framework & Tooling**: React (v18/v19), Vite (ultra-fast build tool and dev server).
- **Styling & UI Components**: Tailwind CSS, Lucide React (vector icon suite), custom animated progress rings, responsive glassmorphism design system.
- **State & Networking**: Axios (HTTP client with automatic JWT refresh interceptor), Native Browser WebSocket API (for live bi-directional telemetry).
- **Client-Side Vision & Multimedia**: HTML5 Canvas API & MediaDevices Web API for real-time camera feed capture, HUD posture bounding boxes, and frame extraction.

### B. Backend (AI Inference Engine & API Gateway)
- **Runtime & Web Framework**: Python 3.13, FastAPI (high-performance asynchronous REST and WebSocket server), Uvicorn (ASGI server).
- **Data Validation & Serialization**: Pydantic v2 (strict type enforcement and schemas).
- **Database & ORM**: SQLite (development/embedded) with SQLAlchemy ORM, database migrations, connection pooling.
- **Authentication & Security**: OAuth2 with JWT (JSON Web Tokens), bcrypt / passlib for secure password hashing, rolling token refresh mechanics.
- **Real-Time Communication**: FastAPI WebSockets (`/ws/device`, `/ws/dashboard`, `/ws/study`, `/ws/session`) with event broadcast managers and client heartbeat watchdogs.

### C. Computer Vision, Document Intelligence & AI
- **Pose & Facial Analysis**: Google MediaPipe (Pose Landmarker, Holistic, Face Mesh) and OpenCV (`cv2`).
- **Object / Distraction Detection**: YOLO (You Only Look Once) / OpenCV DNN object detection model for mobile phone localization within camera field of view.
- **Document Ingestion & OCR**: PyPDF2, pdfplumber, python-docx, Tesseract OCR (`pytesseract`) for scanned syllabus digitization.
- **Generative AI / LLM**: Google Gemini API (`google-genai` SDK / Google Generative AI Python SDK).

### D. IoT Hardware & Embedded Firmware
- **Microcontroller**: ESP32 38-Pin Development Board (Tensilica Xtensa 32-bit dual-core, 2.4 GHz Wi-Fi).
- **Display**: 0.96″ SSD1306 I2C OLED (128×64 resolution, 100 kHz standard mode, non-blocking 12 FPS animation engine).
- **Physical Indicator**: 3-Color Traffic Light LED Module (Green = GPIO 25, Yellow = GPIO 26, Red = GPIO 27).
- **Embedded Software Stack**: Arduino C/C++, `WiFi.h`, `WebSocketsClient` (Markus Sattler), `ArduinoJson` (v6/v7), `Adafruit_SSD1306`, `Adafruit_GFX`.

---

## 2. Unique Points About the Project

1. **Dual Edge-and-Cloud AI Architecture**:
   - Heavy AI computer vision inference runs locally on the student's laptop GPU/CPU (preserving privacy and keeping video streams offline).
   - Minimalist, low-latency state packets are broadcast over WebSockets to an external ESP32 physical companion bot that operates on the student's desk.

2. **Sequential Dual-Point Posture Calibration**:
   - Rather than relying on rigid geometric assumptions, AI StudySense calibrates dynamically to each student's unique physique, chair height, and camera angle.
   - Requires explicit **Upright Reference** and **Slouched Reference** capture before starting a session to compute personalized baseline thresholds.

3. **3-Second Forgiving Buffer System**:
   - Avoids alert fatigue and false positives. If a student briefly leans forward to take a note, a Yellow LED warning and a live 3s countdown trigger on the OLED; a red alert triggers only if slouching persists beyond 3 seconds.

4. **Syllabus-Driven Autonomous Academic Planning**:
   - Students register subjects by simply uploading course PDFs or syllabus photos.
   - The system automatically extracts modules, topics, and subtopics into an interactive checklist, and schedules them throughout the semester based on exam dates and assignment deadlines.

5. **Desk Presence & Phone Distraction Auditing**:
   - Tracks not only when the student is working, but also logs timestamped absence intervals (empty seat detection) and active phone distraction episodes.
   - Automatically pauses distraction tracking during scheduled restorative breaks.

6. **Physical Ambient Feedback (Traffic Light + Expressive OLED)**:
   - Removes the need to keep the web dashboard active on the screen while studying.
   - The physical bot's expressive face animations and color-coded LEDs provide peripheral awareness of focus status without screen distractions.

---

## 3. AI Algorithms, APIs & External Services

| AI Algorithm / API / Model | Purpose & Exact Usage | Configuration / Key Details |
| :--- | :--- | :--- |
| **Google MediaPipe Pose Landmarker** | **Spine & Neck Ergonomics**: Analyzes 33 3D skeletal landmarks (ears, shoulders, nose, hips). Calculates vertical spine angle, ear-to-shoulder displacement, and neck inclination. | Runs on laptop backend via OpenCV; processes frames at ~1 FPS during live study sessions. |
| **MediaPipe Face / Presence Tracking** | **Absence & Face Landmark Verification**: Detects when the user leaves their desk. Measures absence timestamps, frequency, and total absent duration. | Bounding box & landmark confidence thresholds; flags absence if confidence drops below threshold during active session. |
| **YOLO / Mobile Object Detector** | **Phone Distraction Detection**: Detects handheld smartphone objects in the camera frame. Triggers an instant `PHONE_DISTRACTION` state and flags session logs. | Only active during focus intervals (disabled during scheduled restorative breaks). |
| **SuperMemo SM-2 Spaced Repetition Algorithm** | **Cognitive Memory & Topic Retention**: Calculates optimal revision intervals ($I$) and ease factors ($EF$) based on student confidence ratings ($0-5$) on completed syllabus topics. | Implemented algorithmically in backend: $EF' = EF + (0.1 - (5 - q) \times (0.08 + (5 - q) \times 0.02))$. |
| **Google Gemini API (`gemini-1.5-flash` / `gemini-pro`)** | **Syllabus Intelligence & AI Study Coach**: Parses raw unstructured text/tables from uploaded syllabus documents into structured JSON modules/topics. Generates personalized semester study distribution and daily priority tasks. | `GEMINI_API_KEY` environment variable; utilized via `google-genai` / `google.generativeai` SDK. |
| **Tesseract OCR (`pytesseract`)** | **Document Image Text Extraction**: Extracts text from scanned syllabus PDF pages and syllabus photos before passing to Gemini for structural schema mapping. | Requires local Tesseract binary / `pdf2image` pipeline with fallback heuristic parser. |
| **Heuristic Posture Baseline Distance Classifier** | **Calibrated Slouch Detection**: Compares live neck-to-shoulder Euclidean vectors against user's stored good-pose and bad-pose calibration vectors. | Fallback client-side and server-side calculation for high resilience even with network jitter. |

---

## 4. All Important Points About the Project

- **Hardware Pinout Strict Compliance**:
  - OLED Display: `VCC` $\rightarrow$ `3V3`, `GND` $\rightarrow$ `GND`, `SDA` $\rightarrow$ `GPIO 21`, `SCL` $\rightarrow$ `GPIO 22`.
  - Traffic Light Module: `G` $\rightarrow$ `GPIO 25`, `Y` $\rightarrow$ `GPIO 26`, `R` $\rightarrow$ `GPIO 27`, `GND` $\rightarrow$ `GND`.
- **Network Routing & Local Wi-Fi**:
  - The laptop runs FastAPI bound to `0.0.0.0:8000` so that external Wi-Fi devices (ESP32) can communicate via LAN.
  - ESP32 connects via `ws://<LAPTOP_LOCAL_IP>:8000/ws/device` (or `/ws/esp32`).
- **Hardware Priority Hierarchy**:
  - When multiple triggers occur simultaneously, the priority engine resolves alerts in this strict order:
    1. **Absence Alert** (`RED` LED, `?_?` confused face)
    2. **Phone Distraction** (`RED` LED, `X_X` alert face)
    3. **Persistent Bad Posture** (`RED` LED, `>_<` slouch alert)
    4. **Buffer Warning** (`YELLOW` LED, `O_O` 3s countdown)
    5. **Flow State / Upright Posture** (`GREEN` LED, `^_^` smiling face + timer)
- **Token & Session Resilience**:
  - JWT tokens are auto-refreshed in the background via `/api/v1/auth/refresh`.
  - Vision calibration and telemetry endpoints accept optional authentication to prevent expired tokens from interrupting physical setup.
- **Non-Blocking Firmware Design**:
  - Arduino firmware executes at ~12 FPS with zero blocking `delay()` calls during live operation.
  - Automatic 5-second `HEARTBEAT` frames prevent server watchdog disconnects.
