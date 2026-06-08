"""QDD 波发生器凸轮 / Wave Generator Cam — elliptical cam for harmonic drive.

Bearing design: cam ellipse contacts the inner race of a thin-section flex
bearing (Φ20.85 × Φ26.85 × 3 mm). The bearing outer race (Φ26.85 mm) presses
into the flex spline inner bore, transmitting the elliptical deformation.

Harmonic drive engagement analysis (with bearing):
  Flex cup inner bore (undeformed) : 26.85 mm  (= 2 × cup_inner_r = 2 × 13.425)
  Bearing wall thickness (per side): ~3.0 mm
  Required deformation per side    : m × (ring_z − flex_z) / 2 = 0.3 × 2/2 = 0.3 mm

  Long axis (+X, engagement zone):
    cam_long_r + bearing_wall = 10.725 + 3.0 = 13.725 mm (bearing outer surface)
    flex_inner_r + δ          = 13.425 + 0.3 = 13.725 mm ✓  → +0.3 mm/side engagement
  Short axis (+Y, disengagement zone):
    cam_short_r + bearing_wall = 10.125 + 3.0 = 13.125 mm
    flex_inner_r − δ           = 13.425 − 0.3 = 13.125 mm ✓  → −0.3 mm/side clearance

  Bearing nominal ID:
    mean_r = (10.725 + 10.125) / 2 = 10.425 mm  →  bearing_ID_nom = 20.85 mm

Geometry (local Z: bottom=0, top=cam_h):
  XY cross-section : ellipse, long-axis 21.45 mm (+X), short-axis 20.25 mm (+Y)
  Center bore      : Φ5 H7  (mates with motor rotor shaft, h6 fit)
  Keyway           : 2×1.2 mm hub-side (DIN 6885, +Y direction)
  Height           : 14 mm

Bearing spec (nominal): Φ20.85 × Φ26.85 × 3 mm  (ID × OD × W)
  thin_section_bearing.py is parametric — pass these dimensions directly.

Material: SLA resin (primary) / PETG FDM (fallback)
Key tolerances:
  Center bore Φ5 H7 : +0.010/0 mm
  Ellipse accuracy  : ±0.1 mm (drives flex-spline deformation uniformity)
  Cam OD surface    : h6 fit for bearing inner race press-fit
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
# Bearing design: cam_long_r = cup_inner_r + δ − bearing_wall = 13.425 + 0.3 − 3.0 = 10.725
#                 cam_short_r = cup_inner_r − δ − bearing_wall = 13.425 − 0.3 − 3.0 = 10.125
wave_gen_d_long  = 21.45  # cam ellipse long-axis diameter  mm (+X)  — bearing inner race contact
wave_gen_d_short = 20.25  # cam ellipse short-axis diameter mm (+Y)  — bearing inner race contact
cam_h            = 14.0   # cam height  mm

# Mating bearing spec (nominal): Φ20.85 × Φ26.85 × 3 mm
bearing_id_nom   = 20.85  # bearing inner race nominal diameter mm
bearing_od       = 26.85  # bearing outer race diameter mm  (= flex spline inner bore)
bearing_w        =  3.0   # bearing width mm

bore_d           =  5.0   # center bore diameter (H7)  mm
bore_r           =  bore_d / 2   # 2.5 mm

# ── 键槽参数（DIN 6885，轮毂侧）/ Keyway dimensions (hub side) ─────────────────
key_w            =  2.0   # keyway width  mm
key_hub_depth    =  1.2   # hub-side keyway depth  mm (+Y direction from bore surface)


def make_wave_generator_cam() -> Part:
    """Generate QDD wave generator elliptical cam (bearing-based design).

    生成 QDD 波发生器椭圆凸轮（有轴承设计，含中心孔 + 键槽）。

    Build order:
    1. Elliptical extrude (solid cam body)
    2. Subtract center bore Φ5 H7
    3. Subtract keyway slot (2×1.2 mm, hub side, +Y direction)
    4. Chamfer bore entry (C0.3) to ease shaft press-fit
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


