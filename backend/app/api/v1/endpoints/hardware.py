import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.services.hardware_service import hardware_service
from backend.app.schemas.hardware import (
    ESP32Command,
    HardwareStateResponse,
    HardwareTestCommand,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/status", response_model=HardwareStateResponse)
async def get_hardware_status():
    """
    Retrieve live hardware connection status, connected ESP32 devices metadata,
    current traffic light color, and OLED animation state.
    """
    return HardwareStateResponse(**hardware_service.get_status_summary())


@router.post("/command")
async def send_hardware_command(command: ESP32Command):
    """
    Manually or programmatically dispatch a state update to connected ESP32 device(s)
    and broadcast telemetry to the web dashboard.
    """
    state = await hardware_service.send_structured_state(
        posture=command.posture or "good",
        focus=command.focus or "focused",
        session=command.session or "active",
        custom_message=command.message,
        timer_seconds=command.timer_seconds,
        override_led=command.led_state,
        override_oled=command.oled_animation,
        session_id=command.session_id,
    )
    return {
        "status": "dispatched",
        "state": state,
    }


@router.post("/test-mode")
async def execute_hardware_test(test_cmd: HardwareTestCommand):
    """
    Hardware Test Mode: Manually send Traffic Light colors (GREEN, YELLOW, RED)
    and OLED animations to physical ESP32 for pre-session hardware verification.
    """
    state = await hardware_service.execute_test_command(
        led_state=test_cmd.led_state,
        oled_animation=test_cmd.oled_animation,
        custom_message=test_cmd.custom_message,
    )
    return {
        "status": "test_executed",
        "led": test_cmd.led_state.upper(),
        "oled_animation": test_cmd.oled_animation,
        "state": state,
    }


@router.post("/ping")
async def ping_esp32_devices():
    """
    Sends ping frame to all active ESP32 devices to verify connection liveness.
    """
    summary = hardware_service.get_status_summary()
    if not summary["connected"]:
        return {
            "status": "disconnected",
            "message": "No active ESP32 controller currently connected",
            "active_devices": 0,
        }

    await hardware_service._transmit_to_esp32({
        "type": "PING",
        "timestamp": hardware_service.current_state.get("last_updated"),
    })

    return {
        "status": "ping_sent",
        "active_devices": summary["active_devices_count"],
        "devices": summary["devices"],
    }


@router.get("/protocol")
async def get_hardware_protocol_docs() -> Dict[str, Any]:
    """
    Returns the formal specification of the AI StudySense Hardware Protocol
    including supported message types, traffic light priority rules, and OLED animations.
    """
    return {
        "protocol_version": "1.0.0",
        "transport": "Wi-Fi WebSocket (JSON Text Frames)",
        "endpoints": {
            "esp32_websocket": "/ws/esp32",
            "dashboard_websocket": "/ws/dashboard",
        },
        "states": [
            "POSTURE_GOOD",
            "POSTURE_BUFFER",
            "POSTURE_BAD",
            "FOCUS_GOOD",
            "FOCUS_WARNING",
            "BREAK",
            "SESSION_ACTIVE",
            "SESSION_COMPLETE",
            "ESP32_CONNECTED",
            "ESP32_DISCONNECTED",
            "HEARTBEAT",
            "ERROR",
        ],
        "priority_rule": "Posture has highest priority for Traffic Light: BAD (RED) > BUFFER (YELLOW) > GOOD (GREEN).",
        "oled_animations": [
            {"id": "good_posture", "expression": "^_^", "meaning": "Optimal posture & focus"},
            {"id": "buffer_warning", "expression": "-_-", "meaning": "Buffer warning, sit straight"},
            {"id": "bad_posture", "expression": ">_<", "meaning": "Poor posture alert"},
            {"id": "focus_warning", "expression": "O.O", "meaning": "Eyes away from screen"},
            {"id": "break_time", "expression": "Zzz", "meaning": "Study break active"},
            {"id": "session_complete", "expression": "★_★", "meaning": "Session successfully finished"},
            {"id": "idle", "expression": "^_^", "meaning": "Ready for study session"},
        ],
    }
