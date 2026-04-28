"""Hex standoff (brass spacer) — Female-Female (FF) and Male-Female (MF).

Standard:  Market convention (no unified ISO/DIN)
License:   MIT

支持规格 / Supported sizes: M3, M4
支持样式 / Supported styles:
  FF (Female-Female / 双通): 两端均为内螺纹
                              both ends internal thread, depth = 0.8*L per end
  MF (Male-Female / 单通):   一端内螺纹 + 另一端外螺纹小杆
                              one end internal thread, other end male stud
                              stud length: 6mm (M3), 8mm (M4)

几何 / Geometry:
- 六棱柱主体(对边宽 s) / Hex prism body with across-flats width s
- 原点底面中心，+Z 为轴方向 / Origin at bottom face center, +Z is axis direction
- FF: 两端各有内螺纹孔 / FF: internal thread holes from both ends
- MF: 底面内螺纹孔；顶面外螺纹小杆 fuse 在顶面之上
       MF: internal thread bore from bottom; external thread stud fused on top
- 两端 0.3mm 倒角(Pattern 14) / 0.3mm chamfer at top/bottom edges (Pattern 14)
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
    Cylinder,
    Location,
    Locations,
    Part,
    Plane,
    RegularPolygon,
    export_step,
    extrude,
)

from ._thread_utils import make_external_thread, make_internal_thread


# ─── 1. Spec 数据容器 / Spec data container ─────────────────────────────────
class StandoffSpec(NamedTuple):
    d:     float   # 螺纹大径 / thread major diameter
    pitch: float   # 粗牙螺距 / coarse pitch
    s:     float   # 对边宽 / across-flats width


# ─── 2. 内置后备数据 / Built-in fallback data ───────────────────────────────
_FALLBACK: dict[str, StandoffSpec] = {
    "M3": StandoffSpec(d=3.0, pitch=0.50, s=5.5),
    "M4": StandoffSpec(d=4.0, pitch=0.70, s=7.0),
}

# MF 样式默认外螺纹小杆长度 / default male-stud length for MF style
_MF_STUD_LENGTH: dict[str, float] = {
    "M3": 6.0,
    "M4": 8.0,
}


# ─── 3. YAML 加载(优先 YAML，缺失 key 用 fallback 补) ───────────────────────
# YAML loading: YAML takes priority, fallback fills missing keys
def _load_specs() -> dict[str, StandoffSpec]:
    """从 _entries_standoff.yaml 读取六角铜柱规格。
    Load hex standoff specs from _entries_standoff.yaml.
    """
    # _entries_standoff.yaml is at repo root, two levels above this file
    # _entries_standoff.yaml 位于仓库根目录，本文件向上两级
    yaml_path = Path(__file__).parent / "fasteners.yaml"

    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(_FALLBACK)

    specs: dict[str, StandoffSpec] = {}
    if isinstance(raw, dict):
        for _k, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            # 接受两种 type tag(FF / MF) / accept both FF and MF type tags
            if entry.get("type") not in ("hex-standoff-ff", "hex-standoff-mf"):
                continue
            size = entry.get("factory", {}).get("args", {}).get("size", "")
            if not size:
                continue
            thread = entry.get("thread", {})
            dims = entry.get("dimensions", {})
            try:
                # 后写覆盖前写无所谓，FF/MF 两种 size 字段都一致
                # FF and MF entries share the same d/pitch/s for a given size
                specs[size.upper()] = StandoffSpec(
                    d     = float(thread["d"]),
                    pitch = float(thread["pitch"]),
                    s     = float(dims["s"]),
                )
            except (KeyError, TypeError, ValueError):
                continue

    for size, spec in _FALLBACK.items():
        if size not in specs:
            specs[size] = spec
    return specs


_SPECS = _load_specs()


# ─── 4. 公开工厂函数 / Public factory function ─────────────────────────────
def make_hex_standoff(
    size: str = "M3",
    length: float = 10.0,
    style: str = "FF",
) -> Part:
    """生成六角铜柱隔离柱(FF 双通 / MF 单通)。
    Generate a hex standoff (FF: female-female / MF: male-female).

    Args:
        size:   规格字符串 / Size string, e.g. "M3", "M4"
        length: 六角柱总长 / total hex prism length (mm)
        style:  "FF" (Female-Female / 双通) or "MF" (Male-Female / 单通)

    几何 / Geometry:
        - 原点 = 六角柱底面中心 / Origin = bottom face centre of hex prism
        - +Z = 轴方向 / +Z = axis direction
        - 六角柱外接圆半径 r = s/sqrt(3) / hex circumradius r = s/sqrt(3)
        - FF: 两端内螺纹孔深 = min(0.8*L, L-1) / FF: bore depth at each end
        - MF: 底端内螺纹孔深 = min(0.8*L, L-1)；顶端外螺纹杆向上伸出
              MF: bottom bore + top male stud extending upward
    """
    key = size.upper().strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    style_key = style.upper().strip()
    if style_key not in ("FF", "MF"):
        raise ValueError(f"Unknown style {style!r}, must be 'FF' or 'MF'")

    if length <= 2.0:
        raise ValueError(f"length must be > 2.0 mm, got {length}")

    spec = _SPECS[key]
    r_hex = spec.s / math.sqrt(3)              # 外接圆半径 / hex circumradius

    # 内螺纹孔深 = 0.8 * L，但留 1mm 防穿透 / bore depth with 1mm safety margin
    bore_depth = min(length * 0.8, length - 1.0)

    # ── (a) 六棱柱主体 / hex prism body ────────────────────────────────────
    with BuildPart() as body_bp:
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=r_hex, side_count=6)
        extrude(amount=length)

    solid = body_bp.part

    # ── (b) 底端内螺纹减料 (z=0 朝上) / bottom internal thread cut ────────
    bottom_thread = make_internal_thread(spec.d, spec.pitch, bore_depth)
    solid = solid.cut(bottom_thread)

    if style_key == "FF":
        # FF：顶端也减一段内螺纹 / FF: cut top internal thread as well
        # 把另一段螺纹放到 z = length - bore_depth → 顶到 z = length
        # Translate top thread so its top face sits at z = length
        top_thread = make_internal_thread(spec.d, spec.pitch, bore_depth)
        top_thread = top_thread.translate((0, 0, length - bore_depth))
        solid = solid.cut(top_thread)

    elif style_key == "MF":
        # MF：顶端 fuse 外螺纹小杆 / MF: fuse external-thread male stud on top
        stud_len = _MF_STUD_LENGTH.get(key, 6.0)

        # 小径杆体 + 外螺纹 / minor-diameter shank + external thread
        r_minor = (spec.d - 1.2269 * spec.pitch) / 2
        with BuildPart() as stud_bp:
            Cylinder(
                radius=r_minor,
                height=stud_len,
                align=(Align.CENTER, Align.CENTER, Align.MIN),
            )
        thread_add = make_external_thread(spec.d, spec.pitch, stud_len)
        stud = stud_bp.part.fuse(thread_add)

        # 移到六角柱顶面之上 / move stud above hex prism top face
        stud = stud.translate((0, 0, length))
        solid = solid.fuse(stud)

    # ── (c) 两端倒角 (Pattern 14, 闭合边过滤) ──────────────────────────────
    # Chamfer top & bottom closed edges (only the hex's outer top/bottom rim)
    # 容差用 0.2mm,避免 OCC fuse 后顶点漂移导致过滤失败
    # Use 0.2mm tolerance to handle OCC vertex drift after boolean ops
    chamfer_size = 0.3
    top_z = length
    bot_z = 0.0

    edges_to_chamfer = []
    for e in solid.edges():
        if not e.is_closed:
            continue
        cz = e.center().Z
        # 只挑六棱柱顶/底圈,避开内螺纹圆环 / only outer hex rims, skip thread rings
        # 通过边长过滤:六角周长 ≈ 6 * r_hex,内螺纹圆周 ≈ pi * d (更小)
        # Filter by edge length: hex perimeter ~6*r_hex; thread ring perim ~pi*d
        hex_perim_approx = 6.0 * r_hex
        if abs(e.length - hex_perim_approx) > 1.5:
            continue
        if abs(cz - top_z) < 0.2 or abs(cz - bot_z) < 0.2:
            edges_to_chamfer.append(e)

    if edges_to_chamfer:
        try:
            solid = solid.chamfer(chamfer_size, None, edges_to_chamfer)
        except Exception:
            # 倒角失败静默跳过(几何主体已正确) / silently skip if chamfer fails
            pass

    return solid


# ─── 5. 独立运行块 / standalone run block ──────────────────────────────────
if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    tasks = [
        ("M3", "FF", 10.0),
        ("M3", "MF", 10.0),
        ("M4", "FF", 10.0),
        ("M4", "MF", 10.0),
    ]
    for size, style, length in tasks:
        part = make_hex_standoff(size=size, length=length, style=style)
        slug = f"{size.lower()}_standoff_{style.lower()}_L{int(length)}"
        out = cache_dir / f"{slug}.step"
        export_step(part, str(out))
        print(f"OK: {out.name}  vol={part.volume:.1f} mm³")
