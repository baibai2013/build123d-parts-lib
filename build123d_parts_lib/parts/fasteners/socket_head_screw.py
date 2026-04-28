"""ISO 4762 / DIN 912 hex socket head cap screw with ISO metric thread geometry.

Source: data-sources/fasteners.yaml + parts/fasteners/fasteners.yaml (skill build123d-cad)
Standards: ISO 4762 / DIN 912
License: MIT

支持规格：M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10

几何：
- 头部圆柱 + 内六角凹槽（正六棱柱减料，深度 ≈ 0.7k）
- 杆部 = 小径圆柱 + ISO 旋转锯齿螺纹牙（revolve）
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

from ._thread_utils import make_external_thread


class ScrewSpec(NamedTuple):
    d:      float   # 螺纹大径（公称直径） / nominal thread diameter
    dk:     float   # 头部外径 / head outer diameter
    k:      float   # 头部高度 / head height
    pitch:  float   # 粗牙螺距 / coarse thread pitch
    s:      float   # 内六角扳手对边宽 / hex socket key across-flats width


# 静态后备数据 —— 涵盖 YAML 中尚未收录的规格（M2/M4/M5）
# Static fallback for sizes not yet in YAML (M2, M4, M5)
_FALLBACK_SPECS: dict[str, ScrewSpec] = {
    "M2":  ScrewSpec(d=2.0, dk=3.8,  k=2.0, pitch=0.40, s=1.5),
    "M4":  ScrewSpec(d=4.0, dk=7.0,  k=4.0, pitch=0.70, s=3.0),
    "M5":  ScrewSpec(d=5.0, dk=8.5,  k=5.0, pitch=0.80, s=4.0),
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
        return dict(_FALLBACK_SPECS)

    specs: dict[str, ScrewSpec] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "hex-socket-head-cap-screw":
                continue
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
                    s=float(head["s"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

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

    for size in specs:
        if size not in lengths:
            lengths[size] = built_in.get(size, 10.0)

    return lengths


# 模块级单例 —— 仅在导入时加载一次 / module-level singletons, loaded once at import
_SPECS: dict[str, ScrewSpec] = _load_specs()
DEFAULT_LENGTHS: dict[str, float] = _build_default_lengths(_SPECS)


def make_socket_head_screw(size: str = "M3", length: float | None = None) -> Part:
    """生成 ISO 4762 内六角圆柱头螺丝实体（头 + 内六角凹槽 + ISO 螺纹杆）。
    Generate ISO 4762 socket head cap screw solid (head + hex socket recess + ISO threaded shank).

    Args:
        size:   规格字符串，如 "M3"、"M2.5"。 / Size string, e.g. "M3", "M2.5".
        length: 螺杆长度（不含头部）。None 时取各规格默认值。
                Shank length (excluding head). None uses per-size defaults.

    几何 / Geometry:
        - 原点在杆底面中心 / Origin at bottom of shank
        - 杆沿 +Z 伸出 `length` / Shank extends along +Z by `length`
        - 头部在杆顶面向上再伸出 `k` / Head sits atop shank, extends k upward
        - 内六角凹槽从头顶面向下切入，深度 0.7*k / Hex socket recess cut from head top, depth 0.7*k
        - 杆部建模为小径圆柱 + 旋转锯齿螺纹牙 / Shank = minor-diameter cylinder + revolve thread
    """
    key = size.upper().replace("M0", "M").strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知规格 {size!r}，可用：{available}")

    spec = _SPECS[key]
    l = length if length is not None else DEFAULT_LENGTHS[key]
    if l <= 0:
        raise ValueError(f"length 必须 > 0，得到 {l}")

    r_minor = (spec.d - 1.2269 * spec.pitch) / 2   # 小径 = 螺纹根部半径 / minor radius = thread root
    recess_depth = 0.7 * spec.k    # 内六角凹槽深度（ISO 4762 约定） / hex socket depth ~0.7*head height
    hex_r = spec.s / math.sqrt(3)  # 内六角外接圆半径 / hex socket circumradius from across-flats width

    with BuildPart() as screw:
        # 小径杆体（螺纹根部圆柱） / minor-diameter shank cylinder (thread root)
        Cylinder(
            radius=r_minor, height=l,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 头部圆柱 / head cylinder
        with Locations(Location((0, 0, l))):
            Cylinder(
                radius=spec.dk / 2, height=spec.k,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        # 内六角凹槽：从头顶面向下减料 / hex socket recess: cut downward from head top face
        head_top_z = l + spec.k
        with BuildSketch(Plane.XY.offset(head_top_z)):
            RegularPolygon(radius=hex_r, side_count=6)
        extrude(amount=-recess_depth, mode=Mode.SUBTRACT)

    # 叠加螺纹牙（外螺纹旋转体） / fuse external thread solid
    thread = make_external_thread(spec.d, spec.pitch, l)
    return screw.part.fuse(thread)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, default_l in DEFAULT_LENGTHS.items():
        part = make_socket_head_screw(size=size, length=default_l)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_iso4762_L{int(default_l)}.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.1f} mm³")
