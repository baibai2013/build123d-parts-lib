"""外转子壳磁钢保留槽优化 — 3 变体并排对比 / Rotor shell magnet retention improvement.

OCP 并排：V1 保守 | V2 推荐 | V3 最强
选定后替换 rotor_shell.py 中的参数。

关键几何说明：
  catch = pocket_depth − lip_protrusion
        = 磁钢外表面(22.25mm) − 卡唇尖端半径
  catch 越大，磁钢需要把卡唇推开越多才能脱出 → 保持力越强

原始设计 catch = 0.20mm（PETG 打印边缘容差约 0.1-0.2mm，保持力极弱）

License: Apache-2.0
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    GeomType,
    Hole,
    Mode,
    Part,
    Pos,
    Rot,
    chamfer,
    export_step,
    import_step,
)

from build123d_parts_lib.parts.actuators.arc_magnet import (
    magnet_half_deg,   # ≈ 11.57°
    magnet_h,          # 10.0 mm
    n_poles,           # 14
)

# ── 公共不变参数 / shared base params ──────────────────────────────────────────
rotor_od      = 47.5   # mm
rotor_h       = 12.0   # mm
shell_wall_t  =  1.5   # mm
center_bore_d =  5.0   # mm
endplate_t    =  2.0   # mm
shell_inner_r = rotor_od / 2 - shell_wall_t   # 22.25 mm


def _make_variant(
    pocket_depth:    float = 0.5,   # mm — radial depth of arc pocket into wall
    lip_protrusion:  float = 0.3,   # mm — radial inward reach of snap lip
    retention_lip_h: float = 2.0,   # mm — axial height of snap lip
) -> Part:
    """Parameterised factory shared by all three variants.

    Geometry invariant:  catch = pocket_depth − lip_protrusion  (must be > 0)
    """
    assert pocket_depth > lip_protrusion, (
        f"catch must be > 0: pocket_depth={pocket_depth} lip_protrusion={lip_protrusion}"
    )
    pocket_r_outer = shell_inner_r                    # pocket opens at inner wall surface
    pocket_r_inner = shell_inner_r - pocket_depth     # pocket bottom
    pocket_h       = magnet_h + 0.2                   # 10.2 mm axial clearance

    # ── Base shell ───────────────────────────────────────────────────────────
    with BuildPart() as p:
        Cylinder(
            radius=rotor_od / 2,
            height=rotor_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=shell_inner_r,
            height=rotor_h - endplate_t + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        Hole(radius=center_bore_d / 2)
        try:
            open_edges = [
                e for e in p.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - rotor_od / 2) < 0.3 and abs(e.center().Z) < 0.3
            ]
            if open_edges:
                chamfer(open_edges, length=0.5)
        except Exception:
            pass

    solid = p.part

    # ── 14× arc pocket + snap-in lip (Algebra mode) ─────────────────────────
    clip_size = pocket_r_outer + 5.0
    clip_h    = pocket_h + 0.2

    # Full-depth pocket annulus: cut from inner wall inward by pocket_depth
    pocket_annulus = (
        Cylinder(
            radius=pocket_r_outer + 0.05,
            height=pocket_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=pocket_r_inner - 0.05,
            height=pocket_h + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # Retention lip: add back material at open end, leaving catch undercut
    # lip tip radius = pocket_r_inner + lip_protrusion < shell_inner_r → undercut
    lip_annulus = (
        Cylinder(
            radius=pocket_r_inner + lip_protrusion,
            height=retention_lip_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=pocket_r_inner - 0.05,
            height=retention_lip_h + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # Arc clip planes — trim annulus to magnet angular width
    upper_clip = (
        Rot(0, 0, +magnet_half_deg)
        * Pos(0, clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )

    pocket_proto = pocket_annulus - upper_clip - lower_clip
    lip_proto    = lip_annulus    - upper_clip - lower_clip

    for i in range(n_poles):
        angle = 360.0 * i / n_poles
        solid = (
            solid
            - Rot(0, 0, angle) * pocket_proto
            + Rot(0, 0, angle) * lip_proto
        )

    return solid


# ══ 3 变体实例化 / instantiate variants ═══════════════════════════════════════
print("Building V1 (conservative)...")
v1 = _make_variant(pocket_depth=0.5, lip_protrusion=0.3, retention_lip_h=2.0)
# catch=0.20mm — 与原版相同保持力，卡唇加高至 2.0mm (原 0.8mm)，更厚实可靠
# 剩余壁厚 1.0mm；装配力：低

print("Building V2 (recommended)...")
v2 = _make_variant(pocket_depth=0.8, lip_protrusion=0.3, retention_lip_h=2.0)
# catch=0.50mm — 磁钢需推开卡唇 0.50mm 才能脱出 (原 0.20mm 的 2.5×)
# 剩余壁厚 0.7mm；装配力：中（倾斜 ~15° 安装同原来）

print("Building V3 (maximum)...")
v3 = _make_variant(pocket_depth=0.8, lip_protrusion=0.5, retention_lip_h=2.0)
# catch=0.30mm — 卡唇更宽(0.5mm)，摩擦面更大，适合无粘合剂场景
# 剩余壁厚 0.7mm；装配力：中高

# ── 三层断言验证 / 3-layer assertion ──────────────────────────────────────────
out_dir = Path(__file__).parent / "cache"
out_dir.mkdir(exist_ok=True)

VARIANTS = [
    ("V1 (pocket=0.5 lip_h=2.0)", v1, 0.5, 0.3, 2.0),
    ("V2 (pocket=0.8 lip_h=2.0)", v2, 0.8, 0.3, 2.0),
    ("V3 (pocket=0.8 lip_h=2.0 prot=0.5)", v3, 0.8, 0.5, 2.0),
]

print("\n── 三层验证 ────────────────────────────────────────────")
for label, part, pd, lp, lh in VARIANTS:
    results = []
    results.append("✅ BRep" if part.is_valid else "❌ BRep无效")
    vol = part.volume
    results.append(f"✅ vol={vol:.0f}mm³" if vol > 0 else "❌ vol≤0")
    bb = part.bounding_box()
    results.append(
        f"✅ OD={bb.size.X:.1f}mm" if abs(bb.size.X - rotor_od) < 0.5
        else f"❌ OD={bb.size.X:.2f}"
    )
    results.append(
        f"✅ H={bb.size.Z:.1f}mm" if abs(bb.size.Z - rotor_h) < 0.2
        else f"❌ H={bb.size.Z:.2f}"
    )
    tag = label.split()[0]
    step_p = str(out_dir / f"rotor_shell_{tag.lower()}.step")
    export_step(part, step_p)
    ri = import_step(step_p)
    diff = abs(ri.volume - vol) / vol
    results.append("✅ STEP精度" if diff < 0.001 else f"❌ STEP差{diff:.4%}")
    catch = pd - lp
    print(f"{tag}: catch={catch:.2f}mm  wall_rem={shell_wall_t-pd:.1f}mm  "
          f"{' | '.join(results)}")

# ── OCP 并排预览 / side-by-side OCP preview ──────────────────────────────────
from build123d import Location

offset = rotor_od * 1.4   # ≈ 66 mm 间距
v2_show = v2.move(Location((offset, 0, 0)))
v3_show = v3.move(Location((offset * 2, 0, 0)))

try:
    from ocp_vscode import show, set_port, Camera
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports

    active_port = next(
        (int(p) for p in get_ports() if port_check(int(p))), None
    )
    if active_port:
        set_port(active_port)
        show(
            v1, v2_show, v3_show,
            names=["V1_conservative", "V2_recommended", "V3_maximum"],
            colors=["steelblue", "orange", "green"],
            reset_camera=Camera.ISO,
        )
        print("\nOCP Viewer: 3 变体并排展示 ✓")
        print("  左 V1=steelblue | 中 V2=orange | 右 V3=green")
    else:
        print("OCP Viewer 未检测到，请在 VS Code/Cursor 中启动 OCP CAD Viewer 扩展")
except Exception as e:
    print(f"OCP 预览跳过: {e}")

print("""
── 变体对比 ─────────────────────────────────────────────────
  原始  catch=0.20mm  lip=0.3×0.8mm  wall=1.0mm  → 磁钢容易掉
  V1    catch=0.20mm  lip=0.3×2.0mm  wall=1.0mm  → 卡唇更高，打印更可靠
  V2    catch=0.50mm  lip=0.3×2.0mm  wall=0.7mm  → 保持力 2.5×，推荐
  V3    catch=0.30mm  lip=0.5×2.0mm  wall=0.7mm  → 卡唇更宽，摩擦更大

推荐 V2：catch 从 0.20mm 增至 0.50mm，磁钢需要把 PETG 卡唇推开 0.5mm 才脱出。
         安装方法：倾斜约 15° 插入一端，轻按另一端听到咔哒声即入位。
""")
