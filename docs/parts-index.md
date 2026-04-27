# 零件索引

> 按类别 + 名称快速查找。新加零件时更新此文件。

---

## 📦 parts/ — 标准件实体

| Slug | 模块路径 | Factory | Cache STEP | 参数来源 |
|------|---------|---------|-----------|---------|
| sg90 | `build123d_parts_lib.parts.servos.sg90` | `make_sg90()` | `parts/servos/cache/sg90.step` | build123d-cad `data-sources/servos.yaml:SG90` |
| m3_iso4762 | `build123d_parts_lib.parts.fasteners.m3_iso4762` | `make_m3_screw(length=10)` | `parts/fasteners/cache/m3_iso4762_L10.step` | build123d-cad `data-sources/fasteners.yaml:M3_ISO4762` |

## 🔧 modules/ — 功能模块

| Slug | 模块路径 | Factory | 说明 |
|------|---------|---------|------|
| threaded_insert_boss | `build123d_parts_lib.modules.threaded_insert_boss` | `make_m3_boss(...)` | FDM 热压铜螺母柱（M3×5-OD4.2 默认） |
| snap_fit_latch | `build123d_parts_lib.modules.snap_fit_latch` | `make_snap_latch(...)` | 悬臂卡扣（cantilever style） |

## 🎨 generators/ — 参数化生成器

| Slug | 模块路径 | Entry | 返回 |
|------|---------|-------|------|
| vents | `build123d_parts_lib.generators.vents` | `make_vent_pattern(target_face, ...)` | Sketch |
| clearance | `build123d_parts_lib.generators.clearance` | `get_clearance_diameter(m_size, fit)` | float (mm) |

## 🏗 templates/ — 项目模板

| Slug | 模块路径 | Entry | 场景 |
|------|---------|-------|------|
| sg90_bracket | `build123d_parts_lib.templates.sg90_bracket` | `make_sg90_bracket(...)` | SG90 舵机安装座 |
| pcb_enclosure | `build123d_parts_lib.templates.pcb_enclosure` | `make_pcb_enclosure(...)` | PCB 外壳（无盖板无螺丝柱 MVP） |

## 🧪 materials/ — 工程元数据

| 文件 | 内容概要 |
|------|---------|
| `materials/densities.yaml` | 20+ 种材料密度（塑料/光敏/金属/木材） |
| `materials/fits.yaml` | ISO H7/h6 + H7/k6 公差配合 + 3D 打印经验间隙 |

---

## 命名约定

- **文件名**：小写 + 下划线，含规格信息（`m3_iso4762.py`、`608zz.py`）
- **Factory 函数**：`make_<snake_case>`（`make_m3_screw`）
- **类**：PascalCase，仅在参数化多样时用
- **cache 文件**：`<slug>_<参数>.step`（`m3_iso4762_L10.step`）

---

## 未来扩充（按需添加）

- `parts/bearings/` — 608ZZ / 624ZZ / 625ZZ / 6001-2RS
- `parts/servos/` — MG90S / MG996R / DS3218
- `modules/` — hinge / magnetic_lock / rubber_foot / slide_rail
- `generators/` — radiused_rectangle / bolt_circle_holes
- `templates/` — quadruped_leg / gearbox_housing / cable_gland
- `materials/` — `processes.yaml`（FDM/SLA/CNC 标准参数）
