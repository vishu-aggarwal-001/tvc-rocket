#pragma once
// The OLED face. Expressions change with what the robot is doing; it blinks on its own.
namespace Face {
enum Mood { HAPPY, SLEEPY, FOCUS, ANGRY, SURPRISED, SAD, LOVE, WINK };
void begin();
void set(Mood m);
Mood get();
const char *name(Mood m);
bool fromName(const char *s, Mood &out);
void update();            // ~20 Hz
void status(const char *line);   // tiny text line under the eyes (mode / battery)
}
