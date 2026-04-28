"""SG90 servo bracket template.

3 参数生成一个 SG90 舵机安装座（可卡入并用两颗 M2 螺丝固定耳朵）。

Reference: build123d-cad skill references/assembly/mounting-experience.md §1.1
License: MIT
"""
from __future__ import annotations

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Plane,
    Rectangle,
    extrude,
)

from build123d_parts_lib.parts.servos.sg90 import (
    BODY_H,
    BODY_L,
    BODY_W,
    EAR_T,
    EAR_W_TOTAL,
    EAR_Z_OFFSET,
)


def make_sg90_bracket(
    wall_thickness: float = 2.5,
    print_clearance: float = 0.3,
    base_thickness: float = 3.0,
) -> Part:
    """生成 SG90 舵机安装座（一个带腔的盒体 + 底板）。

    Args:
        wall_thickness: 墙壁厚（默认 2.5 mm，FDM 标准）
        print_clearance: 3D 打印间隙（每侧，默认 0.3 mm）
        base_thickness: 底板厚（默认 3.0 mm）

    几何：
        - 中央矩形腔：贴合 SG90 主体（加间隙）
        - 耳朵槽：侧壁开槽让 SG90 侧耳插入
        - 底板：可再开孔用 M2 螺丝从底部固定
        - 原点：底面中心，+Z = 开口向上

    使用示例:
        >>> bracket = make_sg90_bracket()
        >>> export_step(bracket, "sg90_mount.step")
    """
    # 内腔
    cavity_l = BODY_L + 2 * print_clearance
    cavity_w = BODY_W + 2 * print_clearance
    cavity_h = BODY_H           # 深度=舵机主体高（不含输出轴伸出）
    # 外壳
    outer_l = cavity_l + 2 * wall_thickness
    outer_w = cavity_w + 2 * wall_thickness
    outer_h = cavity_h + base_thickness
    # 耳朵槽（从 Z = base_thickness + EAR_Z_OFFSET - EAR_T/2 位置开始 + EAR_T 厚度）
    ear_slot_z = base_thickness + EAR_Z_OFFSET
    ear_slot_w = EAR_W_TOTAL + 2 * print_clearance

    with BuildPart() as bracket:
        # 实心外盒
        with BuildSketch(Plane.XY):
            Rectangle(outer_l, outer_w)
        extrude(amount=outer_h)

        # 挖内腔（从顶面向下挖 cavity_h 深）
        top = bracket.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top):
            Rectangle(cavity_l, cavity_w)
        extrude(amount=-cavity_h, mode=Mode.SUBTRACT)

        # 挖耳朵槽（横穿 +X/-X 两侧壁）
        ear_plane = Plane.XY.offset(ear_slot_z)
        with BuildSketch(ear_plane):
            Rectangle(ear_slot_w, cavity_w)
            Rectangle(cavity_l, cavity_w, mode=Mode.SUBTRACT)
        extrude(amount=EAR_T, mode=Mode.SUBTRACT, both=True)

    return bracket.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_sg90_bracket()
    export_step(p, "/tmp/sg90_bracket.step")
    print(f"OK: SG90 bracket, volume={p.volume:.1f} mm³")
