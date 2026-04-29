"""Internal gear (ring gear) with true involute tooth profile.

内齿圈 / Internal Gear (Ring Gear) —— ISO 54 / DIN 867 标准渐开线齿形。

Standards: ISO 54 (基本齿形), DIN 867 (参考齿条), 压力角 α = 20°
License: MIT

用途 / Usage:
    - 行星齿轮系 (planetary gearbox) 的外环
    - 自行车后轴内齿 / 差速器内齿圈
    - 机器人关节减速器 (harmonic / cycloidal drive 外层)

支持规格 / Supported specs:
    m1.0: z=48 / z=60 / z=80
    m1.5: z=48
    m2.0: z=40 / z=60

核心几何 / Core geometry (m = module, z = teeth count, α = pressure angle):
    分度圆 pitch     d  = m × z
    齿顶圆 addendum  da = m × (z − 2)   ← 内齿:内圆,齿向圆心凸,故 da < d
    齿根圆 dedendum  df = m × (z + 2.5) ← 内齿:外圆,df > d
    基圆   base      db = d × cos(α)
    外径   outer     do = df + 2 × wall_thickness  (默认壁厚 3 × m)

⚠️ 内齿圈 vs 外齿轮(spur_gear) 的 3 个区别:
    1. 齿顶圆在内侧 (da < d)、齿根圆在外侧 (df > d)      —— 正负号反过来
    2. 齿廓渐开线旋转方向相反 (齿朝圆心凸出)              —— 采样角符号翻转
    3. 实体外侧是环形圆柱 (ring hub)、内侧才是齿          —— 减材建模

简化级别 / Simplification level: ★★★★☆
    - 真实渐开线齿廓 (逐点采样 + 多边形拟合)
    - 齿槽过渡圆弧 (齿根圆连接两侧渐开线)
    - 建模策略:环形基础实体 + 逐齿槽减材 (Mode.SUBTRACT)
      参考 08_gear_spur_v2 的"逐齿融合/减材"策略,避免一次性合并 z 个齿槽造成的
      非凸多边形,OCP viewer 会 "face ignored"。
    - 渐开线以分度圆 (pitch) 作为锚点: θ(r) = θ_ref + inv(α(r)) − inv(α_pitch),
      保证 r = pitch_r 处齿槽边界正好在 a_i ± half_t,齿厚分布符合标准。

备注 / Note:
    cache 由 scripts/build_cache.py 生成, 本模块 __main__ 仅做断言自检。
"""
from __future__ import annotations

import math
from typing import NamedTuple

from build123d import (
    BuildPart,
    BuildSketch,
    Cylinder,
    Face,
    Part,
    Plane,
    Wire,
    add,
    extrude,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]


class InternalGearSpec(NamedTuple):
    """Internal (ring) gear parameter record / 内齿圈参数记录。"""

    module: float         # 模数 m (mm)
    teeth: int            # 齿数 z
    outer_d: float        # 外径 do (mm)
    face_width: float     # 齿宽 (mm)
    pressure_angle: float # 压力角 (°)
    pitch_d: float        # 分度圆直径 (mm), 推导值
    addendum_d: float     # 齿顶圆直径 da (mm) — 内侧小圆
    dedendum_d: float     # 齿根圆直径 df (mm) — 外侧大圆


# ---------- 几何辅助 / Geometry helpers ----------
# XY 平面(用于从 2D 点集构造 Face)
_XY_PLANE = gp_Pln(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1))


