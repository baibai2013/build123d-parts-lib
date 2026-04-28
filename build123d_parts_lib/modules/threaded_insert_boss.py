"""Heat-set threaded insert boss (FDM standard: M3×5-OD4.2, predrill ⌀4.0).

常见 FDM 固定方案：在打印件上留一个圆柱凸台，预孔热压铜螺母。
参数默认为 M3×5-OD4.2 铜螺母，可调其他规格。

Reference: data-sources/fasteners.yaml:M3_ISO4762.threaded_insert
License: MIT
"""
from __future__ import annotations

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Cylinder,
    Mode,
    Part,
    extrude,
)


def make_m3_boss(
    insert_od: float = 4.2,
    insert_length: float = 5.0,
    predrill_d: float = 4.0,
    boss_outer_d: float = 5.5,
    height: float | None = None,
) -> Part:
    """生成 FDM 热压铜螺母柱。

    Args:
        insert_od: 铜螺母外径（M3×5 默认 4.2）。目前仅作记录用。
        insert_length: 铜螺母长度（决定预孔深度，默认 5.0）
        predrill_d: 预孔直径（建议 4.0，略小于 OD，热压微张开后贴合）
        boss_outer_d: 凸台外径（默认 5.5，壁厚 ~0.75 mm）
        height: 凸台总高（默认 = insert_length + 2mm 余量）

    几何：
        原点在柱底面中心（XY），柱沿 +Z 伸出 `height`。
        顶面居中有一个 `predrill_d × insert_length` 的盲孔。
    """
    if height is None:
        height = insert_length + 2.0
    if boss_outer_d <= predrill_d:
        raise ValueError(
            f"boss_outer_d ({boss_outer_d}) must > predrill_d ({predrill_d})"
        )

    with BuildPart() as boss:
        # 实心凸台：底面在 Z=0（Align=MIN）
        Cylinder(
            radius=boss_outer_d / 2, height=height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 顶面预孔
        top = boss.faces().sort_by(Axis.Z)[-1]
        with BuildSketch(top):
            Circle(predrill_d / 2)
        extrude(amount=-insert_length, mode=Mode.SUBTRACT)

    return boss.part


if __name__ == "__main__":
    from build123d import export_step
    p = make_m3_boss()
    export_step(p, "/tmp/m3_boss.step")
    print(f"OK: M3 boss, volume={p.volume:.2f} mm³, height default=7mm")
