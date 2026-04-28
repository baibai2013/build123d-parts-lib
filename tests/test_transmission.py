"""Transmission parts smoke tests — GT2 timing pulleys, parallel keys.
传动件冒烟测试 — GT2 同步带轮、平键。

Tests cover:
  - GT2 带轮构建有效性 + 齿数/外径正确 / GT2 pulley validity + tooth count / OD check
  - 平键构建有效性 + 几何尺寸正确 / parallel key validity + dimension check
  - 非法参数报错 / invalid-parameter error raising
"""
import math

import pytest

from build123d_parts_lib.parts.transmission.key_parallel import make_parallel_key
from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import (
    _PITCH,
    make_gt2_pulley,
)

# ── GT2 同步带轮测试 / GT2 timing pulley tests ───────────────────────────

def test_gt2_pulley_default():
    """默认参数 20T ⌀5 构建，实体有效，节径/外径符合 GT2 公式。
    Default 20T ⌀5 build: valid solid, pitch/OD match GT2 formula.
    """
    # 调用默认参数构建 / build with default args
    part = make_gt2_pulley(teeth=20, bore_d=5.0)

    assert part is not None
    assert part.is_valid, "GT2 pulley 20T bore5 should produce a valid solid"
    assert part.volume > 0

    # 节径 = teeth * pitch / π / pitch diameter = teeth * pitch / π
    pitch_d = 20 * _PITCH / math.pi  # ≈ 12.732 mm
    # 外径 = pitch_d - 0.508 / OD = pitch_d - 2*0.254
    od = pitch_d - 0.254 * 2         # ≈ 12.224 mm
    # 法兰外径 = od + 2.5 / flange OD = od + 2.5
    flange_od = od + 2.5              # ≈ 14.724 mm

    # bounding box X ≈ flange_od（带法兰）/ bbox X ≈ flange_od (with flanges)
    bb = part.bounding_box()
    assert abs(bb.size.X - flange_od) < 0.2, (
        f"20T flange OD: expected ≈{flange_od:.3f}, got {bb.size.X:.3f}"
    )

    # 总高 = 8.0mm（法兰 1mm × 2 + 带宽 6mm）/ total height = 8.0 mm
    assert abs(bb.size.Z - 8.0) < 0.1, (
        f"20T total height: expected 8.0, got {bb.size.Z:.3f}"
    )


def test_gt2_pulley_16t_bore8():
    """16T ⌀8 构建，实体有效，尺寸合理。
    16T bore-8 build: valid solid, reasonable dimensions.
    """
    part = make_gt2_pulley(teeth=16, bore_d=8.0)

    assert part is not None
    assert part.is_valid, "GT2 pulley 16T bore8 should be valid"

    # 16T 节径 ≈ 10.186mm，外径 ≈ 9.678mm，法兰外径 ≈ 12.178mm
    # 16T pitch_d ≈ 10.186 mm, OD ≈ 9.678 mm, flange OD ≈ 12.178 mm
    pitch_d = 16 * _PITCH / math.pi
    flange_od = (pitch_d - 0.508) + 2.5
    bb = part.bounding_box()
    assert abs(bb.size.X - flange_od) < 0.2, (
        f"16T bore8 flange OD: expected ≈{flange_od:.3f}, got {bb.size.X:.3f}"
    )


def test_gt2_pulley_40t_bore5():
    """40T ⌀5 构建，体积应大于 20T ⌀5（更多材料）。
    40T bore-5 build: volume should exceed 20T bore-5 (more material).
    """
    part_20t = make_gt2_pulley(teeth=20, bore_d=5.0)
    part_40t = make_gt2_pulley(teeth=40, bore_d=5.0)

    assert part_40t.is_valid
    # 40T 外径更大，体积更大 / 40T has larger OD, so larger volume
    assert part_40t.volume > part_20t.volume, (
        f"40T vol={part_40t.volume:.2f} should > 20T vol={part_20t.volume:.2f}"
    )


def test_gt2_pulley_invalid_bore_too_large():
    """孔径超过外径时必须抛出 ValueError。
    Must raise ValueError when bore_d exceeds OD.
    """
    # 16T 外径约 9.678mm，孔径 10mm > 外径 / 16T OD ≈ 9.678 mm, bore=10 > OD
    with pytest.raises(ValueError):
        make_gt2_pulley(teeth=16, bore_d=10.0)


# ── 平键测试 / parallel key tests ────────────────────────────────────────

def test_parallel_key_default():
    """默认参数 5×5 L20 构建，实体有效，几何尺寸正确。
    Default 5×5 L20 build: valid solid, correct geometry.
    """
    # 调用默认参数 / build with standard 5×5 L20 key
    part = make_parallel_key(width=5.0, height=5.0, length=20.0)

    assert part is not None
    assert part.is_valid, "Parallel key 5x5 L20 should produce a valid solid"
    assert part.volume > 0

    bb = part.bounding_box()
    # 键长沿 X 轴 / key length along X axis
    assert abs(bb.size.X - 20.0) < 0.15, (
        f"Key length: expected 20.0, got {bb.size.X:.3f}"
    )
    # 键宽沿 Y 轴 / key width along Y axis
    assert abs(bb.size.Y - 5.0) < 0.15, (
        f"Key width: expected 5.0, got {bb.size.Y:.3f}"
    )
    # 键高沿 Z 轴 / key height along Z axis
    assert abs(bb.size.Z - 5.0) < 0.15, (
        f"Key height: expected 5.0, got {bb.size.Z:.3f}"
    )


def test_parallel_key_3x3():
    """3×3 L12 平键，实体有效，体积小于 5×5 L20。
    3×3 L12 key: valid solid, volume smaller than 5×5 L20.
    """
    part_small = make_parallel_key(width=3.0, height=3.0, length=12.0)
    part_large = make_parallel_key(width=5.0, height=5.0, length=20.0)

    assert part_small.is_valid
    # 小键体积应小于大键 / smaller key should have smaller volume
    assert part_small.volume < part_large.volume, (
        f"3x3 L12 vol={part_small.volume:.2f} should < 5x5 L20 vol={part_large.volume:.2f}"
    )


def test_parallel_key_8x7():
    """8×7 L32 大键，实体有效，尺寸正确。
    8×7 L32 large key: valid solid, correct dimensions.
    """
    part = make_parallel_key(width=8.0, height=7.0, length=32.0)

    assert part is not None
    assert part.is_valid, "Parallel key 8x7 L32 should be valid"

    bb = part.bounding_box()
    # 键长 / length
    assert abs(bb.size.X - 32.0) < 0.15, (
        f"8x7 key length: expected 32.0, got {bb.size.X:.3f}"
    )
    # 键高（高 ≠ 宽，7mm）/ height (h ≠ w, 7 mm)
    assert abs(bb.size.Z - 7.0) < 0.15, (
        f"8x7 key height: expected 7.0, got {bb.size.Z:.3f}"
    )


def test_parallel_key_invalid_short():
    """键长小于键宽时必须抛出 ValueError。
    Must raise ValueError when length < width.
    """
    # 键长 3mm < 键宽 5mm / length=3 < width=5 should raise
    with pytest.raises(ValueError):
        make_parallel_key(width=5.0, height=5.0, length=3.0)


def test_parallel_key_invalid_zero():
    """零尺寸必须抛出 ValueError。
    Zero dimensions must raise ValueError.
    """
    with pytest.raises(ValueError):
        make_parallel_key(width=0.0, height=5.0, length=20.0)
