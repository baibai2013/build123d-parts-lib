"""build123d-parts-lib — reusable CAD parts for build123d projects.

Categories:
    parts/       — standard part entities (SG90, M3 screws, bearings, ...)
    modules/     — functional multi-part modules (threaded-insert boss, snap-fit, ...)
    generators/  — parametric helper functions (vent patterns, clearance holes, ...)
    templates/   — project starter templates (SG90 bracket, PCB enclosure, ...)
    materials/   — engineering metadata (densities, fits, process params)

Quick start:
    from build123d_parts_lib.parts.servos.sg90 import make_sg90
    from build123d_parts_lib.modules.threaded_insert_boss import make_m3_boss
    from build123d_parts_lib.generators.vents import make_vent_pattern
"""

__version__ = "0.1.0"
