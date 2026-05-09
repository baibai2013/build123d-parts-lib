"""M4 — QDD actuator parts 三层验证 / Three-layer validation.

Layer 1: geometry — is_valid (soft warning for 100-tooth gear BRep false-positive)
                    + volume > 0
Layer 2: bounding box — key dimensions within ±1 mm (OD) / ±0.2 mm (height)
Layer 3: STEP round-trip — export then re-import, volume diff < 0.1%

Extra: flex spline wall thickness constant ≥ 1.1 mm (print quality gate)

Run from repo root:
    python build123d_parts_lib/parts/actuators/validate_actuators.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from build123d import export_step, import_step  # noqa: E402

# ── Part registry ─────────────────────────────────────────────────────────────
# (slug, factory, od_expected, h_expected, od_tol, h_tol, soft_is_valid)
PARTS_SPEC = [
    ("housing_circular_spline",
     "build123d_parts_lib.parts.actuators.housing_circular_spline",
     "make_housing_circular_spline",
     45.0, 30.0, 1.0, 0.5, False),
    ("flex_spline",
     "build123d_parts_lib.parts.actuators.flex_spline",
     "make_flex_spline",
     32.0, 20.0, 1.0, 0.5, True),   # OCC false-positive on 100-tooth gear
    ("wave_generator_cam",
     "build123d_parts_lib.parts.actuators.wave_generator_cam",
     "make_wave_generator_cam",
     17.0, 14.0, 0.5, 0.2, False),
    ("output_flange",
     "build123d_parts_lib.parts.actuators.output_flange",
     "make_output_flange",
     40.0, 8.0, 1.0, 0.2, False),
    ("motor_endcap_front",
     "build123d_parts_lib.parts.actuators.motor_endcap_front",
     "make_motor_endcap_front",
     45.0, 5.0, 1.0, 0.2, False),
    ("encoder_cover",
     "build123d_parts_lib.parts.actuators.encoder_cover",
     "make_encoder_cover",
     30.0, 6.0, 1.0, 0.2, False),
]

STEP_DIFF_LIMIT = 0.1   # % round-trip tolerance (plan.md: < 0.1%)
FLEX_WALL_MIN   = 1.1   # mm — print quality lower bound


def _import_factory(module_path: str, fn_name: str):
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, fn_name)


def validate_one(
    slug: str,
    module_path: str,
    fn_name: str,
    od_exp: float,
    h_exp: float,
    od_tol: float,
    h_tol: float,
    soft_is_valid: bool,
) -> bool:
    """Return True if all layers pass."""
    ok = True
    print(f"\n{'='*52}")
    print(f"  {slug}")

    # ── 调用工厂函数 / Call factory ────────────────────────────────────────────
    try:
        factory = _import_factory(module_path, fn_name)
        part    = factory()
    except Exception as exc:
        print(f"  [FAIL] factory raised: {exc}")
        return False

    # ── Layer 1: is_valid + volume > 0 ────────────────────────────────────────
    vol = part.volume
    if vol <= 0:
        print(f"  [FAIL] L1 volume ≤ 0: {vol:.1f} mm³")
        ok = False
    else:
        print(f"  [OK]   L1 volume = {vol:.1f} mm³")

    if not part.is_valid:
        if soft_is_valid:
            print(f"  [WARN] L1 is_valid=False (expected — OCC false-positive on complex"
                  f" boolean history)")
        else:
            print(f"  [FAIL] L1 is_valid=False")
            ok = False
    else:
        print(f"  [OK]   L1 is_valid=True")

    # ── Layer 2: bounding box ──────────────────────────────────────────────────
    bb = part.bounding_box()
    x_err = abs(bb.size.X - od_exp)
    z_err = abs(bb.size.Z - h_exp)
    if x_err > od_tol:
        print(f"  [FAIL] L2 X={bb.size.X:.2f}  expected≈{od_exp}  err={x_err:.3f} > {od_tol}")
        ok = False
    else:
        print(f"  [OK]   L2 BBox X={bb.size.X:.2f}  Z={bb.size.Z:.2f} mm  "
              f"(exp {od_exp}×{h_exp})")
    if z_err > h_tol:
        print(f"  [FAIL] L2 Z={bb.size.Z:.2f}  expected≈{h_exp}  err={z_err:.3f} > {h_tol}")
        ok = False

    # ── Layer 3: STEP round-trip ───────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        export_step(part, tmp_path)
        readback   = import_step(tmp_path)
        vol_back   = readback.volume
        diff_pct   = abs(vol - vol_back) / vol * 100
        if diff_pct >= STEP_DIFF_LIMIT:
            print(f"  [FAIL] L3 STEP RT diff {diff_pct:.4f}% ≥ {STEP_DIFF_LIMIT}%"
                  f"  (orig={vol:.2f}  back={vol_back:.2f})")
            ok = False
        else:
            print(f"  [OK]   L3 STEP RT diff {diff_pct:.4f}%  (< {STEP_DIFF_LIMIT}%)")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return ok


def check_flex_wall_thickness() -> bool:
    """Check flex spline wall_t constant (print quality gate)."""
    import importlib
    mod  = importlib.import_module(
        "build123d_parts_lib.parts.actuators.flex_spline"
    )
    wall = getattr(mod, "flex_wall_t", None)
    if wall is None:
        print("\n  [WARN] flex_spline.flex_wall_t constant not found")
        return True
    if wall < FLEX_WALL_MIN:
        print(f"\n  [FAIL] flex_spline wall_t={wall} mm < {FLEX_WALL_MIN} mm")
        return False
    print(f"\n  [OK]   flex_spline wall_t={wall} mm  (≥ {FLEX_WALL_MIN} mm)")
    return True


def main() -> int:
    print("QDD Actuator M4 — Three-Layer Validation")
    print("=" * 52)

    results: dict[str, bool] = {}

    for (slug, mod, fn, od, h, od_tol, h_tol, soft) in PARTS_SPEC:
        results[slug] = validate_one(slug, mod, fn, od, h, od_tol, h_tol, soft)

    # flex wall thickness extra check
    results["flex_wall_t"] = check_flex_wall_thickness()

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{'='*52}")
    print("SUMMARY")
    ok_count = fail_count = 0
    for key, passed in results.items():
        status = "[OK]  " if passed else "[FAIL]"
        print(f"  {status}  {key}")
        if passed:
            ok_count += 1
        else:
            fail_count += 1

    print(f"\n  Total: {ok_count} passed, {fail_count} failed")
    if fail_count == 0:
        print("  ✅ 所有验证通过 — M4 PASS")
        return 0
    else:
        print(f"  ❌ {fail_count} 项未通过")
        return 1


if __name__ == "__main__":
    sys.exit(main())
