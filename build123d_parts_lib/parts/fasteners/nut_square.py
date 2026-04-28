"""DIN 562 square nut / 方形螺母.

Standards: DIN 562
License: MIT

支持规格: M3, M4, M5

几何:
- 正方形棱柱主体 / Square prism body
- 四条竖棱小倒角 / Small chamfer on four vertical corner edges
- 贯通 ISO 内螺纹 / Through ISO internal thread
- 原点底面中心，+Z 为轴方向
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    Box,
    BuildPart,
    Edge,
    Part,
    export_step,
)

from ._thread_utils import make_internal_thread


class SquareNutSpec(NamedTuple):
    d:     float   # 螺纹大径 / nominal thread diameter
    a:     float   # 方边长 / square side length
    m:     float   # 厚度（高度）/ height/thickness
    pitch: float   # 粗牙螺距 / coarse thread pitch


_FALLBACK: dict[str, SquareNutSpec] = {
    "M3": SquareNutSpec(d=3.0, a=5.5, m=1.8, pitch=0.50),
    "M4": SquareNutSpec(d=4.0, a=7.0, m=2.2, pitch=0.70),
    "M5": SquareNutSpec(d=5.0, a=8.0, m=2.7, pitch=0.80),
}


def _load_specs() -> dict[str, SquareNutSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, SquareNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "nut-square":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = SquareNutSpec(
                    d=float(thread["d"]),
                    a=float(dims["a"]),
                    m=float(dims["m"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_square_nut(size: str = "M4") -> Part:
    """DIN 562 方形螺母（正方形棱柱 + 四棱竖边倒角 + 贯通内螺纹）。
    DIN 562 square nut (square prism + corner chamfers + through internal thread).

    Args:
        size: 规格字符串 e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]

    with BuildPart() as bp:
        Box(spec.a, spec.a, spec.m,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = bp.part

    # Chamfer the 4 vertical corner edges (edges running along Z)
    chamfer_e = max(0.3, spec.a * 0.05)
    half_m = spec.m / 2
    vert_edges: list[Edge] = [
        e for e in solid.edges()
        if not e.is_closed
        and abs(e.center().Z - half_m) < spec.m * 0.45  # edge spans most of height
        and abs(e.length - spec.m) < 0.1                # length ≈ nut height
    ]
    if vert_edges:
        solid = solid.chamfer(chamfer_e, None, vert_edges)

    # Through internal thread
    thread_sub = make_internal_thread(spec.d, spec.pitch, spec.m)
    return solid.cut(thread_sub)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_square_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_nut_din562.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
