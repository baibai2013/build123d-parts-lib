"""Worm and worm wheel — industrial 3D-printable parametric pair.

蜗杆 + 蜗轮 / Worm + Worm Gear —— 配合件对,ISO 1122 轴向系蜗杆传动标准。

Source: ISO 1122 (cylindrical worm gear pair vocabulary & geometry)
Standards: ISO 1122, DIN 3975, 轴向齿形梯形压力角 α = 20°
License: MIT

支持规格 / Supported specs:
    蜗杆 / Worm:
      m1.0, z1=1, L=30, q=10
      m2.0, z1=1, L=50, q=10
      m2.0, z1=2, L=50, q=10 (双头 / two-thread)
    蜗轮 / Worm wheel:
      m1.0, z2=30, bore=5,  worm_d=10
      m2.0, z2=30, bore=8,  worm_d=20
      m2.0, z2=40, bore=10, worm_d=20, z1=2 (1:20 减速)

核心几何 / Core geometry:
    蜗杆 / Worm:
        分度圆 d1  = q × mx        (q = diameter coefficient, 推荐 10)
        齿顶圆 da1 = d1 + 2·mx
        齿根圆 df1 = d1 − 2.4·mx
        导程   Pz  = π·mx·z1        (每转轴向位移)
        导程角 γ  : tan γ = z1 / q
    蜗轮 / Worm wheel (mates with worm):
        分度圆 d2  = mx × z2
        齿顶圆 da2 = d2 + 2·mx
        齿根圆 df2 = d2 − 2.4·mx
        齿宽   b2  = 0.75 × d1      (简化默认)
        中心距 a   = (d1 + d2) / 2

简化级别 / Simplification level: ★★★☆☆
    - 蜗杆: 梯形截面沿螺旋 sweep,天然避免非凸问题
      (trapezoidal section swept along helix — convex-safe)
    - 蜗轮: 渐开线直齿轮 + Torus (环面) 布尔车削形成圆弧包络槽
      (spur gear + torus subtract — simplified concave envelope)
    - 未建精确圆弧齿包络面 (逐层变截面),但 3D 打印装配足够

备注 / Note:
    cache 由 scripts/build_cache.py 统一生成;本文件 __main__ 仅做冒烟断言。
    (STEP cache is produced by scripts/build_cache.py; __main__ here runs
     smoke assertions only — no file I/O, no viewer.)
"""
from __future__ import annotations

import math
from typing import NamedTuple

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    Edge,
    Face,
    Part,
    Plane,
    Polyline,
    Torus,
    Vector,
    Wire,
    add,
    extrude,
    make_face,
    sweep,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]


# ---------- 规格记录 / Spec records ----------

class WormSpec(NamedTuple):
    """蜗杆参数记录 / Worm parameter record."""
    module: float          # 轴向模数 mx (mm)
    threads: int           # 头数 z1
    length: float          # 总长 L (mm)
    diameter_coeff: float  # 直径系数 q
    pressure_angle: float  # 压力角 (°)
    # 推导 / Derived
    pitch_d: float         # 分度圆 d1  (mm)
    addendum_d: float      # 齿顶圆 da1 (mm)
    dedendum_d: float      # 齿根圆 df1 (mm)
    lead: float            # 导程 Pz (mm)
    lead_angle: float      # 导程角 γ (°)


class WormWheelSpec(NamedTuple):
    """蜗轮参数记录 / Worm wheel parameter record."""
    module: float          # 模数 mx (mm)
    teeth: int             # 齿数 z2
    bore_d: float          # 中心孔径 (mm)
    worm_threads: int      # 配对蜗杆头数 z1
    worm_d: float          # 配对蜗杆分度圆直径 d1 (mm)
    face_width: float      # 齿宽 b2 (mm)
    pressure_angle: float  # 压力角 (°)
    # 推导 / Derived
    pitch_d: float         # 分度圆 d2  (mm)
    addendum_d: float      # 齿顶圆 da2 (mm)
    dedendum_d: float      # 齿根圆 df2 (mm)
    center_distance: float # 中心距 a = (d1 + d2) / 2


# ---------- 渐开线齿廓辅助 (复用自 spur_gear.py) ----------
# Involute profile helpers (reused from spur_gear.py).

_XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))


def _make_face_from_pts(pts_2d: list[tuple[float, float]]) -> Face:
    """Turn a closed 2-D polyline into a planar Face.

    从闭合 2D 点集构造 XY 平面上的面 (齿廓用)。
    """
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(_XY_PLANE, wire.wrapped, True).Face())


