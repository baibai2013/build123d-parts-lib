"""QDD 转子轴 / Rotor Shaft — precision ground shaft for QDD joint module.

CNC precision-ground shaft connecting the BLDC motor rotor to the harmonic
wave generator cam.  Mates with:
  - wave_generator_cam  (Φ5 H7 bore, DIN 6885 keyway)
  - MR84ZZ front bearing  (Φ4 journal, 3 mm wide, at the +Z / wave-cam end)
  - motor_rotor_shell    (Φ5 press-fit)

Geometry (local Z: rear/encoder end = 0, wave-cam / output end = shaft_len):
  Main shaft   : Φ5 h6, L=42 mm  (lower section)
  Front journal: Φ4 × 3 mm       (MR84ZZ inner bore, at shaft_len end)
  Keyway       : 2×1.0 mm shaft-side, DIN 6885 (+Y dir, z = 2…20 mm)
  Rear bore    : M3 blind hole, Φ3 × 5 mm (encoder magnet, at z=0 end)

Key tolerances:
  Shaft OD Φ5 h6   : 0 / −0.008 mm  (fits wave_cam Φ5 H7)
  Front journal Φ4  : sliding fit with MR84ZZ
  Concentricity     : ≤ 0.01 mm
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    GeomType,
    Part,
    Pos,
    add,
    chamfer,
    export_step,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ──────────────────────────────────────────────────
shaft_od         =  5.0    # h6 — mates with wave_cam Φ5 H7
shaft_len        = 45.0    # total length
shaft_r          = shaft_od / 2   # 2.5 mm

front_journal_d  =  4.0    # MR84ZZ inner bore
front_journal_l  =  3.0    # MR84ZZ bearing width
front_journal_r  = front_journal_d / 2   # 2.0 mm
body_h           = shaft_len - front_journal_l   # 42.0 mm

# ── 键槽（DIN 6885，轴侧，+Y）/ Keyway (shaft side, +Y direction) ─────────────
key_w            = 2.0    # width mm  — same as wave_generator_cam.py
key_shaft_depth  = 1.0    # shaft-side depth mm  (t1 per DIN 6885 for b=2)
key_length       = 18.0   # keyway span — covers wave_cam height (14 mm) + 4 mm margin
key_z_start      = 2.0    # keyway begins 2 mm from rear (z=0) end

# ── 后端 M3 盲孔 / Rear M3 blind hole ─────────────────────────────────────────
rear_bore_d      = 3.0
rear_bore_l      = 5.0

chamfer_l        = 0.3    # C0.3 on shaft ends


def make_rotor_shaft() -> Part:
    """Generate QDD rotor shaft (Φ5 h6 × 45 mm, DIN 6885 keyway, M3 rear bore).

    Build order:
    1. Main body Φ5 × 42 mm + front journal Φ4 × 3 mm (union)
    2. DIN 6885 keyway 2×1.0 mm shaft-side, +Y direction
    3. M3 rear blind hole Φ3 × 5 mm (z=0 face)
    4. Chamfer C0.3 at shaft ends
    """
    # Step 1: 主体 + 轴颈 / Main body + front journal ────────────────────────────
    shaft = Cylinder(
        radius=shaft_r,
        height=body_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shaft = shaft + Pos(0, 0, body_h) * Cylinder(
        radius=front_journal_r,
        height=front_journal_l,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 2: 键槽（+Y 方向，从 OD 向内切 1.0 mm）/ Keyway ─────────────────────
    shaft = shaft - Pos(
        0,
        shaft_r - key_shaft_depth / 2,
        key_z_start + key_length / 2,
    ) * Box(
        key_w,
        key_shaft_depth + 0.1,
        key_length + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # Step 3: 后端 M3 盲孔 / Rear M3 blind hole (z=0 face) ─────────────────────
    shaft = shaft - Cylinder(
        radius=rear_bore_d / 2,
        height=rear_bore_l + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 4: 倒角 / Chamfer C0.3 ──────────────────────────────────────────────
    with BuildPart() as _ch:
        add(shaft)
        rim_edges = [
            e for e in _ch.edges().filter_by(GeomType.CIRCLE)
            if (abs(e.radius - shaft_r) < 0.15 and abs(e.center().Z) < 0.15)
               or (abs(e.radius - front_journal_r) < 0.15
                   and abs(e.center().Z - shaft_len) < 0.15)
        ]
        if rim_edges:
            chamfer(rim_edges, length=chamfer_l)

    return _ch.part


if __name__ == "__main__":
    print("Building QDD rotor shaft ...")
    print(f"  Shaft  : Φ{shaft_od} h6 × {shaft_len} mm")
    print(f"  Journal: Φ{front_journal_d} × {front_journal_l} mm  (MR84ZZ, +Z end)")
    print(f"  Keyway : {key_w} × {key_shaft_depth} mm  (DIN 6885 shaft-side, +Y)")
    print(f"  Rear   : M3 blind hole Φ{rear_bore_d} × {rear_bore_l} mm")

    part = make_rotor_shaft()

    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, names=["rotor_shaft"], colors=["lightgray"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 转子轴 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "rotor_shaft.step"
    export_step(part, str(step_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── rotor_shaft ────────────────────────────────────")
    print(f"  Volume : {vol:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    assert abs(bb.size.X - shaft_od) < 0.5,  f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - shaft_len) < 0.5, f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")
