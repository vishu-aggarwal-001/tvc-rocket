"""SkyCrawler — parametric CAD for every printed part.

    pip install cadquery
    python skycrawler.py          # writes ../stl/*.stl and ../stl/*.step

All sizes in millimetres. The servo numbers fit MG90S / SG90-size micro servos;
measure yours and adjust SERVO if they differ.

Coordinate convention: body centre at the origin, Z up, front = +Y (the face).
The four hips sit on the diagonals, so in drone mode the legs form an X quad.
"""
import math
import os
import cadquery as cq

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'stl')

# ------------------------------------------------------------------ parameters
SERVO = dict(
    L=23.0,          # body length (along the tab line), with clearance
    W=12.6,          # body width, with clearance
    tab_span=32.6,   # tip-to-tip length of the mounting tabs
    tab_t=2.6,       # tab thickness
    below_tab=16.0,  # body depth below the tabs (bottom of the case to the tabs)
    above_tab=12.0,  # tabs to the top face of a fitted horn
    shaft_off=5.6,   # shaft centre from the body centre, along the length
    screw_pitch=27.8,  # distance between the two tab screw holes
    screw_d=1.9,     # pilot hole for the M2 self-tapping screws that come with the servo
)
HIP_R = 48.0              # body centre to hip axis (on the diagonals)
PLATE_T = 3.0             # bottom plate
DECK_T = 2.6              # top deck
COXA_T = 5.0              # coxa root thickness (between the horn and the deck)
GAP = 0.5
COXA_LEN = 34.0           # hip axis to knee axis
SHIN_TO_MOTOR = 48.0      # knee axis to motor centre
SHIN_LEN = 92.0           # knee axis to the toe
TOE_LEN = 42.0            # the toe: a foot when walking, landing gear (clears the battery) when flying
MOTOR_HOLES = [(9.0, 9.0), (12.0, 12.0)]   # 1104-1404 class motor patterns (M2), both drilled
M2_TAP, M2_CLR, M3_TAP, M3_CLR = 1.7, 2.3, 2.6, 3.3
MAGNET = (6.2, 3.1)       # 6x3 mm neodymium disc pocket (d, depth)
FC_PATTERN = 20.0         # 20x20 flight controller stack
KNEE_FRAME_T = 3.0        # knee servo frame plate (tab plane at y = KNEE_FRAME_T)
LEG_Y0 = KNEE_FRAME_T + SERVO['above_tab']   # inner face of the shin = top of the knee horn
LEG_Y1 = LEG_Y0 + 8.0
STOP_Y = (LEG_Y0 + 2.2, LEG_Y0 + 10.2)     # end-stop plane: clear of the horn (y 15..16.6)
STOP_R0, STOP_R1 = 10.5, 23.5             # ledge spans this far behind the knee axis
STOP_MAG, STOP_SCREW = 19.0, 13.5         # magnet / levelling-screw distance behind the knee

# derived heights (bottom plate top face = z PLATE_T)
Z_TAB = PLATE_T
Z_HORN = Z_TAB + SERVO['above_tab']
Z_COXA_TOP = Z_HORN + COXA_T
Z_DECK = Z_COXA_TOP + GAP
Z_KNEE = Z_HORN + COXA_T / 2
HIP = HIP_R / math.sqrt(2)
HIPS = [(HIP, HIP), (-HIP, HIP), (-HIP, -HIP), (HIP, -HIP)]


def servo_cut(wp_plane_obj, through):
    """A servo body slot plus its two tab screw holes, centred on the BODY centre."""
    s = SERVO
    slot = cq.Workplane(wp_plane_obj).rect(s['L'], s['W']).extrude(through, both=True)
    holes = (cq.Workplane(wp_plane_obj).pushPoints([(-s['screw_pitch'] / 2, 0), (s['screw_pitch'] / 2, 0)])
             .circle(s['screw_d'] / 2).extrude(through, both=True))
    return slot.union(holes)


