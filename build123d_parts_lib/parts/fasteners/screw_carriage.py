"""DIN 603 / ISO 8678 carriage bolt — round (mushroom) head + square neck.

Standards: DIN 603 / ISO 8678
License:   MIT

支持规格 / Supported sizes: M4 (extended, market convention), M5

几何 / Geometry (Pattern 13 — multi-body fuse):
  - 圆形(蘑菇)头 / Round mushroom head: cylinder + top fillet to dome
  - 方颈(防转) / Square neck: Box(sq, sq, sq_h) under the head
  - 螺杆 / Threaded shank: minor-diam cylinder + ISO external thread

坐标约定 / Coordinate convention:
  - 原点 = 螺杆底端中心 / origin = shank bottom centre
  - z = 0 .. length              : shank
  - z = length .. length+sq_h    : square neck
  - z = length+sq_h .. length+sq_h+k : head
  - +Z 朝向头部 / +Z points toward head

Note: DIN 603 standard begins at M5; M4 here follows market convention.
      DIN 603 标准起步于 M5;M4 按市场惯例补充。
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
    Cylinder,
    Location,
    Locations,
    Part,
    export_step,
)

from ._thread_utils import make_external_thread


# ─── 1. Spec 数据容器 / Spec data container ─────────────────────────────────
class CarriageBoltSpec(NamedTuple):
    d:     float   # 螺纹大径 / thread major diameter
    pitch: float   # 粗牙螺距 / coarse pitch
    dk:    float   # 圆头外径 / round head outer diameter
    k:     float   # 头高 / head height
    sq:    float   # 方颈对边 / square neck side length
    sq_h:  float   # 方颈高 / square neck depth


# ─── 2. 内置后备数据 / Built-in fallback data ───────────────────────────────
_FALLBACK: dict[str, CarriageBoltSpec] = {
    "M4": CarriageBoltSpec(d=4.0, pitch=0.70, dk=8.0,  k=2.4, sq=4.0, sq_h=2.4),
    "M5": CarriageBoltSpec(d=5.0, pitch=0.80, dk=13.0, k=3.0, sq=5.0, sq_h=3.5),
}

# 默认长度 / default lengths (used when length=None)
_DEFAULT_LENGTHS: dict[str, float] = {
    "M4": 20.0,
    "M5": 20.0,
}


# ─── 3. YAML 加载(优先 YAML，缺失 key 用 fallback 补) ──────────────────────
def _load_specs() -> dict[str, CarriageBoltSpec]:
    """从 _entries_standoff.yaml 读取 DIN 603 规格。
    Load DIN 603 carriage bolt specs from _entries_standoff.yaml.
    """
    repo_root = Path(__file__).parent.parent.parent.parent
    yaml_path = repo_root / "_entries_standoff.yaml"

    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, CarriageBoltSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "carriage-bolt":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head = entry.get("head", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = CarriageBoltSpec(
                    d     = float(thread["d"]),
                    pitch = float(thread["pitch"]),
                    dk    = float(head["dk"]),
                    k     = float(head["k"]),
                    sq    = float(dims["sq"]),
                    sq_h  = float(dims["sq_h"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


# ─── 4. 公开工厂函数 / Public factory function ─────────────────────────────
def make_carriage_bolt(size: str = "M4", length: float = 20.0) -> Part:
    """生成 DIN 603 马车螺栓(圆头 + 方颈 + 外螺纹杆)。
    Generate a DIN 603 / ISO 8678 carriage bolt (mushroom head + square neck +
    threaded shank).

    Args:
        size:   规格字符串 / Size string, e.g. "M4", "M5"
        length: 螺杆长度(从方颈底面到杆端) / shank length from neck to tip (mm)

    几何 / Geometry (Pattern 13):
        - 原点 = 螺杆底端中心 / Origin = shank bottom centre
        - z = 0 .. length                 : threaded shank
        - z = length .. length+sq_h       : square neck (anti-rotation)
        - z = length+sq_h .. length+sq_h+k: round mushroom head
        - 头顶圆角形成蘑菇 dome / top fillet creates the mushroom dome
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    if length <= 2.0:
        raise ValueError(f"length must be > 2.0 mm, got {length}")

    spec = _SPECS[key]

    # ── (1) 螺杆 (shank) ────────────────────────────────────────────────────
    # Pattern 15: 小径圆柱 + ISO 外螺纹 fuse
    # Pattern 15: minor-diameter cylinder fused with ISO external thread
    r_minor = (spec.d - 1.2269 * spec.pitch) / 2
    with BuildPart() as shank_bp:
        Cylinder(
            radius=r_minor,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    thread_add = make_external_thread(spec.d, spec.pitch, length)
    shank = shank_bp.part.fuse(thread_add)

    # ── (2) 方颈 (square neck) ──────────────────────────────────────────────
    # 中心在 XY 原点,z 范围 = [length, length+sq_h]
    # Center on XY origin, z range = [length, length+sq_h]
    with BuildPart() as neck_bp:
        with Locations(Location((0, 0, length))):
            Box(
                spec.sq, spec.sq, spec.sq_h,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    neck = neck_bp.part

    # ── (3) 圆形蘑菇头 (mushroom head) ──────────────────────────────────────
    # 圆柱底盘 + 顶部圆角 → 蘑菇形 dome
    # Cylinder base + top fillet → mushroom dome shape
    head_z0 = length + spec.sq_h
    with BuildPart() as head_bp:
        with Locations(Location((0, 0, head_z0))):
            Cylinder(
                radius=spec.dk / 2,
                height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
    head_solid = head_bp.part

    # 顶部圆角 → 蘑菇 dome / top fillet → mushroom dome
    # 圆角半径 = min(k, dk/4) 保证不超出实体
    # fillet radius = min(k, dk/4) to avoid over-filleting
    fillet_r = min(spec.k * 0.95, spec.dk / 4.0)
    head_top_z = head_z0 + spec.k
    top_edges = []
    for e in head_solid.edges():
        if not e.is_closed:
            continue
        cz = e.center().Z
        if abs(cz - head_top_z) < 0.2:
            top_edges.append(e)
    if top_edges:
        try:
            head_solid = head_solid.fillet(fillet_r, top_edges)
        except Exception:
            # fillet 失败时保持原始头部 / fall back to plain cylinder head
            pass

    # ── (4) 多体融合 / multi-body fuse (Pattern 13) ────────────────────────
    bolt = shank.fuse(neck).fuse(head_solid)

    return bolt


# ─── 5. 独立运行块 / standalone run block ──────────────────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size in _SPECS.keys():
        length = _DEFAULT_LENGTHS.get(size, 20.0)
        part = make_carriage_bolt(size=size, length=length)
        slug = f"{size.lower()}_din603_L{int(length)}"
        out = cache_dir / f"{slug}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
