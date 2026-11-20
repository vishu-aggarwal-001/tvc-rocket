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
SHIN_LEN = 82.0           # knee axis to the toe
TOE_LEN = 42.0            # the toe: a foot when walking, landing gear (clears the battery) when flying
MOTOR_SEAT = 10.0        # motor seat height above the knee axis (drone pose)
MOTOR_SLOT = (4.5, 8.5)   # M2 slots on the diagonals, radius 4.5..8.5: fits 9 mm-circle, 9x9 and 12x12 motor patterns
M2_TAP, M2_CLR, M3_TAP, M3_CLR = 1.7, 2.3, 2.6, 3.3
MAGNET = (6.2, 3.1)       # 6x3 mm neodymium disc pocket (d, depth)
FC_PATTERNS = (20.0, 26.0)  # standoffs for 20x20 stacks and 26x26 (25.5) whoop-style AIO boards
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
SHELL_SCREWS = [(-24, -22), (24, -22), (-24, 22), (24, 22)]   # canopy -> deck (M2)


def soft(wp, selector, r):
    """Fillet if OCC can do it, otherwise leave the edges sharp (never break the build)."""
    try:
        out = wp.edges(selector).fillet(r)
        return out if out.val().isValid() else wp
    except Exception:
        return wp


def rrect(w, h, r):
    return cq.Sketch().rect(w, h).vertices().fillet(r)


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
    p = cq.Workplane('XY').placeSketch(rrect(2 * half, 2 * half, 16)).extrude(PLATE_T)
    p = soft(p, '<Z', 1.2)
    rim = (cq.Workplane('XY').placeSketch(rrect(2 * half, 2 * half, 16)).extrude(PLATE_T + 3)
           .cut(cq.Workplane('XY').placeSketch(rrect(2 * half - 6, 2 * half - 6, 13)).extrude(PLATE_T + 3)))
    rim = soft(rim, '>Z', 1.2)
    p = p.union(rim)
    for (x, y) in HIPS:
        ang = math.degrees(math.atan2(y, x))
        r_body = HIP_R - SERVO['shaft_off']      # body centre sits inward of the shaft
        cx, cy = r_body * math.cos(math.radians(ang)), r_body * math.sin(math.radians(ang))
        cut = servo_cut(cq.Plane(origin=(cx, cy, 0), xDir=(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)), 20)
        p = p.cut(cut)
        # rim relief so the coxa can swing +-50 deg
        p = p.cut(cq.Workplane('XY').center(x, y).circle(17).extrude(PLATE_T + 4).translate((0, 0, PLATE_T)))
    # pillars (M3 heat-set inserts on top) between the hips, flared at the foot
    for (x, y) in [(0, 40), (0, -40), (40, 0), (-40, 0)]:
        pil = cq.Workplane('XY').center(x, y).circle(4.2).extrude(Z_DECK)
        pil = pil.union(cq.Workplane('XY').center(x, y).circle(5.8).workplane(offset=PLATE_T + 3).circle(4.2).loft()
                        .translate((0, 0, 0)))
        p = p.union(pil).cut(cq.Workplane('XY').center(x, y).circle(2.0).extrude(Z_DECK + 1).translate((0, 0, Z_DECK - 6)))
    # battery strap slots + weight-saving windows
    for x in (-24, 24):
        p = p.cut(cq.Workplane('XY').center(x, 0).slot2D(22, 3.2, 90).extrude(10, both=True))
    p = p.cut(cq.Workplane('XY').placeSketch(rrect(30, 46, 6)).extrude(10, both=True))
    # power switch / XT30 pass-through at the back
    p = p.cut(cq.Workplane('XY').center(0, -40).slot2D(14, 6).extrude(10, both=True))
    return p


