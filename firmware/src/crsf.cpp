#include "crsf.h"

namespace Crsf {
static HardwareSerial *ser = nullptr;
static uint8_t buf[64];
static int n = 0;
static uint32_t lastTelem = 0;
static float vb = 0, pitch = 0, roll = 0;

static uint8_t crc8(const uint8_t *p, int len) {
  uint8_t c = 0;
  for (int i = 0; i < len; i++) {
    c ^= p[i];
    for (int b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0xD5) : (uint8_t)(c << 1);
  }
  return c;
}

void begin(HardwareSerial &port, int rxPin, int txPin) {
  ser = &port;
  ser->begin(420000, SERIAL_8N1, rxPin, txPin);
}

void send(const uint16_t ch[16]) {
  if (!ser) return;
  uint8_t f[26];
  f[0] = 0xC8;            // address: flight controller
  f[1] = 24;              // length (type + 22 payload + crc)
  f[2] = 0x16;            // RC_CHANNELS_PACKED
  uint32_t bits = 0; int bitn = 0, o = 3;
  for (int i = 0; i < 16; i++) {
    int us = constrain((int)ch[i], 988, 2012);
    uint32_t v = (uint32_t)((us - 1500) * 8 / 5 + 992);   // 172..1811
    bits |= v << bitn; bitn += 11;
    while (bitn >= 8) { f[o++] = bits & 0xFF; bits >>= 8; bitn -= 8; }
  }
  f[25] = crc8(&f[2], 23);
  ser->write(f, 26);
}

static void handle(const uint8_t *fr, int len) {
  const uint8_t type = fr[2];
  const uint8_t *p = &fr[3];
  if (type == 0x08 && len >= 10) {          // BATTERY_SENSOR: voltage in 0.1 V, big endian
    vb = ((p[0] << 8) | p[1]) / 10.0f; lastTelem = millis();
  } else if (type == 0x1E && len >= 8) {    // ATTITUDE: pitch, roll, yaw in 1e-4 rad, big endian
    pitch = (int16_t)((p[0] << 8) | p[1]) / 10000.0f * 57.2958f;
    roll = (int16_t)((p[2] << 8) | p[3]) / 10000.0f * 57.2958f;
    lastTelem = millis();
  } else if (type == 0x21 || type == 0x14) {   // flight mode / link stats: just liveness
    lastTelem = millis();
  }
}

void poll() {
  if (!ser) return;
  while (ser->available()) {
    uint8_t b = ser->read();
    if (n == 0 && b != 0xC8 && b != 0xEA && b != 0xEE) continue;   // sync bytes
    buf[n++] = b;
    if (n == 2 && (buf[1] < 2 || buf[1] > 62)) { n = 0; continue; }
    if (n >= 2 && n == buf[1] + 2) {
      if (crc8(&buf[2], buf[1] - 1) == buf[n - 1]) handle(buf, n);
      n = 0;
    }
    if (n >= (int)sizeof(buf)) n = 0;
  }
}

bool fcAlive() { return lastTelem && millis() - lastTelem < 1500; }
float vbat() { return vb; }
float pitchDeg() { return pitch; }
float rollDeg() { return roll; }
}  // namespace Crsf
