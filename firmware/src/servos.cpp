#include "servos.h"
#include "config.h"
#include <ESP32Servo.h>
#include <Preferences.h>

namespace Servos {
static Servo hipS[4], kneeS[4];
static float hipCur[4], kneeCur[4], hipTgt[4], kneeTgt[4];
static float hipTrim[4], kneeTrim[4];
static float rate = 180.0f;
static bool kneesRelaxed = false, allRelaxed = true;
static Preferences prefs;

static int toUs(float deg) { return (int)(SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * constrain(deg, 0.0f, 180.0f) / 180.0f); }
// robot angle -> raw servo angle (90 = centre)
static float rawHip(int i, float a) { float v = a + hipTrim[i]; return 90.0f + (HIP_REV[i] ? -v : v); }
static float rawKnee(int i, float a) { float v = a + kneeTrim[i]; return 90.0f + (KNEE_REV[i] ? -(v - 45.0f) : (v - 45.0f)); }   // 45° robot = servo centre

static void attach() {
  for (int i = 0; i < 4; i++) {
    if (!hipS[i].attached()) hipS[i].attach(PIN_HIP[i], SERVO_MIN_US, SERVO_MAX_US);
    if (!kneesRelaxed && !kneeS[i].attached()) kneeS[i].attach(PIN_KNEE[i], SERVO_MIN_US, SERVO_MAX_US);
  }
  allRelaxed = false;
}

void begin() {
  ESP32PWM::allocateTimer(0); ESP32PWM::allocateTimer(1); ESP32PWM::allocateTimer(2); ESP32PWM::allocateTimer(3);
  prefs.begin("trims", false);
  for (int i = 0; i < 4; i++) {
    hipTrim[i] = prefs.getFloat(("h" + String(i)).c_str(), HIP_TRIM_DEFAULT[i]);
    kneeTrim[i] = prefs.getFloat(("k" + String(i)).c_str(), KNEE_TRIM_DEFAULT[i]);
    hipS[i].setPeriodHertz(50); kneeS[i].setPeriodHertz(50);
    // start where a robot usually sits at power-on: on its belly, legs folded under
    hipCur[i] = hipTgt[i] = 0; kneeCur[i] = kneeTgt[i] = SIT_KNEE;
  }
}

void setLeg(int i, float h, float k) {
  hipTgt[i] = constrain(h, -HIP_LIMIT, HIP_LIMIT);
  kneeTgt[i] = constrain(k, KNEE_MIN, KNEE_MAX);
}
void setRate(float r) { rate = r; }

void update(float dt) {
  if (allRelaxed) attach();
  const float step = rate * dt;
  for (int i = 0; i < 4; i++) {
    hipCur[i] += constrain(hipTgt[i] - hipCur[i], -step, step);
    kneeCur[i] += constrain(kneeTgt[i] - kneeCur[i], -step, step);
    hipS[i].writeMicroseconds(toUs(rawHip(i, hipCur[i])));
    if (!kneesRelaxed) kneeS[i].writeMicroseconds(toUs(rawKnee(i, kneeCur[i])));
  }
}

void relaxKnees(bool r) {
  if (r == kneesRelaxed) return;
  kneesRelaxed = r;
  for (int i = 0; i < 4; i++) {
    if (r) kneeS[i].detach();
    else { kneeS[i].attach(PIN_KNEE[i], SERVO_MIN_US, SERVO_MAX_US); }
  }
}

void relaxAll() {
  for (int i = 0; i < 4; i++) { hipS[i].detach(); kneeS[i].detach(); }
  allRelaxed = true; kneesRelaxed = false;
}

bool atTarget(float tol) {
  for (int i = 0; i < 4; i++) if (fabsf(hipCur[i] - hipTgt[i]) > tol || fabsf(kneeCur[i] - kneeTgt[i]) > tol) return false;
  return true;
}
float hip(int i) { return hipCur[i]; }
float knee(int i) { return kneeCur[i]; }

void setTrim(int i, float h, float k) { hipTrim[i] = constrain(h, -30.0f, 30.0f); kneeTrim[i] = constrain(k, -30.0f, 30.0f); }
void getTrim(int i, float &h, float &k) { h = hipTrim[i]; k = kneeTrim[i]; }
void saveTrims() {
  for (int i = 0; i < 4; i++) { prefs.putFloat(("h" + String(i)).c_str(), hipTrim[i]); prefs.putFloat(("k" + String(i)).c_str(), kneeTrim[i]); }
}
}  // namespace Servos
