"""DIN 1587 cap nut / 盖形螺母 (acorn nut).

Standards: DIN 1587
License: MIT

支持规格: M3, M4, M5

几何:
- 六棱柱下体 + 顶部半球形冠（大圆角成穹顶）/ Hex lower body + spherical dome (large fillet)
- 盲孔内螺纹（不贯通）/ Blind bore internal thread
- 原点底面中心，+Z 为轴方向
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
    Edge,
    Location,
    Locations,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)

from ._thread_utils import make_internal_thread


class CapNutSpec(NamedTuple):
    d:     float   # 螺纹大径 / nominal thread diameter
    s:     float   # 六棱对边宽 / hex across-flats
    m:     float   # 总高（含穹顶）/ total height including dome
    pitch: float   # 粗牙螺距 / coarse thread pitch


_FALLBACK: dict[str, CapNutSpec] = {
    "M3": CapNutSpec(d=3.0, s=5.5, m=5.0,  pitch=0.50),
    "M4": CapNutSpec(d=4.0, s=7.0, m=6.5,  pitch=0.70),
    "M5": CapNutSpec(d=5.0, s=8.0, m=8.0,  pitch=0.80),
}


def _load_specs() -> dict[str, CapNutSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, CapNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "nut-cap":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = CapNutSpec(
                    d=float(thread["d"]),
                    s=float(dims["s"]),
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


def make_cap_nut(size: str = "M4") -> Part:
    """DIN 1587 盖形螺母（六棱柱 + 球面穹顶 + 盲孔内螺纹）。
    DIN 1587 cap nut (hex body + spherical dome cap + blind internal thread).

    Args:
        size: 规格字符串 e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    r_hex = spec.s / math.sqrt(3)   # hex circumradius (vertex-to-centre)
    cap_r = spec.s / 2              # dome outer radius = hex inscribed radius
    m_hex = spec.m * 0.42           # height of lower hex body
    cap_h = spec.m - m_hex          # height of dome cylinder body
    tol = 1e-3

    # Hex body + dome cylinder in same BuildPart (auto-fused)
    with BuildPart() as hex_bp:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=m_hex)

    with BuildPart() as cap_bp:
        Cylinder(radius=cap_r, height=cap_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = hex_bp.part.fuse(cap_bp.part.translate((0, 0, m_hex)))

    # Large fillet on dome top circular edge → spherical cap
    fillet_r = cap_h * 0.92
    top_edges: list[Edge] = [
        e for e in solid.edges()
        if e.is_closed and abs(e.center().Z - spec.m) < tol
    ]
    if top_edges:
        solid = solid.fillet(fillet_r, top_edges)

    # Blind threaded bore from bottom (leaves dome wall intact)
    bore_depth = m_hex + cap_h * 0.30
    thread_sub = make_internal_thread(spec.d, spec.pitch, bore_depth)
    return solid.cut(thread_sub)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_cap_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_nut_din1587.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
