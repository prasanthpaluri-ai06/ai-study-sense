#ifndef DISPLAY_ANIMATIONS_H
#define DISPLAY_ANIMATIONS_H

#include <Arduino.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

/**
 * AI StudySense - Non-Blocking OLED Animation & State Machine Engine
 * 
 * Drives 0.96-inch SSD1306 (128x64) I2C OLED display smoothly at ~12 FPS
 * without using any blocking delay() calls. Network handling, WebSocket frames,
 * and timer ticks remain completely responsive while animations render.
 */

enum AnimState {
    ANIM_STARTUP,
    ANIM_SELF_TEST,
    ANIM_CONNECTING,
    ANIM_CONNECTED,
    ANIM_GOOD_POSTURE,
    ANIM_POSTURE_WARNING,
    ANIM_BAD_POSTURE,
    ANIM_FOCUSED,
    ANIM_DISTRACTED,
    ANIM_ABSENT,
    ANIM_BREAK,
    ANIM_SESSION_COMPLETE,
    ANIM_RECONNECTING,
    ANIM_IDLE
};

class DisplayAnimationManager {
private:
    Adafruit_SSD1306* display;
    AnimState currentState;
    unsigned long lastFrameMs;
    unsigned long stateEnteredMs;
    int animFrame;
    
    char titleBuf[32];
    char subtitleBuf[32];
    char timerBuf[16];
    int countdownSeconds;

public:
    DisplayAnimationManager(Adafruit_SSD1306* disp)
        : display(disp),
          currentState(ANIM_STARTUP),
          lastFrameMs(0),
          stateEnteredMs(0),
          animFrame(0),
          countdownSeconds(-1)
    {
        strcpy(titleBuf, "AI STUDYSENSE");
        strcpy(subtitleBuf, "Ready");
        strcpy(timerBuf, "00:00");
    }

    void setState(
        AnimState newState,
        const char* title = nullptr,
        const char* subtitle = nullptr,
        const char* timerStr = nullptr,
        int countdown = -1
    ) {
        if (title && strlen(title) > 0) {
            strncpy(titleBuf, title, sizeof(titleBuf) - 1);
            titleBuf[sizeof(titleBuf) - 1] = '\0';
        }
        if (subtitle && strlen(subtitle) > 0) {
            strncpy(subtitleBuf, subtitle, sizeof(subtitleBuf) - 1);
            subtitleBuf[sizeof(subtitleBuf) - 1] = '\0';
        }
        if (timerStr && strlen(timerStr) > 0) {
            strncpy(timerBuf, timerStr, sizeof(timerBuf) - 1);
            timerBuf[sizeof(timerBuf) - 1] = '\0';
        }
        countdownSeconds = countdown;

        if (currentState != newState) {
            currentState = newState;
            stateEnteredMs = millis();
            animFrame = 0;
            renderCurrentFrame(); // Immediate first frame render
        }
    }

    AnimState getState() const {
        return currentState;
    }

    void setTimer(const char* timerStr) {
        if (timerStr && strlen(timerStr) > 0) {
            strncpy(timerBuf, timerStr, sizeof(timerBuf) - 1);
            timerBuf[sizeof(timerBuf) - 1] = '\0';
        }
    }

    void setCountdown(int secs) {
        countdownSeconds = secs;
    }

    /**
     * Non-blocking update loop. Must be called in loop().
     * Advances animation frames at ~12 FPS (every 80 ms).
     */
    void update() {
        unsigned long now = millis();
        if (now - lastFrameMs >= 80) {
            lastFrameMs = now;
            animFrame++;
            renderCurrentFrame();
        }
    }

    void renderSelfTest(bool greenOk, bool yellowOk, bool redOk, bool oledOk) {
        display->clearDisplay();
        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(18, 4);
        display->println("HARDWARE SELF-TEST");
        display->drawLine(0, 14, 128, 14, SSD1306_WHITE);

        display->setCursor(6, 18);
        display->printf("OLED I2C (21,22): %s", oledOk ? "[PASS]" : "[FAIL]");
        display->setCursor(6, 29);
        display->printf("LED GREEN (25):   %s", greenOk ? "[PASS]" : "[FAIL]");
        display->setCursor(6, 40);
        display->printf("LED YELLOW (26):  %s", yellowOk ? "[PASS]" : "[FAIL]");
        display->setCursor(6, 51);
        display->printf("LED RED (27):     %s", redOk ? "[PASS]" : "[FAIL]");
        display->display();
    }

private:
    void renderCurrentFrame() {
        display->clearDisplay();
        display->setTextColor(SSD1306_WHITE);

        switch (currentState) {
            case ANIM_STARTUP:
                drawStartup();
                break;
            case ANIM_SELF_TEST:
                // Rendered explicitly by renderSelfTest()
                break;
            case ANIM_CONNECTING:
                drawConnecting();
                break;
            case ANIM_CONNECTED:
                drawConnected();
                break;
            case ANIM_GOOD_POSTURE:
                drawGoodPosture();
                break;
            case ANIM_POSTURE_WARNING:
                drawPostureWarning();
                break;
            case ANIM_BAD_POSTURE:
                drawBadPosture();
                break;
            case ANIM_FOCUSED:
                drawFocused();
                break;
            case ANIM_DISTRACTED:
                drawDistracted();
                break;
            case ANIM_ABSENT:
                drawAbsent();
                break;
            case ANIM_BREAK:
                drawBreak();
                break;
            case ANIM_SESSION_COMPLETE:
                drawSessionComplete();
                break;
            case ANIM_RECONNECTING:
                drawReconnecting();
                break;
            case ANIM_IDLE:
            default:
                drawIdle();
                break;
        }

        display->display();
    }

