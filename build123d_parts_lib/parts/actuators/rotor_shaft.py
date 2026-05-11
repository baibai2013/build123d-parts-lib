"""QDD 转子轴 / Rotor Shaft — precision ground shaft for QDD joint module.

CNC precision-ground shaft connecting the BLDC motor rotor to the harmonic
wave generator cam.  Mates with:
  - wave_generator_cam  (Φ5 H7 bore, DIN 6885 keyway)
  - MR85ZZ front bearing  (Φ5 inner bore, in motor_endcap_front Φ8 H7 seat)
  - MR85ZZ rear  bearing  (Φ5 inner bore, in encoder_cover Φ8 H7 seat)
  - motor_rotor_shell    (Φ5 press-fit at z=28~40 in assembly)

Geometry (local Z: output/wave-cam end = 0, encoder/rear end = shaft_len):
  Shaft        : Φ5 h6, L=45 mm
  Shoulder     : Φ6 × 1 mm at z=2~3  (台肩, locates wave_generator_cam axially)
  Keyway       : 2×1.0 mm shaft-side, DIN 6885 (+Y dir, z = 3…18 mm)
                 (covers wave_generator_cam at assembly z=3~17)
  Ring groove  : GB/T 894.1, d=4.3 mm, w=0.8 mm, center z=17.5
                 (wave_cam top face at z=17; ring locks cam axially from above)
  Encoder bore : M3 blind hole, Φ3 × 5 mm at z=shaft_len end (encoder magnet)

Assembly bearing positions (in assembly coords, shaft placed at Pos(0,0,0)):
  Front bearing (MR85ZZ): z ≈ 30  in motor_endcap_front Φ8 H7 seat
  Rear  bearing (MR85ZZ): z ≈ 35  in encoder_cover Φ8 H7 seat

Key tolerances:
  Shaft OD Φ5 h6  : 0 / −0.008 mm  (fits wave_cam Φ5 H7, MR85ZZ ID=5)
  Concentricity   : ≤ 0.01 mm
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
shaft_od         =  5.0    # h6 — mates with wave_cam Φ5 H7 and MR85ZZ ID=5
shaft_len        = 45.0    # total length  mm
shaft_r          = shaft_od / 2   # 2.5 mm

# ── 键槽（DIN 6885，轴侧，+Y）/ Keyway (shaft side, +Y direction) ─────────────
key_w            = 2.0    # width mm  — same as wave_generator_cam.py
key_shaft_depth  = 1.0    # shaft-side depth mm  (t1 per DIN 6885 for b=2)
key_length       = 15.0   # keyway span z=3~18, covers wave_cam (z=3~17) + 1mm margin
key_z_start      = 3.0    # keyway begins at shoulder top (z=3)

# ── 台肩 / Shoulder for wave_generator_cam axial location ─────────────────────
shoulder_od = 6.0    # shoulder OD mm  (Φ5→Φ6 step, Δr=0.5mm wall)
shoulder_h  = 1.0    # shoulder height mm  (z=2~3)
shoulder_z  = 2.0    # shoulder z start mm

# ── 卡簧槽（GB/T 894.1, d5mm）/ Retaining ring groove ─────────────────────────
groove_d    = 4.3    # groove bottom diameter mm  (GB/T 894.1: d1=4.3 for d=5)
groove_w    = 0.8    # groove width mm  (GB/T 894.1: b=0.8 for d=5)
groove_z    = 17.5   # groove center z mm  (0.5mm above wave_cam top at z=17)

# ── 编码器端 M3 盲孔 / Encoder-end M3 blind hole (z=shaft_len face) ──────────
encoder_bore_d   = 3.0   # M3 tapped / glue pocket for encoder disc magnet
encoder_bore_l   = 5.0

chamfer_l        = 0.3    # C0.3 on shaft ends


GEOMETRY_INVARIANTS = {
    "shaft_od":        shaft_od,
    "shaft_len":       shaft_len,
    "key_w":           key_w,
    "key_shaft_depth": key_shaft_depth,
    "key_length":      key_length,
    "key_z_start":     key_z_start,
    "shoulder_od":     shoulder_od,
    "shoulder_h":      shoulder_h,
    "groove_d":        groove_d,
    "groove_w":        groove_w,
    "groove_z":        groove_z,
    "encoder_bore_d":  encoder_bore_d,
    "encoder_bore_l":  encoder_bore_l,
}


def make_rotor_shaft() -> Part:
    """Generate QDD rotor shaft (Φ5 h6 × 45 mm, shoulder, groove, DIN 6885 keyway).

    Build order:
    1.  Uniform Φ5 h6 × 45 mm shaft body
    1b. Shoulder Φ6 × 1 mm at z=2~3  (wave_cam axial stop)
    2.  DIN 6885 keyway 2×1.0 mm shaft-side, +Y direction (z=3~18)
    3.  M3 encoder blind hole Φ3 × 5 mm at encoder end (z=shaft_len face)
    3b. GB/T 894.1 retaining ring groove d=4.3 mm, w=0.8 mm at z=17.5
    4.  Chamfer C0.3 at both shaft ends
    """
    # Step 1: 均匀 Φ5 轴体 / Uniform Φ5 shaft body ──────────────────────────────
    shaft = Cylinder(
        radius=shaft_r,
        height=shaft_len,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 1b: 台肩（Φ6×1mm, z=2~3）/ Shoulder ring for cam axial location ──────
    shaft = shaft + Pos(0, 0, shoulder_z) * Cylinder(
        radius=shoulder_od / 2,
        height=shoulder_h,
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

    # Step 3: 编码器端 M3 盲孔（z=shaft_len 面向下）/ Encoder M3 blind hole ──────
    shaft = shaft - Pos(0, 0, shaft_len - encoder_bore_l) * Cylinder(
        radius=encoder_bore_d / 2,
        height=encoder_bore_l + 0.1,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 3b: 卡簧槽（GB/T 894.1, d5mm, z=17.5）/ Retaining ring groove ─────────
    groove_ring = (
        Cylinder(
            radius=shaft_r + 0.1,
            height=groove_w,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=groove_d / 2,
            height=groove_w + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )
    shaft = shaft - Pos(0, 0, groove_z - groove_w / 2) * groove_ring

    # Step 4: 倒角两端 / Chamfer C0.3 both ends ────────────────────────────────
    with BuildPart() as _ch:
        add(shaft)
        rim_edges = [
            e for e in _ch.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - shaft_r) < 0.15
               and (abs(e.center().Z) < 0.15 or abs(e.center().Z - shaft_len) < 0.15)
        ]
        if rim_edges:
            chamfer(rim_edges, length=chamfer_l)

    return _ch.part


if __name__ == "__main__":
    print("Building QDD rotor shaft (Φ5 h6, shoulder, GB/T894.1 groove, DIN6885 keyway)...")
    print(f"  Shaft    : Φ{shaft_od} h6 × {shaft_len} mm")
    print(f"  Shoulder : Φ{shoulder_od} × {shoulder_h} mm  z={shoulder_z}~{shoulder_z+shoulder_h}")
    print(f"  Keyway   : {key_w} × {key_shaft_depth} mm  (DIN 6885 +Y, z={key_z_start}~{key_z_start+key_length})")
    print(f"  Groove   : d={groove_d} mm, w={groove_w} mm  (GB/T 894.1, z={groove_z})")
    print(f"  Encoder  : M3 blind hole Φ{encoder_bore_d} × {encoder_bore_l} mm at z={shaft_len} end")

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
    assert abs(bb.size.X - shoulder_od) < 0.5, f"X 偏差: {bb.size.X:.2f} (exp ≈ {shoulder_od})"
    assert abs(bb.size.Z - shaft_len) < 0.5,   f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")
