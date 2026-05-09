"""QDD 关节模组爆炸展开动画 / QDD Joint Module Exploded-View Animation.

16-second loop in OCP CAD Viewer:
  0 → 6 s  — staged explosion along Z (encoder_cover first, output_flange last)
  6 → 12 s — hold exploded view
  12 → 14 s — reassemble
  14 → 16 s — hold assembled

Explosion order (top → bottom):
  t=0-1 s : encoder_cover   → +45 mm  (topmost, farthest)
  t=1-2 s : motor_endcap    → +30 mm
  t=2-3 s : wave_cam        → +25 mm
  t=2-3 s : thin_bearing    → +20 mm  (same group as wave_cam)
  t=3-4 s : flex_spline     → +15 mm
  t=4-5 s : bearing_7001c   → -20 mm  (downward, toward output side)
  t=5-6 s : output_flange   → -30 mm  (bottommost, farthest down)
  housing  stays as reference frame (no track added)
"""
from __future__ import annotations

from pathlib import Path

from build123d import Pos, import_step
from ocp_vscode import Animation, Camera, show, set_port
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

CACHE         = Path(__file__).parent / "cache"
BEARING_CACHE = Path(__file__).parent.parent / "bearings" / "cache"

HOLD_END  = 12  # explosion held until 12 s
CLOSE_END = 14  # reassembly done at 14 s
TOTAL     = 16  # full cycle length


def _track(start: float, dist: float) -> tuple[list, list]:
    """Return (times, values) for a single-axis translation track."""
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
    housing      = import_step(str(CACHE / "housing_circular_spline.step"))
    flex         = import_step(str(CACHE / "flex_spline.step"))
    wave_cam     = import_step(str(CACHE / "wave_generator_cam.step"))
    out_flange   = import_step(str(CACHE / "output_flange.step"))
    motor_cap    = import_step(str(CACHE / "motor_endcap_front.step"))
    enc_cover    = import_step(str(CACHE / "encoder_cover.step"))
    bearing_7001 = import_step(str(BEARING_CACHE / "angular_contact_bearing.step"))
    thin_brg     = import_step(str(BEARING_CACHE / "thin_section_bearing.step"))

    # ── 装配态定位（与 assembly.py 一致）/ Assembled positions ─────────────────
    housing_asm      = Pos(0, 0,  0) * housing
    flex_asm         = Pos(0, 0,  0) * flex
    wave_cam_asm     = Pos(0, 0,  3) * wave_cam
    output_asm       = Pos(0, 0, -8) * out_flange
    motor_cap_asm    = Pos(0, 0, 30) * motor_cap
    enc_cover_asm    = Pos(0, 0, 35) * enc_cover
    bearing_7001_asm = Pos(0, 0,  0) * bearing_7001
    thin_bearing_asm = Pos(0, 0,  3) * thin_brg

    # ── 显示装配态（动画起点）/ Show assembled state — animation start ──────────
    show(
        housing_asm, flex_asm, wave_cam_asm, output_asm,
        motor_cap_asm, enc_cover_asm, bearing_7001_asm, thin_bearing_asm,
        names=[
            "housing", "flex_spline", "wave_cam", "output_flange",
            "motor_endcap", "encoder_cover", "bearing_7001c", "thin_bearing",
        ],
        colors=[
            "steelblue", "coral", "goldenrod", "mediumseagreen",
            "slateblue", "lightgray", "silver", "silver",
        ],
        reset_camera=Camera.ISO,
    )

    # ── 爆炸动画轨道 / Explosion animation tracks ─────────────────────────────
    anim = Animation()

    # 顶部零件先出，底部零件后出 / Top parts first, bottom parts last
    t_enc, v_enc = _track(start=0, dist=+45)   # encoder_cover  → up
    t_mot, v_mot = _track(start=1, dist=+30)   # motor_endcap   → up
    t_wav, v_wav = _track(start=2, dist=+25)   # wave_cam       → up
    t_thn, v_thn = _track(start=2, dist=+20)   # thin_bearing   → up (same group)
    t_flx, v_flx = _track(start=3, dist=+15)   # flex_spline    → up
    t_b7,  v_b7  = _track(start=4, dist=-20)   # bearing_7001c  → down
    t_out, v_out = _track(start=5, dist=-30)   # output_flange  → down

    anim.add_track("/Group/encoder_cover",  "tz", t_enc, v_enc)
    anim.add_track("/Group/motor_endcap",   "tz", t_mot, v_mot)
    anim.add_track("/Group/wave_cam",       "tz", t_wav, v_wav)
    anim.add_track("/Group/thin_bearing",   "tz", t_thn, v_thn)
    anim.add_track("/Group/flex_spline",    "tz", t_flx, v_flx)
    anim.add_track("/Group/bearing_7001c",  "tz", t_b7,  v_b7)
    anim.add_track("/Group/output_flange",  "tz", t_out, v_out)
    # housing stays fixed — no track needed

    anim.animate(1)   # speed=1, normal playback

    print("✅ 爆炸动画已启动（16 s 循环）")
    print("   顶部: encoder_cover → motor_endcap → wave_cam / thin_bearing")
    print("   底部: flex_spline → bearing_7001c → output_flange")
    print("   housing 固定作为参考基准")


if __name__ == "__main__":
    main()
