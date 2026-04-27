"""Metric screw clearance hole generator.

给定 M 规格和配合精度，返回合适的通孔直径。
Source: data-sources/fasteners.yaml (skill build123d-cad)
License: MIT
"""
from __future__ import annotations

# 每个 M 规格的三档配合直径 (close / medium / loose)
# medium 适合 FDM 3D 打印；close 适合 SLA/CNC；loose 适合宽松定位
_CLEARANCE_TABLE: dict[str, dict[str, float]] = {
    "M2":  {"close": 2.2, "medium": 2.4, "loose": 2.6},
    "M2.5": {"close": 2.7, "medium": 2.9, "loose": 3.1},
    "M3":  {"close": 3.2, "medium": 3.4, "loose": 3.6},
    "M4":  {"close": 4.3, "medium": 4.5, "loose": 4.8},
    "M5":  {"close": 5.3, "medium": 5.5, "loose": 5.8},
    "M6":  {"close": 6.4, "medium": 6.6, "loose": 7.0},
}


def get_clearance_diameter(m_size: str, fit: str = "medium") -> float:
    """返回给定 M 规格和配合等级的通孔直径（mm）。

    Args:
        m_size: "M2" / "M2.5" / "M3" / "M4" / "M5" / "M6"
        fit:    "close"  — 贴合（SLA/CNC 优选）
                "medium" — 中等（FDM 3D 打印优选，默认）
                "loose"  — 宽松（需要手动调整定位时）

    返回：通孔直径（mm）

    错误：未收录规格或错误 fit 名称时 ValueError
    """
    m_norm = m_size.upper()
    if m_norm not in _CLEARANCE_TABLE:
        available = ", ".join(_CLEARANCE_TABLE.keys())
        raise ValueError(f"Unknown screw size {m_size!r}; available: {available}")
    row = _CLEARANCE_TABLE[m_norm]
    if fit not in row:
        raise ValueError(
            f"fit must be one of {list(row.keys())}, got {fit!r}"
        )
    return row[fit]


def make_clearance_hole(
    m_size: str,
    fit: str = "medium",
):
    """返回一个 build123d Hole 对象（需在 BuildPart 的某个面上用）。

    使用示例:
        with BuildPart() as plate:
            Box(60, 40, 3)
            top = plate.faces().sort_by(Axis.Z)[-1]
            with BuildSketch(top):
                with Locations((10, 10), (50, 10)):
                    Circle(get_clearance_diameter("M3") / 2)
            extrude(amount=-3, mode=Mode.SUBTRACT)

    本函数只是便捷构造器：
    """
    from build123d import Hole
    return Hole(radius=get_clearance_diameter(m_size, fit) / 2)


if __name__ == "__main__":
    for m in _CLEARANCE_TABLE:
        print(
            f"{m}: close={get_clearance_diameter(m, 'close')}, "
            f"medium={get_clearance_diameter(m, 'medium')}, "
            f"loose={get_clearance_diameter(m, 'loose')}"
        )
