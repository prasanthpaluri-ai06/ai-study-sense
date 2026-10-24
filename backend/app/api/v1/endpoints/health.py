from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.core.websocket_manager import ws_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Service health check endpoint returning system status, environment,
    and active hardware connectivity status.
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hardware": {
            "esp32_connected": ws_manager.latest_hardware_state["connected"],
            "device_id": ws_manager.latest_hardware_state["device_id"],
            "active_clients": len(ws_manager.frontend_connections)
        }
    }
