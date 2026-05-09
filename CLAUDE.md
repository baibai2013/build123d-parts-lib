# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`build123d-parts-lib` is a reusable CAD parts library for [build123d](https://github.com/gumyr/build123d) projects. It provides importable Python modules for standard mechanical parts (bearings, fasteners, servos, gears, seals, actuators), parametric generators, functional modules, project templates, and material metadata YAML files.

Companion to the [build123d-cad skill](https://github.com/baibai2013/build123d-cad): the skill's `data-sources/*.yaml` files maintain parameter data, this library provides importable CAD code.

## Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run single test
pytest tests/test_generators.py::test_clearance_m3_defaults -v

# Lint
ruff check build123d_parts_lib/

# Rebuild representative STEP cache (all categories)
python scripts/build_cache.py

# Rebuild cache for one category or slug
python scripts/build_cache.py --only bearings
python scripts/build_cache.py --only ball_bearing --model 6000ZZ

# Verify cache matches factory output (3-layer: exist + bbox + volume)
python scripts/verify_cache.py
python scripts/verify_cache.py --only bearings

# Health-check all gates (D0 ops-yaml + D1 YAML geometry + D2 code structure)
python scripts/scan_all_gates.py
python scripts/scan_all_gates.py --d1   # YAML-only scan
```

## Architecture

### Package Layout

```
build123d_parts_lib/
├── parts/          # Single standard parts — factory functions returning Part
│   ├── bearings/   # Ball, MR, flanged, thin-section, angular-contact
│   ├── fasteners/  # Screws, bolts, nuts, washers, inserts, standoffs
│   ├── pins/       # Cylindrical, split, spring pins; smooth shafts
│   ├── servos/     # SG90 / MG996R / standard servo + servo horns
│   ├── transmission/ # GT2 pulleys/belts, spur/helical/bevel/worm gears, racks
│   ├── retainers/  # Shaft & hole retaining rings
│   ├── seals/      # O-rings (ISO 3601-1 / GB/T 3452.1)
│   └── actuators/  # QDD harmonic drive joint module (M0–M4 milestone work)
├── modules/        # Multi-part assemblies (threaded insert boss, snap latch)
├── generators/     # Parametric helpers returning floats/Sketch/Part
│   └── clearance.py  # get_clearance_diameter(m_size, fit) — close/medium/loose
├── templates/      # Project starters (SG90 bracket, PCB enclosure)
└── materials/      # YAML data — densities.yaml, fits.yaml
scripts/
├── build_cache.py      # Build representative STEP + PNG for each factory
├── verify_cache.py     # 3-layer cache verification (exist + bbox + volume)
├── rebuild_cache.py    # Full cache rebuild (alias)
├── scan_all_gates.py   # D0+D1+D2 periodic health check
├── check_d0_ops.py     # D0: ops-yaml completeness
├── check_d1_yaml.py    # D1: YAML geometry field validation
└── check_d2_code.py    # D2: factory code structure (GEOMETRY_INVARIANTS/assert)
```

### Factory Function Convention

Every part file exposes a `make_<name>(**kwargs) -> Part` factory:

```python
def make_<name>(param: float = default, ...) -> Part:
    """One-line description.
    Args: param — meaning, unit, default rationale
    Geometry: origin location, axis orientation
    """
    with BuildPart() as p:
        ...
    return p.part

if __name__ == "__main__":
    # Generates cache STEP when run directly
    export_step(make_<name>(), "/tmp/<name>.step")
```

All fasteners use **smooth-shank** (no thread geometry). The `pitch` parameter is retained in YAML for clearance-hole computation only.

### Cache Strategy

Each `parts/<category>/cache/` directory holds one representative STEP + PNG per factory. Cache files are committed to the repo (dual-storage strategy). `scripts/build_cache.py` maintains a `_rep_bundle()` registry — **register new parts there** when adding them.

### Verification Gates (D0/D1/D2)

- **D0** — ops-yaml documentation completeness
- **D1** — YAML geometry fields match expected values  
- **D2** — factory `.py` contains `GEOMETRY_INVARIANTS` dict + `assert` checks

### Actuators Subsystem (In Progress)

`parts/actuators/` is a QDD harmonic-drive joint module (Φ45×45 mm). Work tracked in `parts/actuators/PLAN.md`. Milestones M0–M4 cover proxy preview → parts-lib gap fill (thin-section + angular contact bearings) → 6 printed parts → assembly → cache. Some milestone files are complete; rotor shaft (`rotor_shaft.py`) is in progress.

## Adding a New Part

1. Place in the correct subdirectory (`parts/`, `modules/`, `generators/`, `templates/`, `materials/`).
2. File header docstring must include `License:` and `Source:`.
3. Factory named `make_<snake_case>`, typed, with defaults.
4. Add smoke test in `tests/test_<category>.py`: `is_valid`, bbox range, `pytest.raises` for bad input.
5. Register in `scripts/build_cache.py` `_rep_bundle()` and run cache rebuild.
6. Update `docs/parts-index.md` and `CHANGELOG.md`.
7. If the part maps to a `build123d-cad` skill YAML entry, add a `parts_lib:` block there too.

**External code attribution**: always annotate with `# 参考：repo@commit file#L... (License)`. Only MIT/BSD/Apache-2.0/Unlicense/CC0 sources are compatible.

## Linting Rules

Ruff with `line-length = 100`. Ignored: `E501` (line length), `E741` (ambiguous `l` — used for length in build123d convention), `F841` (unused build123d context-manager variables).
