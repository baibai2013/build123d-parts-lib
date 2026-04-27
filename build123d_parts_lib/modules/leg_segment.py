"""通用机器人连杆 / Generic robotic link segment.

参数化矩形连杆，两端可选圆孔（用作铰接销孔或螺丝过孔）。
Parametric rectangular link with optional pivot holes at each end.

常见用途 / Typical use:
    - 四足腿：股骨（femur）、胫骨（tibia）
    - 机械臂：连杆
    - 剪式机构 / 平行四边形

Source: build123d-cad-skill-test/tests/23-quadruped-leg-2dof
License: MIT
"""
from __future__ import annotations

from build123d import (
    BuildPart, BuildSketch, Rectangle, Circle, Locations, Location,
    Mode, Part, Plane, Axis, extrude, fillet,
)


def make_leg_segment(
    length: float = 60.0,
    width: float = 10.0,
    thickness: float = 4.0,
    pivot_hole_r: float = 1.6,
    pivot_offset: float = 6.0,
    end_fillet_r: float = 3.0,
    drill_pivots: bool = True,
) -> Part:
    """生成两端带铰孔的矩形连杆 / Rectangular link with pivot holes at both ends.

    Args:
        length:        连杆全长（X 方向）/ total length along X (mm)
        width:         连杆宽度（Y 方向）/ width along Y (mm)
        thickness:     连杆厚度（Z 方向）/ thickness along Z (mm)
        pivot_hole_r:  铰孔半径（默认 1.6 = M3 过孔）/ pivot hole radius
        pivot_offset:  铰孔距端部的距离 / pivot distance from each end
        end_fillet_r:  端部圆角半径（0 = 不倒圆）/ end fillet radius
        drill_pivots:  是否打通两端孔（False 时仅输出实心杆）/ whether to drill holes

    几何 / Geometry:
        - 原点 = 连杆几何中心，连杆沿 +X / -X 延伸 length/2
        - 铰孔轴向 = +Z（贯穿 thickness）
        - 铰孔中心 = (±(length/2 - pivot_offset), 0, 0)
    """
    if pivot_hole_r * 2 >= min(width, thickness):
        raise ValueError(
            f"pivot_hole_r*2 ({pivot_hole_r*2}) must be smaller than "
            f"min(width, thickness)=({min(width, thickness)})"
        )
    if pivot_offset >= length / 2:
        raise ValueError(
            f"pivot_offset ({pivot_offset}) must be < length/2 ({length/2})"
        )

    with BuildPart() as seg:
        with BuildSketch(Plane.XY):
            Rectangle(length, width)
        extrude(amount=thickness / 2, both=True)

        if end_fillet_r > 0:
            z_edges = seg.edges().filter_by(Axis.Z)
            fillet(z_edges, radius=end_fillet_r)

        if drill_pivots:
            top_face = seg.faces().sort_by(Axis.Z)[-1]
            with BuildSketch(top_face):
                with Locations(
                    Location(( length / 2 - pivot_offset, 0, 0)),
                    Location((-length / 2 + pivot_offset, 0, 0)),
                ):
                    Circle(pivot_hole_r)
            extrude(amount=-thickness, mode=Mode.SUBTRACT)

    return seg.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_leg_segment()
    export_step(p, "/tmp/leg_segment.step")
    print(f"OK: leg_segment, volume={p.volume:.1f} mm³, bbox={p.bounding_box().size}")
