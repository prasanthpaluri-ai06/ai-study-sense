"""
WebSocket Manager integrating with HardwareCommunicationService.
Provides seamless bidirectional bridging between Laptop Brain, Frontend Dashboard,
and ESP32 Hardware Controllers.
"""

import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket

from backend.app.services.hardware_service import hardware_service

logger = logging.getLogger("studysense.websocket")


class WebSocketManager:
    def __init__(self):
        self._service = hardware_service

    @property
    def frontend_connections(self) -> Set[WebSocket]:
        return self._service.frontend_sockets

    @property
    def latest_hardware_state(self) -> dict:
        return self._service.get_status_summary()

    async def connect_frontend(self, websocket: WebSocket):
        await self._service.connect_frontend(websocket)

    def disconnect_frontend(self, websocket: WebSocket):
        self._service.disconnect_frontend(websocket)

    async def connect_esp32(self, websocket: WebSocket, device_id: str = "default_esp32"):
        await self._service.handle_esp32_connect(websocket, device_id)

    def disconnect_esp32(self, device_id: str = "default_esp32"):
        import asyncio
        asyncio.create_task(self._service.handle_esp32_disconnect(device_id))

    async def send_to_esp32(self, payload: dict, device_id: Optional[str] = None):
        return await self._service._transmit_to_esp32(payload, target_device_id=device_id)

    async def broadcast_to_frontend(self, message: dict):
        await self._service.broadcast_to_frontend(message)

    async def update_study_state(
        self,
        posture: str = "good",
        focus: str = "focused",
        session: str = "active",
        oled_animation: Optional[str] = None,
        led_state: Optional[str] = None,
        message: Optional[str] = None,
        timer_seconds: Optional[int] = None,
        session_id: Optional[int] = None,
    ):
        return await self._service.send_structured_state(
            posture=posture,
            focus=focus,
            session=session,
            custom_message=message,
            timer_seconds=timer_seconds,
            override_led=led_state,
            override_oled=oled_animation,
            session_id=session_id,
        )


ws_manager = WebSocketManager()
