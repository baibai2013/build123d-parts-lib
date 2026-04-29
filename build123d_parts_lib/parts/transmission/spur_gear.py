"""Spur gear with true involute tooth profile.

直齿圆柱齿轮 / Spur Gear —— ISO 54 / DIN 867 标准渐开线齿形。

Standards: ISO 54 (基本齿形), DIN 867 (参考齿条), 压力角 α = 20°
License: MIT

支持规格 / Supported specs:
    m1.0: (z=16, bore=5) / (z=20, bore=5) / (z=32, bore=8) / (z=40, bore=8)
    m2.0: (z=12, bore=6) / (z=20, bore=8) / (z=30, bore=8) / (z=40, bore=10)

核心几何 / Core geometry (m = module, z = teeth count, α = pressure angle):
    分度圆 pitch  d  = m × z
    齿顶圆 addend da  = m × (z + 2)
    齿根圆 dedend df  = m × (z − 2.5)
    基圆   base   db  = d × cos(α)

简化级别 / Simplification level: ★★★★★
    - 真实渐开线齿廓（逐点采样 + 多边形拟合），非圆柱/多边形近似
    - 齿根圆弧过渡连接两侧渐开线
    - 建模策略：根圆柱 + 逐齿 Algebra Mode 融合
      (避免 z 齿一次性拉伸造成的非凸多边形，OCP viewer 会 "face ignored")
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    BuildPart,
    BuildSketch,
    Cylinder,
    Plane,
    Part,
    add,
    export_step,
    extrude,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]
from build123d import Wire, Face


class SpurGearSpec(NamedTuple):
    """Spur gear parameter record / 直齿轮参数记录。"""

    module: float       # 模数 m (mm)
    teeth: int          # 齿数 z
    bore_d: float       # 中心孔径 (mm)
    face_width: float   # 齿宽 (mm)
    pressure_angle: float  # 压力角 (°)
    pitch_d: float      # 分度圆直径 (mm)，推导值
    addendum_d: float   # 齿顶圆直径 (mm)，推导值
    dedendum_d: float   # 齿根圆直径 (mm)，推导值


# ---------- 几何辅助 / Geometry helpers ----------
# XY 平面（用于从 2D 点集构造 Face）
_XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))


def _make_face_from_pts(pts_2d: list[tuple[float, float]]) -> Face:
    """Turn a closed 2D polyline into a planar Face.

    从闭合 2D 点集构造 XY 平面上的面（齿廓用）。
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
    """Compute 2D polyline points for a single involute tooth.

    逐齿计算渐开线齿廓闭合点集 (左侧 + 右侧 + 齿根圆弧)。

    Args:
        tooth_idx: 齿的索引 (0 .. teeth-1)
        teeth:     齿数 z
        base_r:    基圆半径 db/2
        root_r:    齿根圆半径 df/2
        addendum_r:齿顶圆半径 da/2
        steps:     渐开线采样点数（越大越光滑，默认 8 足够打印）

    Returns:
        闭合多边形的 2D 坐标列表；若该齿完全退化则返回 None。
    """
    pitch_angle = 2 * math.pi / teeth       # 齿距角 / tooth pitch angle
    half_t = math.pi / (2 * teeth)          # 半齿厚对应的圆心角 / half tooth angle
    a_i = pitch_angle * tooth_idx           # 当前齿中心方位角 / tooth central angle

    # 渐开线展角上限 (齿顶处)
    # ia_max 对应 addendum 处的渐开线参数
    inv_max = math.sqrt(max(0, (addendum_r / base_r) ** 2 - 1))

    # ---- 左侧渐开线 (left flank, 从齿根到齿顶) ----
    left: list[tuple[float, float]] = []
    for s in range(steps + 1):
        t = s / steps
        ia = inv_max * t                        # 渐开线参数 involute angle
        r = base_r * math.sqrt(1 + ia ** 2)     # 渐开线半径 r(t)
        if r < root_r:                          # 小于齿根圆则裁掉（用圆弧过渡）
            continue
        r = min(r, addendum_r)                  # 上限不超过齿顶圆
        th = a_i + half_t - ia + math.atan(ia)  # 渐开线极角
        left.append((r * math.cos(th), r * math.sin(th)))

    # ---- 右侧渐开线 (right flank, 从齿顶回齿根) ----
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

    # ---- 齿根过渡圆弧 (root fillet) ----
    # 连接右侧末点 → 左侧起点，沿齿根圆走 4 段
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


