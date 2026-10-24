# AI StudySense — Hardware & Website Connection Guide (`cnct_wbst_hrdwr`)

This guide explains how to connect your **ESP32 physical hardware** (Traffic Light Module + 0.96″ I2C OLED display) to the **AI StudySense software ecosystem** (FastAPI Python backend + React/Vite website).

---

## 1. Hardware Pin Mapping & Wiring

Connect the components to your ESP32 (38-pin board) as shown below:

### ESP32 38-Pin Board → 0.96″ SSD1306 I2C OLED (128×64)
| OLED Pin | ESP32 GPIO / Pin | Function |
| :--- | :--- | :--- |
| **VCC / VDD** | **3V3** | 3.3V Power |
| **GND** | **GND** | Ground |
| **SCK / SCL** | **GPIO 22** | I2C Clock Line |
| **SDA** | **GPIO 21** | I2C Data Line |

### ESP32 38-Pin Board → Traffic Light LED Module
| Traffic Light Pin | ESP32 GPIO / Pin | State / Trigger |
| :--- | :--- | :--- |
| **G (Green)** | **GPIO 25** | Active Focus Sprint / Good Posture / Calming Break |
| **Y (Yellow)** | **GPIO 26** | 3-Second Buffer Warning / Session Paused |
| **R (Red)** | **GPIO 27** | Bad Posture Alert / Phone Distraction / Absence Alert |
| **GND** | **GND** | Common Ground |

---

## 2. Arduino IDE Setup & Libraries

1. **Install Arduino IDE** (Version 2.x or later).
2. **Add ESP32 Board URL**:
   - Open Arduino IDE → **File** → **Preferences** (or `Ctrl + ,`).
   - In **Additional boards manager URLs**, add:
     ```text
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to **Tools** → **Board** → **Boards Manager...**, search for `esp32` by **Espressif Systems**, and click **Install**.
3. **Install Required Libraries** via **Tools** → **Manage Libraries...**:
   - `WebSockets` (by **Markus Sattler**)
   - `ArduinoJson` (by **Benoît Blanchon**, version 6.x or 7.x)
   - `Adafruit SSD1306` (by **Adafruit**)
   - `Adafruit GFX Library` (by **Adafruit**)
4. **Board Settings**:
   - **Board**: `ESP32 Dev Module`
   - **Upload Speed**: `921600` (use `115200` if upload fails)
   - **CPU Frequency**: `240MHz (WiFi/BT)`
   - **Flash Frequency**: `80MHz`
   - **Partition Scheme**: `Default 4MB with spiffs (1.2MB APP/1.5MB SPIFFS)`
   - **Port**: Select the COM port of your connected ESP32 (e.g., `COM3`, `COM4`, etc.)

---

## 3. The ESP32 Code to Push into ESP32

You can use the modular firmware files in `hardware/esp32_studysense/` OR paste this **Complete All-in-One Standalone Sketch** directly into the Arduino IDE:

```cpp
/**
 * =========================================================================
 * AI StudySense - ESP32 Standalone Wireless Firmware (v2.0.0)
 * 
 * Hardware Pin Mapping:
 * - Green LED:   GPIO 25
 * - Yellow LED:  GPIO 26
 * - Red LED:     GPIO 27
 * - OLED SDA:    GPIO 21
 * - OLED SCL:    GPIO 22
 * =========================================================================
 */

#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// =================== NETWORK CONFIGURATION ===================
// 1. Enter your 2.4 GHz Wi-Fi credentials:
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// 2. Enter your laptop's local Wi-Fi IPv4 address (Find using `ipconfig`):
// IMPORTANT: Do NOT use "localhost" or "127.0.0.1" here!
const char* BACKEND_HOST  = "10.162.167.218"; 
const int   BACKEND_PORT  = 8000;
const char* WS_PATH       = "/ws/device"; // Or "/ws/esp32"

// Device Metadata
#define DEVICE_ID         "esp32_studysense"
#define FIRMWARE_VER      "2.0.0"
#define CHIP_MODEL        "ESP32-38PIN"

// =================== PIN DEFINITIONS ===================
#define PIN_LED_GREEN     25
#define PIN_LED_YELLOW    26
#define PIN_LED_RED       27
#define PIN_I2C_SDA       21
#define PIN_I2C_SCL       22

#define SCREEN_WIDTH      128
#define SCREEN_HEIGHT     64
#define OLED_RESET        -1
#define SCREEN_ADDRESS    0x3C

// =================== GLOBAL INSTANCES ===================
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
WebSocketsClient webSocket;

