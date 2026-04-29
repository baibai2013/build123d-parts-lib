"""transmission package — 传动件标准库.

Factories（对外导出的 make_* 函数）：

- 同步传动（GT2）
    make_gt2_pulley, make_gt2_belt

- 平键（ISO 2491 / DIN 6885A）
    make_parallel_key

- 齿轮族（ISO 54 / DIN 867 / ISO 23509 / ISO 1122）
    make_spur_gear        直齿轮 Spur Gear
    make_gear_rack        齿条 Gear Rack
    make_helical_gear     斜齿轮 Helical Gear
    make_bevel_gear       锥齿轮 Bevel Gear
    make_worm             蜗杆 Worm
    make_worm_wheel       蜗轮 Worm Wheel
    make_internal_gear    内齿圈 Internal / Ring Gear

Cache 规范：每个 factory 一个代表 <slug>.step + <slug>.png，
统一由 `scripts/build_cache.py` 生成（VTK 后端离屏渲染，不依赖 OCP Viewer）。
"""
from build123d_parts_lib.parts.transmission.bevel_gear import make_bevel_gear
from build123d_parts_lib.parts.transmission.gear_rack import make_gear_rack
from build123d_parts_lib.parts.transmission.helical_gear import make_helical_gear
from build123d_parts_lib.parts.transmission.internal_gear import make_internal_gear
from build123d_parts_lib.parts.transmission.key_parallel import make_parallel_key
from build123d_parts_lib.parts.transmission.spur_gear import make_spur_gear
from build123d_parts_lib.parts.transmission.timing_belt_gt2 import make_gt2_belt
from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import make_gt2_pulley
from build123d_parts_lib.parts.transmission.worm_gear import make_worm, make_worm_wheel

__all__ = [
    # timing belt / pulley
    "make_gt2_belt",
    "make_gt2_pulley",
    # keys
    "make_parallel_key",
    # gear family
    "make_spur_gear",
    "make_gear_rack",
    "make_helical_gear",
    "make_bevel_gear",
    "make_worm",
    "make_worm_wheel",
    "make_internal_gear",
]
