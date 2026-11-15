# Assembly

## Printing

Print all four parts in PETG or ASA. PLA softens in a hot car and too close to a motor case. Use 0.2 mm layers, 4 walls and 40% infill. The parts are oriented flat in the STL files, so no supports should be needed. The motor sleeve prints standing up, with the nozzle end down.

If your body tube or motor isn't the default size (65 mm inside diameter, 24 mm motor), change the numbers at the top of `cad/gimbal.py` and run it again:

```
pip install manifold3d trimesh numpy
python cad/gimbal.py
```

## Gimbal

1. Slide the motor sleeve into the inner ring. Line up the sleeve's two side bosses with the ring's X holes. From outside the ring, run an M3 × 8 bolt through each hole and into the boss. The bolt cuts its own thread in the plastic. Stop when the sleeve swings freely with no wobble.
2. Put the inner ring inside the outer mount and line up the Y holes. Run M3 × 10 bolts through the mount wall and into the ring bosses. The counterbores keep the bolt heads flush.
3. Both axes should now swing smoothly by hand. If anything rubs, sand it. Don't drill the holes bigger.

## Servos and pushrods

1. Push the two MG90S servos into the servo plate pockets and screw them in with their M2 screws. The pitch servo goes in the pocket on the +X side, and the yaw servo goes on the +Y side.
2. Glue the outer mount into the bottom of the body tube. Glue the servo plate about 65 mm above the top edge of the mount, so the servo bodies hanging under the plate clear the top of the swinging sleeve. Turn the plate so its pockets line up with the lugs: the pitch servo over the ring lug and the yaw servo over the sleeve lug.
3. Center both servos first (send `c` over serial), then fit the horns as close to straight across as you can.
4. Bend 1.5 mm steel wire into pushrods with a Z-bend at each end. One runs from the pitch horn to the ring lug and the other from the yaw horn to the sleeve lug. Adjust the length until the motor hangs straight with the servos centered. Then fine-tune with `PITCH_TRIM_US` and `YAW_TRIM_US` in `config.h`.

## Electronics

```
2S LiPo ── arming switch ── 5 V 3 A BEC ──┬── servo +5 V (both)  + 470 µF cap
                                         └── ESP32 5V / VIN
ESP32 GND ── BEC GND ── servo GND ── MPU6050 GND
ESP32 3V3 ── MPU6050 VCC
GPIO21 ── MPU6050 SDA      GPIO22 ── MPU6050 SCL
GPIO25 ── pitch servo signal
GPIO26 ── yaw servo signal
GPIO27 ── arm switch to GND (second pole, or a separate switch)
GPIO2  ── status LED       GPIO4 ── buzzer
```

Mount the MPU6050 firmly with screws, not tape, near the middle of the rocket. Its Z axis points to the nose and its X and Y axes line up with the gimbal axes. If your board sits differently, remap the axes in `config.h`.

## Motor

Push the motor into the sleeve until it seats on the forward lip. Then wrap tape around the joint at the nozzle end or add a clip so the ejection charge can't push the motor out the back. Choose a motor with a delay that fires the ejection near the top of the flight.
