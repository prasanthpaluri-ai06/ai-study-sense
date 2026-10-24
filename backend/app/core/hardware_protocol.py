"""
AI StudySense - Hardware Communication Protocol Specification
Defines state constants, message schemas, and priority resolution logic
for Wi-Fi WebSocket communication between Laptop Brain and ESP32 Controller.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HardwareStateType(str, Enum):
    # Posture States (Highest Priority for Traffic Light)
    POSTURE_GOOD = "POSTURE_GOOD"
    POSTURE_BUFFER = "POSTURE_BUFFER"
    POSTURE_BAD = "POSTURE_BAD"

    # Focus States
    FOCUS_GOOD = "FOCUS_GOOD"
    FOCUS_WARNING = "FOCUS_WARNING"

    # Session States
    BREAK = "BREAK"
    SESSION_ACTIVE = "SESSION_ACTIVE"
    SESSION_COMPLETE = "SESSION_COMPLETE"

    # Connection States
    ESP32_CONNECTED = "ESP32_CONNECTED"
    ESP32_DISCONNECTED = "ESP32_DISCONNECTED"

    # System States
    HEARTBEAT = "HEARTBEAT"
    HANDSHAKE = "HANDSHAKE"
    HANDSHAKE_ACK = "HANDSHAKE_ACK"
    TEST_COMMAND = "TEST_COMMAND"
    ERROR = "ERROR"


class TrafficLightColor(str, Enum):
    OFF = "OFF"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class OLEDAnimation(str, Enum):
    IDLE = "idle"
    GOOD_POSTURE = "good_posture"       # Expression: (^_^)
    BUFFER_WARNING = "buffer_warning"   # Expression: (-_-)
    BAD_POSTURE = "bad_posture"         # Expression: (>_<)
    FOCUS_WARNING = "focus_warning"     # Expression: (O.O)
    BREAK_TIME = "break_time"           # Expression: (Zzz)
    SESSION_COMPLETE = "session_complete" # Expression: (★_★)
    COUNTDOWN_TIMER = "countdown_timer"
    CUSTOM_TEXT = "custom_text"


class OLEDPayload(BaseModel):
    animation: OLEDAnimation = OLEDAnimation.IDLE
    title: str = "AI StudySense"
    subtitle: Optional[str] = "Ready"
    expression: Optional[str] = "^_^"
    timer_seconds: Optional[int] = None
    timer_formatted: Optional[str] = None
    progress_percent: Optional[int] = None


class ESP32Handshake(BaseModel):
    type: str = "HANDSHAKE"
    device_id: str = "esp32_studysense_01"
    firmware_version: str = "1.0.0"
    chip_model: Optional[str] = "ESP32-WROOM-32"
    mac_address: Optional[str] = None
    capabilities: List[str] = Field(default_factory=lambda: ["traffic_light", "oled_ssd1306", "buzzer"])


class ESP32Heartbeat(BaseModel):
    type: str = "HEARTBEAT"
    device_id: str
    uptime_ms: int = 0
    rssi: Optional[int] = None  # Wi-Fi signal strength in dBm
    free_heap: Optional[int] = None


class StructuredESP32Message(BaseModel):
    """
    Structured payload transmitted from Laptop Brain to ESP32.
    Never sends raw video/AI frames.
    """
    type: str = "STATE_UPDATE"
    event: str = "POSTURE_GOOD"
    seq: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    led: TrafficLightColor = TrafficLightColor.GREEN
    oled: OLEDPayload = Field(default_factory=OLEDPayload)
    posture: str = "good"
    focus: str = "focused"
    session: str = "active"
    posture_status: HardwareStateType = HardwareStateType.POSTURE_GOOD
    focus_status: HardwareStateType = HardwareStateType.FOCUS_GOOD
    session_status: HardwareStateType = HardwareStateType.SESSION_ACTIVE
    session_id: Optional[int] = None
    message: Optional[str] = None


class HardwarePriorityResolver:
    """
    Resolves conflicting telemetry into strict deterministic Traffic Light and OLED states.
    Priority Rule:
      Posture has highest priority for the traffic-light module:
      1. POSTURE_BAD -> RED
      2. POSTURE_BUFFER -> YELLOW
      3. POSTURE_GOOD -> GREEN (with secondary states determining OLED animation)
    """

    @classmethod
    def resolve_state(
        cls,
        posture: str = "good",
        focus: str = "focused",
        session: str = "active",
        custom_message: Optional[str] = None,
        timer_seconds: Optional[int] = None,
        override_led: Optional[str] = None,
        override_oled: Optional[str] = None,
    ) -> Dict[str, Any]:
        p_norm = posture.strip().lower()
        f_norm = focus.strip().lower()
        s_norm = session.strip().lower()

        # 1. Resolve Traffic Light Color (Strict Posture Priority)
        if override_led:
            led = TrafficLightColor(override_led.upper())
        elif p_norm in ("bad", "poor", "red", "posture_bad"):
            led = TrafficLightColor.RED
        elif p_norm in ("buffer", "warning", "yellow", "posture_buffer"):
            led = TrafficLightColor.YELLOW
        else:
            led = TrafficLightColor.GREEN

        # 2. Resolve OLED Animation & Expressions
        if override_oled:
            oled_anim = OLEDAnimation(override_oled.lower())
        elif p_norm in ("bad", "poor", "posture_bad"):
            oled_anim = OLEDAnimation.BAD_POSTURE
        elif p_norm in ("buffer", "warning", "posture_buffer"):
            oled_anim = OLEDAnimation.BUFFER_WARNING
        elif f_norm in ("distracted", "away", "warning", "focus_warning"):
            oled_anim = OLEDAnimation.FOCUS_WARNING
        elif s_norm in ("break", "break_time"):
            oled_anim = OLEDAnimation.BREAK_TIME
        elif s_norm in ("complete", "completed", "session_complete"):
            oled_anim = OLEDAnimation.SESSION_COMPLETE
        else:
            oled_anim = OLEDAnimation.GOOD_POSTURE

        # 3. Map expression and text
        expression_map = {
            OLEDAnimation.GOOD_POSTURE: "^_^",
            OLEDAnimation.BUFFER_WARNING: "-_-",
            OLEDAnimation.BAD_POSTURE: ">_<",
            OLEDAnimation.FOCUS_WARNING: "O.O",
            OLEDAnimation.BREAK_TIME: "Zzz",
            OLEDAnimation.SESSION_COMPLETE: "★_★",
            OLEDAnimation.IDLE: "^_^",
            OLEDAnimation.COUNTDOWN_TIMER: "0_0",
            OLEDAnimation.CUSTOM_TEXT: "•_•",
        }

        title_map = {
            OLEDAnimation.GOOD_POSTURE: "FLOW STATE",
            OLEDAnimation.BUFFER_WARNING: "SIT STRAIGHT",
            OLEDAnimation.BAD_POSTURE: "POSTURE ALERT",
            OLEDAnimation.FOCUS_WARNING: "EYES ON STUDY",
            OLEDAnimation.BREAK_TIME: "REST BREAK",
            OLEDAnimation.SESSION_COMPLETE: "SESSION DONE",
            OLEDAnimation.IDLE: "STUDYSENSE READY",
            OLEDAnimation.COUNTDOWN_TIMER: "FOCUS TIMER",
            OLEDAnimation.CUSTOM_TEXT: "NOTIFICATION",
        }

        timer_formatted = None
        if timer_seconds is not None and timer_seconds >= 0:
            mins = timer_seconds // 60
            secs = timer_seconds % 60
            timer_formatted = f"{mins:02d}:{secs:02d}"

        oled_payload = OLEDPayload(
            animation=oled_anim,
            title=title_map.get(oled_anim, "AI StudySense"),
            subtitle=custom_message or ("Ergonomics Good" if led == TrafficLightColor.GREEN else "Adjust Posture"),
            expression=expression_map.get(oled_anim, "^_^"),
            timer_seconds=timer_seconds,
            timer_formatted=timer_formatted,
        )

        posture_state = (
            HardwareStateType.POSTURE_BAD
            if led == TrafficLightColor.RED
            else (HardwareStateType.POSTURE_BUFFER if led == TrafficLightColor.YELLOW else HardwareStateType.POSTURE_GOOD)
        )

        focus_state = HardwareStateType.FOCUS_WARNING if oled_anim == OLEDAnimation.FOCUS_WARNING else HardwareStateType.FOCUS_GOOD
        session_state = (
            HardwareStateType.BREAK
            if oled_anim == OLEDAnimation.BREAK_TIME
            else (HardwareStateType.SESSION_COMPLETE if oled_anim == OLEDAnimation.SESSION_COMPLETE else HardwareStateType.SESSION_ACTIVE)
        )

        # Determine semantic event name
        if oled_anim == OLEDAnimation.SESSION_COMPLETE:
            event = "SESSION_COMPLETE"
        elif oled_anim == OLEDAnimation.BREAK_TIME:
            event = "BREAK"
        elif "phone" in (custom_message or "").lower():
            event = "PHONE_DISTRACTION"
        elif oled_anim == OLEDAnimation.FOCUS_WARNING:
            event = "FOCUS_WARNING"
        elif led == TrafficLightColor.RED:
            event = "POSTURE_BAD"
        elif led == TrafficLightColor.YELLOW:
            event = "POSTURE_WARNING"
        elif s_norm == "idle":
            event = "IDLE"
        else:
            event = "POSTURE_GOOD"

        return {
            "event": event,
            "led": led,
            "oled": oled_payload,
            "posture_status": posture_state,
            "focus_status": focus_state,
            "session_status": session_state,
            "message": custom_message or oled_payload.title,
        }
