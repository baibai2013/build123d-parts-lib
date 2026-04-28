"""Washers: ISO 7089 plain washer and GB/T 93 spring washer (simplified).

Standards: ISO 7089 / GB/T 93
License: MIT

Supported sizes:
  ISO 7089 (flat):    M2, M2.5, M3, M4, M5
  GB/T 93 (spring):  M3, M4, M5

Simplification:
- ISO 7089: simple annular ring (torus-section cylinder with bore)
- GB/T 93 spring washer: annular ring with one diagonal radial cut slot
  (single diagonal slot across the top face represents the split)
- No thread; sufficient for assembly positioning
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    export_step,
)


class WasherSpec(NamedTuple):
    id_: float   # 内径（孔径） / inner diameter (bore)
    od:  float   # 外径 / outer diameter
    t:   float   # 厚度 / thickness


# ─────────────────────────────────────────────────────────────────────────────
# 静态后备数据 —— 涵盖 YAML 中尚未收录的规格
# Static fallback for sizes absent from YAML
# ─────────────────────────────────────────────────────────────────────────────

# ISO 7089 flat: M2 / M2.5 absent from YAML
_FALLBACK_FLAT: dict[str, WasherSpec] = {
    "M2":   WasherSpec(id_=2.2, od=5.0,  t=0.3),
    "M2.5": WasherSpec(id_=2.7, od=6.0,  t=0.5),
}

# GB/T 93 spring: M5 absent from YAML
_FALLBACK_SPRING: dict[str, WasherSpec] = {
    "M5": WasherSpec(id_=5.1, od=9.2, t=1.3),
}


def _load_washer_specs() -> tuple[dict[str, WasherSpec], dict[str, WasherSpec]]:
    """从 fasteners.yaml 读取垫圈规格，与后备数据合并。
    Load washer specs from fasteners.yaml, merged with fallback data.
    Returns (flat_specs, spring_specs).
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        raw = {}

    flat: dict[str, WasherSpec] = {}
    spring: dict[str, WasherSpec] = {}

    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            w_type = entry.get("type", "")
            if w_type not in ("plain-washer", "spring-lock-washer"):
                continue
            # 从 factory.args.size 提取规格键 / extract size key from factory.args.size
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            dims = entry.get("dimensions", {})
            try:
                spec = WasherSpec(
                    id_=float(dims["id"]),
                    od=float(dims["od"]),
                    t=float(dims["t"]),
                )
            except (KeyError, TypeError, ValueError):
                continue
            if w_type == "plain-washer":
                flat[size.upper()] = spec
            else:
                spring[size.upper()] = spec

    # 合并后备数据（仅填充 YAML 中不存在的规格）
    # Merge fallback data for sizes absent from YAML
    for size, spec in _FALLBACK_FLAT.items():
        if size not in flat:
            flat[size] = spec

    for size, spec in _FALLBACK_SPRING.items():
        if size not in spring:
            spring[size] = spec

    return flat, spring


# 模块级单例 —— 仅在导入时加载一次 / module-level singletons, loaded once at import
_SPECS_FLAT, _SPECS_SPRING = _load_washer_specs()


def _make_flat_washer(spec: WasherSpec) -> Part:
    """Plain annular ring. / 普通环形平垫圈。"""
    with BuildPart() as w:
        Cylinder(
            radius=spec.od / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=spec.id_ / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
    return w.part


def _make_spring_washer(spec: WasherSpec) -> Part:
    """Spring washer: annular ring with one diagonal cut slot at one side.
    弹簧垫圈：一侧对角切口的环形垫圈。

    The slot is a narrow box that cuts radially through the ring at an angle,
    representing the characteristic split of a spring washer.
    """
    with BuildPart() as w:
        # 基础环形圈（弹簧垫圈受压时略厚）
        # Base annular ring (slightly thicker - spring is under tension when flat)
        Cylinder(
            radius=spec.od / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=spec.id_ / 2, height=spec.t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        # 对角切口：窄矩形沿 X 轴放置，绕 Z 轻微旋转以穿过环体
        # Diagonal cut slot: narrow box along X, rotated slightly in Z to cut through ring
        slot_width = spec.t * 0.8   # 切口宽度与厚度成比例 / slot width proportional to thickness
        slot_length = spec.od       # 足够穿过整个环体 / long enough to cut through the ring
        slot_height = spec.t * 1.2  # 略高于环体确保干净切割 / slightly taller for clean cut
        # 切口居中，以 10° 斜角切穿环体 / slot at centre, 10° diagonal cut
        with Locations(Location((0, 0, spec.t / 2), (0, 0, 10))):
            Box(
                length=slot_length, width=slot_width, height=slot_height,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    return w.part


def make_washer(size: str, type_: str = "flat") -> Part:
    """Generate a simplified washer solid.
    生成简化垫圈实体。

    Args:
        size:  Size string, e.g. "M3", "M4".
        type_: "flat" for ISO 7089, "spring" for GB/T 93.

    Geometry:
        - Origin at bottom face centre
        - Height along +Z
    """
    t = type_.lower().strip()
    if t == "flat":
        key = size.upper().replace(" ", "").strip()
        if key not in _SPECS_FLAT:
            available = ", ".join(_SPECS_FLAT.keys())
            raise ValueError(f"Size {size!r} not available for flat washer, available: {available}")
        return _make_flat_washer(_SPECS_FLAT[key])
    elif t == "spring":
        key = size.upper().replace(" ", "").strip()
        if key not in _SPECS_SPRING:
            available = ", ".join(_SPECS_SPRING.keys())
            raise ValueError(f"Size {size!r} not available for spring washer, available: {available}")
        return _make_spring_washer(_SPECS_SPRING[key])
    else:
        raise ValueError(f"Unknown type_ {type_!r}, use 'flat' or 'spring'")


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size in _SPECS_FLAT:
        part = make_washer(size=size, type_="flat")
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_washer_iso7089.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.3f} mm3")

    for size in _SPECS_SPRING:
        part = make_washer(size=size, type_="spring")
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_washer_gbt93.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.3f} mm3")
