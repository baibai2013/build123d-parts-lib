"""角接触球轴承（Angular Contact Ball Bearing）。
Angular contact ball bearing — industrial quality.

几何特征：
- 外圈推力自由侧（+Z）带孔肩倒去，形成单肩截面（'C' 剖面）。
- 内圈标准双肩，承受单向轴向载荷 + 径向载荷 + 倾覆力矩。
- 通常成对 DB（背靠背）或 DF（面对面）配置，以支持双向轴向。

Geometry: outer ring has a counterbore on +Z side (thrust-free shoulder removed),
giving the characteristic single-shoulder cross-section.
Typically used in DB (back-to-back) or DF (face-to-face) pairs.

支持型号 / Supported models:
    7001C  — Φ12×Φ28×8 mm，接触角 15°（谐波减速器输出主轴承，BOM A4）
    7002C  — Φ15×Φ32×9 mm，接触角 15°
    7003C  — Φ17×Φ35×10 mm，接触角 15°
    7004C  — Φ20×Φ42×12 mm，接触角 15°

Standards / 参考标准: ISO 7228, JIS B1520, DIN 628-1
License: MIT
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import Compound, export_step

from build123d_parts_lib.parts.bearings._bearing_geometry import (
    make_angular_contact_bearing_compound,
)


class ACBSpec(NamedTuple):
    d:              float   # 内径 / bore diameter (mm)
    D:              float   # 外径 / outer diameter (mm)
    B:              float   # 宽度 / width (mm)
    contact_angle:  float   # 接触角 / contact angle (°)


def _load_specs() -> dict[str, ACBSpec]:
    """Load angular-contact bearing specs from bearings.yaml."""
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    specs: dict[str, ACBSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "angular-contact-ball-bearing":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = ACBSpec(
            d=dims["d"],
            D=dims["D"],
            B=dims["B"],
            contact_angle=dims.get("contact_angle_deg", 15.0),
        )
    return specs


_SPECS: dict[str, ACBSpec] = _load_specs()


def make_angular_contact_bearing(model: str = "7001C") -> Compound:
    """Generate an angular contact ball bearing.
    生成角接触球轴承（外圈 + 内圈 + 滚珠 + 保持架）。

    外圈 +Z 侧带孔肩倒去（单肩截面），是与深沟球轴承的关键视觉区别。
    Outer ring has counterbore on +Z side — key visual distinction from deep-groove.

    Args:
        model: 型号字符串，如 "7001C"。大小写不敏感。

    Returns:
        Compound with 4 labeled parts:
          - {model}/outer_ring  (steel silver, single-shoulder on +Z)
          - {model}/inner_ring  (steel silver, full shoulders)
          - {model}/cage        (brass gold)
          - {model}/ball_NN     (polished steel)

    Coordinates:
        - 原点在轴承几何中心，轴线沿 Z / origin at center, axis along Z
        - Z 范围 -B/2 ~ +B/2
        - 推力自由侧（开口肩）在 +Z / thrust-free (open shoulder) side is +Z
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(
            f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}"
        )

    spec = _SPECS[key]
    return make_angular_contact_bearing_compound(
        d=spec.d, D=spec.D, B=spec.B,
        contact_angle_deg=spec.contact_angle,
        label_prefix=f"{key}/",
    )


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name, spec in _SPECS.items():
        part = make_angular_contact_bearing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"angular_contact_{slug}.step"
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
