"""MR series miniature deep-groove ball bearing (simplified).
MR 系列微型深沟球轴承（简化版）。

Source: bearings.yaml (YAML single source of truth / YAML 单一数据源)
Standards: ISO 15 / JIS B1521
License: MIT

支持型号 / Supported models:
    MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR104ZZ

简化程度 / Simplification level:
- 外圈 + 内圈 + 保持架（用中径圆柱近似）/ outer ring + inner ring + cage (mid-diameter cylinder approx)
- 不建模滚球；足够装配定位与 bbox 占位 / no balls modeled; sufficient for assembly and bbox
- 两端盖用浅槽区分（ZZ 双金属盖）/ end shields approximated
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    Cylinder,
    Mode,
    Part,
    export_step,
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
        # 仅加载微型深沟球轴承 / only load miniature deep-groove type
        if entry.get("type") != "miniature-deep-groove-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = MRSpec(d=dims["d"], D=dims["D"], B=dims["B"])
    return specs


# 参数表（从 bearings.yaml 动态加载 / loaded dynamically from bearings.yaml）
_SPECS: dict[str, MRSpec] = _load_specs()

SHIELD_DEPTH = 0.4   # ZZ 防尘盖槽深（近似值）
CAGE_RATIO   = 0.55  # 保持架中径 = (d + D) / 2 × ratio（视觉近似）


def make_mr_bearing(model: str = "MR85ZZ") -> Part:
    """生成 MR 系列微型轴承简化实体（外圈 + 内圈 + 中间保持架）。

    Args:
        model: 型号字符串，如 "MR63ZZ"、"MR85ZZ"。大小写不敏感。

    坐标：
        - 原点在轴承几何中心（XY 中心，Z 方向居中）
        - 轴承轴线沿 Z 轴
        - Z 范围：-B/2 ~ +B/2
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}")

    spec = _SPECS[key]
    r_inner = spec.d / 2
    r_outer = spec.D / 2
    half_b  = spec.B / 2
    r_cage  = (r_inner + r_outer) / 2

    # 环壁厚度（外圈/内圈各约占 1/4 径向间隙）
    gap     = r_outer - r_inner
    ring_t  = max(gap * 0.28, 0.3)   # 最小 0.3mm 防止负体积

    with BuildPart() as bearing:
        # 外圈（Z 居中）
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

        # 保持架（薄圆柱，仅视觉参考）
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

    return bearing.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name in _SPECS:
        part = make_mr_bearing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(f"OK: {out_path.name}  "
              f"⌀{bb.size.X:.1f}×{bb.size.Z:.1f}mm  "
              f"vol={part.volume:.2f} mm³")
