"""QDD 波发生器凸轮 / Wave Generator Cam — elliptical cam for harmonic drive.

Bearing-free design: SLA resin cam slides directly on TPU 95A flex spline
inner bore. Long axis ≈ flex_cup_inner_bore (26.85 mm) + slight preload;
short axis slightly smaller, allowing flex cup to retract at disengagement.

Geometry (local Z: bottom=0, top=cam_h):
  XY cross-section : ellipse, long-axis 27 mm (+X), short-axis 26.5 mm (+Y)
  Center bore      : Φ5 H7  (mates with motor rotor shaft, h6 fit)
  Keyway           : 2×1.2 mm hub-side (DIN 6885, +Y direction)
  Height           : 14 mm

Flex spline interface:
  Flex cup inner bore (undeformed) : 26.85 mm (= 2 × 13.425 mm)
  Cam long axis Φ27.0 → δ ≈ +0.075 mm radial preload at engagement zone
  Cam short axis Φ26.5 → δ ≈ −0.175 mm clearance at disengagement zone
  Lubricate with PTFE grease before assembly

Material: SLA resin (primary) / PETG FDM (fallback)
Key tolerances:
  Center bore Φ5 H7 : +0.010/0 mm
  Ellipse accuracy  : ±0.1 mm (drives flex-spline deformation uniformity)
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Ellipse,
    GeomType,
    Part,
    Plane,
    Pos,
    add,
    chamfer,
    export_step,
    export_stl,
    extrude,
)
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸 / Key dimensions ──────────────────────────────────────────────────
# Flex cup inner bore = 2 × (root_r − flex_wall_t) = 2 × 13.425 = 26.85 mm
# Long axis ≈ inner bore + 0.15 mm preload; short axis < inner bore (clearance).
wave_gen_d_long  = 27.0   # ellipse long-axis diameter  mm (+X)  ← presses on flex cup
wave_gen_d_short = 26.5   # ellipse short-axis diameter mm (+Y)  ← flex cup retracts
cam_h            = 14.0   # cam height  mm

bore_d           =  5.0   # center bore diameter (H7)  mm
bore_r           =  bore_d / 2   # 2.5 mm

# ── 键槽参数（DIN 6885，轮毂侧）/ Keyway dimensions (hub side) ─────────────────
key_w            =  2.0   # keyway width  mm
key_hub_depth    =  1.2   # hub-side keyway depth  mm (+Y direction from bore surface)


def make_wave_generator_cam() -> Part:
    """Generate QDD wave generator elliptical cam.

    生成 QDD 波发生器椭圆凸轮（含中心孔 + 键槽）。

    Build order:
    1. Elliptical extrude (solid cam body)
    2. Subtract center bore Φ5 H7
    3. Subtract keyway slot (2×1.2 mm, hub side, +Y direction)
    4. Chamfer bore entry (C0.3) to ease bearing press-fit
    """
    # Step 1: 椭圆凸轮主体 / Elliptical cam body ────────────────────────────────
    with BuildPart() as _cam:
        with BuildSketch(Plane.XY):
            Ellipse(
                x_radius=wave_gen_d_long  / 2,
                y_radius=wave_gen_d_short / 2,
            )
        extrude(amount=cam_h)
    cam: Part = _cam.part

    # Step 2: 中心孔 Φ5 H7 / Center bore ─────────────────────────────────────
    cam = cam - Cylinder(
        radius=bore_r,
        height=cam_h + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Step 3: 键槽（轮毂侧，+Y 方向）/ Keyway (hub side, +Y) ──────────────────
    # Keyway center offset from bore axis = bore_r + key_hub_depth/2
    cam = cam - Pos(0, bore_r + key_hub_depth / 2, cam_h / 2) * Box(
        key_w,
        key_hub_depth + 0.1,   # slight overcut for clean Boolean
        cam_h + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )

    # Step 4: 倒角 — 中心孔入口 C0.3 / Bore entry chamfer C0.3 ─────────────────
    with BuildPart() as _ch:
        add(cam)
        bore_entry = [
            e for e in _ch.edges().filter_by(GeomType.CIRCLE)
            if abs(e.radius - bore_r) < 0.1 and
               (abs(e.center().Z) < 0.15 or abs(e.center().Z - cam_h) < 0.15)
        ]
        if bore_entry:
            chamfer(bore_entry, length=0.3)

    return _ch.part


GEOMETRY_INVARIANTS = {
    "wave_gen_d_long":  wave_gen_d_long,
    "wave_gen_d_short": wave_gen_d_short,
    "cam_h":            cam_h,
    "bore_d":           bore_d,
    "key_w":            key_w,
    "key_hub_depth":    key_hub_depth,
    # flex spline interface
    "flex_cup_inner_bore": 26.85,  # mm — from flex_spline.py root_r − wall_t geometry
    "long_axis_delta":  (wave_gen_d_long  - 26.85) / 2,  # +0.075 mm preload
    "short_axis_delta": (wave_gen_d_short - 26.85) / 2,  # −0.175 mm clearance
}


if __name__ == "__main__":
    print("Building QDD wave generator cam (bearing-free, direct TPU sliding)...")
    print(f"  Ellipse: {wave_gen_d_long} × {wave_gen_d_short} mm  "
          f"(long × short axis, flex cup inner bore = 26.85 mm)")
    print(f"  Bore   : Φ{bore_d} H7  Keyway: {key_w}×{key_hub_depth} mm  "
          f"Height: {cam_h} mm")

    part = make_wave_generator_cam()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part, names=["wave_generator_cam"], colors=["goldenrod"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: 波发生器凸轮 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP + STL ───────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "wave_generator_cam.step"
    stl_path  = out_dir / "wave_generator_cam.stl"

    export_step(part, str(step_path))
    export_stl(part, str(stl_path))

    vol = part.volume
    bb  = part.bounding_box()
    print(f"\n── wave_generator_cam 尺寸汇总 ─────────────────────")
    print(f"  Volume : {vol:.1f} mm³  ({vol / 1000:.2f} cm³)")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    print(f"  STL    : {stl_path}")
    assert part.is_valid, "❌ BRep validity FAILED"
    assert abs(bb.size.X - wave_gen_d_long)  < 0.15, f"X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Y - wave_gen_d_short) < 0.15, f"Y 偏差: {bb.size.Y:.2f}"
    assert abs(bb.size.Z - cam_h)            < 0.1,  f"Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox: ✓")
    print("────────────────────────────────────────────────────")
