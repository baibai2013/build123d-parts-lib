"""QDD 电机转子总成 / Motor Rotor Assembly — outrunner BLDC rotor for QDD joint module.

Compound factory combining rotor shell and 14 arc magnets:
  make_motor_rotor() → Compound

For individual sub-parts see:
  rotor_shell.py — make_rotor_shell()  (thin-wall cup + magnet pockets)
  arc_magnet.py  — make_arc_magnet()   (single NdFeB arc segment)

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC rotor geometry
"""
from __future__ import annotations

from pathlib import Path

from build123d import Compound, Rot, export_step

from build123d_parts_lib.parts.actuators.arc_magnet import make_arc_magnet, n_poles
from build123d_parts_lib.parts.actuators.rotor_shell import make_rotor_shell


def make_motor_rotor() -> Compound:
    """Generate complete rotor: shell + 14 arc magnets equally spaced as a Compound."""
    shell   = make_rotor_shell()
    magnet  = make_arc_magnet()
    magnets = [Rot(0, 0, 360.0 * i / n_poles) * magnet for i in range(n_poles)]
    return Compound(children=[shell] + magnets)


if __name__ == "__main__":
    print("Building QDD motor rotor assembly ...")
    rotor = make_motor_rotor()

    bb = rotor.bounding_box()
    print(f"  BBox : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")

    out_dir = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    export_step(rotor, str(out_dir / "motor_rotor.step"))
    print("  STEP → cache/motor_rotor.step ✓")
