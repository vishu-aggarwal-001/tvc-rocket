// SkyCrawler — a walking robot that turns into a quadcopter.
// The ESP32-S3 is the robot's brain: it walks the legs, runs the transformation, draws
// the face, talks to the phone app over WiFi and, in drone mode, drives the Betaflight
// flight controller over CRSF like a radio receiver. Betaflight does the flying.
#include <Arduino.h>
#include "config.h"
#include "servos.h"
#include "gait.h"
#include "face.h"
#include "crsf.h"
#include "net.h"

enum Mode { SIT, STAND, TO_FLY, FLY, TO_WALK, TRICK, SERVICE };
static const char *MODE_NAMES[] = {"SIT", "WALK", "TO_FLY", "FLY", "TO_WALK", "TRICK", "SERVICE"};
static Mode mode = SIT;
static int step = 0;               // sub-step inside a transformation
static uint32_t stepT = 0;
static bool armed = false, beeper = false;
static uint32_t moodHoldUntil = 0, trickUntil = 0;
static String trickName;
static float vbatAdc = 0;
static int cells = 0;
static String note;

static void beep(int ms) { digitalWrite(PIN_BUZZER, HIGH); delay(ms); digitalWrite(PIN_BUZZER, LOW); }
static void setMode(Mode m) { mode = m; step = 0; stepT = millis(); }
static float vbat() { float v = Crsf::vbat(); return v > 1 ? v : vbatAdc; }
static bool kneesLevel() { for (int i = 0; i < 4; i++) if (fabsf(Servos::knee(i)) > 2.5f) return false; return true; }

// ---------------------------------------------------------------- commands from the app
static void onCmd(const char *c, const char *a, float v) {
  if (!strcmp(c, "hello")) { note = "app connected"; return; }
  if (!strcmp(c, "sit") && !armed && (mode == STAND || mode == TRICK || mode == SERVICE)) { setMode(SIT); return; }
  if (!strcmp(c, "stand") && !armed && (mode == SIT || mode == TRICK || mode == SERVICE)) { setMode(STAND); return; }
  if (!strcmp(c, "fly") && (mode == SIT || mode == STAND)) { setMode(TO_FLY); return; }
  if (!strcmp(c, "walk") && mode == FLY) {
    if (armed) { note = "disarm first"; return; }
    setMode(TO_WALK); return;
  }
  if (!strcmp(c, "arm")) {
    const Net::Sticks &s = Net::sticks();
    const float thr = (s.ly + 1) / 2;
    if (mode != FLY) note = "transform to fly first";
    else if (!kneesLevel()) note = "arms not on the stops";
    else if (thr > 0.06f) note = "throttle down to arm";
    else if (cells && vbat() / cells < 3.4f) note = "battery too low";
    else { armed = true; note = "ARMED"; }
    return;
  }
  if (!strcmp(c, "disarm")) { armed = false; note = "disarmed"; return; }
  if (!strcmp(c, "beeper")) { beeper = v > 0.5f; return; }
  if (!strcmp(c, "gait")) { Gait::setKind(!strcmp(a, "trot") ? Gait::TROT : Gait::CREEP); return; }
  if (!strcmp(c, "face")) { Face::Mood m; if (Face::fromName(a, m)) { Face::set(m); moodHoldUntil = millis() + 8000; } return; }
  if (!strcmp(c, "trick") && !armed && (mode == STAND || mode == SIT)) { trickName = a; trickUntil = millis() + 3500; setMode(TRICK); return; }
  if (!strcmp(c, "trim")) {
    int leg; float h, k;
    if (sscanf(a, "%d,%f,%f", &leg, &h, &k) == 3 && leg >= 0 && leg < 4) Servos::setTrim(leg, h, k);
    return;
  }
  if (!strcmp(c, "trim_save")) { Servos::saveTrims(); note = "trims saved"; return; }
  // assembly helpers: hold every servo at its centre (hip 0, knee 45 = 1500 us), or let them all go limp
  const bool idle = !armed && (mode == SIT || mode == STAND || mode == TRICK || mode == SERVICE);
  if (!strcmp(c, "centre") && idle) {
    setMode(SERVICE); Servos::setRate(90);
    for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, 45);
    note = "servos centred"; return;
  }
  if (!strcmp(c, "relax") && idle) { setMode(SERVICE); Servos::relaxAll(); note = "servos relaxed"; return; }
}

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  pinMode(PIN_BUZZER, OUTPUT);
  analogReadResolution(12);
  Servos::begin();
  Face::begin();
  Crsf::begin(Serial1, PIN_CRSF_RX, PIN_CRSF_TX);
  Net::begin(onCmd);
  Servos::setRate(90);
  for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, SIT_KNEE);
  beep(60); delay(60); beep(60);
  Serial.printf("SkyCrawler up. WiFi: %s / %s\n", Net::ssid(), AP_PASS);
}

