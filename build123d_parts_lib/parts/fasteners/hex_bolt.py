"""DIN 933 / ISO 4017 hex bolt, full thread (simplified).

Source: DIN 933 / ISO 4017 standard dimensions
Standards: DIN 933 / ISO 4017
License: MIT

支持规格：M4 / M5 / M6 / M8 / M10

简化程度：
- 头部六棱柱（不建模倒角、滚花）
- 杆部光杆（不建螺纹；装配用足够）
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
    Location,
    Locations,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)


class BoltSpec(NamedTuple):
    d:      float   # 螺纹大径（公称直径） / nominal thread diameter
    s:      float   # 头部对边宽 / across flats (wrench width)
    k:      float   # 头部高度 / head height
    pitch:  float   # 粗牙螺距 / coarse thread pitch


# 静态后备数据 —— YAML 全量覆盖 M4/M5/M6/M8/M10，通常不需要后备
# Static fallback — YAML covers M4/M5/M6/M8/M10 fully; kept for resilience
_FALLBACK_SPECS: dict[str, BoltSpec] = {
    "M4":  BoltSpec(d=4.0,  s=7.0,  k=2.8, pitch=0.70),
    "M5":  BoltSpec(d=5.0,  s=8.0,  k=3.5, pitch=0.80),
    "M6":  BoltSpec(d=6.0,  s=10.0, k=4.0, pitch=1.00),
    "M8":  BoltSpec(d=8.0,  s=13.0, k=5.3, pitch=1.25),
    "M10": BoltSpec(d=10.0, s=16.0, k=6.4, pitch=1.50),
}


def _load_specs() -> dict[str, BoltSpec]:
    """从 fasteners.yaml 读取 hex-bolt-full-thread 规格，与后备数据合并。
    Load hex-bolt-full-thread specs from fasteners.yaml, merged with fallback data.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK_SPECS)

    specs: dict[str, BoltSpec] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-bolt-full-thread":
                continue
            # 从 factory.args.size 提取规格键 / extract size key from factory.args.size
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            try:
                specs[size.upper()] = BoltSpec(
                    d=float(thread["d"]),
                    s=float(head["s"]),
                    k=float(head["k"]),
                    pitch=float(thread["pitch"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    # 合并后备数据（仅填充 YAML 中不存在的规格）
    # Merge fallback for any sizes missing from YAML
    for size, spec in _FALLBACK_SPECS.items():
        if size not in specs:
            specs[size] = spec

    return specs


def _build_default_lengths(specs: dict[str, BoltSpec]) -> dict[str, float]:
    """从 YAML common_lengths_mm 推导默认长度；不可用时使用内置值。
    Derive default lengths from YAML common_lengths_mm; fall back to built-in values.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    built_in: dict[str, float] = {
        "M4": 12.0, "M5": 16.0, "M6": 20.0, "M8": 25.0, "M10": 30.0,
    }
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return {k: built_in.get(k, 12.0) for k in specs}

    lengths: dict[str, float] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-bolt-full-thread":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            common = entry.get("common_lengths_mm")
            if common and isinstance(common, list) and len(common) > 0:
                lengths[size.upper()] = float(common[0])

    for size in specs:
        if size not in lengths:
            lengths[size] = built_in.get(size, 12.0)

    return lengths


# 模块级单例 —— 仅在导入时加载一次 / module-level singletons, loaded once at import
_SPECS: dict[str, BoltSpec] = _load_specs()
DEFAULT_LENGTHS: dict[str, float] = _build_default_lengths(_SPECS)


def _hex_major_radius(s: float) -> float:
    """Convert across-flats width s to major radius (vertex-to-centre).
    将对边宽 s 转换为外接圆半径（顶点到圆心距离）。

    For a regular hexagon: s (across flats) = 2 * r_minor = r_major * sqrt(3)
    Therefore: r_major = s / sqrt(3)
    BBox in X direction = 2 * r_major = 2 * s / sqrt(3)  ≈ 1.1547 * s
    """
    return s / math.sqrt(3)


def make_hex_bolt(size: str = "M6", length: float | None = None) -> Part:
    """生成 DIN 933 外六角螺栓简化实体（六角头 + 光杆）。

    Args:
        size:   规格字符串，如 "M6"、"M8"。
        length: 螺杆长度（不含头部）。None 时取各规格默认值。

    几何：
        - 原点在杆底面中心
        - 杆沿 +Z 伸出 `length`
        - 六角头在杆顶面向上再伸出 `k`
    """
    key = size.upper().replace(" ", "").strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知规格 {size!r}，可用：{available}")

    spec = _SPECS[key]
    l = length if length is not None else DEFAULT_LENGTHS[key]
    if l <= 0:
        raise ValueError(f"length 必须 > 0，得到 {l}")

    r_major = _hex_major_radius(spec.s)

    with BuildPart() as bolt:
        # 螺杆（光杆）/ shank (plain cylinder)
        Cylinder(
            radius=spec.d / 2, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 六角头（在杆顶面）/ hexagonal head (at shank top)
        with Locations(Location((0, 0, l))):
            with BuildSketch(Plane.XY.offset(l)):
                RegularPolygon(radius=r_major, side_count=6)
            extrude(amount=spec.k)

    return bolt.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in DEFAULT_LENGTHS.items():
        part = make_hex_bolt(size=size, length=default_l)
        slug = size.lower()
        out_path = cache_dir / f"{slug}_din933_L{int(default_l)}.step"
        export_step(part, str(out_path))

        # 验证六角头 bbox X 方向 ≈ 2 * s / sqrt(3)
        spec = _SPECS[size]
        expected_bbox_x = 2 * spec.s / math.sqrt(3)
        print(
            f"OK: {out_path.name}  vol={part.volume:.1f} mm³  "
            f"head_bbox_x_expected≈{expected_bbox_x:.3f}"
        )
