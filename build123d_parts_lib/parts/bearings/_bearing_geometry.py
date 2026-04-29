"""Shared industrial-quality bearing geometry.
共享工业级轴承几何构造模块。

所有深沟球轴承（标准、MR 微型、法兰）共用同一套核心几何：
- 外圈（带内侧滚道沟槽 / raceway groove on inner side）
- 内圈（带外侧滚道沟槽 / raceway groove on outer side）
- 滚珠（均匀分布在节圆 / steel balls on pitch circle）
- 保持架（带球窝 / cage with ball pockets）

All deep-groove ball bearings share the same core geometry:
- Outer ring with raceway groove
- Inner ring with raceway groove
- Steel balls distributed on pitch circle
- Cage with ball pockets

Geometry philosophy:
滚珠直径 d_ball ≈ 径向间隙 × 0.58（经验系数）
沟槽曲率半径 r_groove ≈ d_ball × 0.52 / 2（沟槽比球略大 4%，允许润滑间隙）
滚珠数量 n_balls 由节圆周长 / (球径 × 1.6) 得出，最少 6 颗
"""
from __future__ import annotations

import math

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Circle,
    Color,
    Compound,
    Cylinder,
    Locations,
    Mode,
    Part,
    Plane,
    PolarLocations,
    Sphere,
    revolve,
)


# ────── 设计系数 / Design Coefficients ─────────────────────────────
BALL_TO_GAP_RATIO   = 0.58   # 球径 / 径向间隙  ball diameter / radial gap
GROOVE_TO_BALL_RATIO = 0.52  # 沟槽半径 / 球径  groove radius / ball diameter
BALL_PITCH_RATIO    = 1.6    # 相邻球中心距 / 球径  ball-to-ball pitch / ball diameter
CAGE_THICKNESS_RATIO = 0.35  # 保持架壁厚 / 球径  cage thickness / ball diameter
CAGE_HEIGHT_RATIO   = 0.55   # 保持架高 / 轴承宽度 B
MIN_BALLS           = 6


def _compute_ball_geometry(d: float, D: float, B: float) -> dict:
    """Compute ball pitch and count from bearing bore/OD/width.
    由轴承内外径和宽度计算滚珠直径 / 节圆 / 数量。
    """
    r_i  = d / 2
    r_o  = D / 2
    r_pc = (r_i + r_o) / 2                # pitch circle radius / 节圆半径
    gap  = r_o - r_i                       # radial gap / 径向间隙

    # 球径受径向间隙和轴承宽度双重约束 / ball size capped by both gap and width
    d_ball = min(gap * BALL_TO_GAP_RATIO, B * 0.85)
    r_ball = d_ball / 2

    # 滚道沟槽半径（略大于球，预留润滑间隙）/ groove radius slightly > ball
    r_groove = d_ball * GROOVE_TO_BALL_RATIO

    # 滚珠数量：节圆周长 / 相邻球中心距 / ball count from pitch circle circumference
    circumference = 2 * math.pi * r_pc
    n_balls = max(MIN_BALLS, int(circumference / (d_ball * BALL_PITCH_RATIO)))

    return {
        "r_i": r_i, "r_o": r_o, "r_pc": r_pc, "gap": gap,
        "d_ball": d_ball, "r_ball": r_ball, "r_groove": r_groove,
        "n_balls": n_balls,
    }


def _make_raceway_torus(r_pc: float, r_groove: float) -> Part:
    """Build a torus on the pitch circle via XZ-plane revolve.
    在节圆上用 XZ 平面圆截面旋转生成滚道环面。

    Circle at (r_pc, 0) in Plane.XZ → revolve about Axis.Z → torus.
    在 Plane.XZ 上画圆 (r_pc, 0) → 绕 Axis.Z 旋转 → 环面。
    """
    with BuildSketch(Plane.XZ) as sk:
        with Locations((r_pc, 0)):
            Circle(r_groove)
    torus_part = revolve(sk.sketch, axis=Axis.Z)
    return torus_part


