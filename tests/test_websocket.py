import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.core.websocket_manager import ws_manager


def test_dashboard_and_esp32_websockets():
    client = TestClient(app)

    # 1. Connect frontend WebSocket client
    with client.websocket_connect("/ws/dashboard") as ws_frontend:
        initial_msg = ws_frontend.receive_json()
        assert initial_msg["type"] == "HARDWARE_STATUS"
        assert initial_msg["data"]["led_state"] == "GREEN"

        # 2. Connect ESP32 WebSocket client in parallel
        with client.websocket_connect("/ws/esp32?device_id=test_esp32") as ws_esp32:
            # Backend should broadcast connection to frontend
            esp_connect_event = ws_frontend.receive_json()
            assert esp_connect_event["type"] == "ESP32_CONNECTED"
            assert esp_connect_event["device_id"] == "test_esp32"