static void runMode(float dt) {
  const Net::Sticks &s = Net::sticks();
  const bool link = Net::connected();
  switch (mode) {
    case SIT:
      Servos::setRate(90);
      for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, SIT_KNEE);
      break;
    case STAND:
      Servos::setRate(link ? 300 : 120);
      if (link) Gait::update(dt, s.ly, -s.lx, s.ry);
      else Gait::stand(0);                       // lost the phone: stop and stand still
      break;
    case TRICK: {
      Servos::setRate(260);
      const float t = (millis() - stepT) / 1000.0f;
      if (trickName == "wave") {
        for (int i = 1; i < 4; i++) Servos::setLeg(i, 0, STAND_KNEE + (i == 2 ? 6 : 0));
        Servos::setLeg(0, 25 * sinf(t * 9), 5);
      } else if (trickName == "dance") {
        for (int i = 0; i < 4; i++) Servos::setLeg(i, 12 * sinf(t * 6 + i), STAND_KNEE - 14 * sinf(t * 12 + (i % 2) * PI));
      } else {   // "bow"
        for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, i < 2 ? STAND_KNEE + 18 : STAND_KNEE - 10);
      }
      if (millis() > trickUntil) setMode(STAND);
      break;
    }
    case TO_FLY:
      // 1) legs to the diagonals and the belly down, 2) arms up onto the end stops, 3) let the knees go
      Servos::relaxKnees(false);
      if (step == 0) { Servos::setRate(90); for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, SIT_KNEE); if (Servos::atTarget()) { step = 1; stepT = millis(); } }
      else if (step == 1) { Servos::setRate(45); for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, KNEE_MIN); if (Servos::atTarget() && millis() - stepT > 600) { step = 2; stepT = millis(); } }
      else if (millis() - stepT > 400) { Servos::relaxKnees(true); setMode(FLY); beep(150); }
      break;
    case FLY:
      // hips hold the X; knees are off — thrust (and the magnets) keep the arms on the stops
      Servos::setRate(60);
      for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, KNEE_MIN);
      break;
    case SERVICE:                                // assembly / calibration: hold whatever was set
      break;
    case TO_WALK:
      armed = false;
      Servos::relaxKnees(false);
      Servos::setRate(40);                       // lift the body slowly
      for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, STAND_KNEE);
      if (Servos::atTarget()) setMode(STAND);
      break;
  }
}

static void sendCrsf() {
  static uint32_t last = 0;
  if (millis() - last < CRSF_PERIOD_MS) return;
  last = millis();
  const Net::Sticks &s = Net::sticks();
  const bool link = Net::connected();
  if (armed && !link) return;   // lost the app while flying: go silent -> Betaflight failsafe lands it
  uint16_t ch[16];
  for (int i = 0; i < 16; i++) ch[i] = 1500;
  const bool fly = mode == FLY && link;
  ch[0] = 1500 + (int)((fly ? s.rx : 0) * 500);           // roll
  ch[1] = 1500 + (int)((fly ? s.ry : 0) * 500);           // pitch
  ch[2] = 1000 + (int)((fly ? (s.ly + 1) / 2 : 0) * 1000); // throttle
  ch[3] = 1500 + (int)((fly ? s.lx : 0) * 500);           // yaw
  ch[4] = armed && mode == FLY ? 2000 : 1000;              // AUX1 = ARM
  ch[5] = 2000;                                            // AUX2 = ANGLE (self-level) always on
  ch[6] = beeper ? 2000 : 1000;                            // AUX3 = BEEPER
  Crsf::send(ch);
}

static void updateFace() {
  static uint32_t last = 0;
  if (millis() - last < 50) return;
  last = millis();
  if (millis() > moodHoldUntil) {
    Face::Mood m = Face::HAPPY;
    if (!Net::connected() && mode != SIT) m = Face::SURPRISED;
    else if (mode == SIT) m = Face::SLEEPY;
    else if (mode == TO_FLY || mode == TO_WALK) m = Face::SURPRISED;
    else if (mode == FLY) m = armed ? Face::ANGRY : Face::FOCUS;
    else if (mode == TRICK) m = trickName == "wave" ? Face::WINK : Face::LOVE;
    if (cells && vbat() / cells < 3.5f) m = Face::SAD;
    Face::set(m);
  }
  char line[22];
  if (vbat() > 1) snprintf(line, sizeof line, "%s %.1fV", armed ? "ARMED" : MODE_NAMES[mode], vbat());
  else snprintf(line, sizeof line, "%s", armed ? "ARMED" : MODE_NAMES[mode]);
  Face::status(line);
  Face::update();
}

static void telemetry() {
  static uint32_t last = 0;
  if (millis() - last < 200) return;
  last = millis();
  char js[256];
  snprintf(js, sizeof js,
           "{\"t\":\"tel\",\"mode\":\"%s\",\"armed\":%s,\"vbat\":%.2f,\"cells\":%d,\"fc\":%s,\"face\":\"%s\",\"gait\":\"%s\",\"pitch\":%.1f,\"roll\":%.1f,\"note\":\"%s\"}",
           MODE_NAMES[mode], armed ? "true" : "false", vbat(), cells, Crsf::fcAlive() ? "true" : "false",
           Face::name(Face::get()), Gait::kind() == Gait::TROT ? "trot" : "creep", Crsf::pitchDeg(), Crsf::rollDeg(), note.c_str());
  Net::sendText(js);
  note = "";
}

void loop() {
  static uint32_t lastUs = micros();
  const uint32_t now = micros();
  const float dt = (now - lastUs) / 1e6f;
  if (dt < 0.004f) { Net::loop(); Crsf::poll(); return; }   // ~250 Hz
  lastUs = now;
  Net::loop();
  Crsf::poll();
  // battery: FC telemetry if wired, else the divider on PIN_VBAT
  vbatAdc = vbatAdc * 0.95f + 0.05f * (analogReadMilliVolts(PIN_VBAT) / 1000.0f * VBAT_SCALE);
  if (!cells && vbat() > 5) cells = (int)ceilf(vbat() / 4.35f);
  runMode(dt);
  Servos::update(dt);
  sendCrsf();
  updateFace();
  telemetry();
}