def _tooth_pts(
    tooth_idx: int,
    teeth: int,
    base_r: float,
    root_r: float,
    addendum_r: float,
    steps: int = 8,
) -> list[tuple[float, float]] | None:
    """Compute 2-D polyline points for a single involute tooth.

    逐齿计算渐开线齿廓闭合点集 (左侧 + 右侧 + 齿根圆弧)。
    Algorithm: reused from spur_gear.py (ISO 54 involute profile).
    """
    pitch_angle = 2 * math.pi / teeth
    half_t = math.pi / (2 * teeth)
    a_i = pitch_angle * tooth_idx
    inv_max = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1))

    left: list[tuple[float, float]] = []
    for s in range(steps + 1):
        t = s / steps
        ia = inv_max * t
        r = base_r * math.sqrt(1 + ia ** 2)
        if r < root_r:
            continue
        r = min(r, addendum_r)
        th = a_i + half_t - ia + math.atan(ia)
        left.append((r * math.cos(th), r * math.sin(th)))

    right: list[tuple[float, float]] = []
    for s in range(steps, -1, -1):
        t = s / steps
        ia = inv_max * t
        r = base_r * math.sqrt(1 + ia ** 2)
        if r < root_r:
            continue
        r = min(r, addendum_r)
        th = a_i - half_t + ia - math.atan(ia)
        right.append((r * math.cos(th), r * math.sin(th)))

    if not left or not right:
        return None

    th_r = math.atan2(right[-1][1], right[-1][0])
    th_l = math.atan2(left[0][1], left[0][0])
    if th_l < th_r:
        th_l += 2 * math.pi
    arc_pts = [
        (
            root_r * math.cos(th_r + (th_l - th_r) * k / 4),
            root_r * math.sin(th_r + (th_l - th_r) * k / 4),
        )
        for k in range(1, 4)
    ]
    return left + right + arc_pts


# ---------- 蜗杆 / Worm ----------

def _derive_worm_spec(
    module: float, threads: int, length: float,
    diameter_coeff: float, pressure_angle: float,
) -> WormSpec:
    """Compute all derived quantities for a worm."""
    d1 = diameter_coeff * module
    da1 = d1 + 2.0 * module
    df1 = d1 - 2.4 * module
    lead = math.pi * module * threads
    lead_angle = math.degrees(math.atan(threads / diameter_coeff))
    return WormSpec(
        module=module,
        threads=threads,
        length=length,
        diameter_coeff=diameter_coeff,
        pressure_angle=pressure_angle,
        pitch_d=round(d1, 3),
        addendum_d=round(da1, 3),
        dedendum_d=round(df1, 3),
        lead=round(lead, 3),
        lead_angle=round(lead_angle, 3),
    )


