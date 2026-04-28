"""ISO 7045 pan head Phillips screw (十字圆头螺丝).

Standards: ISO 7045
License: MIT

支持规格: M2, M3, M4, M5

几何:
- 圆盘形头，顶边小圆角呈浅穹顶 / Disc head with small top-edge fillet → slight dome
- 十字 Phillips 凹槽（两矩形臂 + 中心引导锥）
- 小径圆柱杆 + ISO 外螺纹 + 杆端 45° 倒角
- 原点杆底面中心，+Z 为杆方向
"""
from __future__ import annotations

import math
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
    Mode,
    Part,
    export_step,
)

from ._thread_utils import make_external_thread


class PanScrewSpec(NamedTuple):
    d:     float   # 螺纹大径
    dk:    float   # 头外径
    k:     float   # 头高
    pitch: float   # 粗牙螺距


_FALLBACK: dict[str, PanScrewSpec] = {
    "M2":  PanScrewSpec(d=2.0, dk=4.0,  k=1.6, pitch=0.40),
    "M3":  PanScrewSpec(d=3.0, dk=6.0,  k=2.4, pitch=0.50),
    "M4":  PanScrewSpec(d=4.0, dk=8.0,  k=3.1, pitch=0.70),
    "M5":  PanScrewSpec(d=5.0, dk=9.5,  k=3.7, pitch=0.80),
}

_DEFAULT_LENGTHS: dict[str, float] = {
    "M2": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
}


def _load_specs() -> dict[str, PanScrewSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, PanScrewSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "screw-pan-head-phillips":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = PanScrewSpec(
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
    """在头顶面切出 Phillips 十字凹槽。
    Cut Phillips cross recess from head top face.
    两矩形臂 + 中心引导锥 / Two rect arms + center guide cone.
    """
    depth = 0.6 * k
    arm_w = max(0.5, 0.20 * dk)    # 臂宽 / arm width
    arm_l = dk * 0.88               # 臂长（贯穿头径）/ arm length (spans head)
    arm_z = head_top_z - depth / 2  # 臂体中心 Z / arm body centre Z

    with BuildPart() as cutter:
        # 水平臂 / horizontal arm
        with Locations(Location((0, 0, arm_z))):
            Box(arm_l, arm_w, depth + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
        # 垂直臂 / vertical arm
        with Locations(Location((0, 0, arm_z))):
            Box(arm_w, arm_l, depth + 0.5,
                align=(Align.CENTER, Align.CENTER, Align.CENTER))
        # 中心引导锥：顶部宽，向下收尖 / center cone: wide at top, pointed down
        cone_h = depth * 0.35
        with Locations(Location((0, 0, head_top_z - depth))):
            Cone(
                bottom_radius=0.01,
                top_radius=arm_w * 0.55,
                height=cone_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return solid.cut(cutter.part)


def make_pan_phillips_screw(size: str = "M4", length: float | None = None) -> Part:
    """ISO 7045 圆头十字螺丝（圆盘头 + Phillips 十字槽 + ISO 螺纹杆）。
    ISO 7045 pan head Phillips screw (disc head + Phillips cross + ISO threaded shank).

    Args:
        size:   规格 e.g. "M4" / Size e.g. "M4"
        length: 杆长（不含头）；None 取默认值 / Shank length excl. head; None = default
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
        # 圆盘头 / pan head disc
        with Locations(Location((0, 0, l))):
            Cylinder(radius=spec.dk / 2, height=spec.k,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 外螺纹 / external thread
    thread = make_external_thread(spec.d, spec.pitch, l)
    solid = bp.part.fuse(thread)

    # 头顶小圆角（浅穹顶）/ small top-edge fillet → slight dome
    fillet_r = min(spec.k * 0.28, spec.dk / 2 * 0.12)
    tol = 1e-3
    top_edges: list[Edge] = [
        e for e in solid.edges()
        if e.is_closed and abs(e.center().Z - head_top_z) < tol
    ]
    if top_edges:
        solid = solid.fillet(fillet_r, top_edges)

    # Phillips 十字槽 / Phillips cross recess
    solid = _cut_phillips(solid, head_top_z, spec.dk, spec.k)

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
        part = make_pan_phillips_screw(size=size, length=default_l)
        slug = size.lower()
        out = cache_dir / f"{slug}_iso7045_L{int(default_l)}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