def _make_face_from_pts(pts_2d: list[tuple[float, float]]) -> Face:
    """Turn a closed 2D polyline into a planar Face.

    从闭合 2D 点集构造 XY 平面上的面 (齿槽轮廓用)。
    """
    wire = Wire.make_polygon([(x, y, 0) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(_XY_PLANE, wire.wrapped, True).Face())


def _tooth_gap_pts(
    tooth_idx: int,
    teeth: int,
    base_r: float,
    pitch_r: float,     # 分度圆半径 d/2
    addendum_r: float,  # 内齿齿顶圆 (小圆)
    dedendum_r: float,  # 内齿齿根圆 (大圆)
    steps: int = 12,
) -> list[tuple[float, float]] | None:
    """Compute 2D polyline for a single internal tooth *gap* (tooth slot).

    逐齿计算内齿"齿槽"渐开线闭合点集。

    几何原理 / Geometry theory:
        参数化渐开线角位置: θ(r) = θ_base + inv(α(r)),
        其中 α(r) = arccos(base_r / r),  inv(x) = tan(x) − x。
        约束: 在分度圆 r = pitch_r 处, 左侧齿槽边恰好为 (a_i + half_t);
        右侧齿槽边恰好为 (a_i − half_t)。
        由此反推: θ_base_left  = a_i + half_t − inv(α_pitch)
                 θ_base_right = a_i − half_t + inv(α_pitch)

    内齿齿槽的径向范围 / radial range:
        [r_inner, r_outer],  r_inner = max(base_r, addendum_r) − OVERLAP,
                             r_outer = dedendum_r + 微量外扩
        外扩量用于确保齿槽多边形切入齿根(外圈)一段距离, 让齿与齿之间的
        极薄环带不会残留。

    At the pitch circle:
        Left gap edge at a_i + half_t (= +π/(2z))
        Right gap edge at a_i − half_t (= −π/(2z))

    Args:
        tooth_idx:  齿槽索引 (0 .. teeth−1)
        teeth:      齿数 z
        base_r:     基圆半径 db/2
        pitch_r:    分度圆半径 d/2
        addendum_r: 齿顶圆半径 da/2 (内齿内侧小圆)
        dedendum_r: 齿根圆半径 df/2 (内齿外侧大圆)
        steps:      渐开线采样点数

    Returns:
        闭合多边形 2D 点; 退化时返回 None。
    """
    pitch_angle = 2 * math.pi / teeth       # 齿距角
    half_t = math.pi / (2 * teeth)          # 半齿厚角
    a_i = pitch_angle * tooth_idx           # 当前齿槽中心方位角

    # inv(α_pitch) — 分度圆处的渐开线展角, 用作参考锚点
    # inv(α_pitch) — involute offset at pitch circle, used as reference anchor
    if pitch_r <= base_r:
        return None
    ia_pitch = math.sqrt((pitch_r / base_r) ** 2 - 1)
    inv_pitch = ia_pitch - math.atan(ia_pitch)

    # 齿槽径向工作区间 / radial working range
    # - 下限 (内): max(base_r, addendum_r) 向内让一点,确保穿透内孔
    # - 上限 (外): dedendum_r 向外让一点,确保完全切入外环
    # slack inward (_IN) lets gap polygon poke through the addendum bore;
    # slack outward (_OUT) lets it cut into the ring past dedendum.
    _SLACK = 0.05 * max(dedendum_r - addendum_r, 0.1)
    r_inner = max(base_r, addendum_r - _SLACK)
    r_outer = dedendum_r + _SLACK
    if r_inner >= r_outer:
        return None

    # 渐开线参数 / involute parameter
    ia_inner = math.sqrt(max(0.0, (r_inner / base_r) ** 2 - 1))
    ia_outer = math.sqrt((r_outer / base_r) ** 2 - 1)

    # ---- 左侧齿槽边 (tooth j's right flank 的内齿版) ----
    # 极角公式: θ(r) = a_i + half_t + (inv(α(r)) − inv(α_pitch))
    # 内齿齿槽左边界 = 其左侧齿的右齿廓面。在分度圆处 θ = a_i + half_t。
    # 沿 r 增大 (从齿顶 addendum 向齿根 dedendum) θ 递增,齿槽角向变宽,
    # 对应齿变窄; 沿 r 减小 θ 递减,齿槽变窄,对应齿在 addendum 处仍有厚度。
    # 注意: 当 r_inner < base_r 时渐开线不存在,我们用 base_r 处的切线
    # (视觉上在 addendum 补一小段径向直线) 完成封闭。
    left: list[tuple[float, float]] = []
    for s in range(steps + 1):
        t = s / steps
        ia = ia_inner + (ia_outer - ia_inner) * t
        r = base_r * math.sqrt(1 + ia * ia)
        inv_a = ia - math.atan(ia)
        th = a_i + half_t + (inv_a - inv_pitch)
        left.append((r * math.cos(th), r * math.sin(th)))

    # ---- 右侧齿槽边 (对称构造) ----
    right: list[tuple[float, float]] = []
    for s in range(steps, -1, -1):
        t = s / steps
        ia = ia_inner + (ia_outer - ia_inner) * t
        r = base_r * math.sqrt(1 + ia * ia)
        inv_a = ia - math.atan(ia)
        th = a_i - half_t - (inv_a - inv_pitch)
        right.append((r * math.cos(th), r * math.sin(th)))

    # ---- 齿根过渡圆弧 (root arc) —— 沿 r_outer 大圆走 4 段 ----
    # 从 left 最末点 (r_outer, θ_L_end) 扫到 right 起点 (r_outer, θ_R_start),
    # 跨过齿槽中心 a_i 构成齿根连接弧。
    th_L_end = a_i + half_t + (ia_outer - math.atan(ia_outer) - inv_pitch)
    th_R_start = a_i - half_t - (ia_outer - math.atan(ia_outer) - inv_pitch)
    delta_out = th_L_end - th_R_start
    root_arc = [
        (
            r_outer * math.cos(th_L_end - delta_out * k / 4),
            r_outer * math.sin(th_L_end - delta_out * k / 4),
        )
        for k in range(1, 4)
    ]

    # ---- 齿顶过渡圆弧 (addendum/tip arc) —— 沿 r_inner 小圆走 4 段 ----
    # 从 right 末点 (r_inner, θ_R_end) 扫回 left 起点 (r_inner, θ_L_start)
    inv_inner = ia_inner - math.atan(ia_inner)
    th_L_start = a_i + half_t + (inv_inner - inv_pitch)
    th_R_end = a_i - half_t - (inv_inner - inv_pitch)
    delta_in = th_L_start - th_R_end
    add_arc = [
        (
            r_inner * math.cos(th_R_end + delta_in * k / 4),
            r_inner * math.sin(th_R_end + delta_in * k / 4),
        )
        for k in range(1, 4)
    ]

    # 闭合顺序: left (内→外) + root_arc (外弧) + right (外→内) + add_arc (内弧)
    return left + root_arc + right + add_arc


# ---------- 主接口 / Public API ----------
def make_internal_gear(
    module: float = 1.0,
    teeth: int = 60,
    outer_d: float | None = None,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate an industrial-grade involute internal (ring) gear.

    生成工业级渐开线内齿圈。

    Args:
        module:         模数 m (mm)
        teeth:          齿数 z (内齿圈通常 z > 40)
        outer_d:        外径 do (mm); None 时默认 df + 6 × m (壁厚 3m × 2)
        face_width:     齿宽 (mm); None 时默认 8 × module
        pressure_angle: 压力角 α (°), ISO 标准 20°

    Coordinate system / 坐标系:
        - Z 轴为旋转轴
        - 几何中心在原点, Z ∈ [-face_width/2, +face_width/2]

    Raises:
        ValueError: 外径不足以包住齿根圆, 或齿数过少。
    """
    if face_width is None:
        face_width = 8.0 * module

    # ---- 内齿几何参数 / Internal gear geometry ----
    # 注意: 与外齿相反,齿顶圆变小,齿根圆变大
    pitch_r = module * teeth / 2                                     # 分度圆半径
    addendum_r = pitch_r - module                                    # 齿顶圆 = m(z-2)/2  内侧
    dedendum_r = pitch_r + 1.25 * module                             # 齿根圆 = m(z+2.5)/2 外侧
    base_r = pitch_r * math.cos(math.radians(pressure_angle))        # 基圆

    if outer_d is None:
        outer_d = 2 * dedendum_r + 6.0 * module  # 壁厚默认 3m
    outer_r = outer_d / 2

    # ---- 验证 / Sanity check ----
    if teeth < 12:
        raise ValueError(f"teeth={teeth} too small for internal gear (min 12)")
    if outer_r <= dedendum_r:
        raise ValueError(
            f"outer_d={outer_d:.3f} <= dedendum_d={2 * dedendum_r:.3f}; "
            f"外径小于齿根圆, 材料不够。需 outer_d > {2 * dedendum_r:.3f} mm"
        )
    if addendum_r <= 0:
        raise ValueError(
            f"addendum_r={addendum_r:.3f}; 齿数过少或模数异常,齿顶圆收缩到圆心"
        )
    if base_r > addendum_r:
        # 标准内齿在 z >= 12, α = 20° 时 base_r ≈ 0.94 pitch_r, addendum_r = pitch_r - m
        # z 很小时 base_r 可能 > addendum_r, 影响渐开线起点
        # 算法会用 r_start = max(base_r, addendum_r) 自动处理, 仅告警
        pass

    # ---- 建模: 环形基础实体 + 逐齿槽减材 ----
    # Step 1: 大外圆 - 内孔(齿顶圆 da) = 环形胚体
    # 注意: 减出的孔是 da (内齿齿顶圆, 未来齿向内凸所达的极限)
    ring: Part = Cylinder(radius=outer_r, height=face_width) \
               - Cylinder(radius=addendum_r, height=face_width + 0.1)

    # Step 2: 逐齿槽减材 (每齿槽独立做一次 Mode.SUBTRACT)
    # ⚠️ 不能一次性把 z 个齿槽合成一个大 Sketch 再减 ——
    #    非凸多边形会被 OCP viewer 忽略 (face ignored)。
    cut = 0
    for i in range(teeth):
        pts = _tooth_gap_pts(i, teeth, base_r, pitch_r, addendum_r, dedendum_r)
        if pts is None:
            continue
        face = _make_face_from_pts(pts)
        with BuildPart() as slot:
            with BuildSketch(Plane.XY.offset(-face_width / 2)):
                add(face)
            extrude(amount=face_width)
        ring = ring - slot.part
        cut += 1

    if cut == 0:
        raise ValueError("no tooth gaps were generated; check module/teeth/pressure_angle")

    return ring


def _derive_spec(
    module: float, teeth: int, outer_d: float,
    face_width: float | None = None, pressure_angle: float = 20.0,
) -> InternalGearSpec:
    """Construct an InternalGearSpec with derived pitch/addendum/dedendum diameters."""
    fw = face_width if face_width is not None else 8.0 * module
    pitch_d = module * teeth
    return InternalGearSpec(
        module=module,
        teeth=teeth,
        outer_d=outer_d,
        face_width=fw,
        pressure_angle=pressure_angle,
        pitch_d=round(pitch_d, 3),
        addendum_d=round(pitch_d - 2 * module, 3),
        dedendum_d=round(pitch_d + 2.5 * module, 3),
    )


# 参数表 / Spec table (行星齿轮箱典型规格; outer_d = df + 6·m 默认壁厚 3m×2)
_SPECS: dict[str, InternalGearSpec] = {
    # m1.0 —— 轻载行星箱
    "INT_M1_48T":  _derive_spec(1.0, 48,  1.0 * (48 + 2.5) + 6.0 * 1.0),   # df=50.5, od=56.5
    "INT_M1_60T":  _derive_spec(1.0, 60,  1.0 * (60 + 2.5) + 6.0 * 1.0),   # df=62.5, od=68.5
    "INT_M1_80T":  _derive_spec(1.0, 80,  1.0 * (80 + 2.5) + 6.0 * 1.0),   # df=82.5, od=88.5
    # m1.5
    "INT_M15_48T": _derive_spec(1.5, 48,  1.5 * (48 + 2.5) + 6.0 * 1.5),   # df=75.75, od=84.75
    # m2.0 —— 机器人关节减速器
    "INT_M2_40T":  _derive_spec(2.0, 40,  2.0 * (40 + 2.5) + 6.0 * 2.0),   # df=85, od=97
    "INT_M2_60T":  _derive_spec(2.0, 60,  2.0 * (60 + 2.5) + 6.0 * 2.0),   # df=125, od=137
}


def _m_slug(module: float) -> str:
    """Format module for filename: 1.0 -> m1_0, 1.5 -> m1_5."""
    return f"m{module:.1f}".replace(".", "_")


if __name__ == "__main__":
    # ⚠️ 仅做断言自检 —— cache 由 scripts/build_cache.py 生成
    #     Assertion-only self-check; cache is produced by build_cache script.
    specs: list[tuple[float, int, float | None]] = [
        (1.0, 48, None),
        (1.0, 60, None),
        (2.0, 40, 90.0),
        (2.0, 60, 130.0),
    ]
    for m, z, od in specs:
        part = make_internal_gear(module=m, teeth=z, outer_d=od)
        # 注意:is_valid 在 build123d 中是属性,不是方法
        #       is_valid is a property (not method) in build123d Part API
        assert part.is_valid, f"m{m} z{z} BRep invalid"
        assert len(part.solids()) == 1, f"m{m} z{z} not single solid"
        bb = part.bounding_box()
        print(
            f"OK m{m} z{z}: "
            f"bbox={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f} "
            f"vol={part.volume:.1f}"
        )
