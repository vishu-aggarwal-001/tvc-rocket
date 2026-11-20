#pragma once
#include <Arduino.h>
// CRSF (Crossfire / ELRS) receiver emulation: the ESP32 tells the Betaflight flight
// controller what the sticks are doing, exactly like an ELRS receiver would, and reads
// back the FC's battery telemetry. Wire ESP TX -> FC RX of a UART set to "Serial RX".
namespace Crsf {
void begin(HardwareSerial &port, int rxPin, int txPin);
// channels in microseconds (988..2012). ch[0..3] = roll, pitch, throttle, yaw (AETR)
void send(const uint16_t ch[16]);
void poll();                     // read telemetry, call often
bool fcAlive();                  // got a telemetry frame recently
float vbat();                    // volts from the FC (0 if unknown)
float pitchDeg();
float rollDeg();
}
