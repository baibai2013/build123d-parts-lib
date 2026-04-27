"""MR series miniature deep-groove ball bearing (simplified).

Source: data-sources/bearings.yaml:MR63ZZ~MR104ZZ (skill build123d-cad)
Standards: ISO 15 / JIS B1521
License: MIT

支持型号：MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR104ZZ

简化程度：
- 外圈 + 内圈 + 保持架（用中径圆柱近似）
- 不建模滚球；足够装配定位与 bbox 占位
- 两端盖用浅槽区分（ZZ 双金属盖）
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, Axis, BuildPart, Cylinder, Locations, Location,
    Mode, Part, export_step,
)


class MRSpec(NamedTuple):
    d: float   # inner diameter
    D: float   # outer diameter
    B: float   # width


# 参数表（与 data-sources/bearings.yaml 对应）
_SPECS: dict[str, MRSpec] = {
    "MR63ZZ":  MRSpec(d=3.0,  D=6.0,  B=2.5),
    "MR74ZZ":  MRSpec(d=4.0,  D=7.0,  B=2.5),
    "MR84ZZ":  MRSpec(d=4.0,  D=8.0,  B=3.0),
    "MR85ZZ":  MRSpec(d=5.0,  D=8.0,  B=2.5),
    "MR104ZZ": MRSpec(d=4.0,  D=10.0, B=4.0),
}

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
        raise ValueError(f"未知型号 {model!r}，可用型号：{available}")

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
