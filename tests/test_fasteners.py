"""Fasteners smoke tests — ISO 4762 / DIN 912 socket head screws,
ISO 10642 countersunk screws, ISO 4032 / GB/T 6172.1 / DIN 985 hex nuts,
DIN 933 hex bolts, ISO 7089 / GB/T 93 washers.

螺丝零件冒烟测试 — ISO 4762 内六角圆柱头螺丝、ISO 10642 沉头螺丝、
ISO 4032 / GB/T 6172.1 / DIN 985 六角螺母、DIN 933 外六角螺栓、
ISO 7089 / GB/T 93 垫圈。
"""
import pytest

from build123d_parts_lib.parts.fasteners.countersunk_screw import (
    make_countersunk_screw,
)
from build123d_parts_lib.parts.fasteners.hex_bolt import make_hex_bolt
from build123d_parts_lib.parts.fasteners.nut_hex import make_hex_nut
from build123d_parts_lib.parts.fasteners.socket_head_screw import (
    _SPECS as _SCREW_SPECS,
)
from build123d_parts_lib.parts.fasteners.socket_head_screw import (
    make_socket_head_screw,
)
from build123d_parts_lib.parts.fasteners.washer import make_washer

# ═════════════════════════════════════════════════════════════════════════════
# socket_head_screw — ISO 4762 内六角圆柱头螺丝
# socket_head_screw — ISO 4762 hex socket head cap screw
# ═════════════════════════════════════════════════════════════════════════════

def test_socket_head_screw_m3_default():
    """M3 默认长度螺丝应有效，头径 dk ≈ 5.5，总高 ≈ length + k。
    M3 with default length should be valid, head diameter dk ≈ 5.5, total Z ≈ length + k.
    """
    p = make_socket_head_screw(size="M3")
    # 实体有效 / solid must be valid
    assert p.is_valid

    bb = p.bounding_box().size
    # 头径方向 bbox ≈ dk = 5.5 / head diameter direction bbox ≈ dk = 5.5
    assert abs(bb.X - 5.5) < 0.1, f"X(head dia) expected ≈5.5, got {bb.X}"
    assert abs(bb.Y - 5.5) < 0.1, f"Y(head dia) expected ≈5.5, got {bb.Y}"
    # 默认 length=5（来自 YAML common_lengths_mm[0]），k=3.0 / default length=5, k=3.0
    # Z = length + k；从 _SCREW_SPECS 取 k 值更健壮 / Z = length + k; use _SCREW_SPECS for robustness
    spec = _SCREW_SPECS["M3"]
    from build123d_parts_lib.parts.fasteners.socket_head_screw import DEFAULT_LENGTHS
    expected_z = DEFAULT_LENGTHS["M3"] + spec.k
    assert abs(bb.Z - expected_z) < 0.1, f"Z expected ≈{expected_z}, got {bb.Z}"


def test_socket_head_screw_m6():
    """M6 螺丝头径 dk ≈ 10.0。
    M6 screw head diameter dk ≈ 10.0.
    """
    p = make_socket_head_screw(size="M6", length=20)
    assert p.is_valid
    bb = p.bounding_box().size
    # 头径方向 bbox ≈ dk = 10.0 / head diameter bbox ≈ dk = 10.0
    assert abs(bb.X - 10.0) < 0.1, f"X expected ≈10.0, got {bb.X}"
    assert abs(bb.Y - 10.0) < 0.1, f"Y expected ≈10.0, got {bb.Y}"


def test_socket_head_screw_custom_length():
    """M3 指定 length=20：总高 ≈ 20 + k（3.0）= 23.0。
    M3 with explicit length=20: total Z ≈ 20 + k(3.0) = 23.0.
    """
    p = make_socket_head_screw(size="M3", length=20)
    assert p.is_valid
    bb = p.bounding_box().size
    # 螺杆长度 / shaft length
    expected_z = 20.0 + _SCREW_SPECS["M3"].k
    assert abs(bb.Z - expected_z) < 0.1, f"Z expected ≈{expected_z}, got {bb.Z}"


def test_socket_head_screw_unknown_size():
    """未知规格应抛出 ValueError。
    Unknown size should raise ValueError.
    """
    with pytest.raises(ValueError, match="M99"):
        make_socket_head_screw(size="M99")


def test_socket_head_screw_zero_length():
    """length=0 应抛出 ValueError。
    length=0 should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_socket_head_screw(size="M3", length=0)


def test_socket_head_screw_negative_length():
    """负 length 应抛出 ValueError。
    Negative length should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_socket_head_screw(size="M3", length=-5)


