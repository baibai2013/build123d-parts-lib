"""T-slot nut for 2020 aluminum extrusion / 2020 铝型材 T 型螺母.

No universal standard; geometry follows common 2020-slot market practice.
License: MIT

支持规格 / Supported sizes: M3, M4, M5

几何 / Geometry:
- T 字截面（从槽端观察）/ T cross-section (viewed from slot end)
- 宽头（下）嵌入型材槽腔，窄茎（上）穿过 6mm 槽口 / Wide head (bottom) in cavity; narrow stem (top) through 6 mm slot
- 中心贯通内螺纹（垂直于型材表面）/ Central through thread (perpendicular to extrusion face)
- 原点底面中心，+Z 为螺纹轴方向，+X 为槽长方向 / Origin at bottom centre, +Z = thread axis, +X = slot direction
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    Box,
    BuildPart,
    Part,
    export_step,
)

from ._thread_utils import make_internal_thread


class TSlotNutSpec(NamedTuple):
    d:       float   # 螺纹大径 / nominal thread diameter
    pitch:   float   # 粗牙螺距 / coarse thread pitch
    head_w:  float   # 宽头 Y 方向尺寸（嵌入槽腔）/ head width (inside cavity)
    head_h:  float   # 宽头高度（Z）/ head height
    stem_w:  float   # 窄茎 Y 方向尺寸（穿槽口）/ stem width (through slot opening)
    stem_h:  float   # 窄茎高度（Z）/ stem height
    length:  float   # 螺母长度（X，沿槽方向）/ nut length along slot


_FALLBACK: dict[str, TSlotNutSpec] = {
    "M3": TSlotNutSpec(d=3.0, pitch=0.50, head_w=5.75, head_h=1.8, stem_w=3.0, stem_h=0.9, length=10.0),
    "M4": TSlotNutSpec(d=4.0, pitch=0.70, head_w=5.75, head_h=1.8, stem_w=3.8, stem_h=0.9, length=10.0),
    "M5": TSlotNutSpec(d=5.0, pitch=0.80, head_w=7.75, head_h=2.0, stem_w=4.8, stem_h=1.0, length=10.0),
}


def _load_specs() -> dict[str, TSlotNutSpec]:
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, TSlotNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "nut-tslot":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = TSlotNutSpec(
                    d=float(thread["d"]),
                    pitch=float(thread["pitch"]),
                    head_w=float(dims["head_w"]),
                    head_h=float(dims["head_h"]),
                    stem_w=float(dims["stem_w"]),
                    stem_h=float(dims["stem_h"]),
                    length=float(dims["length"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


def make_tslot_nut(size: str = "M4") -> Part:
    """2020 铝型材 T 型螺母（T 截面体 + 贯通内螺纹）。
    2020 extrusion T-slot nut (T cross-section body + through internal thread).

    Orientation:
      - Origin at bottom face centre
      - +Z = thread axis (bolt comes from above / outside)
      - +X = slot direction (nut slides along here)

    Args:
        size: 规格字符串 e.g. "M4" / Size string e.g. "M4"
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]
    total_h = spec.head_h + spec.stem_h

    # Wide head block (sits inside slot cavity, cannot exit through slot opening)
    with BuildPart() as head_bp:
        Box(spec.length, spec.head_w, spec.head_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Narrow stem block (fits through 6 mm slot opening)
    with BuildPart() as stem_bp:
        Box(spec.length, spec.stem_w, spec.stem_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

    solid = head_bp.part.fuse(stem_bp.part.translate((0.0, 0.0, spec.head_h)))

    # Through internal thread along Z (bolt threads in from stem top)
    thread_sub = make_internal_thread(spec.d, spec.pitch, total_h)
    return solid.cut(thread_sub)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_tslot_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_nut_tslot2020.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
