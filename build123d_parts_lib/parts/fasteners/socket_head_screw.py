"""ISO 4762 / DIN 912 hex socket head cap screw (simplified).

Source: data-sources/fasteners.yaml + parts/fasteners/fasteners.yaml (skill build123d-cad)
Standards: ISO 4762 / DIN 912
License: MIT

支持规格：M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10

简化程度：
- 头部圆柱（不建模内六角凹槽，仅外形）
- 杆部光杆（不建螺纹；装配用足够）
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Location,
    Locations,
    Part,
    export_step,
)


class ScrewSpec(NamedTuple):
    d:      float   # 螺纹大径（公称直径） / nominal thread diameter
    dk:     float   # 头部外径 / head outer diameter
    k:      float   # 头部高度 / head height
    pitch:  float   # 粗牙螺距 / coarse thread pitch


# 静态后备数据 —— 涵盖 YAML 中尚未收录的规格（M2/M4/M5）
# Static fallback for sizes not yet in YAML (M2, M4, M5)
_FALLBACK_SPECS: dict[str, ScrewSpec] = {
    "M2":  ScrewSpec(d=2.0, dk=3.8,  k=2.0, pitch=0.40),
    "M4":  ScrewSpec(d=4.0, dk=7.0,  k=4.0, pitch=0.70),
    "M5":  ScrewSpec(d=5.0, dk=8.5,  k=5.0, pitch=0.80),
}


def _load_specs() -> dict[str, ScrewSpec]:
    """从 fasteners.yaml 读取 hex-socket-head-cap-screw 规格，与后备数据合并。
    Load hex-socket-head-cap-screw specs from fasteners.yaml, merged with fallback data.
    YAML 优先；后备数据补充 YAML 中不存在的规格。
    YAML takes priority; fallback fills in sizes absent from YAML.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        # YAML 读取失败时退化为全静态数据 / Degrade to full static data if YAML read fails
        return dict(_FALLBACK_SPECS)

    specs: dict[str, ScrewSpec] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-socket-head-cap-screw":
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
    # Merge fallback (only for sizes not present in YAML)
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
        "M6": 20.0, "M8": 25.0, "M10": 30.0,
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
            if entry.get("type") != "hex-socket-head-cap-screw":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            common = entry.get("common_lengths_mm")
            if common and isinstance(common, list) and len(common) > 0:
                lengths[size.upper()] = float(common[0])

    # 补充后备默认长度 / fill in missing default lengths
    for size in specs:
        if size not in lengths:
            lengths[size] = built_in.get(size, 10.0)

    return lengths


# 模块级单例 —— 仅在导入时加载一次 / module-level singletons, loaded once at import
_SPECS: dict[str, ScrewSpec] = _load_specs()
DEFAULT_LENGTHS: dict[str, float] = _build_default_lengths(_SPECS)


def make_socket_head_screw(size: str = "M3", length: float | None = None) -> Part:
    """生成 ISO 4762 内六角圆柱头螺丝简化实体（头 + 光杆）。

    Args:
        size:   规格字符串，如 "M3"、"M2.5"。
        length: 螺杆长度（不含头部）。None 时取各规格默认值。

    几何：
        - 原点在杆底面中心
        - 杆沿 +Z 伸出 `length`
        - 头部在杆顶面向上再伸出 `k`
    """
    key = size.upper().replace("M0", "M").strip()
    # 兼容 "m3" / "M3" / "M 3"
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知规格 {size!r}，可用：{available}")

    spec = _SPECS[key]
    l = length if length is not None else DEFAULT_LENGTHS[key]
    if l <= 0:
        raise ValueError(f"length 必须 > 0，得到 {l}")

    with BuildPart() as screw:
        Cylinder(
            radius=spec.d / 2, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        with Locations(Location((0, 0, l))):
            Cylinder(
                radius=spec.dk / 2, height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return screw.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in DEFAULT_LENGTHS.items():
        part = make_socket_head_screw(size=size, length=default_l)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_iso4762_L{int(default_l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.1f} mm³")
