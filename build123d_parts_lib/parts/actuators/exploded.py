"""QDD 关节模组爆炸展开动画 / QDD Joint Module Exploded-View Animation.

16-second loop in OCP CAD Viewer:
  0 →  8 s  — staged explosion (motor-end parts first, output-end last)
  8 → 12 s  — hold exploded view
  12 → 14 s — reassemble
  14 → 16 s — hold assembled

Explosion order (top → bottom, inner → outer):
  t=0-1 : motor_controller          → +65 mm  (topmost PCB)
  t=1-2 : encoder_cover + mr85zz_rear  → +55 mm  (rear bearing exits with cover)
  t=2-3 : motor_endcap + mr85zz_front  → +42 mm  (front bearing exits with endcap)
  t=3-4 : rotor_shell + ×14 magnets → +30 mm  (outer rotor shell)
  t=4-5 : stator_winding      → +20 mm  (winding co-located with stator)
  t=4-5 : motor_stator        → +15 mm
  t=4-5 : wave_cam            → +12 mm  (bearing-free SLA cam, direct TPU contact)
  t=5-6 : flex_spline         → +8  mm
  t=6-7 : bearing_7001c       → -18 mm  (downward, output side)
  t=7-8 : output_flange       → -32 mm  (bottommost)

  housing     — fixed reference frame (no track)
  rotor_shaft — fixed reference spine (no track)

License: Apache-2.0
"""
from __future__ import annotations

from pathlib import Path

from build123d import Pos, Rot, import_step
from ocp_vscode import Animation, Camera, show, set_port
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

CACHE         = Path(__file__).parent / "cache"
BEARING_CACHE = Path(__file__).parent.parent / "bearings" / "cache"

HOLD_END  = 12  # explosion held until 12 s
CLOSE_END = 14  # reassembly done at 14 s
TOTAL     = 16  # full cycle length


def _track(start: float, dist: float) -> tuple[list, list]:
    """Return (times, values) for a single-axis Z-translation track."""
    return (
        [0, start, start + 1, HOLD_END, CLOSE_END, TOTAL],
        [0, 0,     dist,      dist,     0,         0],
    )


