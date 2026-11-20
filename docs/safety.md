# Safety checklist

2.5" props on 3S cut skin. LiPos catch fire. Read this before every flying session.

## Before every flight

- [ ] Props on the right motors (CW and CCW) and tight. No chips or cracks.
- [ ] All 4 arms sitting **on their stops**, with the magnets touching. Check this by eye: the robot can't sense the arms, it only knows it commanded them there.
- [ ] The app shows `FLY` (the knee servos are switched off in this mode).
- [ ] Battery strap tight, battery voltage above 3.7 V per cell.
- [ ] Failsafe tested this session: arm with **props off**, then turn the phone's WiFi off. The motors should drop to failsafe throttle and stop after about 3 s.
- [ ] Open space, nobody within 5 m, not over people or roads, local drone rules followed.

## Never

- Arm with props on while you're holding the robot.
- Calibrate, trim or test walking with props on.
- Fly from a phone that is also downloading something big. The control link shares that WiFi.
- Leave a LiPo charging unattended. Store and charge LiPos in a LiPo bag.

## Limits of this design

- The WiFi control link has short range: about 30–60 m line of sight. The robot is a **close-range toy**, not an FPV quad.
- Failsafe auto-land is a fixed-throttle descent, not a GPS or barometer landing. From high up it can still land hard.
- The arms are held in flight by thrust plus a magnet. A hard yaw or flip manoeuvre at low throttle can unload an arm. Fly gently in angle mode, which the robot always forces on.
