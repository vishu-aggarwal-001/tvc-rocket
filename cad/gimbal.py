"""Generate the TVC gimbal STL files.

Run:  pip install manifold3d trimesh numpy
      python gimbal.py

All sizes are in millimetres. Change the numbers in PARAMS to fit your
motor and body tube, then run it again.
"""
import math
import os

import numpy as np
import trimesh
from manifold3d import Manifold

PARAMS = dict(
    motor_d=24.0,        # motor diameter
    motor_fit=0.4,       # extra room so the motor slides in
    sleeve_wall=1.6,
    sleeve_len=75.0,
    stop_hole_d=19.0,    # forward thrust stop; ejection gas passes through
    stop_len=3.0,
    body_id=65.0,        # inside diameter of your body tube
    body_fit=0.4,
    ring_h=10.0,
    bolt_hole=3.2,       # M3 clearance
    tap_hole=2.8,        # M3 self-tapping into PETG/ASA
    rod_hole=1.7,        # 1.5 mm wire pushrod
    servo_w=12.6,        # MG90S body + clearance
    servo_l=23.0,
    seg=96,
)

P = PARAMS
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")


def cyl(h, r, center=False):
    return Manifold.cylinder(h, r, r, P["seg"], center)


def tube(h, r_out, r_in, center=False):
    return cyl(h, r_out, center) - cyl(h + 2, r_in, True).translate(
        [0, 0, h / 2 if not center else 0])


def box(x, y, z):
    return Manifold.cube([x, y, z], True)


def x_axis(m):
    return m.rotate([0, 90, 0])


def y_axis(m):
    return m.rotate([90, 0, 0])


def save(m, name):
    mesh = m.to_mesh()
    tm = trimesh.Trimesh(vertices=np.array(mesh.vert_properties)[:, :3],
                         faces=np.array(mesh.tri_verts))
    assert tm.is_watertight, name
    os.makedirs(OUT, exist_ok=True)
    tm.export(os.path.join(OUT, name + ".stl"))
    print(f"{name}.stl  {tm.extents.round(1)} mm  watertight={tm.is_watertight}")


# Derived sizes
r_motor = (P["motor_d"] + P["motor_fit"]) / 2
r_sleeve = r_motor + P["sleeve_wall"]
gap = 2.0
r_ring_in = r_sleeve + gap
r_ring_out = r_ring_in + 4.0
r_mount_in = r_ring_out + gap
r_mount_out = (P["body_id"] - P["body_fit"]) / 2
pivot_z = 30.0  # pivot height on the sleeve, measured from the nozzle end


def motor_sleeve():
    L = P["sleeve_len"]
    s = tube(L, r_sleeve, r_motor)
    # forward thrust stop: the motor pushes on this lip
    lip = tube(P["stop_len"], r_sleeve, P["stop_hole_d"] / 2).translate(
        [0, 0, L - P["stop_len"]])
    s = s + lip
    # X pivot bosses, reaching across the gap to the inner ring
    # flat boss face: its corners (radius 3.5 off-axis) keep a 0.3 mm gap
    boss_len = math.sqrt((r_ring_in - 0.3) ** 2 - 3.5 ** 2) - (r_motor + 0.2)
    boss = x_axis(cyl(boss_len, 3.5)).translate([r_motor + 0.2, 0, pivot_z])
    s = s + boss + boss.rotate([0, 0, 180])
    # yaw lug at +Y near the forward end, for the pushrod
    lug = box(3.0, 9.0, 10.0).translate([0, r_sleeve + 3.5, L - 8])
    lug = lug - x_axis(cyl(10, P["rod_hole"] / 2, True)).translate(
        [0, r_sleeve + 5.5, L - 6])
    s = s + lug
    # tapped pivot holes (clear the bore so they never touch the motor)
    hole = x_axis(cyl(r_sleeve * 2 + 10, P["tap_hole"] / 2, True)).translate(
        [0, 0, pivot_z])
    s = s - hole
    # keep the motor bore clean
    s = s - cyl(L - P["stop_len"], r_motor).translate([0, 0, -0.01])
    return s


def inner_ring():
    h = P["ring_h"]
    r = tube(h, r_ring_out, r_ring_in, True)
    # Y bosses reaching to the outer mount
    y_end = math.sqrt((r_mount_in - 0.3) ** 2 - 3.5 ** 2)
    boss = y_axis(cyl(y_end - r_ring_out + 0.5, 3.5)).translate([0, y_end, 0])
    r = r + boss + boss.rotate([0, 0, 180])
    # pitch lug on top at +X, beside the sleeve pivot
    lug = box(4.0, 3.0, 9.0).translate([r_ring_in + 1.5, 7.0, h / 2 + 4.0])
    lug = lug - y_axis(cyl(10, P["rod_hole"] / 2, True)).translate(
        [r_ring_in + 1.5, 7.0, h / 2 + 5.5])
    r = r + lug
    # X clearance holes for the sleeve pivots (M3 bolts)
    r = r - x_axis(cyl(r_ring_out * 2 + 10, P["bolt_hole"] / 2, True))
    # Y tapped holes for the mount pivots
    r = r - y_axis(cyl((r_ring_out + gap) * 2 + 10, P["tap_hole"] / 2, True))
    return r


def outer_mount():
    h = P["ring_h"]  # same height as the ring so the pitch lug stays above it
    m = tube(h, r_mount_out, r_mount_in, True)
    m = m - y_axis(cyl(r_mount_out * 2 + 10, P["bolt_hole"] / 2, True))
    # counterbore for the bolt heads so the ring still slides into the tube
    cb = y_axis(cyl(3.0, 3.2)).translate([0, r_mount_out + 0.01, 0])
    m = m - cb - cb.rotate([0, 0, 180])
    return m


def servo_plate():
    t = 4.0
    p = cyl(t, r_mount_out)
    p = p - cyl(t + 2, 15.0, True).translate([0, 0, t / 2])  # ejection path
    r_s = 24.0
    sx = box(P["servo_w"], P["servo_l"], t + 2).translate([r_s, 0, t / 2])
    sy = box(P["servo_l"], P["servo_w"], t + 2).translate([0, r_s, t / 2])
    p = p - sx - sy
    # mounting-ear screw holes (M2 self-tap)
    for dx, dy in [(r_s, 14.0), (r_s, -14.0)]:
        p = p - cyl(t + 2, 0.9, True).translate([dx, dy, t / 2])
        p = p - cyl(t + 2, 0.9, True).translate([dy, dx, t / 2])
    return p


if __name__ == "__main__":
    print(f"sleeve OD {2*r_sleeve:.1f}, ring {2*r_ring_in:.1f}/{2*r_ring_out:.1f}, "
          f"mount {2*r_mount_in:.1f}/{2*r_mount_out:.1f}")
    save(motor_sleeve(), "motor_sleeve")
    save(inner_ring(), "inner_ring")
    save(outer_mount(), "outer_mount")
    save(servo_plate(), "servo_plate")
