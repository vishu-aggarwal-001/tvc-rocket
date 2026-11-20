#pragma once
#include <Arduino.h>
// WiFi access point + WebSocket link to the phone app (and a small status page on port 80).
namespace Net {
struct Sticks { float lx = 0, ly = 0, rx = 0, ry = 0; };
typedef void (*CmdHandler)(const char *cmd, const char *arg, float value);
void begin(CmdHandler h);
void loop();
const Sticks &sticks();
uint32_t lastInputMs();          // millis() of the last stick packet
bool connected();
void sendText(const String &json);
const char *ssid();
}
