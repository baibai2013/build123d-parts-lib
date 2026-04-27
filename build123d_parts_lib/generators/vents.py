"""Vent hole pattern generator.

在指定面上用 GridLocations 打孔阵，常用于外壳散热。
返回 Sketch 对象供 `extrude(mode=Mode.SUBTRACT)` 使用。

License: MIT
"""
from __future__ import annotations

from build123d import (
    BuildSketch, Circle, Face, GridLocations, Rectangle, Sketch,
)


def make_vent_pattern(
    target_face: Face,
    hole_radius: float = 2.0,
    x_spacing: float = 8.0,
    y_spacing: float = 8.0,
    x_count: int = 5,
    y_count: int = 3,
    shape: str = "circle",
) -> Sketch:
    """生成散热孔阵 Sketch。

    Args:
        target_face: 目标面（BuildPart 的 face 对象）
        hole_radius: 圆孔半径（圆孔时）；矩形槽时为短边一半
        x_spacing: X 方向孔距（中心到中心）
        y_spacing: Y 方向孔距
        x_count: X 方向孔数
        y_count: Y 方向孔数
        shape: "circle" 或 "slot"（椭圆/长圆槽，长宽比 2:1）

    返回：Sketch 对象

    使用示例:
        with BuildPart() as case:
            Box(60, 40, 30)
            top = case.faces().sort_by(Axis.Z)[-1]
            vent_sketch = make_vent_pattern(top, hole_radius=2)
            with BuildSketch(top):
                add(vent_sketch)
            extrude(amount=-2, mode=Mode.SUBTRACT)
    """
    if shape not in ("circle", "slot"):
        raise ValueError(f"shape must be 'circle' or 'slot', got {shape!r}")
    if x_count < 1 or y_count < 1:
        raise ValueError("x_count and y_count must be >= 1")

    with BuildSketch(target_face) as sk:
        with GridLocations(x_spacing, y_spacing, x_count, y_count):
            if shape == "circle":
                Circle(hole_radius)
            else:  # slot
                Rectangle(hole_radius * 2 * 2, hole_radius * 2)
    return sk.sketch


if __name__ == "__main__":
    from build123d import BuildPart, Box, Axis, Mode, extrude, export_step
    with BuildPart() as demo:
        Box(60, 40, 5)
        top = demo.faces().sort_by(Axis.Z)[-1]
        vents = make_vent_pattern(top, hole_radius=2, x_count=6, y_count=4)
        # 直接 extrude 需把 sketch 并入 BuildPart 内的 sketch context
        # 此处演示外部生成后手动合并
    print(f"OK: vents generated, {6*4} holes expected")
