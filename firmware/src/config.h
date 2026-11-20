// SkyCrawler — wiring and tuning. Change pins here if your board differs.
#pragma once
#include <Arduino.h>

// ---------- pins (ESP32-S3 SuperMini: GPIO 1-13, 43/44, RGB LED on 48) ----------
// Leg order: 0 = front-right, 1 = front-left, 2 = back-left, 3 = back-right
static const uint8_t PIN_VBAT = 1;                     // battery divider 100k/22k (ADC1)
static const uint8_t PIN_HIP[4]  = {2, 3, 4, 5};
static const uint8_t PIN_KNEE[4] = {6, 7, 8, 9};
static const uint8_t PIN_SDA = 10, PIN_SCL = 11;       // SSD1306 128x64 OLED face
static const uint8_t PIN_BUZZER = 12;                  // active buzzer (optional)
static const uint8_t PIN_CRSF_TX = 43, PIN_CRSF_RX = 44;  // to the flight controller UART (RX / TX pads)
static const float VBAT_SCALE = (100.0f + 22.0f) / 22.0f;  // divider ratio

// ---------- servos ----------
static const int SERVO_MIN_US = 500, SERVO_MAX_US = 2500;   // MG90S: 0..180°
// Angle convention (degrees, after calibration):
//   hip  0 = leg pointing straight out along its diagonal, + = towards the front of the robot
//   knee 0 = shin level (drone arm, on the end stop), 90 = shin straight down (standing)
static const float HIP_LIMIT = 50.0f;
static const float KNEE_MIN = -2.0f, KNEE_MAX = 112.0f;
// default trims; overwrite them from the app (Calibrate) — they are saved in flash
static const float HIP_TRIM_DEFAULT[4]  = {0, 0, 0, 0};
static const float KNEE_TRIM_DEFAULT[4] = {0, 0, 0, 0};
// mirror flags: servos on the left side turn the other way for the same leg motion
static const bool HIP_REV[4]  = {false, true, false, true};
static const bool KNEE_REV[4] = {false, true, false, true};

// ---------- gait ----------
static const float STAND_KNEE = 92.0f;      // knee angle when standing
static const float SIT_KNEE = 18.0f;        // legs splayed out, body resting on its belly (power-on pose)
static const float STEP_HIP = 22.0f;        // hip sweep per step (deg)
static const float STEP_LIFT = 28.0f;       // knee lift while a leg swings (deg)
static const float GAIT_HZ = 1.6f;          // full gait cycles per second at full stick

// ---------- flight link ----------
static const uint32_t CRSF_BAUD = 420000;
static const uint32_t CRSF_PERIOD_MS = 10;  // 100 Hz RC frames
static const uint32_t LINK_TIMEOUT_MS = 350; // no app packets for this long = failsafe
static const uint16_t ARM_HOLD_MS = 1000;    // app must hold ARM this long

// ---------- WiFi ----------
static const char *AP_PASS = "skycrawler";   // change me! (8+ chars)
static const uint16_t WS_PORT = 81;
