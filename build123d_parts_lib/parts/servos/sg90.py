"""SG90 servo entity — reverse-engineered from sg90_ref.step.

Source:    references/sg90-step/sg90_ref.step (Autodesk Translation Framework v14.24)
Reference: servodatabase.com/servo/towerpro/sg-90
License:   MIT

坐标系：原点在机体底面中心（XY），Z=0 底面，Z=BODY_H 顶面。
输出轴从顶面沿 +Z 方向伸出。
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align, Axis, Box, BuildPart, BuildSketch, Circle, Cylinder,
    Locations, Mode, Part, Plane, Rectangle, export_step, extrude,
)

# ── 机体 ──────────────────────────────────────────────────────────────────
BODY_L = 23.0    # X 长（实测，规格书 22.8）
BODY_W = 12.6    # Y 宽（实测，规格书 12.2）
BODY_H = 27.9    # Z 高含底部连接器凸台（实测，规格书仅壳体 22.7）

# ── 安装耳 ────────────────────────────────────────────────────────────────
EAR_W_TOTAL   = 29.9   # 含两侧耳朵总 X 宽（实测，规格书 32.2）
EAR_T         = 2.4    # 耳朵板厚（实测）
EAR_Z_FROM_TOP = 8.5   # 耳朵上表面距机体顶面（实测）
SCREW_D       = 2.1    # 螺孔直径（实测）
SCREW_PITCH   = 27.8   # 两螺孔间距（实测）

# ── 输出轴 ────────────────────────────────────────────────────────────────
SHAFT_R       = 2.5    # 输出轴半径
SHAFT_H       = 3.2    # 输出轴高出机体顶面（实测，规格书 5.0）
SHAFT_X_OFF   = -1.8   # 输出轴 X 偏移（相对机体中心，负=偏向连接器侧）
COLLAR_R      = 6.3    # 衬套外径（实测）
COLLAR_DEPTH  = 4.2    # 衬套嵌入机体顶面深度（实测）


def make_sg90() -> Part:
    """生成 SG90 舵机简化实体。

    坐标：原点在机体底面中心（XY），Z=0 底面，Z=BODY_H 顶面。
    """
    ear_z_bottom_from_top = EAR_Z_FROM_TOP + EAR_T          # 耳朵下表面距顶面
    ear_z_top    = BODY_H - EAR_Z_FROM_TOP                   # 耳朵上表面 Z
    ear_z_bottom = BODY_H - ear_z_bottom_from_top            # 耳朵下表面 Z
    ear_overhang = (EAR_W_TOTAL - BODY_L) / 2               # 单侧耳朵伸出量

    with BuildPart() as servo:
        # 主体
        Box(BODY_L, BODY_W, BODY_H,
            align=(Align.CENTER, Align.CENTER, Align.MIN))

        # 安装耳（左右各伸出 ear_overhang，高度为 EAR_T）
        with BuildSketch(Plane.XY.offset(ear_z_bottom)):
            Rectangle(EAR_W_TOTAL, BODY_W)
            Rectangle(BODY_L, BODY_W, mode=Mode.SUBTRACT)
        extrude(amount=EAR_T)

        # 螺孔（通孔，穿透耳板）
        with BuildSketch(Plane.XY.offset(ear_z_top + 0.1)):
            with Locations((SCREW_PITCH / 2, 0), (-SCREW_PITCH / 2, 0)):
                Circle(SCREW_D / 2)
        extrude(amount=-(EAR_T + 0.2), mode=Mode.SUBTRACT)

        # 输出轴
        with BuildSketch(Plane.XY.offset(BODY_H)):
            with Locations((SHAFT_X_OFF, 0)):
                Circle(SHAFT_R)
        extrude(amount=SHAFT_H)

    return servo.part


if __name__ == "__main__":
    part = make_sg90()
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    export_step(part, str(cache_dir / "sg90.step"))
    print(f"OK  volume={part.volume:.1f} mm3  bbox_Z={part.bounding_box().size.Z:.2f}")
