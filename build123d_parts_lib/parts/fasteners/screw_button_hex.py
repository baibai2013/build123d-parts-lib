"""ISO 7380-1 hex socket button head cap screw.

Standards: ISO 7380-1
License: MIT

支持规格 / Supported sizes: M2, M3, M4, M5, M6

几何 / Geometry:
- 低剖面圆柱头，顶部大圆角形成球面冠 / Low-profile cylindrical head with top fillet → spherical dome
- 内六角凹槽 / Hex socket recess
- 小径圆柱杆 + ISO 锯齿外螺纹 + 杆端 45° 倒角
- 原点杆底面中心，+Z 为杆方向
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
    Mode,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)

from ._thread_utils import make_external_thread


class ButtonScrewSpec(NamedTuple):
    d:     float   # 螺纹大径 / nominal thread diameter
    dk:    float   # 头外径 / head outer diameter
    k:     float   # 头高 / head height
    pitch: float   # 粗牙螺距 / coarse pitch
    s:     float   # 内六角对边宽 / hex key across-flats


_FALLBACK: dict[str, ButtonScrewSpec] = {
    "M2":  ButtonScrewSpec(d=2.0, dk=3.8,  k=1.3,  pitch=0.40, s=1.5),
    "M3":  ButtonScrewSpec(d=3.0, dk=5.7,  k=1.65, pitch=0.50, s=2.0),
    "M4":  ButtonScrewSpec(d=4.0, dk=7.6,  k=2.2,  pitch=0.70, s=2.5),
    "M5":  ButtonScrewSpec(d=5.0, dk=9.5,  k=2.75, pitch=0.80, s=3.0),
    "M6":  ButtonScrewSpec(d=6.0, dk=10.5, k=3.0,  pitch=1.00, s=4.0),
}

_DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 6.0, "M3": 10.0, "M4": 12.0, "M5": 16.0, "M6": 20.0,
}


def _load_specs() -> dict[str, ButtonScrewSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, ButtonScrewSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "screw-button-head-hex-socket":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = ButtonScrewSpec(
                    d=float(thread["d"]),
                    dk=float(head["dk"]),
                    k=float(head["k"]),
                    pitch=float(thread["pitch"]),
                    s=float(head["s"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_button_head_screw(size: str = "M4", length: float | None = None) -> Part:
    """ISO 7380-1 内六角圆头螺丝（球面冠头 + 内六角凹槽 + ISO 螺纹杆）。
    ISO 7380-1 button head socket cap screw (dome head + hex recess + ISO threaded shank).

    Args:
        size:   规格字符串 e.g. "M4"  / Size string e.g. "M4"
        length: 杆长（不含头）；None 取默认值  / Shank length excl. head; None = default
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
    # 内六角凹槽 / hex socket recess
    recess_depth = 0.7 * spec.k
    hex_r = spec.s / math.sqrt(3)
    head_top_z = l + spec.k

    with BuildPart() as bp:
        # 杆（小径圆柱）/ shank
        Cylinder(radius=r_minor, height=l,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 圆头：完整高度圆柱，后续对顶棱施以大圆角形成球面冠
        # Button head: full-height cylinder; top edge gets a large fillet → dome
        with Locations(Location((0, 0, l))):
            Cylinder(radius=spec.dk / 2, height=spec.k,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 内六角凹槽（从头顶面向下）/ hex socket recess down from head top
        with BuildSketch(Plane.XY.offset(head_top_z)):
            RegularPolygon(radius=hex_r, side_count=6)
        extrude(amount=-recess_depth, mode=Mode.SUBTRACT)

    # 叠加螺纹 / fuse external thread
    thread = make_external_thread(spec.d, spec.pitch, l)
    solid = bp.part.fuse(thread)

    # 头顶棱大圆角 → 球面冠效果
    # Large fillet on head top edge → spherical dome appearance
    fillet_r = min(spec.dk / 2 * 0.42, spec.k * 0.88)
    tol = 1e-3
    top_edges: list[Edge] = [
        e for e in solid.edges()
        if e.is_closed and abs(e.center().Z - head_top_z) < tol
    ]
    if top_edges:
        solid = solid.fillet(fillet_r, top_edges)

    # 杆端 45° 倒角 / shank tip 45° chamfer
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
        part = make_button_head_screw(size=size, length=default_l)
        slug = size.lower()
        out = cache_dir / f"{slug}_iso7380_L{int(default_l)}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
