/**
 * AI StudySense - ESP32 Hardware Firmware (v2.0.0)
 * 
 * Hardware Pin Mapping (Source of Truth):
 * ESP32 38-Pin Board -> 0.96" SSD1306 I2C OLED (128x64)
 *   - VCC / VDD -> 3V3
 *   - GND       -> GND
 *   - SCK / SCL -> GPIO 22
 *   - SDA       -> GPIO 21
 * 
 * ESP32 38-Pin Board -> Traffic Light LED Module
 *   - G (Green)  -> GPIO 25
 *   - Y (Yellow) -> GPIO 26
 *   - R (Red)    -> GPIO 27
 *   - GND        -> GND
 * 
 * Communication Architecture:
 *   Laptop Camera -> AI Inference -> FastAPI Session Engine -> WebSocket -> ESP32 -> OLED + Traffic Light
 *   - Wi-Fi Station Mode
 *   - Bi-directional JSON WebSocket Client (/ws/device or /ws/esp32)
 *   - Non-blocking OLED animation state machine (12 FPS)
 *   - Automated Heartbeat (every 5s) & Hardware Self-Test on boot
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "config.h"
#include "display_animations.h"

// ---------------- PIN DEFINITIONS (EXACT SPECIFICATION) ----------------
#define PIN_LED_GREEN   25
#define PIN_LED_YELLOW  26
#define PIN_LED_RED     27

#define PIN_I2C_SDA     21
#define PIN_I2C_SCL     22

#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_RESET      -1
#define SCREEN_ADDRESS  0x3C

// ---------------- GLOBAL INSTANCES ----------------
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
DisplayAnimationManager animManager(&display);
WebSocketsClient webSocket;

// Runtime state variables
bool isWsConnected = false;
unsigned long lastHeartbeatMs = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;

// Track active hardware states to prevent redundant animations
String lastLedState = "OFF";
String lastAnimState = "";

// ---------------- TRAFFIC LIGHT CONTROL ----------------
void setTrafficLight(bool green, bool yellow, bool red) {
    digitalWrite(PIN_LED_GREEN,  green  ? HIGH : LOW);
    digitalWrite(PIN_LED_YELLOW, yellow ? HIGH : LOW);
    digitalWrite(PIN_LED_RED,    red    ? HIGH : LOW);
}

void applyLedColor(const char* color) {
    if (strcmp(color, "GREEN") == 0) {
        setTrafficLight(true, false, false);
    } else if (strcmp(color, "YELLOW") == 0) {
        setTrafficLight(false, true, false);
    } else if (strcmp(color, "RED") == 0) {
        setTrafficLight(false, false, true);
    } else {
        // OFF or unknown safe state
        setTrafficLight(false, false, false);
    }
}

// Track detected OLED address
byte detectedOledAddress = SCREEN_ADDRESS;

// ---------------- I2C BUS SCANNER ----------------
byte scanI2CAddress() {
    Serial.println("[I2C Scanner] Scanning I2C bus (SDA=GPIO 21, SCL=GPIO 22)...");
    byte foundAddr = 0;
    int nDevices = 0;
    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        byte error = Wire.endTransmission();
        if (error == 0) {
            Serial.printf(" -> Device detected at address 0x%02X\n", addr);
            if (addr == 0x3C || addr == 0x3D) {
                foundAddr = addr;
            }
            nDevices++;
        }
    }
    if (nDevices == 0) {
        Serial.println(" [WARN] No I2C devices responded! Check wiring: VCC->3V3, GND->GND, SDA->21, SCL->22.");
    } else {
        Serial.printf(" [OK] %d device(s) found on I2C bus. Target OLED Address: 0x%02X\n", nDevices, foundAddr ? foundAddr : SCREEN_ADDRESS);
    }
    return (foundAddr != 0) ? foundAddr : SCREEN_ADDRESS;
}

// ---------------- HARDWARE SELF-TEST ----------------
void executeHardwareSelfTest() {
    Serial.println("\n==================================================");
    Serial.println("  AI StudySense - Hardware Self-Test & Diagnostics");
    Serial.println("==================================================");

    // 1. Initialize LED outputs
    pinMode(PIN_LED_GREEN,  OUTPUT);
    pinMode(PIN_LED_YELLOW, OUTPUT);
    pinMode(PIN_LED_RED,    OUTPUT);
    setTrafficLight(false, false, false);

    // 2. Test Green LED (GPIO 25)
    Serial.println("[TEST 1/4] Green LED (GPIO 25)...");
    digitalWrite(PIN_LED_GREEN, HIGH);
    delay(350);
    digitalWrite(PIN_LED_GREEN, LOW);
    Serial.println(" -> Green LED: OK");

    // 3. Test Yellow LED (GPIO 26)
    Serial.println("[TEST 2/4] Yellow LED (GPIO 26)...");
    digitalWrite(PIN_LED_YELLOW, HIGH);
    delay(350);
    digitalWrite(PIN_LED_YELLOW, LOW);
    Serial.println(" -> Yellow LED: OK");

    // 4. Test Red LED (GPIO 27)
    Serial.println("[TEST 3/4] Red LED (GPIO 27)...");
    digitalWrite(PIN_LED_RED, HIGH);
    delay(350);
    digitalWrite(PIN_LED_RED, LOW);
    Serial.println(" -> Red LED: OK");

    // 5. Test OLED I2C Display (GPIO 21, 22)
    Serial.println("[TEST 4/4] OLED Display I2C (SDA=21, SCL=22)...");
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(100000); // 100 kHz standard mode ensures maximum cable noise immunity

    detectedOledAddress = scanI2CAddress();
    bool oledOk = display.begin(SSD1306_SWITCHCAPVCC, detectedOledAddress, false, false);
    if (!oledOk && detectedOledAddress != 0x3D) {
        Serial.println(" -> Primary begin failed, probing secondary address 0x3D...");
        oledOk = display.begin(SSD1306_SWITCHCAPVCC, 0x3D, false, false);
        if (oledOk) detectedOledAddress = 0x3D;
    }

    if (!oledOk) {
        Serial.println(" [ERROR] OLED allocation failed! Check display controller (SSD1306) and pullups.");
    } else {
        Serial.printf(" -> OLED Display OK at address 0x%02X!\n", detectedOledAddress);
        display.ssd1306_command(SSD1306_DISPLAYON);
        display.ssd1306_command(SSD1306_SETCONTRAST);
        display.ssd1306_command(0xFF); // Maximum display brightness
        animManager.renderSelfTest(true, true, true, true);
        delay(1200);
    }

    Serial.println("==================================================");
    Serial.println("  Hardware Self-Test Complete - All Pins Verified");
    Serial.println("==================================================\n");
}

// ---------------- DEVICE REGISTRATION & HANDSHAKE ----------------
void sendDeviceHandshake() {
    StaticJsonDocument<256> doc;
    doc["type"] = "HANDSHAKE";
    doc["device_id"] = DEVICE_ID;
    doc["firmware_version"] = FIRMWARE_VER;
    doc["chip_model"] = CHIP_MODEL;
    doc["mac_address"] = WiFi.macAddress();
    
    JsonArray caps = doc.createNestedArray("capabilities");
    caps.add("traffic_light");
    caps.add("oled_ssd1306");

    String output;
    serializeJson(doc, output);
    webSocket.sendTXT(output);
    Serial.printf("[WS] Transmitted HANDSHAKE for [%s]\n", DEVICE_ID);
}

// ---------------- PERIODIC HEARTBEAT ----------------
void sendHeartbeat() {
    StaticJsonDocument<256> doc;
    doc["type"] = "HEARTBEAT";
    doc["device_id"] = DEVICE_ID;
    doc["uptime_ms"] = millis();
    doc["rssi"] = WiFi.RSSI();
    doc["free_heap"] = ESP.getFreeHeap();

    String output;
    serializeJson(doc, output);
    webSocket.sendTXT(output);
    Serial.printf("[WS] Heartbeat sent (RSSI: %d dBm, Heap: %u bytes)\n", WiFi.RSSI(), ESP.getFreeHeap());
}

// ---------------- STATE UPDATE PARSER & DISPATCHER ----------------
void handleStateUpdate(JsonObject& root) {
    int seq = root["seq"] | 0;
    const char* ledColor = root["led"] | "GREEN";
    const char* eventName = root["event"] | "POSTURE_GOOD";
    const char* posture = root["posture"] | "good";
    const char* focus = root["focus"] | "focused";
    const char* session = root["session"] | "active";
    const char* message = root["message"] | "";

    // OLED payload can be an object or flat strings
    const char* animType = "good_posture";
    const char* oledTitle = "AI StudySense";
    const char* oledSubtitle = message;
    const char* timerFormatted = "00:00";
    int countdownSec = -1;

    if (root.containsKey("oled") && root["oled"].is<JsonObject>()) {
        JsonObject oledObj = root["oled"];
        animType = oledObj["animation"] | "good_posture";
        oledTitle = oledObj["title"] | "AI StudySense";
        oledSubtitle = oledObj["subtitle"] | message;
        timerFormatted = oledObj["timer_formatted"] | "00:00";
        if (oledObj.containsKey("timer_seconds")) {
            int tSec = oledObj["timer_seconds"];
            if (tSec <= 3 && tSec >= 0 && strcmp(animType, "buffer_warning") == 0) {
                countdownSec = tSec;
            }
        }
    } else if (root.containsKey("oled_animation")) {
        animType = root["oled_animation"] | "good_posture";
        oledTitle = root["message"] | "AI StudySense";
    }

    Serial.printf("[STATE_UPDATE #%d] Event: %s | LED: %s | Anim: %s | Subtitle: %s | Timer: %s\n",
                  seq, eventName, ledColor, animType, oledSubtitle, timerFormatted);

    // 1. Apply physical Traffic Light color
    applyLedColor(ledColor);
    lastLedState = ledColor;

    // 2. Resolve target OLED animation state machine
    AnimState targetState = ANIM_GOOD_POSTURE;

    if (strcmp(animType, "bad_posture") == 0 || strcmp(posture, "bad") == 0 || strcmp(eventName, "POSTURE_BAD") == 0) {
        targetState = ANIM_BAD_POSTURE;
    } else if (strcmp(animType, "buffer_warning") == 0 || strcmp(posture, "buffer") == 0 || strcmp(eventName, "POSTURE_WARNING") == 0) {
        targetState = ANIM_POSTURE_WARNING;
    } else if (strcmp(animType, "focus_warning") == 0 || strcmp(eventName, "PHONE_DISTRACTION") == 0) {
        targetState = ANIM_DISTRACTED;
    } else if (strcmp(focus, "absent") == 0 || strcmp(eventName, "ABSENCE_ALERT") == 0) {
        targetState = ANIM_ABSENT;
    } else if (strcmp(animType, "break_time") == 0 || strcmp(session, "break") == 0 || strcmp(eventName, "BREAK") == 0) {
        targetState = ANIM_BREAK;
    } else if (strcmp(animType, "session_complete") == 0 || strcmp(session, "completed") == 0 || strcmp(eventName, "SESSION_COMPLETE") == 0) {
        targetState = ANIM_SESSION_COMPLETE;
    } else if (strcmp(session, "idle") == 0 || strcmp(eventName, "IDLE") == 0) {
        targetState = ANIM_IDLE;
    } else {
        targetState = ANIM_GOOD_POSTURE;
    }

    // 3. Update non-blocking animation state
    animManager.setState(targetState, oledTitle, oledSubtitle, timerFormatted, countdownSec);

    // 4. Send STATE_ACK acknowledgement frame back to FastAPI backend
    StaticJsonDocument<128> ackDoc;
    ackDoc["type"] = "STATE_ACK";
    ackDoc["device_id"] = DEVICE_ID;
    ackDoc["seq"] = seq;
    ackDoc["uptime_ms"] = millis();

    String ackOutput;
    serializeJson(ackDoc, ackOutput);
    webSocket.sendTXT(ackOutput);
}

// ---------------- WEBSOCKET EVENT CALLBACK ----------------
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch (type) {
        case WStype_DISCONNECTED:
            isWsConnected = false;
            Serial.println("[WS] Disconnected from AI StudySense Laptop Backend.");
            // Safe state when connection lost: turn all LEDs off and display reconnecting
            setTrafficLight(false, false, false);
            animManager.setState(ANIM_RECONNECTING, "DISCONNECTED", "Retrying Backend...");
            break;

        case WStype_CONNECTED:
            isWsConnected = true;
            Serial.printf("[WS] Connected successfully to ws://%s:%d%s\n", BACKEND_HOST, BACKEND_PORT, WS_PATH);
            
            // Show Connected state with assigned local IP
            animManager.setState(ANIM_CONNECTED, "CONNECTED", WiFi.localIP().toString().c_str());
            
            // Dispatch initial device registration handshake
            sendDeviceHandshake();
            break;

        case WStype_TEXT: {
            DynamicJsonDocument doc(1024);
            DeserializationError err = deserializeJson(doc, payload, length);
            if (err) {
                Serial.printf("[JSON] Parse error: %s\n", err.c_str());
                return;
            }

            const char* msgType = doc["type"] | "";

            if (strcmp(msgType, "STATE_UPDATE") == 0) {
                JsonObject rootObj = doc.as<JsonObject>();
                handleStateUpdate(rootObj);
            } else if (strcmp(msgType, "HANDSHAKE_ACK") == 0) {
                Serial.println("[WS] Handshake acknowledged by AI StudySense backend.");
                animManager.setState(ANIM_IDLE, "STUDYSENSE READY", "Ready to Study");
            } else if (strcmp(msgType, "PONG") == 0) {
                Serial.println("[WS] Received PONG heartbeat acknowledgement.");
            } else if (strcmp(msgType, "PING") == 0) {
                webSocket.sendTXT("{\"type\":\"PONG\",\"device_id\":\"" DEVICE_ID "\"}");
            }
            break;
        }

        case WStype_BIN:
        case WStype_ERROR:
        case WStype_FRAGMENT_TEXT_START:
        case WStype_FRAGMENT_BIN_START:
        case WStype_FRAGMENT:
        case WStype_FRAGMENT_FIN:
        case WStype_PING:
        case WStype_PONG:
            break;
    }
}

// ---------------- ARDUINO SETUP ----------------
void setup() {
    Serial.begin(115200);
    delay(300);

    // 1. Run physical hardware self-test (LEDs 25, 26, 27 and OLED I2C 21, 22)
    executeHardwareSelfTest();

    // 2. Set connecting animation
    animManager.setState(ANIM_CONNECTING, "CONNECTING", WIFI_SSID);

    // 3. Connect to local Wi-Fi station
    Serial.printf("\n[Wi-Fi] Connecting to SSID: '%s'...\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long wifiStartMs = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - wifiStartMs < 15000) {
        animManager.update(); // Keep OLED animated while Wi-Fi negotiates
        delay(80);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[Wi-Fi] Connected! IP: %s | Gateway: %s | RSSI: %d dBm\n",
                      WiFi.localIP().toString().c_str(),
                      WiFi.gatewayIP().toString().c_str(),
                      WiFi.RSSI());
        animManager.setState(ANIM_CONNECTED, "WI-FI OK", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[Wi-Fi] Warning: Connection timeout. Will keep retrying in background.");
        animManager.setState(ANIM_RECONNECTING, "WI-FI FAILED", "Check SSID/PW");
    }

    // 4. Configure WebSocket client to connect to laptop FastAPI backend
    Serial.printf("[WS] Configuring connection to ws://%s:%d%s\n", BACKEND_HOST, BACKEND_PORT, WS_PATH);
    webSocket.begin(BACKEND_HOST, BACKEND_PORT, WS_PATH);
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(3000);
    webSocket.enableHeartbeat(15000, 3000, 2);
}

// ---------------- ARDUINO MAIN LOOP ----------------
void loop() {
    // 1. Process WebSocket incoming and outgoing frame buffers (non-blocking)
    webSocket.loop();

    // 2. Render smooth non-blocking OLED animation frame (~12 FPS)
    animManager.update();

    // 3. Periodic liveness heartbeat every 5 seconds
    unsigned long now = millis();
    if (isWsConnected && (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS)) {
        lastHeartbeatMs = now;
        sendHeartbeat();
    }
}
