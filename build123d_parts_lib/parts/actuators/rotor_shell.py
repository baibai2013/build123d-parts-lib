"""QDD 外转子壳 / Outrunner Rotor Shell for QDD motor.

Factory: make_rotor_shell() → Part
  Thin-wall cylindrical cup (closed end-plate + center bore) with 14 arc-shaped
  magnet retention pockets and snap-in retention lips at the open end.

Geometry (Z=0 at open end, +Z toward closed end):
  OD          : Φ47.5 mm   (shell_wall_t=1.5 mm → inner r=22.25 mm)
  Height      : 12.0 mm    (2 mm taller than stator / magnets to fully enclose them)
  Center bore : Φ5 mm      (press-fit on rotor shaft h6)
  End-plate t : 2.0 mm     (closed end at z=rotor_h)

Magnet retention pockets (14 ×):
  Depth  : 0.5 mm  radially into the shell wall (pocket bottom r=21.75 mm)
  Height : 10.2 mm (magnet_h + 0.2 mm axial clearance)
  Arc    : ±11.57° per half (matching arc_magnet.magnet_half_deg)
  Purpose: tangential + axial location

Retention lips (14 ×, at open end):
  Protrusion : 0.3 mm radially inward (r: 21.75 → 22.05 mm)
  Height     : 2.0 mm axial (Z=0 to Z=2.0 mm)
  Arc        : same as pocket (±magnet_half_deg)
  Purpose    : snap-in mechanical fixation; magnet inserted at ~15° tilt,
               PETG lip deflects elastically then springs back — no adhesive required
               for axial retention; catch=0.50 mm (2.5× original 0.20 mm)

Pocket geometry imports from arc_magnet.py so that pocket dimensions always
track magnet dimensions (single source of truth).

License: Apache-2.0
Source: project-specific design, 4010 outrunner BLDC rotor geometry
"""
from __future__ import annotations

from pathlib import Path

from build123d import (
    Align,
    Box,
    BuildPart,
    Cylinder,
    GeomType,
    Hole,
    Mode,
    Part,
    Pos,
    Rot,
    chamfer,
    export_step,
)

# 磁钢尺寸从 arc_magnet 模块导入，确保槽型与磁钢完全匹配
from build123d_parts_lib.parts.actuators.arc_magnet import (
    magnet_half_deg,  # ≈ 11.57° — pocket arc = magnet arc
    magnet_h,         # 10.0 mm — pocket height base
    n_poles,          # 14      — number of pockets
)

# ── 转子壳尺寸 / Rotor shell dimensions ────────────────────────────────────────
rotor_od      = 47.5   # outer diameter  mm
rotor_h       = 12.0   # axial height  mm  (magnets + end-plate)
shell_wall_t  =  1.5   # radial wall thickness  mm
center_bore_d =  5.0   # shaft bore diameter  mm
endplate_t    =  2.0   # closed end-plate thickness  mm

# ── 磁钢保留唇尺寸 / Retention lip dimensions (open-end snap-in fixation) ──────
retention_lip_h = 2.0  # mm — axial height of lip at open end (Z=0 to Z=lip_h)
lip_protrusion  = 0.3  # mm — radial inward protrusion (PETG flexes to allow snap-in)

GEOMETRY_INVARIANTS = {
    "rotor_od":         rotor_od,
    "rotor_h":          rotor_h,
    "shell_wall_t":     shell_wall_t,
    "center_bore_d":    center_bore_d,
    "n_poles":          n_poles,          # pocket count == magnet count
    "pocket_depth":     0.8,              # V2: catch=0.50mm (was 0.20mm)
    "retention_lip_h":  retention_lip_h,
    "lip_protrusion":   lip_protrusion,
    "catch":            0.8 - 0.3,        # 0.50 mm — retention undercut
}


