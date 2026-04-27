"""Smoke tests for modules/ (functional multi-part combinations)."""
from build123d_parts_lib.modules.snap_fit_latch import make_snap_latch
from build123d_parts_lib.modules.threaded_insert_boss import make_m3_boss


def test_m3_boss_default():
    p = make_m3_boss()
    assert p.is_valid
    bb = p.bounding_box().size
    # 默认 boss_outer_d=5.5, height=7
    assert abs(bb.X - 5.5) < 0.1
    assert abs(bb.Y - 5.5) < 0.1
    assert abs(bb.Z - 7.0) < 0.1


def test_m3_boss_invalid_dimension():
    import pytest
    with pytest.raises(ValueError):
        make_m3_boss(predrill_d=5.0, boss_outer_d=4.0)


def test_snap_latch_default():
    p = make_snap_latch()
    assert p.is_valid
    bb = p.bounding_box().size
    # 默认 length=12, width=4, thickness=1.2, hook=0.8
    # X 方向总长 = length = 12
    assert abs(bb.X - 12.0) < 0.1
    assert abs(bb.Y - 4.0) < 0.1


def test_snap_latch_invalid_hook():
    import pytest
    with pytest.raises(ValueError):
        make_snap_latch(thickness=1.0, hook_size=1.5)   # hook 必须 < thickness
