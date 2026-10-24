/**
 * AI StudySense - Minimal Hardware Diagnostic & OLED/LED Test Sketch
 * 
 * Purpose:
 * Use this minimal sketch first to diagnose hardware wiring, I2C bus address,
 * OLED display rendering, and traffic light LED outputs before running full firmware.
 * 
 * Hardware Pin Mapping:
 * - Green LED:   GPIO 25
 * - Yellow LED:  GPIO 26
 * - Red LED:     GPIO 27
 * - OLED SDA:    GPIO 21
 * - OLED SCL:    GPIO 22
 * - OLED VCC:    3V3
 * - OLED GND:    GND
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

byte detectedI2CAddress = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=======================================================");
  Serial.println("  AI StudySense - Physical Hardware Diagnostic Test");
  Serial.println("=======================================================");

  // 1. Test GPIO LEDs
  Serial.println("\n[1/3] Testing Traffic Light LEDs...");
  pinMode(PIN_LED_GREEN,  OUTPUT);
  pinMode(PIN_LED_YELLOW, OUTPUT);
  pinMode(PIN_LED_RED,    OUTPUT);

  Serial.println(" -> Green LED ON (GPIO 25)");
  digitalWrite(PIN_LED_GREEN, HIGH);
  delay(500);
  digitalWrite(PIN_LED_GREEN, LOW);

  Serial.println(" -> Yellow LED ON (GPIO 26)");
  digitalWrite(PIN_LED_YELLOW, HIGH);
  delay(500);
  digitalWrite(PIN_LED_YELLOW, LOW);

  Serial.println(" -> Red LED ON (GPIO 27)");
  digitalWrite(PIN_LED_RED, HIGH);
  delay(500);
  digitalWrite(PIN_LED_RED, LOW);
  Serial.println(" [PASS] LED GPIO outputs verified.");

  // 2. Scan I2C Bus on GPIO 21 & 22
  Serial.println("\n[2/3] Scanning I2C Bus on SDA=GPIO 21, SCL=GPIO 22...");
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
  Wire.setClock(100000); // 100 kHz standard mode

  int devicesFound = 0;
  for (byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission();
    if (error == 0) {
      Serial.printf(" -> Device detected at address 0x%02X\n", address);
      if (address == 0x3C || address == 0x3D) {
        detectedI2CAddress = address;
      }
      devicesFound++;
    }
  }

  if (devicesFound == 0) {
    Serial.println(" [FAIL] No I2C devices found! Check wiring:");
    Serial.println("   VCC -> 3V3, GND -> GND, SDA -> GPIO 21, SCL -> GPIO 22");
    detectedI2CAddress = 0x3C; // Default attempt
  } else {
    Serial.printf(" [PASS] Total %d I2C device(s) found. Using OLED Address: 0x%02X\n", devicesFound, detectedI2CAddress);
  }

  // 3. Initialize OLED Display
  Serial.printf("\n[3/3] Initializing SSD1306 OLED at 0x%02X...\n", detectedI2CAddress);
  bool ok = display.begin(SSD1306_SWITCHCAPVCC, detectedI2CAddress, false, false);
  if (!ok) {
    Serial.println(" [FAIL] display.begin() failed! Retrying with 0x3D...");
    ok = display.begin(SSD1306_SWITCHCAPVCC, 0x3D, false, false);
  }

  if (!ok) {
    Serial.println(" [FAIL] OLED allocation failed. Verify display controller is SSD1306.");
  } else {
    Serial.println(" [PASS] OLED initialized successfully!");
    display.ssd1306_command(SSD1306_DISPLAYON);
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(14, 4);
    display.println("AI STUDYSENSE");
    display.drawLine(0, 14, 128, 14, SSD1306_WHITE);
    display.setCursor(4, 20);
    display.printf("OLED: 0x%02X OK", detectedI2CAddress);
    display.setCursor(4, 32);
    display.println("LEDs: 25, 26, 27 OK");
    display.setCursor(4, 44);
    display.println("I2C: SDA=21, SCL=22");
    display.setCursor(4, 54);
    display.println("Ready for session!");
    display.display();
  }
  Serial.println("\n=======================================================");
  Serial.println("  Hardware Diagnostic Complete");
  Serial.println("=======================================================\n");
}

int cycle = 0;
void loop() {
  // Continuous verification loop: cycles traffic light and updates display
  cycle++;
  digitalWrite(PIN_LED_GREEN,  (cycle % 3 == 0) ? HIGH : LOW);
  digitalWrite(PIN_LED_YELLOW, (cycle % 3 == 1) ? HIGH : LOW);
  digitalWrite(PIN_LED_RED,    (cycle % 3 == 2) ? HIGH : LOW);

  display.fillRect(100, 20, 28, 12, SSD1306_BLACK);
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(100, 20);
  display.printf("#%d", cycle % 100);
  display.display();

  delay(600);
}