def make_rotor_shell() -> Part:
    """Generate outer rotor cup with 14 arc pockets + snap-in retention lips.

    Pocket geometry:
      inner wall surface r = rotor_od/2 - shell_wall_t = 22.25 mm
      pocket depth = 0.8 mm → pocket bottom r = 21.45 mm  (V2: catch=0.50mm)
      pocket height = magnet_h + 0.2 mm = 10.2 mm (axial clearance)
      pocket arc = ±magnet_half_deg (23.14° full arc per pocket)

    Retention lip (per pocket):
      at Z=0..retention_lip_h the pocket cut is followed by a fill-back of
      0.3 mm, leaving r: 21.45→21.75 as a protruding ledge (catch=0.50 mm).
      Snap-in: tilt magnet ~15°, push end-plate side in first, press remaining
      edge past lip — PETG deflects ~0.5 mm then snaps back.
    """
    shell_inner_r  = rotor_od / 2 - shell_wall_t    # 22.25 mm
    pocket_depth   = 0.8                             # mm radially into wall (V2: catch=0.50mm)
    pocket_r_outer = shell_inner_r                   # pocket opens at inner wall
    pocket_r_inner = shell_inner_r - pocket_depth    # 21.45 mm pocket bottom
    pocket_h       = magnet_h + 0.2                  # 10.2 mm — axial clearance

    # ── Base shell: outer cylinder minus inner cavity minus shaft bore ────────
    with BuildPart() as p:
        Cylinder(
            radius=rotor_od / 2,
            height=rotor_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        Cylinder(
            radius=shell_inner_r,
            height=rotor_h - endplate_t + 0.1,   # +0.1 avoids zero-face artefact
            align=(Align.CENTER, Align.CENTER, Align.MIN),
            mode=Mode.SUBTRACT,
        )
        Hole(radius=center_bore_d / 2)

        # Chamfer open-end outer edge 0.5 mm (print + assembly friendliness)
        try:
            open_edges = [
                e for e in p.edges().filter_by(GeomType.CIRCLE)
                if abs(e.radius - rotor_od / 2) < 0.3 and abs(e.center().Z) < 0.3
            ]
            if open_edges:
                chamfer(open_edges, length=0.5)
        except Exception:
            pass

    solid = p.part

    # ── 14 magnet retention pockets + snap-in lips (Algebra mode) ────────────
    # Strategy: cut full-depth pocket, then fuse back a thin retention lip at Z=0.
    # Same half-plane clip strategy as make_arc_magnet() in arc_magnet.py.
    clip_size = pocket_r_outer + 5.0
    clip_h    = pocket_h + 0.2

    # Full-depth pocket annulus
    pocket_annulus = (
        Cylinder(
            radius=pocket_r_outer + 0.05,
            height=pocket_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=pocket_r_inner - 0.05,
            height=pocket_h + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # Retention lip fill-back: adds 0.3 mm protrusion at open end (Z=0..lip_h)
    lip_annulus = (
        Cylinder(
            radius=pocket_r_inner + lip_protrusion,
            height=retention_lip_h,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        - Cylinder(
            radius=pocket_r_inner - 0.05,
            height=retention_lip_h + 0.1,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    # Arc clip planes — shared by both pocket and lip
    upper_clip = (
        Rot(0, 0, +magnet_half_deg)
        * Pos(0, clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    lower_clip = (
        Rot(0, 0, -magnet_half_deg)
        * Pos(0, -clip_size / 2, pocket_h / 2)
        * Box(2 * clip_size, clip_size, clip_h)
    )
    pocket_proto = pocket_annulus - upper_clip - lower_clip
    lip_proto    = lip_annulus    - upper_clip - lower_clip

    for i in range(n_poles):
        angle = 360.0 * i / n_poles
        solid = solid - Rot(0, 0, angle) * pocket_proto + Rot(0, 0, angle) * lip_proto

    return solid


if __name__ == "__main__":
    print("Building QDD rotor shell ...")
    print(f"  OD={rotor_od} mm  H={rotor_h} mm  wall={shell_wall_t} mm"
          f"  {n_poles} magnet pockets  pocket_arc=±{magnet_half_deg:.2f}°")

    shell = make_rotor_shell()

    bb = shell.bounding_box()
    print(f"  Volume : {shell.volume:.1f} mm³")
    print(f"  BBox   : {bb.size.X:.2f} × {bb.size.Y:.2f} × {bb.size.Z:.2f} mm")

    assert shell.volume > 0, "❌ rotor_shell volume ≤ 0"
    assert abs(bb.size.X - rotor_od) < 1.0, f"shell X 偏差: {bb.size.X:.2f}"
    assert abs(bb.size.Z - rotor_h)  < 0.2, f"shell Z 偏差: {bb.size.Z:.2f}"
    print("  BRep + BBox ✓")

    out_dir = Path(__file__).parent / "cache"
    out_dir.mkdir(exist_ok=True)
    export_step(shell, str(out_dir / "rotor_shell.step"))
    print("  STEP → cache/rotor_shell.step ✓")
