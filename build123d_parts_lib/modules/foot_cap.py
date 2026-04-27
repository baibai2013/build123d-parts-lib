"""通用脚垫（机器人末端接触点）/ Generic foot cap for robotic contact point.

半球形脚垫，顶部可选带一段圆柱杆柄（插入腿段末端用）。
Hemispherical foot with optional top shaft for mounting into a leg segment.

常见用途 / Typical use:
    - 四足机器人足端
    - 六足/八足 robot 足部减震/吸附点
    - 桌面设备的橡胶垫（用 TPU 打印）

Source: build123d-cad-skill-test/tests/23-quadruped-leg-2dof
License: MIT
"""
from __future__ import annotations

from build123d import (
    BuildPart, Sphere, Cylinder, Box, Plane, Part, Mode, Location, Locations,
    Align, Axis,
)


def make_foot_cap(
    radius: float = 8.0,
    shaft_d: float = 3.0,
    shaft_length: float = 6.0,
    flatten_bottom: bool = False,
) -> Part:
    """生成带柄半球脚垫 / Hemisphere with a mounting shaft on top.

    Args:
        radius:          半球半径 / hemisphere radius (mm)
        shaft_d:         顶部圆柱杆柄直径（M3 = 3.0）/ top shaft diameter
        shaft_length:    杆柄长度 / shaft length (mm)
        flatten_bottom:  True 则把底部切平（更稳定的站立面）
                         / if True, flatten the bottom for better standing contact

    几何 / Geometry:
        - 原点 = 脚垫顶面中心（杆柄根部），半球向 -Z 下伸
        - Origin at the top of the cap (shaft root); hemisphere extends toward -Z
        - 杆柄沿 +Z 向上 / shaft extends along +Z

    Returns:
        Part: 半球 + 杆柄（布尔 union）
    """
    if radius <= 0 or shaft_d <= 0 or shaft_length < 0:
        raise ValueError("radius / shaft_d / shaft_length must be positive")
    if shaft_d >= radius * 2:
        raise ValueError(
            f"shaft_d ({shaft_d}) must be smaller than 2*radius ({2*radius})"
        )

    with BuildPart() as cap:
        sphere = Sphere(radius)
        # 切掉上半球（只留 -Z 半球） / cut upper half, keep -Z hemisphere
        Box(
            2 * radius, 2 * radius, radius,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        if flatten_bottom:
            # 切掉最底部 10%，生成平面站立面 / flatten bottom 10% for stable standing
            flat_h = radius * 0.1
            with Locations(Location((0, 0, -radius))):
                Box(
                    2 * radius, 2 * radius, flat_h,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                    mode=Mode.SUBTRACT,
                )

        if shaft_length > 0:
            Cylinder(
                radius=shaft_d / 2,
                height=shaft_length,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )

    return cap.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_foot_cap()
    export_step(p, "/tmp/foot_cap.step")
    print(f"OK: foot_cap, volume={p.volume:.1f} mm³, bbox={p.bounding_box().size}")
