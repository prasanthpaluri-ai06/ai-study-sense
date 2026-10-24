from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ESP32Command(BaseModel):
    posture: Optional[str] = "good"  # good, buffer, bad
    focus: Optional[str] = "focused"
    session: Optional[str] = "active"
    led_state: Optional[str] = None  # GREEN, YELLOW, RED, OFF
    oled_animation: Optional[str] = None
    message: Optional[str] = None
    timer_seconds: Optional[int] = None
    session_id: Optional[int] = None


class HardwareTestCommand(BaseModel):
    led_state: str = Field(..., description="GREEN, YELLOW, RED, or OFF")
    oled_animation: Optional[str] = Field(
        None,
        description="good_posture, buffer_warning, bad_posture, focus_warning, break_time, session_complete, idle",
    )
    custom_message: Optional[str] = Field(None, description="Optional custom text for OLED screen")


class HardwareDeviceMetadata(BaseModel):
    device_id: str
    connected: bool
    connected_at: str
    last_seen: str
    seconds_since_last_seen: float
    firmware_version: str
    chip_model: str
    mac_address: Optional[str] = None
    capabilities: List[str] = []
    uptime_ms: int = 0
    rssi_dbm: Optional[int] = None
    free_heap_bytes: Optional[int] = None


class HardwareStateResponse(BaseModel):
    connected: bool
    device_id: Optional[str] = None
    posture: str
    focus: str
    session: str
    led_state: str
    oled_animation: str
    oled_title: Optional[str] = None
    oled_subtitle: Optional[str] = None
    oled_expression: Optional[str] = None
    message: str
    timer_seconds: Optional[int] = 0
    timer_formatted: Optional[str] = "00:00"
    last_updated: Optional[str] = None
    test_mode_active: Optional[bool] = False
    active_devices_count: Optional[int] = 0
    devices: Optional[List[Dict[str, Any]]] = []