# ------------------------------------------------------------------ chassis
def chassis_bottom():
    """Bottom plate: four hip servos hang through it, battery straps underneath,
    four pillars carry the deck."""
    half = 46.0
    p = (cq.Workplane('XY').rect(2 * half, 2 * half).extrude(PLATE_T)
         .edges('|Z').fillet(14))
    # stiffening rim
    rim = (cq.Workplane('XY').rect(2 * half, 2 * half).extrude(PLATE_T + 3).edges('|Z').fillet(14)
           .cut(cq.Workplane('XY').rect(2 * half - 6, 2 * half - 6).extrude(PLATE_T + 3).edges('|Z').fillet(11)))
    p = p.union(rim)
    for (x, y) in HIPS:
        ang = math.degrees(math.atan2(y, x))
        # body centre sits inward of the shaft along the diagonal
        r_body = HIP_R - SERVO['shaft_off']
        cx, cy = r_body * math.cos(math.radians(ang)), r_body * math.sin(math.radians(ang))
        cut = servo_cut(cq.Plane(origin=(cx, cy, 0), xDir=(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)), 20)
        p = p.cut(cut)
        # rim relief so the coxa can swing ±45°
        p = p.cut(cq.Workplane('XY').center(x, y).circle(17).extrude(PLATE_T + 4).translate((0, 0, PLATE_T)))
    # pillars (M3 heat-set inserts on top) between the hips
    for (x, y) in [(0, 40), (0, -40), (40, 0), (-40, 0)]:
        pil = cq.Workplane('XY').center(x, y).circle(4.2).extrude(Z_DECK)
        p = p.union(pil).cut(cq.Workplane('XY').center(x, y).circle(2.0).extrude(Z_DECK + 1).translate((0, 0, Z_DECK - 6)))
    # battery strap slots + weight-saving windows
    for x in (-24, 24):
        p = p.cut(cq.Workplane('XY').center(x, 0).rect(3.2, 22).extrude(10, both=True))
    p = p.cut(cq.Workplane('XY').rect(30, 46).extrude(10, both=True).edges('|Z').fillet(5))
    # power switch / XT30 pass-through at the back
    p = p.cut(cq.Workplane('XY').center(0, -40).rect(14, 6).extrude(10, both=True).edges('|Z').fillet(2))
    return p


def chassis_deck():
    """Top deck: takes the coxa pins (dual-support hips), carries the FC stack,
    the ESP32-S3 and the head shell."""
    half = 46.0
    d = (cq.Workplane('XY').rect(2 * half, 2 * half).extrude(DECK_T).edges('|Z').fillet(14))
    for (x, y) in HIPS:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(3.25).extrude(10, both=True))   # Ø6 pin bushing
    for (x, y) in [(0, 40), (0, -40), (40, 0), (-40, 0)]:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M3_CLR / 2).extrude(10, both=True))
    # FC 20x20 standoffs (M2), slightly behind centre
    fc = [(sx * FC_PATTERN / 2, -6 + sy * FC_PATTERN / 2) for sx in (-1, 1) for sy in (-1, 1)]
    for (x, y) in fc:
        d = d.union(cq.Workplane('XY').center(x, y).circle(2.6).extrude(DECK_T + 4))
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M2_TAP / 2).extrude(20, both=True))
    # ESP32-S3 SuperMini bay at the front (zip-tie slots) and wiring windows
    for x in (-13, 13):
        d = d.cut(cq.Workplane('XY').center(x, 22).rect(2.4, 6).extrude(10, both=True))
    d = d.cut(cq.Workplane('XY').center(0, -6).rect(12, 12).extrude(10, both=True))
    for (x, y) in [(-26, 0), (26, 0)]:
        d = d.cut(cq.Workplane('XY').center(x, y).rect(8, 20).extrude(10, both=True).edges('|Z').fillet(3))
    # head shell screw holes
    for (x, y) in [(-27, -24), (27, -24), (-27, 30), (27, 30)]:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M2_TAP / 2).extrude(10, both=True))
    return d.translate((0, 0, Z_DECK))


