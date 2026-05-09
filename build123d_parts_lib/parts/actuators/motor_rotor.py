"""QDD 外转子 / Motor Rotor — outrunner BLDC rotor shell + arc magnets for QDD.

Two Part factories + one Compound factory:
  make_rotor_shell()  → outer cup (thin-wall cylinder + end-plate + center bore)
  make_arc_magnet()   → single arc-segment magnet (1 of 14 poles, on +X axis)
  make_motor_rotor()  → Compound of shell + 14 arc magnets at equal angular spacing

Geometry (local Z: open end = 0, closed end = rotor_h):
  Rotor shell OD   : Φ47.5 mm  (shell_wall_t=1.5 mm → inner r=22.25 mm)
  Rotor shell H    : 12 mm     (slightly taller than stator to overlap magnets)
  Center bore      : Φ5 mm     (press-fit on rotor shaft h6)
  End-plate t      : 2.0 mm    (closed end at z=rotor_h)

  Arc magnets      : 14 poles, arc = 360/14 × 0.9 ≈ 23.1° (pole-arc factor 0.9)
  Magnet inner r   : 20.25 mm  (stator OD/2 + air_gap 0.25 mm)
  Magnet thickness : 2.0 mm    → outer r = 22.25 mm (flush with shell inner wall)
  Magnet height    : 10.0 mm   (same as stator)

Arc magnet clipping strategy:
  1. Build full annulus ring (outer_r − inner_r).
  2. Subtract two large half-space boxes rotated to ±half_angle,
     removing all material outside the angular sector.
     upper_clip removes region where y > x·tan(+half_angle)
     lower_clip removes region where y < x·tan(−half_angle)
     Together they leave exactly the sector [−half, +half] centered on +X.

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC rotor geometry
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Compound,
    Cylinder,
    GeomType,
    Hole,
    Mode,
    Part,
    Pos,
    Rot,
    chamfer,
    export_step,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 转子壳尺寸 / Rotor shell dimensions ────────────────────────────────────────
rotor_od       = 47.5   # outer diameter  mm
rotor_h        = 12.0   # axial height  mm
shell_wall_t   =  1.5   # radial wall thickness  mm
center_bore_d  =  5.0   # shaft bore diameter  mm
endplate_t     =  2.0   # closed end-plate thickness  mm

# ── 弧形磁钢尺寸 / Arc magnet dimensions ───────────────────────────────────────
n_poles         = 14                           # number of poles
magnet_inner_r  = 20.25                        # inner radius  mm  (stator r + air gap)
magnet_t        =  2.0                         # radial thickness  mm
magnet_outer_r  = magnet_inner_r + magnet_t    # 22.25 mm (flush with shell inner wall)
magnet_h        = 10.0                         # axial height  mm
arc_factor      =  0.9                         # pole-arc ratio
magnet_half_deg = 180.0 * arc_factor / n_poles # ≈ 11.57°

GEOMETRY_INVARIANTS = {
    "rotor_od":       rotor_od,
    "rotor_h":        rotor_h,
    "shell_wall_t":   shell_wall_t,
    "center_bore_d":  center_bore_d,
    "n_poles":        n_poles,
    "magnet_inner_r": magnet_inner_r,
    "magnet_t":       magnet_t,
    "magnet_h":       magnet_h,
}


def make_rotor_shell() -> Part:
    """Generate outer rotor cup: thin-wall cylinder + closed end-plate + center bore
    + 14 arc-shaped magnet retention pockets on the inner wall.

    Magnet pocket geometry:
      Pocket opens at inner wall surface (r=22.25 mm), goes 0.5 mm into the wall.
      Arc = magnet arc angle (23.1°), height = magnet_h = 10 mm.
      Pockets evenly distributed at 360/14 spacing, providing tangential + axial
      location for the 14 arc magnets (adhesive bonding still required).
    """
    shell_inner_r  = rotor_od / 2 - shell_wall_t   # 22.25 mm
    pocket_depth   = 0.5                            # mm — radially into wall from inner surface
    pocket_r_outer = shell_inner_r                  # 22.25 mm (pocket opening faces inward)
    pocket_r_inner = shell_inner_r - pocket_depth   # 21.75 mm (pocket bottom)
    pocket_h       = magnet_h + 0.2                 # 10.2 mm — slight clearance for magnet

    # ── Base shell ──────────────────────────────────────────────────────────
    with BuildPart() as p:
        Cylinder(
            radius=rotor_od / 2,
            height=rotor_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=shell_inner_r,
            height=rotor_h - endplate_t + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        Hole(radius=center_bore_d / 2)

        try:
            open_edges = [
                e for e in p.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - rotor_od / 2) < 0.3 and abs(e.center().Z) < 0.3
            ]
            if open_edges:
                chamfer(open_edges, length=0.5)
        except Exception:
            pass

    solid = p.part

    # ── 14 magnet retention pockets (Algebra mode) ──────────────────────────
    # Each pocket is a shallow arc-sector cut into the inner wall.
    # Uses same half-plane clip strategy as make_arc_magnet().
    clip_size = pocket_r_outer + 5.0
    clip_h    = pocket_h + 0.2

    pocket_annulus = (
        Cylinder(
            radius=pocket_r_outer + 0.05,
            height=pocket_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=pocket_r_inner - 0.05,
            height=pocket_h + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    upper_clip = (
        Rot(0, 0, +magnet_half_deg)
        * Pos(0, clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    pocket_proto = pocket_annulus - upper_clip - lower_clip

    for i in range(n_poles):
        solid = solid - Rot(0, 0, 360.0 * i / n_poles) * pocket_proto

    return solid


def make_arc_magnet() -> Part:
    """Generate one arc-segment permanent magnet centered on +X axis.

    Method: full annulus ring clipped by two half-space subtractions rotated to
    ±half_angle, leaving exactly the intended angular sector.
    """
    clip_size = magnet_outer_r + 5.0   # large enough to cover annulus fully
    clip_h    = magnet_h + 0.2

    # 弧形磁钢环（全环）/ Full annulus ring
    annulus = (
        Cylinder(
            radius=magnet_outer_r + 0.05,
            height=magnet_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=magnet_inner_r,
            height=clip_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # 上裁剪（去除 y > x·tan(+half) 区域）/ Upper clip: remove y > x·tan(+half_angle)
    # Box placed at +Y in the frame rotated by +half_angle → removes above sector boundary
    upper_clip = (
        Rot(0, 0, magnet_half_deg)
        * Pos(0, clip_size / 2, magnet_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )

    # 下裁剪（去除 y < x·tan(-half) 区域）/ Lower clip: remove y < x·tan(-half_angle)
    lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, magnet_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )

    return annulus - upper_clip - lower_clip


def make_motor_rotor() -> Compound:
    """Generate complete rotor: shell + 14 arc magnets equally spaced as a Compound."""
    shell  = make_rotor_shell()
    magnet = make_arc_magnet()

    magnets = [Rot(0, 0, 360.0 * i / n_poles) * magnet for i in range(n_poles)]
    return Compound(children=[shell] + magnets)


if __name__ == "__main__":
    print("Building QDD motor rotor ...")
    print(f"  Shell   : Φ{rotor_od} OD  H={rotor_h} mm  wall={shell_wall_t} mm")
    print(f"  Magnets : {n_poles} poles  inner_r={magnet_inner_r} mm  "
          f"t={magnet_t} mm  arc±{magnet_half_deg:.2f}°")

    shell  = make_rotor_shell()
    magnet = make_arc_magnet()
    rotor  = make_motor_rotor()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(
            shell, magnet,
            names=["rotor_shell", "arc_magnet_x1"],
            colors=["dimgray", "tomato"],
            reset_camera=Camera.ISO,
        )
        print("OCP Viewer: 转子壳 + 单磁钢 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP ─────────────────────────────────────────────────────────────
    out_dir = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)

    export_step(shell,  str(out_dir / "rotor_shell.step"))
    export_step(magnet, str(out_dir / "arc_magnet.step"))
    export_step(rotor,  str(out_dir / "motor_rotor.step"))

    bb_s = shell.bounding_box()
    bb_m = magnet.bounding_box()
    print(f"\n── rotor_shell ──────────────────────────────────────")
    print(f"  Volume : {shell.volume:.1f} mm³")
    print(f"  BBox   : {bb_s.size.X:.2f} × {bb_s.size.Y:.2f} × {bb_s.size.Z:.2f} mm")
    print(f"── arc_magnet ───────────────────────────────────────")
    print(f"  Volume : {magnet.volume:.1f} mm³")
    print(f"  BBox   : {bb_m.size.X:.2f} × {bb_m.size.Y:.2f} × {bb_m.size.Z:.2f} mm")

    assert shell.volume  > 0, "❌ rotor_shell volume ≤ 0"
    assert magnet.volume > 0, "❌ arc_magnet volume ≤ 0"
    assert abs(bb_s.size.X - rotor_od) < 1.0, f"shell X 偏差: {bb_s.size.X:.2f}"
    assert abs(bb_s.size.Z - rotor_h)  < 0.2, f"shell Z 偏差: {bb_s.size.Z:.2f}"
    assert abs(bb_m.size.Z - magnet_h) < 0.2, f"magnet Z 偏差: {bb_m.size.Z:.2f}"
    print("  BRep + BBox ✓")
    print("────────────────────────────────────────────────────")
