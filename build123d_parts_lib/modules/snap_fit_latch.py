"""FDM-friendly snap-fit latch (cantilever style).

经典悬臂卡扣：悬臂梁 + 末端钩凸起。
按 FDM 打印特性优化：横向打印、层纹顺柔性方向。

MVP 简化版：主体用 Box，钩凸起用小 Box 叠加（避免复杂多边形在 OCP 中的
三角化问题）。未来迭代可加斜面引导（chamfer）。

License: MIT
"""
from __future__ import annotations

from build123d import (
    Align,
    Box,
    BuildPart,
    Location,
    Locations,
    Part,
)


def make_snap_latch(
    width: float = 4.0,
    length: float = 12.0,
    thickness: float = 1.2,
    hook_size: float = 0.8,
) -> Part:
    """生成一根悬臂卡扣（cantilever latch）。

    Args:
        width: 悬臂宽度（Y 方向，默认 4 mm）
        length: 悬臂长度（X 方向，默认 12 mm）
        thickness: 悬臂厚度（Z 方向主体，默认 1.2 mm 适合 FDM 柔性）
        hook_size: 末端钩凸起尺寸（X=Z，默认 0.8 mm）

    几何：
        - 悬臂根部在 X=0，伸出方向 +X
        - 厚度中心线 Z=0
        - 钩位于 +X 末端，朝 +Z 凸起 hook_size
    """
    if hook_size >= thickness:
        raise ValueError(
            f"hook_size ({hook_size}) should be < thickness ({thickness})"
        )

    with BuildPart() as latch:
        # 悬臂梁主体：Align=MIN → 梁根在 X=0 起始，沿 +X 伸出
        Box(
            length, width, thickness,
            align=(Align.MIN, Align.CENTER, Align.CENTER),
        )
        # 钩凸起：在悬臂末端 +X 侧、+Z 顶面上方凸出 hook_size
        # 放置在 X=length-hook_size/2（末端 hook_size 宽块），Z=thickness/2+hook_size/2
        with Locations(Location((length - hook_size / 2, 0,
                                   thickness / 2 + hook_size / 2))):
            Box(hook_size, width, hook_size)

    return latch.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_snap_latch()
    export_step(p, "/tmp/snap_latch.step")
    print(f"OK: snap latch, volume={p.volume:.2f} mm³")
