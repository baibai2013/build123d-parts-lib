"""Rebuild cache/: 每个 factory 只保留一个代表 STEP + 一张 PNG。

- 清空所有 parts/*/cache/*
- 对每个 factory 调用一次"代表调用"
- 导出 STEP 到 cache/<slug>.step
- 渲染 PNG 到 cache/<slug>.png

运行方式（从仓库根）：
    python scripts/build_cache.py

License: MIT
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from build123d import export_step  # noqa: E402

from build123d_parts_lib._preview import save_preview_png  # noqa: E402

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
    from build123d_parts_lib.parts.transmission.key_parallel import (
        make_parallel_key,
    )
    from build123d_parts_lib.parts.transmission.timing_belt_gt2 import make_gt2_belt
    from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import (
        make_gt2_pulley,
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


def main() -> int:
    parts_root = REPO_ROOT / "build123d_parts_lib" / "parts"

    print(f">> Purging cache under {parts_root} ...")
    n = purge_cache(parts_root)
    print(f"   removed {n} files\n")

    bundle = _rep_bundle()
    print(f">> Building {len(bundle)} representative parts ...")

    ok, fail = 0, 0
    for category, slug, fn, kwargs, title in bundle:
        cache_dir = parts_root / category / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        step_path = cache_dir / f"{slug}.step"
        png_path = cache_dir / f"{slug}.png"
        try:
            part = fn(**kwargs)
            export_step(part, str(step_path))
            save_preview_png(part, png_path, title=title)
            vol = part.volume
            print(f"   [OK] {category}/{slug}.step  vol={vol:.1f} mm3  + .png")
            ok += 1
        except Exception as e:
            print(f"   [FAIL] {category}/{slug}: {type(e).__name__}: {e}")
            fail += 1

    print(f"\nDone. ok={ok}, fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
