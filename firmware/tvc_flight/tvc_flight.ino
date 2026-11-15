// TVC flight computer for an ESP32 + MPU6050 + two micro servos.
//
// The flight computer never lights the motor. You launch with a normal
// model rocket launch controller; this code notices liftoff from the
// accelerometer and steers until burnout.
//
// Serial commands at 115200 baud (only while DISARMED):
//   b  bench mode: steer live with no motor, to check servo directions
//   s  sweep both servos to the gimbal limits and back
//   c  centre the servos
//   d  dump the last flight log as CSV
//
// Needs the ESP32Servo library (Library Manager: "ESP32Servo").

#include <Wire.h>
#include <ESP32Servo.h>
#include "config.h"
#include "types.h"

// ---------------------------------------------------------------- IMU ----
static const uint8_t MPU = 0x68;
static const float GYRO_LSB = 65.5f;     // +-500 deg/s
static const float ACC_LSB  = 2048.0f;   // +-16 g, so the motor kick can't clip


static void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU); Wire.write(reg); Wire.write(val); Wire.endTransmission();
}

static bool mpuInit() {
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(400000);
  mpuWrite(0x6B, 0x01);   // wake, PLL clock from gyro X
  delay(50);
  mpuWrite(0x1A, 0x03);   // DLPF ~42 Hz
  mpuWrite(0x19, 0x04);   // 200 Hz sample rate
  mpuWrite(0x1B, 0x08);   // gyro +-500 deg/s
  mpuWrite(0x1C, 0x18);   // accel +-16 g
  Wire.beginTransmission(MPU); Wire.write(0x75); Wire.endTransmission(false);
  Wire.requestFrom(MPU, (uint8_t)1);
  return Wire.available() && Wire.read() == 0x68;
}

static bool mpuRead(Imu &o) {
  Wire.beginTransmission(MPU); Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(MPU, (uint8_t)14) != 14) return false;
  int16_t r[7];
  for (int i = 0; i < 7; i++) r[i] = (Wire.read() << 8) | Wire.read();
  float ax = r[0] / ACC_LSB, ay = r[1] / ACC_LSB, az = r[2] / ACC_LSB;
  float gx = r[4] / GYRO_LSB, gy = r[5] / GYRO_LSB, gz = r[6] / GYRO_LSB;
  const float D2R = PI / 180.0f;
  o.ax = IMU_X(ax, ay, az); o.ay = IMU_Y(ax, ay, az); o.az = IMU_Z(ax, ay, az);
  o.gx = IMU_X(gx, gy, gz) * D2R; o.gy = IMU_Y(gx, gy, gz) * D2R; o.gz = IMU_Z(gx, gy, gz) * D2R;
  return true;
}

// ---------------------------------------------------------- attitude ----
// Quaternion, body to world. Integrated from the gyro. On the pad the
// accelerometer only sees gravity, so it gently corrects drift. After
// liftoff it sees thrust too, so the firmware stops listening to it.
static float qw = 1, qx = 0, qy = 0, qz = 0;
static float biasX = 0, biasY = 0, biasZ = 0;

static void normalizeQ() {
  float n = sqrtf(qw * qw + qx * qx + qy * qy + qz * qz);
  qw /= n; qx /= n; qy /= n; qz /= n;
}

static void updateAttitude(float gx, float gy, float gz, const Imu *acc, float dt) {
  if (acc) {   // pad only: pull "up" toward the measured gravity direction
    float an = sqrtf(acc->ax * acc->ax + acc->ay * acc->ay + acc->az * acc->az);
    if (an > 0.9f && an < 1.1f) {
      float ux = 2 * (qx * qz - qw * qy), uy = 2 * (qy * qz + qw * qx),
            uz = 1 - 2 * (qx * qx + qy * qy);
      float mx = acc->ax / an, my = acc->ay / an, mz = acc->az / an;
      const float K = 2.0f;
      gx += K * (my * uz - mz * uy);
      gy += K * (mz * ux - mx * uz);
      gz += K * (mx * uy - my * ux);
    }
  }
  float hw = -qx * gx - qy * gy - qz * gz, hx = qw * gx + qy * gz - qz * gy,
        hy = qw * gy - qx * gz + qz * gx, hz = qw * gz + qx * gy - qy * gx;
  float h = 0.5f * dt;
  qw += hw * h; qx += hx * h; qy += hy * h; qz += hz * h;
  normalizeQ();
}

// Tilt of the rocket about its own X and Y axes, in radians.
static void tilts(float &tx, float &ty) {
  float ux = 2 * (qx * qz - qw * qy), uy = 2 * (qy * qz + qw * qx),
        uz = 1 - 2 * (qx * qx + qy * qy);   // world "up" seen from the rocket
  tx = atan2f(uy, uz);
  ty = atan2f(-ux, uz);
}

