"""QDD 编码器后盖 / Encoder Cover — AS5047P PCB mount and magnet pocket.

Rear cover that holds the AS5047P encoder PCB (Φ20 mm) and positions the
diametrically magnetised disc magnet (Φ6 mm) concentrically over the IC.

Geometry (local Z: motor side=0, outer face=6):
  OD             : Φ30 mm
  Height         : 6 mm
  Magnet pocket  : center Φ6.2 mm, depth 3.5 mm  (blind, opens at z=0)
  PCB mount holes: 3× M2 clearance Ø2.4 mm, PCD 16 mm, 120° spacing
  Outer rim      : C0.5 chamfer both ends

Material: PETG FDM
Key tolerances:
  Magnet pocket Φ6.2 : +0.2/0 mm  (slight clearance for Φ6.0 disc magnet)
  Magnet depth 3.5   : ±0.1 mm    (controls axial air gap to AS5047P IC)
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

magnet_d     =  6.2   # magnet pocket diameter  mm (Φ6 + 0.2 clearance)
magnet_depth =  3.5   # magnet pocket depth  mm (blind from motor-side face z=0)

pcb_hole_d   =  2.4   # M2 clearance hole diameter  mm
pcb_pcd      = 16.0   # PCB mounting holes PCD  mm
pcb_hole_n   =  3     # number of PCB mount holes (AS5047P standard 3-hole)


def make_encoder_cover() -> Part:
    """Generate QDD encoder rear cover.

    生成 QDD 编码器后盖（含磁钢盲孔 + 3× M2 PCB 安装孔）。

    Build order:
    1. Main cylinder (Algebra Mode, z=0~6)
    2. Subtract magnet pocket (Algebra: blind cylinder z=0~3.5)
    3. Subtract 3× M2 PCB holes (Builder Mode PolarLocations through-holes)
    4. Chamfer outer rim both ends
    """
    # Step 1: 主体圆柱 / Main cylinder ─────────────────────────────────────────
    cover: Part = Cylinder(
        radius=cover_od / 2,
        height=cover_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 2: 磁钢盲孔（从 z=0 向上 3.5 mm）/ Magnet pocket (blind, z=0~3.5)
    # Cylinder aligned MIN means z=0→magnet_depth, opening at z=0 (motor side)
    cover = cover - Cylinder(
        radius=magnet_d / 2,
        height=magnet_depth + 0.01,
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
    print("Building QDD encoder cover ...")
    print(f"  OD={cover_od} mm  H={cover_h} mm  "
          f"Magnet pocket Φ{magnet_d}×{magnet_depth}  "
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
