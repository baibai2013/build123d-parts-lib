"""QDD 电机控制器 PCB / Motor Controller PCB — FOC driver board for QDD joint module.

Simplified engineering model: circular FR4 PCB + surface-mount component placeholders.

Layout (outrunner FOC driver, single-board):
  PCB board      : Φ40 mm × 1.6 mm  (fits inside Φ45 housing)
  MOSFETs        : 6 × TO-252 package (3-phase full H-bridge), r=15 mm ring
  Gate drivers   : 3 × SOIC-8,  r=12 mm, between MOSFET pairs
  MCU            : 1 × QFP-64 (10×10 mm, e.g. STM32G4), center
  Filter caps    : 2 × Φ6×7 mm electrolytic, r=11 mm, 180° apart
  Phase connectors : 3 × JST-PH 3-pin, r=18 mm, 120° apart (motor phase wires)
  Encoder connector : 1 × JST-ZH 5-pin, r=16 mm, 270°

Geometry (local Z: bottom face = 0, top component face = up):
  Origin: PCB center, z=0 at bottom solder face.
  All components mount on top face (z=pcb_t = 1.6 mm).

Axial position in assembly: z=41 mm (just above encoder cover).

License: Apache-2.0
Source: project-specific design, QDD joint FOC driver layout
"""
from __future__ import annotations

import math
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Part,
    Pos,
    Rot,
    export_step,
)

# ── PCB 尺寸 / PCB dimensions ─────────────────────────────────────────────────
pcb_d   = 40.0   # board diameter  mm
pcb_t   =  1.6   # FR4 thickness   mm

# ── 元件封装尺寸 / Component package dimensions (LWH) ─────────────────────────
mosfet_l, mosfet_w, mosfet_h_pkg   = 6.0, 5.0, 1.0    # TO-252 footprint
gate_drv_l, gate_drv_w, gate_drv_h = 5.0, 4.0, 1.2    # SOIC-8
mcu_l, mcu_w, mcu_h_pkg            = 10.0, 10.0, 1.2  # QFP-64
cap_d, cap_h_pkg                   = 6.0, 7.0          # electrolytic cap
phase_conn_l, phase_conn_w, phase_conn_h = 8.0, 5.0, 5.0   # JST-PH 3-pin
enc_conn_l,   enc_conn_w,   enc_conn_h   = 10.0, 3.5, 3.5  # JST-ZH 5-pin

# ── 布局半径 / Placement radii ────────────────────────────────────────────────
r_mosfet     = 15.0   # mm from axis
r_gate_drv   = 12.0
r_cap        = 11.0
r_phase_conn = 18.0
r_enc_conn   = 15.0

g = {
    "pcb_d":      pcb_d,
    "pcb_t":      pcb_t,
    "n_mosfets":  6,
    "n_phases":   3,
}

# GEOMETRY_INVARIANTS 是约束的唯一真相 / single source of truth for invariants.
GEOMETRY_INVARIANTS = [
    ("MOSFET 数 = 2 × 相数（每相半桥）/ n_mosfets == 2 * n_phases",
     lambda g: g["n_mosfets"] == 2 * g["n_phases"]),
    ("三相驱动 / 3-phase drive",
     lambda g: g["n_phases"] == 3),
    ("板厚 < 板径 / board thinner than its diameter",
     lambda g: g["pcb_t"] < g["pcb_d"]),
    ("板尺寸为正 / board dims positive",
     lambda g: g["pcb_d"] > 0 and g["pcb_t"] > 0),
]


def _assert_geometry_invariants(g: dict) -> None:
    """Assert all geometry invariants; fail immediately on violation.
    断言所有几何不变式，违反时立即报错（不吞异常）。"""
    for desc, test in GEOMETRY_INVARIANTS:
        assert test(g), f"Invariant FAIL: {desc}\n  g={g}"


_assert_geometry_invariants(g)


def make_motor_controller() -> Compound:
    """Generate FOC motor controller PCB with component placeholders.

    Returns Compound with PCB board + all surface-mount component proxies.
    Origin: PCB center, z=0 at bottom face.
    """
    parts: list = []

    # ── PCB board ─────────────────────────────────────────────────────────────
    pcb = Cylinder(
        radius=pcb_d / 2, height=pcb_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    parts.append(pcb)

    # ── 6 × MOSFET (TO-252): evenly spaced at r=15 mm ────────────────────────
    for k in range(6):
        angle = k * 60.0
        mosfet = (
            Rot(0, 0, angle)
            * Pos(r_mosfet, 0, pcb_t)
            * Box(mosfet_l, mosfet_w, mosfet_h_pkg,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(mosfet)

    # ── 3 × Gate driver (SOIC-8): between MOSFET pairs at r=12 mm ────────────
    for k in range(3):
        angle = k * 120.0 + 30.0   # offset 30° from MOSFET angles
        gate_drv = (
            Rot(0, 0, angle)
            * Pos(r_gate_drv, 0, pcb_t)
            * Box(gate_drv_l, gate_drv_w, gate_drv_h,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(gate_drv)

    # ── MCU (QFP-64): centered on PCB ────────────────────────────────────────
    mcu = Pos(0, 0, pcb_t) * Box(
        mcu_l, mcu_w, mcu_h_pkg,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    parts.append(mcu)

    # ── 2 × Filter capacitor: r=11 mm, 180° apart ────────────────────────────
    for angle in (90.0, 270.0):
        cap = (
            Rot(0, 0, angle)
            * Pos(r_cap, 0, pcb_t)
            * Cylinder(cap_d / 2, cap_h_pkg,
                       align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(cap)

    # ── 3 × Phase connector (JST-PH 3-pin): r=18 mm, 120° ───────────────────
    for k in range(3):
        angle = k * 120.0
        conn = (
            Rot(0, 0, angle)
            * Pos(r_phase_conn, 0, pcb_t)
            * Box(phase_conn_l, phase_conn_w, phase_conn_h,
                  align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(conn)

    # ── 1 × Encoder connector (JST-ZH 5-pin): r=15 mm at 270° ───────────────
    enc_conn = (
        Rot(0, 0, 270.0)
        * Pos(r_enc_conn, 0, pcb_t)
        * Box(enc_conn_l, enc_conn_w, enc_conn_h,
              align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    parts.append(enc_conn)

    return Compound(children=parts)


if __name__ == "__main__":
    from ocp_vscode import Camera, show
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports

    print("Building QDD motor controller PCB ...")
    board = make_motor_controller()

    # ── OCP 预览 ──────────────────────────────────────────────────────────────
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(board, names=["motor_controller"], colors=["darkgreen"],
             reset_camera=Camera.TOP)
        print("OCP Viewer: 控制器 PCB ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # ── 导出 STEP ─────────────────────────────────────────────────────────────
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "motor_controller.step"
    export_step(board, str(step_path))

    bb  = board.bounding_box()
    vol = board.volume
    print(f"\n── motor_controller 尺寸汇总 ────────────────────────")
    print(f"  Volume : {vol:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  STEP   : {step_path}")
    assert vol > 0, "❌ volume ≤ 0"
    assert abs(bb.size.X - pcb_d) < 4.0, f"X 偏差: {bb.size.X:.2f}"
    print("  BRep + BBox ✓")
    print("────────────────────────────────────────────────────")
