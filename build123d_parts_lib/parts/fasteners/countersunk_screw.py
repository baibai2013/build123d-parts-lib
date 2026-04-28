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

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    Cone,
    Cylinder,
    Location,
    Locations,
    Part,
    export_step,
)


class ScrewSpec(NamedTuple):
    d:  float   # 公称螺纹直径 / nominal thread diameter
    dk: float   # 头部最大直径（与安装面齐平处） / head top diameter (flush with surface)
    k:  float   # 头部高度 / head height
    pitch: float  # 粗牙螺距 / coarse thread pitch


# 静态后备数据 —— 涵盖 YAML 中尚未收录的规格（M2 / M2.5）
# Static fallback for sizes absent from YAML (M2, M2.5)
_FALLBACK_SPECS: dict[str, ScrewSpec] = {
    "M2":   ScrewSpec(d=2.0, dk=3.8,  k=1.1,  pitch=0.40),
    "M2.5": ScrewSpec(d=2.5, dk=4.7,  k=1.5,  pitch=0.45),
}


def _load_specs() -> dict[str, ScrewSpec]:
    """从 fasteners.yaml 读取 hex-socket-countersunk-head-screw 规格，与后备数据合并。
    Load hex-socket-countersunk-head-screw specs from fasteners.yaml, merged with fallback data.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK_SPECS)

    specs: dict[str, ScrewSpec] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-socket-countersunk-head-screw":
                continue
            # 从 factory.args.size 提取规格键 / extract size key from factory.args.size
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = ScrewSpec(
                    d=float(thread["d"]),
                    dk=float(head["dk"]),
                    k=float(head["k"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    # 合并后备数据（仅填充 YAML 中不存在的规格）
    # Merge fallback data for sizes absent from YAML
    for size, spec in _FALLBACK_SPECS.items():
        if size not in specs:
            specs[size] = spec

    return specs


def _build_default_lengths(specs: dict[str, ScrewSpec]) -> dict[str, float]:
    """从 YAML common_lengths_mm 推导默认长度；不可用时使用内置值。
    Derive default lengths from YAML common_lengths_mm; fall back to built-in values.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    built_in: dict[str, float] = {
        "M2": 8.0, "M2.5": 8.0, "M3": 10.0, "M4": 12.0, "M5": 16.0,
    }
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return {k: built_in.get(k, 10.0) for k in specs}

    lengths: dict[str, float] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-socket-countersunk-head-screw":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            common = entry.get("common_lengths_mm")
            if common and isinstance(common, list) and len(common) > 0:
                lengths[size.upper()] = float(common[0])

    for size in specs:
        if size not in lengths:
            lengths[size] = built_in.get(size, 10.0)

    return lengths


# 模块级单例 —— 仅在导入时加载一次 / module-level singletons, loaded once at import
_SPECS: dict[str, ScrewSpec] = _load_specs()
DEFAULT_LENGTHS: dict[str, float] = _build_default_lengths(_SPECS)


def make_countersunk_screw(size: str = "M3", length: float | None = None) -> Part:
    """Generate an ISO 10642 countersunk screw simplified solid (cone head + plain shank).
    生成 ISO 10642 内六角沉头螺丝简化实体（锥形头 + 光杆）。

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
        # 光杆 / Shank (plain cylinder)
        Cylinder(
            radius=spec.d / 2, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 锥形头：底面半径 = d/2（与杆相接），顶面半径 = dk/2
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
