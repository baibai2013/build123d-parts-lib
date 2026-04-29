"""薄截面深沟球轴承（Thin-Section Deep-Groove Ball Bearing）。
Thin-section deep-groove ball bearing — industrial quality.

几何与标准深沟球轴承相同，但截面极薄（(D-d)/2 ≈ 3–6 mm）。
Same geometry as ISO 15 deep-groove ball bearing; cross-section is very thin.

支持型号 / Supported models:
    TS17x23x3_5  — Φ17×Φ23×3.5 mm（谐波减速器波发生器轴承，BOM A3）
    TS20x27x4    — Φ20×Φ27×4 mm
    TS25x33x4    — Φ25×Φ33×4 mm
    TS30x40x6    — Φ30×Φ40×6 mm（KSS / INA 系）

Standards / 参考标准: ISO 15, JIS B1521, INA(FAG) 61803 系列
License: MIT
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import Compound, export_step

from build123d_parts_lib.parts.bearings._bearing_geometry import (
    make_deep_groove_bearing_compound,
)


class ThinSectionSpec(NamedTuple):
    d: float   # 内径 / bore diameter (mm)
    D: float   # 外径 / outer diameter (mm)
    B: float   # 宽度 / width (mm)


def _load_specs() -> dict[str, ThinSectionSpec]:
    """Load thin-section bearing specs from bearings.yaml.
    从 bearings.yaml 加载薄截面轴承规格（thin-section-deep-groove-ball-bearing 类型）。
    """
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text())
    specs: dict[str, ThinSectionSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "thin-section-deep-groove-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key.upper()] = ThinSectionSpec(d=dims["d"], D=dims["D"], B=dims["B"])
    return specs


_SPECS: dict[str, ThinSectionSpec] = _load_specs()


def make_thin_section_bearing(model: str = "TS17x23x3_5") -> Compound:
    """Generate a thin-section deep-groove ball bearing.
    生成薄截面深沟球轴承（外圈 + 内圈 + 滚珠 + 保持架）。

    Args:
        model: 型号字符串，如 "TS17x23x3_5"。大小写不敏感。

    Returns:
        Compound with 4 labeled parts:
          - {model}/outer_ring  (steel silver)
          - {model}/inner_ring  (steel silver)
          - {model}/cage        (brass gold)
          - {model}/ball_NN     (polished steel)

    Coordinates:
        - 原点在轴承几何中心，轴线沿 Z / origin at center, axis along Z
        - Z 范围 -B/2 ~ +B/2
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(
            f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}"
        )

    spec = _SPECS[key]
    return make_deep_groove_bearing_compound(
        d=spec.d, D=spec.D, B=spec.B,
        label_prefix=f"{key}/",
    )


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name, spec in _SPECS.items():
        part = make_thin_section_bearing(model_name)
        slug = model_name.lower().replace("-", "_")
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(
            f"OK: {out_path.name}  "
            f"⌀{bb.size.X:.1f}×{bb.size.Z:.1f}mm  "
            f"vol={part.volume:.2f} mm³"
        )
        # Layer 1 断言 / Layer 1 assertions
        assert part.is_valid, f"{model_name}: BRep invalid"
        assert part.volume > 0, f"{model_name}: zero volume"
        assert abs(bb.size.X - spec.D) < 0.5, f"{model_name}: OD mismatch"
        assert abs(bb.size.Z - spec.B) < 0.5, f"{model_name}: B mismatch"
        print(f"   ✅ 断言全通 / All assertions passed")
