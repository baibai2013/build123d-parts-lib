"""ISO 7046 countersunk Phillips head screw (十字沉头螺丝).

Standards: ISO 7046
License: MIT

支持规格: M2, M3, M4, M5

几何:
- 90° 锥形沉头（与 ISO 10642 同头型，仅驱动不同）
- 十字 Phillips 凹槽
- 小径圆柱杆 + ISO 外螺纹 + 杆端 45° 倒角
- 原点杆底面中心，+Z 为杆方向
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


class CskPhillipsSpec(NamedTuple):
    d:     float   # 螺纹大径
    dk:    float   # 头最大径（顶面）
    k:     float   # 头高（锥面高）
    pitch: float   # 粗牙螺距


_FALLBACK: dict[str, CskPhillipsSpec] = {
    "M2":  CskPhillipsSpec(d=2.0, dk=3.8,  k=1.2,  pitch=0.40),
    "M3":  CskPhillipsSpec(d=3.0, dk=5.6,  k=1.65, pitch=0.50),
    "M4":  CskPhillipsSpec(d=4.0, dk=7.5,  k=2.2,  pitch=0.70),
    "M5":  CskPhillipsSpec(d=5.0, dk=9.2,  k=2.75, pitch=0.80),
}

_DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
}


def _load_specs() -> dict[str, CskPhillipsSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, CskPhillipsSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "screw-csk-head-phillips":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = CskPhillipsSpec(
                    d=float(thread["d"]),
                    dk=float(head["dk"]),
                    k=float(head["k"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def _cut_phillips(solid: Part, head_top_z: float, dk: float, k: float) -> Part:
    """Phillips 十字凹槽减料。
    Cut Phillips cross recess. Two rect arms + center guide cone.
    """
    depth = 0.55 * k
    arm_w = max(0.5, 0.20 * dk)
    arm_l = dk * 0.88
    arm_z = head_top_z - depth / 2

    with BuildPart() as cutter:
        with Locations(Location((0, 0, arm_z))):
            Box(arm_l, arm_w, depth + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
        with Locations(Location((0, 0, arm_z))):
            Box(arm_w, arm_l, depth + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
        # 中心引导锥 / center guide cone (wide at top, pointed at bottom)
        cone_h = depth * 0.35
        with Locations(Location((0, 0, head_top_z - depth))):
            Cone(bottom_radius=0.01, top_radius=arm_w * 0.55, height=cone_h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))

    return solid.cut(cutter.part)


def make_csk_phillips_screw(size: str = "M4", length: float | None = None) -> Part:
    """ISO 7046 沉头十字螺丝（90° 锥形头 + Phillips 槽 + ISO 螺纹杆）。
    ISO 7046 countersunk Phillips screw (90° cone head + Phillips recess + ISO shank).

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
        # 杆 / shank
        Cylinder(radius=r_minor, height=l,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
        # 锥形沉头：底面 dk/2（大），顶面 d/2（小），同 countersunk_screw.py 约定
        # Conical head: bottom radius dk/2 (wide), top radius d/2 (narrow) — same convention as countersunk_screw.py
        with Locations(Location((0, 0, l))):
            Cone(
                bottom_radius=spec.dk / 2,
                top_radius=spec.d / 2,
                height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    thread = make_external_thread(spec.d, spec.pitch, l)
    solid = bp.part.fuse(thread)

    # Phillips 十字槽 / Phillips cross recess
    solid = _cut_phillips(solid, head_top_z, spec.dk, spec.k)

    # 杆端倒角 / shank tip chamfer
    chamfer_size = 0.5 * spec.pitch
    tol = 1e-3
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
        part = make_csk_phillips_screw(size=size, length=default_l)
        slug = size.lower()
        out = cache_dir / f"{slug}_iso7046_L{int(default_l)}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
