#ifndef CONFIG_H
#define CONFIG_H

// =========================================================================
// AI StudySense - ESP32 Hardware Network Configuration Template
//
// Copy this file to "config.h" and enter your Wi-Fi credentials and Laptop IP:
//   cp config.example.h config.h
//
// CRITICAL: Never use "localhost" or "127.0.0.1" for ESP32.
// Use your laptop's reachable IPv4 address on the local Wi-Fi network.
// =========================================================================

// Wi-Fi Access Point Credentials
#define WIFI_SSID     "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// Laptop FastAPI Backend Server
#define BACKEND_HOST  "192.168.1.100"  // Replace with your laptop's Wi-Fi IPv4
#define BACKEND_PORT  8000
#define WS_PATH       "/ws/device"

// Device Metadata
#define DEVICE_ID     "esp32_studysense"
#define FIRMWARE_VER  "2.0.0"
#define CHIP_MODEL    "ESP32-38PIN"

#endif // CONFIG_H
