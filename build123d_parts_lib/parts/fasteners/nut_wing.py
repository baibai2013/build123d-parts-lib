"""DIN 315 wing nut / 蝶形螺母.

Standards: DIN 315
License: MIT

支持规格: M3, M4, M5

几何:
- 圆柱轮毂 / Cylindrical hub body
- 两侧对称矩形翼片（±X 方向伸出，顶端大圆角）/ Two symmetric wing tabs (±X), rounded outer tips
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
    Cylinder,
    Edge,
    Location,
    Locations,
    Part,
    export_step,
)

from ._thread_utils import make_internal_thread


class WingNutSpec(NamedTuple):
    d:         float   # 螺纹大径 / nominal thread diameter
    hub_d:     float   # 轮毂外径 / hub outer diameter
    m:         float   # 总高 / total height
    wing_span: float   # 翼展（尖对尖）/ total wing span tip-to-tip
    wing_h:    float   # 翼片高度（Z 方向）/ wing plate height
    wing_w:    float   # 翼片厚度（Y 方向）/ wing plate thickness
    pitch:     float   # 粗牙螺距 / coarse thread pitch


_FALLBACK: dict[str, WingNutSpec] = {
    "M3": WingNutSpec(d=3.0, hub_d=10.0, m=11.0, wing_span=24.0, wing_h=9.5,  wing_w=2.0, pitch=0.50),
    "M4": WingNutSpec(d=4.0, hub_d=12.0, m=13.0, wing_span=28.0, wing_h=11.0, wing_w=2.5, pitch=0.70),
    "M5": WingNutSpec(d=5.0, hub_d=14.0, m=15.0, wing_span=32.0, wing_h=13.0, wing_w=3.0, pitch=0.80),
}


def _load_specs() -> dict[str, WingNutSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, WingNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "nut-wing":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = WingNutSpec(
                    d=float(thread["d"]),
                    hub_d=float(dims["hub_d"]),
                    m=float(dims["m"]),
                    wing_span=float(dims["wing_span"]),
                    wing_h=float(dims["wing_h"]),
                    wing_w=float(dims["wing_w"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_wing_nut(size: str = "M4") -> Part:
    """DIN 315 蝶形螺母（圆柱轮毂 + 两侧翼片 + 贯通内螺纹）。
    DIN 315 wing nut (cylindrical hub + two side wings + through internal thread).

    Args:
        size: 规格字符串 e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    hub_r = spec.hub_d / 2
    # Wing extends from hub edge outward; wing is positioned in ±X direction
    wing_reach = spec.wing_span / 2 - hub_r   # length of wing beyond hub edge

    # Hub cylinder
    with BuildPart() as hub_bp:
        Cylinder(radius=hub_r, height=spec.m,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

    hub_solid = hub_bp.part

    # Wing plates anchored at base (z=0 → z=wing_h); bolt-entry cylinder
    # protrudes above the wings, matching real DIN 315 geometry.
    wing_z_center = spec.wing_h / 2
    with BuildPart() as wingp_bp:
        with Locations(Location((hub_r + wing_reach / 2, 0, wing_z_center))):
            Box(wing_reach, spec.wing_w, spec.wing_h,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))

    with BuildPart() as wingn_bp:
        with Locations(Location((-(hub_r + wing_reach / 2), 0, wing_z_center))):
            Box(wing_reach, spec.wing_w, spec.wing_h,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))

    solid = hub_solid.fuse(wingp_bp.part).fuse(wingn_bp.part)

    # Fillet the two vertical corner edges at each outer wing tip
    # (the edges running along Z at the outermost ±Y corners of the wing).
    # Filter: near outer X face, near ±Y corners, length ≈ wing_h.
    fillet_r = min(spec.wing_w * 0.45, wing_reach * 0.4)
    outer_x_pos = spec.wing_span / 2
    outer_edges: list[Edge] = [
        e for e in solid.edges()
        if not e.is_closed
        and abs(abs(e.center().X) - outer_x_pos) < 0.5
        and abs(abs(e.center().Y) - spec.wing_w / 2) < 0.5
        and abs(e.length - spec.wing_h) < 2.0
    ]
    if outer_edges:
        solid = solid.fillet(fillet_r, outer_edges)

    # Through internal thread
    thread_sub = make_internal_thread(spec.d, spec.pitch, spec.m)
    return solid.cut(thread_sub)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_wing_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_nut_din315.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
