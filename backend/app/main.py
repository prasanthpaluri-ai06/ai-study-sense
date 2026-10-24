import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.api import api_router
from backend.app.core.config import settings
from backend.app.core.websocket_manager import ws_manager
from backend.app.db.base import Base
from backend.app.db.session import engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("studysense")


def sync_database_schema(sync_conn):
    Base.metadata.create_all(sync_conn)
    cursor = sync_conn.connection.cursor()
    for table_name, table in Base.metadata.tables.items():
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_cols = {row[1] for row in cursor.fetchall()}
            for col in table.columns:
                if col.name not in existing_cols:
                    col_type = "TEXT" if str(col.type).startswith(("JSON", "VARCHAR", "TEXT", "STRING")) else str(col.type)
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}")
                    logger.info(f"Auto-migrated column: {table_name}.{col.name}")
        except Exception as e:
            logger.debug(f"Auto-migration check for {table_name}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and sync database schema
    logger.info("Initializing and synchronizing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(sync_database_schema)
    logger.info("Database schema successfully synchronized.")
    yield
    # Shutdown: Close database engine connections
    logger.info("Shutting down AI StudySense backend...")
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="AI StudySense - AI-Powered Academic Growth and Focus Companion Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else ["*"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health check endpoints
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
async def root_health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "hardware_connected": ws_manager.latest_hardware_state["connected"],
    }


# Include API V1 Router
app.include_router(api_router, prefix="/api/v1")


from backend.app.services.hardware_service import hardware_service

# WebSocket Endpoints
@app.websocket("/ws/esp32")
@app.websocket("/ws/device")
async def websocket_esp32_endpoint(websocket: WebSocket, device_id: str = "esp32_studysense"):
    """
    Dedicated bidirectional WebSocket endpoint for ESP32 hardware controller.
    Supports /ws/device and /ws/esp32 paths for device registration, handshake,
    heartbeat monitoring, traffic light LED states, and OLED animation streaming.
    """
    await hardware_service.handle_esp32_connect(websocket, device_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                import json
                payload = json.loads(raw_data)
                msg_type = payload.get("type", "").upper()

                if msg_type == "HANDSHAKE":
                    await hardware_service.handle_esp32_handshake(device_id, payload)
                elif msg_type == "HEARTBEAT":
                    pong = hardware_service.handle_esp32_heartbeat(device_id, payload)
                    await websocket.send_text(json.dumps(pong))
                elif msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG", "device_id": device_id}))
                elif msg_type == "STATE_ACK":
                    logger.debug("ESP32 [%s] ACK state seq: %s", device_id, payload.get("seq"))
                else:
                    logger.debug("Received payload from ESP32 [%s]: %s", device_id, payload)
            except json.JSONDecodeError:
                logger.debug("Received non-JSON from ESP32 [%s]: %s", device_id, raw_data)
    except WebSocketDisconnect:
        await hardware_service.handle_esp32_disconnect(device_id)


@app.websocket("/ws/dashboard")
@app.websocket("/ws/session")
@app.websocket("/ws/study")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket endpoint for Frontend React Dashboard to receive live telemetry,
    hardware status, posture alerts, and session updates.
    """
    await hardware_service.connect_frontend(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            logger.debug("Received message from frontend WebSocket: %s", msg)
    except WebSocketDisconnect:
        hardware_service.disconnect_frontend(websocket)

