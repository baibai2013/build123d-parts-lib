"""QDD 弧形磁钢 / Arc Segment Permanent Magnet for QDD outrunner motor.

Factory: make_arc_magnet() → Part
  Single arc-segment NdFeB magnet centered on the +X axis.
  Multiply with PolarLocations × 14 to form the complete 14-pole rotor array.

Geometry (Z=0 at open end, +Z toward closed rotor end):
  inner_r : 20.25 mm  (stator tooth-tip OD/2 + 0.25 mm air gap)
  outer_r : 22.25 mm  (inner_r + t=2 mm, flush with rotor-shell inner wall)
  height  : 10.0 mm   (equal to stator lamination height)
  arc     : ±11.57°   (pole-arc factor 0.9 → 360°/14 × 0.9 ÷ 2)

Purchasing spec (淘宝采购规格):
  类型   : 瓦形/弧形钕铁硼 (NdFeB tile/arc magnet)
  内径   : 40.5 mm  (= 2 × 20.25)
  外径   : 44.5 mm  (= 2 × 22.25)
  高度   : 10 mm
  圆心角 : 23° (≈ 360/14 × 0.9)
  充磁   : 径向充磁，N/S 交替 (radially magnetised, alternating poles)
  牌号   : N35 ~ N45 (N38SH recommended for thermal stability)
  数量   : 14 片 / 套

Method: full annulus ring clipped by two half-space Box subtractions at ±half_angle,
leaving exactly the intended arc sector centred on +X.

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC rotor geometry
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    Cylinder,
    Part,
    Pos,
    Rot,
    export_step,
)

# ── 弧形磁钢尺寸 / Arc magnet dimensions ───────────────────────────────────────
n_poles         = 14                            # number of poles
magnet_inner_r  = 20.25                         # inner radius  mm  (stator r + air gap)
magnet_t        =  2.0                          # radial thickness  mm
magnet_outer_r  = magnet_inner_r + magnet_t     # 22.25 mm (flush with shell inner wall)
magnet_h        = 10.0                          # axial height  mm
arc_factor      =  0.9                          # pole-arc ratio
magnet_half_deg = 180.0 * arc_factor / n_poles  # ≈ 11.57°  (half arc of one pole)

GEOMETRY_INVARIANTS = {
    "n_poles":         n_poles,
    "magnet_inner_r":  magnet_inner_r,
    "magnet_t":        magnet_t,
    "magnet_outer_r":  magnet_outer_r,
    "magnet_h":        magnet_h,
    "arc_factor":      arc_factor,
    "magnet_half_deg": magnet_half_deg,
}


def make_arc_magnet() -> Part:
    """Generate one arc-segment permanent magnet centred on +X axis.

    Method: full annulus ring clipped by two half-space Box subtractions rotated
    to ±half_angle, leaving exactly the intended angular sector.
    """
    clip_size = magnet_outer_r + 5.0   # large enough to cover annulus fully
    clip_h    = magnet_h + 0.2

    # 弧形磁钢全环 / Full annulus ring
    annulus = (
        Cylinder(
            radius=magnet_outer_r + 0.05,
            height=magnet_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=magnet_inner_r,
            height=clip_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # 上裁剪：去除 y > x·tan(+half_angle) 区域
    upper_clip = (
        Rot(0, 0, magnet_half_deg)
        * Pos(0, clip_size / 2, magnet_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )

    # 下裁剪：去除 y < x·tan(−half_angle) 区域
    lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, magnet_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )

    return annulus - upper_clip - lower_clip


if __name__ == "__main__":
    print("Building QDD arc magnet ...")
    print(f"  {n_poles} poles  inner_r={magnet_inner_r} mm  t={magnet_t} mm"
          f"  arc=±{magnet_half_deg:.2f}°")

    magnet = make_arc_magnet()

    bb = magnet.bounding_box()
    print(f"  Volume : {magnet.volume:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")

    assert magnet.volume > 0, "❌ arc_magnet volume ≤ 0"
    assert abs(bb.size.Z - magnet_h) < 0.2, f"magnet Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")

    out_dir = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    export_step(magnet, str(out_dir / "arc_magnet.step"))
    print("  STEP → cache/arc_magnet.step ✓")