    void drawStartup() {
        display->setTextSize(1);
        display->setCursor(20, 8);
        display->println("AI STUDYSENSE");
        
        display->drawRect(10, 20, 108, 38, SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(44, 26);
        display->println("^_^");
        
        display->setTextSize(1);
        display->setCursor(30, 46);
        display->println("BOOTING UP");
    }

    void drawConnecting() {
        display->fillRect(0, 0, 128, 12, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(18, 2);
        display->println("CONNECTING WI-FI");

        display->setTextColor(SSD1306_WHITE);
        // Animated rotating spinner
        int spinFrame = (animFrame / 2) % 4;
        display->setTextSize(2);
        display->setCursor(48, 22);
        if (spinFrame == 0) display->println("o . .");
        else if (spinFrame == 1) display->println(". o .");
        else if (spinFrame == 2) display->println(". . o");
        else display->println("o o o");

        display->setTextSize(1);
        display->setCursor(8, 48);
        display->printf("%.18s", subtitleBuf);
    }

    void drawConnected() {
        display->fillRect(0, 0, 128, 12, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(30, 2);
        display->println("ONLINE & SYNCED");

        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println("^_^");

        display->setTextSize(1);
        display->setCursor(12, 48);
        display->printf("IP: %.16s", subtitleBuf);
    }

    void drawGoodPosture() {
        // Solid inverted header bar
        display->fillRect(0, 0, 128, 13, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(24, 3);
        display->println("POSTURE GOOD");

        display->setTextColor(SSD1306_WHITE);
        // Blinking face every 24 frames
        bool blink = (animFrame % 24) == 0;
        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println(blink ? "-_-" : "^_^");

        // Subtitle / timer footer
        display->setTextSize(1);
        display->setCursor(12, 48);
        if (strlen(timerBuf) > 0 && strcmp(timerBuf, "00:00") != 0) {
            display->printf("%.10s  [%s]", subtitleBuf, timerBuf);
        } else {
            display->printf("%.18s", subtitleBuf);
        }
    }

    void drawPostureWarning() {
        // Flashing border
        bool flash = (animFrame % 6) < 3;
        if (flash) {
            display->drawRect(0, 0, 128, 64, SSD1306_WHITE);
        }

        display->setTextSize(1);
        display->setCursor(14, 6);
        display->println("[!] POSTURE WARNING");

        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println("-_-");

        display->setTextSize(1);
        display->setCursor(8, 48);
        if (countdownSeconds >= 0) {
            display->printf("SIT UP: %ds TO ALERT", countdownSeconds);
        } else {
            display->printf("%.18s", subtitleBuf);
        }
    }

    void drawBadPosture() {
        // Inverted alert banner
        display->fillRect(0, 0, 128, 16, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(14, 4);
        display->println("! BAD POSTURE ALERT !");

        display->setTextColor(SSD1306_WHITE);
        // Shake offset for intense alert animation
        int shake = ((animFrame % 4) == 0) ? 2 : 0;
        display->setTextSize(2);
        display->setCursor(44 + shake, 24);
        display->println(">_<");

        display->setTextSize(1);
        display->setCursor(8, 48);
        display->println("SIT STRAIGHT NOW!");
    }

    void drawFocused() {
        display->fillRect(0, 0, 128, 12, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(28, 2);
        display->println("FLOW STATE");

        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(44, 20);
        display->println("^_^");

        // Centered timer
        display->setTextSize(1);
        display->setCursor(36, 48);
        display->printf("TIME: %s", timerBuf);
    }

    void drawDistracted() {
        display->drawRect(0, 0, 128, 14, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(10, 3);
        display->println("DISTRACTION DETECTED");

        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println("O.O");

        display->setTextSize(1);
        display->setCursor(10, 48);
        display->printf("%.18s", subtitleBuf);
    }

    void drawAbsent() {
        display->fillRect(0, 0, 128, 14, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(18, 3);
        display->println("STUDENT ABSENT");

        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println("X_X");

        display->setTextSize(1);
        display->setCursor(16, 48);
        display->println("Away from desk");
    }

    void drawBreak() {
        display->fillRect(0, 0, 128, 13, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(28, 3);
        display->println("REST BREAK");

        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(44, 22);
        display->println("Zzz");

        display->setTextSize(1);
        display->setCursor(20, 48);
        display->printf("REMAIN: %s", timerBuf);
    }

    void drawSessionComplete() {
        display->fillRect(0, 0, 128, 14, SSD1306_WHITE);
        display->setTextColor(SSD1306_BLACK, SSD1306_WHITE);
        display->setTextSize(1);
        display->setCursor(14, 3);
        display->println("SESSION COMPLETE");

        display->setTextColor(SSD1306_WHITE);
        display->setTextSize(2);
        display->setCursor(42, 22);
        display->println("*_*"); // Star eyes

        display->setTextSize(1);
        display->setCursor(18, 48);
        display->println("Great Study Sprint!");
    }

    void drawReconnecting() {
        display->setTextSize(1);
        display->setCursor(18, 8);
        display->println("DISCONNECTED");

        display->drawRect(10, 20, 108, 22, SSD1306_WHITE);
        display->setCursor(16, 26);
        display->println("Reconnecting...");

        // Animated dots
        int dotCount = (animFrame / 3) % 4;
        display->setCursor(48, 48);
        for (int i = 0; i < dotCount; i++) display->print(".");
    }

    void drawIdle() {
        display->setTextSize(1);
        display->setCursor(24, 6);
        display->println("AI STUDYSENSE");
        display->drawLine(0, 16, 128, 16, SSD1306_WHITE);

        display->setTextSize(2);
        display->setCursor(44, 24);
        display->println("^_^");

        display->setTextSize(1);
        display->setCursor(18, 48);
        display->println("Ready to study");
    }
};

#endif // DISPLAY_ANIMATIONS_H