bool isWsConnected = false;
unsigned long lastHeartbeatMs = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 5000;

// Animation & Display States
enum AnimState {
  STATE_BOOT,
  STATE_CONNECTING,
  STATE_IDLE,
  STATE_FLOW,
  STATE_POSTURE_WARN,
  STATE_BAD_POSTURE,
  STATE_PHONE_ALERT,
  STATE_ABSENT_ALERT,
  STATE_BREAK,
  STATE_COMPLETE
};

AnimState currentAnim = STATE_BOOT;
int animFrame = 0;
unsigned long lastFrameMs = 0;
String dispTitle = "AI StudySense";
String dispSub = "Ready";
String dispTimer = "00:00";
int countdownVal = -1;

// =================== LED CONTROL ===================
void setLeds(bool g, bool y, bool r) {
  digitalWrite(PIN_LED_GREEN,  g ? HIGH : LOW);
  digitalWrite(PIN_LED_YELLOW, y ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,    r ? HIGH : LOW);
}

void applyLed(const char* color) {
  if (strcmp(color, "GREEN") == 0)       setLeds(true, false, false);
  else if (strcmp(color, "YELLOW") == 0) setLeds(false, true, false);
  else if (strcmp(color, "RED") == 0)    setLeds(false, false, true);
  else                                   setLeds(false, false, false);
}

// =================== NON-BLOCKING OLED DRAWING ===================
void drawFace(const char* expression) {
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(44, 20);
  display.print(expression);
}

void updateOledFrame() {
  unsigned long now = millis();
  if (now - lastFrameMs < 80) return; // ~12 FPS
  lastFrameMs = now;
  animFrame++;

  display.clearDisplay();

  // Top Title Bar
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(4, 2);
  display.print(dispTitle);
  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);

  // Expression / Graphic
  switch (currentAnim) {
    case STATE_BOOT:
    case STATE_CONNECTING:
      drawFace("~_~");
      display.setCursor(15, 42);
      display.print("Connecting WiFi");
      break;

    case STATE_IDLE:
      drawFace("^_^");
      display.setCursor(22, 42);
      display.print("StudySense Ready");
      break;

    case STATE_FLOW:
      drawFace(animFrame % 10 < 5 ? "^_^" : "*_*");
      display.setCursor(4, 40);
      display.print(dispSub.length() > 0 ? dispSub : "Flow State");
      display.setCursor(4, 52);
      display.print("Timer: ");
      display.print(dispTimer);
      break;

    case STATE_POSTURE_WARN:
      drawFace("O_O");
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
      drawFace(">_<");
      display.setCursor(4, 40);
      display.print("Poor Posture!");
      display.setCursor(4, 52);
      display.print("Correct Spine Now");
      break;

    case STATE_PHONE_ALERT:
      drawFace("X_X");
      display.setCursor(4, 40);
      display.print("Phone Detected!");
      display.setCursor(4, 52);
      display.print("Stay Focused");
      break;

    case STATE_ABSENT_ALERT:
      drawFace("?_?");
      display.setCursor(4, 40);
      display.print("Seat Empty!");
      display.setCursor(4, 52);
      display.print("Return to Desk");
      break;

    case STATE_BREAK:
      drawFace("Zzz");
      display.setCursor(4, 40);
      display.print("Restorative Break");
      display.setCursor(4, 52);
      display.print("Rest: ");
      display.print(dispTimer);
      break;

    case STATE_COMPLETE:
      drawFace(animFrame % 6 < 3 ? "\\o/" : "^o^");
      display.setCursor(4, 40);
      display.print("Great Session!");
      display.setCursor(4, 52);
      display.print("Session Saved");
      break;
  }

  display.display();
}

// =================== HARDWARE SELF-TEST ===================
void runSelfTest() {
  Serial.println("[BOOT] Running Hardware Self-Test...");
  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED,    OUTPUT);

  // Cycle LEDs
  setLeds(true, false, false);  delay(300);
  setLeds(false, true, false);  delay(300);
  setLeds(false, false, true);  delay(300);
  setLeds(false, false, false);

  // Initialize I2C OLED
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println("[BOOT] ERROR: SSD1306 allocation failed. Check OLED wiring!");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(10, 20);
    display.println("AI StudySense");
    display.setCursor(10, 35);
    display.println("Hardware Verified OK");
    display.display();
    delay(1000);
  }
}

// =================== PROTOCOL HANDLERS ===================
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
  Serial.printf("[WS] Handshake dispatched for %s\n", DEVICE_ID);
}