def head_shell():
    """The head: covers the electronics, OLED face window at the front, cat ears."""
    W, D, H, t = 62.0, 62.0, 30.0, 2.0
    outer = cq.Workplane('XY').center(0, 3).rect(W, D).extrude(H).edges('|Z').fillet(9).faces('>Z').edges().fillet(4)
    inner = cq.Workplane('XY').center(0, 3).rect(W - 2 * t, D - 2 * t).extrude(H - t).edges('|Z').fillet(7)
    s = outer.cut(inner)
    # 0.96" SSD1306 window (active area ~22x11) + PCB pocket behind it
    s = s.cut(cq.Workplane('XZ', origin=(0, 3 + D / 2, 0)).center(0, 17).rect(24, 13).extrude(-5))
    s = s.cut(cq.Workplane('XZ', origin=(0, 3 + D / 2 - t, 0)).center(0, 16).rect(28.0, 28.0).extrude(1.2))
    # screw bosses down to the deck
    for (x, y) in [(-27, -24), (27, -24), (-27, 30), (27, 30)]:
        s = s.union(cq.Workplane('XY').center(x, y).circle(3.2).extrude(H - t))
        s = s.cut(cq.Workplane('XY').center(x, y).circle(M2_CLR / 2).extrude(H + 1))
        s = s.cut(cq.Workplane('XY').center(x, y).circle(2.2).extrude(3))
    # ears
    for sx in (-1, 1):
        ear = (cq.Workplane('XZ', origin=(0, 3 + D / 2 - 14, 0)).polyline([(sx * 12, H - 1), (sx * 26, H - 1), (sx * 24, H + 9)]).close().extrude(8))
        s = s.union(ear)
    # vents on the back, USB-C access on the left
    for i in range(5):
        s = s.cut(cq.Workplane('XZ', origin=(0, 3 - D / 2 + 3, 0)).center(-16 + i * 8, 14).rect(3, 14).extrude(5))
    s = s.cut(cq.Workplane('YZ', origin=(-W / 2 - 1, 0, 0)).center(22, 5).rect(10, 5).extrude(5))
    # leave the hip bushings uncovered: nothing to cut (shell sits inside them)
    return s.translate((0, 0, Z_DECK + DECK_T))


