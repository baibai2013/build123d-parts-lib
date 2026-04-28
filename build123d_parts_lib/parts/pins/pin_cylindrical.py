"""Cylindrical dowel pin (simplified).

Source: data-sources/pins.yaml:PIN_D3~PIN_D6 (skill build123d-cad)
Standards: GB/T 119.1 / ISO 8734
License: MIT

支持规格：D3 / D4 / D5 / D6（长度任意指定）

简化程度：
- 光滑圆柱 + 两端倒角（chamfer）
- 不建模 m6 表面粗糙度与磨削纹理
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

# 标准倒角长度（GB/T 119.1）
_CHAMFERS: dict[float, float] = {
    3.0: 0.5,
    4.0: 0.5,
    5.0: 0.8,
    6.0: 1.0,
}

VALID_DIAMETERS = sorted(_CHAMFERS.keys())


def make_cylindrical_pin(diameter: float = 4.0, length: float = 20.0) -> Part:
    """生成精密圆柱销简化实体（光轴 + 两端倒角）。

    Args:
        diameter: 公称直径（mm）。支持 3.0 / 4.0 / 5.0 / 6.0。
        length:   销轴总长（mm）。

    坐标：
        - 原点在底面中心
        - 销轴沿 +Z 伸出 `length`
    """
    if diameter not in _CHAMFERS:
        raise ValueError(
            f"不支持的直径 {diameter}mm，可选：{VALID_DIAMETERS}"
        )
    if length <= 0:
        raise ValueError(f"length 必须 > 0，得到 {length}")

    chamfer_l = _CHAMFERS[diameter]

    with BuildPart() as pin:
        Cylinder(
            radius=diameter / 2,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 两端倒角
        top_edge    = pin.faces().sort_by(Axis.Z)[-1].edges()
        bottom_edge = pin.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edge + bottom_edge, length=chamfer_l)

    return pin.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    defaults = [(3.0, 12), (4.0, 20), (5.0, 20), (6.0, 25)]
    for d, l in defaults:
        part = make_cylindrical_pin(diameter=d, length=l)
        out_path = cache_dir / f"pin_d{int(d)}_L{int(l)}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(f"OK: {out_path.name}  "
              f"⌀{d:.0f}×{l}mm  vol={part.volume:.2f} mm³")