@pytest.mark.parametrize("size", ["M2", "M2.5", "M3", "M4", "M5", "M6", "M8", "M10"])
def test_socket_head_screw_all_sizes(size: str):
    """所有支持规格均应生成有效实体。
    All supported sizes should produce a valid solid.
    """
    # 使用固定长度避免 DEFAULT_LENGTHS 差异 / use fixed length to avoid DEFAULT_LENGTHS variations
    p = make_socket_head_screw(size=size, length=10)
    assert p.is_valid, f"{size} 螺丝生成失败 / screw build failed"
    bb = p.bounding_box().size
    # 总高 = 10 + k；k 在合理范围内 / total Z = 10 + k; k in reasonable range
    spec = _SCREW_SPECS[size]
    assert abs(bb.Z - (10.0 + spec.k)) < 0.1


def test_socket_head_screw_specs_loaded_from_yaml():
    """验证 YAML 加载：M3 dk 与 YAML 中 5.5 一致。
    Verify YAML loading: M3 dk matches YAML value 5.5.
    """
    spec = _SCREW_SPECS["M3"]
    # YAML 中 M3 head.dk = 5.5 / YAML M3 head.dk = 5.5
    assert abs(spec.dk - 5.5) < 0.01, f"M3 dk from YAML expected 5.5, got {spec.dk}"
    # YAML 中 M6 head.dk = 10.0 / YAML M6 head.dk = 10.0
    assert abs(_SCREW_SPECS["M6"].dk - 10.0) < 0.01


# ═════════════════════════════════════════════════════════════════════════════
# countersunk_screw — ISO 10642 内六角沉头螺丝
# countersunk_screw — ISO 10642 hex socket countersunk head screw
# ═════════════════════════════════════════════════════════════════════════════

def test_countersunk_screw_m3_default():
    """M3 沉头螺丝默认应有效，头径 dk ≈ 5.6。
    M3 countersunk screw default should be valid, head diameter dk ≈ 5.6.
    """
    p = make_countersunk_screw(size="M3")
    assert p.is_valid
    bb = p.bounding_box().size
    # 锥形头最大径 ≈ dk = 5.6 / max cone head diameter ≈ dk = 5.6
    assert abs(bb.X - 5.6) < 0.1, f"X expected ≈5.6, got {bb.X}"


def test_countersunk_screw_m4():
    """M4 沉头螺丝应有效。
    M4 countersunk screw should be valid.
    """
    p = make_countersunk_screw(size="M4", length=12)
    assert p.is_valid


def test_countersunk_screw_unknown_size():
    """未知规格应抛出 ValueError。
    Unknown size should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_countersunk_screw(size="M99")


def test_countersunk_screw_zero_length():
    """length=0 应抛出 ValueError。
    length=0 should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_countersunk_screw(size="M3", length=0)


@pytest.mark.parametrize("size", ["M2", "M2.5", "M3", "M4", "M5"])
def test_countersunk_screw_all_sizes(size: str):
    """所有支持规格均应生成有效实体。
    All supported sizes should produce a valid solid.
    """
    p = make_countersunk_screw(size=size, length=10)
    assert p.is_valid, f"{size} 沉头螺丝生成失败 / countersunk screw build failed"


# ═════════════════════════════════════════════════════════════════════════════
# nut_hex — 六角螺母
# nut_hex — hex nuts
# ═════════════════════════════════════════════════════════════════════════════

def test_hex_nut_m3_iso4032():
    """M3 ISO 4032 螺母应有效，高度 m ≈ 2.4。
    M3 ISO 4032 nut should be valid, height m ≈ 2.4.
    """
    p = make_hex_nut(size="M3", standard="ISO4032")
    assert p.is_valid
    bb = p.bounding_box().size
    # 螺母高度 / nut height
    assert abs(bb.Z - 2.4) < 0.1, f"Z(height) expected ≈2.4, got {bb.Z}"


def test_hex_nut_m6_gb6172():
    """M6 GB6172 薄螺母应有效。
    M6 GB6172 thin nut should be valid.
    """
    p = make_hex_nut(size="M6", standard="GB6172")
    assert p.is_valid


def test_hex_nut_m4_din985():
    """M4 DIN 985 尼龙锁紧螺母应有效。
    M4 DIN 985 nylon lock nut should be valid.
    """
    p = make_hex_nut(size="M4", standard="DIN985")
    assert p.is_valid


def test_hex_nut_unknown_size():
    """未知规格应抛出 ValueError。
    Unknown size should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_hex_nut(size="M99", standard="ISO4032")


def test_hex_nut_unknown_standard():
    """未知标准应抛出 ValueError。
    Unknown standard should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_hex_nut(size="M3", standard="DIN_UNKNOWN")


@pytest.mark.parametrize("size,standard", [
    ("M3",  "ISO4032"),
    ("M4",  "ISO4032"),
    ("M6",  "ISO4032"),
    ("M8",  "ISO4032"),
    ("M10", "ISO4032"),
    ("M3",  "GB6172"),
    ("M6",  "GB6172"),
    ("M4",  "DIN985"),
    ("M6",  "DIN985"),
    ("M8",  "DIN985"),
])
def test_hex_nut_yaml_sizes(size: str, standard: str):
    """YAML 中收录的所有螺母规格均应生成有效实体。
    All nut sizes present in YAML should produce valid solids.
    """
    p = make_hex_nut(size=size, standard=standard)
    assert p.is_valid, f"{size}/{standard} 螺母生成失败 / nut build failed"


