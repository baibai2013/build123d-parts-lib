"""精密光轴 / Smooth Shaft（简化模型）。

Source: data-sources/pins.yaml:SHAFT_D* (skill build123d-cad)
Reference: MISUMI PSFJ 系列精密光轴
License: MIT

支持规格：D4 / D5 / D6 / D8（长度范围见 VALID_LENGTHS）

简化程度：
- 光滑圆柱 + 两端倒角（与 pin_cylindrical.py 结构相同）
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Axis,
    BuildPart,
    Cylinder,
    Part,
    chamfer,
    export_step,
)

# 直径 -> (倒角长度, 默认长度, 最小长度, 最大长度)
_SHAFT_PARAMS: dict[float, tuple[float, float, float, float]] = {
    4.0: (0.5, 50.0,  20.0, 200.0),
    5.0: (0.5, 60.0,  20.0, 200.0),
    6.0: (0.8, 80.0,  20.0, 300.0),
    8.0: (1.0, 100.0, 30.0, 500.0),
}

VALID_DIAMETERS = sorted(_SHAFT_PARAMS.keys())


def make_smooth_shaft(diameter: float = 5.0, length: float = 60.0) -> Part:
    """生成精密光轴简化实体（圆柱 + 两端倒角）。

    Args:
        diameter: 公称直径（mm）。支持 4.0 / 5.0 / 6.0 / 8.0。
        length:   轴总长（mm）。

    坐标：
        - 原点在底面中心
        - 轴沿 +Z 伸出 `length`
    """
    if diameter not in _SHAFT_PARAMS:
        raise ValueError(
            f"不支持的直径 {diameter}mm，可选：{VALID_DIAMETERS}"
        )
    chamfer_l, default_l, min_l, max_l = _SHAFT_PARAMS[diameter]
    if length <= 0:
        raise ValueError(f"length 必须 > 0，得到 {length}")
    if not (min_l <= length <= max_l):
        raise ValueError(
            f"直径 {diameter}mm 的光轴长度范围 [{min_l}, {max_l}]mm，"
            f"得到 {length}mm"
        )

    with BuildPart() as shaft:
        Cylinder(
            radius=diameter / 2,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 两端倒角
        top_edge    = shaft.faces().sort_by(Axis.Z)[-1].edges()
        bottom_edge = shaft.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edge + bottom_edge, length=chamfer_l)

    return shaft.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    defaults = [(4.0, 50), (5.0, 60), (6.0, 80), (8.0, 100)]
    for d, l in defaults:
        part = make_smooth_shaft(diameter=d, length=l)
        out_path = cache_dir / f"shaft_smooth_d{int(d)}_L{int(l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  d{d}xL{l}mm  vol={part.volume:.3f} mm3")
