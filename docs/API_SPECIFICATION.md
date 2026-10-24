# AI StudySense - API Specification

## 1. REST Endpoints

### Health Check
- `GET /health` or `GET /api/v1/health`
  - Returns backend status, environment, and ESP32 hardware connection status.

### Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` - Create student account (User ID + password + profile).
- `POST /api/v1/auth/login` - Authenticate with User ID + password.
- `POST /api/v1/auth/face/enroll` - Enroll face embedding template.
- `POST /api/v1/auth/face/login` - Biometric face authentication.

### Academic Management (`/api/v1/academic`)
- `GET /api/v1/academic/subjects` - List subjects with calculated average scores.
- `POST /api/v1/academic/subjects` - Add new subject.
- `GET /api/v1/academic/marks` - List marks (CAT, Quiz, Lab, Midterm, EndSem).
- `POST /api/v1/academic/marks` - Record assessment mark.
- `GET /api/v1/academic/assignments` - List assignments with due dates and priorities.
- `POST /api/v1/academic/assignments` - Create assignment.
- `PATCH /api/v1/academic/assignments/{id}` - Update assignment status or progress.

### Syllabus & Roadmap (`/api/v1/syllabus`)
- `GET /api/v1/syllabus/roadmaps` - Retrieve checklist-based conceptual roadmaps by module.
- `POST /api/v1/syllabus/upload` - Upload and parse syllabus text into modules and topics.
- `POST /api/v1/syllabus/topics/{id}/toggle-status` - Toggle topic progress status.

### Study Sessions (`/api/v1/sessions`)
- `POST /api/v1/sessions/start` - Start study session (Pomodoro, 52/17, Active Recall, Spaced Repetition, Feynman).
- `POST /api/v1/sessions/{id}/end` - Complete study session and compute metrics.
- `POST /api/v1/sessions/{id}/posture-telemetry` - Log real-time posture telemetry.
- `GET /api/v1/sessions/recent` - List recent sessions and productivity scores.

### AI Services (`/api/v1/ai`)
- `POST /api/v1/ai/quiz/generate` - Generate topic quiz questions.
- `POST /api/v1/ai/revision/generate` - Generate 8-step revision package.
- `GET /api/v1/ai/study-health` - Compute composite Study Health Score (0-100).
- `GET /api/v1/ai/recommendations` - Prioritized recommendations based on marks, weaknesses, and deadlines.
- `GET /api/v1/ai/resources` - Categorized resources (Videos, Articles, Practice, References).

### Hardware Control (`/api/v1/hardware`)
- `GET /api/v1/hardware/status` - Live hardware connection state, LED color, and OLED animation.
- `POST /api/v1/hardware/command` - Manual dispatch of LED and OLED commands.

## 2. WebSocket Endpoints
- `ws://<host>:8000/ws/esp32` - ESP32 hardware device connection.
- `ws://<host>:8000/ws/dashboard` - Frontend real-time telemetry streaming.
