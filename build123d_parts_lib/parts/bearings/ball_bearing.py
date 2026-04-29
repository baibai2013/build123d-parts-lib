"""ISO 15 deep-groove ball bearing — industrial quality.
ISO 15 深沟球轴承（工业级几何）。

Source: bearings.yaml (YAML single source of truth / YAML 单一数据源)
Standards: ISO 15 / JIS B1521
License: MIT

支持型号 / Supported models:
    608ZZ / 624ZZ / 625ZZ / 626ZZ / 6000ZZ / 6001-2RS / 6002ZZ

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


class BearingSpec(NamedTuple):
    d: float   # inner diameter / 内径
    D: float   # outer diameter / 外径
    B: float   # width / 宽度


def _load_specs() -> dict[str, BearingSpec]:
    """Load deep-groove ball bearing specs from bearings.yaml.
    从 bearings.yaml 加载深沟球轴承规格（仅 deep-groove-ball-bearing 类型）。
    """
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text())
    specs: dict[str, BearingSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "deep-groove-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = BearingSpec(d=dims["d"], D=dims["D"], B=dims["B"])
    return specs


_SPECS: dict[str, BearingSpec] = _load_specs()


def make_ball_bearing(model: str = "608ZZ") -> Compound:
    """Generate an industrial-quality ISO 15 deep-groove ball bearing.
    生成 ISO 15 深沟球轴承工业级实体（外圈 + 内圈 + 滚珠 + 保持架）。

    Args:
        model: 型号字符串，如 "608ZZ"、"6001-2RS"。大小写不敏感。

    Returns:
        Compound with 4 labeled parts:
          - {model}/outer_ring  (steel silver)
          - {model}/inner_ring  (steel silver)
          - {model}/cage        (brass gold)
          - {model}/ball_NN     (polished steel, N balls)

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
        part = make_ball_bearing(model_name)
        slug = model_name.lower().replace("-", "_")
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        n_balls = sum(1 for c in part.children if c.label.endswith(tuple(f"ball_{i:02d}" for i in range(30))))
        print(f"OK: {out_path.name}  "
              f"⌀{bb.size.X:.1f}×{bb.size.Z:.1f}mm  "
              f"balls={n_balls}  "
              f"vol={part.volume:.2f} mm³")
