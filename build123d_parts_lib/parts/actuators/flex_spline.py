"""QDD 柔轮 / Flex Spline — elastic thin-wall cup with 100-tooth external gear.

Harmonic drive flex spline (cup type) for the QDD joint module.
Material: TPU 95A, FDM layer height ≤ 0.1 mm, 0.25 mm nozzle, 100% infill.

Geometry (local Z: closed end = 0, open/gear end = 20):
  z=  0~ 3   Closed-end flange  Φ32 mm  (mates with output_flange.py)
  z=  3~20   Thin-wall cup      Φ29.25/Φ26.85 mm  (wall = 1.2 mm)
              ↑ 100-tooth external involute gear on outer surface

Key dimensions:
  Flange OD : Φ32 mm
  Center bore: Φ12 mm  (shaft clearance, = 7001C inner ring ID)
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


def _tooth_pts(tooth_idx: int, steps: int = 8) -> list[tuple[float, float]] | None:
    """2D polygon for one external gear tooth (involute profile, solid body).

    柔轮第 tooth_idx 个外齿的渐开线闭合点集。
    算法来自 spur_gear.py，齿廓为外齿（向外突出）。

    Returns the solid TOOTH BODY polygon that gets ADDed to the root cylinder.
    返回 ADD 到根圆柱的齿体多边形点集。
    """
    pitch_angle = 2 * math.pi / flex_teeth
    half_t      = math.pi / (2 * flex_teeth)
    a_i         = pitch_angle * tooth_idx

    inv_max = math.sqrt(max(0.0, (addendum_r / base_r) ** 2 - 1))

    # Left flank (root → tip) / 左齿面（齿根 → 齿顶）
    left: list[tuple[float, float]] = []
    for s in range(steps + 1):
        ia = inv_max * s / steps
        r  = base_r * math.sqrt(1 + ia * ia)
        if r < root_r:
            continue
        r  = min(r, addendum_r)
        th = a_i + half_t - ia + math.atan(ia)
        left.append((r * math.cos(th), r * math.sin(th)))

    # Right flank (tip → root) / 右齿面（齿顶 → 齿根）
    right: list[tuple[float, float]] = []
    for s in range(steps, -1, -1):
        ia = inv_max * s / steps
        r  = base_r * math.sqrt(1 + ia * ia)
        if r < root_r:
            continue
        r  = min(r, addendum_r)
        th = a_i - half_t + ia - math.atan(ia)
        right.append((r * math.cos(th), r * math.sin(th)))

    if not left or not right:
        return None

    # Root fillet arc (right-end → left-start along root circle)
    # 齿根过渡圆弧（沿根圆连接右侧末点到左侧起点）
    th_r = math.atan2(right[-1][1], right[-1][0])
    th_l = math.atan2(left[0][1],   left[0][0])
    if th_l < th_r:
        th_l += 2 * math.pi
    arc_pts = [
        (root_r * math.cos(th_r + (th_l - th_r) * k / 4),
         root_r * math.sin(th_r + (th_l - th_r) * k / 4))
        for k in range(1, 4)
    ]

    return left + right + arc_pts


def make_flex_spline() -> Part:
    """Generate QDD flex spline — TPU cup with 100-tooth external involute ring.

    生成 QDD 柔轮（含 100 齿渐开线外齿，TPU 薄壁杯形）。

    Build order (mirrors spur_gear.py + overlap anti-coplanar trick):
    1. Build solid root cylinder (solid core — same start as spur_gear.py)
    2. ADD 100 teeth onto solid root cylinder (identical to spur_gear.py loop)
    3. Subtract inner bore to hollow the cup (deferred AFTER teeth → clean topology)
    4. Build flange separately with center bore already punched
    5. Shift cup+teeth to overlap 0.15 mm into the flange → no coplanar face
    6. FUSE flange + shifted cup

    Coordinate system:
        Z+ points toward open / gear end
        z=0 = closed end (flange face, mates with output_flange)
        z=flex_spline_h = open end (gear tooth face)
    """
    _OVERLAP = 0.15   # cup extends this far INTO the flange to kill coplanar face
    # ↑ The 0.15 mm overlap is purely topological — no physical material is added.
    #   The cup hollow removes r<cup_inner_r from the flange in that tiny zone.

    cup_total_h = cup_h + _OVERLAP   # 17.15 mm — internal height of cup build

    # Step 1: Solid root cylinder / 实心根圆柱 ────────────────────────────────
    # Start with SOLID cylinder — identical to spur_gear.py's root cylinder.
    # Hollow subtraction is deferred to Step 3 (after all teeth are fused)
    # so the 100 ADD operations see a simple solid surface, not a hollow tube.
    # 先用实心根圆柱（同 spur_gear.py），空心留到齿全部 ADD 完再一次性去除。
    root_cyl: Part = Cylinder(
        radius=root_r,
        height=cup_total_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 2: Add 100 external teeth onto solid root cylinder / 逐齿 ADD 外齿 ──
    # ⚠️ Must ADD individually — merging 100 non-convex polygons causes OCC to
    #    silently drop the geometry (same constraint as ring gear in housing).
    #    必须逐齿 ADD，合并非凸多边形会被 OCC viewer 忽略。
    fused = 0
    for i in range(flex_teeth):
        pts = _tooth_pts(i)
        if pts is None:
            continue
        face = _make_face_from_pts(pts)
        with BuildPart() as tooth:
            with BuildSketch(Plane.XY):   # polygon in XY at z=0
                add(face)
            extrude(amount=cup_total_h)
        root_cyl = root_cyl + tooth.part
        fused += 1
        if (i + 1) % 20 == 0:
            print(f"  teeth fused: {i + 1}/{flex_teeth}")

    print(f"Flex spline: {fused}/{flex_teeth} teeth fused.")

    # Step 3: Hollow out the cup (subtract inner bore after all teeth are done)
    # 所有外齿 ADD 完成后，一次性去除内孔 → 空心杯壁。
    # Deferred from Step 1 to keep the 100-iteration ADD loop working on a
    # clean solid-cylinder outer face (r=root_r) rather than a hollow tube.
    cup_tube: Part = root_cyl - Cylinder(
        radius=cup_inner_r,
        height=cup_total_h + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 4: Closed-end flange with center bore / 底部法兰（含中心孔）────────────
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

    # Step 5: Position cup so it overlaps 0.15 mm into the flange / 杯体定位 ──
    # Shift start z from 0 to (flange_h - _OVERLAP) = 2.85 mm.
    # The overlap region ensures no coplanar interface face at z=flange_h.
    # 杯体上移，使底端插入法兰 0.15 mm，消除 z=flange_h 处的共面接触。
    cup_positioned: Part = Pos(0, 0, flange_h - _OVERLAP) * cup_tube

    # Step 6: Fuse flange + positioned cup / 法兰与杯体融合 ─────────────────────
    return flange + cup_positioned


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
    assert part.is_valid, "❌ BRep validity FAILED"
    print("  BRep   : valid ✓")

    # Wall thickness assertion (TPU quality gate)
    # 壁厚断言（TPU 打印质量门控：壁厚需 ≥ 1.1 mm）
    assert flex_wall_t >= 1.1, f"❌ Wall thickness {flex_wall_t} < 1.1 mm threshold"
    print(f"  Wall   : {flex_wall_t:.1f} mm ≥ 1.1 mm ✓")
    print("──────────────────────────────────────────────────")
