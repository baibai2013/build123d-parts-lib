"""MR series miniature deep-groove ball bearing — industrial quality.
MR 系列微型深沟球轴承（工业级几何）。

Source: bearings.yaml (YAML single source of truth / YAML 单一数据源)
Standards: ISO 15 / JIS B1521
License: MIT

支持型号 / Supported models:
    MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR104ZZ

几何特点 / Geometry features:
- 外圈 + 内圈均带真实滚道沟槽（环面切除）/ raceway grooves via torus subtraction
- 按节圆自动分布滚珠（Sphere 实体）/ actual steel balls on pitch circle
- 保持架带球窝（Sphere 切除）/ cage with spherical ball pockets
- 返回 Compound，各部件带 label + 金属色彩 / Compound with labeled metallic parts
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import Compound, export_step

from build123d_parts_lib.parts.bearings._bearing_geometry import (
    make_deep_groove_bearing_compound,
)


class MRSpec(NamedTuple):
    d: float   # inner diameter / 内径
    D: float   # outer diameter / 外径
    B: float   # width / 宽度


def _load_specs() -> dict[str, MRSpec]:
    """Load MR bearing specs from bearings.yaml.
    从 bearings.yaml 加载 MR 系列微型轴承规格（仅 miniature-deep-groove-ball-bearing 类型）。
    """
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text())
    specs: dict[str, MRSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "miniature-deep-groove-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = MRSpec(d=dims["d"], D=dims["D"], B=dims["B"])
    return specs


_SPECS: dict[str, MRSpec] = _load_specs()


def make_mr_bearing(model: str = "MR85ZZ") -> Compound:
    """Generate an industrial-quality MR series miniature ball bearing.
    生成 MR 系列微型深沟球轴承工业级实体（外圈 + 内圈 + 滚珠 + 保持架）。

    Args:
        model: 型号字符串，如 "MR63ZZ"、"MR85ZZ"。大小写不敏感。

    Returns:
        Compound with 4 labeled parts (outer_ring / inner_ring / cage / ball_NN)

    Coordinates:
        - 原点在轴承几何中心，轴线沿 Z / origin at center, axis along Z
        - Z 范围 -B/2 ~ +B/2
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}")

    spec = _SPECS[key]
    return make_deep_groove_bearing_compound(
        d=spec.d, D=spec.D, B=spec.B,
        label_prefix=f"{key}/",
    )


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name in _SPECS:
        part = make_mr_bearing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        n_balls = sum(1 for c in part.children if "ball_" in c.label)
        print(f"OK: {out_path.name}  "
              f"⌀{bb.size.X:.1f}×{bb.size.Z:.1f}mm  "
              f"balls={n_balls}  "
              f"vol={part.volume:.2f} mm³")
