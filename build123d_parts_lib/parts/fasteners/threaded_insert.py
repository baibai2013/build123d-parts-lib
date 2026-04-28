"""FDM heat-set brass threaded inserts (Ruthex / InsertEZ compatible).

Standards: Ruthex RX-M* / InsertEZ (de facto FDM standard)
License: MIT

Supported sizes: M2.5, M3, M4, M5

Simplification:
- Single outer cylinder (simplified from knurled/stepped real geometry)
- Central through-hole (nominal thread diameter = bore)
- No internal thread modelled; sufficient for assembly and clearance checks
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Mode,
    Part,
    export_step,
)


class InsertSpec(NamedTuple):
    d:      float   # nominal thread diameter (bore)
    od:     float   # outer diameter of insert body
    length: float   # total insert length


_SPECS: dict[str, InsertSpec] = {
    "M2.5": InsertSpec(d=2.5, od=3.5, length=4.0),
    "M3":   InsertSpec(d=3.0, od=4.2, length=5.0),
    "M4":   InsertSpec(d=4.0, od=5.6, length=6.0),
    "M5":   InsertSpec(d=5.0, od=6.4, length=8.0),
}


def make_threaded_insert(size: str = "M3") -> Part:
    """Generate a simplified FDM heat-set threaded insert solid.

    Args:
        size: Size string, e.g. "M3", "M4".

    Geometry:
        - Origin at bottom face centre
        - Insert body extends along +Z by `length`
        - Central through-hole diameter = nominal thread diameter
    """
    key = size.upper().replace(" ", "").strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]

    with BuildPart() as insert:
        # Outer body cylinder
        Cylinder(
            radius=spec.od / 2, height=spec.length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Central bore (thread hole)
        Cylinder(
            radius=spec.d / 2, height=spec.length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

    return insert.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_threaded_insert(size=size)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_insert_fdm.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.2f} mm3")
