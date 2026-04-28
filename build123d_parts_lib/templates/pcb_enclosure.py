"""PCB enclosure template.

从 PCB 尺寸反推壳体：盒底 + 四壁 + 顶开口（留盖板）。
MVP 版本：不含螺丝柱（留到用户自己用 modules.threaded_insert_boss 手动放）。

License: MIT
"""
from __future__ import annotations

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Mode,
    Part,
    Rectangle,
    extrude,
)


def make_pcb_enclosure(
    pcb_length: float,
    pcb_width: float,
    component_height: float = 8.0,
    clearance: float = 1.0,
    wall_thickness: float = 2.0,
    base_thickness: float = 2.0,
) -> Part:
    """生成 PCB 外壳（无盖板、无螺丝柱）。

    Args:
        pcb_length: PCB 长（X 方向）
        pcb_width: PCB 宽（Y 方向）
        component_height: PCB 上元器件最高高度
        clearance: PCB 四周间隙（每侧）
        wall_thickness: 壁厚（默认 2.0，FDM 推荐）
        base_thickness: 底板厚

    几何：
        - 原点：底面几何中心，+Z 开口朝上
        - 内腔：PCB 贴底，上方留 component_height + 2mm 余量
        - 螺丝柱：未集成，用户需用 `modules.threaded_insert_boss.make_m3_boss`
                  + `Pos(x,y,z) * boss` 手动摆放

    使用示例:
        >>> case = make_pcb_enclosure(pcb_length=50, pcb_width=30)
        >>> export_step(case, "case.step")
    """
    # 外壳尺寸
    inner_l = pcb_length + 2 * clearance
    inner_w = pcb_width + 2 * clearance
    inner_h = component_height + 2.0
    outer_l = inner_l + 2 * wall_thickness
    outer_w = inner_w + 2 * wall_thickness
    outer_h = inner_h + base_thickness

    with BuildPart() as case:
        # 实心外盒：底面在 Z=0
        Box(
            outer_l, outer_w, outer_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 顶面挖内腔
        top = case.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top):
            Rectangle(inner_l, inner_w)
        extrude(amount=-inner_h, mode=Mode.SUBTRACT)

    return case.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_pcb_enclosure(pcb_length=50, pcb_width=30)
    export_step(p, "/tmp/pcb_enclosure.step")
    print(f"OK: PCB enclosure, volume={p.volume:.1f} mm³")
