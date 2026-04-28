"""DIN 1481 spring pin (slotted) / 弹簧销（开口圆形截面）.

Standards: DIN 1481 (≈ ISO 8752)
License: MIT

支持公称直径 / Supported nominal diameters: 3 mm, 4 mm

几何 / Geometry:
- 自由状态（安装前）开口圆形截面 / Free-state (pre-install) split circular section
- 截面：圆环（外径 OD_free，内径 OD_free - 2*t）减去一道纵向缝隙
  Section: annulus (OD_free outer, inner = OD - 2*wall_t) minus a longitudinal slit
- 沿 +Z 拉伸 length / Extruded along +Z by `length`
- 缝隙开口朝向 +X 方向（C 形开口，仅切一侧）
  Slit opens along +X (C-shape, only one side is cut)
- 原点底面中心，+Z 为销长方向
  Origin at bottom face centre, +Z = pin axis (length direction)

注：自由状态外径略大于公称直径（DIN 1481 允差，约 1.05×）。
压入孔时收缩贴合，靠弹性夹紧。
Note: Free-state OD slightly exceeds nominal (DIN 1481 tolerance, ~1.05×).
Pin compresses elastically when pressed into a bore of nominal diameter.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    Part,
    Plane,
    Rectangle,
    export_step,
    extrude,
    Locations,
)


# ─── 1. Spec 数据容器 / Spec NamedTuple ────────────────────────
class SpringPinSpec(NamedTuple):
    nominal_d: float   # 公称直径 / nominal diameter
    od_free:   float   # 自由状态外径 / free-state OD
    wall_t:    float   # 壁厚 / wall thickness
    slit_w:    float   # 缝宽（自由状态）/ slit width (free state)


# ─── 2. 内置后备数据 / Built-in fallback ─────────────────────
_FALLBACK: dict[str, SpringPinSpec] = {
    "D3": SpringPinSpec(nominal_d=3.0, od_free=3.15, wall_t=0.8, slit_w=1.0),
    "D4": SpringPinSpec(nominal_d=4.0, od_free=4.20, wall_t=1.0, slit_w=1.2),
}


# ─── 3. YAML 加载 / YAML loader ─────────────────────────────
def _load_specs() -> dict[str, SpringPinSpec]:
    """从 fasteners.yaml 读取 type=spring-pin 条目；缺失回退 _FALLBACK。
    Load type=spring-pin entries from fasteners.yaml; fall back on missing.

    YAML key 形如 D3_DIN1481，使用 nominal.d 而非 thread.d（无螺纹）。
    YAML keys like D3_DIN1481 use nominal.d (no thread on spring pins).
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, SpringPinSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") != "spring-pin":
                continue
            args = entry.get("factory", {}).get("args", {})
            nominal_d_raw = args.get("nominal_d")
            if nominal_d_raw is None:
                continue
            try:
                nd = float(nominal_d_raw)
            except (TypeError, ValueError):
                continue
            # 内部 key 形如 "D3" / "D4" — 整数化以避免 "D3.0"
            # Internal key like "D3" / "D4" — int-ified to avoid "D3.0"
            key = f"D{int(nd)}" if nd.is_integer() else f"D{nd}"

            nominal = entry.get("nominal", {})
            dims = entry.get("dimensions", {})
            try:
                specs[key] = SpringPinSpec(
                    nominal_d=float(nominal.get("d", nd)),
                    od_free=float(dims["od_free"]),
                    wall_t=float(dims["wall_t"]),
                    slit_w=float(dims["slit_w"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for key, spec in _FALLBACK.items():
        if key not in specs:
            specs[key] = spec
    return specs


_SPECS = _load_specs()


# ─── 4. 公开工厂函数 / Public factory ─────────────────────────
def make_spring_pin(nominal_d: float = 4, length: float = 12.0) -> Part:
    """生成 DIN 1481 弹簧销（自由状态）。
    Generate a DIN 1481 spring pin (free state).

    Geometry / 几何:
        - C 形截面（环 - 缝隙）在 XY 平面 / C-section in XY plane
        - 沿 +Z 拉伸 length / Extruded along +Z by `length`
        - 缝隙仅切外侧（+X 方向），保留对侧形成 C 形
          Slit cut only on the +X side, opposite side intact (C-shape)
        - 原点 = 底面中心 / Origin = bottom face centre

    Args:
        nominal_d: 公称直径 mm（3 或 4）/ nominal diameter (3 or 4)
        length:    销长 mm / pin length in mm

    Returns:
        Part: 自由状态弹簧销实体 / free-state spring pin solid
    """
    key = f"D{int(nominal_d)}" if float(nominal_d).is_integer() else f"D{nominal_d}"
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown nominal_d {nominal_d!r}, available: {available}")

    spec = _SPECS[key]

    od = spec.od_free
    id_ = od - 2 * spec.wall_t
    slit_w = spec.slit_w
    # 缝隙矩形：X 长度（缝宽）= slit_w，Y 长度贯穿截面（>od 保证完全切开外壁）
    # 矩形中心偏向 +X，使其仅切右侧外壁、不切对侧 → C 形截面
    # Slit rectangle: X width = slit_w, Y length spans (>od) to fully cut through
    # one wall; rectangle X-centre offset to +X so the slit cuts only one wall,
    # leaving the opposite wall intact → C-shaped cross-section.
    slit_y_len = od + 1.0
    # 矩形左边缘对齐内圆 +X 端 (X = id_/2)，右边缘超出外圆
    # Left edge at inner circle +X edge (X = id_/2); right edge past outer circle
    slit_x_center = id_ / 2 + slit_w / 2

    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            Circle(od / 2)                          # 外圆 / outer
            Circle(id_ / 2, mode=Mode.SUBTRACT)     # 挖空内径 / hollow
            with Locations((slit_x_center, 0, 0)):
                Rectangle(slit_w, slit_y_len, mode=Mode.SUBTRACT)
        extrude(amount=length)

    return bp.part


# ─── 5. 独立运行导出 / Standalone export ─────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    L_demo = 12.0
    for key, spec in _SPECS.items():
        nd = spec.nominal_d
        part = make_spring_pin(nominal_d=nd, length=L_demo)
        slug = f"d{int(nd)}" if nd.is_integer() else f"d{nd}"
        out = cache_dir / f"{slug}_din1481_L{int(L_demo)}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm3")
