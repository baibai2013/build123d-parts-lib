"""O-ring / O型圈 smoke tests — ISO 3601-1 / GB/T 3452.1.

Tests cover:
  - 默认参数构建 / default parameter build
  - 小规格构建 / small-size build
  - YAML 规格表参数化遍历 / parametric sweep over YAML specs
  - 非法参数报错 / invalid-parameter error raising
"""
import pytest

from build123d_parts_lib.parts.seals.oring import _SPECS, make_oring

# ── 辅助常量 / helper constants ──────────────────────────────────────────

# 选取 YAML 中至少 5 个典型规格用于参数化测试
# Select at least 5 representative spec keys from YAML for parametric tests
_SAMPLE_KEYS = [
    "OR_03x15",   # 最小规格 / smallest spec: d1=3, d2=1.5
    "OR_10x20",   # 中等细截面 / mid fine-section: d1=10, d2=2
    "OR_20x25",   # 中型 / medium: d1=20, d2=2.5
    "OR_10x35",   # 大截面小内径 / large cord small ID: d1=10, d2=3.5
    "OR_50x35",   # 大内径大截面 / large ID large cord: d1=50, d2=3.5
    "OR_30x25",   # 追加第 6 个 / extra 6th spec: d1=30, d2=2.5
]


# ── 基础冒烟测试 / basic smoke tests ─────────────────────────────────────

def test_oring_default():
    """默认参数 d1=10, d2=2 构建，几何合法，外径正确。
    Build with default d1=10, d2=2: valid geometry, correct OD.
    """
    # 调用工厂函数生成默认规格 O 型圈 / call factory with default args
    part = make_oring(d1=10.0, d2=2.0)

    # 实体必须有效 / solid must be valid
    assert part is not None
    assert part.is_valid, "make_oring() default should produce a valid solid"

    # 外径应等于 d1 + 2*d2 = 14.0mm，允许 ±0.2mm 误差
    # OD should equal d1 + 2*d2 = 14.0 mm, tolerance ±0.2 mm
    bb = part.bounding_box()
    expected_od = 10.0 + 2 * 2.0  # = 14.0 mm
    assert abs(bb.size.X - expected_od) < 0.2, (
        f"OD mismatch: expected ≈{expected_od}, got {bb.size.X:.3f}"
    )
    # Y 方向也应等于外径（圆形投影）/ Y should also equal OD (circular footprint)
    assert abs(bb.size.Y - expected_od) < 0.2, (
        f"OD (Y) mismatch: expected ≈{expected_od}, got {bb.size.Y:.3f}"
    )

    # 截面高度 = d2 / bounding box Z = cord diameter d2
    assert abs(bb.size.Z - 2.0) < 0.1, (
        f"Height mismatch: expected ≈2.0, got {bb.size.Z:.3f}"
    )

    # 体积须为正值 / volume must be positive
    assert part.volume > 0, "volume should be positive"


def test_oring_small():
    """小规格 d1=5, d2=1.5 构建，实体有效。
    Small spec d1=5, d2=1.5: solid is valid.
    """
    # 构建最小常用规格 / build smallest common spec
    part = make_oring(d1=5.0, d2=1.5)

    assert part is not None
    assert part.is_valid, "make_oring(d1=5, d2=1.5) should be valid"

    # 外径 = 5 + 2*1.5 = 8.0mm / OD = 5 + 3 = 8.0 mm
    bb = part.bounding_box()
    expected_od = 5.0 + 2 * 1.5  # = 8.0 mm
    assert abs(bb.size.X - expected_od) < 0.2, (
        f"Small OD mismatch: expected ≈{expected_od}, got {bb.size.X:.3f}"
    )


def test_oring_large():
    """大规格 d1=50, d2=3.5 构建，实体有效，外径正确。
    Large spec d1=50, d2=3.5: valid solid, correct OD.
    """
    part = make_oring(d1=50.0, d2=3.5)

    assert part is not None
    assert part.is_valid, "make_oring(d1=50, d2=3.5) should be valid"

    # 外径 = 50 + 2*3.5 = 57.0 mm / OD = 57.0 mm
    bb = part.bounding_box()
    expected_od = 50.0 + 2 * 3.5  # = 57.0 mm
    assert abs(bb.size.X - expected_od) < 0.3, (
        f"Large OD mismatch: expected ≈{expected_od}, got {bb.size.X:.3f}"
    )


