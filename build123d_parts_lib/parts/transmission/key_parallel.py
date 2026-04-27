"""ISO 2491 / DIN 6885 parallel key (flat key) — simplified solid.

Source: ISO 2491 / DIN 6885A standard
Standards: ISO 2491, DIN 6885
License: MIT

支持规格（宽×高）：3×3 / 4×4 / 5×5 / 6×6 / 8×7
各规格对应标准长度列表见 _SPECS。

简化程度：
- 主体长方体 + 两端半圆（跑道形/圆头平键）
- 不建键槽配合圆角；足够装配占位
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, Axis, BuildPart, BuildSketch,
    Circle, Cylinder, Location, Locations,
    Mode, Part, Plane, Rectangle,
    export_step,
)
from build123d import extrude as bd_extrude


class KeySpec(NamedTuple):
    width: float    # 键宽 b (mm)
    height: float   # 键高 h (mm)
    lengths: list   # 标准长度列表 (mm)


# 参数表（ISO 2491 / DIN 6885 标准规格）
_SPECS: dict[str, KeySpec] = {
    "3x3": KeySpec(width=3.0, height=3.0, lengths=[10, 12, 16, 20]),
    "4x4": KeySpec(width=4.0, height=4.0, lengths=[10, 12, 16, 20, 25]),
    "5x5": KeySpec(width=5.0, height=5.0, lengths=[16, 20, 25, 32, 40]),
    "6x6": KeySpec(width=6.0, height=6.0, lengths=[20, 25, 32, 40, 50]),
    "8x7": KeySpec(width=8.0, height=7.0, lengths=[25, 32, 40, 50]),
}


def make_parallel_key(
    width: float = 5.0,
    height: float = 5.0,
    length: float = 20.0,
) -> Part:
    """Generate an ISO 2491 parallel key solid (stadium cross-section).

    The key is modeled with rounded ends (half-circle on both ends), as per
    the 'A' form (round-ended) of DIN 6885A.

    Args:
        width:  Key width b in mm (3 / 4 / 5 / 6 / 8).
        height: Key height h in mm (matching width, except 8x7).
        length: Key length L in mm.

    Coordinate system:
        - Length along X axis.
        - Width along Y axis (centered).
        - Height along Z axis (Z=0 at bottom face, Z=height at top).

    几何：
        - 跑道形截面（XY 平面）：矩形 (length-width) × width + 两端半圆 r=width/2
        - 沿 Z 方向挤出 height
    """
    if length < width:
        raise ValueError(
            f"length={length} 必须 >= width={width}（两端半圆需要空间）"
        )
    if width <= 0 or height <= 0 or length <= 0:
        raise ValueError("width/height/length 均须 > 0")

    r = width / 2
    straight = length - width   # 中间矩形段长度（两端预留给半圆）
    cx = straight / 2           # 端部半圆圆心 X 偏移

    with BuildPart() as key:
        with BuildSketch(Plane.XY) as sk:
            if straight > 0:
                Rectangle(straight, width,
                          align=(Align.CENTER, Align.CENTER))
            # 左端半圆
            with Locations(Location((-cx, 0, 0))):
                Circle(r)
            # 右端半圆
            with Locations(Location((cx, 0, 0))):
                Circle(r)
        bd_extrude(amount=height)

    # 将实体移到 Z=0 为底面（extrude 默认从 Z=0 向上，已符合要求）
    return key.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for spec_name, spec in _SPECS.items():
        for length in spec.lengths:
            part = make_parallel_key(
                width=spec.width,
                height=spec.height,
                length=float(length),
            )
            slug = f"key_{spec_name.replace('x', 'x')}_l{length}"
            out_path = cache_dir / f"{slug}.step"
            export_step(part, str(out_path))
            bb = part.bounding_box()
            print(
                f"OK: {out_path.name}  "
                f"{bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f}mm  "
                f"vol={part.volume:.2f} mm3"
            )
