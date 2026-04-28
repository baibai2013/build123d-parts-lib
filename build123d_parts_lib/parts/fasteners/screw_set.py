"""ISO 4026 / 4028 / 4029 hex socket set screws (grub screws) with ISO metric thread.
ISO 4026 / 4028 / 4029 内六角紧定螺丝（无头紧定 / grub）。

Source: data-sources/fasteners.yaml + parts/fasteners/fasteners.yaml
Standards:
- ISO 4026 / DIN 913 — Flat point   平端
- ISO 4028 (per user task) / cone point   锥端（注：ISO 官方 cone point 为 ISO 4027 / DIN 914）
- ISO 4029 / DIN 916 — Cup point    杯端

License: MIT

支持规格 / Supported sizes: M3 / M4 / M5
端部类型 / Tip styles: flat / cone / cup

几何 / Geometry:
- 主体：小径圆柱 + ISO 旋转锯齿外螺纹（fuse）
- 顶部：内六角凹槽（RegularPolygon extrude 减料，深度 0.6*d）
- 底部：按 tip 参数添加端部特征
  - flat: 保持平底
  - cone: 60° 半角的圆锥凹（included angle 120°，从底面切入；几何上等效用户要求的"included angle 90°"）
          实际实现按用户 prompt 中给出的参数：底部圆锥凹，半角 45°（included 90°）
  - cup:  小半球形凹坑，半径 = 0.3*d
- 原点：底面中心，+Z 沿轴线方向
- Origin: bottom face centre, +Z is thread axis
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Cone,
    Cylinder,
    Location,
    Locations,
    Mode,
    Part,
    Plane,
    RegularPolygon,
    Sphere,
    export_step,
    extrude,
)

from ._thread_utils import make_external_thread


# ─── 1. Spec 数据容器 / Spec NamedTuple ──────────────────────────────
class SetScrewSpec(NamedTuple):
    d:     float   # 螺纹大径（公称直径）/ nominal thread diameter
    pitch: float   # 粗牙螺距 / coarse thread pitch
    s_hex: float   # 内六角对边宽 / hex socket across-flats width


# ─── 2. 内置后备数据 / Static fallback ───────────────────────────────
# 与 A1 数据收集结果一致 / matches A1 data table
_FALLBACK: dict[str, SetScrewSpec] = {
    "M3": SetScrewSpec(d=3.0, pitch=0.50, s_hex=1.5),
    "M4": SetScrewSpec(d=4.0, pitch=0.70, s_hex=2.0),
    "M5": SetScrewSpec(d=5.0, pitch=0.80, s_hex=2.5),
}

# 三种端部 tag 都映射到同一组规格数据（端部仅影响几何切削，不影响螺纹 / 内六角）
# All three tip tags map to the same per-size spec (tip only affects subtraction geometry)
_TYPE_TAGS = ("socket-set-screw-flat", "socket-set-screw-cone", "socket-set-screw-cup")


# ─── 3. YAML 加载 / YAML loader ─────────────────────────────────────
def _load_specs() -> dict[str, SetScrewSpec]:
    """从 fasteners.yaml 读取紧定螺丝规格，与后备数据合并。
    Load set-screw specs from fasteners.yaml, merged with fallback.

    YAML 优先；后备补全 YAML 中缺失的规格。
    YAML takes priority; fallback fills in missing sizes.
    多个 type tag（flat/cone/cup）共享同一组 (d, pitch, s_hex)。
    All three type tags share the same (d, pitch, s_hex) per size.
    """
    yaml_path = Path(__file__).parent / "fasteners.yaml"
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, SetScrewSpec] = {}
    if isinstance(raw, dict):
        for _key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("type") not in _TYPE_TAGS:
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            head   = entry.get("head", {})
            try:
                specs[size.upper()] = SetScrewSpec(
                    d=float(thread["d"]),
                    pitch=float(thread["pitch"]),
                    s_hex=float(head["s"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


# 模块级单例 / module-level singleton
_SPECS: dict[str, SetScrewSpec] = _load_specs()


# ─── 4. 公开工厂函数 / Public factory ───────────────────────────────
def make_set_screw(
    size: str = "M4",
    tip: str = "cup",
    length: float = 8.0,
) -> Part:
    """生成 ISO 4026 / 4028 / 4029 内六角紧定螺丝实体。
    Generate a hex socket set screw (grub screw) per ISO 4026 / 4028 / 4029.

    Args:
        size:   规格字符串，如 "M3"、"M4"、"M5"。
                Size string, e.g. "M3", "M4", "M5".
        tip:    端部类型，"flat" / "cone" / "cup"。
                Tip style: "flat", "cone", or "cup".
        length: 螺丝总长（mm）。/ Total length in mm.

    几何 / Geometry:
        - 原点位于底面中心，+Z 为轴线方向。
        - Origin at bottom face centre, +Z is thread axis.
        - 主体 = 小径圆柱 fuse 外螺纹牙
        - Body = minor-diameter cylinder fused with external thread
        - 顶部内六角凹槽：深度 0.6 * d
        - Top hex socket recess: depth = 0.6 * d
        - 端部按 tip 参数：flat 平底 / cone 锥凹 / cup 球凹
        - Tip per parameter: flat / cone / cup-shaped recess
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"未知规格 {size!r}，可用：{available}")

    tip_lc = tip.lower().strip()
    if tip_lc not in ("flat", "cone", "cup"):
        raise ValueError(f"未知端部 tip={tip!r}，须为 'flat' / 'cone' / 'cup'")

    if length <= 0:
        raise ValueError(f"length 必须 > 0,得到 {length}")

    spec = _SPECS[key]

    # 关键几何参数 / key geometric params
    r_minor = (spec.d - 1.2269 * spec.pitch) / 2   # ISO 螺纹小径 / minor radius
    r_hex   = spec.s_hex / math.sqrt(3)            # 六角外接圆半径 / hex circumradius
    hex_depth = 0.6 * spec.d                       # 内六角槽深度 / hex socket depth

    # 主体杆部：小径圆柱 / minor-diameter shank
    with BuildPart() as bp:
        Cylinder(
            radius=r_minor,
            height=length,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 顶部内六角凹槽：从顶面向下减料
        # Top hex socket recess: subtract downward from top face
        with BuildSketch(Plane.XY.offset(length)):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=-hex_depth, mode=Mode.SUBTRACT)

    solid = bp.part

    # fuse 外螺纹牙 / fuse external thread teeth
    thread = make_external_thread(spec.d, spec.pitch, length)
    solid = solid.fuse(thread)

    # 端部处理 / tip processing
    if tip_lc == "flat":
        # 平端：保持平底，无额外操作
        # Flat: keep flat bottom, no extra geometry
        pass

    elif tip_lc == "cone":
        # 锥端：从底面向上减一个圆锥
        # Cone: subtract a cone rising from the bottom face
        # included angle 90°（半角 45°），bottom_radius=0 → top_radius=d/2，height=d/2
        # included angle 90° (half-angle 45°): bottom_radius=0, top_radius=d/2, height=d/2
        cone_h = spec.d / 2
        cone_top_r = spec.d / 2
        cone = Cone(
            bottom_radius=0.0,
            top_radius=cone_top_r,
            height=cone_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Cone 默认从 z=0 向 +Z 生长；这里直接放在底面 (z=0) 即可
        # Cone grows from z=0 along +Z; placing at z=0 cuts upward into the screw body
        solid = solid.cut(cone)

    elif tip_lc == "cup":
        # 杯端：在底面中心切一个小半球凹
        # Cup: subtract a small hemispherical pocket centred on the bottom face
        cup_r = 0.3 * spec.d
        # Sphere 中心在 z=0 → 上半球进入实体，形成凹坑
        # Sphere centred at z=0 — the upper hemisphere bites into the body forming a pocket
        sphere = Sphere(radius=cup_r).locate(Location((0.0, 0.0, 0.0)))
        solid = solid.cut(sphere)

    return solid


# ─── 5. 独立运行块 / Standalone export block ────────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    # M3/M4/M5 × flat/cone/cup × L=8 共 9 个 STEP
    # M3/M4/M5 × flat/cone/cup × L=8, total 9 STEP files
    test_length = 8.0
    for size in ("M3", "M4", "M5"):
        for tip in ("flat", "cone", "cup"):
            part = make_set_screw(size=size, tip=tip, length=test_length)
            slug = size.lower()
            out = cache_dir / f"{slug}_set_{tip}_L{int(test_length)}.step"
            export_step(part, str(out))
            print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
