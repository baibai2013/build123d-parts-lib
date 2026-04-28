"""GT2 timing belt (2 mm pitch) — closed loop, simplified stadium-section placeholder.

Source: GT2 belt standard (Gates Rubber / RepRap community)
Standards: GT2 (2 mm pitch, 6 mm width)
License: MIT

支持规格：L110 / L158 / L200 / L280 / L380（周长 mm）

简化程度：
- 跑道形（stadium）截面：两段直线 + 两端半圆弧
- 实心带板，不建精确齿形
- 足够装配占位与传动路径可视化
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    export_step,
)
from build123d import extrude as bd_extrude

# GT2 带标准厚度
_THICKNESS = 1.38  # mm（GT2 带厚，橡胶基带）

# 常用周长列表 (mm)
_COMMON_LENGTHS = [110.0, 158.0, 200.0, 280.0, 380.0]


def make_gt2_belt(
    length: float = 200.0,
    width: float = 6.0,
    pulley_d: float = 12.7,
) -> Part:
    """Generate a simplified GT2 closed-loop belt solid (stadium-shaped cross section).

    The belt is modeled as a hollow tube with stadium (rounded rectangle) cross-section.
    Teeth are NOT modeled — this is an assembly placeholder.

    Args:
        length:   Belt circumference in mm (e.g. 110 / 158 / 200 / 280 / 380).
        width:    Belt width in mm, default 6.0 (standard GT2).
        pulley_d: End-arc diameter (matching small pulley pitch diameter), default 12.7 mm (20T).

    Coordinate system:
        - Belt lies in the XZ plane (loop runs in X direction, thickness in Y).
        - Z direction = belt width (立起来).
        - Origin at geometric center of the belt loop.

    几何算法：
        r = pulley_d / 2（两端半圆半径）
        两端半圆周长 = π × pulley_d
        直线段长 = (length - π × pulley_d) / 2
        管壁厚 = _THICKNESS
    """
    r = pulley_d / 2
    semicircle_total = math.pi * pulley_d
    straight_len = (length - semicircle_total) / 2

    if straight_len <= 0:
        raise ValueError(
            f"带长 {length} mm 太短：两端半圆周长 {semicircle_total:.2f} mm 已超过带长。"
            f"建议 length > {semicircle_total:.1f}"
        )

    # 跑道形中心线坐标（在 XY 平面，后续绕 X 轴立起来变成 XZ）
    # 两端圆心在 X 轴上，相距 straight_len
    cx = straight_len / 2   # 右端圆心 X
    # 外轮廓：上直线 + 右半圆 + 下直线 + 左半圆
    # 用 BuildSketch 画跑道形

    def _stadium_face(radius: float) -> object:
        """Build a stadium face in XY plane with given half-width radius."""
        with BuildSketch(Plane.XY) as sk:
            # 矩形主体（去掉两端预留半圆）
            Rectangle(straight_len, radius * 2,
                      align=(Align.CENTER, Align.CENTER))
            # 左端半圆
            with Locations(Location((-cx, 0, 0))):
                Circle(radius)
            # 右端半圆
            with Locations(Location((cx, 0, 0))):
                Circle(radius)
        return sk.sketch

    # 外轮廓 (r + thickness) 和内轮廓 (r) 分别做 face 然后挤出成中空管
    outer_r = r + _THICKNESS
    outer_sk = _stadium_face(outer_r)
    inner_sk = _stadium_face(r)

    with BuildPart() as belt:
        # 外轮廓挤出
        with BuildSketch(Plane.XY) as sk_outer:
            Rectangle(straight_len, outer_r * 2,
                      align=(Align.CENTER, Align.CENTER))
            with Locations(Location((-cx, 0, 0))):
                Circle(outer_r)
            with Locations(Location((cx, 0, 0))):
                Circle(outer_r)
        bd_extrude(amount=width)

        # 减去内轮廓（镂空）
        with BuildSketch(Plane.XY) as sk_inner:
            Rectangle(straight_len, r * 2,
                      align=(Align.CENTER, Align.CENTER))
            with Locations(Location((-cx, 0, 0))):
                Circle(r)
            with Locations(Location((cx, 0, 0))):
                Circle(r)
        bd_extrude(amount=width, mode=Mode.SUBTRACT)

    # 将带绕 X 轴转 90°，使带宽沿 Z 方向（立起来）
    part = belt.part
    part = part.rotate(Axis.X, 90)
    return part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for length in _COMMON_LENGTHS:
        part = make_gt2_belt(length=length)
        slug = f"gt2_belt_l{int(length)}"
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(
            f"OK: {out_path.name}  "
            f"bbox={bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f}mm  "
            f"vol={part.volume:.2f} mm3"
        )
