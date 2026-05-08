"""ISO 3601-1 / GB/T 3452.1 O-ring (torus geometry).
O 型圈简化实体 — 圆环截面。

Geometry:
  - 环形圆环 (torus) / torus shape
  - 截面圆直径 d2 / cord diameter d2
  - 内径 d1 / inside diameter d1
  - 原点在 O 型圈几何中心 / origin at geometric center

  Relations:
    major_radius = d1/2 + d2/2  (center of cord circle to torus center)
    minor_radius = d2/2          (cord circle radius)
    outer_diameter = d1 + 2*d2
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import Align, BuildPart, Part, Torus, export_step


class ORingSpec(NamedTuple):
    """Minimal O-ring dimensional spec. / 最小 O 型圈尺寸规格。"""
    d1: float   # inside diameter / 内径 (mm)
    d2: float   # cord diameter / 截面直径 (mm)


def _load_specs() -> dict[str, ORingSpec]:
    """Load all O-ring specs from oring.yaml.
    从 oring.yaml 加载全部规格。
    """
    yaml_path = Path(__file__).parent / "oring.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    specs: dict[str, ORingSpec] = {}
    for key, entry in raw.items():
        # 跳过非 dict 条目（注释块等）/ skip non-dict entries (comment blocks, etc.)
        if not isinstance(entry, dict):
            continue
        # 仅加载 type == 'o-ring' 的条目 / only load entries with type == 'o-ring'
        if entry.get("type") != "o-ring":
            continue
        dims = entry.get("dimensions", {})
        specs[key] = ORingSpec(d1=dims["d1"], d2=dims["d2"])
    return specs


# 模块加载时构建规格字典 / build specs dict at module load time
_SPECS: dict[str, ORingSpec] = _load_specs()


def make_oring(d1: float = 10.0, d2: float = 2.0) -> Part:
    """Generate O-ring torus solid (ISO 3601-1 / GB/T 3452.1).
    生成 O 型圈圆环实体。

    Args:
        d1: inside diameter in mm / 内径（mm），默认 10.0
        d2: cord diameter in mm / 截面直径（mm），默认 2.0

    Returns:
        build123d Part — torus solid centered at origin.
        以原点为中心的圆环体。

    Raises:
        ValueError: if d2 >= d1 or either dimension <= 0.
                    截面直径必须小于内径，且两者均须大于 0。

    Coordinate origin: geometric center of torus / 原点在圆环几何中心。
    Z plane: torus lies in the XY plane / O 型圈在 XY 平面内。
    """
    # 参数合法性检查 / parameter validation
    if d1 <= 0 or d2 <= 0:
        raise ValueError(
            f"dimensions must be positive, got d1={d1}, d2={d2} / "
            f"尺寸必须为正数，输入 d1={d1}, d2={d2}"
        )
    if d2 >= d1:
        raise ValueError(
            f"cord diameter d2={d2} must be < inside diameter d1={d1} / "
            f"截面直径 d2={d2} 必须小于内径 d1={d1}"
        )

    # 计算圆环半径 / compute torus radii
    # major_radius: 圆环中心线半径 = (d1/2) + (d2/2)
    # minor_radius: 截面圆半径    = d2/2
    major_r = d1 / 2 + d2 / 2
    minor_r = d2 / 2

    with BuildPart() as oring:
        # 使用 build123d 内置 Torus 生成圆环体 / use built-in Torus for torus solid
        Torus(
            major_radius=major_r,
            minor_radius=minor_r,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )

    # 计算 g-dict 供不变式断言 / compute geometry dict for invariant checks
    g = {
        "d1": d1,
        "d2": d2,
        "major_r": major_r,
        "minor_r": minor_r,
        "outer_d": d1 + 2 * d2,
    }
    _assert_geometry_invariants(g)

    return oring.part


# ── 几何不变式（Single Truth）──────────────────────────────────────────────
# GEOMETRY_INVARIANTS 是约束的唯一真相；contract.yaml expr 从此派生。
# Geometry invariants — single source of truth; contract.yaml expr derived from here.
GEOMETRY_INVARIANTS = [
    # (描述 / description,  test lambda)
    ("截面直径必须小于内径 / cord diameter must be less than inside diameter",
     lambda g: g["d2"] < g["d1"]),
    ("major_radius 必须等于 d1/2 + d2/2",
     lambda g: abs(g["major_r"] - (g["d1"] / 2 + g["d2"] / 2)) < 1e-9),
    ("minor_radius 必须等于 d2/2 / minor_radius must equal d2/2",
     lambda g: abs(g["minor_r"] - g["d2"] / 2) < 1e-9),
    ("外径必须等于 d1 + 2*d2 / outer diameter must equal d1 + 2*d2",
     lambda g: abs(g["outer_d"] - (g["d1"] + 2 * g["d2"])) < 1e-9),
]


def _assert_geometry_invariants(g: dict) -> None:
    """Assert all geometry invariants. Fail immediately on violation.
    断言所有几何不变式，违反时立即报错（不吞异常）。
    """
    for desc, test in GEOMETRY_INVARIANTS:
        assert test(g), f"Invariant FAIL: {desc}\n  g={g}"


if __name__ == "__main__":
    # 批量生成 STEP 缓存文件 / batch-generate STEP cache files
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for key, spec in _SPECS.items():
        part = make_oring(d1=spec.d1, d2=spec.d2)
        # 文件名：oring_d{内径}_cs{截面直径*10:02d}.step
        out_path = cache_dir / f"oring_d{int(spec.d1)}_cs{int(spec.d2 * 10):02d}.step"
        export_step(part, str(out_path))
        bb = part.bounding_box()
        od = spec.d1 + spec.d2 * 2
        print(
            f"OK: {key:15s}  d1={spec.d1:5.1f}  d2={spec.d2:4.1f}"
            f"  OD={od:5.1f}mm  vol={part.volume:.2f}mm³"
        )
