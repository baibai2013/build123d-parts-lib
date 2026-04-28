"""FDM heat-set brass threaded inserts (Ruthex / InsertEZ compatible).
热熔铜螺母嵌件，适用于 FDM 3D 打印件（Ruthex / InsertEZ 兼容）。

Standards: Ruthex RX-M* / InsertEZ (de facto FDM standard)
License: MIT

Supported sizes / 支持规格: M2.5, M3, M4, M5

Geometry / 几何说明:
- Origin at bottom face centre / 原点在底面中心
- Insert body extends along +Z by `length` / 嵌件沿 +Z 轴延伸 length 高度
- Lower pilot section (od_lower, lower_h) for press-in alignment
  下段导入柱（od_lower, lower_h），用于压入导向
- Upper knurled body (od_upper, length) with triangular knurl rings
  上段带倒刺滚花主体（od_upper），设计有三角形环形倒刺
- Central bore with ISO internal thread geometry (sawtooth revolve)
  内孔带 ISO 内螺纹几何（锯齿旋转体）
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from build123d import (
    Axis,
    Face,
    Part,
    Solid,
    Vector,
    Wire,
    export_step,
)

from ._thread_utils import make_external_thread


class InsertSpec(NamedTuple):
    d:        float  # nominal thread diameter (bore) / 螺纹公称直径（内孔径）
    od_upper: float  # outer diameter of knurled upper body / 上段（滚花）外径
    od_lower: float  # outer diameter of pilot lower section / 下段（导入）外径
    length:   float  # total insert length / 嵌件总长度
    lower_h:  float  # height of lower pilot section / 下段高度
    n_knurl:  int    # number of knurl rings on upper body / 上段倒刺环数
    pitch_k:  float  # axial pitch of each knurl ring / 单个倒刺环轴向间距


_SPECS: dict[str, InsertSpec] = {
    # d    od_up  od_lo  len   lo_h  n_k  pitch_k
    "M2.5": InsertSpec(d=2.5, od_upper=3.5, od_lower=3.2, length=4.0, lower_h=0.8, n_knurl=3, pitch_k=0.6),
    "M3":   InsertSpec(d=3.0, od_upper=4.6, od_lower=4.2, length=5.0, lower_h=1.0, n_knurl=3, pitch_k=0.8),
    "M4":   InsertSpec(d=4.0, od_upper=5.6, od_lower=5.2, length=6.0, lower_h=1.2, n_knurl=4, pitch_k=0.8),
    "M5":   InsertSpec(d=5.0, od_upper=6.4, od_lower=5.9, length=8.0, lower_h=1.5, n_knurl=5, pitch_k=0.9),
}


def _make_insert_body(spec: InsertSpec) -> Solid:
    """Outer insert body via revolve of closed XZ profile around Z axis.
    通过封闭 XZ 截面绕 Z 轴旋转 360° 生成嵌件外体。

    Profile (r, z) sequence / 截面轮廓点序列:
      axis bottom (0, 0)
      → pilot outer edge (r_lo, 0)
      → pilot top (r_lo, lower_h)
      → shoulder to upper (r_up, lower_h)
      → n_knurl triangular ridge rings
      → top outer edge (r_up, length)
      → axis top (0, length)
      → close back to (0, 0)

    Each knurl ring at z0 / 每个倒刺环（z0 处）:
      (r_up, z0) → (r_up + 0.25, z0 + pitch_k*0.3) → (r_up, z0 + pitch_k*0.6)
    """
    r_up = spec.od_upper / 2
    r_lo = spec.od_lower / 2
    lh   = spec.lower_h
    L    = spec.length
    n    = spec.n_knurl
    pk   = spec.pitch_k

    # Available height above shoulder for knurl rings / 倒刺区域可用高度
    knurl_zone = L - lh
    # Start the first knurl ring slightly above shoulder / 第一环略高于台阶
    knurl_start = lh + pk * 0.5

    pts: list[tuple[float, float]] = []

    # Bottom axis point / 底部轴线点
    pts.append((0.0, 0.0))
    # Pilot lower outer edge / 下段外径底部
    pts.append((r_lo, 0.0))
    # Top of pilot section / 下段顶部
    pts.append((r_lo, lh))
    # Shoulder step to upper body / 台阶至上段
    pts.append((r_up, lh))

    # Knurl rings / 倒刺环
    for i in range(n):
        z0 = knurl_start + i * pk
        # Clip rings to remain within insert body / 环不超出嵌件顶部
        if z0 + pk * 0.6 > L - 0.1:
            break
        pts.append((r_up,        z0))
        pts.append((r_up + 0.25, z0 + pk * 0.3))
        pts.append((r_up,        z0 + pk * 0.6))

    # Top outer edge / 顶部外径
    pts.append((r_up, L))
    # Top axis point / 顶部轴线点
    pts.append((0.0, L))
    # Close back to start / 封闭回起点
    pts.append((0.0, 0.0))

    pts3d = [Vector(r, 0.0, z) for r, z in pts]
    return Solid.revolve(Face(Wire.make_polygon(pts3d)), 360, Axis.Z)


_INSERT_PITCH: dict[float, float] = {2.5: 0.45, 3.0: 0.5, 4.0: 0.7, 5.0: 0.8}


def make_threaded_insert(size: str = "M3") -> Part:
    """Generate an FDM heat-set threaded insert solid with knurls and internal thread.
    生成带倒刺滚花和内螺纹的 FDM 热熔嵌件实体。

    Args:
        size: Size string / 规格字符串，e.g. "M3", "M4".

    Returns:
        Part: Outer body with internal thread subtracted.
              外体减去内螺纹后的 Part。

    Geometry / 几何:
        - Origin at bottom face centre / 原点在底面中心
        - Insert body extends along +Z by `length` / 嵌件沿 +Z 轴延伸 length
    """
    key = size.upper().replace(" ", "").strip()
    if key not in _SPECS:
        available = ", ".join(_SPECS.keys())
        raise ValueError(f"Unknown size {size!r}, available: {available}")

    spec = _SPECS[key]

    outer  = _make_insert_body(spec)
    pitch  = _INSERT_PITCH.get(spec.d, spec.d * 0.175)
    thread = make_external_thread(spec.d, pitch, spec.length)

    return outer.cut(thread)


if __name__ == "__main__":
    cache_dir = Path(__file__).parent / "cache"
    cache_dir.mkdir(exist_ok=True)

    for size, spec in _SPECS.items():
        part = make_threaded_insert(size=size)
        slug = size.replace(".", "_").lower()
        out_path = cache_dir / f"{slug}_insert_fdm.step"
        export_step(part, str(out_path))
        print(f"OK: {out_path.name}  vol={part.volume:.2f} mm3")
