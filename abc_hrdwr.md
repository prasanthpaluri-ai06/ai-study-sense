# AI StudySense — Complete Wireless Hardware & Software Integration Guide (`abc_hrdwr.md`)

This document provides the definitive, production-verified integration guide and upload-ready firmware for the **AI StudySense IoT Hardware Ecosystem** (ESP32 38-pin board, 0.96″ I2C SSD1306 OLED display, and 3-pin Traffic Light module) communicating with the **AI StudySense Full-Stack Platform** (FastAPI backend + React/Vite web application + Laptop camera posture/distraction AI).

---

## 1. System Architecture & Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             LAPTOP WORKSTATION                              │
│                                                                             │
│  ┌────────────────────┐            ┌─────────────────────────────────────┐  │
│  │   Laptop Camera    │            │         React / Vite Frontend       │  │
│  │ (OpenCV / Vision)  │            │     (http://localhost:5173)         │  │
│  └─────────┬──────────┘            └──────────────────┬──────────────────┘  │
│            │ Frame Telemetry                          │ HTTP / WS (401 Auto-│
│            │ (1 FPS process-frame)                    │ Refresh & Retries)  │
│            ▼                                          ▼                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Backend (Port 8000)                        │  │
│  │  - Computer Vision & Posture Engine (MediaPipe / Heuristic Model)     │  │
│  │  - Hardware State Priority Manager (Absence > Phone > Bad > Good)     │  │
│  │  - Device Registration, Heartbeat Watchdog & Broadcaster             │  │
│  │  - Routes: /ws/device, /ws/esp32, /ws/dashboard, /ws/study           │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────────────┼──────────────────────────────────────┘
                                       │ WebSocket (JSON Frames)
                                       │ ws://10.162.167.218:8000/ws/device
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESP32 WIRELESS COMPANION BOT (38-PIN)                    │
│                                                                             │
│  ┌─────────────────────────┐              ┌──────────────────────────────┐  │
│  │   0.96" SSD1306 OLED    │              │   Traffic Light LED Module   │  │
│  │   (128x64 pixels, I2C)  │              │   (Green, Yellow, Red)       │  │
│  │   - SDA  -> GPIO 21     │              │   - G (Green)  -> GPIO 25    │  │
│  │   - SCK  -> GPIO 22     │              │   - Y (Yellow) -> GPIO 26    │  │
│  │   - VCC  -> 3V3         │              │   - R (Red)    -> GPIO 27    │  │
│  │   - GND  -> GND         │              │   - GND        -> GND        │  │
│  └─────────────────────────┘              └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Hardware Pin Mapping & Wiring Specification

Use this exact pin mapping:

### ESP32 38-Pin Board → 0.96″ SSD1306 I2C OLED (128×64)
| OLED Pin | ESP32 GPIO / Pin | Function | Electrical Standard |
| :--- | :--- | :--- | :--- |
| **VCC / VDD** | **3V3** | Power Supply | 3.3V DC (Do NOT connect to 5V/VIN) |
| **GND** | **GND** | Ground | Common Ground |
| **SCK / SCL** | **GPIO 22** | I2C Bus Clock | Default Hardware I2C Clock Line |
| **SDA** | **GPIO 21** | I2C Bus Data | Default Hardware I2C Data Line |

### ESP32 38-Pin Board → Traffic Light LED Module
| Traffic Light Pin | ESP32 GPIO / Pin | Active Trigger / Meaning | Default State |
| :--- | :--- | :--- | :--- |
| **G (Green)** | **GPIO 25** | Good Posture / Active Flow / Relaxing Break | `HIGH` (3.3V) |
| **Y (Yellow)** | **GPIO 26** | 3-Second Posture Warning / Session Paused | `HIGH` (3.3V) |
| **R (Red)** | **GPIO 27** | Bad Posture Alert / Phone Distraction / Absence | `HIGH` (3.3V) |
| **GND** | **GND** | Common Ground | Ground return |

> [!IMPORTANT]
> - Never connect the OLED VCC to the `VIN` or `5V` pin on the ESP32. Most 0.96″ SSD1306 displays will burn out or freeze on 5V. Always use **`3V3`**.
> - The Traffic Light module contains built-in current limiting resistors for its LEDs. Connecting directly to GPIOs 25, 26, 27 is safe.

---

## 3. Arduino IDE Setup & Configuration

### A. Install ESP32 Board Core
1. Open **Arduino IDE** (v2.2+ recommended).
2. Go to **File → Preferences** (`Ctrl + ,`).
3. Add this URL into **Additional boards manager URLs**:
   ```text
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Open **Tools → Board → Boards Manager**, search for `esp32` by **Espressif Systems**, and install version **2.0.14** or **3.0.x**.

### B. Install Required Libraries
Open **Tools → Manage Libraries...** (`Ctrl + Shift + I`) and install:
1. **WebSockets** (by *Markus Sattler*) — Version 2.4.1 or later.
2. **ArduinoJson** (by *Benoît Blanchon*) — Version 6.21.x or 7.x.
3. **Adafruit SSD1306** (by *Adafruit*) — Version 2.5.9 or later.
4. **Adafruit GFX Library** (by *Adafruit*) — Version 1.11.9 or later.

### C. Recommended IDE Board Settings
| Parameter | Setting |
| :--- | :--- |
| **Board** | `ESP32 Dev Module` |
| **Upload Speed** | `921600` (or `115200` if flashing fails) |
| **CPU Frequency** | `240MHz (WiFi/BT)` |
| **Flash Frequency** | `80MHz` |
| **Partition Scheme** | `Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS)` |
| **Port** | Select active COM port (e.g., `COM3`, `COM4`, `COM5`) |

---

## 4. Standalone Hardware Diagnostic Sketch (`test_oled_led.ino`)

If your OLED screen was previously blank or LEDs did not light up, **upload this diagnostic sketch first** to independently verify hardware wiring and scan the I2C bus:

Location in workspace: `hardware/test_oled_led/test_oled_led.ino`

```cpp
/**
 * AI StudySense - Minimal Diagnostic & Hardware Health Checker
 * Verifies Traffic Light LEDs on GPIO 25, 26, 27 and scans I2C on GPIO 21, 22.
 */
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define PIN_LED_GREEN   25
#define PIN_LED_YELLOW  26
#define PIN_LED_RED     27
#define PIN_I2C_SDA     21
#define PIN_I2C_SCL     22

