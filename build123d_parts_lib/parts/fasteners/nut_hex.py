"""Hex nuts: ISO 4032 standard, GB/T 6172.1 thin, DIN 985 nylon-insert lock nut.

Standards: ISO 4032 / GB/T 6172.1 / DIN 985
License: MIT

Supported sizes:
  ISO 4032  (standard):          M2, M2.5, M3, M4, M5, M6, M8, M10
  GB/T 6172.1 (thin):            M2, M2.5, M3, M4, M5, M6, M8, M10
  DIN 985 (nylon insert lock):   M3, M4, M5, M6, M8, M10

Simplification:
- Hexagonal prism + central through-hole (nominal thread diameter)
- DIN 985 modelled as slightly taller hex prism to represent nylon ring section
- No chamfer, no thread
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
    Mode,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)


class NutSpec(NamedTuple):
    d: float   # 公称螺纹直径（内孔） / nominal thread diameter (bore)
    s: float   # 对边宽（扳手宽） / wrench width (across flats)
    m: float   # 螺母高度 / nut height/thickness


# ─────────────────────────────────────────────────────────────────────────────
# 静态后备数据 —— 涵盖 YAML 中尚未收录的规格（M2 / M2.5）
# Static fallback data for sizes absent from YAML (M2, M2.5)
# ─────────────────────────────────────────────────────────────────────────────

_FALLBACK_ISO4032: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0, s=4.0, m=1.6),
    "M2.5": NutSpec(d=2.5, s=5.0, m=2.0),
}

_FALLBACK_GB6172: dict[str, NutSpec] = {
    "M2":   NutSpec(d=2.0, s=4.0, m=1.2),
    "M2.5": NutSpec(d=2.5, s=5.0, m=1.6),
    # M4 / M5 also absent from YAML — include here
    "M4":   NutSpec(d=4.0, s=7.0, m=2.2),
    "M5":   NutSpec(d=5.0, s=8.0, m=2.7),
}

# DIN 985 M3 absent from YAML
_FALLBACK_DIN985: dict[str, NutSpec] = {
    "M3":   NutSpec(d=3.0, s=5.5, m=4.0),
}


def _load_nut_specs() -> dict[str, dict[str, NutSpec]]:
    """从 fasteners.yaml 读取各标准六角螺母规格，与后备数据合并。
    Load hex nut specs from fasteners.yaml for each standard, merged with fallback data.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"

    # 标准名称映射：YAML type → 内部键 / type → internal key
    # hex-nut          → ISO4032
    # hex-thin-nut     → GB6172
    # hex-nylon-insert-lock-nut → DIN985
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
        # YAML 读取失败 → 完全使用后备数据 / fall back to static data entirely
        raw = {}

    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            nut_type = entry.get("type", "")
            std_key = type_to_std.get(nut_type)
            if std_key is None:
                continue
            # 从 factory.args.size 提取规格键 / extract size key from factory.args.size
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                result[std_key][size.upper()] = NutSpec(
                    d=float(thread["d"]),
                    s=float(dims["s"]),
                    m=float(dims["m"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    # 合并后备数据（仅填充 YAML 中不存在的规格）
    # Merge fallback data for sizes absent from YAML
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


# 模块级单例 —— 仅在导入时加载一次 / module-level singleton, loaded once at import
_NUT_SPECS = _load_nut_specs()

# 公开各标准的独立视图，与模块旧 API 兼容 / expose per-standard views for backward compat
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
    # For regular hexagon: s = 2 * r * cos(30°) = r * sqrt(3)
    return s / math.sqrt(3)


def make_hex_nut(size: str, standard: str = "ISO4032") -> Part:
    """Generate a simplified hex nut solid.
    生成六角螺母简化实体。

    Args:
        size:     Size string, e.g. "M3", "M4".
        standard: One of "ISO4032", "GB6172", "DIN985".

    Geometry:
        - Origin at bottom face centre
        - Nut height along +Z
        - Central through-hole diameter = nominal thread diameter
    """
    std_key = standard.upper().replace(" ", "").replace("/", "").replace(".", "")
    # 规范化常见别名 / normalise common aliases
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

    with BuildPart() as nut:
        # 六棱柱主体 / hexagonal prism
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=spec.m)
        # 中心通孔 / central through-hole
        Cylinder(
            radius=spec.d / 2, height=spec.m,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

    return nut.part


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
