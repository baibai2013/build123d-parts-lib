"""GT2 timing pulley (2 mm pitch) — simplified assembly placeholder.

Source: GT2 belt/pulley standard (common in 3D printer / robotics)
Standards: GT2 (Gates Rubber / RepRap community)
License: MIT

支持规格：16T / 20T / 30T / 40T，孔径 ⌀5 / ⌀8

简化程度：
- 两端法兰盘 + 中间齿部圆柱（不建精确齿形）
- 中心孔 + 侧向 M3 顶丝孔
- 足够装配占位与 BBox 计算
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

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


class GT2PulleySpec(NamedTuple):
    teeth: int       # 齿数
    bore_d: float    # 中心孔直径 (mm)
    pitch_d: float   # 节径 (mm)，推导值
    od: float        # 外径 (mm)，推导值
    flange_od: float # 法兰外径 (mm)


# GT2 标准：齿距 2.0 mm
_PITCH = 2.0  # mm


def _derive_spec(teeth: int, bore_d: float) -> GT2PulleySpec:
    """从齿数和孔径推导几何参数。"""
    pitch_d = teeth * _PITCH / math.pi   # 节径 = teeth × pitch / π
    od = pitch_d - 0.254 * 2             # 外径（GT2 齿顶略低于节圆）
    flange_od = od + 2.5                 # 法兰外径 = 外径 + 2.5 mm
    return GT2PulleySpec(
        teeth=teeth,
        bore_d=bore_d,
        pitch_d=round(pitch_d, 3),
        od=round(od, 3),
        flange_od=round(flange_od, 3),
    )


# 参数表（典型规格组合）
_SPECS: dict[str, GT2PulleySpec] = {
    "GT2_16T_BORE5":  _derive_spec(16, 5.0),
    "GT2_16T_BORE8":  _derive_spec(16, 8.0),
    "GT2_20T_BORE5":  _derive_spec(20, 5.0),
    "GT2_20T_BORE8":  _derive_spec(20, 8.0),
    "GT2_30T_BORE5":  _derive_spec(30, 5.0),
    "GT2_30T_BORE8":  _derive_spec(30, 8.0),
    "GT2_40T_BORE5":  _derive_spec(40, 5.0),
    "GT2_40T_BORE8":  _derive_spec(40, 8.0),
}

# 带宽槽 (6mm GT2 带)
_BELT_WIDTH = 6.0   # mm
_FLANGE_T   = 1.0   # mm，法兰厚度
_TOTAL_H    = 2 * _FLANGE_T + _BELT_WIDTH  # = 8.0 mm，总高
_M3_HOLE_D  = 3.0   # mm，顶丝孔直径


def make_gt2_pulley(teeth: int = 20, bore_d: float = 5.0) -> Part:
    """Generate a simplified GT2 timing pulley solid (flanges + body + bore + set-screw hole).

    Args:
        teeth:  Number of teeth (16 / 20 / 30 / 40).
        bore_d: Bore (shaft hole) diameter in mm (5.0 or 8.0).

    Coordinate system:
        - Z axis is the rotational axis.
        - Geometric center at Z=0 (flanges symmetric about XY plane).
        - Z range: -TOTAL_H/2 ~ +TOTAL_H/2.
    """
    spec = _derive_spec(teeth, bore_d)
    r_body    = spec.od / 2
    r_flange  = spec.flange_od / 2
    r_bore    = bore_d / 2
    half_h    = _TOTAL_H / 2

    # 验证孔径不超过外径
    if bore_d >= spec.od:
        raise ValueError(
            f"bore_d={bore_d} >= od={spec.od:.3f}; 减小孔径或增加齿数"
        )

    with BuildPart() as pulley:
        # ── 中间齿部圆柱（简化为实心圆柱，无齿形）──
        Cylinder(
            radius=r_body,
            height=_BELT_WIDTH,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )

        # ── 上法兰（+Z 侧）──
        with Locations(Location((0, 0, _BELT_WIDTH / 2))):
            Cylinder(
                radius=r_flange,
                height=_FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

        # ── 下法兰（-Z 侧）──
        with Locations(Location((0, 0, -_BELT_WIDTH / 2))):
            Cylinder(
                radius=r_flange,
                height=_FLANGE_T,
                align=(Align.CENTER, Align.CENTER, Align.MAX),
            )

        # ── 中心孔（贯穿全高）──
        Cylinder(
            radius=r_bore,
            height=_TOTAL_H + 0.1,   # 略长保证完全穿透
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )

        # ── M3 顶丝孔（侧面，穿过齿部壁）──
        # 孔中心在 XZ 平面，沿 Y 轴方向，Z=0（中心线）
        setscrew_depth = r_body + 1.0   # 从外侧穿入，穿到轴孔处
        with Locations(Location((0, r_body, 0), (90, 0, 0))):
            Cylinder(
                radius=_M3_HOLE_D / 2,
                height=setscrew_depth,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

    return pulley.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    combos = [
        (16, 5.0), (16, 8.0),
        (20, 5.0), (20, 8.0),
        (30, 5.0), (30, 8.0),
        (40, 5.0), (40, 8.0),
    ]
    for teeth, bore in combos:
        part = make_gt2_pulley(teeth, bore)
        slug = f"gt2_pulley_{teeth}t_bore{int(bore)}"
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(
            f"OK: {out_path.name}  "
            f"d={bb.size.X:.1f}x{bb.size.Z:.1f}mm  "
            f"vol={part.volume:.2f} mm3"
        )
