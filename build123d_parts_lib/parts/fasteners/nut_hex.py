"""Hex nuts: ISO 4032 standard, GB/T 6172.1 thin, DIN 985 nylon-insert lock nut.

Standards: ISO 4032 / GB/T 6172.1 / DIN 985
License: MIT

Supported sizes:
  ISO 4032  (standard):          M2, M2.5, M3, M4, M5, M6, M8, M10
  GB/T 6172.1 (thin):            M2, M2.5, M3, M4, M5, M6, M8, M10
  DIN 985 (nylon insert lock):   M3, M4, M5, M6, M8, M10

几何：
- 六棱柱主体 + ISO 旋转内螺纹（revolve 锯齿减料）
- 无倒角；DIN 985 建模为略高六棱柱
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
    Mode,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)

from ._thread_utils import make_internal_thread

# 标准粗牙螺距表 / standard coarse thread pitch table
_COARSE_PITCH: dict[str, float] = {
    "M2": 0.40, "M2.5": 0.45, "M3": 0.50, "M4": 0.70,
    "M5": 0.80, "M6": 1.00,  "M8": 1.25, "M10": 1.50,
}


class NutSpec(NamedTuple):
    d:     float   # 公称螺纹直径（孔径大径） / nominal thread diameter (major)
    s:     float   # 对边宽（扳手宽） / wrench width (across flats)
    m:     float   # 螺母高度 / nut height/thickness
    pitch: float   # 粗牙螺距 / coarse thread pitch


# ─────────────────────────────────────────────────────────────────────────────
# 静态后备数据（含螺距） / static fallback data including pitch
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_ISO4032: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0, s=4.0, m=1.6, pitch=0.40),
    "M2.5": NutSpec(d=2.5, s=5.0, m=2.0, pitch=0.45),
}

_FALLBACK_GB6172: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0, s=4.0, m=1.2, pitch=0.40),
    "M2.5": NutSpec(d=2.5, s=5.0, m=1.6, pitch=0.45),
    "M4":   NutSpec(d=4.0, s=7.0, m=2.2, pitch=0.70),
    "M5":   NutSpec(d=5.0, s=8.0, m=2.7, pitch=0.80),
}

_FALLBACK_DIN985: dict[str, NutSpec] = {
    "M3":   NutSpec(d=3.0, s=5.5, m=4.0, pitch=0.50),
}


def _load_nut_specs() -> dict[str, dict[str, NutSpec]]:
    """从 fasteners.yaml 读取各标准六角螺母规格，与后备数据合并。
    Load hex nut specs from fasteners.yaml for each standard, merged with fallback data.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"

    type_to_std: dict[str, str] = {
        "hex-nut":                      "ISO4032",
        "hex-thin-nut":                 "GB6172",
        "hex-nylon-insert-lock-nut":    "DIN985",
    }

    result: dict[str, dict[str, NutSpec]] = {
        "ISO4032": {},
        "GB6172":  {},
        "DIN985":  {},
    }

    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}

    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            nut_type = entry.get("type", "")
            std_key = type_to_std.get(nut_type)
            if std_key is None:
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                d = float(thread["d"])
                size_key = size.upper()
                pitch = float(thread.get("pitch", _COARSE_PITCH.get(size_key, 1.0)))
                result[std_key][size_key] = NutSpec(
                    d=d,
                    s=float(dims["s"]),
                    m=float(dims["m"]),
                    pitch=pitch,
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK_ISO4032.items():
        if size not in result["ISO4032"]:
            result["ISO4032"][size] = spec

    for size, spec in _FALLBACK_GB6172.items():
        if size not in result["GB6172"]:
            result["GB6172"][size] = spec

    for size, spec in _FALLBACK_DIN985.items():
        if size not in result["DIN985"]:
            result["DIN985"][size] = spec

    return result


# 模块级单例 / module-level singleton
_NUT_SPECS = _load_nut_specs()
_SPECS_ISO4032 = _NUT_SPECS["ISO4032"]
_SPECS_GB6172  = _NUT_SPECS["GB6172"]
_SPECS_DIN985  = _NUT_SPECS["DIN985"]

_STANDARDS: dict[str, dict[str, NutSpec]] = {
    "ISO4032": _SPECS_ISO4032,
    "GB6172":  _SPECS_GB6172,
    "DIN985":  _SPECS_DIN985,
}


def _hex_circumradius(s: float) -> float:
    """Convert across-flats width s to circumradius (vertex-to-center).
    将对边宽 s 转换为外接圆半径（顶点到圆心距离）。
    """
    return s / math.sqrt(3)


def make_hex_nut(size: str, standard: str = "ISO4032") -> Part:
    """生成六角螺母实体（六棱柱 + ISO 内螺纹）。
    Generate a hex nut solid with ISO internal thread geometry.

    Args:
        size:     Size string, e.g. "M3", "M4".
        standard: One of "ISO4032", "GB6172", "DIN985".

    Geometry:
        - Origin at bottom face centre
        - Nut height along +Z
        - Internal thread via revolve subtract
    """
    std_key = standard.upper().replace(" ", "").replace("/", "").replace(".", "")
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

    # DIN 985: hex metal section + cylindrical nylon cap on top
    # DIN 985：六角金属段 + 顶部圆柱尼龙圈（无六角、无内螺纹）
    if std_key == "DIN985":
        nylon_h = min(1.5, spec.m * 0.375)
        metal_h = spec.m - nylon_h
        r_nylon = spec.s / 2      # nylon cap radius = inscribed circle (across-flats / 2)

        with BuildPart() as nut_body:
            with BuildSketch(Plane.XY):
                RegularPolygon(radius=r_hex, side_count=6)
            extrude(amount=metal_h)
            with Locations(Location((0, 0, metal_h))):
                Cylinder(
                    radius=r_nylon, height=nylon_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            # through-bore subtract (full height) / 通孔减料（全高）
            Cylinder(
                radius=spec.d / 2, height=spec.m,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

        # internal thread only in metal section / 内螺纹仅在金属段
        thread_sub = make_internal_thread(spec.d, spec.pitch, metal_h)
        return nut_body.part.cut(thread_sub)

    with BuildPart() as nut:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=spec.m)

    # 减去内螺纹旋转体（锯齿轮廓从轴到大径，在螺距半处缩至小径形成牙形）
    # Subtract internal thread solid (sawtooth ridges protrude inward into bore)
    thread_sub = make_internal_thread(spec.d, spec.pitch, spec.m)
    return nut.part.cut(thread_sub)


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
