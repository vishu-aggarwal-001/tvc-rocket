#pragma once
#include <Arduino.h>

// Eight leg servos with trims, limits, smooth motion and "relax" (PWM off).
namespace Servos {
void begin();
// target angles in the robot's convention (see config.h). Motion is rate-limited.
void setLeg(int leg, float hipDeg, float kneeDeg);
void setRate(float degPerSec);              // max joint speed
void update(float dt);                      // call every loop
void relaxKnees(bool relax);                // knees off (drone mode: thrust holds the arms on the stops)
void relaxAll();                            // everything off (power saving / safe)
bool atTarget(float tolDeg = 1.5f);
float hip(int leg);
float knee(int leg);
// calibration (saved to flash)
void setTrim(int leg, float hipTrim, float kneeTrim);
void getTrim(int leg, float &hipTrim, float &kneeTrim);
void saveTrims();
}
