// Types live here so the Arduino IDE's auto-generated prototypes can see them.
#pragma once
#include <stdint.h>

struct Imu { float gx, gy, gz, ax, ay, az; };  // rad/s and g, rocket frame
struct Pid { float i = 0; };
struct LogRow { uint32_t t; int16_t tx, ty, rx, ry, dx, dy, az; };
enum State { DISARMED, CALIBRATING, ARMED, POWERED, COAST, ABORTED, BENCH };