void sendHeartbeat() {
  StaticJsonDocument<192> doc;
  doc["type"] = "HEARTBEAT";
  doc["device_id"] = DEVICE_ID;
  doc["uptime_ms"] = millis();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();

  String out;
  serializeJson(doc, out);
  webSocket.sendTXT(out);
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

  // 1. Control Physical Traffic Light
  applyLed(ledColor);

  // 2. Select OLED Animation
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

  // 3. Send STATE_ACK
  StaticJsonDocument<128> ack;
  ack["type"] = "STATE_ACK";
  ack["device_id"] = DEVICE_ID;
  ack["seq"] = seq;
  String ackOut;
  serializeJson(ack, ackOut);
  webSocket.sendTXT(ackOut);
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      isWsConnected = false;
      setLeds(false, false, false);
      currentAnim = STATE_CONNECTING;
      dispTitle = "DISCONNECTED";
      dispSub = "Retrying Backend";
      Serial.println("[WS] Disconnected from server.");
      break;

    case WStype_CONNECTED:
      isWsConnected = true;
      Serial.printf("[WS] Connected to ws://%s:%d%s\n", BACKEND_HOST, BACKEND_PORT, WS_PATH);
      currentAnim = STATE_IDLE;
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
        dispSub = "Select topic to start";
      } else if (strcmp(msgType, "PING") == 0) {
        webSocket.sendTXT("{\"type\":\"PONG\",\"device_id\":\"" DEVICE_ID "\"}");
      }
      break;
    }
    default:
      break;
  }
}

// =================== ARDUINO SETUP ===================
void setup() {
  Serial.begin(115200);
  delay(300);

  runSelfTest();

  currentAnim = STATE_CONNECTING;
  dispTitle = "CONNECTING WIFI";
  dispSub = WIFI_SSID;

  Serial.printf("\n[WiFi] Connecting to %s...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned long startMs = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - startMs < 15000) {
    updateOledFrame();
    delay(80);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] Connected! IP: %s\n", WiFi.localIP().toString().c_str());
    dispTitle = "WIFI CONNECTED";
    dispSub = WiFi.localIP().toString();
  } else {
    Serial.println("\n[WiFi] Connection timeout. Retrying in background...");
    dispTitle = "WIFI FAILED";
    dispSub = "Check credentials";
  }

  // Connect WebSocket to Laptop Backend
  webSocket.begin(BACKEND_HOST, BACKEND_PORT, WS_PATH);
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(3000);
  webSocket.enableHeartbeat(15000, 3000, 2);
}

// =================== ARDUINO LOOP ===================
void loop() {
  webSocket.loop();
  updateOledFrame();

  unsigned long now = millis();
  if (isWsConnected && (now - lastHeartbeatMs >= HEARTBEAT_INTERVAL_MS)) {
    lastHeartbeatMs = now;
    sendHeartbeat();
  }
}
```

---

## 4. Steps to Establish Proper Connection between Website and Software

Follow these steps in sequence:

```
Step 1: Check Laptop Wi-Fi IP
         │
Step 2: Flash ESP32 & Connect to Same Wi-Fi
         │
Step 3: Start FastAPI Backend (0.0.0.0:8000)
         │
Step 4: Start React/Vite Frontend (localhost:5173)
         │
Step 5: Verify Hardware Status on Dashboard
         │
