"""QDD 电机前端盖 / Motor Front Endcap — front bearing seat and motor interface.

Closes the motor (stator) front end, holds the MR85ZZ front bearing (Φ8 OD),
and connects to the main housing via 4× M3 screws.

Geometry (local Z: motor side=0, housing side=5):
  OD             : Φ45 mm  (matches housing OD)
  Bearing seat   : Φ8 H7 center bore  (MR85ZZ outer ring press-fit)
  Bolt holes     : 4× M3 clearance Ø3.4 mm, PCD 39 mm, 90° spacing
  Height         : 5 mm

Material: PETG FDM
Key tolerances:
  Bearing seat Φ8 H7  : +0.015/0 mm  (press-fit for MR85ZZ)
  M3 clearance holes  : Ø3.4 mm
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
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
endcap_od       = 45.0   # outer diameter  mm (matches housing)
endcap_h        =  5.0   # height  mm

bearing_seat_d  =  8.0   # MR85ZZ outer diameter  mm (H7 press-fit)
m3_clear_d      =  3.4   # M3 clearance hole diameter  mm
m3_pcd          = 39.0   # M3 bolt-circle diameter  mm
m3_count        =  4     # number of M3 holes


def make_motor_endcap_front() -> Part:
    """Generate QDD motor front endcap.

    生成 QDD 电机前端盖（含 MR85ZZ 轴承座 + 4× M3 连接孔）。
    """
    with BuildPart() as cap:
        # 主体圆柱 / Main cylinder
        Cylinder(
            radius=endcap_od / 2,
            height=endcap_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 轴承座 Φ8 H7（贯通）/ Bearing seat through-hole
        Hole(radius=bearing_seat_d / 2)

        # 4× M3 安装孔（PCD 39 mm，均布 90°）/ 4× M3 clearance holes
        with PolarLocations(radius=m3_pcd / 2, count=m3_count):
            Hole(radius=m3_clear_d / 2)

        # 倒角：轴承座入口 C0.3（引导压入）/ Bearing seat entry chamfer C0.3
        seat_edges = [
            e for e in cap.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - bearing_seat_d / 2) < 0.1
        ]
        if seat_edges:
            chamfer(seat_edges, length=0.3)

    return cap.part


if __name__ == "__main__":
    print("Building QDD motor front endcap ...")
    print(f"  OD={endcap_od} mm  H={endcap_h} mm  "
          f"Bearing seat Φ{bearing_seat_d} H7  "
          f"{m3_count}× M3 clear Φ{m3_clear_d} PCD{m3_pcd}")

    part = make_motor_endcap_front()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, names=["motor_endcap_front"], colors=["slateblue"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 电机前端盖 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP + STL ───────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "motor_endcap_front.step"
    stl_path  = out_dir / "motor_endcap_front.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── motor_endcap_front 尺寸汇总 ─────────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.2f} cm³)")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    assert abs(bb.size.X - endcap_od) < 1.0, f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - endcap_h)  < 0.2, f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox: ✓")
    print("────────────────────────────────────────────────────")
