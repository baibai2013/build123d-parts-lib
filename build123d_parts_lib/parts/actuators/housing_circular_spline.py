"""QDD 主外壳 / 刚轮一体件 — housing with integrated circular spline.

Housing + circular spline (ring gear) one-piece printed part for the
QDD harmonic drive joint module.

Geometry (local Z: output end=0, motor end=30):
  z=  0~ 8  Bearing seat Φ28 H7  (7001C angular contact pair)
  z=  8~28  Ring gear bore Φ30   (102-tooth internal gear, m=0.3)
  z= 28~30  Top rim / motor-end land (no bore)
  Output face (z=0):  6× M2 heat-insert holes PCD 34 mm (robot link mount)
  Motor face (z=30):  4× M3 heat-insert holes PCD 39 mm (motor endcap conn.)

Material: PA12 SLS (recommended) / ASA FDM (fallback)
Key tolerances:
  Bearing seat Φ28 H7 : +0.021/0 mm
  Ring gear tooth      : ±0.05 mm (SLS resolution limit)
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
    GeomType,
    Part,
    Plane,
    Pos,
    Wire,
    add,
    chamfer,
    export_step,
    export_stl,
    extrude,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ─────────────────────────────────────────────
housing_od      = 45.0   # outer diameter  mm
housing_h       = 30.0   # total height    mm

# 输出端轴承座（7001C 角接触，H7 压配）/ Bearing seat (7001C, H7 press fit)
bearing_seat_d  = 28.0   # mm — 7001C outer diameter
bearing_seat_h  =  8.0   # mm — 7001C width  (= ring zone start z)

# 刚轮区域 / Ring gear zone
ring_zone_z0    =  bearing_seat_h          # 8 mm from output face
ring_zone_z1    =  housing_h - 2.0         # 28 mm (2 mm top rim)
ring_zone_h     =  ring_zone_z1 - ring_zone_z0  # 20 mm

# 刚轮齿形参数（谐波减速器刚轮）/ Ring gear (circular spline) tooth parameters
ring_teeth      = 102
ring_module     =   0.3  # gear module mm
pressure_angle  =  20.0  # degrees (ISO standard)

# M3 热嵌铜螺母孔（连接电机端盖）/ M3 heat-insert holes (motor endcap connection)
m3_pcd          = 39.0   # PCD mm
m3_count        =  4
m3_insert_d     =  4.6   # drill diameter for M3×5 insert mm
m3_depth        =  5.5   # blind hole depth mm

# M2 热嵌铜螺母孔（机器人安装面）/ M2 heat-insert holes (robot link mount)
m2_pcd          = 34.0   # PCD mm
m2_count        =  6
m2_insert_d     =  3.5   # drill diameter for M2×3.5 insert mm
m2_depth        =  4.0   # blind hole depth mm

# ── 刚轮几何计算 / Ring gear geometry (derived) ───────────────────────────
pitch_r    = ring_module * ring_teeth / 2              # 15.3 mm
addendum_r = pitch_r - ring_module                     # 15.0 mm  (tip circle, inner)
dedendum_r = pitch_r + 1.25 * ring_module              # 15.675 mm (root circle, outer)
base_r     = pitch_r * math.cos(math.radians(pressure_angle))  # 14.378 mm

# ── OCC 平面（齿槽 Face 构造用）/ XY plane for OCC face construction ──────
_XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))


def _make_face_from_pts(pts_2d: list[tuple[float, float]]) -> Face:
    """Closed 2D polygon → planar OCC Face. / 闭合 2D 多边形 → XY 平面 Face。"""
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(_XY_PLANE, wire.wrapped, True).Face())


def _tooth_gap_pts(
    tooth_idx: int,
    steps: int = 12,
) -> list[tuple[float, float]] | None:
    """2D polygon for one tooth gap of the ring gear (involute profile).

    刚轮第 tooth_idx 个齿槽的渐开线闭合点集。
    算法同 internal_gear.py，参数从模块级变量读取。
    """
    pitch_angle = 2 * math.pi / ring_teeth
    half_t      = math.pi / (2 * ring_teeth)
    a_i         = pitch_angle * tooth_idx

    if pitch_r <= base_r:
        return None
    ia_pitch  = math.sqrt((pitch_r / base_r) ** 2 - 1)
    inv_pitch = ia_pitch - math.atan(ia_pitch)

    _SLACK  = 0.05 * max(dedendum_r - addendum_r, 0.1)
    r_inner = max(base_r, addendum_r - _SLACK)
    r_outer = dedendum_r + _SLACK
    if r_inner >= r_outer:
        return None

    ia_inner = math.sqrt(max(0.0, (r_inner / base_r) ** 2 - 1))
    ia_outer = math.sqrt((r_outer / base_r) ** 2 - 1)

    # 左侧齿槽边（渐开线，内→外）/ Left flank (inner→outer)
    left: list[tuple[float, float]] = []
    for s in range(steps + 1):
        t   = s / steps
        ia  = ia_inner + (ia_outer - ia_inner) * t
        r   = base_r * math.sqrt(1 + ia * ia)
        inv_a = ia - math.atan(ia)
        th  = a_i + half_t + (inv_a - inv_pitch)
        left.append((r * math.cos(th), r * math.sin(th)))

    # 右侧齿槽边（渐开线，外→内）/ Right flank (outer→inner)
    right: list[tuple[float, float]] = []
    for s in range(steps, -1, -1):
        t   = s / steps
        ia  = ia_inner + (ia_outer - ia_inner) * t
        r   = base_r * math.sqrt(1 + ia * ia)
        inv_a = ia - math.atan(ia)
        th  = a_i - half_t - (inv_a - inv_pitch)
        right.append((r * math.cos(th), r * math.sin(th)))

    # 齿根过渡圆弧（外圈 r_outer）/ Root arc at r_outer
    th_L_end   = a_i + half_t + (ia_outer - math.atan(ia_outer) - inv_pitch)
    th_R_start = a_i - half_t - (ia_outer - math.atan(ia_outer) - inv_pitch)
    delta_out  = th_L_end - th_R_start
    root_arc   = [
        (r_outer * math.cos(th_L_end - delta_out * k / 4),
         r_outer * math.sin(th_L_end - delta_out * k / 4))
        for k in range(1, 4)
    ]

    # 齿顶过渡圆弧（内圈 r_inner）/ Addendum arc at r_inner
    inv_inner  = ia_inner - math.atan(ia_inner)
    th_L_start = a_i + half_t + (inv_inner - inv_pitch)
    th_R_end   = a_i - half_t - (inv_inner - inv_pitch)
    delta_in   = th_L_start - th_R_end
    add_arc    = [
        (r_inner * math.cos(th_R_end + delta_in * k / 4),
         r_inner * math.sin(th_R_end + delta_in * k / 4))
        for k in range(1, 4)
    ]

    # 闭合顺序: left (内→外) + root_arc (外弧) + right (外→内) + add_arc (内弧)
    return left + root_arc + right + add_arc


def make_housing_circular_spline() -> Part:
    """Generate QDD housing with integrated circular spline ring gear.

    生成 QDD 外壳/刚轮一体件（含 102 齿渐开线内齿刚轮）。

    Coordinate system:
        Z+ points toward motor end
        z=0 = output face (bearing / output flange interface)
        z=housing_h = motor face (motor endcap interface)
    """
    # Step 1: 主外壳圆柱体 / Outer housing cylinder ─────────────────────────
    housing: Part = Cylinder(
        radius=housing_od / 2,
        height=housing_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 2: 输出端轴承座孔 / Bearing seat bore (z=0~8) ─────────────────────
    housing = housing - Cylinder(
        radius=bearing_seat_d / 2,
        height=bearing_seat_h + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 3: 刚轮区齿顶圆初始孔 / Ring gear tip-circle bore (z=8~28) ─────────
    housing = housing - (
        Pos(0, 0, ring_zone_z0) * Cylinder(
            radius=addendum_r,
            height=ring_zone_h + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # Step 4: 逐齿槽减材构建内齿刚轮 / Subtract 102 tooth gaps one by one ─────
    # ⚠️ Each gap MUST be subtracted individually — merging all 102 non-convex
    #    polygons into one face causes OCC to silently drop the geometry.
    #    必须逐齿减材，合并大非凸多边形会被 OCC viewer 忽略。
    cut = 0
    for i in range(ring_teeth):
        pts = _tooth_gap_pts(i)
        if pts is None:
            continue
        face = _make_face_from_pts(pts)
        with BuildPart() as slot:
            with BuildSketch(Plane.XY.offset(ring_zone_z0)):
                add(face)
            extrude(amount=ring_zone_h)
        housing = housing - slot.part
        cut += 1
        if (i + 1) % 20 == 0:
            print(f"  tooth gaps subtracted: {i + 1}/{ring_teeth}")

    print(f"Ring gear: {cut}/{ring_teeth} tooth gaps subtracted.")

    # Step 5: M3 热嵌铜螺母孔（电机端面）/ M3 heat-insert holes on motor face ──
    for k in range(m3_count):
        ang = math.radians(k * 360 / m3_count)
        x   = (m3_pcd / 2) * math.cos(ang)
        y   = (m3_pcd / 2) * math.sin(ang)
        housing = housing - (
            Pos(x, y, housing_h - m3_depth) * Cylinder(
                radius=m3_insert_d / 2,
                height=m3_depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )

    # Step 6: M2 热嵌铜螺母孔（输出端面）/ M2 heat-insert holes on output face ─
    # Offset 30° from M3 pattern for visual clarity in assembly.
    for k in range(m2_count):
        ang = math.radians(k * 360 / m2_count + 30)
        x   = (m2_pcd / 2) * math.cos(ang)
        y   = (m2_pcd / 2) * math.sin(ang)
        housing = housing - (
            Pos(x, y, 0) * Cylinder(
                radius=m2_insert_d / 2,
                height=m2_depth + 0.1,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        )

    # Step 7: 倒角 / Chamfers ──────────────────────────────────────────────────
    # Edges must be queried from within the BuildPart context (after add) so
    # OCC topology references stay valid. Re-query after each chamfer call.
    # 边必须从 BuildPart 上下文内（add 之后）查询，OCC 拓扑引用才有效。
    # 每次 chamfer 后重新查询，避免引用失效。

    def _pick(ctx: "BuildPart", z_nom: float, r_nom: float,
              z_tol: float = 0.15, r_tol: float = 0.4) -> list:
        """Select circular edges by Z-position and radius from current context."""
        return [
            e for e in ctx.edges().filter_by(GeomType.CIRCLE)
            if abs(e.center().Z - z_nom) < z_tol
            and abs(e.radius - r_nom) < r_tol
        ]

    with BuildPart() as _ch:
        add(housing)

        # 小特征先倒，再做大外圆棱，避免外圆棱改变拓扑后小孔失败
        # Small features first, then outer rims — avoids topology change invalidating small holes

        # 轴承座孔入口 C0.5（引导 7001C 压入）
        # Bearing bore entry C0.5 (guide 7001C press-fit)
        bore_entry = _pick(_ch, 0.0, bearing_seat_d / 2)
        if bore_entry:
            chamfer(bore_entry, length=0.5)

        # M2 插入孔开口 C0.3（对齐铜螺母）
        # M2 heat-insert openings C0.3 (align brass insert)
        m2_openings = _pick(_ch, 0.0, m2_insert_d / 2, r_tol=0.2)
        if m2_openings:
            chamfer(m2_openings, length=0.3)

        # M3 插入孔开口 C0.3（对齐铜螺母）— 必须在电机面外圆棱前完成
        # M3 heat-insert openings C0.3 — must run before motor rim chamfer
        m3_openings = _pick(_ch, housing_h, m3_insert_d / 2, r_tol=0.2)
        if m3_openings:
            chamfer(m3_openings, length=0.3)

        # 输出面外圆棱 C1.0（M2 孔距外壁 3.75mm，空间充足）
        # Output face outer rim C1.0 (M2 holes leave 3.75mm clearance to OD)
        e_output_rim = _pick(_ch, 0.0, housing_od / 2)
        if e_output_rim:
            chamfer(e_output_rim, length=1.0)

        # 电机面外圆棱跳过：M3 孔(PCD39)+外壁=0.7mm，M3 C0.3 已消耗壁厚，
        # 与外圆棱倒角叠加超限（0.3+0.5>0.7）；电机面由端盖遮蔽，无需此倒角。
        # Motor face outer rim SKIPPED: M3 holes at PCD39 leave 0.7mm wall;
        # M3 C0.3 + outer C0.5 would exceed wall (0.8mm > 0.7mm); face is
        # covered by motor_endcap_front so the sharp edge is not exposed.

    return _ch.part


if __name__ == "__main__":
    print("Building QDD housing / circular spline ...")
    print(f"  Ring gear: m={ring_module}, z={ring_teeth}, "
          f"pitch_d={2 * pitch_r:.2f} mm")
    print(f"  addendum_r={addendum_r:.3f}  dedendum_r={dedendum_r:.3f}  "
          f"base_r={base_r:.3f}  mm")

    part = make_housing_circular_spline()

    # ── OCP 预览 / OCP preview ────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(
            part,
            names=["housing_circular_spline"],
            colors=["steelblue"],
            reset_camera=Camera.ISO,
        )
        print("OCP Viewer: 主外壳/刚轮一体件 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP + STL / Export STEP + STL ──────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "housing_circular_spline.step"
    stl_path  = out_dir / "housing_circular_spline.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── housing_circular_spline 尺寸汇总 ──────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.1f} cm³)")
    print(f"  BBox   : {bb.size.X:.1f} × {bb.size.Y:.1f} × {bb.size.Z:.1f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    print("  BRep   : valid ✓")
    print("──────────────────────────────────────────────────────")