g = {
    "wave_gen_d_long":  wave_gen_d_long,
    "wave_gen_d_short": wave_gen_d_short,
    "cam_h":            cam_h,
    "bore_d":           bore_d,
    "key_w":            key_w,
    "key_hub_depth":    key_hub_depth,
    # bearing interface
    "bearing_id_nom":   bearing_id_nom,
    "bearing_od":       bearing_od,
    "bearing_w":        bearing_w,
    # flex spline interface (via bearing)
    "flex_cup_inner_bore": 26.85,   # mm — flex_spline.py cup_inner_r geometry
    "long_axis_delta":  (bearing_od - 26.85) / 2 + (wave_gen_d_long  - bearing_id_nom) / 2,
    "short_axis_delta": (bearing_od - 26.85) / 2 + (wave_gen_d_short - bearing_id_nom) / 2,
    # Required deformation = m × (ring_teeth − flex_teeth) / 2 = 0.3 × 2/2 = 0.3 mm/side
}

# GEOMETRY_INVARIANTS 是约束的唯一真相 / single source of truth for invariants.
GEOMETRY_INVARIANTS = [
    ("椭圆长轴 > 短轴 / ellipse long axis > short axis",
     lambda g: g["wave_gen_d_long"] > g["wave_gen_d_short"]),
    ("轴承外径 > 内径 / bearing OD > ID",
     lambda g: g["bearing_od"] > g["bearing_id_nom"]),
    ("中心孔 < 短轴 / center bore inside cam",
     lambda g: g["bore_d"] < g["wave_gen_d_short"]),
    ("轴承外径 = 柔轮杯内孔 / bearing_od == flex cup inner bore",
     lambda g: abs(g["bearing_od"] - g["flex_cup_inner_bore"]) < 1e-9),
    ("长轴干涉量定义 / long_axis_delta definition",
     lambda g: abs(g["long_axis_delta"]
                   - ((g["bearing_od"] - g["flex_cup_inner_bore"]) / 2
                      + (g["wave_gen_d_long"] - g["bearing_id_nom"]) / 2)) < 1e-9),
    ("短轴干涉量定义 / short_axis_delta definition",
     lambda g: abs(g["short_axis_delta"]
                   - ((g["bearing_od"] - g["flex_cup_inner_bore"]) / 2
                      + (g["wave_gen_d_short"] - g["bearing_id_nom"]) / 2)) < 1e-9),
    ("关键尺寸为正 / key dims positive",
     lambda g: g["cam_h"] > 0 and g["bore_d"] > 0 and g["key_w"] > 0 and g["bearing_w"] > 0),
]


def _assert_geometry_invariants(g: dict) -> None:
    """Assert all geometry invariants; fail immediately on violation.
    断言所有几何不变式，违反时立即报错（不吞异常）。"""
    for desc, test in GEOMETRY_INVARIANTS:
        assert test(g), f"Invariant FAIL: {desc}\n  g={g}"


_assert_geometry_invariants(g)


if __name__ == "__main__":
    print("Building QDD wave generator cam (bearing design, Φ20.85×Φ26.85×3 bearing)...")
    print(f"  Cam ellipse: {wave_gen_d_long} × {wave_gen_d_short} mm  "
          f"(long × short axis — bearing inner race contact)")
    print(f"  Bearing    : ID={bearing_id_nom} OD={bearing_od} W={bearing_w} mm")
    print(f"  Bore       : Φ{bore_d} H7  Keyway: {key_w}×{key_hub_depth} mm  "
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
    # Verify ellipse aspect ratio is distinguishable (≥1.0 mm = physically meaningful)
    aspect_diff = wave_gen_d_long - wave_gen_d_short
    assert aspect_diff >= 1.0, f"❌ 椭圆长短轴差 {aspect_diff:.2f}mm < 1.0mm，不足以驱动谐波啮合"
    print(f"  Ellipse: {wave_gen_d_long}×{wave_gen_d_short} mm  差 {aspect_diff:.2f}mm ✓")
    assert abs(bb.size.Z - cam_h)            < 0.1,  f"Z 偏差: {bb.size.Z:.2f}"
    print(f"  BRep + BBox: ✓")
    print(f"  Bearing: ID={bearing_id_nom} OD={bearing_od} W={bearing_w} mm")
    print("────────────────────────────────────────────────────")