def chassis_deck():
    """Top deck: takes the coxa pins (dual-support hips), carries the FC stack,
    the ESP32-S3 and the canopy."""
    half = 46.0
    d = cq.Workplane('XY').placeSketch(rrect(2 * half, 2 * half, 16)).extrude(DECK_T)
    d = soft(d, '>Z', 1.0)
    for (x, y) in HIPS:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(3.25).extrude(10, both=True))   # Ø6 pin bushing
    for (x, y) in [(0, 40), (0, -40), (40, 0), (-40, 0)]:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M3_CLR / 2).extrude(10, both=True))
    # FC standoffs (M2), slightly behind centre: 20x20 and 26x26 patterns
    fc = [(sx * p / 2, -6 + sy * p / 2) for p in FC_PATTERNS for sx in (-1, 1) for sy in (-1, 1)]
    for (x, y) in fc:
        d = d.union(cq.Workplane('XY').center(x, y).circle(2.6).extrude(DECK_T + 4))
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M2_TAP / 2).extrude(20, both=True))
    # ESP32-S3 SuperMini bay at the front (zip-tie slots) and wiring windows
    for x in (-13, 13):
        d = d.cut(cq.Workplane('XY').center(x, 22).rect(2.4, 6).extrude(10, both=True))
    d = d.cut(cq.Workplane('XY').center(0, -6).rect(12, 12).extrude(10, both=True))
    for (x, y) in [(-26, 0), (26, 0)]:
        d = d.cut(cq.Workplane('XY').center(x, y).rect(8, 20).extrude(10, both=True).edges('|Z').fillet(3))
    # canopy screw holes
    for (x, y) in SHELL_SCREWS:
        d = d.cut(cq.Workplane('XY').center(x, y).circle(M2_TAP / 2).extrude(10, both=True))
    return d.translate((0, 0, Z_DECK))


