"""Smoke tests for parts/ (standard part entities)."""
from build123d_parts_lib.parts.fasteners.m3_iso4762 import make_m3_screw
from build123d_parts_lib.parts.servos.sg90 import make_sg90


def test_m3_screw_imports_and_builds():
    p = make_m3_screw()
    assert p is not None
    assert p.is_valid
    # 合理体积范围：L10 头+杆 约 ~140 mm³
    assert 50 < p.volume < 300, f"M3 screw volume out of range: {p.volume}"


def test_m3_screw_custom_length():
    p_short = make_m3_screw(length=5)
    p_long = make_m3_screw(length=20)
    assert p_long.volume > p_short.volume


def test_sg90_imports_and_builds():
    p = make_sg90()
    assert p is not None
    assert p.is_valid
    # SG90 bbox 期望：32.2 × 12.2 × 27.7（含耳 + 输出轴）
    bb = p.bounding_box().size
    assert abs(bb.X - 32.2) < 0.5
    assert abs(bb.Y - 12.2) < 0.5
    assert abs(bb.Z - 27.7) < 0.5
