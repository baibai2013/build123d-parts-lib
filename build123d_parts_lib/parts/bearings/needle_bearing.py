"""冲压外圈滚针轴承 / Drawn-Cup Needle Roller Bearing (HK series).

Simplified engineering model: outer drawn-cup shell only (no needle geometry).
One closed end (z=0 face); open end at z=B for shaft entry.

Supported models (DIN 618-1 / ISO 3030):
    HK0608  —  Φ6 bore × Φ10 OD × 8 mm wide
    HK0810  —  Φ8 bore × Φ12 OD × 10 mm wide
    HK1010  — Φ10 bore × Φ14 OD × 10 mm wide

Geometry (local Z: closed end = 0, open/shaft end = B):
    Outer shell: thin-wall drawn steel cup, wall_t ≈ 0.4 mm
    Bottom cap : wall_t at z = 0
    Inner bore : Φd clearance for shaft / needles from z=wall_t to z=B

Standards: DIN 618-1 / ISO 3030
License: Apache-2.0
Source: Schaeffler/INA HK drawn-cup needle bearing catalog (confidence 4)
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml
from build123d import (
    Align,
    BuildPart,
    Cylinder,
    GeomType,
    Mode,
    Part,
    Pos,
    chamfer,
    export_step,
)

# ── Spec ──────────────────────────────────────────────────────────────────────

class NeedleBearingSpec(NamedTuple):
    d: float          # bore (shaft) diameter  mm
    D: float          # outer diameter  mm
    B: float          # width  mm
    shell_wall_t: float  # drawn-cup wall thickness  mm


_FALLBACK: dict[str, NeedleBearingSpec] = {
    "HK0608": NeedleBearingSpec(d=6.0,  D=10.0, B=8.0,  shell_wall_t=0.4),
    "HK0810": NeedleBearingSpec(d=8.0,  D=12.0, B=10.0, shell_wall_t=0.4),
    "HK1010": NeedleBearingSpec(d=10.0, D=14.0, B=10.0, shell_wall_t=0.4),
}

GEOMETRY_INVARIANTS = {
    "r_inner_cup_gt_r_bore": "shell inner radius > shaft bore radius",
    "wall_t_lt_2mm": "drawn-cup wall thickness < 2 mm (thin stamped steel)",
}


def _load_specs() -> dict[str, NeedleBearingSpec]:
    """Load HK needle bearing specs from bearings.yaml."""
    yaml_path = Path(__file__).parent / "bearings.yaml"
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    specs: dict[str, NeedleBearingSpec] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "drawn-cup-needle-bearing":
            continue
        dims = entry.get("dimensions", {})
        geo  = entry.get("geometry", {})
        specs[key.upper()] = NeedleBearingSpec(
            d=dims["d"],
            D=dims["D"],
            B=dims["B"],
            shell_wall_t=geo.get("shell_wall_t", 0.4),
        )
    return specs


_SPECS: dict[str, NeedleBearingSpec] = _load_specs() or _FALLBACK


def make_needle_bearing(model: str = "HK0608") -> Part:
    """Generate a drawn-cup needle roller bearing outer shell (simplified — no needles).

    冲压外圈滚针轴承外圈壳体（工程简化，不建滚针；单体 Part）。

    Args:
        model: 型号字符串，如 "HK0608"。大小写不敏感。

    Geometry:
        origin at bottom center (closed end face center);
        axis along Z; outer OD × total width (Z 方向).
    """
    key = model.upper()
    if key not in _SPECS:
        available = ", ".join(sorted(_SPECS.keys()))
        raise ValueError(
            f"Unknown needle bearing model {model!r}. "
            f"Available: {available}"
        )

    spec = _SPECS[key]
    d, D, B, wall_t = spec.d, spec.D, spec.B, spec.shell_wall_t

    # Geometry invariant assertions
    r_inner_cup = D / 2 - wall_t
    assert r_inner_cup > d / 2, (
        f"r_inner_cup={r_inner_cup:.2f} must be > r_bore={d/2:.2f}"
    )
    assert wall_t < 2.0, f"wall_t={wall_t} must be < 2 mm for drawn-cup type"

    with BuildPart() as p:
        # 外圆筒（全实心）/ Full outer cylinder
        Cylinder(
            radius=D / 2,
            height=B,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # 内腔（保留密闭端底板）/ Inner cavity — leave closed-end cap at z=0
        # Cavity starts at z=wall_t and goes to z=B (open end)
        Pos(0, 0, wall_t) * Cylinder(
            radius=r_inner_cup,
            height=B - wall_t + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )

        # 开口端倒角 C0.3 / Open-end outer-rim chamfer C0.3 (ease assembly)
        try:
            open_rim = [
                e for e in p.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - D / 2) < 0.2 and abs(e.center().Z - B) < 0.2
            ]
            if open_rim:
                chamfer(open_rim, length=0.3)
        except Exception:
            pass

    return p.part


if __name__ == "__main__":
    from ocp_vscode import Camera, show
    from ocp_vscode.comms import port_check
    from ocp_vscode.state import get_ports

    print("Building HK drawn-cup needle bearings ...")
    for model_name in ("HK0608", "HK0810", "HK1010"):
        part = make_needle_bearing(model_name)
        bb   = part.bounding_box()
        spec = _SPECS[model_name]
        print(f"  {model_name}: vol={part.volume:.1f} mm³  "
              f"BBox {bb.size.X:.2f}×{bb.size.Y:.2f}×{bb.size.Z:.2f} mm  "
              f"(exp {spec.D}×{spec.D}×{spec.B})")
        assert part.volume > 0,              f"❌ {model_name} volume ≤ 0"
        assert abs(bb.size.X - spec.D) < 0.5, f"❌ {model_name} X 偏差: {bb.size.X:.2f}"
        assert abs(bb.size.Z - spec.B) < 0.2, f"❌ {model_name} Z 偏差: {bb.size.Z:.2f}"
        print(f"  BRep + BBox ✓")

    # Show representative HK0608
    part_hk = make_needle_bearing("HK0608")
    try:
        active_port = next(
            (int(p) for p in get_ports() if port_check(int(p))), None
        )
        if active_port:
            from ocp_vscode import set_port
            set_port(active_port)
        show(part_hk, names=["needle_bearing_HK0608"], colors=["silver"],
             reset_camera=Camera.ISO)
        print("OCP Viewer: HK0608 ✓")
    except Exception as e:
        print(f"OCP preview skipped: {e}")

    # Export representative STEP
    out_dir   = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    step_path = out_dir / "needle_bearing.step"
    export_step(part_hk, str(step_path))
    print(f"STEP: {step_path}")