def canopy():
    """One-piece shell over the deck: a low, sloped body with hex vents on top and
    slotted vents on the sides. Screws to the deck with 4x M2."""
    t = 1.8
    BW, TW, TD, H = 78.0, 58.0, 58.0, 17.0          # base width, top width/depth, height

    def body(off):
        lo = (cq.Workplane('XY').placeSketch(rrect(BW - 2 * off, BW - 2 * off, 26 - off),
                                             rrect(TW - 2 * off, TD - 2 * off, 17 - off).moved(cq.Location(cq.Vector(0, 0, H - off))))
              .loft())
        return soft(lo, '>Z', 7 - off)

    outer, inner = body(0), body(t).translate((0, 0, -0.01))
    shell = outer.cut(inner)
    # screw bosses, clipped to the inside of the shell
    bosses = cq.Workplane('XY').pushPoints(SHELL_SCREWS).circle(3.2).extrude(H)
    shell = shell.union(bosses.intersect(inner))
    shell = shell.cut(cq.Workplane('XY').pushPoints(SHELL_SCREWS).circle(M2_CLR / 2).extrude(H + 1))
    # clear the coxa pins that poke through the deck
    shell = shell.cut(cq.Workplane('XY').pushPoints(HIPS).circle(5).extrude(6, both=True))
    # hex vents across the top
    pts = []
    for row in range(7):
        for col in range(-4, 5):
            x, y = col * 6.4 + (3.2 if row % 2 else 0), -16.8 + row * 5.6
            if abs(x) < 19 and abs(y) < 19:
                pts.append((x, y))
    shell = shell.cut(cq.Workplane('XY').pushPoints(pts).polygon(6, 4.6).extrude(10).translate((0, 0, H - 4)))
    # slotted side vents (left/right) and USB-C access for the ESP32 at the front
    for sx in (-1, 1):
        for i in range(4):
            shell = shell.cut(cq.Workplane('YZ', origin=(sx * 40, 0, 0)).center(-10.5 + i * 7, 7.5)
                              .slot2D(9, 2.6, 90).extrude(14, both=True))
    shell = shell.cut(cq.Workplane('XZ', origin=(0, 42, 0)).center(0, 4.5).placeSketch(rrect(12, 5.5, 2)).extrude(10))
    return shell.translate((0, 0, Z_DECK + DECK_T))


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
    # arm: a tapered beam that deepens towards the knee, rounded along its length
    arm = (cq.Workplane('XZ').moveTo(6, z0).spline([(18, z0 - 2.5), (COXA_LEN - 7, z0 - 7)], includeCurrent=True)
           .lineTo(COXA_LEN - 7, z0 + COXA_T).lineTo(6, z0 + COXA_T).close().extrude(5, both=True))
    arm = soft(arm, '|Y', 0.8)
    try:   # round the long edges only (the ends are buried in the root and the knee frame)
        arm = arm.faces('>Y or <Y').edges('not |Z').fillet(1.6)
    except Exception:
        pass
    # knee servo frame: plate normal to Y at y=0..3, servo body passes through to -Y
    kx, kz = COXA_LEN, Z_KNEE
    frame = cq.Workplane('XY').box(20, KNEE_FRAME_T, 38).translate((kx, KNEE_FRAME_T / 2, kz - 9))
    frame = soft(frame, '|Y', 4)
    body_c = (kx, 0, kz - s['shaft_off'])
    # sleeve that wraps the knee servo body (stiffer, and it hides the screws). The servo
    # slides in from the horn side; the far end is open, with a notch for the lead.
    sl_len = 12.0
    sleeve = (cq.Workplane('XZ').center(kx, kz - s['shaft_off'])
              .placeSketch(rrect(s['W'] + 3.6, s['L'] + 3.6, 3)).extrude(sl_len))
    sleeve = sleeve.cut(cq.Workplane('XZ').center(kx, kz - s['shaft_off']).rect(s['W'], s['L']).extrude(sl_len + 1))
    sleeve = sleeve.cut(cq.Workplane('XY').box(6, 6, 6).translate((kx, -sl_len, kz - s['shaft_off'] - s['L'] / 2)))
    sleeve = soft(sleeve, '<Y', 0.8)
    frame = frame.union(sleeve)
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
    riser = cq.Workplane('XY').box(6.5, ys0 - 0.6 - 2, 9).translate((kx - STOP_R1 + 3.25, (ys0 - 0.6 + 2) / 2, kz - 5.5))
    stop = soft(ledge, '|X', 1.2).union(soft(web, '|Y', 1.2)).union(soft(riser, '|Y', 1.2))
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
    ym = (y0 + y1) / 2
    root = cq.Workplane('XZ').circle(10).extrude(-4).translate((0, y0, 0))
    root = soft(root, '>Y', 1.0)
    horn = (cq.Workplane('XZ').rect(32, 6.2).extrude(-1.6).union(cq.Workplane('XZ').rect(6.2, 20).extrude(-1.6))
            .union(cq.Workplane('XZ').circle(3.8).extrude(-1.6))).translate((0, y0, 0))
    # main beam: tapers from the knee to the toe, upper edge gently curved
    L = SHIN_LEN
    beam = (cq.Workplane('XZ').moveTo(3, -5.5).lineTo(L, -3.5).lineTo(L, 3)
            .spline([(L * 0.55, 4.6), (3, 6)], includeCurrent=True).close()
            .extrude(-(y1 - y0)).translate((0, y0, 0)))
    beam = soft(beam, '>Y', 1.8)
    # tail: sits on the stop ledge (magnet in its underside); reaches back into the root disc
    ys0, ys1 = STOP_Y
    yt = (ys0 + ys1) / 2
    tail = cq.Workplane('XY').box(STOP_R1 - 6, ys1 - ys0, 7).translate((-(STOP_R1 + 6) / 2, yt, -1.5))
    tail = soft(tail, '|Y and >Z', 2.5)
    tail = soft(tail, '|X', 1.0)
    # round motor boss through the beam; its top (the motor seat) is level with the top of
    # the knee disc, so the arm prints upside down with the motor seat flat on the bed
    mx = SHIN_TO_MOTOR
    pad = cq.Workplane('XY').center(mx, ym).circle(11.5).extrude(MOTOR_SEAT + 4).translate((0, 0, -4))
    pad = soft(pad, '>Z or <Z', 1.2)
    # toe with a gusset on the inner side (points down in drone mode, inward when walking)
    toe = cq.Workplane('XY').box(8, 8, TOE_LEN).translate((L - 4, ym - 0.4, -2 - TOE_LEN / 2))   # 8x8: the TPU boot fits
    toe = soft(toe, '|Z', 1.6)
    gus = (cq.Workplane('XZ').polyline([(L - 7, -3), (L - 7, -16), (L - 22, -3)]).close()
           .extrude(-(y1 - y0 - 2)).translate((0, y0 + 1, 0)))
    leg = root.union(beam).union(tail).union(pad).union(toe).union(gus)
    leg = leg.cut(horn)
    leg = leg.cut(cq.Workplane('XZ').pushPoints([(9, 0), (-9, 0), (0, 9)]).circle(0.9).extrude(-6).translate((0, y0 - 1, 0)))
    leg = leg.cut(cq.Workplane('XY').center(-STOP_MAG, yt).circle(MAGNET[0] / 2).extrude(MAGNET[1]).translate((0, 0, -5)))
    leg = leg.cut(cq.Workplane('XY').center(-STOP_SCREW, yt).rect(5, 5).extrude(1.0).translate((0, 0, -5)))   # flat for the levelling screw tip
    # motor mount: four diagonal M2 slots (any 1103-1404 pattern) + shaft/circlip relief;
    # screw heads sit flat under the boss
    r0, r1 = MOTOR_SLOT
    rm, ln = (r0 + r1) / 2, r1 - r0 + M2_CLR
    for k in range(4):
        a = 45 + 90 * k
        cx, cy = mx + rm * math.cos(math.radians(a)), ym + rm * math.sin(math.radians(a))
        leg = leg.cut(cq.Workplane('XY').center(cx, cy).slot2D(ln, M2_CLR, a).extrude(30, both=True))
        leg = leg.cut(cq.Workplane('XY').center(cx, cy).slot2D(ln + 2.2, 4.4, a).extrude(MOTOR_SEAT + 10 - 3).translate((0, 0, -10)))  # head counterbore: 3 mm left under the motor
    leg = leg.cut(cq.Workplane('XY').center(mx, ym).circle(2.6).extrude(30, both=True))
    # lightening windows (also the motor-wire path)
    for (x, ln) in ((22, 16), (66, 12)):
        leg = leg.cut(cq.Workplane('XZ').center(x, 0.3).slot2D(ln, 4.2).extrude(-20).translate((0, y0 - 1, 0)))
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
    'canopy': (canopy, 1),
    'coxa': (coxa, 4),
    'shin_arm': (shin, 4),
    'foot_tpu': (foot_tpu, 4),
    'leg_spacer': (leg_spacer, 4),
}

