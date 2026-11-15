// Settings for tvc_flight.ino. Everything you need to change for your own
// build is in this file.
#pragma once

// ---------- Pins (ESP32 dev board) ----------
#define PIN_SDA          21
#define PIN_SCL          22
#define PIN_SERVO_PITCH  25   // servo that tilts the inner ring (about body Y)
#define PIN_SERVO_YAW    26   // servo that tilts the motor sleeve (about body X)
#define PIN_ARM_SWITCH   27   // switch to GND. Closed = armed.
#define PIN_LED          2
#define PIN_BUZZER       4

// ---------- Control loop ----------
#define LOOP_HZ          200
#define KP               1.2f   // from sim/tvc_sim.py --sweep, backed off a little
#define KD               0.18f
#define KI               0.05f
#define MAX_GIMBAL_DEG   5.0f   // the printed gimbal clears 8 deg; keep margin
#define ABORT_TILT_DEG   30.0f  // past this, stop steering and centre the motor

// ---------- Servos ----------
// Microseconds of servo pulse per degree of MOTOR swing. Depends on your horn
// length and where the pushrod meets the lug. Measure it: command +5 deg in
// bench mode and check the motor angle with a phone inclinometer app.
#define SERVO_US_PER_DEG 40.0f
#define PITCH_TRIM_US    0      // adjust so the motor hangs straight at centre
#define YAW_TRIM_US      0
// Flip these if the bench test shows a servo correcting the wrong way.
#define PITCH_SIGN       (+1)
#define YAW_SIGN         (+1)

// ---------- IMU mounting ----------
// The firmware wants: Z along the rocket toward the nose, X and Y across it,
// lined up with the two gimbal axes. If your board is mounted differently,
// remap here (for example, swap X and Y or flip a sign).
#define IMU_X(ax, ay, az)  (ax)
#define IMU_Y(ax, ay, az)  (ay)
#define IMU_Z(ax, ay, az)  (az)

// ---------- Flight events ----------
#define LAUNCH_G         2.5f   // axial acceleration that counts as liftoff
#define LAUNCH_MS        20     // ...held this long
#define BURNOUT_G        0.5f   // axial acceleration below this = motor done
#define BURNOUT_MS       100
#define MAX_BURN_MS      4000   // stop steering after this no matter what
#define CAL_MS           2000   // gyro calibration time after arming
#define LOG_SECONDS      10
