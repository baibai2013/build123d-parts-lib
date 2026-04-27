"""弹性圆柱销 / Roll Pin（简化模型）。

Source: data-sources/pins.yaml:SPRING_PIN_* (skill build123d-cad)
Standards: ISO 8752
License: MIT

支持规格：D3 / D4 / D5 / D6（长度任意指定）

简化程度：
- 空心圆柱（外径 od，内径 od - 2t）
- 不建模纵向开缝
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align, Axis, BuildPart, Cylinder, Part, export_step,
)

# 外径 -> 壁厚（ISO 8752 轻型系列）
_WALL_THICKNESS: dict[float, float] = {
    3.0: 0.5,
    4.0: 0.6,
    5.0: 0.8,
    6.0: 1.0,
}

VALID_DIAMETERS = sorted(_WALL_THICKNESS.keys())


def make_spring_pin(diameter: float = 4.0, length: float = 20.0) -> Part:
    """生成弹性圆柱销简化实体（空心圆柱）。

    Args:
        diameter: 公称外径（mm）。支持 3.0 / 4.0 / 5.0 / 6.0。
        length:   销轴总长（mm）。

    坐标：
        - 原点在底面中心
        - 销轴沿 +Z 伸出 `length`
    """
    if diameter not in _WALL_THICKNESS:
        raise ValueError(
            f"不支持的直径 {diameter}mm，可选：{VALID_DIAMETERS}"
        )
    if length <= 0:
        raise ValueError(f"length 必须 > 0，得到 {length}")

    t = _WALL_THICKNESS[diameter]
    od = diameter
    id_ = od - 2 * t

    with BuildPart() as pin:
        # 外圆柱
        Cylinder(
            radius=od / 2,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 内孔（减去内圆柱）
        Cylinder(
            radius=id_ / 2,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=__import__("build123d", fromlist=["Mode"]).Mode.SUBTRACT,
        )

    return pin.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    defaults = [(3.0, 16), (4.0, 20), (5.0, 24), (6.0, 30)]
    for d, l in defaults:
        part = make_spring_pin(diameter=d, length=l)
        out_path = cache_dir / f"pin_spring_d{int(d)}_L{int(l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  d{d}xL{l}mm  vol={part.volume:.3f} mm3")
