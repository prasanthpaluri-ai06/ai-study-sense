# AI StudySense - Hardware Subsystem

## Overview
The ESP32 microcontroller acts as the **wireless bridge and physical interface** for the AI StudySense system. The laptop performs all heavy computer-vision and AI calculations, streaming states to the ESP32 over a real-time WebSocket connection (`ws://<laptop_ip>:8000/ws/esp32`).

## Components
1. **ESP32 NodeMCU / Dev Module**
2. **0.96-inch OLED Display (I2C SSD1306, 128x64)**
3. **Traffic Light LED Module (Red, Yellow, Green)**
4. **Breadboard & Jumper Wires**

## Pin Connections

### OLED Display (I2C)
| OLED Pin | ESP32 GPIO Pin |
|---|---|
| VCC | 3.3V / 5V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### Traffic Light Module
| Traffic Light Pin | ESP32 GPIO Pin | Meaning in AI StudySense |
|---|---|---|
| R (Red LED) | GPIO 18 | Poor posture confirmed (> 10s threshold) |
| Y (Yellow LED) | GPIO 19 | Posture buffer warning (temporary slouch) |
| G (Green LED) | GPIO 23 | Good upright posture |
| GND | GND | Common Ground |

## Flashing Instructions
1. Open Arduino IDE or PlatformIO.
2. Install the required libraries via Arduino Library Manager:
   - `Adafruit SSD1306`
   - `Adafruit GFX Library`
   - `WebSockets` by Markus Sattler
   - `ArduinoJson` (v6+)
3. Open `hardware/esp32_studysense/esp32_studysense.ino`.
4. Update `WIFI_SSID`, `WIFI_PASSWORD`, and `BACKEND_HOST` (your laptop's local IP).
5. Select board **ESP32 Dev Module** and the correct COM port.
6. Click **Upload**.