# ═════════════════════════════════════════════════════════════════════════════
# hex_bolt — DIN 933 外六角螺栓
# hex_bolt — DIN 933 hex bolts
# ═════════════════════════════════════════════════════════════════════════════

def test_hex_bolt_m6_default():
    """M6 外六角螺栓默认应有效。
    M6 hex bolt with default length should be valid.
    """
    p = make_hex_bolt(size="M6")
    assert p.is_valid


def test_hex_bolt_m8_custom_length():
    """M8 螺栓 length=30 应有效，总高 ≈ 30 + k（5.3）= 35.3。
    M8 bolt length=30 should be valid, total Z ≈ 30 + k(5.3) = 35.3.
    """
    p = make_hex_bolt(size="M8", length=30)
    assert p.is_valid
    bb = p.bounding_box().size
    # 头高 k=5.3 for M8 in YAML / head height k=5.3 for M8
    from build123d_parts_lib.parts.fasteners.hex_bolt import _SPECS
    expected_z = 30.0 + _SPECS["M8"].k
    assert abs(bb.Z - expected_z) < 0.1, f"Z expected ≈{expected_z}, got {bb.Z}"


def test_hex_bolt_unknown_size():
    """未知规格应抛出 ValueError。
    Unknown size should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_hex_bolt(size="M99")


def test_hex_bolt_zero_length():
    """length=0 应抛出 ValueError。
    length=0 should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_hex_bolt(size="M6", length=0)


@pytest.mark.parametrize("size", ["M4", "M5", "M6", "M8", "M10"])
def test_hex_bolt_all_sizes(size: str):
    """所有 DIN 933 规格均应生成有效实体。
    All DIN 933 sizes should produce valid solids.
    """
    p = make_hex_bolt(size=size, length=20)
    assert p.is_valid, f"{size} 螺栓生成失败 / bolt build failed"


# ═════════════════════════════════════════════════════════════════════════════
# washer — 垫圈
# washer — washers
# ═════════════════════════════════════════════════════════════════════════════

def test_washer_m3_flat():
    """M3 平垫圈（ISO 7089）应有效，外径 ≈ 7.0，厚度 ≈ 0.5。
    M3 flat washer (ISO 7089) should be valid, OD ≈ 7.0, thickness ≈ 0.5.
    """
    p = make_washer(size="M3", type_="flat")
    assert p.is_valid
    bb = p.bounding_box().size
    # 外径方向 / OD direction
    assert abs(bb.X - 7.0) < 0.1, f"X(OD) expected ≈7.0, got {bb.X}"
    assert abs(bb.Y - 7.0) < 0.1, f"Y(OD) expected ≈7.0, got {bb.Y}"
    # 厚度 / thickness
    assert abs(bb.Z - 0.5) < 0.05, f"Z(thickness) expected ≈0.5, got {bb.Z}"


def test_washer_m4_flat():
    """M4 平垫圈应有效。
    M4 flat washer should be valid.
    """
    p = make_washer(size="M4", type_="flat")
    assert p.is_valid


def test_washer_m3_spring():
    """M3 弹簧垫圈（GB/T 93）应有效。
    M3 spring washer (GB/T 93) should be valid.
    """
    p = make_washer(size="M3", type_="spring")
    assert p.is_valid


def test_washer_unknown_size_flat():
    """未知规格的平垫圈应抛出 ValueError。
    Unknown flat washer size should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_washer(size="M99", type_="flat")


def test_washer_unknown_size_spring():
    """未知规格的弹簧垫圈应抛出 ValueError。
    Unknown spring washer size should raise ValueError.
    """
    with pytest.raises(ValueError):
        make_washer(size="M99", type_="spring")


def test_washer_unknown_type():
    """未知垫圈类型应抛出 ValueError。
    Unknown washer type should raise ValueError.
    """
    with pytest.raises(ValueError, match="(?i)unknown"):
        make_washer(size="M3", type_="rubber")


@pytest.mark.parametrize("size", ["M2", "M2.5", "M3", "M4", "M5"])
def test_washer_flat_all_sizes(size: str):
    """所有平垫圈规格均应生成有效实体。
    All flat washer sizes should produce valid solids.
    """
    p = make_washer(size=size, type_="flat")
    assert p.is_valid, f"{size} 平垫圈生成失败 / flat washer build failed"


@pytest.mark.parametrize("size", ["M3", "M4", "M5"])
def test_washer_spring_all_sizes(size: str):
    """所有弹簧垫圈规格均应生成有效实体。
    All spring washer sizes should produce valid solids.
    """
    p = make_washer(size=size, type_="spring")
    assert p.is_valid, f"{size} 弹簧垫圈生成失败 / spring washer build failed"
