"""Shared ISO metric thread geometry for fastener modules.
ISO 公制螺纹旋转体共用工具，供各紧固件模块导入。
"""
from __future__ import annotations

import math

from build123d import Axis, Face, Solid, Vector, Wire


def make_external_thread(d: float, pitch: float, length: float) -> Solid:
    """ISO 外螺纹旋转体（锯齿牙形绕 Z 轴旋转 360°），用于 fuse 到杆部。
    ISO external thread solid via revolve — fuse onto shank.

    Sawtooth peaks at r_major (d/2), roots at r_minor (d/2 - 0.6134*pitch).
    """
    n = math.ceil(length / pitch) + 1
    r_major = d / 2
    r_minor = r_major - 0.6134 * pitch

    pts: list[tuple[float, float]] = []
    for i in range(n):
        z0 = i * pitch
        pts.append((r_minor, z0))
        pts.append((r_major, z0 + pitch * 0.5))
    pts.append((r_minor, n * pitch))
    pts.append((0.0, n * pitch))
    pts.append((0.0, 0.0))

    pts3d = [Vector(r, 0.0, z) for r, z in pts]
    pts3d.append(pts3d[0])
    return Solid.revolve(Face(Wire.make_polygon(pts3d)), 360, Axis.Z)


def make_internal_thread(d: float, pitch: float, length: float) -> Solid:
    """ISO 内螺纹减料旋转体（锯齿牙形绕 Z 轴旋转 360°），用于 subtract 自螺母体。
    ISO internal thread subtract solid via revolve — cut from nut/insert body.

    Peaks at r_major (d/2) pointing inward; subtracting leaves ridges in bore.
    """
    n = math.ceil(length / pitch) + 1
    r_major = d / 2
    r_minor = r_major - 0.6134 * pitch

    pts: list[tuple[float, float]] = [(0.0, 0.0)]
    for i in range(n):
        z0 = i * pitch
        pts.append((r_major, z0))
        pts.append((r_minor, z0 + pitch * 0.5))
    pts.append((r_major, n * pitch))
    pts.append((0.0, n * pitch))

    pts3d = [Vector(r, 0.0, z) for r, z in pts]
    pts3d.append(pts3d[0])
    return Solid.revolve(Face(Wire.make_polygon(pts3d)), 360, Axis.Z)
