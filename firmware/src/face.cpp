#include "face.h"
#include "config.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

namespace Face {
static Adafruit_SSD1306 oled(128, 64, &Wire, -1);
static bool ok = false;
static Mood mood = SLEEPY;
static uint32_t nextBlink = 0, blinkUntil = 0;
static char line[22] = "";
static const char *NAMES[] = {"happy", "sleepy", "focus", "angry", "surprised", "sad", "love", "wink"};

void begin() {
  Wire.begin(PIN_SDA, PIN_SCL);
  ok = oled.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  if (ok) { oled.clearDisplay(); oled.display(); }
}
void set(Mood m) { mood = m; }
Mood get() { return mood; }
const char *name(Mood m) { return NAMES[m]; }
bool fromName(const char *s, Mood &out) {
  for (int i = 0; i < 8; i++) if (!strcmp(s, NAMES[i])) { out = (Mood)i; return true; }
  return false;
}
void status(const char *s) { strncpy(line, s, sizeof(line) - 1); }

static void eye(int cx, int cy, bool closed, Mood m, bool left) {
  if (closed || m == SLEEPY) { oled.fillRoundRect(cx - 14, cy - 2, 28, 5, 2, SSD1306_WHITE); return; }
  switch (m) {
    case HAPPY:      // upside-down U
      oled.fillRoundRect(cx - 14, cy - 12, 28, 24, 10, SSD1306_WHITE);
      oled.fillRect(cx - 15, cy + 2, 30, 12, SSD1306_BLACK);
      oled.fillRoundRect(cx - 10, cy - 7, 20, 10, 5, SSD1306_BLACK);
      break;
    case FOCUS:      // flat-topped "goggles"
      oled.fillRoundRect(cx - 14, cy - 10, 28, 20, 4, SSD1306_WHITE);
      oled.fillRect(cx - 15, cy - 11, 30, 6, SSD1306_BLACK);
      break;
    case ANGRY:
      oled.fillRoundRect(cx - 13, cy - 10, 26, 20, 6, SSD1306_WHITE);
      if (left) oled.fillTriangle(cx - 15, cy - 12, cx + 15, cy - 12, cx + 15, cy, SSD1306_BLACK);
      else oled.fillTriangle(cx - 15, cy - 12, cx + 15, cy - 12, cx - 15, cy, SSD1306_BLACK);
      break;
    case SURPRISED:
      oled.fillCircle(cx, cy, 13, SSD1306_WHITE); oled.fillCircle(cx, cy, 6, SSD1306_BLACK);
      break;
    case SAD:
      oled.fillRoundRect(cx - 12, cy - 8, 24, 18, 7, SSD1306_WHITE);
      if (left) oled.fillTriangle(cx - 14, cy - 10, cx + 14, cy - 10, cx - 14, cy + 2, SSD1306_BLACK);
      else oled.fillTriangle(cx - 14, cy - 10, cx + 14, cy - 10, cx + 14, cy + 2, SSD1306_BLACK);
      break;
    case LOVE:
      oled.fillCircle(cx - 6, cy - 4, 7, SSD1306_WHITE); oled.fillCircle(cx + 6, cy - 4, 7, SSD1306_WHITE);
      oled.fillTriangle(cx - 13, cy - 1, cx + 13, cy - 1, cx, cy + 13, SSD1306_WHITE);
      break;
    case WINK:
      if (left) oled.fillRoundRect(cx - 13, cy - 12, 26, 24, 8, SSD1306_WHITE);
      else { oled.fillRoundRect(cx - 14, cy - 2, 28, 5, 2, SSD1306_WHITE); }
      break;
    default: break;
  }
}

void update() {
  if (!ok) return;
  const uint32_t now = millis();
  if (now > nextBlink) { blinkUntil = now + 120; nextBlink = now + 2500 + random(3500); }
  const bool closed = now < blinkUntil && mood != WINK && mood != LOVE;
  oled.clearDisplay();
  eye(36, 26, closed, mood, true);
  eye(92, 26, closed, mood, false);
  // mouth
  if (mood == HAPPY || mood == LOVE || mood == WINK) { oled.drawCircleHelper(64, 40, 6, 0x4 | 0x8, SSD1306_WHITE); }
  else if (mood == SURPRISED) oled.drawCircle(64, 46, 3, SSD1306_WHITE);
  else if (mood == SAD || mood == ANGRY) oled.drawCircleHelper(64, 50, 6, 0x1 | 0x2, SSD1306_WHITE);
  else oled.drawFastHLine(60, 46, 9, SSD1306_WHITE);
  oled.setTextSize(1); oled.setTextColor(SSD1306_WHITE);
  oled.setCursor((128 - 6 * strlen(line)) / 2, 56); oled.print(line);
  oled.display();
}
}  // namespace Face
