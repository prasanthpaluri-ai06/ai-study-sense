# AI StudySense - Hardware Setup & Wiring Guide

## Overview
This document guides you through wiring the ESP32, 0.96-inch OLED display, and Traffic Light LED module on a breadboard.

## Wiring Diagram

### 1. 0.96" I2C OLED (SSD1306)
- **VCC** -> ESP32 **3.3V** (or **VIN 5V**)
- **GND** -> ESP32 **GND**
- **SDA** -> ESP32 **GPIO 21**
- **SCL** -> ESP32 **GPIO 22**

### 2. Traffic Light Module
- **R (Red LED)** -> ESP32 **GPIO 18**
- **Y (Yellow LED)** -> ESP32 **GPIO 19**
- **G (Green LED)** -> ESP32 **GPIO 23**
- **GND** -> ESP32 **GND** (Common Ground)

## Physical Behavior
1. **Power On / Boot:** OLED shows `AI STUDYSENSE ^_^ STARTING...`.
2. **Wi-Fi Search:** OLED shows `CONNECTING o . .`.
3. **Wi-Fi Connected:** OLED shows `CONNECTED! IP: 192.168.x.x`.
4. **Active Session - Good Posture:** Green LED lights up; OLED shows `^_^ POSTURE GOOD`.
5. **Active Session - Slouch Warning (< 10s):** Yellow LED lights up; OLED shows `-_- [!] WARNING Check posture`.
6. **Active Session - Bad Posture (> 10s):** Red LED lights up; OLED shows `>_< POSTURE ALERT Sit upright!`.
7. **Session End:** Green LED lights up; OLED shows `[v] SESSION COMPLETE`.
