"""M2.5 ISO 4762 / DIN 912 hex socket head cap screw (simplified).

Source: data-sources/fasteners.yaml:M2_5_ISO4762 (skill build123d-cad)
Standards: ISO 4762 / DIN 912
License: MIT

简化程度：
- 头部圆柱（不建模内六角凹槽，仅外形）
- 杆部光杆（不建螺纹；装配用足够，工程图再细化）
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align, BuildPart, Cylinder, Location, Locations, Part, export_step,
)

# ===== M2.5 ISO 4762 参数 =====
HEAD_D = 4.5           # 头部直径 dk
HEAD_H = 2.5           # 头部高度 k
THREAD_D = 2.5         # 螺纹大径（公称 M2.5）
DEFAULT_LENGTH = 8.0


def make_m2_5_screw(length: float = DEFAULT_LENGTH) -> Part:
    """生成 M2.5 内六角圆柱头螺丝简化实体（头 + 光杆）。

    Args:
        length: 螺杆长度（不含头部）。常见阶梯 4/5/6/8/10/12/16/20 mm

    几何：
        - 原点在杆底面中心
        - 杆沿 +Z 伸出 `length`
        - 头部贴在杆顶面，向上再伸出 `HEAD_H`
        - 总高 = length + HEAD_H
    """
    if length <= 0:
        raise ValueError(f"length must be > 0, got {length}")

    with BuildPart() as screw:
        # 光杆
        Cylinder(
            radius=THREAD_D / 2, height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 头部
        with Locations(Location((0, 0, length))):
            Cylinder(
                radius=HEAD_D / 2, height=HEAD_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return screw.part


if __name__ == "__main__":
    part = make_m2_5_screw(length=DEFAULT_LENGTH)
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    export_step(part, str(cache_dir / f"m2_5_iso4762_L{int(DEFAULT_LENGTH)}.step"))
    print(f"OK: m2_5_iso4762_L8.step written, volume={part.volume:.1f} mm³")
