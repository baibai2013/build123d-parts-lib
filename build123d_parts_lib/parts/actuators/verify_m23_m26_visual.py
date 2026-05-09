"""M2-3 ~ M2-6 统一 7 视图视觉验证脚本。

对 4 件零件各生成 7 视图截图（ISO/FRONT/BACK/LEFT/RIGHT/TOP/BOTTOM），
存入 cache/ 目录，供人工目视检查。
"""
from __future__ import annotations

import time
from pathlib import Path

from build123d import import_step
from ocp_vscode import Camera, show, save_screenshot, set_port
from ocp_vscode.comms import port_check
from ocp_vscode.state import get_ports

CACHE = Path(__file__).parent / "cache"

PARTS = [
    ("wave_generator_cam",  "goldenrod"),
    ("output_flange",       "mediumseagreen"),
    ("motor_endcap_front",  "slateblue"),
    ("encoder_cover",       "lightgray"),
]

VIEWS = [
    ("ISO",    Camera.ISO),
    ("FRONT",  Camera.FRONT),
    ("BACK",   Camera.BACK),
    ("LEFT",   Camera.LEFT),
    ("RIGHT",  Camera.RIGHT),
    ("TOP",    Camera.TOP),
    ("BOTTOM", Camera.BOTTOM),
]


def main() -> None:
    active_port = next(
        (int(p) for p in get_ports() if port_check(int(p))), None
    )
    if active_port is None:
        print("❌ 未检测到 OCP CAD Viewer")
        return
    set_port(active_port)

    for slug, color in PARTS:
        step_path = CACHE / f"{slug}.step"
        if not step_path.exists():
            print(f"  ⚠ STEP 不存在，跳过: {step_path}")
            continue

        part = import_step(str(step_path))
        bb   = part.bounding_box()
        print(f"\n{'='*50}")
        print(f"  {slug}")
        print(f"  BBox: {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")

        for view_name, camera_pos in VIEWS:
            show(part, names=[slug], colors=[color], reset_camera=camera_pos)
            time.sleep(1.5)
            out = CACHE / f"{slug}_{view_name}.png"
            save_screenshot(str(out))
            print(f"  ✓ {view_name:8s} → {out.name}")

    print("\n✅ 全部截图完成")


if __name__ == "__main__":
    main()
