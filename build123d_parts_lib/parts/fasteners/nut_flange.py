"""DIN 6923 flange nut / 法兰螺母.

Standards: DIN 6923
License: MIT

支持规格: M3, M4, M5

几何:
- 底部薄圆盘法兰 / Thin circular flange disc at base
- 上方六棱柱螺母体 / Hex nut body above flange
- 贯通 ISO 内螺纹 / Through ISO internal thread
- 原点法兰底面中心，+Z 为轴方向
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cylinder,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)

from ._thread_utils import make_internal_thread


class FlangeNutSpec(NamedTuple):
    d:        float   # 螺纹大径 / nominal thread diameter
    s:        float   # 六棱对边宽 / hex across-flats
    m:        float   # 六棱柱高（不含法兰）/ hex height excl. flange
    flange_d: float   # 法兰外径 / flange outer diameter
    flange_t: float   # 法兰厚度 / flange thickness
    pitch:    float   # 粗牙螺距 / coarse thread pitch


_FALLBACK: dict[str, FlangeNutSpec] = {
    "M3": FlangeNutSpec(d=3.0, s=5.5,  m=4.0, flange_d=9.0,  flange_t=1.0, pitch=0.50),
    "M4": FlangeNutSpec(d=4.0, s=7.0,  m=5.0, flange_d=11.0, flange_t=1.0, pitch=0.70),
    "M5": FlangeNutSpec(d=5.0, s=8.0,  m=6.5, flange_d=13.5, flange_t=1.2, pitch=0.80),
}


def _load_specs() -> dict[str, FlangeNutSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, FlangeNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "nut-flange":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = FlangeNutSpec(
                    d=float(thread["d"]),
                    s=float(dims["s"]),
                    m=float(dims["m"]),
                    flange_d=float(dims["flange_d"]),
                    flange_t=float(dims["flange_t"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_flange_nut(size: str = "M4") -> Part:
    """DIN 6923 法兰螺母（圆盘法兰底 + 六棱柱体 + 贯通内螺纹）。
    DIN 6923 flange nut (disc flange base + hex body + through internal thread).

    Args:
        size: 规格字符串 e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    r_hex = spec.s / math.sqrt(3)
    total_h = spec.flange_t + spec.m

    # Flange disc
    with BuildPart() as flange_bp:
        Cylinder(radius=spec.flange_d / 2, height=spec.flange_t,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Hex body
    with BuildPart() as hex_bp:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=spec.m)

    solid = flange_bp.part.fuse(hex_bp.part.translate((0, 0, spec.flange_t)))

    # Through internal thread
    thread_sub = make_internal_thread(spec.d, spec.pitch, total_h)
    return solid.cut(thread_sub)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_flange_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_nut_din6923.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