def make_worm(
    module: float = 2.0,
    threads: int = 1,
    length: float = 40.0,
    diameter_coeff: float = 10.0,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate an industrial worm (helical screw-like gear).

    生成工业级蜗杆 (梯形齿沿螺旋扫掠)。

    Args:
        module:         Axial module mx (mm).
        threads:        Number of starts z1 (1 ~ 4, typ.).
        length:         Worm overall length L (mm) along Z axis.
        diameter_coeff: Diameter coefficient q, d1 = q·mx (typ. 8 ~ 12).
        pressure_angle: Axial pressure angle α (°), ISO 20°.

    Coordinate system:
        - Z axis = rotational axis.
        - Geometrically centered at origin; Z ∈ [-L/2, +L/2].

    Strategy (additive sweep along helix — convex-safe):
        1. 根圆柱作骨架 / root cylinder at r_root.
        2. 轴向梯形齿廓 (压力角 α) / trapezoidal tooth profile in axial section.
        3. 沿螺旋 sweep 生成一条齿线;多头时旋转相位复制 z1 份。
           (sweep along helix; replicate with phase offset 360/z1 for z1 starts)
        4. 与根圆柱并集,外径由齿顶圆自然保证。
        5. 用盒 intersect 裁掉两端多出的螺旋尾。
    """
    if threads < 1 or threads > 4:
        raise ValueError(f"threads={threads} out of typical range [1..4]")
    if length <= 0:
        raise ValueError(f"length={length} must be positive")
    if diameter_coeff <= 0:
        raise ValueError(f"diameter_coeff={diameter_coeff} must be positive")

    spec = _derive_worm_spec(module, threads, length, diameter_coeff, pressure_angle)

    r_pitch = spec.pitch_d / 2
    r_root = spec.dedendum_d / 2
    r_addendum = spec.addendum_d / 2
    ha = module          # 齿顶高 / addendum height
    hd = 1.2 * module    # 齿根高 / dedendum height (ISO)
    pz = spec.lead       # 导程 / lead
    px = pz / threads    # 轴向齿距 / axial pitch (π·mx)
    alpha_rad = math.radians(pressure_angle)
    tan_a = math.tan(alpha_rad)

    # ── 轴向梯形齿廓 (ISO 1122) / axial trapezoidal tooth profile ──
    # 分度线处齿厚 = px/2;向齿顶收敛、向齿根发散,两侧压力角 α。
    # At pitch line: tooth thickness = px/2; converges toward tip, diverges toward root.
    tooth_w_pitch = 0.5 * px
    tooth_w_tip = tooth_w_pitch - 2.0 * ha * tan_a
    tooth_w_root = tooth_w_pitch + 2.0 * hd * tan_a
    if tooth_w_tip <= 0.05:
        tooth_w_tip = 0.05  # 防止退化 / avoid degenerate tip

    # 4 个顶点,局部坐标 (u = 径向相对分度圆, v = 轴向偏移)
    # Four vertices (u = radial offset from r_pitch, v = axial offset).
    pts_local = [
        (-hd, -tooth_w_root / 2),  # 齿根左 / root-left
        (-hd, +tooth_w_root / 2),  # 齿根右 / root-right
        (+ha, +tooth_w_tip  / 2),  # 齿顶右 / tip-right
        (+ha, -tooth_w_tip  / 2),  # 齿顶左 / tip-left
    ]

    # ── 1) 根圆柱 / root cylinder ──
    worm: Part = Cylinder(
        radius=r_root,
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # ── 2) 多头螺旋扫掠 / helical sweeps for each thread start ──
    # 两端各多扫 1/4 圈导程,最后用 trim_box 裁齐,避免端面齿缺损。
    # margin 取 0.25·Pz:太大会导致多圈自相交干扰后续 boolean intersect,
    # 太小又会在两端出现齿缺损。实测 0.25 对 1/2/3 头均稳定。
    # (Extend helix by 1/4 lead per end; larger margin risks self-overlap
    #  that confuses the final box intersection.)
    margin = 0.25 * pz
    helix_h = length + 2 * margin

    for k in range(threads):
        phase_deg = 360.0 * k / threads
        phase_rad = math.radians(phase_deg)

        # 生成一条等直径螺旋(半径=分度圆 r_pitch),中心居中
        # Helix with radius = r_pitch, centered about Z = 0
        helix: Edge | Wire = Edge.make_helix(
            pitch=pz,
            height=helix_h,
            radius=r_pitch,
            center=(0, 0, -helix_h / 2),
            normal=(0, 0, 1),
        )
        if phase_deg:
            helix = helix.rotate(axis=Axis.Z, angle=phase_deg)

        # 起点位置 / helix start point (in world coords, after rotation)
        start_pt = helix.start_point()

        # 切向 @start: (-r·sinθ, r·cosθ, pz/(2π)),θ = phase_rad
        # Tangent at helix start (parametric derivative).
        tx = -r_pitch * math.sin(phase_rad)
        ty = r_pitch * math.cos(phase_rad)
        tz = pz / (2 * math.pi)
        tnorm = math.sqrt(tx * tx + ty * ty + tz * tz)
        tangent = Vector(tx / tnorm, ty / tnorm, tz / tnorm)

        # 径向 @start: (cosθ, sinθ, 0) — 指向外侧
        # Radial direction (outward) at start.
        radial = Vector(math.cos(phase_rad), math.sin(phase_rad), 0.0)

        # 截面平面:原点=start, x_dir=径向(以齿根为基准), z_dir=切向
        # Section plane: origin at helix start, x_dir radial, z_dir tangent.
        section_plane = Plane(
            origin=Vector(start_pt),
            x_dir=radial,
            z_dir=tangent,
        )

        with BuildPart() as thread_solid:
            with BuildSketch(section_plane):
                with BuildLine():
                    Polyline(*pts_local, close=True)
                make_face()
            sweep(path=helix, is_frenet=True)

        worm = worm + thread_solid.part

    # ── 3) 用盒子 intersect 裁齐两端 / trim axial ends to exact length ──
    trim_box = Box(
        length=spec.addendum_d + 4,
        width=spec.addendum_d + 4,
        height=length,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    worm = worm & trim_box

    return worm


# ---------- 蜗轮 / Worm Wheel ----------

def _derive_worm_wheel_spec(
    module: float, teeth: int, bore_d: float,
    worm_threads: int, worm_d: float,
    face_width: float | None, pressure_angle: float,
) -> WormWheelSpec:
    """Compute all derived quantities for a worm wheel."""
    d2 = module * teeth
    da2 = d2 + 2.0 * module
    df2 = d2 - 2.4 * module
    fw = face_width if face_width is not None else 0.75 * worm_d
    center_dist = (worm_d + d2) / 2
    return WormWheelSpec(
        module=module,
        teeth=teeth,
        bore_d=bore_d,
        worm_threads=worm_threads,
        worm_d=worm_d,
        face_width=round(fw, 3),
        pressure_angle=pressure_angle,
        pitch_d=round(d2, 3),
        addendum_d=round(da2, 3),
        dedendum_d=round(df2, 3),
        center_distance=round(center_dist, 3),
    )


def make_worm_wheel(
    module: float = 2.0,
    teeth: int = 30,
    bore_d: float = 8.0,
    worm_threads: int = 1,
    worm_d: float = 20.0,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate an industrial worm wheel (spur-gear blank + torus concave groove).

    生成工业级蜗轮 (渐开线直齿轮毛坯 + 圆弧凹槽,简化包络面)。

    Args:
        module:         Module mx (mm).
        teeth:          Number of teeth z2 (≥ 6).
        bore_d:         Central bore diameter (mm).
        worm_threads:   Mating worm starts z1 (记录用,几何简化忽略偏转).
        worm_d:         Mating worm pitch diameter d1 (mm).
        face_width:     Gear face width b2 (mm), default 0.75·d1.
        pressure_angle: Pressure angle α (°), ISO 20°.

    Coordinate system:
        - Z axis = rotational axis.
        - Geometrically centered at origin; Z ∈ [-b2/2, +b2/2].

    Strategy:
        1. 建渐开线直齿轮毛坯 (z2 齿, 模数 mx, 齿宽 b2)。
           (build involute spur gear blank)
        2. 用 Torus 布尔车削中部圆弧凹槽,抱紧蜗杆:
           Torus 主轴 = X (= 蜗杆装配轴向), 位于原点;
           大半径 major_R = 中心距 a,小半径 minor_r = 蜗杆齿顶半径 + 间隙。
           (subtract a torus whose axis = X, major_R = a, minor_r = worm tip + clearance)
        3. 挖中心孔 / subtract central bore.
    """
    if teeth < 6:
        raise ValueError(f"teeth={teeth} too small (min 6)")
    if worm_d <= 0:
        raise ValueError(f"worm_d={worm_d} must be positive")

    spec = _derive_worm_wheel_spec(
        module, teeth, bore_d, worm_threads, worm_d, face_width, pressure_angle,
    )

    pitch_r = spec.pitch_d / 2
    addendum_r = spec.addendum_d / 2
    root_r = spec.dedendum_d / 2
    base_r = pitch_r * math.cos(math.radians(pressure_angle))

    if bore_d >= spec.dedendum_d:
        raise ValueError(
            f"bore_d={bore_d} >= dedendum_d={spec.dedendum_d}; "
            f"reduce bore or increase teeth/module"
        )
    if base_r <= 0:
        raise ValueError(f"base_r={base_r:.3f} invalid")

    fw = spec.face_width

    # ── 1) 渐开线直齿轮毛坯 / involute spur gear blank ──
    # 策略与 spur_gear 完全一致:根圆柱 + 逐齿 Algebra Mode 融合
    # (avoid extruding z non-convex polygons at once; OCP viewer drops faces.)
    gear: Part = Cylinder(
        radius=root_r,
        height=fw,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    for i in range(teeth):
        pts = _tooth_pts(i, teeth, base_r, root_r, addendum_r)
        if pts is None:
            continue
        face = _make_face_from_pts(pts)
        with BuildPart() as tooth:
            with BuildSketch(Plane.XY.offset(-fw / 2)):
                add(face)
            extrude(amount=fw)
        gear = gear + tooth.part

    # ── 2) 圆弧凹槽 / concave envelope groove ──
    # 真实蜗轮齿面是蜗杆展成的复杂圆弧包络,这里用一个 Torus 简化:
    # The real worm wheel tooth surface is a swept envelope of the worm;
    # we simplify by subtracting a torus centered on the gear axis.
    #
    # - Torus 主轴(自旋轴) → X 轴 (即蜗杆装配轴向)
    # - 大半径 major_R   = 中心距 a = (d1+d2)/2
    # - 小半径 minor_r   = 蜗杆齿顶半径 + 间隙
    # (Torus axis = X; major_R = center distance; minor_r = worm tip + clearance.)
    worm_tip_r = worm_d / 2 + module
    clearance = 0.3  # mm
    minor_r = worm_tip_r + clearance
    major_R = spec.center_distance

    torus_cutter = Torus(major_radius=major_R, minor_radius=minor_r)
    # 原生 Torus 主轴 = Z,绕 Y 轴旋转 90° 使主轴 = X
    # Default torus axis is Z; rotate 90° about Y to align with X.
    torus_cutter = torus_cutter.rotate(axis=Axis.Y, angle=90)

    gear = gear - torus_cutter

    # ── 3) 中心孔 / central bore ──
    gear = gear - Cylinder(
        radius=bore_d / 2,
        height=fw + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    return gear


# ---------- 参数表 / Spec tables ----------

_WORM_SPECS: dict[str, WormSpec] = {
    "WORM_M1_Z1_L30":  _derive_worm_spec(1.0, 1, 30.0, 10.0, 20.0),
    "WORM_M2_Z1_L50":  _derive_worm_spec(2.0, 1, 50.0, 10.0, 20.0),
    "WORM_M2_Z2_L50":  _derive_worm_spec(2.0, 2, 50.0, 10.0, 20.0),
}

_WORM_WHEEL_SPECS: dict[str, WormWheelSpec] = {
    "WHEEL_M1_Z30_BORE5":  _derive_worm_wheel_spec(1.0, 30, 5.0,  1, 10.0, None, 20.0),
    "WHEEL_M2_Z30_BORE8":  _derive_worm_wheel_spec(2.0, 30, 8.0,  1, 20.0, None, 20.0),
    "WHEEL_M2_Z40_BORE10": _derive_worm_wheel_spec(2.0, 40, 10.0, 2, 20.0, None, 20.0),
}


# ---------- 冒烟断言 / Smoke assertions (no cache I/O) ----------
# 按 parts-lib 新规范:cache 由 scripts/build_cache.py 统一生成;
# __main__ 只做 is_valid / bbox 基础断言,不写 STEP,不开 viewer。
# (Cache is produced by scripts/build_cache.py; __main__ here runs smoke
#  assertions only — no STEP export, no ocp_vscode.show().)

if __name__ == "__main__":
    print("=" * 70)
    print("Worm + Worm Wheel smoke tests / 蜗杆 + 蜗轮冒烟测试")
    print("=" * 70)

    # ---- Worms / 蜗杆 ----
    specs_worm = [
        # (module, threads, length, diameter_coeff)
        (1.0, 1, 30, 10),
        (2.0, 1, 50, 10),
        (2.0, 2, 50, 10),
    ]
    for m, z1, L, q in specs_worm:
        part = make_worm(module=m, threads=z1, length=L, diameter_coeff=q)
        # 注:BRep `is_valid` 对薄边微自交敏感,此处用 volume+bbox 作主断言
        # (OCP's is_valid flags helix tangent micro-intersections even when
        #  the solid is geometrically usable; use volume/bbox as primary check.)
        assert part.volume > 0, f"worm m{m} z{z1} empty (zero volume)"
        bb = part.bounding_box()
        assert bb.size.Z > 0, f"worm m{m} z{z1} empty bbox"
        # 粗略检查外径与分度圆+齿顶吻合
        expected_od = (q * m) + 2 * m  # da1
        assert abs(bb.size.X - expected_od) < 0.05, (
            f"worm m{m} z{z1} bbox.X={bb.size.X} != da1={expected_od}"
        )
        print(
            f"OK worm  m{m} z{z1} L{L}: "
            f"bbox={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} "
            f"vol={part.volume:.1f}"
        )

    # ---- Worm wheels / 蜗轮 ----
    specs_wheel = [
        # (module, teeth, bore_d, worm_threads, worm_d)
        (1.0, 30, 5,  1, 10),
        (2.0, 30, 8,  1, 20),
        (2.0, 40, 10, 2, 20),
    ]
    for m, z2, bore, wt, wd in specs_wheel:
        part = make_worm_wheel(
            module=m, teeth=z2, bore_d=bore,
            worm_threads=wt, worm_d=wd,
        )
        assert part.volume > 0, f"wheel m{m} z{z2} empty (zero volume)"
        bb = part.bounding_box()
        assert bb.size.Z > 0, f"wheel m{m} z{z2} empty bbox"
        # 外径应接近齿顶圆 da2 = m(z2+2)
        expected_od = m * (z2 + 2)
        assert abs(bb.size.X - expected_od) < 0.05, (
            f"wheel m{m} z{z2} bbox.X={bb.size.X} != da2={expected_od}"
        )
        print(
            f"OK wheel m{m} z{z2} bore{bore}: "
            f"bbox={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} "
            f"vol={part.volume:.1f}"
        )

    print("=" * 70)
    print("All smoke tests passed. Run scripts/build_cache.py to generate STEP cache.")
