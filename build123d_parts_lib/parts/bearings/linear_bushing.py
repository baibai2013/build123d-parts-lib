"""ISO 10736 / JIS B 2604 linear ball bearing (LMxxUU series).
ISO 10736 / JIS B 2604 直线球轴承（LMxxUU 系列）。

Linear ball bushing for smooth shafts.
直线球轴承 — LM6UU / LM8UU / LM10UU / LM12UU / LMF8UU / LMF10UU

Geometry / 几何约定:
  - Origin at bottom center / 原点在底面中心
  - Axis along +Z / 轴线沿 +Z
  - Outer cylinder diameter D, length L / 外径 D，总长 L
  - For flanged (LMF) type: flange protrudes at +Z end / 法兰伸出在 +Z 端
    Total height = L + flange_t / 总高 = L + flange_t
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


class LMSpec(NamedTuple):
    d: float           # bore / 内径
    D: float           # outer diameter / 外径
    L: float           # length / 长度
    flange_D: float = 0.0   # flange outer diameter (LMF type) / 法兰外径
    flange_t: float = 0.0   # flange thickness / 法兰厚度


def _load_specs() -> dict[str, LMSpec]:
    """Load linear bushing specs from lm_bearings.yaml.
    从 lm_bearings.yaml 加载直线轴承规格。
    """
    yaml_path = Path(__file__).parent / "lm_bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    specs: dict[str, LMSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        dims = entry.get("dimensions", {})
        specs[key] = LMSpec(
            d=dims["d"],
            D=dims["D"],
            L=dims["L"],
            flange_D=dims.get("flange_D", 0.0),
            flange_t=dims.get("flange_t", 0.0),
        )
    return specs


# 参数表（从 lm_bearings.yaml 动态加载 / loaded dynamically from lm_bearings.yaml）
_SPECS: dict[str, LMSpec] = _load_specs()


def make_linear_bushing(model: str = "LM8UU") -> Part:
    """Generate simplified LMxxUU / LMFxxUU linear bushing solid.
    生成简化直线轴承实体（外圆筒 + 内孔，法兰型含法兰圆盘）。

    Args:
        model: Model string, e.g. "LM8UU", "LMF10UU". Case-insensitive.
               型号字符串，大小写不敏感。

    Coordinate origin: bottom center / 原点在底面中心
    Z range (non-flanged): 0 ~ L
    Z range (flanged LMF):  0 ~ L+flange_t
        - Cylinder body: Z 0 ~ L / 圆筒主体
        - Flange disc:   Z L ~ L+flange_t / 法兰圆盘在 +Z 端
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(
            f"unknown model / 未知型号 {model!r}. Available / 可用型号：{available}"
        )

    spec = _SPECS[key]

    with BuildPart() as bushing:
        # 外圆筒 / outer cylinder (body, Z 0 ~ L)
        Cylinder(
            radius=spec.D / 2,
            height=spec.L,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 内孔贯穿全长 / bore hole through full length
        Cylinder(
            radius=spec.d / 2,
            height=spec.L,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        # 法兰圆盘（仅 LMF 型）/ flange disc (LMF type only)
        if spec.flange_D > 0 and spec.flange_t > 0:
            # 法兰贴在主体 +Z 端 / flange at top (+Z) end of body
            flange_z = spec.L + spec.flange_t / 2
            with Locations(Location((0, 0, flange_z))):
                Cylinder(
                    radius=spec.flange_D / 2,
                    height=spec.flange_t,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                )
                # 法兰中心孔与内孔同径 / bore through flange same as body bore
                Cylinder(
                    radius=spec.d / 2,
                    height=spec.flange_t,
                    align=(Align.CENTER, Align.CENTER, Align.CENTER),
                    mode=Mode.SUBTRACT,
                )

    return bushing.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    for model_name in _SPECS:
        part = make_linear_bushing(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(f"OK: {out_path.name}  OD={bb.size.X:.1f}x{bb.size.Z:.1f}mm")
