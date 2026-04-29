"""Straight bevel gear with involute tooth profile (Tredgold approximation).

直齿锥齿轮 / Straight Bevel Gear —— ISO 23509 标准，基于 Tredgold 近似。

Standards: ISO 23509 (Bevel gear geometry), DIN 3971, 压力角 αn = 20°
License: MIT

支持规格 / Supported specs (批量示例):
    等传动比 1:1 (δ = 45°):
        m1.0 × z=20  × z_mate=20 × bore=5
        m2.0 × z=16  × z_mate=16 × bore=8
        m2.0 × z=24  × z_mate=24 × bore=8
    变速比:
        m1.5 × z=15 × z_mate=30 × bore=5  (1:2, δ1 ≈ 26.57°)
        m2.0 × z=20 × z_mate=40 × bore=8  (1:2, δ1 ≈ 26.57°)

核心几何 / Core geometry (大端 heel 参考):
    节锥半角   δ  = atan2(z, z_mate)    (等比时 45°)
    大端节圆   de = m · z
    节锥距     R  = de / (2·sinδ)
    大端齿顶高 ha = m         齿根高 hf = 1.25·m
    大端齿顶圆 da = de + 2·m           (Tredgold 近似：径向齿高 = m)
    大端齿根圆 df = de − 2.5·m
    基圆       db = de · cos(αn)

建模策略 / Modeling strategy (Tredgold 近似 + 两截面 Loft, ★★★★☆):
    1. 大端面 (Z=0) 画完整渐开线齿廓 + 根圆截面
       Large-end involute tooth profile on plane Z=0.
    2. 小端面 (Z = b·cosδ) 等比缩放 (R-b)/R，同一齿对齐
       Small-end profile scaled by (R-b)/R at Z = b·cosδ, teeth aligned.
    3. 每齿独立 Loft 两截面 → 锥形齿体，齐数次布尔融合
       Per-tooth loft avoids non-convex face issues in OCP viewer.
    4. 根锥台 (frustum) 作为本体骨架；中心孔贯穿整体。
       Root frustum as body; central bore pierces full height.

坐标系 / Coordinate system:
    - Z 轴为旋转轴 / Z axis = rotational axis
    - 原点在**大端面中心** / origin at large-end face center
    - +Z 指向节锥顶 (apex) / +Z points toward pitch-cone apex
    - 大端位于 Z=0，小端位于 Z = b·cosδ
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    Cylinder,
    Face,
    Location,
    Part,
    Plane,
    Polyline,
    Wire,
    add,
    export_step,
    loft,
    make_face,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]


class BevelGearSpec(NamedTuple):
    """Straight bevel gear parameter record / 直齿锥齿轮参数记录。"""

    module: float         # 大端模数 me (mm)
    teeth: int            # 齿数 z
    mating_teeth: int     # 配对齿数 z_mate
    bore_d: float         # 中心孔径 (mm)
    face_width: float     # 齿宽 b (mm)
    pressure_angle: float # 压力角 αn (°)
    pitch_cone_deg: float # 节锥半角 δ (°)，推导值
    cone_distance: float  # 节锥距 R (mm)，推导值
    heel_pitch_d: float   # 大端节圆 de (mm)，推导值
    heel_addendum_d: float# 大端齿顶圆 da (mm)，推导值
    heel_dedendum_d: float# 大端齿根圆 df (mm)，推导值


# ---------- 几何辅助 / Geometry helpers ----------


def _make_face_at_z(pts_2d: list[tuple[float, float]], z: float) -> Face:
    """Build a planar face on plane Z=z from closed 2-D points.

    从 2D 点集在 Z=z 平面上构造闭合面 (齿截面)。
    用 BuildSketch 规范化 wire,避免 BRepBuilderAPI_MakeFace 对非凸多边形
    (齿根凹弧) 误合并为凸扇形。
    Uses BuildSketch to normalize wires; avoids the convex-hull collapse
    that OCP's raw MakeFace can produce on non-convex tooth profiles.
    """
    plane = Plane.XY.offset(z)
    with BuildSketch(plane) as sk:
        with BuildLine(plane) as _bl:
            Polyline(*[(x, y) for x, y in pts_2d], close=True)
        make_face()
    # BuildSketch accumulates faces in sk.sketch; locate returned faces on plane
    faces = sk.sketch.faces()
    if not faces:
        # Fallback to raw OCP if BuildSketch yields nothing (shouldn't happen)
        plane_occ = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
        wire = Wire.make_polygon([(x, y, z) for x, y in pts_2d], close=True)
        return Face(BRepBuilderAPI_MakeFace(plane_occ, wire.wrapped, True).Face())
    return faces[0]


def _tooth_pts_2d(
    tooth_idx: int,
    teeth: int,
    base_r: float,
    root_r: float,
    addendum_r: float,
    steps: int = 8,
) -> list[tuple[float, float]] | None:
    """Compute 2-D involute tooth polyline at a given scale.

    计算单齿渐开线 2D 闭合多边形 (左侧 + 右侧 + 齿根圆弧)。

    Args:
        tooth_idx: 齿索引 0 .. z-1
        teeth:     齿数 z
        base_r:    基圆半径 (本截面上)
        root_r:    齿根圆半径 (本截面上)
        addendum_r:齿顶圆半径 (本截面上)
        steps:     渐开线采样数
    """
    pitch_angle = 2 * math.pi / teeth
    half_t = math.pi / (2 * teeth)
    a_i = pitch_angle * tooth_idx

    inv_max = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1))

    # ---- 左侧渐开线 / left involute flank ----
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

    # ---- 右侧渐开线 / right involute flank ----
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

    # ---- 齿根过渡圆弧 / root fillet arc ----
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


def _scale_pts(pts: list[tuple[float, float]], s: float) -> list[tuple[float, float]]:
    """Radial scale of 2-D polyline by factor s (about origin).

    围绕原点等比缩放 2D 点集，用于小端齿截面（保证齿对齐）。
    """
    return [(x * s, y * s) for x, y in pts]


# ---------- 主接口 / Public API ----------


def make_bevel_gear(
    module: float = 2.0,
    teeth: int = 20,
    mating_teeth: int = 20,
    bore_d: float = 8.0,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate an industrial-grade straight bevel gear.

    生成工业级直齿锥齿轮 (ISO 23509, Tredgold 近似)。

    Args:
        module:         大端模数 me (mm)
        teeth:          齿数 z
        mating_teeth:   配对齿数 z_mate (决定节锥半角 δ)
        bore_d:         中心孔径 (mm)
        face_width:     齿宽 b (mm)；None 则取 min(8·m, R/3)
        pressure_angle: 压力角 αn (°)

    Coordinate system:
        - Origin at large-end face center; +Z toward pitch-cone apex.
        - 大端在 Z=0, 小端在 Z = b·cosδ.

    Raises:
        ValueError: 参数无效 (齿数过少 / 孔径过大 / 齿宽过大).
    """
    if teeth < 6:
        raise ValueError(f"teeth={teeth} too small (min 6)")
    if mating_teeth < 6:
        raise ValueError(f"mating_teeth={mating_teeth} too small (min 6)")

    # ---- 节锥半角 δ / pitch cone half-angle ----
    # δ1 = atan2(z1, z2)  使 tan(δ1) = z1/z2，等比时 δ=45°
    delta_rad = math.atan2(teeth, mating_teeth)
    delta_deg = math.degrees(delta_rad)
    cos_d = math.cos(delta_rad)
    sin_d = math.sin(delta_rad)

    # ---- 大端几何 / heel (large-end) geometry ----
    # Tredgold 近似:大端齿廓等价于半径=cone_distance 的"背锥虚拟直齿轮"
    # 齿顶高/齿根高按径向量取,不做 cos_d 投影(这是 Tredgold 的核心简化)
    # Heel tooth profile = virtual spur gear on back-cone plane;
    # addendum/dedendum taken radially (no cos_d projection).
    heel_pitch_r = module * teeth / 2              # 大端节圆半径
    heel_addendum_r = heel_pitch_r + module        # 大端齿顶圆半径 = m(z+2)/2
    heel_root_r = heel_pitch_r - 1.25 * module     # 大端齿根圆半径 = m(z-2.5)/2
    heel_base_r = heel_pitch_r * math.cos(math.radians(pressure_angle))

    # 节锥距 R = de / (2·sinδ)
    cone_distance = heel_pitch_r / sin_d

    # ---- 齿宽 b / face width ----
    if face_width is None:
        face_width = min(8.0 * module, cone_distance / 3.0)
    b = face_width
    if b >= cone_distance:
        raise ValueError(
            f"face_width={b:.2f} >= cone_distance={cone_distance:.2f}; "
            f"齿宽不能超过节锥距，减小 face_width"
        )

    # ---- 小端几何 (Tredgold 缩放比) / toe (small-end) scale ----
    # 小端距 R_toe = R - b, 缩放因子 s = (R-b)/R
    scale = (cone_distance - b) / cone_distance
    toe_z = b * cos_d  # 小端面 Z 位置

    # ---- 验证 / Sanity check ----
    if bore_d >= 2 * heel_root_r * scale:
        raise ValueError(
            f"bore_d={bore_d} >= toe dedendum dia "
            f"{2*heel_root_r*scale:.3f} mm; 中心孔在小端超过齿根圆"
        )
    if heel_base_r <= 0:
        raise ValueError(f"base_r={heel_base_r:.3f} invalid")

    # ---- 根锥台骨架 / root frustum skeleton ----
    # 大端根半径 heel_root_r，小端根半径 heel_root_r·scale，高度 b·cosδ
    # Use BuildPart + loft over two circles for frustum
    with BuildPart() as frustum_builder:
        # 大端根圆
        big_circle_face = _make_face_at_z(
            [
                (
                    heel_root_r * math.cos(2 * math.pi * i / 64),
                    heel_root_r * math.sin(2 * math.pi * i / 64),
                )
                for i in range(64)
            ],
            0.0,
        )
        # 小端根圆
        small_r = heel_root_r * scale
        small_circle_face = _make_face_at_z(
            [
                (
                    small_r * math.cos(2 * math.pi * i / 64),
                    small_r * math.sin(2 * math.pi * i / 64),
                )
                for i in range(64)
            ],
            toe_z,
        )
        loft([big_circle_face, small_circle_face], ruled=True)

    gear: Part = frustum_builder.part

    # ---- 每齿独立 Loft / per-tooth loft ----
    # 关键 / Key:
    #   - 大端齿廓在 Z=0 平面上，完整渐开线参数
    #   - 小端齿廓为大端等比缩放 (同齿索引，同旋转角对齐)
    #   - 两截面 loft (ruled=True) 形成锥形齿面
    #   For each tooth: scale heel profile by (R-b)/R for the toe section,
    #   then loft the two aligned faces into a conical tooth solid.
    fused = 0
    for i in range(teeth):
        heel_pts = _tooth_pts_2d(
            i, teeth, heel_base_r, heel_root_r, heel_addendum_r
        )
        if heel_pts is None:
            continue
        toe_pts = _scale_pts(heel_pts, scale)

        heel_face = _make_face_at_z(heel_pts, 0.0)
        toe_face = _make_face_at_z(toe_pts, toe_z)

        with BuildPart() as tooth_builder:
            loft([heel_face, toe_face], ruled=True)
        gear = gear + tooth_builder.part
        fused += 1

    if fused == 0:
        raise ValueError("no teeth generated; check module/teeth/pressure_angle")

    # ---- 中心孔 (贯穿整个锥台) / bore pierces full height ----
    # 大端在 Z=0, 小端在 Z=toe_z; 孔从 Z=-0.2 打到 Z=toe_z+0.2 完全贯穿
    bore = Cylinder(
        radius=bore_d / 2,
        height=toe_z + 0.4,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).moved(Location((0, 0, -0.2)))
    gear = gear - bore

    # ---- 清理孤立小面 / Clean up isolated tiny solids from fuse operations ----
    # 逐齿 boolean fuse 在齿-锥台切线处可能留下微小孤立 solid（浮点误差）。
    # Per-tooth boolean fuse may leave micro isolated solids at tangent edges
    # due to floating-point tolerance; keep only the largest (main gear body).
    solids = gear.solids()
    if len(solids) > 1:
        main = max(solids, key=lambda s: s.volume)
        # 重新包装为 Part（保持返回类型一致） / rewrap as Part to keep type
        with BuildPart() as _wrap:
            add(main)
        gear = _wrap.part

    return gear