static void initFromAccel(const Imu &a) {
  float tx = atan2f(a.ay, a.az);
  float ty = atan2f(-a.ax, sqrtf(a.ay * a.ay + a.az * a.az));
  float cx = cosf(tx / 2), sx = sinf(tx / 2), cy = cosf(ty / 2), sy = sinf(ty / 2);
  qw = cx * cy; qx = sx * cy; qy = cx * sy; qz = -sx * sy;
  normalizeQ();
}

// ------------------------------------------------------------ servos ----
static Servo servoPitch, servoYaw;
static const float D2R = PI / 180.0f, R2D = 180.0f / PI;
static float cmdX = 0, cmdY = 0;   // motor angle commands, degrees

static void setGimbal(float dx, float dy) {
  dx = constrain(dx, -MAX_GIMBAL_DEG, MAX_GIMBAL_DEG);
  dy = constrain(dy, -MAX_GIMBAL_DEG, MAX_GIMBAL_DEG);
  cmdX = dx; cmdY = dy;
  servoYaw.writeMicroseconds(1500 + YAW_TRIM_US + (int)(YAW_SIGN * dx * SERVO_US_PER_DEG));
  servoPitch.writeMicroseconds(1500 + PITCH_TRIM_US + (int)(PITCH_SIGN * dy * SERVO_US_PER_DEG));
}

// --------------------------------------------------------- controller ----
static Pid pidX, pidY;


// Same rule as sim/tvc_sim.py: delta = Kp*tilt + Kd*rate + integral
static float steer(Pid &p, float tilt, float rate, float dt) {
  float lim = MAX_GIMBAL_DEG * D2R;
  p.i = constrain(p.i + KI * tilt * dt, -lim, lim);   // anti-windup
  return (KP * tilt + KD * rate + p.i) * R2D;
}

// ------------------------------------------------------------ logging ----
static const int LOG_N = LOG_SECONDS * LOOP_HZ;
static LogRow logBuf[LOG_N];
static int logLen = 0;
static uint32_t tLaunch = 0;

static void logRow(float tx, float ty, float rx, float ry, float az) {
  if (logLen >= LOG_N) return;
  LogRow &r = logBuf[logLen++];
  r.t = millis() - tLaunch;
  r.tx = tx * R2D * 100; r.ty = ty * R2D * 100;
  r.rx = rx * R2D * 10;  r.ry = ry * R2D * 10;
  r.dx = cmdX * 100;     r.dy = cmdY * 100;
  r.az = az * 100;
}

static void dumpLog() {
  Serial.println("t_ms,tilt_x_deg,tilt_y_deg,rate_x_dps,rate_y_dps,gimbal_x_deg,gimbal_y_deg,accel_z_g");
  for (int i = 0; i < logLen; i++) {
    LogRow &r = logBuf[i];
    Serial.printf("%lu,%.2f,%.2f,%.1f,%.1f,%.2f,%.2f,%.2f\n", (unsigned long)r.t,
                  r.tx / 100.0, r.ty / 100.0, r.rx / 10.0, r.ry / 10.0,
                  r.dx / 100.0, r.dy / 100.0, r.az / 100.0);
  }
}

// ------------------------------------------------------- state machine ----
static State state = DISARMED;
static const char *NAMES[] = {"DISARMED", "CALIBRATING", "ARMED", "POWERED", "COAST", "ABORTED", "BENCH"};

static void go(State s) {
  state = s;
  Serial.printf("[%lu ms] -> %s\n", millis(), NAMES[s]);
}

static void beep(int ms) { digitalWrite(PIN_BUZZER, HIGH); delay(ms); digitalWrite(PIN_BUZZER, LOW); }

static bool armed() { return digitalRead(PIN_ARM_SWITCH) == LOW; }

static float calSum[3], calSq[3];
static int calN = 0;
static uint32_t tState = 0, tAbove = 0, tBelow = 0;
static uint32_t overruns = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_ARM_SWITCH, INPUT_PULLUP);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  ESP32PWM::allocateTimer(0);
  servoPitch.setPeriodHertz(50);   // MG90S is an analog servo: 50 Hz frames
  servoYaw.setPeriodHertz(50);
  servoPitch.attach(PIN_SERVO_PITCH, 1000, 2000);
  servoYaw.attach(PIN_SERVO_YAW, 1000, 2000);
  setGimbal(0, 0);
  if (!mpuInit()) {
    Serial.println("MPU6050 not found. Check wiring.");
    while (true) { beep(100); delay(400); }
  }
  Serial.println("TVC flight computer ready. Arm switch open = DISARMED.");
  beep(80);
}

static void serialCommands() {
  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == 'd') dumpLog();
  if (c == 'c') setGimbal(0, 0);
  if (c == 'b') { initFromAccel(Imu{0, 0, 0, 0, 0, 1}); pidX = Pid(); pidY = Pid(); go(BENCH); }
  if (c == 's') {
    float seq[][2] = {{1, 0}, {-1, 0}, {0, 0}, {0, 1}, {0, -1}, {0, 0}};
    for (auto &p : seq) { setGimbal(p[0] * MAX_GIMBAL_DEG, p[1] * MAX_GIMBAL_DEG); delay(500); }
  }
}

