"""ISO 10642 hex socket countersunk head screw (simplified).

Standards: ISO 10642
License: MIT

Supported sizes: M2 / M2.5 / M3 / M4 / M5

Simplification:
- Conical head (90° included angle), no internal hex recess modelled
- Plain shank (no thread; sufficient for assembly use)
- Origin at bottom of shank, shank along +Z, head flares upward at top
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, Axis, BuildPart, BuildSketch, Cone, Cylinder,
    Location, Locations, Mode, Part, Plane, Polyline,
    RegularPolygon, export_step, make_face,
)


class ScrewSpec(NamedTuple):
    d:  float   # nominal thread diameter
    dk: float   # head top diameter (widest, flush with surface)
    k:  float   # head height
    pitch: float  # coarse thread pitch


_SPECS: dict[str, ScrewSpec] = {
    "M2":   ScrewSpec(d=2.0, dk=3.8,  k=1.1,  pitch=0.40),
    "M2.5": ScrewSpec(d=2.5, dk=4.7,  k=1.5,  pitch=0.45),
    "M3":   ScrewSpec(d=3.0, dk=5.6,  k=1.65, pitch=0.50),
    "M4":   ScrewSpec(d=4.0, dk=7.5,  k=2.2,  pitch=0.70),
    "M5":   ScrewSpec(d=5.0, dk=9.2,  k=2.75, pitch=0.80),
}

DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 8.0, "M2.5": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
}


def make_countersunk_screw(size: str = "M3", length: float | None = None) -> Part:
    """Generate an ISO 10642 countersunk screw simplified solid (cone head + plain shank).

    Args:
        size:   Size string, e.g. "M3", "M2.5".
        length: Shank length (excluding head). None uses per-size defaults.

    Geometry:
        - Origin at bottom of shank
        - Shank extends along +Z by `length`
        - Conical head sits atop the shank: base diameter = d (shank OD),
          top diameter = dk, height = k (cone flares outward as Z increases)
    """
    key = size.upper().replace(" ", "").strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    l = length if length is not None else DEFAULT_LENGTHS[key]
    if l <= 0:
        raise ValueError(f"length must be > 0, got {l}")

    with BuildPart() as screw:
        # Shank (plain cylinder)
        Cylinder(
            radius=spec.d / 2, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Conical head: bottom radius = d/2 (joins shank), top radius = dk/2
        # Cone in build123d: bottom_radius, top_radius, height, placed at shank top
        with Locations(Location((0, 0, l))):
            Cone(
                bottom_radius=spec.dk / 2,
                top_radius=spec.d / 2,
                height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return screw.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in DEFAULT_LENGTHS.items():
        part = make_countersunk_screw(size=size, length=default_l)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_iso10642_L{int(default_l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.2f} mm3")