# ---------- 主接口 / Public API ----------
def make_spur_gear(
    module: float = 2.0,
    teeth: int = 20,
    bore_d: float = 8.0,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate an industrial-grade involute spur gear.

    生成工业级渐开线直齿圆柱齿轮。

    Args:
        module:         模数 m (mm)，ISO 齿轮基本参数
        teeth:          齿数 z (>= 6)
        bore_d:         中心孔直径 (mm)，必须小于齿根圆直径
        face_width:     齿宽 (mm)；默认 10 × module
        pressure_angle: 压力角 α (°)，ISO 标准值 20°

    Coordinate system / 坐标系:
        - Z 轴为旋转轴 / Z axis = rotational axis
        - 几何中心在原点 / centered at origin
        - Z ∈ [-face_width/2, +face_width/2]

    Raises:
        ValueError: 当 bore_d >= 齿根圆直径，无物理意义。
    """
    if face_width is None:
        face_width = 10.0 * module

    # ---- 几何参数计算 ----
    pitch_r = module * teeth / 2                                 # 分度圆半径
    addendum_r = pitch_r + module                                # 齿顶圆半径 = m(z+2)/2
    root_r = pitch_r - 1.25 * module                             # 齿根圆半径 = m(z-2.5)/2
    base_r = pitch_r * math.cos(math.radians(pressure_angle))    # 基圆半径 = d·cosα / 2

    # ---- 验证 / Sanity check ----
    if teeth < 6:
        raise ValueError(f"teeth={teeth} too small (min 6)")
    if bore_d >= 2 * root_r:
        raise ValueError(
            f"bore_d={bore_d} >= dedendum_d={2 * root_r:.3f} mm; "
            f"中心孔超过齿根圆，减小孔径或增加模数/齿数"
        )
    if base_r <= 0:
        raise ValueError(f"base_r={base_r:.3f} invalid")

    # ---- 建模：根圆柱 + 逐齿融合 ----
    # ⚠️ 关键：不能把 z 齿一次性拉伸成非凸多边形，
    # 否则 OCP viewer 会忽略顶底面（face ignored）。
    gear: Part = Cylinder(radius=root_r, height=face_width)

    fused = 0
    for i in range(teeth):
        pts = _tooth_pts(i, teeth, base_r, root_r, addendum_r)
        if pts is None:
            continue
        face = _make_face_from_pts(pts)
        with BuildPart() as tooth:
            with BuildSketch(Plane.XY.offset(-face_width / 2)):
                add(face)
            extrude(amount=face_width)
        gear = gear + tooth.part
        fused += 1

    if fused == 0:
        raise ValueError("no teeth were generated; check module/teeth/pressure_angle")

    # ---- 中心孔（贯穿）----
    gear = gear - Cylinder(radius=bore_d / 2, height=face_width + 0.1)

    return gear


def _derive_spec(
    module: float, teeth: int, bore_d: float,
    face_width: float | None = None, pressure_angle: float = 20.0,
) -> SpurGearSpec:
    """Construct a SpurGearSpec with derived pitch/addendum/dedendum diameters."""
    fw = face_width if face_width is not None else 10.0 * module
    pitch_d = module * teeth
    return SpurGearSpec(
        module=module,
        teeth=teeth,
        bore_d=bore_d,
        face_width=fw,
        pressure_angle=pressure_angle,
        pitch_d=round(pitch_d, 3),
        addendum_d=round(pitch_d + 2 * module, 3),
        dedendum_d=round(pitch_d - 2.5 * module, 3),
    )


# 参数表 / Spec table
_SPECS: dict[str, SpurGearSpec] = {
    # m1.0 —— 小模数齿轮
    "SPUR_M1_16T_BORE5": _derive_spec(1.0, 16, 5.0),
    "SPUR_M1_20T_BORE5": _derive_spec(1.0, 20, 5.0),
    "SPUR_M1_32T_BORE8": _derive_spec(1.0, 32, 8.0),
    "SPUR_M1_40T_BORE8": _derive_spec(1.0, 40, 8.0),
    # m2.0 —— 中等模数齿轮
    "SPUR_M2_12T_BORE6":  _derive_spec(2.0, 12, 6.0),
    "SPUR_M2_20T_BORE8":  _derive_spec(2.0, 20, 8.0),
    "SPUR_M2_30T_BORE8":  _derive_spec(2.0, 30, 8.0),
    "SPUR_M2_40T_BORE10": _derive_spec(2.0, 40, 10.0),
}


def _m_slug(module: float) -> str:
    """Format module for filename: 1.0 -> m1_0, 2.0 -> m2_0."""
    return f"m{module:.1f}".replace(".", "_")


if __name__ == "__main__":
    # Smoke-test / 冒烟断言（不写 cache；cache 由 scripts/build_cache.py 统一生成）
    combos: list[tuple[float, int, float]] = [
        # (module, teeth, bore)
        (1.0, 16, 5.0),
        (1.0, 20, 5.0),
        (1.0, 32, 8.0),
        (1.0, 40, 8.0),
        (2.0, 12, 6.0),
        (2.0, 20, 8.0),
        (2.0, 30, 8.0),
        (2.0, 40, 10.0),
    ]

    for m, z, bore in combos:
        part = make_spur_gear(module=m, teeth=z, bore_d=bore)
        assert part.is_valid, f"m{m} z{z} bore{bore}: BRep invalid"
        assert len(part.solids()) == 1, f"m{m} z{z}: not single solid"
        bb = part.bounding_box()
        # 齿顶圆直径 da = m × (z + 2)
        da_expected = m * (z + 2)
        assert abs(bb.size.X - da_expected) < 0.5, (
            f"m{m} z{z}: bbox X={bb.size.X:.2f} vs da={da_expected:.2f}"
        )
        print(
            f"OK  spur m{m} z{z} bore{bore}:  "
            f"bbox={bb.size.X:.2f}x{bb.size.Y:.2f}x{bb.size.Z:.2f}mm  "
            f"vol={part.volume:.2f} mm3"
        )
