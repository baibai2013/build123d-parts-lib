"""Bearings smoke tests — ISO 15 ball bearings + ISO 10736 linear bushings.
轴承冒烟测试 — 深沟球轴承 + 直线球轴承。

All comments are bilingual (Chinese/English) per project rules.
所有注释均为中英双语，符合项目规范。
"""
import pytest

from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.bearings.linear_bushing import make_linear_bushing
from build123d_parts_lib.parts.bearings.mr_bearing import make_mr_bearing

# ──────────────────────────────────────────────────────────────────────────────
# ISO 15 深沟球轴承 / ISO 15 deep-groove ball bearing
# ──────────────────────────────────────────────────────────────────────────────

def test_ball_bearing_608zz():
    """608ZZ 基本几何验证 / 608ZZ basic geometry check.

    Expected dimensions from bearings.yaml / 预期尺寸来自 bearings.yaml:
        d=8, D=22, B=7 (all in mm)
    Bounding box / 包围盒:
        X/Y = D = 22.0 mm  (outer diameter / 外径)
        Z   = B = 7.0 mm   (width / 宽度; Z-centered, -B/2 ~ +B/2)
    """
    p = make_ball_bearing("608ZZ")
    # 实体必须有效 / part must be valid
    assert p.is_valid

    bb = p.bounding_box().size
    # 外径检查：bbox.X 应等于 D=22.0 mm (±0.1)
    # Outer diameter check: bbox.X should equal D=22.0 mm (±0.1)
    assert abs(bb.X - 22.0) < 0.1, f"Expected OD=22.0, got {bb.X:.3f}"
    # 宽度检查：bbox.Z 应等于 B=7.0 mm (±0.1)
    # Width check: bbox.Z should equal B=7.0 mm (±0.1)
    assert abs(bb.Z - 7.0) < 0.1, f"Expected B=7.0, got {bb.Z:.3f}"


@pytest.mark.parametrize("model,d,D,B", [
    # 型号,内径,外径,宽度 / model, bore, OD, width
    ("608ZZ",    8.0,  22.0, 7.0),
    ("624ZZ",    4.0,  13.0, 5.0),
    ("625ZZ",    5.0,  16.0, 5.0),
    ("626ZZ",    6.0,  19.0, 6.0),
    ("6000ZZ",  10.0,  26.0, 8.0),
    ("6001-2RS", 12.0,  28.0, 8.0),
    ("6002ZZ",  15.0,  32.0, 9.0),
])
def test_ball_bearing_all_models(model, d, D, B):
    """所有 ISO 15 深沟球轴承型号参数化测试 / parametrized test for all ISO 15 models.

    Checks: is_valid, OD (bbox.X == D), width (bbox.Z == B).
    检查：实体有效性、外径、宽度。
    """
    p = make_ball_bearing(model)
    # 实体有效性 / part validity
    assert p.is_valid, f"Part {model} is not valid"

    bb = p.bounding_box().size
    # 外径 / outer diameter
    assert abs(bb.X - D) < 0.1, f"{model}: expected OD={D}, got {bb.X:.3f}"
    # 宽度 / width
    assert abs(bb.Z - B) < 0.1, f"{model}: expected B={B}, got {bb.Z:.3f}"


def test_ball_bearing_unknown():
    """未知型号抛出 ValueError / unknown model raises ValueError.

    The error message must contain "unknown" for grep-ability.
    错误信息必须包含 "unknown" 以便过滤。
    """
    with pytest.raises(ValueError, match="unknown"):
        make_ball_bearing("999ZZ")


# ──────────────────────────────────────────────────────────────────────────────
# MR 系列微型深沟球轴承 / MR series miniature deep-groove ball bearing
# ──────────────────────────────────────────────────────────────────────────────

def test_mr_bearing_mr63zz():
    """MR63ZZ 基本几何验证 / MR63ZZ basic geometry check.

    Expected dimensions from bearings.yaml / 预期尺寸来自 bearings.yaml:
        d=3, D=6, B=2.5 (all in mm)
    Bounding box / 包围盒:
        X/Y = D = 6.0 mm  (outer diameter / 外径)
        Z   = B = 2.5 mm  (width / 宽度)
    """
    p = make_mr_bearing("MR63ZZ")
    # 实体必须有效 / part must be valid
    assert p.is_valid

    bb = p.bounding_box().size
    # 外径检查 / outer diameter check: D=6.0 mm
    assert abs(bb.X - 6.0) < 0.1, f"Expected OD=6.0, got {bb.X:.3f}"
    # 宽度检查 / width check: B=2.5 mm
    assert abs(bb.Z - 2.5) < 0.1, f"Expected B=2.5, got {bb.Z:.3f}"


@pytest.mark.parametrize("model,D,B", [
    # 型号,外径,宽度 / model, OD, width
    ("MR63ZZ",  6.0, 2.5),
    ("MR74ZZ",  7.0, 2.5),
    ("MR84ZZ",  8.0, 3.0),
    ("MR85ZZ",  8.0, 2.5),
    ("MR104ZZ", 10.0, 4.0),
])
def test_mr_bearing_all(model, D, B):
    """所有 MR 系列型号参数化测试 / parametrized test for all MR series models.

    Checks: is_valid, OD (bbox.X == D), width (bbox.Z == B).
    检查：实体有效性、外径、宽度。
    """
    p = make_mr_bearing(model)
    # 实体有效性 / part validity
    assert p.is_valid, f"Part {model} is not valid"

    bb = p.bounding_box().size
    # 外径 / outer diameter
    assert abs(bb.X - D) < 0.1, f"{model}: expected OD={D}, got {bb.X:.3f}"
    # 宽度 / width
    assert abs(bb.Z - B) < 0.1, f"{model}: expected B={B}, got {bb.Z:.3f}"


