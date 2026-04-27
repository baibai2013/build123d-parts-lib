# Changelog

All notable changes to this project are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-27

### Added

- Initial MVP skeleton with 5 category directories
- `parts/` — standard part entities:
  - `servos/sg90.py` + cache/sg90.step
  - `fasteners/m3_iso4762.py` + cache/m3_iso4762_L10.step
- `modules/` — functional multi-part modules:
  - `threaded_insert_boss.py` (M3×5 heat-set insert boss)
  - `snap_fit_latch.py` (FDM snap-fit latch)
- `generators/` — parametric helpers:
  - `vents.py` (grid hole pattern)
  - `clearance.py` (metric screw clearance holes)
- `templates/` — project starters:
  - `sg90_bracket.py`
  - `pcb_enclosure.py`
- `materials/` — engineering metadata:
  - `densities.yaml`
  - `fits.yaml` (ISO H7/h6 and 3D-printing fits)
- `pyproject.toml` with `pip install -e` support
- MIT license
- Smoke tests under `tests/`
- `scripts/rebuild_cache.py` to regenerate all cached STEP files
- Documentation: `README.md`, `docs/parts-index.md`, `docs/contributing.md`

### Integration

- Companion skill `build123d-cad` references entries via `parts_lib:` field
  in `data-sources/*.yaml`; see skill commit for cross-reference.
