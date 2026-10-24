#ifndef CONFIG_H
#define CONFIG_H

// =========================================================================
// AI StudySense - ESP32 Hardware Network Configuration
//
// CRITICAL: Never use "localhost" or "127.0.0.1" for ESP32.
// Use your laptop's reachable IPv4 address on the local Wi-Fi network.
// =========================================================================

// Wi-Fi Access Point Credentials
// (Update with your 2.4 GHz Wi-Fi network credentials)
#define WIFI_SSID     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Laptop FastAPI Backend Server
// Current Laptop Wi-Fi IPv4 address: 10.162.167.218 (or update if IP changes)
#define BACKEND_HOST  "10.162.167.218"
#define BACKEND_PORT  8000
#define WS_PATH       "/ws/device"    // Also supports "/ws/esp32"

// Device Metadata
#define DEVICE_ID     "esp32_studysense"
#define FIRMWARE_VER  "2.0.0"
#define CHIP_MODEL    "ESP32-38PIN"

// Hardware Diagnostics
// Set to false after initial physical verification to boot directly into connection mode
#define ENABLE_HARDWARE_SELF_TEST true

#endif // CONFIG_H
