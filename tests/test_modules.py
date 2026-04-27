"""Smoke tests for modules/ (functional multi-part combinations)."""
from build123d_parts_lib.modules.snap_fit_latch import make_snap_latch
from build123d_parts_lib.modules.threaded_insert_boss import make_m3_boss
from build123d_parts_lib.modules.leg_segment import make_leg_segment
from build123d_parts_lib.modules.foot_cap import make_foot_cap


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


def test_leg_segment_default():
    p = make_leg_segment()
    assert p.is_valid
    bb = p.bounding_box().size
    # 默认 length=60, width=10, thickness=4
    assert abs(bb.X - 60.0) < 0.1, f"X {bb.X} != 60"
    assert abs(bb.Y - 10.0) < 0.1, f"Y {bb.Y} != 10"
    assert abs(bb.Z - 4.0) < 0.1,  f"Z {bb.Z} != 4"


def test_leg_segment_no_drill():
    p = make_leg_segment(drill_pivots=False)
    assert p.is_valid
    # 不打孔时体积 ≥ 带孔版本
    p_drilled = make_leg_segment(drill_pivots=True)
    assert p.volume > p_drilled.volume


def test_leg_segment_invalid_pivot():
    import pytest
    with pytest.raises(ValueError):
        make_leg_segment(pivot_hole_r=6.0, width=10, thickness=4)  # 孔径 > 宽度


def test_foot_cap_default():
    p = make_foot_cap()
    assert p.is_valid
    bb = p.bounding_box().size
    # 默认 radius=8, shaft_d=3, shaft_length=6
    assert abs(bb.X - 16.0) < 0.1   # 2*radius
    assert abs(bb.Y - 16.0) < 0.1
    # Z: -radius (半球最低) 到 +shaft_length (杆柄顶)
    assert abs(bb.Z - (8.0 + 6.0)) < 0.1


def test_foot_cap_flat_bottom():
    p = make_foot_cap(flatten_bottom=True)
    assert p.is_valid
    # 切平底部后高度减少 radius * 0.1
    bb = p.bounding_box().size
    assert abs(bb.Z - (8.0 + 6.0 - 0.8)) < 0.1


def test_foot_cap_invalid_shaft():
    import pytest
    with pytest.raises(ValueError):
        make_foot_cap(radius=3.0, shaft_d=8.0)  # shaft_d > 2*radius
