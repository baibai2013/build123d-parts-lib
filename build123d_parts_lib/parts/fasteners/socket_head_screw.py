"""ISO 4762 / DIN 912 hex socket head cap screw (simplified).

Source: data-sources/fasteners.yaml + parts/fasteners/fasteners.yaml (skill build123d-cad)
Standards: ISO 4762 / DIN 912
License: MIT

支持规格：M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10

简化程度：
- 头部圆柱（不建模内六角凹槽，仅外形）
- 杆部光杆（不建螺纹；装配用足够）
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, BuildPart, Cylinder, Location, Locations, Part, export_step,
)


class ScrewSpec(NamedTuple):
    d:      float   # 螺纹大径（公称直径）
    dk:     float   # 头部外径
    k:      float   # 头部高度
    pitch:  float   # 粗牙螺距


_SPECS: dict[str, ScrewSpec] = {
    "M2":   ScrewSpec(d=2.0, dk=3.8,  k=2.0,  pitch=0.40),
    "M2.5": ScrewSpec(d=2.5, dk=4.5,  k=2.5,  pitch=0.45),
    "M3":   ScrewSpec(d=3.0, dk=5.5,  k=3.0,  pitch=0.50),
    "M4":   ScrewSpec(d=4.0, dk=7.0,  k=4.0,  pitch=0.70),
    "M5":   ScrewSpec(d=5.0, dk=8.5,  k=5.0,  pitch=0.80),
    "M6":   ScrewSpec(d=6.0, dk=10.0, k=6.0,  pitch=1.00),
    "M8":   ScrewSpec(d=8.0, dk=13.0, k=8.0,  pitch=1.25),
    "M10":  ScrewSpec(d=10.0, dk=16.0, k=10.0, pitch=1.50),
}

DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 8.0, "M2.5": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
    "M6": 20.0, "M8": 25.0, "M10": 30.0,
}


def make_socket_head_screw(size: str = "M3", length: float | None = None) -> Part:
    """生成 ISO 4762 内六角圆柱头螺丝简化实体（头 + 光杆）。

    Args:
        size:   规格字符串，如 "M3"、"M2.5"。
        length: 螺杆长度（不含头部）。None 时取各规格默认值。

    几何：
        - 原点在杆底面中心
        - 杆沿 +Z 伸出 `length`
        - 头部在杆顶面向上再伸出 `k`
    """
    key = size.upper().replace("M0", "M").strip()
    # 兼容 "m3" / "M3" / "M 3"
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知规格 {size!r}，可用：{available}")

    spec = _SPECS[key]
    l = length if length is not None else DEFAULT_LENGTHS[key]
    if l <= 0:
        raise ValueError(f"length 必须 > 0，得到 {l}")

    with BuildPart() as screw:
        Cylinder(
            radius=spec.d / 2, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations(Location((0, 0, l))):
            Cylinder(
                radius=spec.dk / 2, height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return screw.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in DEFAULT_LENGTHS.items():
        part = make_socket_head_screw(size=size, length=default_l)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_iso4762_L{int(default_l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.1f} mm³")
