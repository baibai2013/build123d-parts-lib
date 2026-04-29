"""Helical cylindrical gear — industrial 3D-printable parametric model.

Source: Involute helical gear geometry (standard references)
Standards: ISO 54 (cylindrical gears, normal module series)
License: MIT

支持规格 / Supported specs:
- 法向模数 / normal module mn: 1.0 / 1.5 / 2.0
- 齿数 / teeth z: 20 / 30
- 螺旋角 / helix angle β: 15° / 20° (左旋正 / 右旋传 -β)
- 孔径 / bore_d: 5 / 6 / 8 / 10 mm

简化程度 / Simplification level: ★★★★★
- 渐开线端面齿廓 (involute transverse profile, 8 samples per flank)
- 多截面 Loft 堆叠法沿 Z 方向扭转 (multi-section loft along Z — recommended Plan A)
- 每齿独立 Loft + 根圆柱布尔融合 (per-tooth loft + root cylinder boolean fusion)
- 齿根圆角做成直齿根圆弧过渡 (root arc transition)
- 不建倒角 / 不建键槽 (keyway/chamfer omitted for simplicity)
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    Cylinder,
    Face,
    Part,
    Wire,
    export_step,
    loft,
)
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace  # type: ignore[import-untyped]
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt  # type: ignore[import-untyped]


class HelicalGearSpec(NamedTuple):
    module: float        # 法向模数 mn (mm)
    teeth: int           # 齿数 z
    helix_angle: float   # 螺旋角 β (度)
    bore_d: float        # 孔径 (mm)
    face_width: float    # 齿宽 (mm)
    pressure_angle: float  # 法向压力角 αn (度)
    # 推导量 / Derived
    mt: float            # 端面模数 / transverse module
    pitch_d: float       # 端面分度圆直径 / transverse pitch diameter
    outer_d: float       # 齿顶圆直径 / addendum diameter
    root_d: float        # 齿根圆直径 / dedendum diameter
    twist_deg: float     # 总扭转角度 / total twist across face_width


# ===== 内部几何辅助 / Internal helpers =====

_N_LAYERS = 10          # Loft 截面层数 / number of loft sections (≥8 for smooth helix)
_TOOTH_STEPS = 8        # 渐开线采样数 / involute samples per flank


def _tooth_pts_2d(
    tooth_idx: int,
    teeth: int,
    base_r: float,
    pitch_r: float,
    addendum_r: float,
    root_r: float,
    steps: int = _TOOTH_STEPS,
):
    """Return 2-D point list of one tooth profile on the transverse plane.

    直接复用 08_gear_spur_v2.py 的 tooth_pts() 算法：
    沿渐开线左/右齿廓采样 + 齿根圆弧衔接。
    Reused from the spur-gear reference: involute flanks + root arc closure.
    """
    pitch_angle = 2 * math.pi / teeth
    half_t = math.pi / (2 * teeth)
    a_i = pitch_angle * tooth_idx
    inv_max = math.sqrt(max(0.0, (addendum_r / base_r) ** 2 - 1))

    left = []
    for s in range(steps + 1):
        t = s / steps
        ia = inv_max * t
        r = base_r * math.sqrt(1 + ia ** 2)
        if r < root_r:
            continue
        r = min(r, addendum_r)
        th = a_i + half_t - ia + math.atan(ia)
        left.append((r * math.cos(th), r * math.sin(th)))

    right = []
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
        (root_r * math.cos(th_r + (th_l - th_r) * k / 4),
         root_r * math.sin(th_r + (th_l - th_r) * k / 4))
        for k in range(1, 4)
    ]
    return left + right + arc_pts


def _rotate_pts(pts, theta_rad):
    """Rotate 2-D points by theta radians about origin."""
    ct, st = math.cos(theta_rad), math.sin(theta_rad)
    return [(x * ct - y * st, x * st + y * ct) for x, y in pts]


def _make_face_at_z(pts_2d, z):
    """Build a planar face on the plane Z = z from 2-D points."""
    plane = gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1))
    wire = Wire.make_polygon([(x, y, z) for x, y in pts_2d], close=True)
    return Face(BRepBuilderAPI_MakeFace(plane, wire.wrapped, True).Face())


def _derive_spec(
    module: float,
    teeth: int,
    helix_angle: float,
    bore_d: float,
    face_width: float | None,
    pressure_angle: float,
) -> HelicalGearSpec:
    """Compute derived helical gear geometry.

    核心换算 / Core conversions:
    - mt = mn / cos(β)
    - d  = mt × z
    - da = d + 2·mn     (齿顶圆 / addendum circle)
    - df = d - 2.5·mn   (齿根圆 / dedendum circle)
    - tan(αt) = tan(αn)/cos(β)
    - Δθ = face_width × tan(β) / (d/2) × 180/π   (degrees)
    """
    fw = face_width if face_width is not None else 10.0 * module
    beta_rad = math.radians(helix_angle)
    mt = module / math.cos(beta_rad)
    pitch_d = mt * teeth
    outer_d = pitch_d + 2 * module
    root_d = pitch_d - 2.5 * module
    # 沿齿宽的总扭转角 (度) / total twist (deg) — 注意 β 的符号决定旋向
    twist_deg = (fw * math.tan(beta_rad) / (pitch_d / 2)) * (180.0 / math.pi)
    return HelicalGearSpec(
        module=module,
        teeth=teeth,
        helix_angle=helix_angle,
        bore_d=bore_d,
        face_width=fw,
        pressure_angle=pressure_angle,
        mt=round(mt, 4),
        pitch_d=round(pitch_d, 3),
        outer_d=round(outer_d, 3),
        root_d=round(root_d, 3),
        twist_deg=round(twist_deg, 3),
    )


# ===== 对外 API / Public API =====


def make_helical_gear(
    module: float = 1.0,
    teeth: int = 20,
    helix_angle: float = 15.0,
    bore_d: float = 5.0,
    face_width: float | None = None,
    pressure_angle: float = 20.0,
) -> Part:
    """Generate a helical cylindrical gear.

    Args:
        module:         Normal module mn (mm).
        teeth:          Number of teeth z.
        helix_angle:    Helix angle β in degrees (左旋/LH = +β, 右旋/RH = -β).
        bore_d:         Central bore diameter (mm).
        face_width:     Gear face width b (mm). ``None`` → 10 × module.
        pressure_angle: Normal pressure angle αn (degrees).

    Coordinate system:
        - Z axis = rotational axis.
        - Geometric center at origin; Z ∈ [-b/2, +b/2].

    Strategy (Plan A — multi-section loft):
        1. 端面模数 mt = mn/cos(β), 推得端面分度/齿顶/齿根/基圆
           (derive transverse module and circles).
        2. 采样 N_LAYERS 个 Z 层,每层旋转 θ = total_twist × (layer/N)
           (sample N layers, rotate each by θ to build helix).
        3. 每齿 loft N 个截面为单齿螺旋体
           (per-tooth loft → helical tooth solid).
        4. 根圆柱 + 逐齿布尔融合,再挖中心孔
           (root cylinder + per-tooth fuse, then subtract bore).
    """
    if teeth < 6:
        raise ValueError(f"teeth={teeth} too small (min 6)")
    if abs(helix_angle) >= 45:
        raise ValueError(f"helix_angle={helix_angle}° out of practical range")

    spec = _derive_spec(module, teeth, helix_angle, bore_d, face_width, pressure_angle)
    fw = spec.face_width
    half_h = fw / 2

    base_r = (spec.pitch_d / 2) * math.cos(
        math.atan(math.tan(math.radians(pressure_angle)) / math.cos(math.radians(helix_angle)))
    )
    pitch_r = spec.pitch_d / 2
    addendum_r = spec.outer_d / 2
    root_r = spec.root_d / 2

    if bore_d >= spec.root_d:
        raise ValueError(
            f"bore_d={bore_d} >= root_d={spec.root_d}; reduce bore or increase teeth"
        )

    # ── 根圆柱作为实体骨架 / root cylinder as body skeleton ──
    gear: Part = Cylinder(
        radius=root_r,
        height=fw,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # ── 每齿独立 Loft / per-tooth loft ──
    # 关键算法 / Key algorithm:
    #   对第 i 齿,构造 _N_LAYERS+1 个等距 Z 平面截面,
    #   每层齿形在底截面基础上绕 Z 旋转 theta_layer = twist × (layer / N) 度,
    #   然后把这些截面 loft 成一个螺旋齿实体。
    #   For tooth i: stack N+1 sections along Z, each rotated by
    #   theta_layer = twist × (layer/N) around the Z axis, then loft.
    fused = 0
    for i in range(teeth):
        base_pts = _tooth_pts_2d(i, teeth, base_r, pitch_r, addendum_r, root_r)
        if base_pts is None:
            continue

        section_faces = []
        for layer in range(_N_LAYERS + 1):
            frac = layer / _N_LAYERS
            z = -half_h + frac * fw
            # β 的正负决定旋向：LH = +θ,RH = -θ / sign of β → handedness
            theta_rad = math.radians(spec.twist_deg) * frac
            pts_rot = _rotate_pts(base_pts, theta_rad)
            section_faces.append(_make_face_at_z(pts_rot, z))

        # loft ruled=False 让 OCCT 用 B-spline 生成光滑螺旋齿面
        # loft with ruled=False → smooth B-spline helical flank
        tooth_solid = loft(section_faces, ruled=False)
        gear = gear + tooth_solid
        fused += 1

    # ── 中心孔 / central bore (algebra-mode subtract) ──
    bore = Cylinder(
        radius=bore_d / 2,
        height=fw + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    gear = gear - bore
    return gear


# ===== 批量生成入口 / Batch entry =====

if __name__ == "__main__":
    # Smoke-test / 冒烟断言（不写 cache；cache 由 scripts/build_cache.py 统一生成）
    combos = [
        # (mn, teeth, beta_deg, bore)
        (1.0, 20, 15.0, 5.0),
        (1.0, 30, 15.0, 8.0),
        (1.5, 20, 20.0, 6.0),
        (1.5, 30, 20.0, 8.0),
        (2.0, 20, 15.0, 8.0),
        (2.0, 30, 20.0, 10.0),
    ]

    print("Helical Gear — smoke test")
    for mn, z, beta, bore in combos:
        part = make_helical_gear(
            module=mn, teeth=z, helix_angle=beta, bore_d=bore
        )
        assert part.is_valid, f"mn{mn} z{z} β{beta}: BRep invalid"
        assert len(part.solids()) == 1, f"mn{mn} z{z}: not single solid"
        bb = part.bounding_box()
        print(
            f"OK  helical mn{mn} z{z} β{int(beta)}° bore{int(bore)}:  "
            f"bbox={bb.size.X:.2f}x{bb.size.Y:.2f}x{bb.size.Z:.2f}mm  "
            f"vol={part.volume:.2f} mm3"
        )
