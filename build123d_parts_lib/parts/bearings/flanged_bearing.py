"""法兰微型深沟球轴承（Flanged Miniature Deep-Groove Ball Bearing），简化版。
Flanged miniature deep-groove ball bearing, simplified.

Source: bearings.yaml (YAML single source of truth / YAML 单一数据源)
Standards: ISO 15 / JIS B1521（法兰系列）
License: MIT

支持型号 / Supported models:
    F688ZZ / F693ZZ / F623ZZ / F624ZZ / F625ZZ / F684ZZ

简化程度 / Simplification level:
- 外圈 + 内圈 + 保持架（用中径圆柱近似）+ 法兰圆盘
  outer ring + inner ring + cage (mid-diameter cylinder approx) + flange disc
- 不建模滚球；足够装配定位与 bbox 占位 / no balls modeled; sufficient for assembly and bbox
- 法兰贴在外圈 +Z 端（主体 Z 居中，法兰往 +Z 伸出）
  flange at +Z end of body (body Z-centered, flange protrudes +Z)
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
    Mode,
    Part,
    export_step,
)


class FlangedBearingSpec(NamedTuple):
    d: float         # inner diameter / 内径
    D: float         # outer diameter / 外径
    B: float         # width (body only, excluding flange) / 宽度（不含法兰）
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
        # 仅加载法兰深沟球轴承 / only load flanged deep-groove type
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


# 参数表（从 bearings.yaml 动态加载 / loaded dynamically from bearings.yaml）
_SPECS: dict[str, FlangedBearingSpec] = _load_specs()


def make_flanged_bearing(model: str = "F688ZZ") -> Part:
    """生成法兰微型轴承简化实体（外圈 + 内圈 + 保持架 + 法兰圆盘）。

    Args:
        model: 型号字符串，如 "F688ZZ"、"F624ZZ"。大小写不敏感。

    坐标：
        - 主体（B 高度）中心在 Z=0，Z 范围：-B/2 ~ +B/2
        - 法兰圆盘紧贴主体 +Z 端，Z 范围：+B/2 ~ +B/2+flange_t
        - 总高 = B + flange_t
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}")

    spec = _SPECS[key]
    r_inner   = spec.d / 2
    r_outer   = spec.D / 2
    r_flange  = spec.flange_D / 2

    # 环壁厚度
    gap    = r_outer - r_inner
    ring_t = max(gap * 0.28, 0.3)

    with BuildPart() as bearing:
        # ── 主体（Z 居中） ──────────────────────────────
        # 外圈
        Cylinder(
            radius=r_outer, height=spec.B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_outer - ring_t, height=spec.B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )

        # 内圈
        Cylinder(
            radius=r_inner + ring_t, height=spec.B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_inner, height=spec.B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )

        # 保持架
        r_cage = (r_inner + r_outer) / 2
        cage_t = min(ring_t * 0.6, gap * 0.15)
        Cylinder(
            radius=r_cage + cage_t / 2, height=spec.B * 0.6,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_cage - cage_t / 2, height=spec.B * 0.6,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )

        # ── 法兰圆盘（贴在主体 +Z 端） ─────────────────
        # 法兰中心 Z = B/2 + flange_t/2
        flange_z = spec.B / 2 + spec.flange_t / 2
        with Locations(Location((0, 0, flange_z))):
            Cylinder(
                radius=r_flange, height=spec.flange_t,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
            # 中心孔穿透法兰
            Cylinder(
                radius=r_inner, height=spec.flange_t,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )

    return bearing.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name in _SPECS:
        part = make_flanged_bearing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        spec = _SPECS[model_name]
        total_h = spec.B + spec.flange_t
        print(f"OK: {out_path.name}  "
              f"OD={bb.size.X:.1f}x{bb.size.Z:.1f}mm (expect OD={spec.flange_D}x{total_h})  "
              f"vol={part.volume:.2f} mm3")
