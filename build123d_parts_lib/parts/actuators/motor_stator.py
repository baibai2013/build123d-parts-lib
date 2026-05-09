"""QDD 电机定子 / Motor Stator — outrunner BLDC 12-slot stator for QDD joint module.

Simplified engineering model (no winding geometry, no laminations).
Outer cylinder Φ40 × 10 mm with 12 radial slots cut from the OD inward,
plus a central shaft-clearance bore Φ14.

Geometry (local Z: rear face = 0, front face = stator_h):
  Tooth-tip OD  : Φ40 mm  (faces outward toward rotor magnets)
  Height        : 10 mm
  Yoke OD       : Φ28 mm  (back-iron connecting tooth bases, inner slot boundary)
  Central bore  : Φ14 mm  (shaft clearance)
  Slots         : 12 × (6.0 mm deep × 2.5 mm wide), equal angular spacing

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC stator geometry
"""
from __future__ import annotations

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
    PolarLocations,
    Rot,
    chamfer,
    export_step,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ──────────────────────────────────────────────────
stator_od    = 40.0   # tooth-tip outer diameter  mm
stator_h     = 10.0   # axial height  mm
yoke_od      = 28.0   # back-iron outer diameter  mm  (= inner slot radius × 2)
stator_id    = 14.0   # center bore diameter (shaft clearance)  mm
n_slots      = 12     # number of stator slots (= number of teeth)
slot_depth   = (stator_od - yoke_od) / 2   # 6.0 mm radial tooth height
slot_opening = 2.5    # tangential slot width  mm

GEOMETRY_INVARIANTS = {
    "stator_od":   stator_od,
    "stator_h":    stator_h,
    "yoke_od":     yoke_od,
    "stator_id":   stator_id,
    "n_slots":     n_slots,
    "slot_depth":  slot_depth,
}


def make_motor_stator() -> Part:
    """Generate QDD outrunner BLDC motor stator (4010, 12-slot, OD=40×H=10 mm).

    Geometry: solid outer cylinder − central bore − 12 radial slots from OD inward.
    """
    slot_center_r = stator_od / 2 - slot_depth / 2   # 17.0 mm from axis

    with BuildPart() as p:
        # 外圆柱体 / Outer solid cylinder
        Cylinder(
            radius=stator_od / 2,
            height=stator_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 中心贯通孔（轴间隙）/ Central through-bore for shaft clearance
        Hole(radius=stator_id / 2)

        # 12 径向槽从外径向内切（切出 12 个齿）/ 12 radial slots cut from OD inward
        with PolarLocations(radius=slot_center_r, count=n_slots):
            Box(
                slot_depth + 0.5,       # radial extent + ε (ensures clean OD cut)
                slot_opening,           # tangential slot width
                stator_h + 0.2,         # axial + ε
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # 外缘倒角 C0.5 / Tooth-tip outer-edge chamfer C0.5
        try:
            rim_edges = [
                e for e in p.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - stator_od / 2) < 0.3
            ]
            if rim_edges:
                chamfer(rim_edges, length=0.5)
        except Exception:
            pass   # complex boolean history may prevent chamfer — non-critical

    return p.part


def make_stator_winding() -> Compound:
    """Generate simplified copper coil winding for the 12-slot stator.

    Returns a Compound of 36 copper pieces:
      - 12 slot conductors (one per slot, axial rectangular prisms filling the slot)
      - 12 top end-turns   (one per tooth, 30° annular sector above z=stator_h)
      - 12 bottom end-turns (one per tooth, 30° annular sector below z=0)

    Geometry origin matches make_motor_stator(): z=0 at rear face.
    """
    insulation    = 0.2                                   # mm per side — slot liner gap
    cu_tang       = slot_opening - 2 * insulation         # 2.1 mm tangential copper width
    cu_radial_c   = slot_depth - 0.5                      # 5.5 mm radial copper depth
    end_h         = 3.0                                   # axial end-turn overhang  mm
    slot_center_r = stator_od / 2 - slot_depth / 2       # 17.0 mm
    et_outer_R    = slot_center_r + cu_radial_c / 2       # 19.75 mm
    et_inner_R    = slot_center_r - cu_radial_c / 2       # 14.25 mm

    parts: list = []

    # ── 12 slot conductors ────────────────────────────────────────────────────
    for j in range(n_slots):
        angle = j * 30.0 + 15.0      # slot centre angle  (between tooth j and j+1)
        conductor = (
            Rot(0, 0, angle)
            * Pos(slot_center_r, 0, stator_h / 2)
            * Box(
                cu_radial_c, cu_tang, stator_h,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
        )
        parts.append(conductor)

    # ── End-turn prototype: 30° annular sector (pure Algebra mode) ──────────
    # Same half-plane clip strategy as make_arc_magnet() — proven approach.
    clip_size = et_outer_R + 5.0
    clip_h    = end_h + 0.2
    et_half_deg = 15.0    # half of 30° arc span

    _et_annulus = (
        Cylinder(et_outer_R + 0.05, end_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Cylinder(et_inner_R - 0.05, end_h + 0.2,
                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    _et_upper = (
        Rot(0, 0, +et_half_deg)
        * Pos(0, clip_size / 2, end_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    _et_lower = (
        Rot(0, 0, -et_half_deg)
        * Pos(0, -clip_size / 2, end_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    et_proto = _et_annulus - _et_upper - _et_lower

    # ── 12 top + 12 bottom end-turns ─────────────────────────────────────────
    for k in range(n_slots):
        tooth_angle = k * 30.0                    # tooth k is at this angle
        for z_base in (stator_h, -end_h):
            end_turn = Pos(0, 0, z_base) * Rot(0, 0, tooth_angle - 15.0) * et_proto
            parts.append(end_turn)

    return Compound(children=parts)


if __name__ == "__main__":
    print("Building QDD motor stator ...")
    print(f"  Tooth-tip OD={stator_od} mm  H={stator_h} mm")
    print(f"  Yoke OD={yoke_od} mm  Bore ID={stator_id} mm  Slots={n_slots}")
    print(f"  Slot: {slot_depth} mm deep × {slot_opening} mm wide")

    part = make_motor_stator()

    winding = make_stator_winding()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, winding,
             names=["motor_stator", "stator_winding"],
             colors=["steelblue", "goldenrod"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 电机定子 + 铜线绕组 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP ─────────────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "motor_stator.step"
    export_step(part, str(step_path))
    winding_path = out_dir / "stator_winding.step"
    export_step(winding, str(winding_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── motor_stator 尺寸汇总 ────────────────────────────")
    print(f"  Volume : {vol:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    assert vol > 0, "❌ volume ≤ 0"
    assert abs(bb.size.X - stator_od) < 1.0, f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - stator_h)  < 0.2, f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")
    print("────────────────────────────────────────────────────")

    bb_w = winding.bounding_box()
    print(f"\n── stator_winding 尺寸汇总 ──────────────────────────")
    print(f"  Volume : {winding.volume:.1f} mm³")
    print(f"  BBox   : {bb_w.size.X:.2f} × {bb_w.size.Y:.2f} × {bb_w.size.Z:.2f} mm")
    print(f"  STEP   : {winding_path}")
    assert winding.volume > 0, "❌ winding volume ≤ 0"
    assert abs(bb_w.size.X - stator_od) < 1.5, f"winding X 偏差: {bb_w.size.X:.2f}"
    assert abs(bb_w.size.Z - (stator_h + 6.0)) < 1.0, f"winding Z 偏差: {bb_w.size.Z:.2f}"
    print("  BRep + BBox ✓")
    print("────────────────────────────────────────────────────")
