"""ISO 54 / DIN 867 gear rack (straight-tooth rack) — industrial 3D-print quality.

Source: ISO 54 / DIN 867 involute gear tooth reference profile
Standards: ISO 54, DIN 867 (20° pressure angle, module system)
License: MIT

齿条 (Gear Rack) = 齿数 -> 无限大 的极限齿轮，齿廓退化为**直线梯形**。
    A rack is the limit case of a gear with infinite teeth — tooth flanks
    become straight lines inclined at the pressure angle (20° standard).

支持规格（module × length × width）：
  m1.0 x L100 x W10    — small 3D printer
  m1.0 x L200 x W10
  m1.5 x L150 x W12
  m2.0 x L100 x W15    — standard CNC / robot
  m2.0 x L200 x W15
  m2.0 x L300 x W15
  m2.5 x L200 x W20    — heavy-duty

简化程度: ★★★★★
- 真实梯形齿形(非方齿/非三角齿)，符合 20° 压力角标准
- 每齿单独 extrude + 融合基座(规避 OCP 非凸多边形渲染问题)
- 标准齿高 h=2.25m, 齿顶高 ha=m, 齿根高 hf=1.25m
- 可选 M3 沉头安装孔阵列
- 两端留半齿距余量避免端部断齿
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    Polygon,
    export_step,
)
from build123d import extrude as bd_extrude


class RackSpec(NamedTuple):
    module: float   # 模数 m (mm)
    length: float   # 齿条总长 (mm)
    width: float    # 齿面宽 (mm)
    base_h: float   # 齿根下基座厚度 (mm)


# 典型规格组合(工业级 3D 打印 / CNC 常用)
# Standard specs for 3D-printed and CNC gear racks.
_SPECS: list[RackSpec] = [
    RackSpec(module=1.0, length=100.0, width=10.0, base_h=5.0),
    RackSpec(module=1.0, length=200.0, width=10.0, base_h=5.0),
    RackSpec(module=1.5, length=150.0, width=12.0, base_h=6.0),
    RackSpec(module=2.0, length=100.0, width=15.0, base_h=8.0),
    RackSpec(module=2.0, length=200.0, width=15.0, base_h=8.0),
    RackSpec(module=2.0, length=300.0, width=15.0, base_h=8.0),
    RackSpec(module=2.5, length=200.0, width=20.0, base_h=10.0),
]

# 标准常量 / Standard constants
_M3_HOLE_D = 3.2         # M3 过孔直径 (mm)
_M3_CSK_D = 6.0          # M3 沉头孔直径 (mm)
_M3_CSK_DEPTH = 1.8      # M3 沉头深度 (mm)


def make_gear_rack(
    module: float = 2.0,
    length: float = 200.0,
    width: float = 15.0,
    base_h: float = 8.0,
    pressure_angle: float = 20.0,
    mounting_holes: bool = True,
) -> Part:
    """Generate an ISO 54 / DIN 867 straight-tooth gear rack.

    Args:
        module:         Module m (mm). Tooth size: pitch p = pi*m.
        length:         Total rack length along X (mm).
        width:          Face width along Y (mm).
        base_h:         Base plate thickness below tooth root (mm).
        pressure_angle: Pressure angle in degrees (standard 20°).
        mounting_holes: Whether to drill M3 countersunk mounting holes in base.

    Coordinate system:
        - Length along X axis, centered at origin (X in [-L/2, +L/2]).
        - Width along Y axis, centered at origin (Y in [-W/2, +W/2]).
        - Height along Z, Z=0 at base bottom, Z=base_h+2.25m at tooth tip.

    Geometry (ISO 54 standard tooth profile, m = module):
        - Pitch              p  = pi * m           齿距
        - Addendum           ha = m                齿顶高
        - Dedendum           hf = 1.25 * m         齿根高
        - Total tooth ht     h  = 2.25 * m         齿全高
        - Fillet radius     rf ~= 0.38 * m         齿根圆角 (此处简化为直线梯形)
        - Tooth tip width   = p/2 - 2*ha*tan(a)   齿顶宽
        - Tooth root width  = p/2 + 2*hf*tan(a)   齿根宽

    Returns:
        Part: Gear rack solid (base plate + trapezoidal teeth array).
    """
    # ── 参数校验 / Parameter validation ──
    if module <= 0 or length <= 0 or width <= 0 or base_h <= 0:
        raise ValueError("module/length/width/base_h 均须 > 0")
    if not (5.0 <= pressure_angle <= 30.0):
        raise ValueError(f"pressure_angle={pressure_angle}° 超出合理范围 [5,30]")
    if mounting_holes and base_h < _M3_CSK_DEPTH + 1.0:
        raise ValueError(
            f"base_h={base_h} 太薄, 无法容纳 M3 沉头孔 "
            f"(需 >= {_M3_CSK_DEPTH + 1.0}mm)"
        )

    # ── 标准齿形参数 / Standard tooth profile dimensions ──
    p = math.pi * module                  # 齿距 / pitch
    ha = module                           # 齿顶高 / addendum
    hf = 1.25 * module                    # 齿根高 / dedendum
    alpha = math.radians(pressure_angle)  # 压力角(弧度) / pressure angle
    tan_a = math.tan(alpha)

    # 齿顶宽、齿根宽(梯形上下底长度)
    # Tip width and root width of the trapezoidal tooth.
    tooth_tip_w = p / 2 - 2 * ha * tan_a          # 齿顶宽
    tooth_root_w = p / 2 + 2 * hf * tan_a         # 齿根宽
    h_tooth = ha + hf                             # 齿全高 = 2.25 * m

    # ── 齿数: 两端各留 p/2 余量避免断齿 ──
    # Number of teeth: leave >= p/2 margin on each end to avoid partial teeth.
    usable = length - p
    if usable <= p:
        raise ValueError(
            f"length={length} 对 m={module} 太短 (需 > 2*p = {2*p:.2f})"
        )
    n_teeth = int(usable // p) + 1
    teeth_span = n_teeth * p
    first_center_x = -teeth_span / 2 + p / 2  # 首齿中心 X (齿列居中)

    # ── 建模 / Build geometry ──
    # 基座: Z in [0, base_h], 齿根线位于 Z = base_h
    # 齿  : 完整梯形 h_tooth = 2.25m, 从 Z=base_h 延伸到 Z=base_h+h_tooth
    with BuildPart() as rack:
        # 1. 底板 / Base plate
        Box(
            length=length,
            width=width,
            height=base_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )

        # 2. 沿 X 方向阵列齿形(每齿单独 extrude 避免非凸多边形)
        #    Extrude each tooth individually as a trapezoidal prism on XZ plane,
        #    then extrude ±W/2 along Y (symmetric) to span the full face width.
        for i in range(n_teeth):
            cx = first_center_x + i * p        # 当前齿中心 X
            x_root_l = cx - tooth_root_w / 2   # 齿根左 / root left
            x_root_r = cx + tooth_root_w / 2   # 齿根右 / root right
            x_tip_l = cx - tooth_tip_w / 2     # 齿顶左 / tip left
            x_tip_r = cx + tooth_tip_w / 2     # 齿顶右 / tip right

            with BuildSketch(Plane.XZ):
                # 梯形四顶点(逆时针) / trapezoid vertices (CCW)
                Polygon(
                    (x_root_l, base_h),             # 左下 / bottom-left
                    (x_root_r, base_h),             # 右下 / bottom-right
                    (x_tip_r, base_h + h_tooth),    # 右上 / top-right
                    (x_tip_l, base_h + h_tooth),    # 左上 / top-left
                    align=None,
                )
            # 对称双向 extrude ±width/2 -> 覆盖整个齿面宽度, Y 居中
            bd_extrude(amount=width / 2, both=True)

        # 3. 可选 M3 沉头安装孔阵列 / Optional M3 countersunk mounting holes
        if mounting_holes:
            hole_margin_x = max(8.0, p)           # 端部余量 >= p 或 8mm
            hole_margin_y = min(4.0, width / 4)   # Y 方向离边 4mm
            hole_span = length - 2 * hole_margin_x
            if hole_span > 20.0:
                n_holes = max(2, int(hole_span / 50.0) + 1)
                dx = hole_span / (n_holes - 1)
                y_off = width / 2 - hole_margin_y
                use_two_rows = width >= 10.0   # 宽度足够时开双排孔
                for i in range(n_holes):
                    x = -hole_span / 2 + i * dx
                    ys = [-y_off, +y_off] if use_two_rows else [0.0]
                    for y in ys:
                        # 贯穿过孔 / through-hole
                        with Locations(Location((x, y, 0))):
                            Cylinder(
                                radius=_M3_HOLE_D / 2,
                                height=base_h + 0.2,
                                align=(Align.CENTER, Align.CENTER, Align.MIN),
                                mode=Mode.SUBTRACT,
                            )
                        # 底面沉头窝 / bottom-side countersink
                        with Locations(Location((x, y, 0))):
                            Cylinder(
                                radius=_M3_CSK_D / 2,
                                height=_M3_CSK_DEPTH,
                                align=(Align.CENTER, Align.CENTER, Align.MIN),
                                mode=Mode.SUBTRACT,
                            )

    return rack.part


if __name__ == "__main__":
    # Smoke-test / 冒烟断言（不写 cache；cache 由 scripts/build_cache.py 统一生成）
    print("Gear Rack (ISO 54 / DIN 867) — smoke test")
    for spec in _SPECS:
        part = make_gear_rack(
            module=spec.module,
            length=spec.length,
            width=spec.width,
            base_h=spec.base_h,
        )
        assert part.is_valid, f"m{spec.module} L{spec.length}: BRep invalid"
        assert len(part.solids()) == 1, (
            f"m{spec.module} L{spec.length}: not single solid"
        )
        bb = part.bounding_box()
        # 总高 = base_h + 2.25·m
        h_expected = spec.base_h + 2.25 * spec.module
        assert abs(bb.size.Z - h_expected) < 0.5, (
            f"m{spec.module}: Z={bb.size.Z:.2f} vs expected {h_expected:.2f}"
        )
        p = math.pi * spec.module
        n_teeth = int((spec.length - p) // p) + 1
        print(
            f"OK  rack m{spec.module} L{spec.length} W{spec.width}:  "
            f"bbox={bb.size.X:6.1f}x{bb.size.Y:5.1f}x{bb.size.Z:5.1f}mm  "
            f"teeth={n_teeth:3d}  vol={part.volume:.1f} mm3"
        )
