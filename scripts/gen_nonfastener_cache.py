"""Generate canonical STEP + PNG cache for all non-fastener part categories.

Categories: bearings, pins, servos, transmission, retainers, seals
Each uses its own sizing convention (model codes, diameter+length, etc.) — NOT M4.
"""
import socket
import time
import shutil
from pathlib import Path

from build123d import export_step

REPO = Path(__file__).parent.parent
PARTS = REPO / "build123d_parts_lib" / "parts"

# ── OCP setup ────────────────────────────────────────────────────────────────
def _get_port():
    for p in [3939, 4567]:
        try:
            socket.create_connection(("localhost", p), timeout=0.5).close()
            return p
        except OSError:
            pass
    return None

ocp_port = _get_port()
if ocp_port:
    from ocp_vscode import show, set_port, Camera, save_screenshot
    set_port(ocp_port)
    print(f"OCP connected on port {ocp_port}")
else:
    print("WARNING: OCP not running — STEP only, no PNG screenshots")

def save_png(part, png_path: Path):
    if not ocp_port:
        return False
    try:
        show(part, reset_camera=Camera.RESET)
        time.sleep(2)
        save_screenshot(str(png_path))
        if png_path.exists() and png_path.stat().st_size > 1000:
            print(f"  PNG: {png_path.name}")
            return True
    except Exception as e:
        print(f"  PNG failed: {e}")
    return False


# ── Task list: (category, slug, factory_callable) ───────────────────────────
tasks = []

# Bearings
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.bearings.mr_bearing import make_mr_bearing
from build123d_parts_lib.parts.bearings.flanged_bearing import make_flanged_bearing
from build123d_parts_lib.parts.bearings.linear_bushing import make_linear_bushing

tasks += [
    ("bearings", "ball_bearing",    lambda: make_ball_bearing("608ZZ")),
    ("bearings", "mr_bearing",      lambda: make_mr_bearing("MR85ZZ")),
    ("bearings", "flanged_bearing", lambda: make_flanged_bearing("F688ZZ")),
    ("bearings", "linear_bushing",  lambda: make_linear_bushing("LM8UU")),
]

# Pins
from build123d_parts_lib.parts.pins.pin_cylindrical import make_cylindrical_pin
from build123d_parts_lib.parts.pins.pin_split import make_split_pin
from build123d_parts_lib.parts.pins.pin_spring import make_spring_pin as make_pin_spring
from build123d_parts_lib.parts.pins.shaft_smooth import make_smooth_shaft

tasks += [
    ("pins", "pin_cylindrical", lambda: make_cylindrical_pin(diameter=4.0, length=20.0)),
    ("pins", "pin_split",       lambda: make_split_pin(diameter=2.0, length=16.0)),
    ("pins", "pin_spring",      lambda: make_pin_spring(diameter=4.0, length=20.0)),
    ("pins", "shaft_smooth",    lambda: make_smooth_shaft(diameter=8.0, length=60.0)),
]

# Servos
from build123d_parts_lib.parts.servos.standard_servo import make_servo
from build123d_parts_lib.parts.servos.servo_horn import make_servo_horn

tasks += [
    ("servos", "standard_servo", lambda: make_servo("SG90")),
    ("servos", "servo_horn",     lambda: make_servo_horn("single")),
]

# Transmission
from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import make_gt2_pulley
from build123d_parts_lib.parts.transmission.timing_belt_gt2 import make_gt2_belt
from build123d_parts_lib.parts.transmission.key_parallel import make_parallel_key

tasks += [
    ("transmission", "timing_pulley_gt2", lambda: make_gt2_pulley(teeth=20, bore_d=5.0)),
    ("transmission", "timing_belt_gt2",   lambda: make_gt2_belt(length=200.0, width=6.0)),
    ("transmission", "key_parallel",       lambda: make_parallel_key(width=5.0, height=5.0, length=20.0)),
]

# Retainers
from build123d_parts_lib.parts.retainers.retaining_ring_shaft import make_retaining_ring_shaft
from build123d_parts_lib.parts.retainers.retaining_ring_hole import make_retaining_ring_hole

tasks += [
    ("retainers", "retaining_ring_shaft", lambda: make_retaining_ring_shaft(shaft_d=8.0)),
    ("retainers", "retaining_ring_hole",  lambda: make_retaining_ring_hole(hole_d=12.0)),
]

# Seals
from build123d_parts_lib.parts.seals.oring import make_oring

tasks += [
    ("seals", "oring", lambda: make_oring(d1=10.0, d2=2.0)),
]


# ── Run ──────────────────────────────────────────────────────────────────────
print(f"\nGenerating {len(tasks)} canonical cache files...\n")
ok = []
failed = []

for category, slug, factory in tasks:
    cache_dir = PARTS / category / "cache"
    cache_dir.mkdir(exist_ok=True)
    step_path = cache_dir / f"{slug}.step"
    png_path  = cache_dir / f"{slug}.png"

    print(f"[{category}] {slug}")
    try:
        part = factory()
        export_step(part, str(step_path))
        print(f"  STEP: {step_path.name}  vol={part.volume:.1f} mm³")

        png_ok = save_png(part, png_path)
        if not png_ok:
            print(f"  PNG: skipped (no OCP)")

        ok.append(slug)
    except Exception as e:
        print(f"  ERROR: {e}")
        failed.append((slug, str(e)))

print(f"\n{'='*50}")
print(f"Done: {len(ok)} OK, {len(failed)} failed")
if failed:
    for slug, err in failed:
        print(f"  FAIL: {slug} — {err}")
