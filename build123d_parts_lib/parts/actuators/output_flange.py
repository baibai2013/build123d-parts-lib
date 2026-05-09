"""QDD 输出法兰 / Output Flange — torque output interface for flex spline.

Connects to the open (gear) end of the flex spline and transmits harmonic
drive output torque to the external robot link.

Geometry (local Z: flex-spline side=0, external side=8):
  OD             : Φ40 mm
  Center bore    : Φ12 mm through  (clearance for 7001C inner ring / shaft)
  Bolt circle    : 6× M2 clearance Ø2.4 mm, PCD 34 mm, 60° spacing
  Height         : 8 mm

Material: PETG FDM
Key tolerances:
  M2 clearance holes : Ø2.4 mm (M2 nominal Ø2.0 + 0.4 clearance)
  Center bore        : Ø12 mm clearance (7001C inner ID = 12 mm)
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Axis,
    BuildPart,
    Cylinder,
    GeomType,
    Hole,
    Part,
    PolarLocations,
    chamfer,
    export_step,
    export_stl,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ──────────────────────────────────────────────────
flange_od     = 40.0   # outer diameter  mm
flange_h      =  8.0   # height  mm

center_bore_d = 12.0   # center bore diameter  mm (7001C inner ring clearance)
m2_clear_d    =  2.4   # M2 clearance hole diameter  mm
m2_pcd        = 34.0   # M2 bolt-circle diameter  mm
m2_count      =  6     # number of M2 holes


def make_output_flange() -> Part:
    """Generate QDD output flange.

    生成 QDD 输出法兰（含中心孔 + 6× M2 安装孔）。
    """
    with BuildPart() as flange:
        # 主体圆柱 / Main cylinder
        Cylinder(
            radius=flange_od / 2,
            height=flange_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 中心孔 Φ12（贯通）/ Center bore through-hole
        Hole(radius=center_bore_d / 2)

        # 6× M2 安装孔（PCD 34 mm，均布 60°）/ 6× M2 clearance holes
        with PolarLocations(radius=m2_pcd / 2, count=m2_count):
            Hole(radius=m2_clear_d / 2)

        # 倒角：中心孔两端 C0.5，外圆两端 C0.5 / Chamfers on bore and rim
        bore_edges = [
            e for e in flange.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - center_bore_d / 2) < 0.1
        ]
        if bore_edges:
            chamfer(bore_edges, length=0.5)

        rim_edges = [
            e for e in flange.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - flange_od / 2) < 0.2 and
               (abs(e.center().Z) < 0.15 or abs(e.center().Z - flange_h) < 0.15)
        ]
        if rim_edges:
            chamfer(rim_edges, length=0.5)

    return flange.part


if __name__ == "__main__":
    print("Building QDD output flange ...")
    print(f"  OD={flange_od} mm  H={flange_h} mm  "
          f"Center bore Φ{center_bore_d}  "
          f"{m2_count}× M2 clear Φ{m2_clear_d} PCD{m2_pcd}")

    part = make_output_flange()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, names=["output_flange"], colors=["mediumseagreen"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 输出法兰 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP + STL ───────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "output_flange.step"
    stl_path  = out_dir / "output_flange.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── output_flange 尺寸汇总 ──────────────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.2f} cm³)")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    assert abs(bb.size.X - flange_od) < 1.0, f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - flange_h)  < 0.2, f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox: ✓")
    print("────────────────────────────────────────────────────")
