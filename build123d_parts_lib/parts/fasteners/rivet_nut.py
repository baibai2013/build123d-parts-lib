"""Blind rivet nut (nutsert) — pre-install form / 拉铆螺母（安装前形态）.

Standards: market convention (Bossard / Würth / Misumi rivet-nut catalogs)
License: MIT

支持规格 / Supported sizes: M3, M4

几何 / Geometry:
- 底部法兰盘（薄圆盘，安装时贴紧工件外表面）
  Bottom flange disc (thin, sits flush against workpiece outer surface)
- 主体圆柱沿 +Z 延伸（插入孔的部分）
  Main barrel cylinder extending along +Z (the part inserted into the hole)
- 内螺纹贯通 / Internal thread runs through the full length
- 原点法兰底面中心，+Z = 插入方向（朝向工件内部）
  Origin at flange bottom face centre; +Z = insertion direction (into workpiece)

注：建模为安装前形态（圆柱体）。安装后底部会变形外扩成"second flange"将工件夹紧，
本模块不建模该变形过程。
Note: Models the pre-install form (straight cylinder). After installation the rear
section deforms outward to form a second flange clamping the workpiece — this
deformation is not modeled here.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Part,
    export_step,
)

from ._thread_utils import make_internal_thread


# ─── 1. Spec 数据容器 / Spec NamedTuple ────────────────────────
class RivetNutSpec(NamedTuple):
    d:        float   # 螺纹大径 / nominal thread diameter
    pitch:    float   # 粗牙螺距 / coarse thread pitch
    od:       float   # 主体圆柱外径 / barrel OD
    length:   float   # 安装前总长（含法兰）/ pre-install total length (incl. flange)
    flange_d: float   # 法兰盘外径 / flange OD
    flange_t: float   # 法兰盘厚度 / flange thickness


# ─── 2. 内置后备数据 / Built-in fallback ─────────────────────
_FALLBACK: dict[str, RivetNutSpec] = {
    "M3": RivetNutSpec(d=3.0, pitch=0.50, od=5.0, length=12.0, flange_d=7.0, flange_t=1.0),
    "M4": RivetNutSpec(d=4.0, pitch=0.70, od=6.0, length=13.5, flange_d=9.0, flange_t=1.2),
}


# ─── 3. YAML 加载 / YAML loader ─────────────────────────────
def _load_specs() -> dict[str, RivetNutSpec]:
    """优先加载 fasteners.yaml；缺失时回退到 _FALLBACK。
    Prefer fasteners.yaml; fall back to _FALLBACK on missing keys.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, RivetNutSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "rivet-nut":
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                specs[size.upper()] = RivetNutSpec(
                    d=float(thread["d"]),
                    pitch=float(thread["pitch"]),
                    od=float(dims["od"]),
                    length=float(dims["length"]),
                    flange_d=float(dims["flange_d"]),
                    flange_t=float(dims["flange_t"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


# ─── 4. 公开工厂函数 / Public factory ─────────────────────────
def make_rivet_nut(size: str = "M4") -> Part:
    """生成拉铆螺母（安装前形态）。
    Generate a blind rivet nut (pre-install form).

    Geometry / 几何:
        - 法兰盘 z=0 → z=flange_t（直径 flange_d）
          Flange disc from z=0 → z=flange_t (diameter flange_d)
        - 主体圆柱 z=0 → z=length（直径 od < flange_d）
          Main barrel z=0 → z=length (diameter od < flange_d)
        - 贯通内螺纹（length 全长）
          Internal thread runs through the full length
        - 原点 = 法兰底面中心 / Origin at flange bottom face centre
        - +Z = 插入方向 / +Z = insertion direction

    Args:
        size: 规格字符串 e.g. "M3", "M4"

    Returns:
        Part: 安装前形态的拉铆螺母实体 / pre-install rivet nut solid
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]

    # 法兰盘：直径较大，z=0 起厚 flange_t
    # Flange disc: larger diameter, z=0 to z=flange_t
    with BuildPart() as flange_bp:
        Cylinder(
            radius=spec.flange_d / 2,
            height=spec.flange_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # 主体圆柱：直径较小，z=0 起到 z=length（与法兰底面对齐，覆盖法兰内部环段）
    # Main barrel: smaller diameter, z=0 to z=length (overlaps flange interior)
    with BuildPart() as body_bp:
        Cylinder(
            radius=spec.od / 2,
            height=spec.length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # 融合：法兰圆盘（半径 flange_d/2，高 flange_t）+ 主体圆柱（半径 od/2，高 length）
    # 二者从 z=0 起，主体圆柱穿过法兰内部，fuse 后形成"圆盘 + 凸出圆柱"形状
    # Fuse: flange disc + barrel; barrel passes through flange interior so the
    # result is "disc + protruding cylinder above".
    solid = flange_bp.part.fuse(body_bp.part)

    # 贯通内螺纹减料 / through internal thread subtract
    thread_sub = make_internal_thread(spec.d, spec.pitch, spec.length)
    return solid.cut(thread_sub)


# ─── 5. 独立运行导出 / Standalone export ─────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, _spec in _SPECS.items():
        part = make_rivet_nut(size=size)
        slug = size.lower()
        out = cache_dir / f"{slug}_rivet_nut.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm3")
