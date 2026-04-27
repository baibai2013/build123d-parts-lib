"""SG90 servo entity (simplified).

Source: data-sources/servos.yaml:SG90 (skill build123d-cad)
Reference: https://servodatabase.com/servo/towerpro/sg-90
License (this file): MIT

简化程度：
- 主体箱 + 侧耳凸缘 + 输出轴圆柱
- 不建模线缆、齿牙花键
- 足够装配定位与 bbox 占位
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    BuildPart, BuildSketch, Box, Circle, Cylinder, Locations, Mode, Part, Plane,
    Rectangle, Axis, extrude, export_step,
)

# ===== SG90 参数（与 data-sources/servos.yaml 一致）=====
BODY_L = 22.8   # X 长
BODY_W = 12.2   # Y 窄
BODY_H = 22.7   # Z 高（不含输出轴）
EAR_W_TOTAL = 32.2  # 含两侧耳朵总宽
EAR_T = 2.5          # 耳朵厚
EAR_Z_OFFSET = 15.5  # 耳朵中面到底面距离
SHAFT_R = 2.5
SHAFT_H = 5.0        # 输出轴顶距主体顶面


def make_sg90() -> Part:
    """生成 SG90 舵机简化实体（主体 + 耳朵凸缘 + 输出轴）。

    坐标：原点在主体几何中心（XY），Z=0 为底面。
    """
    with BuildPart() as servo:
        # 主体
        with BuildSketch(Plane.XY):
            Rectangle(BODY_L, BODY_W)
        extrude(amount=BODY_H)

        # 耳朵凸缘（在 Z = EAR_Z_OFFSET 处绘厚度为 EAR_T 的板）
        ear_plane = Plane.XY.offset(EAR_Z_OFFSET - EAR_T / 2)
        with BuildSketch(ear_plane):
            Rectangle(EAR_W_TOTAL, BODY_W)
            Rectangle(BODY_L, BODY_W, mode=Mode.SUBTRACT)
        extrude(amount=EAR_T)

        # 输出轴（偏向主体一端，经验值 0.3*BODY_L）
        top_face = servo.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            with Locations((BODY_L * 0.3 - BODY_L / 2, 0)):
                Circle(SHAFT_R)
        extrude(amount=SHAFT_H)

    return servo.part


if __name__ == "__main__":
    part = make_sg90()
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)
    export_step(part, str(cache_dir / "sg90.step"))
    print(f"OK: sg90.step written, volume={part.volume:.1f} mm³")
