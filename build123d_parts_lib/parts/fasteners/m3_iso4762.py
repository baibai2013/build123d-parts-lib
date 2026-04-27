"""M3 ISO 4762 / DIN 912 hex socket head cap screw (simplified).

Source: data-sources/fasteners.yaml:M3_ISO4762 (skill build123d-cad)
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

# ===== M3 ISO 4762 参数 =====
HEAD_D = 5.5           # 头部直径
HEAD_H = 3.0           # 头部高度
THREAD_D = 3.0         # 螺纹大径（公称 M3）
DEFAULT_LENGTH = 10.0


def make_m3_screw(length: float = DEFAULT_LENGTH) -> Part:
    """生成 M3 内六角圆柱头螺丝简化实体（头 + 光杆）。

    Args:
        length: 螺杆长度（不含头部）。常见阶梯 5/6/8/10/12/14/16/20/25/30 mm

    几何：
        - 原点在杆底面中心
        - 杆沿 +Z 伸出 `length`
        - 头部贴在杆顶面，向上再伸出 `HEAD_H`
        - 总高 = length + HEAD_H
    """
    if length <= 0:
        raise ValueError(f"length must be > 0, got {length}")

    with BuildPart() as screw:
        # 光杆：底面在 Z=0，顶面在 Z=length
        Cylinder(
            radius=THREAD_D / 2, height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 头部：底面在 Z=length，顶面在 Z=length+HEAD_H
        with Locations(Location((0, 0, length))):
            Cylinder(
                radius=HEAD_D / 2, height=HEAD_H,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return screw.part


if __name__ == "__main__":
    part = make_m3_screw(length=DEFAULT_LENGTH)
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    export_step(part, str(cache_dir / f"m3_iso4762_L{int(DEFAULT_LENGTH)}.step"))
    print(f"OK: m3_iso4762_L10.step written, volume={part.volume:.1f} mm³")
