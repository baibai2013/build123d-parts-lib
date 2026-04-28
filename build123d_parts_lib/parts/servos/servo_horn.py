"""25T servo horn (摇臂) for standard hobby servos (simplified).

Types: single / double / cross / disc

License: MIT

几何说明：
- hub：外径 7mm 圆柱（高 4mm）+ 中心孔 5mm（贯穿）
- 臂/盘厚 2mm，叠加在 hub 顶面（Z=4 起）
- 摇臂孔 / 盘上均布孔 直径 1.5mm
- 原点在 hub 底面中心，Z 向上
"""
from __future__ import annotations

from math import cos, pi, sin
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Rectangle,
    export_step,
    extrude,
)


class HornSpec(NamedTuple):
    hub_od: float       # hub 外径
    center_bore: float  # 中心孔径
    hub_h: float        # hub 高度
    arm_t: float        # 臂/盘厚度
    arm_len: float      # 臂长（从 hub 边缘算起）
    arm_w: float        # 臂宽
    hole_d: float       # 末端/均布孔直径
    n_arms: int         # 臂数量（disc 时为 0）
    disc_od: float      # 圆盘外径（仅 disc 有效，其余为 0）
    disc_pcd: float     # 盘孔分布圆直径（仅 disc）
    n_disc_holes: int   # 盘上孔数（仅 disc）


_SPECS: dict[str, HornSpec] = {
    "single": HornSpec(
        hub_od=7.0, center_bore=5.0, hub_h=4.0,
        arm_t=2.0, arm_len=15.0, arm_w=4.0,
        hole_d=1.5, n_arms=1,
        disc_od=0.0, disc_pcd=0.0, n_disc_holes=0,
    ),
    "double": HornSpec(
        hub_od=7.0, center_bore=5.0, hub_h=4.0,
        arm_t=2.0, arm_len=15.0, arm_w=4.0,
        hole_d=1.5, n_arms=2,
        disc_od=0.0, disc_pcd=0.0, n_disc_holes=0,
    ),
    "cross": HornSpec(
        hub_od=7.0, center_bore=5.0, hub_h=4.0,
        arm_t=2.0, arm_len=15.0, arm_w=3.0,
        hole_d=1.5, n_arms=4,
        disc_od=0.0, disc_pcd=0.0, n_disc_holes=0,
    ),
    "disc": HornSpec(
        hub_od=7.0, center_bore=5.0, hub_h=4.0,
        arm_t=2.0, arm_len=0.0, arm_w=0.0,
        hole_d=1.5, n_arms=0,
        disc_od=20.0, disc_pcd=15.0, n_disc_holes=4,
    ),
}


def make_servo_horn(type_: str = "single") -> Part:
    """生成 25T 舵机摇臂简化实体。

    Args:
        type_: 类型字符串：'single' / 'double' / 'cross' / 'disc'。

    坐标：
        - 原点在 hub 底面中心
        - Z 向上，hub 底面在 Z=0
    """
    key = type_.lower()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知摇臂类型 {type_!r}，可用类型：{available}")

    s = _SPECS[key]
    hub_r = s.hub_od / 2
    bore_r = s.center_bore / 2
    arm_base_x = hub_r  # 臂从 hub 边缘起点的 X

    with BuildPart() as horn:
        # ── hub 主体（Z=0 底面，向上 hub_h）──
        Cylinder(
            radius=hub_r, height=s.hub_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 中心孔（贯穿 hub）
        Cylinder(
            radius=bore_r, height=s.hub_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        arm_plane = Plane.XY.offset(s.hub_h)

        if key == "disc":
            # ── 圆盘：盖在 hub 顶面 ──
            disc_r = s.disc_od / 2
            with BuildSketch(arm_plane):
                Circle(disc_r)
                # 中心孔
                Circle(bore_r, mode=Mode.SUBTRACT)
            extrude(amount=s.arm_t)

            # 均布孔
            pcd_r = s.disc_pcd / 2
            hole_r = s.hole_d / 2
            disc_top = arm_plane.offset(s.arm_t)
            with BuildSketch(disc_top):
                n = s.n_disc_holes
                for i in range(n):
                    angle = 2 * pi * i / n
                    cx = pcd_r * cos(angle)
                    cy = pcd_r * sin(angle)
                    with Locations((cx, cy)):
                        Circle(hole_r)
            extrude(amount=-s.arm_t, mode=Mode.SUBTRACT)

        else:
            # ── 带臂类型：均匀分布 n_arms 个臂 ──
            n = s.n_arms
            arm_half_w = s.arm_w / 2
            arm_total_len = arm_base_x + s.arm_len  # 从中心到末端
            hole_r = s.hole_d / 2

            for i in range(n):
                angle_deg = 360.0 * i / n
                angle_rad = 2 * pi * i / n

                # 臂的局部坐标：沿 +X 方向，以 Location 旋转
                with BuildSketch(arm_plane):
                    with Locations(
                        Location((0, 0, 0), (0, 0, 1), angle_deg)
                    ):
                        # 矩形臂（从中心 0 延伸到 arm_total_len）
                        # 矩形中心在 arm_total_len/2 处
                        with Locations((arm_total_len / 2, 0)):
                            Rectangle(arm_total_len, s.arm_w)
                extrude(amount=s.arm_t)

            # 补 hub 顶面圆（盖住臂根部缝隙）
            with BuildSketch(arm_plane):
                Circle(hub_r)
            extrude(amount=s.arm_t)

            # 再次减去中心孔
            Cylinder(
                radius=bore_r, height=s.hub_h + s.arm_t,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
                mode=Mode.SUBTRACT,
            )

            # 末端小孔
            arm_top = arm_plane.offset(s.arm_t)
            for i in range(n):
                angle_deg = 360.0 * i / n
                ex = arm_total_len * cos(2 * pi * i / n)
                ey = arm_total_len * sin(2 * pi * i / n)
                with BuildSketch(arm_top):
                    with Locations((ex, ey)):
                        Circle(hole_r)
                extrude(amount=-s.arm_t, mode=Mode.SUBTRACT)

    return horn.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for type_name in _SPECS:
        part = make_servo_horn(type_name)
        slug = f"servo_horn_{type_name}"
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(f"OK: {out_path.name}  "
              f"{bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f}mm  "
              f"vol={part.volume:.1f} mm3")