# ------------------------------------------------------------------ legs
def coxa():
    """Hip link. Built along +X from the hip axis (origin), Z up.
    Bottom of the root bolts to the hip servo horn; the Ø6 pin on top turns in the deck
    (so thrust and bending loads go into the body, not the servo gears). At the outer
    end it holds the knee servo (shaft along +Y) and the knee END STOP with a magnet
    and an M3 levelling screw."""
    s = SERVO
    z0 = Z_HORN
    root = cq.Workplane('XY').circle(10).extrude(COXA_T).translate((0, 0, z0))
    # cross-horn pocket underneath + 2 screw holes into the horn arms
    horn = (cq.Workplane('XY').rect(32, 6.2).extrude(1.6).union(cq.Workplane('XY').rect(6.2, 20).extrude(1.6))
            .union(cq.Workplane('XY').circle(3.8).extrude(1.6))).translate((0, 0, z0))
    root = root.cut(horn)
    root = root.cut(cq.Workplane('XY').pushPoints([(9, 0), (-9, 0)]).circle(0.9).extrude(COXA_T).translate((0, 0, z0)))
    pin = cq.Workplane('XY').circle(2.95).extrude(DECK_T + GAP + 0.5).translate((0, 0, z0 + COXA_T))
    # arm: deepens away from the hip
    arm = (cq.Workplane('XZ').polyline([(6, z0), (COXA_LEN - 8, z0 - 6), (COXA_LEN - 8, z0 + COXA_T), (6, z0 + COXA_T)]).close()
           .extrude(5, both=True))
    # knee servo frame: plate normal to Y at y=0..3, servo body passes through to -Y
    kx, kz = COXA_LEN, Z_KNEE
    frame = cq.Workplane('XY').box(20, KNEE_FRAME_T, 38).translate((kx, KNEE_FRAME_T / 2, kz - 9))
    body_c = (kx, 0, kz - s['shaft_off'])
    frame = frame.cut(cq.Workplane('XY').box(s['W'], 10, s['L']).translate(body_c))
    frame = frame.cut(cq.Workplane('XZ').pushPoints([(kx, kz - s['shaft_off'] + s['screw_pitch'] / 2), (kx, kz - s['shaft_off'] - s['screw_pitch'] / 2)])
                      .circle(s['screw_d'] / 2).extrude(10, both=True))
    # end-stop ledge, just inboard of the knee. It sits in the STOP plane (outboard of the
    # servo horn, which sweeps r=16 at y 15..16.6) and is held by a web that stays outside
    # the horn's sweep circle, so nothing rubs the horn or the shin root disc.
    ys0, ys1 = STOP_Y
    ym = (ys0 + ys1) / 2
    ledge = cq.Workplane('XY').box(STOP_R1 - STOP_R0, ys1 - ys0, 6).translate((kx - (STOP_R0 + STOP_R1) / 2, ym, kz - 8))
    web = cq.Workplane('XY').box(6.5, ys0 - KNEE_FRAME_T + 2, 6).translate((kx - STOP_R1 + 3.25, (ys0 + KNEE_FRAME_T) / 2, kz - 8))
    stop = ledge.union(web)
    stop = stop.cut(cq.Workplane('XY').center(kx - STOP_MAG, ym).circle(MAGNET[0] / 2).extrude(MAGNET[1]).translate((0, 0, kz - 5 - MAGNET[1])))
    stop = stop.cut(cq.Workplane('XY').center(kx - STOP_SCREW, ym).circle(M3_TAP / 2).extrude(20).translate((0, 0, kz - 15)))
    c = root.union(pin).union(arm).union(frame).union(stop)
    return c.translate((0, 0, -z0))   # origin = hip axis at the horn face