def main() -> None:
    active_port = next(
        (int(p) for p in get_ports() if port_check(int(p))), None
    )
    if active_port is None:
        print("❌ 未检测到 OCP CAD Viewer")
        return
    set_port(active_port)

    print("Loading STEP files ...")
    housing          = import_step(str(CACHE / "housing_circular_spline.step"))
    flex             = import_step(str(CACHE / "flex_spline.step"))
    wave_cam         = import_step(str(CACHE / "wave_generator_cam.step"))
    out_flange       = import_step(str(CACHE / "output_flange.step"))
    motor_cap        = import_step(str(CACHE / "motor_endcap_front.step"))
    enc_cover        = import_step(str(CACHE / "encoder_cover.step"))
    bearing_7001     = import_step(str(BEARING_CACHE / "angular_contact_bearing.step"))
    mr85zz           = import_step(str(BEARING_CACHE / "mr_bearing.step"))
    rotor_shaft      = import_step(str(CACHE / "rotor_shaft.step"))
    motor_stator     = import_step(str(CACHE / "motor_stator.step"))
    rotor_shell      = import_step(str(CACHE / "rotor_shell.step"))
    arc_magnet       = import_step(str(CACHE / "arc_magnet.step"))
    stator_winding   = import_step(str(CACHE / "stator_winding.step"))
    motor_controller = import_step(str(CACHE / "motor_controller.step"))
    print("  All STEP loaded.")

    # ── 装配态定位（与 assembly.py 一致）/ Assembled positions ────────────────
    housing_asm          = Pos(0, 0,  0)  * housing
    flex_asm             = Pos(0, 0,  0)  * flex
    wave_cam_asm         = Pos(0, 0,  3)  * wave_cam
    output_asm           = Pos(0, 0, -8)  * out_flange
    motor_cap_asm        = Pos(0, 0, 30)  * motor_cap
    enc_cover_asm        = Pos(0, 0, 35)  * enc_cover
    bearing_7001_asm     = Pos(0, 0,  0)  * bearing_7001
    mr85zz_front_asm     = Pos(0, 0, 30)  * mr85zz
    mr85zz_rear_asm      = Pos(0, 0, 35)  * mr85zz
    rotor_shaft_asm      = Pos(0, 0,  0)  * rotor_shaft
    motor_stator_asm     = Pos(0, 0, 28)  * motor_stator
    rotor_shell_asm      = Pos(0, 0, 28)  * rotor_shell
    stator_winding_asm   = Pos(0, 0, 28)  * stator_winding
    motor_controller_asm = Pos(0, 0, 41)  * motor_controller
    arc_magnet_asms = [
        Pos(0, 0, 28) * Rot(0, 0, 360.0 * i / 14) * arc_magnet
        for i in range(14)
    ]

    # ── 显示装配态（动画起点）/ Show assembled state ──────────────────────────
    show(
        housing_asm, flex_asm, wave_cam_asm, output_asm,
        motor_cap_asm, enc_cover_asm, bearing_7001_asm,
        mr85zz_front_asm, mr85zz_rear_asm,
        rotor_shaft_asm, motor_stator_asm, rotor_shell_asm,
        stator_winding_asm, motor_controller_asm,
        *arc_magnet_asms,
        names=[
            "housing", "flex_spline", "wave_cam", "output_flange",
            "motor_endcap", "encoder_cover", "bearing_7001c",
            "mr85zz_front", "mr85zz_rear",
            "rotor_shaft", "motor_stator", "rotor_shell",
            "stator_winding", "motor_controller",
            *[f"magnet_{i:02d}" for i in range(14)],
        ],
        colors=[
            "steelblue", "coral", "goldenrod", "mediumseagreen",
            "slateblue", "lightgray", "silver",
            "silver", "silver",
            "dimgray", "orangered", "darkgray",
            "goldenrod", "darkgreen",
            *["mediumpurple"] * 14,
        ],
        reset_camera=Camera.ISO,
    )

    # ── 爆炸动画轨道 / Explosion animation tracks ─────────────────────────────
    anim = Animation()

    # Z 轴平移爆炸：顶部先出 → 底部后出 / Z-axis: top-first staged explosion
    anim.add_track("/Group/motor_controller", "tz", *_track(0, +65))
    anim.add_track("/Group/encoder_cover",    "tz", *_track(1, +55))
    anim.add_track("/Group/mr85zz_rear",      "tz", *_track(1, +55))  # exits with encoder_cover
    anim.add_track("/Group/motor_endcap",     "tz", *_track(2, +42))
    anim.add_track("/Group/mr85zz_front",     "tz", *_track(2, +42))  # exits with motor_endcap
    anim.add_track("/Group/rotor_shell",      "tz", *_track(3, +30))
    # 14 magnets co-move with rotor shell
    for i in range(14):
        anim.add_track(f"/Group/magnet_{i:02d}", "tz", *_track(3, +30))
    anim.add_track("/Group/stator_winding",   "tz", *_track(4, +20))
    anim.add_track("/Group/motor_stator",     "tz", *_track(4, +15))
    anim.add_track("/Group/wave_cam",         "tz", *_track(4, +12))
    anim.add_track("/Group/flex_spline",      "tz", *_track(5, +8))
    anim.add_track("/Group/bearing_7001c",    "tz", *_track(6, -18))
    anim.add_track("/Group/output_flange",    "tz", *_track(7, -32))
    # housing and rotor_shaft stay fixed — no track

    anim.animate(1)   # speed=1, 16 s cycle

    print("✅ QDD 爆炸动画已启动（16 s 循环）")
    print("   顶: motor_controller → encoder_cover+mr85zz_rear → motor_endcap+mr85zz_front")
    print("   中: rotor_shell+14magnets → stator_winding/stator → wave_cam → flex_spline")
    print("   底: bearing_7001c → output_flange")
    print("   固定: housing (参考基准) + rotor_shaft (中心轴)")


if __name__ == "__main__":
    main()