void loop() {
  static uint32_t next = micros();
  const uint32_t period = 1000000UL / LOOP_HZ;
  const float dt = 1.0f / LOOP_HZ;
  while ((int32_t)(micros() - next) < 0) {}
  next += period;
  if ((int32_t)(micros() - next) > (int32_t)period) { overruns++; next = micros() + period; }

  Imu m;
  if (!mpuRead(m)) return;
  float gx = m.gx - biasX, gy = m.gy - biasY, gz = m.gz - biasZ;
  uint32_t now = millis();

  // Disarming always wins, except in flight where it can't help.
  if (!armed() && state != DISARMED && state != BENCH && state != POWERED && state != COAST) {
    setGimbal(0, 0);
    go(DISARMED);
  }

  switch (state) {
    case DISARMED:
      digitalWrite(PIN_LED, (now / 1000) % 2);
      serialCommands();
      if (armed()) {
        calN = 0;
        for (int i = 0; i < 3; i++) { calSum[i] = 0; calSq[i] = 0; }
        tState = now;
        go(CALIBRATING);
      }
      break;

    case CALIBRATING: {   // rocket must sit still on the pad
      float g[3] = {m.gx, m.gy, m.gz};
      for (int i = 0; i < 3; i++) { calSum[i] += g[i]; calSq[i] += g[i] * g[i]; }
      calN++;
      if (now - tState >= CAL_MS) {
        float worstVar = 0;
        for (int i = 0; i < 3; i++) {
          float mean = calSum[i] / calN;
          worstVar = max(worstVar, calSq[i] / calN - mean * mean);
        }
        if (worstVar > sq(0.5f * D2R)) {   // it moved: start over
          Serial.println("Moved during calibration. Hold still.");
          beep(400);
          calN = 0;
          for (int i = 0; i < 3; i++) { calSum[i] = 0; calSq[i] = 0; }
          tState = now;
          break;
        }
        biasX = calSum[0] / calN; biasY = calSum[1] / calN; biasZ = calSum[2] / calN;
        initFromAccel(m);
        pidX = Pid(); pidY = Pid();
        logLen = 0;
        tAbove = 0;
        beep(60); delay(80); beep(60);
        go(ARMED);
      }
      break;
    }

    case ARMED: {
      digitalWrite(PIN_LED, HIGH);
      updateAttitude(gx, gy, gz, &m, dt);   // accel is trustworthy on the pad
      setGimbal(0, 0);
      if (m.az > LAUNCH_G) {
        if (!tAbove) tAbove = now;
        if (now - tAbove >= LAUNCH_MS) { tLaunch = now - LAUNCH_MS; tBelow = 0; go(POWERED); }
      } else {
        tAbove = 0;
      }
      break;
    }

    case POWERED: {
      updateAttitude(gx, gy, gz, nullptr, dt);   // gyro only from here
      float tx, ty;
      tilts(tx, ty);
      if (fabsf(tx) > ABORT_TILT_DEG * D2R || fabsf(ty) > ABORT_TILT_DEG * D2R) {
        setGimbal(0, 0);
        logRow(tx, ty, gx, gy, m.az);
        go(ABORTED);
        break;
      }
      setGimbal(steer(pidX, tx, gx, dt), steer(pidY, ty, gy, dt));
      logRow(tx, ty, gx, gy, m.az);
      if (m.az < BURNOUT_G) {
        if (!tBelow) tBelow = now;
        if (now - tBelow >= BURNOUT_MS) { setGimbal(0, 0); go(COAST); }
      } else {
        tBelow = 0;
      }
      if (now - tLaunch > MAX_BURN_MS) { setGimbal(0, 0); go(COAST); }
      break;
    }

    case COAST:     // parachute comes from the motor's ejection charge
    case ABORTED: {
      updateAttitude(gx, gy, gz, nullptr, dt);
      float tx, ty;
      tilts(tx, ty);
      logRow(tx, ty, gx, gy, m.az);
      setGimbal(0, 0);
      if (logLen >= LOG_N) {   // log full: wait on the ground, beep to be found
        beep(50); delay(950);
        if (!armed()) go(DISARMED);
      }
      break;
    }

    case BENCH: {   // no motor! tilt the rocket by hand and watch the nozzle
      updateAttitude(gx, gy, gz, &m, dt);
      float tx, ty;
      tilts(tx, ty);
      setGimbal(steer(pidX, tx, gx, dt), steer(pidY, ty, gy, dt));
      static int k = 0;
      if (++k % 20 == 0)
        Serial.printf("tilt x %6.2f  y %6.2f   gimbal x %5.2f  y %5.2f   overruns %lu\n",
                      tx * R2D, ty * R2D, cmdX, cmdY, (unsigned long)overruns);
      if (Serial.available() && Serial.read() == 'q') { setGimbal(0, 0); go(DISARMED); }
      break;
    }
  }
}