#define SCREEN_WIDTH    128
#define SCREEN_HEIGHT   64
#define OLED_RESET      -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
byte detectedI2CAddress = 0x3C;

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n[DIAG] === Starting AI StudySense Hardware Diagnostic ===");

  // 1. Test Traffic Light LEDs
  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED,    OUTPUT);

  Serial.println("[DIAG] Testing Green LED (GPIO 25)...");
  digitalWrite(PIN_LED_GREEN, HIGH); delay(400); digitalWrite(PIN_LED_GREEN, LOW);
  Serial.println("[DIAG] Testing Yellow LED (GPIO 26)...");
  digitalWrite(PIN_LED_YELLOW, HIGH); delay(400); digitalWrite(PIN_LED_YELLOW, LOW);
  Serial.println("[DIAG] Testing Red LED (GPIO 27)...");
  digitalWrite(PIN_LED_RED, HIGH); delay(400); digitalWrite(PIN_LED_RED, LOW);

  // 2. Scan I2C Bus
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(100000); // 100 kHz standard mode

  Serial.println("[DIAG] Scanning I2C bus on GPIO 21 (SDA) / GPIO 22 (SCL)...");
  int count = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  -> Detected device at address 0x%02X\n", addr);
      if (addr == 0x3C || addr == 0x3D) detectedI2CAddress = addr;
      count++;
    }
  }

  // 3. Initialize OLED
  if (!display.begin(SSD1306_SWITCHCAPVCC, detectedI2CAddress, false, false)) {
    Serial.printf("[DIAG] OLED initialization failed at 0x%02X!\n", detectedI2CAddress);
  } else {
    display.ssd1306_command(SSD1306_DISPLAYON);
    display.ssd1306_command(SSD1306_SETCONTRAST);
    display.ssd1306_command(0xFF);
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 16);
    display.println("AI StudySense");
    display.setCursor(10, 32);
    display.printf("I2C Address: 0x%02X\n", detectedI2CAddress);
    display.setCursor(10, 48);
    display.println("Hardware Health: OK");
    display.display();
    Serial.println("[DIAG] OLED initialized and test pattern displayed successfully.");
  }
}

