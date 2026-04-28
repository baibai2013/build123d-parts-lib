"""ISO 2009 countersunk slotted head screw (一字沉头螺丝).

Standards: ISO 2009
License: MIT

支持规格: M2, M3, M4, M5

几何:
- 90° 锥形沉头（与 ISO 10642 同头型）
- 一字直槽贯穿头径
- 小径圆柱杆 + ISO 外螺纹 + 杆端 45° 倒角
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    Box,
    BuildPart,
    Cone,
    Cylinder,
    Edge,
    Location,
    Locations,
    Part,
    export_step,
)

from ._thread_utils import make_external_thread


class CskSlottedSpec(NamedTuple):
    d:      float
    dk:     float
    k:      float
    pitch:  float
    slot_w: float
    slot_d: float


_FALLBACK: dict[str, CskSlottedSpec] = {
    "M2":  CskSlottedSpec(d=2.0, dk=3.8,  k=1.2,  pitch=0.40, slot_w=0.5, slot_d=0.5),
    "M3":  CskSlottedSpec(d=3.0, dk=5.6,  k=1.65, pitch=0.50, slot_w=0.8, slot_d=0.7),
    "M4":  CskSlottedSpec(d=4.0, dk=7.5,  k=2.2,  pitch=0.70, slot_w=1.0, slot_d=0.9),
    "M5":  CskSlottedSpec(d=5.0, dk=9.2,  k=2.75, pitch=0.80, slot_w=1.2, slot_d=1.1),
}

_DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
}


def _load_specs() -> dict[str, CskSlottedSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, CskSlottedSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "screw-csk-head-slotted":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = CskSlottedSpec(
                    d=float(thread["d"]),
                    dk=float(head["dk"]),
                    k=float(head["k"]),
                    pitch=float(thread["pitch"]),
                    slot_w=float(head.get("slot_w", 1.0)),
                    slot_d=float(head.get("slot_d", 0.9)),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_csk_slotted_screw(size: str = "M4", length: float | None = None) -> Part:
    """ISO 2009 沉头一字螺丝（90° 锥形头 + 直槽 + ISO 螺纹杆）。
    ISO 2009 countersunk slotted screw (90° cone head + slot + ISO shank).

    Args:
        size:   规格 e.g. "M4"
        length: 杆长（不含头）；None 取默认值
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    l = length if length is not None else _DEFAULT_LENGTHS.get(key, 10.0)
    if l <= 0:
        raise ValueError(f"length must be > 0, got {l}")

    r_minor = (spec.d - 1.2269 * spec.pitch) / 2
    head_top_z = l + spec.k

    with BuildPart() as bp:
        Cylinder(radius=r_minor, height=l,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        with Locations(Location((0, 0, l))):
            Cone(
                bottom_radius=spec.dk / 2,
                top_radius=spec.d / 2,
                height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    thread = make_external_thread(spec.d, spec.pitch, l)
    solid = bp.part.fuse(thread)

    # 一字直槽 / straight slotted recess
    slot_l = spec.dk * 1.05
    slot_z = head_top_z - spec.slot_d / 2
    tol = 1e-3
    with BuildPart() as slot_cutter:
        with Locations(Location((0, 0, slot_z))):
            Box(slot_l, spec.slot_w, spec.slot_d + 0.3,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
    solid = solid.cut(slot_cutter.part)

    # 杆端倒角 / shank tip chamfer
    chamfer_size = 0.5 * spec.pitch
    bottom_edges: list[Edge] = [
        e for e in solid.edges()
        if e.is_closed and abs(e.center().Z) < tol
    ]
    if bottom_edges:
        solid = solid.chamfer(chamfer_size, None, bottom_edges)

    return solid


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in _DEFAULT_LENGTHS.items():
        if size not in _SPECS:
            continue
        part = make_csk_slotted_screw(size=size, length=default_l)
        slug = size.lower()
        out = cache_dir / f"{slug}_iso2009_L{int(default_l)}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
