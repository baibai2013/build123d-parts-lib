English | [中文](README.md)

# build123d-parts-lib

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![build123d](https://img.shields.io/badge/build123d-0.10+-green)](https://github.com/gumyr/build123d)

> **Reusable CAD parts for [build123d](https://github.com/gumyr/build123d) projects** — standard part solids, functional modules, generator functions, project templates, material metadata — accumulated over time for cross-project reuse.

Companion to [build123d-cad skill](https://github.com/baibai2013/build123d-cad); parameter data is maintained in the skill's `data-sources/*.yaml`, while this library provides **importable CAD code**.

---

## Installation

**Option A: submodule + editable install (recommended)**

```bash
cd my-project
git submodule add https://github.com/baibai2013/build123d-parts-lib.git lib/parts-lib
pip install -e lib/parts-lib
```

**Option B: standalone clone + editable install**

```bash
git clone https://github.com/baibai2013/build123d-parts-lib.git
pip install -e build123d-parts-lib
```

---

## Quick Start

```python
# 1. Use a part solid directly
from build123d_parts_lib.parts.servos.sg90 import make_sg90
servo = make_sg90()

# 2. Functional module (multi-part assembly)
from build123d_parts_lib.modules.threaded_insert_boss import make_m3_boss
boss = make_m3_boss(insert_length=5, height=8)

# 3. Generator function (parametric feature)
from build123d_parts_lib.generators.clearance import get_clearance_diameter
d = get_clearance_diameter("M3", "medium")   # → 3.4 mm (FDM recommended)

# 4. Project template (fill parameters to start a project)
from build123d_parts_lib.templates.sg90_bracket import make_sg90_bracket
bracket = make_sg90_bracket(wall_thickness=2.5, print_clearance=0.3)

# 5. Metadata (density / tolerances)
import yaml, importlib.resources as r
densities = yaml.safe_load(
    r.files("build123d_parts_lib.materials").joinpath("densities.yaml").read_text()
)
mass_g = servo.volume / 1000 * densities["plastics"]["PLA"]
```

---

## 5 Content Categories

### A. `parts/` — Standard Part Solids

Complete 3D solids — call factory functions or `import_step()` directly.

> **Full parts index**: see **[docs/parts-index.md](docs/parts-index.md)** (includes previews, factory signatures, and covered specs for each category).

Currently covers 7 categories, 38 factory files, 200+ parametric specs:

| Category | Representative Parts | Module Prefix |
|----------|---------------------|---------------|
| Fasteners | Socket head / countersunk / pan head / Phillips screws, hex / flange / wing nuts, spring washers · standoffs · rivet nuts… | `parts.fasteners` |
| Bearings | Deep groove ball / MR miniature / flanged / linear LM series | `parts.bearings` |
| Pins & Shafts | Cylindrical pins / cotter pins / spring pins / smooth shafts | `parts.pins` |
| Servos | SG90 / MG90S / MG996R / DS3218 + servo horns | `parts.servos` |
| Transmission | GT2 pulleys / belts / parallel keys | `parts.transmission` |
| Retainers | External / internal circlips | `parts.retainers` |
| Seals | O-rings (ISO 3601-1 / GB/T 3452.1) | `parts.seals` |

> **Fastener geometry note**: All fasteners (bolts, screws, etc.) in this library use **smooth shank** representation — real threads are not modeled.
> The `pitch` parameter in YAML is retained for threaded hole calculations; precision is sufficient for assembly simulation.
> For threaded STEP files, download from:
>
> | Platform | URL | Notes |
> |----------|-----|-------|
> | McMaster-Carr | [mcmaster.com](https://www.mcmaster.com) | Highest quality, real threads, first choice |
> | TraceParts | [traceparts.com](https://www.traceparts.com) | Free registration, widest spec coverage |
> | PARTcommunity | [partcommunity.com](https://partcommunity.com) | Free, multi-format |
> | 3DFindit | [3dfindit.com](https://www.3dfindit.com) | Multi-vendor aggregator including Bossard |

### B. `modules/` — Functional Modules

Multi-part assemblies for high-frequency scenarios.

| Module | Entry | Use Case |
|--------|-------|----------|
| Heat-set insert boss | `modules.threaded_insert_boss:make_m3_boss` | Standard fastening for FDM printed parts |
| FDM snap latch | `modules.snap_fit_latch:make_snap_latch` | Screw-free lid / enclosure fastening |

### C. `generators/` — Generator Functions

Parametric features returning Sketch / Part / numeric values.

| Generator | Entry | Output |
|-----------|-------|--------|
| Vent pattern array | `generators.vents:make_vent_pattern` | Sketch |
| Screw clearance diameter | `generators.clearance:get_clearance_diameter` | float |

### D. `templates/` — Project Templates

A few parameters → ready-to-use parts; the 0→1 starting point for new projects.

| Template | Entry | Scenario |
|----------|-------|----------|
| SG90 servo mount | `templates.sg90_bracket:make_sg90_bracket` | Servo installation |
| PCB enclosure | `templates.pcb_enclosure:make_pcb_enclosure` | Electronics housing |

### E. `materials/` — Engineering Metadata

YAML lookup tables.

| File | Content |
|------|---------|
| `materials/densities.yaml` | Material densities (PLA / ABS / aluminum / steel / …) |
| `materials/fits.yaml` | ISO tolerance fits + 3D printing empirical clearances |

---

## Integration with build123d-cad skill

The skill's `data-sources/*.yaml` maintains **parameter data** (SG90 dimensions, M3 specs); this library maintains **importable CAD code**. They are linked via the `parts_lib:` field in the YAML:

```yaml
# skill's data-sources/servos.yaml
SG90:
  body: {length: 22.8, ...}
  parts_lib:
    module: build123d_parts_lib.parts.servos.sg90
    factory: make_sg90
    cache_step: cache/sg90.step
```

When `spec_lookup.py` matches SG90 it also prints the parts-lib entry, so the AI knows "parameters come from YAML, solids use parts-lib."

---

## Development & Contribution

### Run Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### Rebuild Cache STEP Files

After modifying part source code:

```bash
python scripts/build_cache.py                        # Rebuild all representative specs
python scripts/build_cache.py --only bearings        # Rebuild a specific category
python scripts/build_cache.py --only ball_bearing --model 6000ZZ  # Export a specific model
python scripts/verify_cache.py                       # Verify cache vs factory consistency
python scripts/verify_cache.py --only bearings       # Verify a specific category
```

### Adding New Parts (Contribution Guide)

See [docs/contributing.md](docs/contributing.md).

Core rules:
- Place under `parts/` / `modules/` / `generators/` / `templates/` / `materials/` by category
- File header docstring must include: License, Source, parameter documentation
- Every new `.py` must have a corresponding `tests/test_*.py` smoke test
- Code referencing a public repo must include `# Reference: repo@commit file#L... (License)`

---

## Versioning

[Semantic versioning](https://semver.org/). This library is at `0.x` — the API may change. Will enter `1.0` once stable.

History: see [CHANGELOG.md](CHANGELOG.md).

---

## Disclaimer

This library is intended for reference and reuse. Part models are engineering simplifications; parameter data is compiled from publicly available online resources. Actual dimensions vary by manufacturer and batch — verify before applying to specific use cases. Process fit clearances should reference relevant standards; empirical values in `fits.yaml` are for guidance only. Upstream versions evolve; pinning dependency versions is recommended. Provided as-is, without warranty of fitness for a particular purpose.

---

## License

Apache License 2.0 — Commercial use allowed, with explicit patent grant, consistent with upstream [build123d](https://github.com/gumyr/build123d) (Apache 2.0). See [LICENSE](LICENSE).
