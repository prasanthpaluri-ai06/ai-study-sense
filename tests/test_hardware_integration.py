import json
import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from backend.app.core.hardware_protocol import (
    HardwarePriorityResolver,
    HardwareStateType,
    OLEDAnimation,
    TrafficLightColor,
)
from backend.app.main import app
from backend.app.services.hardware_service import hardware_service


def test_hardware_priority_resolver_logic():
    """Unit test strict traffic light and OLED priority resolution."""
    # 1. Posture Bad -> RED LED overrides everything
    res_bad = HardwarePriorityResolver.resolve_state(
        posture="bad",
        focus="focused",
        session="active",
    )
    assert res_bad["led"] == TrafficLightColor.RED
    assert res_bad["oled"].animation == OLEDAnimation.BAD_POSTURE
    assert res_bad["oled"].expression == ">_<"
    assert res_bad["posture_status"] == HardwareStateType.POSTURE_BAD

    # 2. Posture Buffer -> YELLOW LED
    res_buffer = HardwarePriorityResolver.resolve_state(
        posture="buffer",
        focus="distracted",
        session="active",
    )
    assert res_buffer["led"] == TrafficLightColor.YELLOW
    assert res_buffer["oled"].animation == OLEDAnimation.BUFFER_WARNING
    assert res_buffer["oled"].expression == "-_-"

    # 3. Posture Good + Focus Distracted -> GREEN LED + Focus Warning OLED
    res_focus_warn = HardwarePriorityResolver.resolve_state(
        posture="good",
        focus="distracted",
        session="active",
    )
    assert res_focus_warn["led"] == TrafficLightColor.GREEN
    assert res_focus_warn["oled"].animation == OLEDAnimation.FOCUS_WARNING
    assert res_focus_warn["oled"].expression == "O.O"

    # 4. Break Session -> GREEN LED + Break OLED
    res_break = HardwarePriorityResolver.resolve_state(
        posture="good",
        focus="focused",
        session="break",
    )
    assert res_break["led"] == TrafficLightColor.GREEN
    assert res_break["oled"].animation == OLEDAnimation.BREAK_TIME
    assert res_break["oled"].expression == "Zzz"

    # 5. Timer Formatting
    res_timer = HardwarePriorityResolver.resolve_state(
        posture="good",
        timer_seconds=1500,
    )
    assert res_timer["oled"].timer_formatted == "25:00"


def test_esp32_websocket_handshake_and_heartbeat():
    """Integration test ESP32 WebSocket handshake, heartbeat, and state synchronization."""
    client = TestClient(app)

    with client.websocket_connect("/ws/esp32?device_id=test_esp32_node") as ws:
        # 1. Send Handshake
        handshake_payload = {
            "type": "HANDSHAKE",
            "device_id": "test_esp32_node",
            "firmware_version": "1.0.0",
            "chip_model": "ESP32-WROOM-32",
            "mac_address": "AA:BB:CC:DD:EE:FF",
            "capabilities": ["traffic_light", "oled_ssd1306"],
        }
        ws.send_text(json.dumps(handshake_payload))

        # Receive Handshake ACK
        ack_raw = ws.receive_text()
        ack = json.loads(ack_raw)
        assert ack["type"] == "HANDSHAKE_ACK"
        assert ack["status"] == "authenticated"

        # Receive Initial Synced State Frame
        sync_raw = ws.receive_text()
        sync_frame = json.loads(sync_raw)
        assert sync_frame["type"] == "STATE_UPDATE"
        assert "led" in sync_frame
        assert "oled" in sync_frame

        # 2. Send Heartbeat
        heartbeat_payload = {
            "type": "HEARTBEAT",
            "device_id": "test_esp32_node",
            "uptime_ms": 120000,
            "rssi": -55,
            "free_heap": 230000,
        }
        ws.send_text(json.dumps(heartbeat_payload))

        pong_raw = ws.receive_text()
        pong = json.loads(pong_raw)
        assert pong["type"] == "PONG"
        assert pong["device_id"] == "test_esp32_node"