# ── YAML 规格参数化测试 / parametric YAML spec tests ─────────────────────

@pytest.mark.parametrize("key", _SAMPLE_KEYS)
def test_oring_from_yaml(key: str):
    """从 _SPECS 逐条构建 O 型圈，验证实体有效且外径吻合。
    Build each O-ring from _SPECS, verify solid is valid and OD matches.
    """
    # 取出规格，检查 key 存在于规格表 / fetch spec, assert key exists
    assert key in _SPECS, f"Spec key {key!r} not found in _SPECS"
    spec = _SPECS[key]

    # 调用工厂 / call factory
    part = make_oring(d1=spec.d1, d2=spec.d2)

    # 实体须有效 / solid must be valid
    assert part is not None
    assert part.is_valid, (
        f"{key} (d1={spec.d1}, d2={spec.d2}): solid is not valid"
    )

    # 外径检验：bbox.X ≈ d1 + 2*d2 / OD check: bbox.X ≈ d1 + 2*d2
    expected_od = spec.d1 + 2 * spec.d2
    bb = part.bounding_box()
    assert abs(bb.size.X - expected_od) < 0.3, (
        f"{key}: OD mismatch expected={expected_od:.1f}, got={bb.size.X:.3f}"
    )

    # 体积须为正 / volume must be positive
    assert part.volume > 0, f"{key}: volume should be positive"


# ── _SPECS 字典完整性测试 / _SPECS dict integrity test ──────────────────

def test_specs_loaded():
    """_SPECS 应包含 d2=3.5mm 系列（新增条目），总计至少 11 个规格。
    _SPECS should include d2=3.5mm series (newly added), at least 11 specs total.
    """
    # 检查总数 / check total count
    assert len(_SPECS) >= 11, (
        f"Expected >= 11 specs, got {len(_SPECS)}: {list(_SPECS.keys())}"
    )

    # 验证每个 d2=3.5mm 规格都已加载 / verify all d2=3.5 specs are loaded
    for key in ["OR_10x35", "OR_20x35", "OR_30x35", "OR_50x35"]:
        assert key in _SPECS, f"Expected {key!r} in _SPECS"
        assert _SPECS[key].d2 == 3.5, f"{key}: d2 should be 3.5"


def test_oring_volume_increases_with_d1():
    """相同截面 d2，内径越大体积越大。
    For same cord d2, larger d1 gives larger volume.
    """
    # d2 固定为 2.0mm，比较 d1=10 和 d1=20 的体积
    # Fix d2=2.0mm, compare volumes for d1=10 and d1=20
    small = make_oring(d1=10.0, d2=2.0)
    large = make_oring(d1=20.0, d2=2.0)
    assert large.volume > small.volume, (
        f"Expected vol(d1=20) > vol(d1=10), got {large.volume:.2f} vs {small.volume:.2f}"
    )


# ── 非法参数异常测试 / invalid-parameter error tests ────────────────────

def test_oring_invalid_d2_too_large():
    """截面直径 d2 >= 内径 d1 时必须抛出 ValueError。
    Must raise ValueError when cord diameter d2 >= inside diameter d1.
    """
    # d2 等于 d1 时应报错 / d2 == d1 should raise
    with pytest.raises(ValueError, match="d2"):
        make_oring(d1=5.0, d2=5.0)

    # d2 大于 d1 时也应报错 / d2 > d1 should also raise
    with pytest.raises(ValueError):
        make_oring(d1=3.0, d2=4.0)


def test_oring_invalid_zero():
    """d1 = 0 时必须抛出 ValueError。
    Must raise ValueError when d1 = 0.
    """
    with pytest.raises(ValueError):
        make_oring(d1=0.0, d2=1.5)


def test_oring_invalid_negative():
    """负尺寸必须抛出 ValueError。
    Negative dimensions must raise ValueError.
    """
    # 负内径 / negative ID
    with pytest.raises(ValueError):
        make_oring(d1=-5.0, d2=2.0)

    # 负截面直径 / negative cord diameter
    with pytest.raises(ValueError):
        make_oring(d1=10.0, d2=-1.0)
