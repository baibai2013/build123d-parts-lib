"""轴用卡簧（External Retaining Ring，GB/T 894.1 / DIN 471）简化模型。

几何简化：带径向开口的薄圆环 + 两端耳洞。
建模坐标：环在 XY 平面，Z=0 为底面，Z=s 为顶面，开口朝 +X。

License: MIT
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Hole,
    Location,
    Locations,
    Mode,
    Part,
    export_step,
)


class ShaftRingSpec(NamedTuple):
    d_groove: float    # 槽径（装入后内径），mm
    outer_d:  float    # 自由状态外径，mm
    s:        float    # 厚度，mm
    gap:      float    # 开口宽度，mm
    ear_hole_r: float  # 耳洞半径，mm


# GB/T 894.1 / DIN 471 参数表（轴径 → 规格）
_SPECS: dict[str, ShaftRingSpec] = {
    "D4":  ShaftRingSpec(d_groove=3.8,  outer_d=8.0,  s=0.4, gap=0.9, ear_hole_r=0.5),
    "D5":  ShaftRingSpec(d_groove=4.8,  outer_d=9.6,  s=0.6, gap=1.1, ear_hole_r=0.6),
    "D6":  ShaftRingSpec(d_groove=5.7,  outer_d=11.8, s=0.7, gap=1.3, ear_hole_r=0.7),
    "D8":  ShaftRingSpec(d_groove=7.6,  outer_d=14.8, s=0.8, gap=1.7, ear_hole_r=0.9),
    "D10": ShaftRingSpec(d_groove=9.6,  outer_d=18.0, s=1.0, gap=2.0, ear_hole_r=1.0),
    "D12": ShaftRingSpec(d_groove=11.5, outer_d=20.2, s=1.0, gap=2.2, ear_hole_r=1.0),
}

# 轴径 → key 的快速映射
_SHAFT_D_MAP: dict[float, str] = {
    4.0: "D4", 5.0: "D5", 6.0: "D6",
    8.0: "D8", 10.0: "D10", 12.0: "D12",
}


def make_retaining_ring_shaft(shaft_d: float = 5.0) -> Part:
    """生成轴用卡簧简化实体。

    Args:
        shaft_d: 轴公称直径（mm）。支持 4 / 5 / 6 / 8 / 10 / 12。

    坐标：
        - 环在 XY 平面，Z=0 底面，Z=s 顶面
        - 开口朝 +X 方向
        - 圆心在世界原点
    """
    key = _SHAFT_D_MAP.get(float(shaft_d))
    if key is None:
        available = ", ".join(str(k) for k in sorted(_SHAFT_D_MAP))
        raise ValueError(
            f"不支持轴径 shaft_d={shaft_d}，可用值：{available}"
        )

    spec = _SPECS[key]
    inner_r = spec.d_groove / 2
    outer_r = spec.outer_d / 2
    s = spec.s
    gap = spec.gap
    ear_r = spec.ear_hole_r

    # 耳洞中心位置（开口两侧，在内外环交界处）
    ear_mid_r = (inner_r + outer_r) / 2
    # 开口半角（gap/2 对应的角度）
    half_gap_angle = math.degrees(math.asin(min(gap / 2 / outer_r, 1.0)))
    # 耳洞在开口两侧各偏 ~20° 处（简化定位）
    ear_angle_offset = half_gap_angle + 15.0
    ear_angle_rad = math.radians(ear_angle_offset)
    ear_x1 = ear_mid_r * math.cos(ear_angle_rad)
    ear_y1 = ear_mid_r * math.sin(ear_angle_rad)
    ear_x2 = ear_mid_r * math.cos(-ear_angle_rad)
    ear_y2 = ear_mid_r * math.sin(-ear_angle_rad)

    with BuildPart() as ring:
        # 外圆环（底面 Z=0）
        Cylinder(
            radius=outer_r,
            height=s,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 减去内孔
        Cylinder(
            radius=inner_r,
            height=s,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 开口槽：沿 +X 方向，宽 gap，从圆心延伸到外环外
        Box(
            length=outer_r + 1.0,  # 稍超过外径保证完全切穿
            width=gap,
            height=s,
            align=(Align.MIN, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 耳洞 1（开口上侧）
        with Locations(Location((ear_x1, ear_y1, s / 2))):
            Hole(radius=ear_r, depth=s)
        # 耳洞 2（开口下侧）
        with Locations(Location((ear_x2, ear_y2, s / 2))):
            Hole(radius=ear_r, depth=s)

    return ring.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for shaft_d, key in sorted(_SHAFT_D_MAP.items()):
        part = make_retaining_ring_shaft(shaft_d)
        slug = f"ring_shaft_{key.lower()}"
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(
            f"OK: {out_path.name}  "
            f"d{bb.size.X:.1f}x{bb.size.Z:.2f}mm  "
            f"vol={part.volume:.3f} mm3"
        )