def make_deep_groove_bearing_compound(
    d: float,
    D: float,
    B: float,
    label_prefix: str = "",
) -> Compound:
    """Build an industrial-quality deep-groove ball bearing.
    构建工业级深沟球轴承（外圈 + 内圈 + 滚珠 + 保持架）。

    Args:
        d: 内径 / bore diameter (mm)
        D: 外径 / outer diameter (mm)
        B: 宽度 / width (mm)
        label_prefix: children label 前缀，如 "MR85ZZ/"

    Returns:
        Compound with labeled children:
          - {prefix}outer_ring
          - {prefix}inner_ring
          - {prefix}cage
          - {prefix}ball_0 ~ ball_N

    Coordinates: 轴承中心在原点，轴线沿 Z；Z 范围 -B/2 ~ +B/2。
    """
    g = _compute_ball_geometry(d, D, B)
    r_i, r_o, r_pc      = g["r_i"], g["r_o"], g["r_pc"]
    gap                  = g["gap"]
    d_ball, r_ball       = g["d_ball"], g["r_ball"]
    r_groove, n_balls    = g["r_groove"], g["n_balls"]

    # 圈壁厚度（外圈外径 - 节圆到球顶的距离）/ ring wall thickness
    ring_wall_offset = r_ball + gap * 0.12     # 圈与球顶的余量 / clearance above ball
    r_outer_inner    = r_pc + ring_wall_offset  # 外圈内径
    r_inner_outer    = r_pc - ring_wall_offset  # 内圈外径

    # ── 共享滚道环面 / shared raceway torus ───────────────────
    raceway_torus = _make_raceway_torus(r_pc, r_groove)

    # ── 外圈 / Outer Ring ─────────────────────────────────────
    with BuildPart() as outer_bp:
        Cylinder(
            radius=r_o, height=B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_outer_inner, height=B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )
    outer_ring = outer_bp.part - raceway_torus
    outer_ring.label = f"{label_prefix}outer_ring"
    outer_ring.color = Color(0.72, 0.72, 0.78)   # steel silver

    # ── 内圈 / Inner Ring ─────────────────────────────────────
    with BuildPart() as inner_bp:
        Cylinder(
            radius=r_inner_outer, height=B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_i, height=B,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )
    inner_ring = inner_bp.part - raceway_torus
    inner_ring.label = f"{label_prefix}inner_ring"
    inner_ring.color = Color(0.72, 0.72, 0.78)

    # ── 滚珠 / Steel Balls ────────────────────────────────────
    balls = []
    # PolarLocations 在 XY 平面节圆上均匀分布 / evenly spaced on pitch circle
    for i, loc in enumerate(PolarLocations(r_pc, n_balls)):
        ball = loc * Sphere(r_ball)
        ball.label = f"{label_prefix}ball_{i:02d}"
        ball.color = Color(0.85, 0.85, 0.88)   # polished steel
        balls.append(ball)

    # ── 保持架 / Cage ─────────────────────────────────────────
    # 薄环 + 球窝 / thin ring with ball pockets
    cage_t  = max(d_ball * CAGE_THICKNESS_RATIO, 0.25)
    cage_h  = B * CAGE_HEIGHT_RATIO
    r_cage_outer = r_pc + cage_t / 2
    r_cage_inner = r_pc - cage_t / 2

    with BuildPart() as cage_bp:
        Cylinder(
            radius=r_cage_outer, height=cage_h,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        )
        Cylinder(
            radius=r_cage_inner, height=cage_h,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
            mode=Mode.SUBTRACT,
        )
        # 球窝：用比球略大的 sphere 逐个扣除 / ball pockets
        with PolarLocations(r_pc, n_balls):
            Sphere(r_ball * 1.08, mode=Mode.SUBTRACT)
    cage = cage_bp.part
    cage.label = f"{label_prefix}cage"
    cage.color = Color(0.85, 0.72, 0.40)   # brass-like cage

    # ── 组装 Compound / Assemble ──────────────────────────────
    compound = Compound(children=[outer_ring, inner_ring, cage, *balls])
    compound.label = f"{label_prefix}bearing" if label_prefix else "bearing"
    return compound


def make_flange_disc(
    d: float,
    flange_D: float,
    flange_t: float,
    z_center: float,
    label: str = "flange",
) -> Part:
    """Build a flange disc with center bore.
    构建法兰圆盘（带中心孔）。

    Args:
        d: 内径 / bore diameter (mm)
        flange_D: 法兰外径 / flange outer diameter (mm)
        flange_t: 法兰厚度 / flange thickness (mm)
        z_center: 法兰中心 Z 坐标 / flange Z center position
        label: part label
    """
    r_flange = flange_D / 2
    r_inner  = d / 2

    with BuildPart() as flange_bp:
        with Locations((0, 0, z_center)):
            Cylinder(
                radius=r_flange, height=flange_t,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
            )
            Cylinder(
                radius=r_inner, height=flange_t,
                align=(Align.CENTER, Align.CENTER, Align.CENTER),
                mode=Mode.SUBTRACT,
            )
    flange = flange_bp.part
    flange.label = label
    flange.color = Color(0.72, 0.72, 0.78)
    return flange