def _derive_spec(
    module: float,
    teeth: int,
    mating_teeth: int,
    bore_d: float,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> BevelGearSpec:
    """Build a BevelGearSpec with derived cone/pitch values."""
    delta_rad = math.atan2(teeth, mating_teeth)
    cos_d = math.cos(delta_rad)
    sin_d = math.sin(delta_rad)

    pitch_d = module * teeth
    cone_R = pitch_d / (2 * sin_d)
    fw = face_width if face_width is not None else min(8.0 * module, cone_R / 3.0)

    return BevelGearSpec(
        module=module,
        teeth=teeth,
        mating_teeth=mating_teeth,
        bore_d=bore_d,
        face_width=round(fw, 3),
        pressure_angle=pressure_angle,
        pitch_cone_deg=round(math.degrees(delta_rad), 3),
        cone_distance=round(cone_R, 3),
        heel_pitch_d=round(pitch_d, 3),
        # Tredgold 近似:径向齿高 = m / 1.25m,不经锥角投影
        heel_addendum_d=round(pitch_d + 2 * module, 3),
        heel_dedendum_d=round(pitch_d - 2.5 * module, 3),
    )


# 参数表 / Spec table
_SPECS: dict[str, BevelGearSpec] = {
    # 等传动比 1:1 (δ = 45°)
    "BEVEL_M1_Z20_MATE20_BORE5": _derive_spec(1.0, 20, 20, 5.0),
    "BEVEL_M2_Z16_MATE16_BORE8": _derive_spec(2.0, 16, 16, 8.0),
    "BEVEL_M2_Z24_MATE24_BORE8": _derive_spec(2.0, 24, 24, 8.0),
    # 变速比 1:2
    "BEVEL_M1_5_Z15_MATE30_BORE5": _derive_spec(1.5, 15, 30, 5.0),
    "BEVEL_M2_Z20_MATE40_BORE8":   _derive_spec(2.0, 20, 40, 8.0),
}


def _m_slug(module: float) -> str:
    """Format module for filename."""
    return f"{module:.1f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    # Smoke-test / 冒烟断言（不写 cache；cache 由 scripts/build_cache.py 统一生成）
    combos: list[tuple[float, int, int, float]] = [
        # (module, teeth, mating_teeth, bore)
        # 等传动比 1:1
        (1.0, 20, 20, 5.0),
        (2.0, 16, 16, 8.0),
        (2.0, 24, 24, 8.0),
        # 变速比 1:2
        (1.5, 15, 30, 5.0),
        (2.0, 20, 40, 8.0),
    ]

    print("Bevel Gear — smoke test")
    for m, z, z_mate, bore in combos:
        part = make_bevel_gear(
            module=m, teeth=z, mating_teeth=z_mate, bore_d=bore
        )
        assert part.is_valid, f"m{m} z{z}×{z_mate}: BRep invalid"
        assert len(part.solids()) == 1, f"m{m} z{z}: not single solid"
        delta = math.degrees(math.atan2(z, z_mate))
        bb = part.bounding_box()
        print(
            f"OK  bevel m{m} z{z} mate{z_mate} bore{int(bore)}:  "
            f"δ={delta:5.2f}°  "
            f"bbox={bb.size.X:.2f}x{bb.size.Y:.2f}x{bb.size.Z:.2f}mm  "
            f"vol={part.volume:.2f} mm3"
        )
