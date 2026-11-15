"""Pitch-axis simulation of a TVC rocket, for tuning gains before flight.

It models one axis (pitch) as a rigid body pushed by a gimballed motor.
The model includes the things that wreck real flights: sensor noise and
gyro bias, loop delay, a servo that can only move so fast, the gimbal
limit, and thrust that changes over the burn.

Run:
    pip install numpy matplotlib
    python tvc_sim.py                 # one flight with the gains below
    python tvc_sim.py --sweep         # try a grid of gains, print the best

Change ROCKET and GAINS to match your build. Weigh the finished rocket
and measure the distance from the gimbal pivot to the centre of gravity.
"""
import argparse
import math

import numpy as np

ROCKET = dict(
    mass=0.55,            # kg, loaded, with motor
    length=0.60,          # m, used for a rough moment of inertia
    arm=0.28,             # m, gimbal pivot to centre of gravity
    gimbal_limit=5.0,     # deg, matches MAX_GIMBAL_DEG in the firmware
    servo_rate=600.0,     # deg/s at the motor (MG90S geared down by the linkage)
    servo_tau=0.03,       # s, servo + linkage lag (slop, horn flex, PWM frame)
    loop_hz=200.0,
    delay_steps=2,        # loop cycles between reading the IMU and moving the servo
    gyro_noise=0.05,      # deg/s, standard deviation
    gyro_bias=0.3,        # deg/s left over after calibration
    mount_offset=0.3,     # deg, motor mounted slightly crooked
)

# Simple thrust curve: (time s, thrust N). Replace with your motor's data
# sheet. This shape (spike, then a flat sustain) is typical of small motors.
THRUST = [(0.0, 0.0), (0.05, 25.0), (0.25, 20.0), (0.4, 14.0),
          (2.2, 13.0), (2.4, 0.0)]

GAINS = dict(kp=1.2, kd=0.18, ki=0.05)  # from --sweep, backed off a little

START_TILT = 5.0    # deg, initial lean
START_RATE = 10.0   # deg/s, initial tip-over rate (a gust off the pad)


def thrust(t):
    ts, fs = zip(*THRUST)
    return float(np.interp(t, ts, fs, right=0.0))


def simulate(kp, kd, ki, r=ROCKET, seed=1, record=False):
    rng = np.random.default_rng(seed)
    dt = 1.0 / r["loop_hz"]
    inertia = r["mass"] * r["length"] ** 2 / 12.0
    theta = math.radians(START_TILT)
    omega = math.radians(START_RATE)
    delta = 0.0               # actual motor angle, rad
    integ = 0.0
    est_theta = theta         # the firmware only knows what it integrates
    queue = [0.0] * (r["delay_steps"] + 1)
    lim = math.radians(r["gimbal_limit"])
    rate = math.radians(r["servo_rate"])
    lagged = 0.0
    offset = math.radians(r["mount_offset"])
    bias = math.radians(r["gyro_bias"])
    t_end = THRUST[-1][0]
    log = [] if record else None
    worst = 0.0
    sq, n = 0.0, 0

    t = 0.0
    while t < t_end:
        # sensor: gyro rate with bias and noise, integrated like the firmware
        gyro = omega + bias + math.radians(rng.normal(0, r["gyro_noise"]))
        est_theta += gyro * dt

        # controller (same rule as the firmware): delta = Kp*tilt + Kd*rate + I
        # positive delta makes a negative torque, so it pushes the tilt back
        integ = max(-lim, min(lim, integ + ki * est_theta * dt))   # anti-windup
        cmd = kp * est_theta + kd * gyro + integ
        cmd = max(-lim, min(lim, cmd))
        queue.append(cmd)
        target = queue.pop(0)

        # servo: first-order lag, then rate limited
        lagged += (target - lagged) * min(1.0, dt / r["servo_tau"])
        step = max(-rate * dt, min(rate * dt, lagged - delta))
        delta += step

        # physics: thrust tilted by delta (+ mount error) makes a torque
        f = thrust(t)
        torque = -f * math.sin(delta + offset) * r["arm"]
        omega += torque / inertia * dt
        theta += omega * dt

        worst = max(worst, abs(theta))
        sq += theta * theta
        n += 1
        if record:
            log.append((t, math.degrees(theta), math.degrees(est_theta),
                        math.degrees(delta), f))
        t += dt
    rms = math.degrees(math.sqrt(sq / max(n, 1)))
    return math.degrees(worst), math.degrees(theta), rms, log


def sweep():
    results = []
    for kp in np.arange(0.2, 3.01, 0.2):
        for kd in np.arange(0.02, 0.31, 0.02):
            runs = [simulate(kp, kd, GAINS["ki"], seed=s) for s in range(5)]
            rms = max(r[2] for r in runs)
            worst = max(r[0] for r in runs)
            results.append((rms, worst, kp, kd))
    results.sort()
    print("best gains (RMS tilt over the burn, worst of 5 noisy runs):")
    for rms, worst, kp, kd in results[:8]:
        print(f"  kp={kp:.2f}  kd={kd:.2f}  RMS {rms:.2f} deg  peak {worst:.2f} deg")


def plot(log, path="tvc_sim.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    a = np.array(log)
    fig, ax = plt.subplots(3, 1, figsize=(8, 7), sharex=True)
    ax[0].plot(a[:, 0], a[:, 1], label="true tilt")
    ax[0].plot(a[:, 0], a[:, 2], "--", label="what the IMU thinks")
    ax[0].set_ylabel("tilt (deg)")
    ax[0].legend()
    ax[1].plot(a[:, 0], a[:, 3])
    ax[1].set_ylabel("motor angle (deg)")
    ax[2].plot(a[:, 0], a[:, 4])
    ax[2].set_ylabel("thrust (N)")
    ax[2].set_xlabel("time (s)")
    for x in ax:
        x.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    print("saved", path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()
    if args.sweep:
        sweep()
    else:
        worst, final, rms, log = simulate(**GAINS, record=True)
        print(f"peak tilt {worst:.2f} deg, RMS {rms:.2f} deg, "
              f"tilt at burnout {final:.2f} deg")
        plot(log)
