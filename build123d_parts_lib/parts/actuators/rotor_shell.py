"""QDD 外转子壳 / Outrunner Rotor Shell for QDD motor.

Factory: make_rotor_shell() → Part
  Thin-wall cylindrical cup (closed end-plate + center bore) with 14 arc-shaped
  magnet bays formed by divider fins, plus snap-in retention lips at the open end.

Geometry (Z=0 at open end, +Z toward closed end):
  OD          : Φ47.5 mm   (shell_wall_t=1.5 mm → inner r=22.25 mm)
  Height      : 12.0 mm
  Center bore : Φ5 mm      (press-fit on rotor shaft h6)
  End-plate t : 2.0 mm     (closed end at z=rotor_h)

Magnet bays / 磁钢凹槽 (14 ×):
  Formed by 14 divider fins at inter-magnet gap positions.
  Fins project inward from inner wall → 14 visible arc bays (凹槽) for magnets.
  Magnet outer surface (r=22.25 mm) sits against inner wall between fins.
  Gap between adjacent magnets: 360°/14 − 23.14° = 2.57° (arc ≈ 1.0 mm)

Divider fins / 隔离肋 (14 ×, at inter-magnet gaps):
  Protrusion : 1.5 mm inward (fin tip r = 20.75 mm, 0.5 mm clearance from magnet inner face)
  Height     : 10.0 mm axial (full magnet height — tangential guide)
  Arc        : ±gap_half_deg (= ±1.286°, fills the inter-magnet gap exactly)
  Purpose    : tangential location of each magnet in its bay

Retention lips / 保留唇 (14 ×, at open end, at magnet arc positions):
  Protrusion : 0.5 mm inward (lip tip r = 21.75 mm)
  Height     : 1.5 mm axial (Z=0 to Z=1.5 mm)
  Arc        : ±magnet_half_deg (same angular span as magnet)
  Purpose    : axial snap-in; tilt magnet ~15°, PETG lip deflects and snaps back

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC rotor geometry
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    GeomType,
    Hole,
    Mode,
    Part,
    Pos,
    Rot,
    add,
    chamfer,
    export_step,
)

from build123d_parts_lib.parts.actuators.arc_magnet import (
    magnet_half_deg,  # ≈ 11.57° — magnet arc half-angle
    magnet_h,         # 10.0 mm
    magnet_inner_r,   # 20.25 mm — used for fin clearance check
    n_poles,          # 14
)

# ── 转子壳尺寸 / Rotor shell dimensions ────────────────────────────────────────
rotor_od      = 47.5   # outer diameter  mm
rotor_h       = 12.0   # axial height  mm
shell_wall_t  =  1.5   # radial wall thickness  mm
center_bore_d =  5.0   # shaft bore diameter  mm
endplate_t    =  2.0   # closed end-plate thickness  mm

# ── 隔离肋 / Divider fin dimensions ────────────────────────────────────────────
gap_deg      = 360.0 / n_poles - 2 * magnet_half_deg  # 25.714 − 23.143 = 2.571°
gap_half_deg = gap_deg / 2                             # 1.286°
fin_protrusion = 1.5   # mm inward — tip at r=20.75mm (0.5mm clearance from magnet inner face)
fin_h          = magnet_h  # 10.0 mm — full-height tangential guide

# ── 保留唇 / Retention lip dimensions ──────────────────────────────────────────
retention_lip_h = 1.5  # mm axial height at open end
lip_protrusion  = 0.5  # mm inward from inner wall (lip tip r = 21.75 mm)

GEOMETRY_INVARIANTS = {
    "rotor_od":         rotor_od,
    "rotor_h":          rotor_h,
    "shell_wall_t":     shell_wall_t,
    "center_bore_d":    center_bore_d,
    "n_poles":          n_poles,
    "gap_deg":          gap_deg,
    "fin_protrusion":   fin_protrusion,
    "fin_h":            fin_h,
    "retention_lip_h":  retention_lip_h,
    "lip_protrusion":   lip_protrusion,
    # fin tip clearance to magnet inner face
    "fin_tip_r":        rotor_od / 2 - shell_wall_t - fin_protrusion,  # 20.75 mm
    "lip_tip_r":        rotor_od / 2 - shell_wall_t - lip_protrusion,  # 21.75 mm
}


def make_rotor_shell() -> Part:
    """Generate outer rotor cup with 14 divider fins + snap-in retention lips.

    Fins create 14 arc-shaped bays (凹槽) where magnets sit:
      inner wall r = 22.25 mm — magnet outer surface rests here between fins
      fin tip r = 20.75 mm (1.5 mm inward, 0.5 mm clearance from magnet inner face)
      14 fins at inter-magnet gap midpoints provide tangential location

    Retention lips at open end:
      lip tip r = 21.75 mm (0.5 mm inward from inner wall)
      arc = ±magnet_half_deg — one lip per magnet bay
      snap-in: tilt magnet ~15°, push deep end in first, outer edge snaps past lip
    """
    shell_inner_r = rotor_od / 2 - shell_wall_t    # 22.25 mm

    # ── Base shell: outer cylinder − inner cavity − shaft bore ───────────────
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
    clip_size = shell_inner_r + 5.0

    # ── 14 × 隔离肋 / Divider fins (tangential retention → creates visible bays) ──
    fin_r_outer = shell_inner_r                    # 22.25 mm — base at inner wall surface
    fin_r_inner = shell_inner_r - fin_protrusion   # 20.75 mm — fin tip

    fin_annulus = (
        Cylinder(
            radius=fin_r_outer + 0.05,
            height=fin_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=fin_r_inner - 0.05,
            height=fin_h + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    fin_upper_clip = (
        Rot(0, 0, +gap_half_deg)
        * Pos(0, clip_size / 2, fin_h / 2)
        * Box(2 * clip_size, clip_size, fin_h + 0.4)
    )
    fin_lower_clip = (
        Rot(0, 0, -gap_half_deg)
        * Pos(0, -clip_size / 2, fin_h / 2)
        * Box(2 * clip_size, clip_size, fin_h + 0.4)
    )
    fin_proto = fin_annulus - fin_upper_clip - fin_lower_clip

    for i in range(n_poles):
        angle = 360.0 * (i + 0.5) / n_poles   # midpoint of each inter-magnet gap
        solid = solid + Rot(0, 0, angle) * fin_proto

    # ── 14 × 保留唇 / Retention lips at open end (axial snap-in) ─────────────
    lip_r_outer = shell_inner_r                    # 22.25 mm
    lip_r_inner = shell_inner_r - lip_protrusion   # 21.75 mm

    lip_annulus = (
        Cylinder(
            radius=lip_r_outer + 0.05,
            height=retention_lip_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=lip_r_inner - 0.05,
            height=retention_lip_h + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    lip_upper_clip = (
        Rot(0, 0, +magnet_half_deg)
        * Pos(0, clip_size / 2, retention_lip_h / 2)
        * Box(2 * clip_size, clip_size, retention_lip_h + 0.4)
    )
    lip_lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, retention_lip_h / 2)
        * Box(2 * clip_size, clip_size, retention_lip_h + 0.4)
    )
    lip_proto = lip_annulus - lip_upper_clip - lip_lower_clip

    for i in range(n_poles):
        angle = 360.0 * i / n_poles   # at magnet center positions
        solid = solid + Rot(0, 0, angle) * lip_proto

    # ── 外圆边缘倒角 / Outer rim chamfers — prevent sharp edges cutting hands ──
    with BuildPart() as _ch:
        add(solid)
        # 开口端外圆 z=0 → C1.0（最容易割手的边缘）
        open_outer = [
            e for e in _ch.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - rotor_od / 2) < 0.4 and abs(e.center().Z) < 0.4
        ]
        if open_outer:
            chamfer(open_outer, length=1.0)
    with BuildPart() as _ch2:
        add(_ch.part)
        # 封闭端外圆 z=rotor_h → C0.5
        closed_outer = [
            e for e in _ch2.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - rotor_od / 2) < 0.4
               and abs(e.center().Z - rotor_h) < 0.4
        ]
        if closed_outer:
            chamfer(closed_outer, length=0.5)

    return _ch2.part


if __name__ == "__main__":
    import sys

    print("Building QDD rotor shell (v3 — divider fins + retention lips)...")
    print(f"  OD={rotor_od}mm  H={rotor_h}mm  wall={shell_wall_t}mm"
          f"  {n_poles} bays  gap={gap_deg:.2f}°  fin_protrusion={fin_protrusion}mm")

    shell = make_rotor_shell()

    bb = shell.bounding_box()
    print(f"  Volume : {shell.volume:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")

    assert shell.volume > 0, "❌ volume ≤ 0"
    assert abs(bb.size.X - rotor_od) < 1.0, f"X偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - rotor_h)  < 0.2, f"Z偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")

    out_dir = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    export_step(shell, str(out_dir / "rotor_shell.step"))
    print("  STEP → cache/rotor_shell.step ✓")

    # OCP 预览 — 底视图便于观察 14 个凹槽
    try:
        from ocp_vscode import Camera, show, set_port
        from ocp_vscode.comms import port_check
        from ocp_vscode.state import get_ports

        active_port = next((int(p) for p in get_ports() if port_check(int(p))), None)
        if active_port:
            set_port(active_port)
            show(shell, names=["rotor_shell_v3"], colors=["steelblue"],
                 reset_camera=Camera.BOTTOM)
            print("OCP: 底视图 (BOTTOM) — 可观察 14 个磁钢槽 + 隔离肋 ✓")
        else:
            print("OCP Viewer 未检测到")
    except Exception as e:
        print(f"OCP 跳过: {e}")
