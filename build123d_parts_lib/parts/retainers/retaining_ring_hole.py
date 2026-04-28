"""孔用卡簧（Internal Retaining Ring，GB/T 893.1 / DIN 472）简化模型。

几何简化：带径向开口的薄圆环 + 两端耳洞。
建模时用 d_groove 作为外径（近似装入态），inner_d 为内径。

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


class HoleRingSpec(NamedTuple):
    d_groove: float    # 孔壁槽径（建模用外径），mm
    outer_d:  float    # 自由状态外径，mm
    inner_d:  float    # 自由状态内径，mm
    s:        float    # 厚度，mm
    gap:      float    # 开口宽度，mm
    ear_hole_r: float  # 耳洞半径，mm


# GB/T 893.1 / DIN 472 参数表（孔径 → 规格）
_SPECS: dict[str, HoleRingSpec] = {
    "D8":  HoleRingSpec(d_groove=8.4,  outer_d=7.2,  inner_d=5.0,  s=0.8, gap=1.7, ear_hole_r=0.9),
    "D10": HoleRingSpec(d_groove=10.4, outer_d=9.2,  inner_d=7.0,  s=1.0, gap=2.0, ear_hole_r=1.0),
    "D12": HoleRingSpec(d_groove=12.5, outer_d=11.0, inner_d=8.4,  s=1.0, gap=2.2, ear_hole_r=1.0),
    "D16": HoleRingSpec(d_groove=16.8, outer_d=14.8, inner_d=11.8, s=1.0, gap=2.7, ear_hole_r=1.2),
    "D20": HoleRingSpec(d_groove=21.0, outer_d=18.8, inner_d=14.8, s=1.0, gap=3.0, ear_hole_r=1.3),
    "D25": HoleRingSpec(d_groove=26.2, outer_d=23.5, inner_d=18.5, s=1.2, gap=3.4, ear_hole_r=1.5),
}

# 孔径 → key 的快速映射
_HOLE_D_MAP: dict[float, str] = {
    8.0: "D8", 10.0: "D10", 12.0: "D12",
    16.0: "D16", 20.0: "D20", 25.0: "D25",
}


def make_retaining_ring_hole(hole_d: float = 10.0) -> Part:
    """生成孔用卡簧简化实体。

    Args:
        hole_d: 孔公称直径（mm）。支持 8 / 10 / 12 / 16 / 20 / 25。

    坐标：
        - 环在 XY 平面，Z=0 底面，Z=s 顶面
        - 开口朝 +X 方向
        - 圆心在世界原点
    """
    key = _HOLE_D_MAP.get(float(hole_d))
    if key is None:
        available = ", ".join(str(k) for k in sorted(_HOLE_D_MAP))
        raise ValueError(
            f"不支持孔径 hole_d={hole_d}，可用值：{available}"
        )

    spec = _SPECS[key]
    # 建模用外径 = d_groove（装入态几何）
    outer_r = spec.d_groove / 2
    inner_r = spec.inner_d / 2
    s = spec.s
    gap = spec.gap
    ear_r = spec.ear_hole_r

    # 耳洞中心位置（开口两侧，在内外环交界处）
    ear_mid_r = (inner_r + outer_r) / 2
    half_gap_angle = math.degrees(math.asin(min(gap / 2 / outer_r, 1.0)))
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
            length=outer_r + 1.0,
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

    for hole_d, key in sorted(_HOLE_D_MAP.items()):
        part = make_retaining_ring_hole(hole_d)
        slug = f"ring_hole_{key.lower()}"
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(
            f"OK: {out_path.name}  "
            f"d{bb.size.X:.1f}x{bb.size.Z:.2f}mm  "
            f"vol={part.volume:.3f} mm3"
        )
