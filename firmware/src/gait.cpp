#include "gait.h"
#include "config.h"
#include "servos.h"

namespace Gait {
static Kind k = CREEP;
static float phase = 0;
// leg order FR, FL, BL, BR
static const float OFF_CREEP[4] = {0.0f, 0.5f, 0.25f, 0.75f};
static const float OFF_TROT[4] = {0.0f, 0.5f, 0.0f, 0.5f};
static const bool RIGHT[4] = {true, false, false, true};

void setKind(Kind kk) { k = kk; }
Kind kind() { return k; }

void stand(float height) {
  for (int i = 0; i < 4; i++) Servos::setLeg(i, 0, STAND_KNEE - height * 14.0f);
}

void update(float dt, float fwd, float turn, float height) {
  const float mag = fminf(1.0f, fabsf(fwd) + fabsf(turn));
  if (mag < 0.06f) { stand(height); phase = 0; return; }
  const float duty = k == CREEP ? 0.75f : 0.5f;
  phase += dt * GAIT_HZ * (0.35f + 0.65f * mag) * (k == TROT ? 1.3f : 1.0f);
  if (phase >= 1) phase -= 1;
  for (int i = 0; i < 4; i++) {
    // how far this leg's stance sweeps: forward walking moves every foot backwards;
    // turning left moves the right feet backwards and the left feet forwards
    float c = fwd + turn * (RIGHT[i] ? 1.0f : -1.0f);
    c = constrain(c, -1.0f, 1.0f);
    float p = phase + (k == CREEP ? OFF_CREEP[i] : OFF_TROT[i]);
    p -= floorf(p);
    float hip, lift;
    if (p < duty) {                    // stance: +A .. -A, foot on the ground
      float s = p / duty;
      hip = STEP_HIP * c * (1 - 2 * s);
      lift = 0;
    } else {                           // swing: -A .. +A, foot lifted
      float s = (p - duty) / (1 - duty);
      hip = STEP_HIP * c * (-1 + 2 * s);
      lift = sinf(s * PI) * STEP_LIFT;
    }
    Servos::setLeg(i, hip, STAND_KNEE - height * 14.0f - lift);
  }
}
}  // namespace Gait