PRINT_FLIP = {'shin_arm'}   # parts exported upside down for printing (motor seat on the bed)

ASM = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'viewer', 'assembly')

def export_stl(wp, path, tol):
    """Write an STL and make sure the mesh is closed (slicers hate holes); OCC's mesher
    occasionally leaves a seam open, so retry with slightly different settings."""
    from OCP.BRepTools import BRepTools
    for k in range(8):
        BRepTools.Clean_s(wp.val().wrapped)          # drop any cached mesh so the new settings apply
        cq.exporters.export(wp, path, tolerance=tol * (1 + 0.25 * (k // 4)), angularTolerance=(0.15, 0.1, 0.2, 0.25)[k % 4])
        try:
            import trimesh
            if trimesh.load(path).is_watertight:
                return
        except ImportError:
            return
    try:   # last resort: close the seam with MeshFix (pip install pymeshfix)
        import pymeshfix
        m = trimesh.load(path)
        mf = pymeshfix.MeshFix(m.vertices, m.faces); mf.repair()
        trimesh.Trimesh(mf.points, mf.faces).export(path)
        if trimesh.load(path).is_watertight:
            return
    except ImportError:
        pass
    print('  warning: mesh not watertight:', path)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True); os.makedirs(ASM, exist_ok=True)
    for name, (fn, n) in PARTS.items():
        part = fn()
        # assembly coordinates for the 3D viewer
        part = cq.Workplane().add(part.val().clean().fix())
        bb = part.val().BoundingBox()
        # print-ready copy: flipped if it prints better upside down, centred, lowest point on the bed
        bed = part.rotate((0, 0, 0), (1, 0, 0), 180) if name in PRINT_FLIP else part
        pb = bed.val().BoundingBox()
        bed = bed.translate((-(pb.xmin + pb.xmax) / 2, -(pb.ymin + pb.ymax) / 2, -pb.zmin))
        export_stl(part, os.path.join(ASM, f'{name}.stl'), 0.06)        # assembly coordinates (3D viewer)
        export_stl(bed, os.path.join(OUT, f'{name}.stl'), 0.04)         # print-ready: centred, on the bed
        cq.exporters.export(bed, os.path.join(OUT, f'{name}.step'))
        print(f'{name:16s} x{n}  {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:6.1f} mm  vol {part.val().Volume() / 1000:6.1f} cm3')
