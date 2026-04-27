"""Smoke tests for templates/ (project starters)."""
from build123d_parts_lib.templates.pcb_enclosure import make_pcb_enclosure
from build123d_parts_lib.templates.sg90_bracket import make_sg90_bracket


def test_sg90_bracket_default():
    p = make_sg90_bracket()
    assert p is not None
    assert p.is_valid
    # 有合理体积（塑料件大致在几千 mm³ 量级）
    assert 1000 < p.volume < 20000


def test_sg90_bracket_custom_wall():
    p_thin = make_sg90_bracket(wall_thickness=1.5)
    p_thick = make_sg90_bracket(wall_thickness=4.0)
    # 墙更厚 → 外壳更大 → 体积更大（内腔不变）
    assert p_thick.volume > p_thin.volume


def test_pcb_enclosure_small_pcb():
    p = make_pcb_enclosure(pcb_length=50, pcb_width=30)
    assert p is not None
    assert p.is_valid
    bb = p.bounding_box().size
    # 外壳尺寸 = pcb + 2*clearance + 2*wall = 50 + 2*1 + 2*2 = 56
    assert abs(bb.X - 56.0) < 0.5
    assert abs(bb.Y - 36.0) < 0.5


def test_pcb_enclosure_larger_pcb():
    p = make_pcb_enclosure(pcb_length=100, pcb_width=60)
    assert p.is_valid
    bb = p.bounding_box().size
    assert bb.X > 100
    assert bb.Y > 60
