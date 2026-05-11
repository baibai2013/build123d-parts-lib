"""QDD 编码器后盖 / Encoder Cover — rear MR85ZZ bearing seat + AS5047P PCB mount.

Rear cover that:
  ① holds the MR85ZZ rotor-shaft bearing (rear support for Φ5 shaft)
  ② mounts the AS5047P encoder PCB (Φ20 mm)
  ③ provides shaft-tip clearance for encoder disc magnet (glued to shaft M3 bore)

Geometry (local Z: motor side=0, outer face=6):
  OD             : Φ30 mm
  Height         : 6 mm
  Bearing seat   : Φ8 H7, depth 3 mm  (MR85ZZ outer ring press-fit, opens at z=0)
  Shaft clearance: Φ5.5 × 3 mm  (z=3~6, shaft tip + Φ5 magnet disc clearance)
  PCB mount holes: 3× M2 clearance Ø2.4 mm, PCD 16 mm, 120° spacing
  Outer rim      : C0.5 chamfer both ends

Assembly note:
  Encoder disc magnet (Φ5×2 mm diametrically magnetised) is attached to the
  shaft tip (z=45 in shaft local coords) with cyanoacrylate or M3×4 screw.
  Shaft Φ5 passes through MR85ZZ inner bore, magnet floats in Φ5.5 clearance
  zone, AS5047P IC senses through the 3 mm cover wall.

Material: PETG FDM
Key tolerances:
  Bearing seat Φ8 H7 : +0.015/0 mm  (press-fit for MR85ZZ OD=8 mm)
  Shaft clearance Φ5.5 : ±0.1 mm
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    BuildPart,
    Cylinder,
    GeomType,
    Hole,
    Part,
    Pos,
    PolarLocations,
    chamfer,
    export_step,
    export_stl,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ──────────────────────────────────────────────────
cover_od     = 30.0   # outer diameter  mm
cover_h      =  6.0   # height  mm

# 后轴承座（MR85ZZ 压配）/ Rear bearing seat (MR85ZZ press-fit)
bearing_seat_d = 8.0   # MR85ZZ outer diameter  mm
bearing_seat_h = 3.0   # bearing seat depth from motor-side face  mm

# 轴颈间隙 / Shaft clearance above bearing seat
shaft_clear_d  = 5.5   # mm — Φ5 shaft + disc magnet clearance
shaft_clear_h  = cover_h - bearing_seat_h   # 3.0 mm

pcb_hole_d   =  2.4   # M2 clearance hole diameter  mm
pcb_pcd      = 16.0   # PCB mounting holes PCD  mm
pcb_hole_n   =  3     # number of PCB mount holes (AS5047P standard 3-hole)


GEOMETRY_INVARIANTS = {
    "cover_od":         cover_od,
    "cover_h":          cover_h,
    "bearing_seat_d":   bearing_seat_d,
    "bearing_seat_h":   bearing_seat_h,
    "shaft_clear_d":    shaft_clear_d,
    "pcb_hole_d":       pcb_hole_d,
    "pcb_pcd":          pcb_pcd,
}


def make_encoder_cover() -> Part:
    """Generate QDD encoder rear cover.

    生成 QDD 编码器后盖（含 MR85ZZ 后轴承座 + 轴颈间隙 + 3× M2 PCB 安装孔）。

    Build order:
    1. Main cylinder (Algebra Mode, z=0~6)
    2. Bearing seat Φ8 H7 × 3 mm (opens at z=0, motor side)
    3. Shaft clearance Φ5.5 × 3 mm (z=3~6, shaft tip + magnet clearance)
    4. Subtract 3× M2 PCB holes
    5. Chamfer outer rim both ends
    """
    # Step 1: 主体圆柱 / Main cylinder ─────────────────────────────────────────
    cover: Part = Cylinder(
        radius=cover_od / 2,
        height=cover_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 2: 轴承座 Φ8 H7 × 3 mm / Bearing seat (opens at motor-side face z=0)
    cover = cover - Cylinder(
        radius=bearing_seat_d / 2,
        height=bearing_seat_h + 0.01,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 3: 轴颈间隙 Φ5.5 × 3 mm / Shaft-tip clearance (z=3~6)
    cover = cover - Pos(0, 0, bearing_seat_h) * Cylinder(
        radius=shaft_clear_d / 2,
        height=shaft_clear_h + 0.01,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 3: 3× M2 PCB 安装孔（贯通）/ 3× M2 through-holes via BuildPart ──────
    # BuildPart is used to leverage PolarLocations + Hole() API.
    # Result is re-fused with the Algebra Mode part via subtraction.
    angle_step = 360 / pcb_hole_n
    for k in range(pcb_hole_n):
        ang = math.radians(k * angle_step)
        cx  = (pcb_pcd / 2) * math.cos(ang)
        cy  = (pcb_pcd / 2) * math.sin(ang)
        cover = cover - Pos(cx, cy, 0) * Cylinder(
            radius=pcb_hole_d / 2,
            height=cover_h + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

    # Step 4: 倒角 外圆两端 C0.5 / Outer rim chamfer C0.5 both ends ─────────────
    with BuildPart() as _ch:
        from build123d import add
        add(cover)
        rim_edges = [
            e for e in _ch.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - cover_od / 2) < 0.2
        ]
        if rim_edges:
            chamfer(rim_edges, length=0.5)

    return _ch.part


if __name__ == "__main__":
    print("Building QDD encoder cover (MR85ZZ rear bearing seat) ...")
    print(f"  OD={cover_od} mm  H={cover_h} mm  "
          f"Bearing Φ{bearing_seat_d}×{bearing_seat_h}mm  "
          f"Shaft clear Φ{shaft_clear_d}×{shaft_clear_h}mm  "
          f"{pcb_hole_n}× M2 clear Φ{pcb_hole_d} PCD{pcb_pcd}")

    part = make_encoder_cover()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, names=["encoder_cover"], colors=["lightgray"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 编码器后盖 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP + STL ───────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "encoder_cover.step"
    stl_path  = out_dir / "encoder_cover.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── encoder_cover 尺寸汇总 ──────────────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.2f} cm³)")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    assert abs(bb.size.X - cover_od) < 1.0, f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - cover_h)  < 0.2, f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox: ✓")
    print("────────────────────────────────────────────────────")
