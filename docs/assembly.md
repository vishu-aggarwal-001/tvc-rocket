# Assembly

You'll need the parts from the README BOM, a small Phillips driver, 1.5 and 2 mm hex keys, a soldering iron, CA glue and zip ties.

**Leg names** (seen from above, face at the front):

| Leg | Number |
|---|---|
| FR | 0 |
| FL | 1 |
| BL | 2 |
| BR | 3 |

## 0. Centre every servo first

1. Flash the firmware and power the ESP32 from the UBEC with **all servos plugged in and no horns fitted**.
2. Connect the app and tap **⚙ → Centre all servos**. Every servo goes to its middle position, 1500 µs, and stays there.
   - Without the app: join the robot's WiFi and open `http://192.168.4.1/`, then tap *Centre all servos*.
3. Leave it powered while you fit the horns. **Sit** or **Stand** leaves this service mode.

The firmware maps its angles so that:

- **hip 0° = servo centre**
- **knee 45° = servo centre**, halfway between drone (0°) and standing (90°)

This way both ends of the knee's travel stay well inside the servo's range.

## 1. Hips

1. Push the 4 hip servos down into the slots in `chassis_bottom`, with the shafts pointing up. Use the 2 M2 screws that came with each servo.
2. Snap a cross horn onto each hip shaft. Don't screw it yet.

## 2. Upper legs (coxa)

1. With the servo at centre, press the `coxa` root onto the horn so that the leg points **straight out along the diagonal**.
2. Screw the horn arms through the two Ø1.8 holes with M2×6 screws, then add the centre horn screw.
3. Put the `chassis_deck` on top. Each coxa's Ø6 pin goes up through a bushing in the deck.
4. Screw the deck onto the 4 pillars with M3×6 screws.

The pin must turn freely. If it binds, ream the bushing with a 6.5 mm drill by hand.

## 3. Knee servos

1. Slide each knee servo through the frame at the end of the coxa so that the shaft points **outward**, away from the body. Screw it in with M2.
2. Fit a cross horn and centre it.
3. Press the `shin_arm` root onto the horn with the shin at **45° down**, which is the knee's centre position. Screw it on.

If the horn sits below flush, add a `leg_spacer`.

## 4. End stops, magnets and levelling

1. Glue a 6×3 magnet into the ledge pocket on each coxa and another into the matching pocket under each shin tail. **Check the polarity so they attract.**
2. Run an M3 screw up through the ledge. This is the levelling screw.
3. Later, in drone pose, turn it until the arm is exactly level.

## 5. Motors and feet

1. Bolt each motor onto the pad with M2 screws from below. Both 9×9 and 12×12 patterns are drilled.
2. Run the motor wires along the shin's lower edge and through the wire channel, leaving slack around the knee. Use a zip tie at the coxa.
3. Push a TPU `foot_tpu` boot onto each toe.

## 6. Electronics

1. Mount the FC on the 20×20 standoffs in the deck with M2 screws and soft grommets, **arrow towards the face**.
2. Zip-tie the ESP32-S3 into the deck slots.
3. Mount the UBEC under the deck.
4. Glue the OLED behind the window in `head_shell`.
5. Wire everything according to the table in the README.
6. Put a 3-pin header strip on a small perfboard as a **servo power bus**:
   - all servo V+ to UBEC 5 V
   - all servo GND to UBEC GND, which is joined to the FC and ESP32 grounds
   - signals to the ESP32 pins
7. Strap the battery under the belly through the slots in `chassis_bottom`.
8. Clip the head shell on.

## 7. Calibrate (props off)

1. Connect the app and press **Stand**.
2. Open **⚙**. Nudge each hip until every leg is square to the body, and each knee until every shin is vertical. Save.
3. Press **Transform → drone**. All four arms should come down onto their stops at the same time.
4. Turn the M3 levelling screws until the arms are level. Use a phone spirit-level app on each arm.
5. Press **Walk** to unfold, then try walking on carpet.

## 8. Before flying

Do the [Betaflight setup](betaflight.md) and the [safety checklist](safety.md).
