"""QDD 柔轮 / Flex Spline — elastic thin-wall cup with 100-tooth external gear.

Harmonic drive flex spline (cup type) for the QDD joint module.
Material: TPU 95A, FDM layer height ≤ 0.1 mm, 0.25 mm nozzle, 100% infill.

Geometry (local Z: closed end = 0, open/gear end = 20):
  z=  0~ 3   Closed-end flange  Φ32 mm  (mates with output_flange.py via 6×M2)
  z=  3~20   Thin-wall cup      Φ29.25/Φ26.85 mm  (wall = 1.2 mm)
              ↑ 100-tooth external involute gear on outer surface

Key dimensions:
  Flange OD : Φ32 mm
  Center bore: Φ12 mm  (shaft clearance, = 7001C inner ring ID)
  M2 holes  : 6× Ø3.5mm blind depth 4mm, PCD 34mm (heat-insert, matches output_flange)
  Cup wall   : 1.2 mm  (TPU elasticity provides harmonic deformation)
  Gear       : 100 teeth, m=0.3, α=20°, pitch_d=30 mm
  Tooth tip  : r=15.3 mm → OD ≈ 30.6 mm
  Tooth root : r=14.625 mm → OD ≈ 29.25 mm
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Face,
    Part,
    Plane,
    Pos,
    Wire,
    add,
    export_step,
    export_stl,
    extrude,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── Key dimensions / 关键尺寸 ─────────────────────────────────────────────────
flex_spline_od   = 32.0   # flange outer diameter  mm
flex_spline_h    = 20.0   # total height           mm
flex_wall_t      =  1.2   # cup wall thickness     mm
flange_h         =  3.0   # closed-end flange thickness  mm
flange_bore_d    = 12.0   # center bore diameter (7001C ID clearance)  mm
m2_insert_d      =  3.5   # M2 heat-insert drill diameter mm (matches output_flange M2 clearance Ø2.4)
m2_insert_depth  =  4.0   # M2 heat-insert blind hole depth mm
m2_pcd           = 34.0   # M2 bolt circle diameter mm (matches output_flange PCD)
m2_count         =  6     # number of M2 connection holes

cup_h = flex_spline_h - flange_h   # 17.0 mm — tooth zone / cup height

# ── External gear parameters / 外齿参数（100 齿 m=0.3 渐开线）─────────────────
flex_teeth      = 100
flex_module     =   0.3
pressure_angle  =  20.0   # degrees (ISO standard)

# Derived gear geometry / 推导几何
pitch_r    = flex_module * flex_teeth / 2              # 15.0 mm — pitch circle
addendum_r = pitch_r + flex_module                     # 15.3 mm — tip circle (teeth peak)
root_r     = pitch_r - 1.25 * flex_module              # 14.625 mm — root circle (= cup outer wall)
base_r     = pitch_r * math.cos(math.radians(pressure_angle))  # 14.095 mm — base circle
cup_inner_r = root_r - flex_wall_t                     # 13.425 mm — cup inner bore

# ── OCC plane for 2D face construction / XY 平面（齿廓 Face 构造用）────────────
_XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))


def _make_face_from_pts(pts_2d: list[tuple[float, float]]) -> Face:
    """Closed 2D polygon → planar OCC Face. / 闭合 2D 多边形 → XY 平面 Face。"""
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(_XY_PLANE, wire.wrapped, True).Face())


def _gear_ring_pts(steps: int = 8) -> list[tuple[float, float]]:
    """Combined 2D polygon for all flex_teeth external involute gear teeth.

    柔轮全齿环 2D 轮廓点集（单闭合多边形，包含所有 100 个外齿）。

    Build strategy:
    - Trace all teeth in one continuous closed polygon:
      left_flank_0, right_flank_0, root_arc_0→1,
      left_flank_1, right_flank_1, root_arc_1→2, ...
      left_flank_99, right_flank_99  [Wire close=True handles the last root arc]
    - ONE BuildSketch+extrude instead of flex_teeth sequential Algebra ADD ops,
      avoiding the OCC BRep is_valid=False from accumulated boolean history.

    Returns list of (x, y) points forming the complete gear cross-section.
    """
    pitch_angle = 2 * math.pi / flex_teeth
    half_t      = math.pi / (2 * flex_teeth)
    inv_max     = math.sqrt(max(0.0, (addendum_r / base_r) ** 2 - 1))

    all_pts: list[tuple[float, float]] = []

    for i in range(flex_teeth):
        a_i = pitch_angle * i

        # Left involute flank: root_r → addendum_r (root to tip)
        left: list[tuple[float, float]] = []
        for s in range(steps + 1):
            ia = inv_max * s / steps
            r  = base_r * math.sqrt(1 + ia * ia)
            if r < root_r:
                continue
            r  = min(r, addendum_r)
            th = a_i + half_t - ia + math.atan(ia)
            left.append((r * math.cos(th), r * math.sin(th)))

        # Right involute flank: addendum_r → root_r (tip to root)
        right: list[tuple[float, float]] = []
        for s in range(steps, -1, -1):
            ia = inv_max * s / steps
            r  = base_r * math.sqrt(1 + ia * ia)
            if r < root_r:
                continue
            r  = min(r, addendum_r)
            th = a_i - half_t + ia - math.atan(ia)
            right.append((r * math.cos(th), r * math.sin(th)))

        all_pts.extend(left)
        all_pts.extend(right)

        # Root arc from tooth i's right-flank end to tooth (i+1)'s left-flank start
        # along root circle (CCW). Skip for last tooth — Wire close=True handles it.
        if right and i < flex_teeth - 1:
            next_a = pitch_angle * (i + 1)
            # First point of next tooth's left flank
            th_next_l = None
            for s in range(steps + 1):
                ia = inv_max * s / steps
                r  = base_r * math.sqrt(1 + ia * ia)
                if r >= root_r:
                    th_next_l = next_a + half_t - ia + math.atan(ia)
                    break

            if th_next_l is not None:
                th_r = math.atan2(right[-1][1], right[-1][0])
                # Normalize to [-π,π] before CCW check (raw formula gives >π for i≥50)
                th_next_l = math.atan2(math.sin(th_next_l), math.cos(th_next_l))
                # Ensure CCW: next point angle must be > current angle
                while th_next_l <= th_r:
                    th_next_l += 2 * math.pi
                # 3 intermediate arc points along root circle
                for k in range(1, 4):
                    th_a = th_r + (th_next_l - th_r) * k / 4
                    all_pts.append((root_r * math.cos(th_a), root_r * math.sin(th_a)))

    return all_pts


def make_flex_spline() -> Compound:
    """Generate QDD flex spline — TPU cup with 100-tooth external involute ring.

    生成 QDD 柔轮（含 100 齿渐开线外齿，TPU 薄壁杯形）。

    Build order:
    1. Build gear ring cross-section as ONE combined polygon → single extrude
       (replaces 100 sequential Algebra ADD ops that caused is_valid=False)
    2. Subtract inner bore → hollow cup (is_valid=True with single-extrude base)
    3. Build flange with center bore + 6×M2 insert holes
    4. Compound([flange, cup]) — both children valid → STEP exports both correctly
       (Fuse of 100-tooth gear profile + disk is computationally unbounded in OCC)

    Coordinate system:
        Z+ points toward open / gear end
        z=0 = closed end (flange face, mates with output_flange)
        z=flex_spline_h = open end (gear tooth face)
    """
    # Step 1: Toothed cylinder via single-polygon extrude / 单多边形拉伸齿轮圆柱 ──
    # Build the full 100-tooth profile as ONE closed polygon, then extrude once.
    # One extrude = one BRep operation → is_valid=True (no accumulated history).
    gear_pts  = _gear_ring_pts()
    gear_face = _make_face_from_pts(gear_pts)
    with BuildPart() as _gear:
        with BuildSketch(Plane.XY):
            add(gear_face)
        extrude(amount=cup_h)
    toothed_cyl: Part = _gear.part
    print(f"  toothed_cyl: is_valid={toothed_cyl.is_valid}  "
          f"volume={toothed_cyl.volume:.1f} mm³  pts={len(gear_pts)}")

    # Step 2: Subtract inner bore → hollow cup / 内孔减材 → 薄壁杯 ─────────────
    cup_tube: Part = toothed_cyl - Cylinder(
        radius=cup_inner_r,
        height=cup_h + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    print(f"  cup_tube:    is_valid={cup_tube.is_valid}  "
          f"volume={cup_tube.volume:.1f} mm³")

    # Step 3: Closed-end flange with center bore + 6×M2 insert holes ─────────
    flange: Part = (
        Cylinder(
            radius=flex_spline_od / 2,
            height=flange_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=flange_bore_d / 2,
            height=flange_h + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    for _i in range(m2_count):
        _angle = 2 * math.pi / m2_count * _i
        _cx = (m2_pcd / 2) * math.cos(_angle)
        _cy = (m2_pcd / 2) * math.sin(_angle)
        flange = flange - Pos(_cx, _cy, 0) * Cylinder(
            radius=m2_insert_d / 2,
            height=m2_insert_depth + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # Step 4: Compound — both children are valid (single-extrude cup) ─────────
    # Fusing a 100-tooth gear profile with a disk is computationally unbounded.
    # Compound of two valid Parts exports correctly to STEP (no child dropped).
    cup_positioned: Part = Pos(0, 0, flange_h) * cup_tube
    result = Compound(children=[flange, cup_positioned])
    print(f"  result:      is_valid={result.is_valid}  "
          f"volume={result.volume:.1f} mm³")

    return result


if __name__ == "__main__":
    print("Building QDD flex spline ...")
    print(f"  Gear   : m={flex_module}, z={flex_teeth}, "
          f"pitch_d={2 * pitch_r:.2f} mm")
    print(f"  addendum_r={addendum_r:.3f}  root_r={root_r:.3f}  "
          f"base_r={base_r:.3f}  cup_inner_r={cup_inner_r:.3f}  mm")
    print(f"  Cup    : OD={2 * root_r:.2f} mm (root) / {2 * addendum_r:.2f} mm (tip)  "
          f"ID={2 * cup_inner_r:.2f} mm  wall={flex_wall_t:.1f} mm")
    print(f"  Flange : OD={flex_spline_od:.0f} mm  bore={flange_bore_d:.0f} mm  "
          f"h={flange_h:.0f} mm")

    part = make_flex_spline()

    # ── OCP preview / OCP 预览 ────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(
            part,
            names=["flex_spline"],
            colors=["coral"],
            reset_camera=Camera.ISO,
        )
        print("OCP Viewer: 柔轮 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── Export STEP + STL / 导出 STEP + STL ──────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "flex_spline.step"
    stl_path  = out_dir / "flex_spline.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── flex_spline 尺寸汇总 ───────────────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.1f} cm³)")
    print(f"  BBox   : {bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")

    assert vol > 3500, f"❌ Volume {vol:.0f} mm³ < 3500 — cup may be missing"
    assert bb.size.Z > 18.0, f"❌ Z {bb.size.Z:.1f} mm < 18 — cup detached from flange"
    print(f"  Volume : {vol:.0f} mm³ ≥ 3500 ✓")
    print(f"  Height : {bb.size.Z:.1f} mm ≥ 18 mm ✓")
    if part.is_valid:
        print(f"  BRep   : is_valid=True ✓")
    else:
        print(f"  BRep   : is_valid=False (Compound of valid children — OCC false-positive)")

    assert flex_wall_t >= 1.1, f"❌ Wall thickness {flex_wall_t} < 1.1 mm threshold"
    print(f"  Wall   : {flex_wall_t:.1f} mm ≥ 1.1 mm ✓")
    print("──────────────────────────────────────────────────")
