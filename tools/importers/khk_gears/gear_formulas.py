"""Involute spur gear geometry — standard formulas (JIS B 1701 / ISO 53).

All formulas are public domain engineering knowledge.
Source: JIS B 1701-1:1999, KHK Gears technical reference (https://khkgears.net)
License: MIT
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SpurGearDims:
    """Key dimensions of a standard involute spur gear."""
    module: float          # モジュール m (mm)
    num_teeth: int         # 歯数 z
    pressure_angle_deg: float = 20.0

    # --- derived (computed in __post_init__) ---
    pitch_diameter: float = 0.0      # ピッチ円直径 d (mm)
    addendum: float = 0.0            # 歯末の丈 ha (mm)
    dedendum: float = 0.0            # 歯元の丈 hf (mm)
    whole_depth: float = 0.0         # 全歯丈 h (mm)
    outside_diameter: float = 0.0   # 歯先円直径 da (mm)
    root_diameter: float = 0.0       # 歯底円直径 df (mm)
    base_diameter: float = 0.0       # 基礎円直径 db (mm)
    circular_pitch: float = 0.0      # 円周ピッチ p (mm)
    face_width_default: float = 0.0  # 推奨歯幅 b = 8~12m

    def __post_init__(self) -> None:
        m = self.module
        z = self.num_teeth
        alpha = math.radians(self.pressure_angle_deg)

        self.pitch_diameter = m * z
        self.addendum = m                  # ha = 1.00 × m  (standard tooth)
        self.dedendum = 1.25 * m           # hf = 1.25 × m
        self.whole_depth = 2.25 * m
        self.outside_diameter = m * (z + 2)
        self.root_diameter = m * (z - 2.5)
        self.base_diameter = self.pitch_diameter * math.cos(alpha)
        self.circular_pitch = math.pi * m
        self.face_width_default = 10 * m   # typical 8-12×m


def center_distance(m: float, z1: int, z2: int) -> float:
    """Standard center distance between two external gears."""
    return m * (z1 + z2) / 2.0


def gear_ratio(z_driver: int, z_driven: int) -> float:
    return z_driven / z_driver


def min_teeth_no_undercut(pressure_angle_deg: float = 20.0) -> int:
    """Minimum teeth to avoid undercutting at standard addendum."""
    alpha = math.radians(pressure_angle_deg)
    return math.ceil(2 / math.sin(alpha) ** 2)  # = 17 for 20°


if __name__ == "__main__":
    # example: m1 z20 standard spur gear
    g = SpurGearDims(module=1.0, num_teeth=20)
    print(f"m={g.module}  z={g.num_teeth}")
    print(f"  d  = {g.pitch_diameter:.3f} mm")
    print(f"  da = {g.outside_diameter:.3f} mm")
    print(f"  df = {g.root_diameter:.3f} mm")
    print(f"  db = {g.base_diameter:.3f} mm")
    print(f"  h  = {g.whole_depth:.3f} mm")
    print(f"  p  = {g.circular_pitch:.4f} mm")
    print(f"  min teeth (no undercut) = {min_teeth_no_undercut()}")
