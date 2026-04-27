"""法兰微型深沟球轴承（Flanged Miniature Deep-Groove Ball Bearing），简化版。

Source: data-sources/bearings.yaml (skill build123d-cad)
Standards: ISO 15 / JIS B1521（法兰系列）
License: MIT

支持型号：F688ZZ / F693ZZ / F623ZZ / F624ZZ / F625ZZ / F684ZZ

简化程度：
- 外圈 + 内圈 + 保持架（用中径圆柱近似）+ 法兰圆盘
- 不建模滚球；足够装配定位与 bbox 占位
- 法兰贴在外圈 +Z 端（主体 Z 居中，法兰往 +Z 伸出）
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align, BuildPart, Cylinder, Location, Locations,
    Mode, Part, export_step,
)


class FlangedBearingSpec(NamedTuple):
    d: float         # inner diameter
    D: float         # outer diameter
    B: float         # width (body only, excluding flange)
    flange_D: float  # flange outer diameter
    flange_t: float  # flange thickness


# 参数表（与 data-sources/bearings.yaml 对应）
_SPECS: dict[str, FlangedBearingSpec] = {
    "F688ZZ": FlangedBearingSpec(d=8.0, D=16.0, B=5.0,   flange_D=17.5, flange_t=1.0),
    "F693ZZ": FlangedBearingSpec(d=3.0, D=8.0,  B=3.0,   flange_D=9.2,  flange_t=0.6),
    "F623ZZ": FlangedBearingSpec(d=3.0, D=10.0, B=4.0,   flange_D=11.2, flange_t=0.8),
    "F624ZZ": FlangedBearingSpec(d=4.0, D=13.0, B=5.0,   flange_D=14.5, flange_t=1.0),
    "F625ZZ": FlangedBearingSpec(d=5.0, D=16.0, B=5.0,   flange_D=17.5, flange_t=1.0),
    "F684ZZ": FlangedBearingSpec(d=4.0, D=9.0,  B=2.5,   flange_D=10.3, flange_t=0.6),
}


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
        raise ValueError(f"未知型号 {model!r}，可用型号：{available}")

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