@pytest.mark.asyncio
async def test_hardware_rest_api_and_test_mode(client: AsyncClient):
    """Test Hardware REST Endpoints: status, manual command, test mode, ping, and protocol."""
    # 1. GET /api/v1/hardware/status
    status_res = await client.get("/api/v1/hardware/status")
    assert status_res.status_code == 200
    st = status_res.json()
    assert "connected" in st
    assert "led_state" in st
    assert "oled_animation" in st

    # 2. POST /api/v1/hardware/test-mode -> Test GREEN
    test_green = await client.post(
        "/api/v1/hardware/test-mode",
        json={"led_state": "GREEN", "oled_animation": "good_posture", "custom_message": "TEST GREEN"},
    )
    assert test_green.status_code == 200
    res_g = test_green.json()
    assert res_g["led"] == "GREEN"
    assert res_g["state"]["led_state"] == "GREEN"
    assert res_g["state"]["oled_expression"] == "^_^"

    # 3. POST /api/v1/hardware/test-mode -> Test YELLOW
    test_yellow = await client.post(
        "/api/v1/hardware/test-mode",
        json={"led_state": "YELLOW", "oled_animation": "buffer_warning", "custom_message": "TEST YELLOW"},
    )
    assert test_yellow.status_code == 200
    res_y = test_yellow.json()
    assert res_y["led"] == "YELLOW"
    assert res_y["state"]["led_state"] == "YELLOW"
    assert res_y["state"]["oled_expression"] == "-_-"

    # 4. POST /api/v1/hardware/test-mode -> Test RED
    test_red = await client.post(
        "/api/v1/hardware/test-mode",
        json={"led_state": "RED", "oled_animation": "bad_posture", "custom_message": "TEST RED"},
    )
    assert test_red.status_code == 200
    res_r = test_red.json()
    assert res_r["led"] == "RED"
    assert res_r["state"]["led_state"] == "RED"
    assert res_r["state"]["oled_expression"] == ">_<"

    # 5. POST /api/v1/hardware/command (Structured Dispatch)
    cmd_res = await client.post(
        "/api/v1/hardware/command",
        json={
            "posture": "good",
            "focus": "focused",
            "session": "active",
            "message": "Deep Work Flow",
            "timer_seconds": 1200,
        },
    )
    assert cmd_res.status_code == 200
    assert cmd_res.json()["status"] == "dispatched"
    assert cmd_res.json()["state"]["timer_formatted"] == "20:00"

    # 6. POST /api/v1/hardware/ping
    ping_res = await client.post("/api/v1/hardware/ping")
    assert ping_res.status_code == 200

    # 7. GET /api/v1/hardware/protocol
    proto_res = await client.get("/api/v1/hardware/protocol")
    assert proto_res.status_code == 200
    proto = proto_res.json()
    assert proto["protocol_version"] == "1.0.0"
    assert "POSTURE_GOOD" in proto["states"]
    assert "POSTURE_BAD" in proto["states"]
    assert len(proto["oled_animations"]) >= 6


def test_esp32_device_dual_route_and_state_ack():
    """Verify /ws/device route with full handshake, state update, state ack, and heartbeat."""
    client = TestClient(app)

    with client.websocket_connect("/ws/device?device_id=studysense_esp32_01") as ws:
        # Handshake
        ws.send_text(json.dumps({
            "type": "HANDSHAKE",
            "device_id": "studysense_esp32_01",
            "firmware_version": "2.1.0",
            "chip_model": "ESP32-D0WD-V3",
            "mac_address": "24:6F:28:AB:CD:EF",
            "capabilities": ["traffic_light", "oled_ssd1306"],
        }))

        ack = json.loads(ws.receive_text())
        assert ack["type"] == "HANDSHAKE_ACK"
        assert ack["status"] == "authenticated"

        # Initial state update pushed immediately upon connection
        state_frame = json.loads(ws.receive_text())
        assert state_frame["type"] == "STATE_UPDATE"
        assert "event" in state_frame
        assert "posture" in state_frame
        assert "focus" in state_frame
        assert "session" in state_frame
        assert "led" in state_frame
        assert "oled" in state_frame

        # Send STATE_ACK
        ws.send_text(json.dumps({
            "type": "STATE_ACK",
            "device_id": "studysense_esp32_01",
            "applied_led": state_frame["led"],
            "applied_animation": state_frame["oled"]["animation"],
        }))

        # Send Heartbeat
        ws.send_text(json.dumps({
            "type": "HEARTBEAT",
            "device_id": "studysense_esp32_01",
            "uptime_ms": 30000,
            "rssi": -48,
            "free_heap": 210000,
        }))

        pong = json.loads(ws.receive_text())
        assert pong["type"] == "PONG"
        assert pong["device_id"] == "studysense_esp32_01"

