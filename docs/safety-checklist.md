# Safety and flight checklist

Follow the NAR or Tripoli safety code (in the US) and your local rules. Use certified motors only, and never modify one. A finless TVC rocket has no passive stability, so for the first flights go to a club launch and talk to the range safety officer before you fly.

## On the bench (before the first flight)

- [ ] `s` sweep: both servos reach ±5° and come back to center without binding.
- [ ] Measure `SERVO_US_PER_DEG`: command +5° and check the motor angle with a phone inclinometer.
- [ ] Bench mode (`b`), no motor in: lean the nose to the right. The nozzle should swing **left**, so the exhaust pushes the tail right and the nose comes back. Check both axes in both directions. If one is backwards, flip its `PITCH_SIGN` or `YAW_SIGN`.
- [ ] Tilt the rocket past 30° in bench mode and confirm the numbers track smoothly.
- [ ] Run `python sim/tvc_sim.py` with your real mass, pivot-to-CG distance and motor thrust curve.
- [ ] Weigh the finished rocket with a motor in. The motor's average thrust should be at least 3 × that weight.

## At the pad

- [ ] Fresh, fully charged LiPo.
- [ ] Motor taped or clipped in, with the parachute and wadding packed.
- [ ] Rocket on the pad and upright, then close the arm switch and keep your hands off it until you hear the double beep (calibration done).
- [ ] A long beep means it moved during calibration. Wait for the next double beep.
- [ ] Solid LED means it's armed. Clear the pad and launch from the launch controller at the safe distance.

## After landing

- [ ] Open the arm switch.
- [ ] Plug in USB and send `d` to dump the flight log as CSV.
