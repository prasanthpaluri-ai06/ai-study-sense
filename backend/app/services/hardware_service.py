"""
AI StudySense - Dedicated Hardware Communication Service
Manages WebSocket sessions with ESP32 controllers, connection handshakes,
heartbeat health, watchdog timeouts, priority state resolution, and test commands.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

from backend.app.core.hardware_protocol import (
    ESP32Handshake,
    ESP32Heartbeat,
    HardwarePriorityResolver,
    HardwareStateType,
    OLEDAnimation,
    OLEDPayload,
    StructuredESP32Message,
    TrafficLightColor,
)

logger = logging.getLogger("studysense.hardware")


class HardwareDeviceSession:
    def __init__(self, device_id: str, websocket: WebSocket):
        self.device_id = device_id
        self.websocket = websocket
        self.connected_at = datetime.now(timezone.utc)
        self.last_seen = datetime.now(timezone.utc)
        self.firmware_version = "1.0.0"
        self.chip_model = "ESP32"
        self.mac_address: Optional[str] = None
        self.capabilities: List[str] = ["traffic_light", "oled_ssd1306"]
        self.uptime_ms = 0
        self.rssi: Optional[int] = None
        self.free_heap: Optional[int] = None
        self.is_active = True
        self.seq_counter = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "connected": self.is_active,
            "connected_at": self.connected_at.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "seconds_since_last_seen": (datetime.now(timezone.utc) - self.last_seen).total_seconds(),
            "firmware_version": self.firmware_version,
            "chip_model": self.chip_model,
            "mac_address": self.mac_address,
            "capabilities": self.capabilities,
            "uptime_ms": self.uptime_ms,
            "rssi_dbm": self.rssi,
            "free_heap_bytes": self.free_heap,
        }


class HardwareCommunicationService:
    """
    Central hardware service managing ESP32 Wi-Fi WebSocket controllers
    and broadcasting telemetry to the web dashboard.
    """

    HEARTBEAT_TIMEOUT_SECONDS = 15.0

    def __init__(self):
        self.device_sessions: Dict[str, HardwareDeviceSession] = {}
        self.frontend_sockets: Set[WebSocket] = set()
        self.current_state: Dict[str, Any] = {
            "connected": False,
            "device_id": None,
            "posture": "good",
            "focus": "focused",
            "session": "idle",
            "led_state": "GREEN",
            "oled_animation": "good_posture",
            "oled_title": "AI StudySense",
            "oled_subtitle": "Ready",
            "oled_expression": "^_^",
            "message": "AI StudySense Ready",
            "timer_seconds": 0,
            "timer_formatted": "00:00",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "test_mode_active": False,
        }
        self.seq_num = 0
        self._watchdog_task: Optional[asyncio.Task] = None

    def start_watchdog(self):
        if self._watchdog_task is None or self._watchdog_task.done():
            self._watchdog_task = asyncio.create_task(self._heartbeat_watchdog())

    async def _heartbeat_watchdog(self):
        """Monitors ESP32 heartbeats and detects dropouts."""
        while True:
            try:
                await asyncio.sleep(5.0)
                now = datetime.now(timezone.utc)
                for device_id, session in list(self.device_sessions.items()):
                    if session.is_active:
                        diff = (now - session.last_seen).total_seconds()
                        if diff > self.HEARTBEAT_TIMEOUT_SECONDS:
                            logger.warning(
                                "ESP32 [%s] timed out (no heartbeat for %.1fs). Marking DISCONNECTED.",
                                device_id,
                                diff,
                            )
                            session.is_active = False
                            self._update_connectivity_state()
                            await self.broadcast_to_frontend({
                                "type": HardwareStateType.ESP32_DISCONNECTED.value,
                                "device_id": device_id,
                                "reason": f"Heartbeat timeout ({diff:.1f}s)",
                                "timestamp": now.isoformat(),
                            })
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in hardware watchdog: %s", e)

    def _update_connectivity_state(self):
        active_sessions = [s for s in self.device_sessions.values() if s.is_active]
        self.current_state["connected"] = len(active_sessions) > 0
        self.current_state["device_id"] = active_sessions[0].device_id if active_sessions else None

    # --- Connection Lifecycle ---

    async def handle_esp32_connect(self, websocket: WebSocket, device_id: str = "esp32_studysense") -> HardwareDeviceSession:
        await websocket.accept()
        session = HardwareDeviceSession(device_id=device_id, websocket=websocket)
        self.device_sessions[device_id] = session
        self._update_connectivity_state()
        self.start_watchdog()

        logger.info("ESP32 [%s] connected over WebSocket.", device_id)
        # Notify dashboard of connection
        await self.broadcast_to_frontend({
            "type": HardwareStateType.ESP32_CONNECTED.value,
            "device_id": device_id,
            "metadata": session.to_dict(),
        })
        return session

    async def handle_esp32_handshake(self, device_id: str, payload: dict) -> dict:
        """Processes initial identification handshake from ESP32."""
        session = self.device_sessions.get(device_id)
        if session:
            session.firmware_version = payload.get("firmware_version", "1.0.0")
            session.chip_model = payload.get("chip_model", "ESP32")
            session.mac_address = payload.get("mac_address")
            session.capabilities = payload.get("capabilities", ["traffic_light", "oled_ssd1306"])
            session.last_seen = datetime.now(timezone.utc)
            session.is_active = True

        self._update_connectivity_state()

        ack_payload = {
            "type": HardwareStateType.HANDSHAKE_ACK.value,
            "status": "authenticated",
            "server_time": datetime.now(timezone.utc).isoformat(),
            "heartbeat_interval_sec": 5,
        }

        # Send ACK first
        if session and session.is_active:
            try:
                await session.websocket.send_text(json.dumps(ack_payload))
            except Exception as e:
                logger.error("Failed sending HANDSHAKE_ACK to %s: %s", device_id, e)

        # Sync current state to newly joined ESP32
        await self.send_structured_state(
            posture=self.current_state.get("posture", "good"),
            focus=self.current_state.get("focus", "focused"),
            session=self.current_state.get("session", "idle"),
            custom_message="SYNCED",
            device_id=device_id,
        )

        return ack_payload

    def handle_esp32_heartbeat(self, device_id: str, payload: dict) -> dict:
        """Processes periodic heartbeat message."""
        session = self.device_sessions.get(device_id)
        now = datetime.now(timezone.utc)
        if session:
            session.last_seen = now
            session.is_active = True
            session.uptime_ms = payload.get("uptime_ms", session.uptime_ms)
            session.rssi = payload.get("rssi", session.rssi)
            session.free_heap = payload.get("free_heap", session.free_heap)

        self._update_connectivity_state()
        return {
            "type": "PONG",
            "device_id": device_id,
            "server_time": now.isoformat(),
        }

    async def handle_esp32_disconnect(self, device_id: str):
        if device_id in self.device_sessions:
            self.device_sessions[device_id].is_active = False
        self._update_connectivity_state()
        logger.warning("ESP32 [%s] disconnected.", device_id)
        await self.broadcast_to_frontend({
            "type": HardwareStateType.ESP32_DISCONNECTED.value,
            "device_id": device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # --- Frontend Web Dashboard Sockets ---

    async def connect_frontend(self, websocket: WebSocket):
        await websocket.accept()
        self.frontend_sockets.add(websocket)
        # Send live state upon connect
        await websocket.send_json({
            "type": "HARDWARE_STATUS",
            "data": self.get_status_summary(),
        })

    def disconnect_frontend(self, websocket: WebSocket):
        self.frontend_sockets.discard(websocket)

    async def broadcast_to_frontend(self, message: dict):
        if not self.frontend_sockets:
            return

        dead_sockets = set()
        for ws in self.frontend_sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error("Failed sending to frontend websocket: %s", e)
                dead_sockets.add(ws)

        for dead in dead_sockets:
            self.frontend_sockets.discard(dead)

    # --- Structured State Updates & Dispatch ---

    async def send_structured_state(
        self,
        posture: str = "good",
        focus: str = "focused",
        session: str = "active",
        custom_message: Optional[str] = None,
        timer_seconds: Optional[int] = None,
        override_led: Optional[str] = None,
        override_oled: Optional[str] = None,
        device_id: Optional[str] = None,
        session_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates resolved traffic light priority and OLED animation,
        encapsulates into a structured JSON frame, and sends to ESP32 + dashboard.
        """
        self.seq_num += 1
        resolved = HardwarePriorityResolver.resolve_state(
            posture=posture,
            focus=focus,
            session=session,
            custom_message=custom_message,
            timer_seconds=timer_seconds,
            override_led=override_led,
            override_oled=override_oled,
        )

        led_color = resolved["led"]
        oled_payload = resolved["oled"]

        # Build structured message
        msg = StructuredESP32Message(
            type="STATE_UPDATE",
            event=resolved.get("event", "POSTURE_GOOD"),
            seq=self.seq_num,
            timestamp=datetime.now(timezone.utc).isoformat(),
            led=led_color,
            oled=oled_payload,
            posture=posture,
            focus=focus,
            session=session,
            posture_status=resolved["posture_status"],
            focus_status=resolved["focus_status"],
            session_status=resolved["session_status"],
            session_id=session_id,
            message=resolved["message"],
        )

        # Update cached state
        self.current_state.update({
            "posture": posture,
            "focus": focus,
            "session": session,
            "led_state": led_color.value,
            "oled_animation": oled_payload.animation.value,
            "oled_title": oled_payload.title,
            "oled_subtitle": oled_payload.subtitle,
            "oled_expression": oled_payload.expression,
            "message": resolved["message"],
            "timer_seconds": timer_seconds or 0,
            "timer_formatted": oled_payload.timer_formatted or "00:00",
            "last_updated": msg.timestamp,
        })

        # Send to ESP32
        await self._transmit_to_esp32(msg.model_dump(), target_device_id=device_id)

        # Broadcast telemetry to web dashboard
        await self.broadcast_to_frontend({
            "type": "STUDY_TELEMETRY",
            "data": self.get_status_summary(),
        })

        return self.current_state

    async def execute_test_command(
        self,
        led_state: str,
        oled_animation: Optional[str] = None,
        custom_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes explicit hardware test command for Green/Yellow/Red and OLED expressions.
        """
        self.current_state["test_mode_active"] = True
        return await self.send_structured_state(
            posture="good" if led_state.upper() == "GREEN" else ("buffer" if led_state.upper() == "YELLOW" else "bad"),
            override_led=led_state.upper(),
            override_oled=oled_animation,
            custom_message=custom_message or f"TEST: {led_state.upper()}",
        )

    async def _transmit_to_esp32(self, payload: dict, target_device_id: Optional[str] = None) -> bool:
        """Transmits serialized JSON text frame to connected ESP32 client(s)."""
        active_sessions = [
            s for d_id, s in self.device_sessions.items()
            if s.is_active and (target_device_id is None or d_id == target_device_id)
        ]

        if not active_sessions:
            return False

        message_str = json.dumps(payload)
        success = False

        for session in active_sessions:
            try:
                await session.websocket.send_text(message_str)
                success = True
            except Exception as e:
                logger.error("Failed sending frame to ESP32 [%s]: %s", session.device_id, e)
                session.is_active = False

        self._update_connectivity_state()
        return success

    def get_status_summary(self) -> Dict[str, Any]:
        active_sessions = [s.to_dict() for s in self.device_sessions.values() if s.is_active]
        return {
            **self.current_state,
            "active_devices_count": len(active_sessions),
            "devices": active_sessions,
        }


# Global singleton instance
hardware_service = HardwareCommunicationService()
