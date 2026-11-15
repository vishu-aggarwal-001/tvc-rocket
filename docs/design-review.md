# Design review

Before finishing this design, I ran it through a three-round duel. One side defended it. The other side, a simulated adversarial critic, tried to break it. Every change listed here is already in the code and STL files.

## Claims at the start

| # | Claim | Evidence / logic | Weak spot |
|---|---|---|---|
| C1 | Three printed parts on M3 pivots make a gimbal that swings both ways | Standard ring-in-ring layout | Parts might rub at full swing |
| C2 | A complementary filter (gyro plus accelerometer) tracks tilt for the whole flight | Common in drones | Rockets accelerate hard |
| C3 | A PD controller with a small I term, tuned in the sim, keeps it upright | Inverted pendulum theory | Only as good as the sim |
| C4 | An arming switch and launch detection make it safe to handle | Flight computer never lights the motor | Wiring and sign mistakes |
| C5 | The rocket can land upright on its motor | Falcon 9 does it | Small solid motors |
| C6 | Average thrust of at least 3 × weight is enough | From the original guide | Heavy builds |

## Round 1

Critic: C2 is wrong, and it fails quietly. Under thrust, the accelerometer measures the motor's push, not gravity, so it always points along the rocket. A filter that trusts it slowly drags the tilt estimate back to "straight up" while the rocket is actually leaning. The controller goes blind right when it's needed. Euler angles also break once the rocket rolls. C5 can't happen either. A small solid motor can't throttle, stop or relight, so there's no landing burn.

Defense: Both points stand. The firmware now only uses the accelerometer on the pad, where it really does see gravity. From liftoff on it integrates the gyro into a quaternion, which handles roll. During calibration the firmware checks that the rocket held still and starts over if it moved. I checked the attitude math numerically. A 10°/s turn about each axis reads back as exactly 10°, and the startup tilt matches the accelerometer. C5 is dropped. The rocket comes down on a parachute from the motor's ejection charge. Propulsive landing needs a throttleable motor and belongs in a later project.

## Round 2

Critic: Look at the first gain sweep. It kept picking the highest Kp in the grid, which means the model had no reason to stop. A real servo lags, so with gains that high the rocket would wobble itself apart. The 200 Hz loop also oversells the actuation, since an MG90S is an analog servo that only takes a new position every 20 ms.

Defense: Fair. I added a 30 ms first-order servo lag and a two-cycle delay to the sim. Now the sweep finds a real best point around Kp 1.2 to 1.6 and Kd 0.16 to 0.22, and the defaults are set slightly below it at Kp 1.2, Kd 0.18. The 50 Hz frame limit is in the docs, along with a note that digital servos at a higher rate would help. One finding stays: leftover gyro bias leaves about 1° of tilt at burnout. The I term can't remove it because the error sits in the estimate itself, which is why calibration has to happen with the rocket perfectly still.

## Round 3

Critic: This design has several ways to fail that would hurt someone or wreck the rocket. If a servo sign is wrong, the controller drives the rocket over instead of righting it. If the servos stall and pull the 5 V rail down, the ESP32 resets mid-flight. If the ejection charge blows the motor out the back, the parachute never comes out. And the swept collision check shows the inner ring touching the mount at 10° of pitch.

Defense: Each one is now covered.
- Bench mode (`b` over serial) steers live with no motor in, so you can tilt the rocket by hand and see which way the nozzle moves before any flight. Each axis has its own sign switch in `config.h`.
- Steering stops and the motor centers if the tilt passes 30°.
- The wiring guide puts a 470 µF capacitor on the servo rail and keeps servo power on its own BEC.
- If the board resets, it comes back DISARMED with the servos centered. It can't re-arm on a moving rocket, because calibration rejects motion.
- The motor sleeve has a forward thrust lip with a 19 mm hole. The motor pushes against the lip during the burn, and the ejection gas still passes forward through the hole. The rear of the motor gets tape or a clip so the ejection can't push it out the back.
- The parts clear each other up to ±8° on both axes, and they only touch at 10° in one direction. Firmware caps the swing at 5°.

## Final ledger

| # | Claim | Status |
|---|---|---|
| C1 | The gimbal clears ±8° on both axes; firmware limits it to 5° | Revised (clearances fixed, sweep checked) |
| C2 | Accelerometer on the pad only; gyro quaternion in flight | Revised |
| C3 | PD + I with gains from a sim that includes servo lag and delay | Revised |
| C4 | Arm switch, motion-checked calibration, launch detection, 30° abort, bench test | Revised (more checks) |
| C5 | Propulsive landing | Dropped; parachute recovery |
| C6 | Average thrust at least 3 × weight, using the real weight of the finished rocket | Held, with a note to weigh first |
