from fastapi import APIRouter
from backend.app.api.v1.endpoints import academic, ai, analytics, auth, hardware, health, planner, sessions, syllabus, users, vision

api_router = APIRouter()

# Register endpoint subrouters
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(academic.router, prefix="/academic", tags=["Academic Management"])
api_router.include_router(planner.router, prefix="/planner", tags=["AI Academic Planner & Calendars"])
api_router.include_router(syllabus.router, prefix="/syllabus", tags=["Syllabus & Roadmaps"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Study Sessions"])
api_router.include_router(hardware.router, prefix="/hardware", tags=["Hardware & ESP32"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI Academic Services"])
api_router.include_router(vision.router, prefix="/vision", tags=["Laptop Camera Vision AI"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Growth"])
