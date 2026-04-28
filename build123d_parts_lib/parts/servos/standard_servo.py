"""Standard hobby servo motors (simplified).

Supported models: SG90 / MG90S / MG996R / DS3218

Source: data-sources/servos.yaml (skill build123d-cad)
License: MIT

简化程度：
- 主体箱 + 两侧耳朵凸缘（含安装孔）+ 输出轴（含 25T 花键齿）
- 不建模线缆
- 足够装配定位与 bbox 占位
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    Rectangle,
    export_step,
    extrude,
)


class ServoSpec(NamedTuple):
    body_l: float        # X 长
    body_w: float        # Y 宽
    body_h: float        # Z 高（不含输出轴）
    ear_w_total: float   # 含两侧耳朵总宽
    ear_t: float         # 耳朵板厚
    ear_z: float         # 耳朵中面到底面距离
    screw_hole_d: float  # 耳朵安装孔直径（M2 / M3）
    screw_pitch: float   # 两侧耳朵孔中心横向距
    shaft_r: float       # 输出轴半径（花键齿顶半径）
    shaft_h: float       # 输出轴高出主体顶面距离
    spline_teeth: int = 25   # 花键齿数（hobby 舵机标准 25T）


# 参数表（与 data-sources/servos.yaml 对应）
_SPECS: dict[str, ServoSpec] = {
    "SG90":   ServoSpec(body_l=22.8, body_w=12.2, body_h=22.7,
                        ear_w_total=32.2, ear_t=2.5, ear_z=15.5,
                        screw_hole_d=2.0, screw_pitch=28.0,
                        shaft_r=2.5, shaft_h=5.0),
    "MG90S":  ServoSpec(body_l=22.8, body_w=12.2, body_h=28.5,
                        ear_w_total=32.2, ear_t=2.5, ear_z=15.5,
                        screw_hole_d=2.0, screw_pitch=28.0,
                        shaft_r=2.5, shaft_h=2.5),
    "MG996R": ServoSpec(body_l=40.7, body_w=19.7, body_h=42.9,
                        ear_w_total=54.0, ear_t=4.0, ear_z=27.8,
                        screw_hole_d=3.0, screw_pitch=49.5,
                        shaft_r=3.5, shaft_h=5.6),
    "DS3218": ServoSpec(body_l=40.0, body_w=20.0, body_h=40.5,
                        ear_w_total=54.0, ear_t=4.0, ear_z=27.0,
                        screw_hole_d=3.0, screw_pitch=49.5,
                        shaft_r=3.5, shaft_h=4.5),
}


def _spline_profile(outer_r: float, inner_r: float, teeth: int):
    """生成花键齿截面多边形点列：齿顶/齿根交替均布。"""
    pts = []
    for i in range(teeth):
        # 每齿占 2π/teeth 角度，齿顶在 i+0.25、齿根在 i+0.75
        a_outer = 2 * math.pi * (i + 0.25) / teeth
        a_inner = 2 * math.pi * (i + 0.75) / teeth
        pts.append((outer_r * math.cos(a_outer), outer_r * math.sin(a_outer)))
        pts.append((inner_r * math.cos(a_inner), inner_r * math.sin(a_inner)))
    return pts


def make_servo(model: str = "SG90") -> Part:
    """生成标准舵机简化实体（主体 + 带孔耳朵 + 花键输出轴）。

    Args:
        model: 型号字符串，如 "SG90"、"MG996R"。大小写不敏感。

    坐标：
        - 原点在主体几何中心（XY），Z=0 为底面
        - 主体沿 Z 轴向上延伸
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知型号 {model!r}，可用型号：{available}")

    s = _SPECS[key]
    # 输出轴位置（偏向主体长边一侧，经验偏移量 0.3*body_l）
    shaft_offset_x = s.body_l * 0.3 - s.body_l / 2

    # 花键齿几何
    tooth_depth = max(s.shaft_r * 0.12, 0.25)    # 齿深约占半径 12%
    spline_outer_r = s.shaft_r
    spline_inner_r = s.shaft_r - tooth_depth
    spline_pts = _spline_profile(spline_outer_r, spline_inner_r, s.spline_teeth)

    with BuildPart() as servo:
        # 主体
        with BuildSketch(Plane.XY):
            Rectangle(s.body_l, s.body_w)
        extrude(amount=s.body_h)

        # 耳朵凸缘
        ear_plane = Plane.XY.offset(s.ear_z - s.ear_t / 2)
        with BuildSketch(ear_plane):
            Rectangle(s.ear_w_total, s.body_w)
            Rectangle(s.body_l, s.body_w, mode=Mode.SUBTRACT)
        extrude(amount=s.ear_t)

        # 耳朵安装孔（两侧各 1 个 M2/M3 孔，穿透耳朵）
        hole_plane = Plane.XY.offset(s.ear_z + s.ear_t / 2)
        with BuildSketch(hole_plane):
            with Locations(
                (-s.screw_pitch / 2, 0),
                ( s.screw_pitch / 2, 0),
            ):
                Circle(s.screw_hole_d / 2)
        extrude(amount=-s.ear_t, mode=Mode.SUBTRACT)

        # 输出轴底部光滑过渡段（0.8 mm 无齿圆柱，代表齿底部根基）
        base_h = min(0.8, s.shaft_h * 0.25)
        top_face = servo.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top_face):
            with Locations((shaft_offset_x, 0)):
                Circle(s.shaft_r)
        extrude(amount=base_h)

        # 25T 花键齿部分
        spline_plane = Plane.XY.offset(s.body_h + base_h)
        with BuildSketch(spline_plane):
            with Locations((shaft_offset_x, 0)):
                Polygon(*spline_pts)
        extrude(amount=s.shaft_h - base_h)

    return servo.part


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for model_name in _SPECS:
        part = make_servo(model_name)
        slug = model_name.lower()
        out_path = cache_dir / f"{slug}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        print(f"OK: {out_path.name}  "
              f"{bb.size.X:.1f}x{bb.size.Y:.1f}x{bb.size.Z:.1f}mm  "
              f"vol={part.volume:.1f} mm3")