def shin():
    """Lower leg = drone arm. Origin on the knee axis, drawn in DRONE pose (pointing +X).
    The root disc bolts to the knee horn; the tail rests on the coxa end stop when the
    arm is level, so propeller thrust pushes it INTO the stop. Motor pad on top at
    SHIN_TO_MOTOR, toe at the tip pointing down (landing foot in drone mode)."""
    y0, y1 = LEG_Y0, LEG_Y1      # the leg's plane (outboard of the servo horn)
    root = cq.Workplane('XZ').circle(10).extrude(-4).translate((0, y0, 0))
    horn = (cq.Workplane('XZ').rect(32, 6.2).extrude(-1.6).union(cq.Workplane('XZ').rect(6.2, 20).extrude(-1.6))
            .union(cq.Workplane('XZ').circle(3.8).extrude(-1.6))).translate((0, y0, 0))
    root = root.cut(horn)
    root = root.cut(cq.Workplane('XZ').pushPoints([(9, 0), (-9, 0), (0, 9)]).circle(0.9).extrude(-6).translate((0, y0 - 1, 0)))
    # main beam (I-ish section) from the knee to the toe
    beam = cq.Workplane('XZ').polyline([(4, -5), (SHIN_LEN, -4), (SHIN_LEN, 3), (4, 5)]).close().extrude(-(y1 - y0)).translate((0, y0, 0))
    # tail: sits on the stop ledge (magnet in its underside); reaches back into the root disc
    ys0, ys1 = STOP_Y
    ym = (ys0 + ys1) / 2
    tail = cq.Workplane('XY').box(STOP_R1 - 6, ys1 - ys0, 7).translate((-(STOP_R1 + 6) / 2, ym, -1.5))
    tail = tail.cut(cq.Workplane('XY').center(-STOP_MAG, ym).circle(MAGNET[0] / 2).extrude(MAGNET[1]).translate((0, 0, -5)))
    tail = tail.cut(cq.Workplane('XY').center(-STOP_SCREW, ym).rect(5, 5).extrude(1.0).translate((0, 0, -5)))   # flat for the levelling screw tip
    # motor pad
    mx = SHIN_TO_MOTOR
    pad = cq.Workplane('XY').center(mx, (y0 + y1) / 2).circle(12).extrude(3).translate((0, 0, 3))
    pad = pad.union(cq.Workplane('XY').center(mx, (y0 + y1) / 2).rect(22, 8).extrude(6).translate((0, 0, 0)))
    leg = root.union(beam).union(tail).union(pad)
    # motor holes (both patterns) + shaft relief, screw-head pockets from below
    pts = []
    for (a, b) in MOTOR_HOLES:
        pts += [(mx + sx * a / 2, (y0 + y1) / 2 + sy * b / 2) for sx in (-1, 1) for sy in (-1, 1)]
    leg = leg.cut(cq.Workplane('XY').pushPoints(pts).circle(M2_CLR / 2).extrude(30, both=True))
    leg = leg.cut(cq.Workplane('XY').center(mx, (y0 + y1) / 2).circle(3.5).extrude(30, both=True))
    leg = leg.cut(cq.Workplane('XY').pushPoints(pts).circle(2.1).extrude(5).translate((0, 0, -6)))
    # lightening slots + wire channel
    for x in (24, 70):
        leg = leg.cut(cq.Workplane('XZ').center(x, 0).slot2D(14, 4).extrude(-20).translate((0, y0 - 1, 0)))
    # toe (points down in drone mode, inward in walking mode)
    toe = cq.Workplane('XY').box(8, y1 - y0, TOE_LEN).translate((SHIN_LEN - 4, (y0 + y1) / 2, -2 - TOE_LEN / 2))
    leg = leg.union(toe)
    return leg


def foot_tpu():
    """TPU boot that slips over the toe (grip for walking, cushion for landing)."""
    t = 1.6
    outer = cq.Workplane('XY').box(8 + 2 * t, 8 + 2 * t, 14 + t).edges('|Z').fillet(2.5).faces('<Z').edges().fillet(2)
    inner = cq.Workplane('XY').box(8.3, 8.3, 14).translate((0, 0, t / 2 + 0.01))
    return outer.cut(inner)


def leg_spacer():
    """Optional: shim between the knee horn and the shin root if your horns sit low."""
    return cq.Workplane('XZ').circle(10).circle(3.9).extrude(1.0)


PARTS = {
    'chassis_bottom': (chassis_bottom, 1),
    'chassis_deck': (chassis_deck, 1),
    'head_shell': (head_shell, 1),
    'coxa': (coxa, 4),
    'shin_arm': (shin, 4),
    'foot_tpu': (foot_tpu, 4),
    'leg_spacer': (leg_spacer, 4),
}

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'viewer', 'assembly')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); os.makedirs(ASM, exist_ok=True)
    for name, (fn, n) in PARTS.items():
        part = fn()
        # assembly coordinates for the 3D viewer
        cq.exporters.export(part, os.path.join(ASM, f'{name}.stl'), tolerance=0.1, angularTolerance=0.2)
        # print-ready: centred on the bed, lowest point at z = 0
        bb = part.val().BoundingBox()
        bed = part.translate((-(bb.xmin + bb.xmax) / 2, -(bb.ymin + bb.ymax) / 2, -bb.zmin))
        cq.exporters.export(bed, os.path.join(OUT, f'{name}.stl'), tolerance=0.05, angularTolerance=0.1)
        cq.exporters.export(bed, os.path.join(OUT, f'{name}.step'))
        print(f'{name:16s} x{n}  {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm  vol {part.val().Volume() / 1000:6.1f} cm3')