Step 6: Run Calibration & Start Live Study Session
```

---

### Step 1: Find Laptop's Local Wi-Fi IPv4 Address
The ESP32 is a standalone device on your home/office Wi-Fi. It **cannot** reach `localhost` or `127.0.0.1` because that refers to the ESP32 itself.

1. Open PowerShell or Command Prompt on your laptop:
   ```powershell
   ipconfig
   ```
2. Look for **Wireless LAN adapter Wi-Fi** → **IPv4 Address**.
   - Example: `10.162.167.218` or `192.168.1.45`.
3. In the ESP32 code above (or in `hardware/esp32_studysense/config.h`), verify that `BACKEND_HOST` matches this IP address:
   ```cpp
   const char* BACKEND_HOST = "10.162.167.218";
   ```

---

### Step 2: Flash the ESP32
1. Connect the ESP32 to your laptop using a micro-USB / USB-C data cable.
2. In Arduino IDE, select your board and the active COM port.
3. Open **Tools** → **Serial Monitor** and set baud rate to **115200**.
4. Click **Upload** (`Ctrl + U`).
5. After upload, inspect the Serial Monitor. You should see:
   ```text
   [BOOT] Running Hardware Self-Test...
   [WiFi] Connecting to YOUR_SSID...
   [WiFi] Connected! IP: 192.168.x.x
   [WS] Connecting to ws://10.162.167.218:8000/ws/device
   ```

---

### Step 3: Start the Python FastAPI Backend (Bound to `0.0.0.0`)
Open a terminal in the project root:

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Launch FastAPI bound to 0.0.0.0 so external Wi-Fi devices (ESP32) can connect
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Why `--host 0.0.0.0`?**  
> If you run on `--host 127.0.0.1`, only your laptop browser can connect. `--host 0.0.0.0` allows the ESP32 over Wi-Fi to reach port 8000.

When the ESP32 connects, your backend console will immediately log:
```text
[INFO] studysense.hardware: ESP32 [esp32_studysense] connected over WebSocket.
[INFO] studysense.hardware: Handshake accepted for [esp32_studysense].
```

---

### Step 4: Start the React / Vite Frontend
Open a second terminal window:

```powershell
cd frontend
npm run dev
```

The frontend will run at:
```text
http://localhost:5173
```

---

### Step 5: Verify the Hardware Connection in the Browser
1. Open `http://localhost:5173` in Chrome or Edge and sign in.
2. Look at the **Top Navigation Bar** or the **Live Study Session** page under **ESP32 IoT Physical Hardware**.
3. You will see:
   - **Hardware Status**: `Connected` (Green indicator)
   - **Signal**: Wi-Fi RSSI (e.g., `-52 dBm`)
   - **Assigned IP**: The ESP32's IP address
   - **Active LED**: `GREEN` (flow state)
4. *Optional quick test*: Use the Hardware REST test endpoint in PowerShell to manually toggle LEDs:
   ```powershell
   # Test Green
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"GREEN","oled_animation":"good_posture"}'
   
   # Test Yellow
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"YELLOW","oled_animation":"buffer_warning"}'
   
   # Test Red
   Invoke-RestMethod -Uri "http://localhost:8000/api/v1/hardware/test-mode" -Method Post -ContentType "application/json" -Body '{"led_state":"RED","oled_animation":"bad_posture"}'
   ```

---

### Step 6: Run Live Session with Real-Time Hardware Sync
1. Navigate to **Live Study Session** in the web app.
2. Select your topic from **"Today's Study Checklist & Topic Selection"**.
3. Complete the sequential calibration:
   - **Step 1: GOOD POSTURE FRAME** → Sit upright, capture, click **Confirm**.
   - **Step 2: BAD POSTURE FRAME** → Slouch / lean forward, capture, click **Confirm**.
4. Click **Start Live Session**.
5. Observe the live hardware response:
   - **Upright posture**: Green LED (GPIO 25) + Smiling face & live timer on OLED.
   - **Slouching / leaning forward**: Yellow LED (GPIO 26) with a 3-second countdown on OLED.
   - **Bad posture > 3 seconds**: Red LED (GPIO 27) + Alert face `>_<` on OLED.
   - **Taking a break**: Green LED + Sleepy face `Zzz` with break countdown on OLED.
   - **Finishing session**: Celebration animation `\o/` on OLED + Performance report generated on website.

---

## 5. Troubleshooting & Checklist

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **OLED display is blank on boot** | I2C wiring or wrong address | Verify SDA is connected to **GPIO 21** and SCL to **GPIO 22**. Most 0.96″ OLEDs use address `0x3C`. |
| **LEDs do not turn on** | Incorrect GPIO pin or missing ground | Ensure Green = **GPIO 25**, Yellow = **GPIO 26**, Red = **GPIO 27**, and **GND** is connected to ESP32 GND. |
| **ESP32 prints `Connecting WiFi ...` indefinitely** | 5 GHz Wi-Fi or wrong password | ESP32 only supports **2.4 GHz** Wi-Fi networks. Make sure you use a 2.4 GHz SSID. |
| **`[WS] Disconnected from server` repeatedly** | Host IP mismatch or firewall blocking port 8000 | 1. Verify `BACKEND_HOST` matches `ipconfig` Wi-Fi IPv4.<br>2. In Windows Defender Firewall, allow port `8000` inbound, or temporarily disable private network firewall for testing. |
| **Backend started with `127.0.0.1` instead of `0.0.0.0`** | Backend listening only on local loopback | Start backend with `--host 0.0.0.0 --port 8000`. |
| **ESP32 disconnects after 15 seconds** | Missing heartbeat | Ensure `webSocket.loop()` runs in `loop()` without blocking `delay()` calls. Heartbeat is sent automatically every 5s. |
