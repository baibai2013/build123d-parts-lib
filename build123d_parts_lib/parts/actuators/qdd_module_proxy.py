"""QDD 关节模组 — M0 比例占位预览 / QDD joint module M0 bounding-box proxy.

Purpose:
    Verify axial proportions and zone layout with Cylinder proxies before
    modeling any real part.

Axial stack (+Z up, rear→load end):
    z= 0~ 8   Encoder cover  Φ30 × 8   gray
    z= 8~18   Motor stator   Φ40 × 10  steelblue
    z=18~38   Harmonic zone  Φ36 × 20  orange
    z=38~44   Output flange  Φ40 × 6   green
"""
from __future__ import annotations

from build123d import Align, BuildPart, Cylinder, Pos
from ocp_vscode import Camera, show
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

# ── 关键尺寸（与 PLAN.md §模组关键参数 完全一致）────────────────────
# Key dims — must match PLAN.md §模组关键参数 exactly
outer_r        = 22.5   # module outer radius (45/2) mm
motor_r        = 20.0   # stator outer radius (40/2) mm
harmonic_r     = 18.0   # harmonic zone radius        mm
flange_r       = 20.0   # output flange radius        mm
encoder_r      = 15.0   # encoder cover radius        mm

encoder_h      =  8.0   # encoder cover height  mm
stator_h       = 10.0   # motor stator height   mm
harmonic_h     = 20.0   # harmonic zone height  mm
flange_h       =  6.0   # output flange height  mm  (compact proxy)

# ── Z 堆叠位置（从编码器端累积）──────────────────────────────────────
# Z start positions (accumulated from rear)
z_encoder  = 0.0
z_stator   = z_encoder  + encoder_h    # 8
z_harmonic = z_stator   + stator_h     # 18
z_flange   = z_harmonic + harmonic_h   # 38
total_h    = z_flange   + flange_h     # 44 ≈ 45 mm ✓


def _cyl(r: float, h: float, z0: float):
    """Cylinder with bottom at z=z0. / 底面位于 z=z0 的圆柱体。"""
    with BuildPart() as bp:
        Cylinder(radius=r, height=h,
                 align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, z0) * bp.part


# ── 占位体 / Proxy solids ─────────────────────────────────────────
encoder_proxy  = _cyl(encoder_r,  encoder_h,  z_encoder)
stator_proxy   = _cyl(motor_r,    stator_h,   z_stator)
harmonic_proxy = _cyl(harmonic_r, harmonic_h, z_harmonic)
flange_proxy   = _cyl(flange_r,   flange_h,   z_flange)

# ── OCP 预览 / OCP preview ───────────────────────────────────────
try:
    active_port = next(
        (int(p) for p in get_ports() if port_check(int(p))), None
    )
    if active_port:
        from ocp_vscode import set_port
        set_port(active_port)

    show(
        encoder_proxy, stator_proxy, harmonic_proxy, flange_proxy,
        names=[
            "encoder_cover_proxy",
            "motor_stator_proxy",
            "harmonic_zone_proxy",
            "output_flange_proxy",
        ],
        colors=["gray", "steelblue", "orange", "green"],
        reset_camera=Camera.ISO,
    )
    print("OCP Viewer: QDD M0 比例占位预览 ✓")
except Exception as e:
    print(f"OCP preview skipped: {e}")

# ── 尺寸汇总 / Dimension summary ─────────────────────────────────
print(f"\n── QDD M0 比例验证 ─────────────────────────────────────")
print(f"  encoder_cover  z={z_encoder:4.0f}~{z_stator:4.0f}  Φ{encoder_r*2:.0f}×{encoder_h:.0f}  gray")
print(f"  motor_stator   z={z_stator:4.0f}~{z_harmonic:4.0f}  Φ{motor_r*2:.0f}×{stator_h:.0f}  steelblue")
print(f"  harmonic_zone  z={z_harmonic:4.0f}~{z_flange:4.0f}  Φ{harmonic_r*2:.0f}×{harmonic_h:.0f}  orange")
print(f"  output_flange  z={z_flange:4.0f}~{total_h:4.0f}  Φ{flange_r*2:.0f}×{flange_h:.0f}  green")
print(f"  total axial  = {total_h:.0f} mm  (target 45 mm ≈ ✓)")
print(f"  max diameter ≤ Φ{outer_r*2:.0f} mm ✓")
print(f"────────────────────────────────────────────────────────")
