"""Washers: ISO 7089 plain washer and GB/T 93 spring washer (simplified).

Standards: ISO 7089 / GB/T 93
License: MIT

Supported sizes:
  ISO 7089 (flat):    M2, M2.5, M3, M4, M5
  GB/T 93 (spring):  M3, M4, M5

Simplification:
- ISO 7089: simple annular ring (torus-section cylinder with bore)
- GB/T 93 spring washer: annular ring with one diagonal radial cut slot
  (single diagonal slot across the top face represents the split)
- No thread; sufficient for assembly positioning
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, Box, BuildPart, Cylinder, Mode, Part, export_step,
    Location, Locations,
)


class WasherSpec(NamedTuple):
    id_: float   # inner diameter (bore)
    od:  float   # outer diameter
    t:   float   # thickness


# ISO 7089 plain washers
_SPECS_FLAT: dict[str, WasherSpec] = {
    "M2":   WasherSpec(id_=2.2, od=5.0,  t=0.3),
    "M2.5": WasherSpec(id_=2.7, od=6.0,  t=0.5),
    "M3":   WasherSpec(id_=3.2, od=7.0,  t=0.5),
    "M4":   WasherSpec(id_=4.3, od=9.0,  t=0.8),
    "M5":   WasherSpec(id_=5.3, od=10.0, t=1.0),
}

# GB/T 93 spring washers
_SPECS_SPRING: dict[str, WasherSpec] = {
    "M3":   WasherSpec(id_=3.1, od=6.2,  t=0.8),
    "M4":   WasherSpec(id_=4.1, od=7.6,  t=1.1),
    "M5":   WasherSpec(id_=5.1, od=9.2,  t=1.3),
}


def _make_flat_washer(spec: WasherSpec) -> Part:
    """Plain annular ring."""
    with BuildPart() as w:
        Cylinder(
            radius=spec.od / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=spec.id_ / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    return w.part


def _make_spring_washer(spec: WasherSpec) -> Part:
    """Spring washer: annular ring with one diagonal cut slot at one side.

    The slot is a narrow box that cuts radially through the ring at an angle,
    representing the characteristic split of a spring washer.
    """
    with BuildPart() as w:
        # Base annular ring (slightly thicker - spring is under tension when flat)
        Cylinder(
            radius=spec.od / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=spec.id_ / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # Diagonal cut slot: narrow box aligned along X, rotated slightly in Z,
        # cutting all the way through
        slot_width = spec.t * 0.8   # slot width proportional to thickness
        slot_length = spec.od       # long enough to cut through the ring
        slot_height = spec.t * 1.2  # slightly taller than ring to ensure clean cut
        # Place slot at centre, it cuts through ring at slight diagonal (10 deg)
        with Locations(Location((0, 0, spec.t / 2), (0, 0, 10))):
            Box(
                length=slot_length, width=slot_width, height=slot_height,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    return w.part


def make_washer(size: str, type_: str = "flat") -> Part:
    """Generate a simplified washer solid.

    Args:
        size:  Size string, e.g. "M3", "M4".
        type_: "flat" for ISO 7089, "spring" for GB/T 93.

    Geometry:
        - Origin at bottom face centre
        - Height along +Z
    """
    t = type_.lower().strip()
    if t == "flat":
        key = size.upper().replace(" ", "").strip()
        if key not in _SPECS_FLAT:
            available = ", ".join(_SPECS_FLAT.keys())
            raise ValueError(f"Size {size!r} not available for flat washer, available: {available}")
        return _make_flat_washer(_SPECS_FLAT[key])
    elif t == "spring":
        key = size.upper().replace(" ", "").strip()
        if key not in _SPECS_SPRING:
            available = ", ".join(_SPECS_SPRING.keys())
            raise ValueError(f"Size {size!r} not available for spring washer, available: {available}")
        return _make_spring_washer(_SPECS_SPRING[key])
    else:
        raise ValueError(f"Unknown type_ {type_!r}, use 'flat' or 'spring'")


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size in _SPECS_FLAT:
        part = make_washer(size=size, type_="flat")
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_washer_iso7089.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.3f} mm3")

    for size in _SPECS_SPRING:
        part = make_washer(size=size, type_="spring")
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_washer_gbt93.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.3f} mm3")