# ──────────────────────────────────────────────────────────────────────────────
# ISO 10736 直线球轴承 / ISO 10736 linear ball bearing
# ──────────────────────────────────────────────────────────────────────────────

def test_lm8uu():
    """LM8UU 基本几何验证 / LM8UU basic geometry check.

    Expected dimensions from lm_bearings.yaml / 预期尺寸来自 lm_bearings.yaml:
        d=8, D=15, L=24 (all in mm)
    Bounding box / 包围盒 (origin at bottom center, Z=0~L):
        X/Y = D = 15.0 mm  (outer diameter / 外径)
        Z   = L = 24.0 mm  (length / 长度)
    """
    p = make_linear_bushing("LM8UU")
    # 实体必须有效 / part must be valid
    assert p.is_valid

    bb = p.bounding_box().size
    # 外径检查 / outer diameter check: D=15.0 mm
    assert abs(bb.X - 15.0) < 0.1, f"Expected D=15.0, got {bb.X:.3f}"
    # 长度检查 / length check: L=24.0 mm
    assert abs(bb.Z - 24.0) < 0.1, f"Expected L=24.0, got {bb.Z:.3f}"


def test_lm12uu():
    """LM12UU 基本几何验证 / LM12UU basic geometry check.

    Expected dimensions from lm_bearings.yaml / 预期尺寸来自 lm_bearings.yaml:
        d=12, D=21, L=30 (all in mm)
    Bounding box / 包围盒:
        X/Y = D = 21.0 mm  (outer diameter / 外径)
        Z   = L = 30.0 mm  (length / 长度)
    """
    p = make_linear_bushing("LM12UU")
    # 实体有效性 / part validity
    assert p.is_valid

    bb = p.bounding_box().size
    # 外径 / outer diameter: D=21.0 mm
    assert abs(bb.X - 21.0) < 0.1, f"Expected D=21.0, got {bb.X:.3f}"
    # 长度 / length: L=30.0 mm
    assert abs(bb.Z - 30.0) < 0.1, f"Expected L=30.0, got {bb.Z:.3f}"


def test_lmf8uu():
    """LMF8UU 法兰型直线轴承基本几何验证 / LMF8UU flanged linear bushing geometry check.

    Expected dimensions from lm_bearings.yaml / 预期尺寸来自 lm_bearings.yaml:
        d=8, D=15, L=24, flange_D=22, flange_t=1.6 (all in mm)
    Bounding box / 包围盒:
        X/Y = flange_D = 22.0 mm (flange dominates / 法兰决定外廓)
        Z   = L + flange_t = 24.0 + 1.6 = 25.6 mm (body + flange / 主体 + 法兰)
    """
    p = make_linear_bushing("LMF8UU")
    # 实体有效性 / part validity
    assert p.is_valid

    bb = p.bounding_box().size
    # 法兰外径决定 X/Y / flange OD dominates X/Y: flange_D=22.0 mm
    assert abs(bb.X - 22.0) < 0.1, f"Expected flange_D=22.0, got {bb.X:.3f}"
    # 总高 = L + flange_t = 24.0 + 1.6 = 25.6 mm
    # Total height = L + flange_t = 25.6 mm
    assert abs(bb.Z - 25.6) < 0.1, f"Expected total_h=25.6, got {bb.Z:.3f}"


def test_linear_bushing_unknown():
    """未知型号抛出 ValueError / unknown model raises ValueError.

    The error message must contain "unknown" for grep-ability.
    错误信息必须包含 "unknown"。
    """
    with pytest.raises(ValueError, match="unknown"):
        make_linear_bushing("LM999UU")


@pytest.mark.parametrize("model", [
    # 所有直线轴承型号 / all linear bushing models
    "LM6UU",
    "LM8UU",
    "LM10UU",
    "LM12UU",
    "LMF8UU",
    "LMF10UU",
])
def test_linear_bushing_all(model):
    """所有直线轴承型号参数化测试 / parametrized test for all linear bushing models.

    Checks: is_valid, positive volume, bbox dimensions are positive.
    检查：实体有效、体积为正、包围盒各维度均为正值。
    """
    p = make_linear_bushing(model)
    # 实体有效性 / part validity
    assert p.is_valid, f"Part {model} is not valid"

    bb = p.bounding_box().size
    # 包围盒各维度为正 / all bounding box dimensions must be positive
    assert bb.X > 0, f"{model}: bbox.X should be positive, got {bb.X}"
    assert bb.Y > 0, f"{model}: bbox.Y should be positive, got {bb.Y}"
    assert bb.Z > 0, f"{model}: bbox.Z should be positive, got {bb.Z}"

    # 体积为正 / volume must be positive (non-zero solid)
    assert p.volume > 0, f"{model}: volume should be positive, got {p.volume}"
