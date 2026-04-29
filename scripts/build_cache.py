"""Rebuild cache/: 每个 factory 只保留一个代表 STEP + 一张 PNG。

- 增量覆盖 bundle 里的零件，不在 bundle 里的 cache 保留不动
- 导出 STEP 到 cache/<slug>.step
- 渲染 PNG 到 cache/<slug>.png

运行方式(从仓库根)：
    python scripts/build_cache.py                    # 全量重建 bundle 所有条目
    python scripts/build_cache.py --only bearings    # 只重建匹配 category 的条目
    python scripts/build_cache.py --only ball_bearing # 只重建匹配 slug 的条目

License: MIT
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from build123d import export_step  # noqa: E402

from build123d_parts_lib._preview_ocp import save_preview_png_auto  # noqa: E402

# ============================================================
# 代表规格清单（slug, factory callable, kwargs）
# 每个 factory 文件只取一个最具代表性的规格
# ============================================================


def _rep_bundle():
    """延迟 import，避免启动时就全加载。"""
    from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
    from build123d_parts_lib.parts.bearings.flanged_bearing import (
        make_flanged_bearing,
    )
    from build123d_parts_lib.parts.bearings.mr_bearing import make_mr_bearing
    from build123d_parts_lib.parts.fasteners.countersunk_screw import (
        make_countersunk_screw,
    )
    from build123d_parts_lib.parts.fasteners.hex_bolt import make_hex_bolt
    from build123d_parts_lib.parts.fasteners.nut_hex import make_hex_nut
    from build123d_parts_lib.parts.fasteners.socket_head_screw import (
        make_socket_head_screw,
    )
    from build123d_parts_lib.parts.fasteners.threaded_insert import (
        make_threaded_insert,
    )
    from build123d_parts_lib.parts.fasteners.washer import make_washer
    from build123d_parts_lib.parts.pins.pin_cylindrical import make_cylindrical_pin
    from build123d_parts_lib.parts.pins.pin_split import make_split_pin
    from build123d_parts_lib.parts.pins.pin_spring import make_spring_pin
    from build123d_parts_lib.parts.pins.shaft_smooth import make_smooth_shaft
    from build123d_parts_lib.parts.retainers.retaining_ring_hole import (
        make_retaining_ring_hole,
    )
    from build123d_parts_lib.parts.retainers.retaining_ring_shaft import (
        make_retaining_ring_shaft,
    )
    from build123d_parts_lib.parts.servos.servo_horn import make_servo_horn
    from build123d_parts_lib.parts.servos.sg90 import make_sg90
    from build123d_parts_lib.parts.servos.standard_servo import make_servo
    from build123d_parts_lib.parts.transmission.bevel_gear import make_bevel_gear
    from build123d_parts_lib.parts.transmission.gear_rack import make_gear_rack
    from build123d_parts_lib.parts.transmission.helical_gear import make_helical_gear
    from build123d_parts_lib.parts.transmission.internal_gear import (
        make_internal_gear,
    )
    from build123d_parts_lib.parts.transmission.key_parallel import (
        make_parallel_key,
    )
    from build123d_parts_lib.parts.transmission.spur_gear import make_spur_gear
    from build123d_parts_lib.parts.transmission.timing_belt_gt2 import make_gt2_belt
    from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import (
        make_gt2_pulley,
    )
    from build123d_parts_lib.parts.transmission.worm_gear import (
        make_worm,
        make_worm_wheel,
    )

    # (category, slug, callable, kwargs, title)
    return [
        # fasteners
        ("fasteners", "socket_head_screw", make_socket_head_screw,
         dict(size="M3", length=10), "ISO 4762  M3×10"),
        ("fasteners", "countersunk_screw", make_countersunk_screw,
         dict(size="M3", length=10), "ISO 10642  M3×10"),
        ("fasteners", "hex_bolt", make_hex_bolt,
         dict(size="M6", length=20), "DIN 933  M6×20"),
        ("fasteners", "hex_nut", make_hex_nut,
         dict(size="M3", standard="ISO4032"), "ISO 4032  Hex Nut M3"),
        ("fasteners", "washer_flat", make_washer,
         dict(size="M3", type_="flat"), "ISO 7089  Washer M3"),
        ("fasteners", "threaded_insert", make_threaded_insert,
         dict(size="M3"), "Heat-Set Insert  M3×5"),
        # bearings
        ("bearings", "ball_bearing", make_ball_bearing,
         dict(model="608ZZ"), "Ball Bearing  608ZZ"),
        ("bearings", "mr_bearing", make_mr_bearing,
         dict(model="MR85ZZ"), "MR Bearing  MR85ZZ"),
        ("bearings", "flanged_bearing", make_flanged_bearing,
         dict(model="F688ZZ"), "Flanged Bearing  F688ZZ"),
        # pins
        ("pins", "pin_cylindrical", make_cylindrical_pin,
         dict(diameter=4.0, length=20.0), "GB/T 119.1  Pin D4×20"),
        ("pins", "pin_split", make_split_pin,
         dict(diameter=2.0, length=16.0), "ISO 1234  Split Pin D2×16"),
        ("pins", "pin_spring", make_spring_pin,
         dict(diameter=4.0, length=20.0), "ISO 8752  Spring Pin D4×20"),
        ("pins", "shaft_smooth", make_smooth_shaft,
         dict(diameter=5.0, length=60.0), "Smooth Shaft  D5×60"),
        # servos
        ("servos", "standard_servo", make_servo,
         dict(model="SG90"), "Servo  SG90"),
        ("servos", "servo_horn", make_servo_horn,
         dict(type_="single"), "Servo Horn  25T single"),
        ("servos", "sg90_legacy", make_sg90, dict(), "SG90 (legacy)"),
        # transmission
        ("transmission", "timing_pulley_gt2", make_gt2_pulley,
         dict(teeth=20, bore_d=5.0), "GT2 Pulley  20T ⌀5"),
        ("transmission", "timing_belt_gt2", make_gt2_belt,
         dict(length=200.0), "GT2 Belt  L200"),
        ("transmission", "key_parallel", make_parallel_key,
         dict(width=5.0, height=5.0, length=20.0), "ISO 2491  Key 5×5×20"),
        # gears (ISO 54 / ISO 23509 / ISO 1122)
        ("transmission", "spur_gear", make_spur_gear,
         dict(module=2.0, teeth=20, bore_d=8.0),
         "Spur Gear  m2 z20 ⌀8"),
        ("transmission", "gear_rack", make_gear_rack,
         dict(module=2.0, length=200.0, width=15.0, base_h=8.0),
         "Gear Rack  m2 L200 W15"),
        ("transmission", "helical_gear", make_helical_gear,
         dict(module=2.0, teeth=30, helix_angle=20.0, bore_d=10.0),
         "Helical Gear  mn2 z30 β20° ⌀10"),
        ("transmission", "bevel_gear", make_bevel_gear,
         dict(module=2.0, teeth=20, mating_teeth=20, bore_d=8.0),
         "Bevel Gear  m2 z20×20 ⌀8"),
        ("transmission", "worm", make_worm,
         dict(module=2.0, threads=1, length=50.0, diameter_coeff=10.0),
         "Worm  m2 z1 L50 q10"),
        ("transmission", "worm_wheel", make_worm_wheel,
         dict(module=2.0, teeth=30, bore_d=8.0,
              worm_threads=1, worm_d=20.0),
         "Worm Wheel  m2 z30 ⌀8"),
        ("transmission", "internal_gear", make_internal_gear,
         dict(module=2.0, teeth=60, outer_d=130.0),
         "Internal Gear  m2 z60 ⌀130"),
        # retainers
        ("retainers", "retaining_ring_shaft", make_retaining_ring_shaft,
         dict(shaft_d=5.0), "GB/T 894.1  Ring D5 shaft"),
        ("retainers", "retaining_ring_hole", make_retaining_ring_hole,
         dict(hole_d=10.0), "GB/T 893.1  Ring D10 hole"),
    ]


def purge_cache(parts_root: Path) -> int:
    """清空所有 cache/ 目录下的文件。"""
    removed = 0
    for cache_dir in parts_root.glob("*/cache"):
        for f in cache_dir.iterdir():
            if f.is_file():
                f.unlink()
                removed += 1
    return removed


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI: --only 过滤 + --model 指定具体型号。
    CLI: --only filters + --model targets a specific spec.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        metavar="CATEGORY_OR_SLUG",
        help="只重建匹配 category (如 bearings) 或 slug (如 ball_bearing) 的条目;"
             " 不传时全量重建 bundle。",
    )
    parser.add_argument(
        "--model",
        metavar="MODEL_NAME",
        help="指定具体型号 (如 6000ZZ, MR104ZZ)。必须与 --only <slug> 搭配,"
             " 且该 factory 的 kwargs 必须含 'model' 键。输出文件名带型号后缀:"
             " cache/<slug>_<model_lower>.{step,png},不覆盖代表规格。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    parts_root = REPO_ROOT / "build123d_parts_lib" / "parts"

    # 增量式重建：只覆盖 bundle 里的零件，不在 bundle 里的 cache 文件保留不动。
    # Incremental rebuild: only overwrite parts in bundle, keep other cache files intact.
    bundle = _rep_bundle()

    # 按 --only 过滤 / filter by --only
    if args.only:
        filtered = [e for e in bundle if args.only in (e[0], e[1])]
        if not filtered:
            print(f"!! --only {args.only!r} 无匹配条目 / no matching entries")
            print(f"   可用 category: {sorted({e[0] for e in bundle})}")
            return 1
        bundle = filtered

    # --model 覆盖 kwargs['model'] + slug 加型号后缀
    # --model overrides kwargs['model'] + appends model suffix to slug
    if args.model:
        if not args.only:
            print("!! --model 必须与 --only <slug> 搭配 / requires --only <slug>")
            return 1
        if len(bundle) != 1:
            print(f"!! --model 要求 --only 精确匹配单个 slug (当前 {len(bundle)} 个)")
            return 1
        category, slug, fn, kwargs, title = bundle[0]
        if "model" not in kwargs:
            print(f"!! factory {category}/{slug} 的 kwargs 无 'model' 键;"
                  f" kwargs={kwargs}")
            return 1
        new_kwargs = {**kwargs, "model": args.model}
        model_suffix = args.model.lower().replace("-", "_")
        new_slug = f"{slug}_{model_suffix}"
        new_title = f"{title.split()[0]} {args.model}"
        bundle = [(category, new_slug, fn, new_kwargs, new_title)]
        print(f">> --only {args.only!r} --model {args.model!r}"
              f" → {category}/{new_slug}")
    elif args.only:
        print(f">> --only {args.only!r} → {len(bundle)} parts")
    else:
        print(f">> Building {len(bundle)} representative parts ...")

    ok, fail = 0, 0
    backends: dict[str, int] = {}
    for category, slug, fn, kwargs, title in bundle:
        cache_dir = parts_root / category / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        step_path = cache_dir / f"{slug}.step"
        png_path = cache_dir / f"{slug}.png"
        try:
            part = fn(**kwargs)
            export_step(part, str(step_path))
            _, backend = save_preview_png_auto(part, png_path, title=title)
            backends[backend] = backends.get(backend, 0) + 1
            vol = part.volume
            print(
                f"   [OK] {category}/{slug}.step  "
                f"vol={vol:.1f} mm3  + .png ({backend})"
            )
            ok += 1
        except Exception as e:
            print(f"   [FAIL] {category}/{slug}: {type(e).__name__}: {e}")
            fail += 1

    print(
        f"\nDone. ok={ok}, fail={fail}  "
        f"backends={dict(backends)}"
    )
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
