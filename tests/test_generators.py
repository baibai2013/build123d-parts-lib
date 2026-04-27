"""Smoke tests for generators/ (parametric helpers)."""
import pytest

from build123d_parts_lib.generators.clearance import get_clearance_diameter


def test_clearance_m3_defaults():
    assert get_clearance_diameter("M3") == 3.4        # medium default
    assert get_clearance_diameter("M3", "close") == 3.2
    assert get_clearance_diameter("M3", "loose") == 3.6


def test_clearance_case_insensitive():
    assert get_clearance_diameter("m3") == 3.4
    assert get_clearance_diameter("M3") == 3.4


def test_clearance_unknown_size():
    with pytest.raises(ValueError):
        get_clearance_diameter("M99")


def test_clearance_unknown_fit():
    with pytest.raises(ValueError):
        get_clearance_diameter("M3", "super-tight")


def test_vents_import():
    # vents.make_vent_pattern 需要 face 参数，单独测试 import 即可
    from build123d_parts_lib.generators.vents import make_vent_pattern
    assert callable(make_vent_pattern)
