# Flight controller setup (Betaflight 4.4 / 4.5)

The ESP32 acts as the FC's **radio receiver** and speaks CRSF at 420 kbaud, so Betaflight sees it as an ordinary ExpressLRS/Crossfire receiver.

**Props off for everything on this page.**

## 1. Ports and receiver

1. Wire ESP32 **GPIO43 (TX) → FC RX pad** and **GPIO44 (RX) → FC TX pad** of a free UART. Connect GND to GND.
2. In the **Ports** tab, turn on **Serial RX** for that UART. Nothing else should use it.
3. In **Receiver**, set *Serial (via UART)* to **CRSF** and *Channel map* to **AETR1234**.
4. In **Configuration**, turn on **TELEMETRY**. This lets the FC send battery voltage and attitude back to the robot and the app.

## 2. CLI

Paste this into the CLI tab, then check the Modes tab:

```
# receiver
set serialrx_provider = CRSF
set serialrx_inverted = OFF
set serialrx_halfduplex = OFF
feature TELEMETRY

# modes: AUX1 = ARM, AUX2 = ANGLE (the robot always sends this on), AUX3 = BEEPER
aux 0 0 0 1700 2100 0 0
aux 1 1 1 1700 2100 0 0
aux 2 13 2 1700 2100 0 0

# motors
set motor_pwm_protocol = DSHOT300
set dshot_bidir = OFF

# failsafe: when the robot stops sending (app or WiFi lost while armed) it descends and disarms
set failsafe_delay = 5                 # 0.5 s of silence before stage 2
set failsafe_procedure = AUTO-LAND     # on Betaflight 4.4 and older this is called LAND
set failsafe_throttle = 1350           # a little BELOW hover; tune it (see below)
set failsafe_off_delay = 30            # 3 s of descent, then motors off

# battery (3S)
set vbat_min_cell_voltage = 330
set vbat_warning_cell_voltage = 350

save
```

> On Betaflight 4.5, `failsafe_procedure` accepts `AUTO-LAND`, `DROP` or `GPS-RESCUE`. On 4.4 the first option is called `LAND`. If one name is rejected, use the other.

Betaflight's "landing" is not clever. It holds `failsafe_throttle` in angle mode for `failsafe_off_delay`, then cuts the motors. Find your hover throttle in the Betaflight blackbox or by feel, set `failsafe_throttle` about 50 µs below it, and practise over grass.

## 3. Board orientation and motors

- **Front of the robot = the face side** (+Y in the CAD). Mount the FC with its arrow pointing at the face. If you have to rotate it, set *Board alignment* (`align_board_yaw`).
- Betaflight motor order, seen from above:

  | Motor | Position | Spins |
  |---|---|---|
  | 1 | rear-right | CW |
  | 2 | front-right | CCW |
  | 3 | rear-left | CCW |
  | 4 | front-left | CW |

  This is the "props in" layout. The legs are named the same way in the firmware: FR = leg 0, FL = 1, BL = 2, BR = 3.
- In the **Motors** tab (props off, battery on), spin each motor and check its position and direction. Use the *Motor direction / reorder* tool to fix any that are wrong.
- In the **Receiver** tab, with the app connected in fly mode, the sticks should move the bars in the right directions. ARM, ANGLE and BEEPER should switch on when you hold ARM or tap Beeper.

## 4. First hover

1. Calibrate the accelerometer with the robot in **fly pose on a level table**.
2. Starting PIDs: the defaults for a 2.5" quad are fine. If it oscillates, lower P on roll and pitch by 10–20 %.
3. Hover at knee height over grass. Expect it to be heavier and less agile than a normal 2.5" quad.
