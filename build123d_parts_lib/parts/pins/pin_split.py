"""开口销 / Cotter Pin（简化模型）。

Source: data-sources/pins.yaml:SPLIT_PIN_* (skill build123d-cad)
Standards: ISO 1234
License: MIT

支持规格：D1.5 / D2 / D2.5 / D3（长度任意指定）

简化程度：
- 主轴圆柱（公称直径 d，长度 length）
- 顶部一个圆环头（外径 ≈ 2d，线径 ≈ 0.6d，环厚 ≈ d），用 Torus 建模
- 不建模两条分叉、弯折头细节
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Location,
    Mode,
    Part,
    Torus,
    add,
    export_step,
)

# 环头参数：(major_radius, minor_radius, ring_thickness)
# major_radius = 外径/2 - minor_radius（圆环中心半径）
# minor_radius = 线径/2 ≈ 0.3d
_RING_PARAMS: dict[float, tuple[float, float]] = {
    # d -> (torus major_radius, torus minor_radius)
    1.5: (1.5 * 2 / 2 - 1.5 * 0.3, 1.5 * 0.3),   # major=1.05, minor=0.45
    2.0: (2.0 * 2 / 2 - 2.0 * 0.3, 2.0 * 0.3),   # major=1.40, minor=0.60
    2.5: (2.5 * 2 / 2 - 2.5 * 0.3, 2.5 * 0.3),   # major=1.75, minor=0.75
    3.0: (3.0 * 2 / 2 - 3.0 * 0.3, 3.0 * 0.3),   # major=2.10, minor=0.90
}

VALID_DIAMETERS = sorted(_RING_PARAMS.keys())


def make_split_pin(diameter: float = 2.0, length: float = 16.0) -> Part:
    """生成开口销简化实体（主轴圆柱 + 顶部圆环头）。

    Args:
        diameter: 公称直径（mm）。支持 1.5 / 2.0 / 2.5 / 3.0。
        length:   销轴总长（mm），不含环头。

    坐标：
        - 原点在主轴底面中心
        - 销轴沿 +Z 伸出 `length`
        - 环头圆心在 Z = length + minor_radius 处
    """
    if diameter not in _RING_PARAMS:
        raise ValueError(
            f"不支持的直径 {diameter}mm，可选：{VALID_DIAMETERS}"
        )
    if length <= 0:
        raise ValueError(f"length 必须 > 0，得到 {length}")

    major_r, minor_r = _RING_PARAMS[diameter]

    with BuildPart() as pin:
        # 主轴圆柱
        Cylinder(
            radius=diameter / 2,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 圆环头：先建 Torus，再平移到轴顶端（环心高度 = length + minor_r）
        ring = Torus(major_radius=major_r, minor_radius=minor_r, mode=Mode.PRIVATE)
        add(ring.moved(Location((0, 0, length + minor_r))))

    return pin.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    defaults = [(1.5, 16), (2.0, 16), (2.5, 20), (3.0, 25)]
    for d, l in defaults:
        part = make_split_pin(diameter=d, length=l)
        d_str = str(d).replace(".", "_")
        out_path = cache_dir / f"pin_split_d{d_str}_L{int(l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  d{d}xL{l}mm  vol={part.volume:.3f} mm3")