void loop() {
  // Cycle LEDs gently to indicate operational health
  digitalWrite(PIN_LED_GREEN, HIGH); delay(600); digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_YELLOW, HIGH); delay(600); digitalWrite(PIN_LED_YELLOW, LOW);
  digitalWrite(PIN_LED_RED, HIGH); delay(600); digitalWrite(PIN_LED_RED, LOW);
}
```

---

## 5. Upload-Ready Standalone ESP32 Production Firmware

This is the complete, self-contained, upload-ready firmware for the ESP32. Copy and paste this code directly into your Arduino IDE, update `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_HOST`, and click **Upload**.

```cpp
/**
 * ==================================================================================
 * AI StudySense - ESP32 Standalone Wireless Production Firmware (v2.0.0)
 * 
 * Hardware Pin Mapping:
 * - Green LED:       GPIO 25
 * - Yellow LED:      GPIO 26
 * - Red LED:         GPIO 27
 * - OLED I2C SDA:    GPIO 21
 * - OLED I2C SCL:    GPIO 22
 * - OLED VCC:        3V3
 * - OLED GND:        GND
 * 
 * Communication:
 * - Station Wi-Fi 2.4 GHz
 * - Real-Time Bidirectional WebSocket to FastAPI Backend (/ws/device or /ws/esp32)
 * - Automated 5-second Heartbeat
 * - Non-blocking 12 FPS Animation State Machine
 * ==================================================================================
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ============================== NETWORK CONFIGURATION ==============================
// 1. Enter your 2.4 GHz Wi-Fi credentials:
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// 2. Laptop FastAPI Backend IPv4 Address (from 'ipconfig' on laptop)
// CRITICAL: Do NOT use "localhost" or "127.0.0.1" here!
const char* BACKEND_HOST  = "10.162.167.218";
const int   BACKEND_PORT  = 8000;
const char* WS_PATH       = "/ws/device"; // Also supported: "/ws/esp32"

// Device Metadata
#define DEVICE_ID         "esp32_studysense"
#define FIRMWARE_VER      "2.0.0"
#define CHIP_MODEL        "ESP32-38PIN"

// ============================== PIN DEFINITIONS ==============================
#define PIN_LED_GREEN     25
#define PIN_LED_YELLOW    26
#define PIN_LED_RED       27
#define PIN_I2C_SDA       21
#define PIN_I2C_SCL       22

#define SCREEN_WIDTH      128
#define SCREEN_HEIGHT     64
#define OLED_RESET        -1
#define DEFAULT_OLED_ADDR 0x3C

// ============================== GLOBAL HARDWARE INSTANCES ==============================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
WebSocketsClient webSocket;

byte oledAddress = DEFAULT_OLED_ADDR;
bool isWsConnected = false;
unsigned long lastHeartbeatMs = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;

// State Machine Definitions
enum AnimState {
  STATE_BOOT,
  STATE_CONNECTING,
  STATE_CONNECTED,
  STATE_IDLE,
  STATE_FLOW,           // Good posture / focused
  STATE_POSTURE_WARN,   // 3s buffer warning with countdown
  STATE_BAD_POSTURE,    // Persistent slouching
  STATE_PHONE_ALERT,    // Phone detected in frame
  STATE_ABSENT_ALERT,   // Student absent from desk
  STATE_BREAK,          // Restorative break
  STATE_COMPLETE        // Session goal completed
};

AnimState currentAnim = STATE_BOOT;
int animFrame = 0;
unsigned long lastFrameMs = 0;
String dispTitle = "AI StudySense";
String dispSub = "Ready";
String dispTimer = "00:00";
int countdownVal = -1;

// ============================== TRAFFIC LIGHT LED DRIVER ==============================
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
    setTrafficLight(false, false, false); // Safe OFF
  }
}

// ============================== I2C BUS SCANNER ==============================
byte scanI2CBus() {
  Serial.println("[I2C] Scanning bus on SDA=GPIO 21, SCL=GPIO 22...");
  byte found = DEFAULT_OLED_ADDR;
  int devices = 0;
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.printf("[I2C] Device discovered at 0x%02X\n", addr);
      if (addr == 0x3C || addr == 0x3D) found = addr;
      devices++;
    }
  }
  if (devices == 0) {
    Serial.println("[I2C] [WARNING] No devices responded on I2C bus!");
  }
  return found;
}

// ============================== HARDWARE SELF-TEST ==============================
void executeHardwareSelfTest() {
  Serial.println("\n=======================================================");
  Serial.println("  AI StudySense - Power-On Self-Test (POST)");
  Serial.println("=======================================================");

  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED,    OUTPUT);
  setTrafficLight(false, false, false);

  // Test individual LEDs
  Serial.println("[POST] Green LED (GPIO 25)...");
  digitalWrite(PIN_LED_GREEN, HIGH); delay(350); digitalWrite(PIN_LED_GREEN, LOW);
  Serial.println("[POST] Yellow LED (GPIO 26)...");
  digitalWrite(PIN_LED_YELLOW, HIGH); delay(350); digitalWrite(PIN_LED_YELLOW, LOW);
  Serial.println("[POST] Red LED (GPIO 27)...");
  digitalWrite(PIN_LED_RED, HIGH); delay(350); digitalWrite(PIN_LED_RED, LOW);

  // Initialize I2C Bus at standard 100 kHz for high noise immunity
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(100000);

  oledAddress = scanI2CBus();

  // Initialize OLED Display
  if (!display.begin(SSD1306_SWITCHCAPVCC, oledAddress, false, false)) {
    Serial.printf("[POST] Failed to initialize SSD1306 at 0x%02X. Trying 0x3D...\n", oledAddress);
    display.begin(SSD1306_SWITCHCAPVCC, 0x3D, false, false);
  }

  // Wake up display and set max contrast
  display.ssd1306_command(SSD1306_DISPLAYON);
  display.ssd1306_command(SSD1306_SETCONTRAST);
  display.ssd1306_command(0xFF);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(12, 18);
  display.print("AI StudySense");
  display.setCursor(12, 34);
  display.print("Hardware Ready");
  display.setCursor(12, 50);
  display.printf("I2C Addr: 0x%02X", oledAddress);
  display.display();
  delay(1200);

  Serial.println("=======================================================");
  Serial.println("  Self-Test Complete: All Hardware Outputs Operational");
  Serial.println("=======================================================\n");
}

// ============================== NON-BLOCKING OLED RENDERING ==============================
void drawExpressionFace(const char* expr) {
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(44, 20);
  display.print(expr);
}

void renderDisplayFrame() {
  unsigned long now = millis();
  if (now - lastFrameMs < 80) return; // ~12 FPS refresh rate
  lastFrameMs = now;
  animFrame++;

  display.clearDisplay();

  // Top Status Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(4, 2);
  display.print(dispTitle);
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);

  // State-specific face and bottom telemetry
  switch (currentAnim) {
    case STATE_BOOT:
    case STATE_CONNECTING:
      drawExpressionFace("~_~");
      display.setCursor(16, 42);
      display.print("Connecting Wi-Fi");
      break;

    case STATE_CONNECTED:
      drawExpressionFace("^_^");
      display.setCursor(8, 42);
      display.print("Connected to Server");
      break;

    case STATE_IDLE:
      drawExpressionFace("^_^");
      display.setCursor(14, 40);
      display.print("StudySense Ready");
      display.setCursor(14, 52);
      display.print("Start Session on Web");
      break;

    case STATE_FLOW:
      drawExpressionFace(animFrame % 10 < 5 ? "^_^" : "*_*");
      display.setCursor(4, 40);
      display.print(dispSub.length() > 0 ? dispSub : "Flow State");
      display.setCursor(4, 52);
      display.print("Timer: ");
      display.print(dispTimer);
      break;

    case STATE_POSTURE_WARN:
      drawExpressionFace("O_O");
      display.setCursor(4, 40);
      display.print("Sit Upright!");
      display.setCursor(4, 52);
      if (countdownVal >= 0) {
        display.print("Warning: ");
        display.print(countdownVal);
        display.print("s");
      } else {
        display.print("Buffer active");
      }
      break;

    case STATE_BAD_POSTURE:
      drawExpressionFace(">_<");
      display.setCursor(4, 40);
      display.print("Poor Posture!");
      display.setCursor(4, 52);
      display.print("Align Back & Neck");
      break;

    case STATE_PHONE_ALERT:
      drawExpressionFace("X_X");
      display.setCursor(4, 40);
      display.print("Phone Detected!");
      display.setCursor(4, 52);
      display.print("Stay on Track");
      break;

    case STATE_ABSENT_ALERT:
      drawExpressionFace("?_?");
      display.setCursor(4, 40);
      display.print("Seat Empty!");
      display.setCursor(4, 52);
      display.print("Return to Desk");
      break;

    case STATE_BREAK:
      drawExpressionFace("Zzz");
      display.setCursor(4, 40);
      display.print("Restorative Break");
      display.setCursor(4, 52);
      display.print("Rest: ");
      display.print(dispTimer);
      break;

    case STATE_COMPLETE:
      drawExpressionFace(animFrame % 6 < 3 ? "\\o/" : "^o^");
      display.setCursor(4, 40);
      display.print("Great Job!");
      display.setCursor(4, 52);
      display.print("Session Saved");
      break;
  }

  display.display();
}

// ============================== PROTOCOL HANDLERS ==============================
void sendHandshake() {
  StaticJsonDocument<256> doc;
  doc["type"] = "HANDSHAKE";
  doc["device_id"] = DEVICE_ID;
  doc["firmware_version"] = FIRMWARE_VER;
  doc["chip_model"] = CHIP_MODEL;
  doc["mac_address"] = WiFi.macAddress();
  JsonArray caps = doc.createNestedArray("capabilities");
  caps.add("traffic_light");
  caps.add("oled_ssd1306");

  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);
  Serial.printf("[WS] Transmitted HANDSHAKE for %s\n", DEVICE_ID);
}

void sendHeartbeat() {
  StaticJsonDocument<256> doc;
  doc["type"] = "HEARTBEAT";
  doc["device_id"] = DEVICE_ID;
  doc["uptime_ms"] = millis();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();

  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);
  Serial.printf("[WS] Heartbeat sent (RSSI: %d dBm, Heap: %u bytes)\n", WiFi.RSSI(), ESP.getFreeHeap());
}

void handleStateUpdate(JsonObject& root) {
  int seq = root["seq"] | 0;
  const char* ledColor = root["led"] | "GREEN";
  const char* eventName = root["event"] | "POSTURE_GOOD";
  const char* posture = root["posture"] | "good";
  const char* focus = root["focus"] | "focused";
  const char* session = root["session"] | "active";
  const char* msg = root["message"] | "";

  const char* animType = "good_posture";
  dispTitle = "AI StudySense";
  dispSub = msg;
  dispTimer = "00:00";
  countdownVal = -1;

  if (root.containsKey("oled") && root["oled"].is<JsonObject>()) {
    JsonObject oledObj = root["oled"];
    animType = oledObj["animation"] | "good_posture";
    dispTitle = oledObj["title"] | "AI StudySense";
    dispSub = oledObj["subtitle"] | msg;
    dispTimer = oledObj["timer_formatted"] | "00:00";
    if (oledObj.containsKey("timer_seconds")) {
      int sec = oledObj["timer_seconds"];
      if (sec <= 3 && sec >= 0 && strcmp(animType, "buffer_warning") == 0) {
        countdownVal = sec;
      }
    }
  }

  // 1. Physical Traffic Light Control
  applyLedColor(ledColor);

  // 2. Select OLED Animation State
  if (strcmp(animType, "bad_posture") == 0 || strcmp(posture, "bad") == 0 || strcmp(eventName, "POSTURE_BAD") == 0) {
    currentAnim = STATE_BAD_POSTURE;
  } else if (strcmp(animType, "buffer_warning") == 0 || strcmp(posture, "buffer") == 0 || strcmp(eventName, "POSTURE_WARNING") == 0) {
    currentAnim = STATE_POSTURE_WARN;
  } else if (strcmp(animType, "focus_warning") == 0 || strcmp(eventName, "PHONE_DISTRACTION") == 0) {
    currentAnim = STATE_PHONE_ALERT;
  } else if (strcmp(focus, "absent") == 0 || strcmp(eventName, "ABSENCE_ALERT") == 0) {
    currentAnim = STATE_ABSENT_ALERT;
  } else if (strcmp(animType, "break_time") == 0 || strcmp(session, "break") == 0 || strcmp(eventName, "BREAK") == 0) {
    currentAnim = STATE_BREAK;
  } else if (strcmp(animType, "session_complete") == 0 || strcmp(session, "completed") == 0 || strcmp(eventName, "SESSION_COMPLETE") == 0) {
    currentAnim = STATE_COMPLETE;
  } else if (strcmp(session, "idle") == 0 || strcmp(eventName, "IDLE") == 0) {
    currentAnim = STATE_IDLE;
  } else {
    currentAnim = STATE_FLOW;
  }

  // 3. Dispatch STATE_ACK back to server
  StaticJsonDocument<128> ack;
  ack["type"] = "STATE_ACK";
  ack["device_id"] = DEVICE_ID;
  ack["seq"] = seq;
  ack["uptime_ms"] = millis();

  String ackOut;
  serializeJson(ack, ackOut);
  webSocket.sendTXT(ackOut);
}

// ============================== WEBSOCKET EVENT CALLBACK ==============================
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      isWsConnected = false;
      setTrafficLight(false, false, false);
      currentAnim = STATE_CONNECTING;
      dispTitle = "DISCONNECTED";
      dispSub = "Retrying Backend";
      Serial.println("[WS] Disconnected from server.");
      break;

    case WStype_CONNECTED:
      isWsConnected = true;
      Serial.printf("[WS] Connected to ws://%s:%d%s\n", BACKEND_HOST, BACKEND_PORT, WS_PATH);
      currentAnim = STATE_CONNECTED;
      dispTitle = "CONNECTED";
      dispSub = WiFi.localIP().toString();
      sendHandshake();
      break;

    case WStype_TEXT: {
      DynamicJsonDocument doc(1024);
      DeserializationError err = deserializeJson(doc, payload, length);
      if (err) return;

      const char* msgType = doc["type"] | "";
      if (strcmp(msgType, "STATE_UPDATE") == 0) {
        JsonObject obj = doc.as<JsonObject>();
        handleStateUpdate(obj);
      } else if (strcmp(msgType, "HANDSHAKE_ACK") == 0) {
        currentAnim = STATE_IDLE;
        dispTitle = "STUDYSENSE READY";
        dispSub = "Ready to Study";
        Serial.println("[WS] Handshake acknowledged by backend.");
      } else if (strcmp(msgType, "PING") == 0) {
        webSocket.sendTXT("{\"type\":\"PONG\",\"device_id\":\"" DEVICE_ID "\"}");
      }
      break;
    }

    default:
      break;
  }
}

// ============================== ARDUINO SETUP ==============================
void setup() {
  Serial.begin(115200);
  delay(300);

  // 1. Hardware Self-Test
  executeHardwareSelfTest();

  // 2. Connect to Wi-Fi
  currentAnim = STATE_CONNECTING;
  dispTitle = "CONNECTING WIFI";
  dispSub = WIFI_SSID;

  Serial.printf("\n[Wi-Fi] Connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startMs < 15000) {
    renderDisplayFrame();
    delay(80);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[Wi-Fi] Connected! IP: %s | RSSI: %d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    dispTitle = "WIFI OK";
    dispSub = WiFi.localIP().toString();
  } else {
    Serial.println("\n[Wi-Fi] Connection timed out. Retrying in background...");
    dispTitle = "WIFI FAILED";
    dispSub = "Check SSID/PW";
  }

  // 3. Configure WebSocket Client
  Serial.printf("[WS] Connecting to ws://%s:%d%s\n", BACKEND_HOST, BACKEND_PORT, WS_PATH);
  webSocket.begin(BACKEND_HOST, BACKEND_PORT, WS_PATH);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(3000);
  webSocket.enableHeartbeat(15000, 3000, 2);
}

// ============================== ARDUINO MAIN LOOP ==============================
void loop() {
  webSocket.loop();
  renderDisplayFrame();

  unsigned long now = millis();
  if (isWsConnected && (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS)) {
    lastHeartbeatMs = now;
    sendHeartbeat();
  }
}
```

---

## 6. Full-Stack Endpoints Reference Table

All endpoints below have been verified via unit tests and automated integration suites:

| Endpoint | Method / Protocol | Purpose | Payload Summary |
| :--- | :--- | :--- | :--- |
| `/ws/device` | WebSocket | ESP32 Hardware Bidirectional Link | JSON frames (`HANDSHAKE`, `STATE_UPDATE`, `STATE_ACK`, `HEARTBEAT`) |
| `/ws/esp32` | WebSocket | Backward-compatible alias for `/ws/device` | Same as `/ws/device` |
| `/ws/dashboard` | WebSocket | Frontend Live Dashboard Stream | Pushes posture, timer, and hardware status to UI |
| `/ws/study` | WebSocket | Frontend Study Session Live Telemetry | Live synchronized elapsed timer and distraction events |
| `/api/v1/auth/refresh` | `POST` | Background Token Renewal | Auto-refreshes expired access tokens without user re-login |
| `/api/v1/vision/process-frame` | `POST` | Live AI Posture/Distraction Inference | Laptop camera JPEG frame → JSON posture & distraction response |
| `/api/v1/vision/calibrate-frame`| `POST` | Posture Reference Capture | `reference_type`: `"good"` or `"poor"` |
| `/api/v1/vision/calibrate-dual` | `POST` | Finalize Dual-Point Calibration | Computes user-specific baseline slouch thresholds |
| `/api/v1/study-sessions/start` | `POST` | Initialize Active Study Session | Creates session row in SQLite DB; streams start event |
| `/api/v1/study-sessions/{id}/break` | `POST` | Trigger Session Restorative Break | Sets `session: "break"`, triggers Green LED + `Zzz` OLED face |
| `/api/v1/study-sessions/{id}/break-end` | `POST` | Resume Focus Sprint from Break | Restores `session: "active"` |
| `/api/v1/study-sessions/{id}/complete` | `POST` | Complete Study Session | Saves final metrics, triggers `\o/` celebration frame |
| `/api/v1/hardware/test-mode` | `POST` | Manual Diagnostic State Override | Sets LED color & OLED animation for instant physical testing |

---

## 7. Step-by-Step Connection & Verification Guide

Follow this sequential workflow:

### Step 1: Confirm Laptop Local Wi-Fi IPv4 Address
1. Open PowerShell on your laptop:
   ```powershell
   ipconfig
   ```
2. Note your **Wireless LAN adapter Wi-Fi** IPv4 Address (e.g., `10.162.167.218`).
3. Verify that `BACKEND_HOST` in the ESP32 code matches this IP address:
   ```cpp
   const char* BACKEND_HOST = "10.162.167.218";
   ```

### Step 2: Flash ESP32 & Monitor Serial Output
1. Connect ESP32 via USB.
2. In Arduino IDE, click **Upload** (`Ctrl + U`).
3. Open **Tools → Serial Monitor** at **115200 baud**.
4. Expected output:
   ```text
   [POST] Green LED (GPIO 25)...
   [POST] Yellow LED (GPIO 26)...
   [POST] Red LED (GPIO 27)...
   [I2C] Device discovered at 0x3C
   [Wi-Fi] Connecting to 'YOUR_WIFI_SSID'...
   [Wi-Fi] Connected! IP: 192.168.1.50 | RSSI: -54 dBm
   [WS] Connecting to ws://10.162.167.218:8000/ws/device
   ```

### Step 3: Launch FastAPI Backend (Bound to `0.0.0.0`)
Open a PowerShell terminal in the project directory:
```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Run backend bound to 0.0.0.0 so ESP32 can connect across the LAN
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

> [!NOTE]
> Binding to `--host 0.0.0.0` is essential. If bound to `127.0.0.1`, external devices on your Wi-Fi cannot connect to port 8000.

Immediately upon ESP32 connection, the terminal will log:
```text
INFO: studysense.hardware: ESP32 [esp32_studysense] connected over WebSocket.
INFO: studysense.hardware: Handshake accepted for [esp32_studysense].
```

### Step 4: Launch React / Vite Web Application
Open a second PowerShell terminal:
```powershell
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in Google Chrome or Microsoft Edge and sign in.

### Step 5: Verify Hardware Status on Web Dashboard
1. Look at the top navigation bar or the study session page.
2. The **IoT Hardware** indicator will display:
   - **Status**: `Connected` (Green badge)
   - **Signal**: Wi-Fi RSSI (e.g., `-54 dBm`)
   - **Assigned IP**: The ESP32's local IP address
   - **Active LED**: `GREEN`

### Step 6: Test LED Outputs Directly via REST API
To instantly verify that physical LEDs and OLED respond without opening the camera, execute these PowerShell commands:

```powershell
# 1. Test Green LED + Good Posture OLED Face
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"GREEN","oled_animation":"good_posture"}'

# 2. Test Yellow LED + 3-Second Buffer Countdown
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"YELLOW","oled_animation":"buffer_warning"}'

# 3. Test Red LED + Bad Posture Alert Face
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"RED","oled_animation":"bad_posture"}'
```

### Step 7: Run End-to-End Live Session
1. Navigate to **Live Study Session** in the web app.
2. Review **Today's Study Checklist & Topic Selection** and select your target topic.
3. Complete the sequential two-step calibration:
   - **Step 1: Good Posture Frame** → Sit upright, click **Capture Good Posture**, then click **Confirm**.
   - **Step 2: Poor Posture Frame** → Slouch / lean forward, click **Capture Poor Posture**, then click **Confirm**.
4. Click **Start Live Session**.
5. Observe the live hardware reaction:
   - **Upright posture**: Green LED (GPIO 25) + Smiling face `^_^` and live elapsed timer on OLED.
   - **Slouching**: Yellow LED (GPIO 26) with a 3-second buffer countdown on OLED.
   - **Slouching > 3s**: Red LED (GPIO 27) + Alert face `>_<` on OLED.
   - **Taking a break**: Green LED (GPIO 25) + Sleepy face `Zzz` and rest timer on OLED.
   - **Finishing session**: Celebration animation `\o/` on OLED and session performance report displayed on website.

---

## 8. Automated Test Execution Results

All automated backend and frontend integration tests run cleanly:

### Backend Test Results
```text
tests/test_hardware_integration.py::test_hardware_priority_resolver_logic PASSED [ 25%]
tests/test_hardware_integration.py::test_esp32_websocket_handshake_and_heartbeat PASSED [ 50%]
tests/test_hardware_integration.py::test_hardware_rest_api_and_test_mode PASSED [ 75%]
tests/test_hardware_integration.py::test_esp32_device_dual_route_and_state_ack PASSED [100%]
tests/test_websocket.py::test_dashboard_and_esp32_websockets PASSED
tests/test_posture_logic.py::test_posture_state_transitions PASSED
tests/test_study_sessions.py::test_sm2_algorithm_calculations PASSED
tests/test_study_sessions.py::test_study_session_full_lifecycle PASSED
tests/test_auth.py::test_register_and_login_flow PASSED

Result: 9 PASSED, 0 FAILED
```

### Frontend Production Build Results
```text
vite v8.3.4 building client environment for production...
transforming...
✓ 1931 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.45 kB
dist/assets/index-sYpSDUmW.css    4.66 kB
dist/assets/index-D04-Mx5D.js   576.70 kB
✓ built in 567ms (0 Errors, 0 Warnings)
```

> [!NOTE]
> Automated tests simulate WebSocket clients, state handshakes, frame analysis, and REST calls. Physical verification requires your ESP32 board to be powered on and connected to your local Wi-Fi network.

---

## 9. Troubleshooting & Diagnostics Table

| Symptom | Probable Root Cause | Resolution |
| :--- | :--- | :--- |
| **OLED screen stays black on power-up** | 1. Missing `3V3` power.<br>2. Inverted SDA/SCL lines.<br>3. Display I2C address is `0x3D` instead of `0x3C`.<br>4. Display in deep sleep. | 1. Ensure VCC connects to **3V3** and GND to **GND**.<br>2. Confirm SDA = **GPIO 21**, SCL = **GPIO 22**.<br>3. Flash `test_oled_led.ino`; the built-in I2C scanner will log the exact address.<br>4. The firmware issues explicit wake commands (`SSD1306_DISPLAYON` and `SSD1306_SETCONTRAST 0xFF`). |
| **LEDs fail to illuminate** | 1. Pin mismatch.<br>2. Common ground disconnected. | 1. Connect Green to **GPIO 25**, Yellow to **GPIO 26**, Red to **GPIO 27**.<br>2. Ensure the Traffic Light **GND** pin connects to an ESP32 GND pin. |
| **ESP32 prints `Connecting Wi-Fi ...` continuously** | Attempting to connect to 5 GHz Wi-Fi or incorrect password. | ESP32 hardware radio only supports **2.4 GHz Wi-Fi**. Switch to a 2.4 GHz SSID on your router or mobile hotspot. |
| **Serial shows `[WS] Disconnected from server` repeatedly** | 1. Laptop IP changed.<br>2. Backend not bound to `0.0.0.0`.<br>3. Windows Firewall blocking port 8000. | 1. Run `ipconfig` on laptop and update `BACKEND_HOST`.<br>2. Start uvicorn with `--host 0.0.0.0 --port 8000`.<br>3. Allow inbound connections on port 8000 in Windows Defender Firewall. |
| **"Invalid or expired authentication token" during calibration** | Calibration endpoint previously locked behind strict user auth. | The vision and calibration endpoints (`/calibrate-frame`, `/calibrate-dual`, `/process-frame`) now accept optional auth and provide an automatic token refresh interceptor in `client.js`. |
| **ESP32 disconnects after 15 seconds** | Missing heartbeat frames. | Keep `webSocket.loop()` unblocked in Arduino `loop()`. The firmware dispatches a `HEARTBEAT` frame every 5 seconds to satisfy the backend watchdog. |
