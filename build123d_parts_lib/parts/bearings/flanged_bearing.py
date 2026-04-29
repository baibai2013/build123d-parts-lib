"""Flanged miniature deep-groove ball bearing — industrial quality.
法兰微型深沟球轴承（工业级几何）。

Source: bearings.yaml (YAML single source of truth / YAML 单一数据源)
Standards: ISO 15 / JIS B1521（法兰系列）
License: MIT

支持型号 / Supported models:
    F688ZZ / F693ZZ / F623ZZ / F624ZZ / F625ZZ / F684ZZ

几何特点 / Geometry features:
- 主体：外圈 + 内圈 + 滚珠 + 保持架（与 MR/ball_bearing 一致）
  Body: outer ring + inner ring + balls + cage (same as MR/ball_bearing)
- 法兰圆盘贴在外圈 +Z 端
  Flange disc at +Z end of outer ring
- 返回 Compound：4 主体件 + N 滚珠 + 1 法兰 / 4 body parts + N balls + 1 flange
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import Compound, export_step

from build123d_parts_lib.parts.bearings._bearing_geometry import (
    make_deep_groove_bearing_compound,
    make_flange_disc,
)


class FlangedBearingSpec(NamedTuple):
    d: float         # inner diameter / 内径
    D: float         # outer diameter / 外径
    B: float         # body width (excludes flange) / 主体宽度（不含法兰）
    flange_D: float  # flange outer diameter / 法兰外径
    flange_t: float  # flange thickness / 法兰厚度


def _load_specs() -> dict[str, FlangedBearingSpec]:
    """Load flanged bearing specs from bearings.yaml.
    从 bearings.yaml 加载法兰轴承规格（仅 flanged-deep-groove-ball-bearing 类型）。
    """
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text())
    specs: dict[str, FlangedBearingSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "flanged-deep-groove-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = FlangedBearingSpec(
            d=dims["d"],
            D=dims["D"],
            B=dims["B"],
            flange_D=dims["flange_D"],
            flange_t=dims["flange_t"],
        )
    return specs


_SPECS: dict[str, FlangedBearingSpec] = _load_specs()


def make_flanged_bearing(model: str = "F688ZZ") -> Compound:
    """Generate an industrial-quality flanged miniature ball bearing.
    生成法兰微型深沟球轴承工业级实体（主体 + 法兰圆盘）。

    Args:
        model: 型号字符串，如 "F688ZZ"、"F624ZZ"。大小写不敏感。

    Returns:
        Compound with body parts + flange:
          - {model}/outer_ring / inner_ring / cage / ball_NN
          - {model}/flange

    Coordinates:
        - 主体（B 高度）中心在 Z=0 / body centered at Z=0
        - 法兰贴在主体 +Z 端，Z 范围 +B/2 ~ +B/2+flange_t
        - 总高 = B + flange_t
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}")

    spec = _SPECS[key]

    # 主体（外圈 + 内圈 + 滚珠 + 保持架）/ body core
    body = make_deep_groove_bearing_compound(
        d=spec.d, D=spec.D, B=spec.B,
        label_prefix=f"{key}/",
    )

    # 法兰圆盘（贴在外圈 +Z 端）/ flange disc at +Z end
    flange_z_center = spec.B / 2 + spec.flange_t / 2
    flange = make_flange_disc(
        d=spec.d,
        flange_D=spec.flange_D,
        flange_t=spec.flange_t,
        z_center=flange_z_center,
        label=f"{key}/flange",
    )

    # 组合：body 的所有 children + flange
    all_children = list(body.children) + [flange]
    result = Compound(children=all_children)
    result.label = f"{key}/bearing"
    return result


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name in _SPECS:
        part = make_flanged_bearing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        n_balls = sum(1 for c in part.children if "ball_" in c.label)
        spec = _SPECS[model_name]
        total_h = spec.B + spec.flange_t
        print(f"OK: {out_path.name}  "
              f"OD={bb.size.X:.1f}×{bb.size.Z:.1f}mm (expect ⌀{spec.flange_D}×{total_h})  "
              f"balls={n_balls}  "
              f"vol={part.volume:.2f} mm³")
