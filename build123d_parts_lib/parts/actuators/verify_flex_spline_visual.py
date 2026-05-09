"""柔轮 7 角度视觉验证脚本 / Flex Spline 7-view visual verification.

7 正交视图：FRONT / BACK / LEFT / RIGHT / TOP / BOTTOM + ISO
截图保存到 cache/flex_spline_<VIEW>.png

运行方式：
    python build123d_parts_lib/parts/actuators/verify_flex_spline_visual.py
"""
from __future__ import annotations

import time
from pathlib import Path

from build123d import import_step
from ocp_vscode import Camera, show, save_screenshot, set_port
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

STEP_PATH = Path(__file__).parent / "cache" / "flex_spline.step"
OUT_DIR   = Path(__file__).parent / "cache"

# ── 7 视图定义 ─────────────────────────────────────────────────────────────────
VIEWS = [
    ("ISO",    Camera.ISO),
    ("FRONT",  Camera.FRONT),
    ("BACK",   Camera.BACK),
    ("LEFT",   Camera.LEFT),
    ("RIGHT",  Camera.RIGHT),
    ("TOP",    Camera.TOP),
    ("BOTTOM", Camera.BOTTOM),
]

# ── 检查清单（人工确认项）────────────────────────────────────────────────────────
CHECKLIST = """
╔══════════════════════════════════════════════════════════════════╗
║              柔轮视觉检查清单 / Flex Spline Checklist             ║
╠══════════════════════════════════════════════════════════════════╣
║ ISO 视图                                                         ║
║  [ ] 外齿轮廓均匀分布，无缺齿或双齿现象                            ║
║  [ ] 底部法兰与杯壁过渡自然，无阶梯缺口                            ║
║  [ ] 中心孔 Φ12 可见，无堵塞                                      ║
╠══════════════════════════════════════════════════════════════════╣
║ TOP（俯视）                                                       ║
║  [ ] 100 齿均布，对称性正常                                        ║
║  [ ] 齿顶圆 Φ≈30.6 mm，目测与外圆协调                             ║
║  [ ] 中心孔圆心在几何中心                                          ║
╠══════════════════════════════════════════════════════════════════╣
║ BOTTOM（仰视）                                                    ║
║  [ ] 法兰底面平整，无布尔残留凸起                                   ║
║  [ ] 中心孔 Φ12 贯通可见                                          ║
╠══════════════════════════════════════════════════════════════════╣
║ FRONT（正视）                                                     ║
║  [ ] 杯高 ≈ 17 mm，法兰高 ≈ 3 mm，总高 ≈ 20 mm                  ║
║  [ ] 法兰外径 Φ32，杯外径 Φ≈29.25（根圆）                         ║
║  [ ] 杯壁壁厚 ≈ 1.2 mm（根圆半径 - 内孔半径）                     ║
╠══════════════════════════════════════════════════════════════════╣
║ BACK（后视）                                                      ║
║  [ ] 对称性与正视图一致                                            ║
╠══════════════════════════════════════════════════════════════════╣
║ LEFT / RIGHT（侧视）                                              ║
║  [ ] 齿宽均匀，无倾斜                                              ║
║  [ ] 杯底（法兰端）封闭，无开口                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""


def main() -> None:
    # ── 检测 OCP Viewer 端口 ──────────────────────────────────────────────────
    active_port = next(
        (int(p) for p in get_ports() if port_check(int(p))), None
    )
    if active_port is None:
        print("❌ 未检测到 OCP CAD Viewer，请先启动 VS Code OCP Viewer 扩展")
        return
    set_port(active_port)
    print(f"OCP Viewer 端口：{active_port}")

    # ── 导入 STEP ─────────────────────────────────────────────────────────────
    if not STEP_PATH.exists():
        print(f"❌ STEP 文件不存在：{STEP_PATH}")
        print("   请先运行 flex_spline.py 生成 STEP")
        return

    print(f"导入 STEP：{STEP_PATH}")
    part = import_step(str(STEP_PATH))

    bb  = part.bounding_box()
    vol = part.volume
    print(f"  BBox : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")
    print(f"  体积 : {vol:.1f} mm³")

    # ── 逐视图截图 ─────────────────────────────────────────────────────────────
    print(f"\n开始 {len(VIEWS)} 视图截图...\n")
    saved: list[str] = []

    for view_name, camera_pos in VIEWS:
        show(
            part,
            names=["flex_spline"],
            colors=["coral"],
            reset_camera=camera_pos,
        )
        time.sleep(1.5)   # 等待 WebGL 渲染稳定

        out_path = OUT_DIR / f"flex_spline_{view_name}.png"
        save_screenshot(str(out_path))
        saved.append(str(out_path))
        print(f"  ✓ {view_name:8s} → {out_path.name}")

    print(f"\n✅ 全部 {len(saved)} 张截图已保存到 {OUT_DIR}\n")
    print(CHECKLIST)


if __name__ == "__main__":
    main()
