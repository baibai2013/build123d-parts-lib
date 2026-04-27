"""Hex nuts: ISO 4032 standard, GB/T 6172.1 thin, DIN 985 nylon-insert lock nut.

Standards: ISO 4032 / GB/T 6172.1 / DIN 985
License: MIT

Supported sizes:
  ISO 4032  (standard):          M2, M2.5, M3, M4, M5, M6, M8, M10
  GB/T 6172.1 (thin):            M2, M2.5, M3, M4, M5, M6, M8, M10
  DIN 985 (nylon insert lock):   M3, M4, M5, M6, M8, M10

Simplification:
- Hexagonal prism + central through-hole (nominal thread diameter)
- DIN 985 modelled as slightly taller hex prism to represent nylon ring section
- No chamfer, no thread
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, BuildPart, Cylinder, Mode, Part,
    RegularPolygon, BuildSketch, Plane, extrude, export_step,
)

import math


class NutSpec(NamedTuple):
    d: float   # nominal thread diameter (bore)
    s: float   # wrench width (across flats)
    m: float   # nut height/thickness


# ISO 4032 standard hex nut
_SPECS_ISO4032: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0,  s=4.0,  m=1.6),
    "M2.5": NutSpec(d=2.5,  s=5.0,  m=2.0),
    "M3":   NutSpec(d=3.0,  s=5.5,  m=2.4),
    "M4":   NutSpec(d=4.0,  s=7.0,  m=3.2),
    "M5":   NutSpec(d=5.0,  s=8.0,  m=4.7),
    "M6":   NutSpec(d=6.0,  s=10.0, m=5.2),
    "M8":   NutSpec(d=8.0,  s=13.0, m=6.8),
    "M10":  NutSpec(d=10.0, s=16.0, m=8.4),
}

# GB/T 6172.1 thin hex nut
_SPECS_GB6172: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0,  s=4.0,  m=1.2),
    "M2.5": NutSpec(d=2.5,  s=5.0,  m=1.6),
    "M3":   NutSpec(d=3.0,  s=5.5,  m=1.8),
    "M4":   NutSpec(d=4.0,  s=7.0,  m=2.2),
    "M5":   NutSpec(d=5.0,  s=8.0,  m=2.7),
    "M6":   NutSpec(d=6.0,  s=10.0, m=3.2),
    "M8":   NutSpec(d=8.0,  s=13.0, m=4.0),
    "M10":  NutSpec(d=10.0, s=16.0, m=5.0),
}

# DIN 985 nylon insert lock nut
_SPECS_DIN985: dict[str, NutSpec] = {
    "M3":   NutSpec(d=3.0,  s=5.5,  m=4.0),
    "M4":   NutSpec(d=4.0,  s=7.0,  m=5.0),
    "M5":   NutSpec(d=5.0,  s=8.0,  m=5.0),
    "M6":   NutSpec(d=6.0,  s=10.0, m=6.0),
    "M8":   NutSpec(d=8.0,  s=13.0, m=8.0),
    "M10":  NutSpec(d=10.0, s=16.0, m=10.0),
}

_STANDARDS: dict[str, dict[str, NutSpec]] = {
    "ISO4032": _SPECS_ISO4032,
    "GB6172":  _SPECS_GB6172,
    "DIN985":  _SPECS_DIN985,
}


def _hex_circumradius(s: float) -> float:
    """Convert across-flats width s to circumradius (vertex-to-center)."""
    # For regular hexagon: s = 2 * r * cos(30°) = r * sqrt(3)
    return s / math.sqrt(3)


def make_hex_nut(size: str, standard: str = "ISO4032") -> Part:
    """Generate a simplified hex nut solid.

    Args:
        size:     Size string, e.g. "M3", "M4".
        standard: One of "ISO4032", "GB6172", "DIN985".

    Geometry:
        - Origin at bottom face centre
        - Nut height along +Z
        - Central through-hole diameter = nominal thread diameter
    """
    std_key = standard.upper().replace(" ", "").replace("/", "").replace(".", "")
    # Normalise common aliases
    _alias = {
        "ISO4032": "ISO4032", "ISO 4032": "ISO4032",
        "GB6172":  "GB6172",  "GBT61721": "GB6172",
        "DIN985":  "DIN985",
    }
    std_key = _alias.get(std_key, std_key)
    if std_key not in _STANDARDS:
        raise ValueError(f"Unknown standard {standard!r}, available: {list(_STANDARDS.keys())}")

    specs = _STANDARDS[std_key]
    key = size.upper().replace(" ", "").strip()
    if key not in specs:
        available = ", ".join(specs.keys())
        raise ValueError(f"Size {size!r} not available for {standard}, available: {available}")

    spec = specs[key]
    r_hex = _hex_circumradius(spec.s)

    with BuildPart() as nut:
        # Hexagonal prism
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=spec.m)
        # Central through-hole
        Cylinder(
            radius=spec.d / 2, height=spec.m,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

    return nut.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    tasks = [
        ("ISO4032", _SPECS_ISO4032),
        ("GB6172",  _SPECS_GB6172),
        ("DIN985",  _SPECS_DIN985),
    ]
    for std_name, specs in tasks:
        for size in specs:
            part = make_hex_nut(size=size, standard=std_name)
            slug = size.replace(".", "_").lower()
            out_path = cache_dir / f"{slug}_nut_{std_name.lower()}.step"
            export_step(part, str(out_path))
            print(f"OK: {out_path.name}  vol={part.volume:.2f} mm3")
