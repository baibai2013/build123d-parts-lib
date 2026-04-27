# 零件索引

> 按类别 + 名称快速查找。新加零件时更新此文件。
> 详细规格见各 `parts/<category>/<category>.yaml`，路线图见 `docs/parts-roadmap.md`。
>
> 🖼 每行末尾的预览图由 `scripts/build_cache.py` 从各 factory 的"代表规格"渲染生成。
> 重新生成：`python scripts/build_cache.py`。

---

## 📦 parts/ — 标准件实体

### 🔩 Fasteners（紧固件）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| socket_head_screw | `make_socket_head_screw(size, length)` | M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10 | ![](../build123d_parts_lib/parts/fasteners/cache/socket_head_screw.png) |
| countersunk_screw | `make_countersunk_screw(size, length)` | M2 / M2.5 / M3 / M4 / M5 | ![](../build123d_parts_lib/parts/fasteners/cache/countersunk_screw.png) |
| hex_bolt | `make_hex_bolt(size, length)` | M4 / M5 / M6 / M8 / M10（DIN 933） | ![](../build123d_parts_lib/parts/fasteners/cache/hex_bolt.png) |
| nut_hex | `make_hex_nut(size, standard)` | ISO4032 / GB6172 / DIN985（M2-M10） | ![](../build123d_parts_lib/parts/fasteners/cache/hex_nut.png) |
| washer | `make_washer(size, type_)` | 平垫 ISO7089（M2-M5） + 弹簧垫 GB93（M3-M5） | ![](../build123d_parts_lib/parts/fasteners/cache/washer_flat.png) |
| threaded_insert | `make_threaded_insert(size)` | M2.5 / M3 / M4 / M5 | ![](../build123d_parts_lib/parts/fasteners/cache/threaded_insert.png) |

> 模块路径统一为 `build123d_parts_lib.parts.fasteners.<slug>`。YAML：`fasteners.yaml`。

### ⚙️ Bearings（轴承）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| ball_bearing | `make_ball_bearing(model)` | 608 / 624 / 625 / 626 / 6000 / 6001-2RS / 6002 | ![](../build123d_parts_lib/parts/bearings/cache/ball_bearing.png) |
| mr_bearing | `make_mr_bearing(model)` | MR63 / MR74 / MR84 / MR85 / MR104 | ![](../build123d_parts_lib/parts/bearings/cache/mr_bearing.png) |
| flanged_bearing | `make_flanged_bearing(model)` | F688 / F693 / F623 / F624 / F625 / F684 | ![](../build123d_parts_lib/parts/bearings/cache/flanged_bearing.png) |

> 模块路径：`build123d_parts_lib.parts.bearings.<slug>`。YAML：`bearings.yaml`。

### 📍 Pins & Shafts（销与光轴）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| pin_cylindrical | `make_cylindrical_pin(diameter, length)` | D3 / D4 / D5 / D6（GB/T 119.1） | ![](../build123d_parts_lib/parts/pins/cache/pin_cylindrical.png) |
| pin_split | `make_split_pin(diameter, length)` | D1.5 / D2 / D2.5 / D3（ISO 1234） | ![](../build123d_parts_lib/parts/pins/cache/pin_split.png) |
| pin_spring | `make_spring_pin(diameter, length)` | D3 / D4 / D5 / D6（ISO 8752） | ![](../build123d_parts_lib/parts/pins/cache/pin_spring.png) |
| shaft_smooth | `make_smooth_shaft(diameter, length)` | D4 / D5 / D6 / D8（MISUMI PSFJ） | ![](../build123d_parts_lib/parts/pins/cache/shaft_smooth.png) |

> 模块路径：`build123d_parts_lib.parts.pins.<slug>`。YAML：`pins.yaml`。

### 🤖 Servos（舵机）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| standard_servo | `make_servo(model)` | SG90 / MG90S / MG996R / DS3218 | ![](../build123d_parts_lib/parts/servos/cache/standard_servo.png) |
| servo_horn | `make_servo_horn(type_)` | single / double / cross / disc | ![](../build123d_parts_lib/parts/servos/cache/servo_horn.png) |

> 模块路径：`build123d_parts_lib.parts.servos.<slug>`。YAML：`servos.yaml`。`sg90.py` 原文件保留向后兼容。

### ⚙️ Transmission（传动件）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| timing_pulley_gt2 | `make_gt2_pulley(teeth, bore_d)` | 16T / 20T / 30T / 40T × ⌀5 / ⌀8 | ![](../build123d_parts_lib/parts/transmission/cache/timing_pulley_gt2.png) |
| timing_belt_gt2 | `make_gt2_belt(length, width, pulley_d)` | L110 / L158 / L200 / L280 / L380 | ![](../build123d_parts_lib/parts/transmission/cache/timing_belt_gt2.png) |
| key_parallel | `make_parallel_key(width, height, length)` | 3×3 / 4×4 / 5×5 / 6×6 / 8×7（ISO 2491） | ![](../build123d_parts_lib/parts/transmission/cache/key_parallel.png) |

> 模块路径：`build123d_parts_lib.parts.transmission.<slug>`。YAML：`transmission.yaml`。

### 🔘 Retainers（卡簧）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| retaining_ring_shaft | `make_retaining_ring_shaft(shaft_d)` | D4 / D5 / D6 / D8 / D10 / D12（GB/T 894.1） | ![](../build123d_parts_lib/parts/retainers/cache/retaining_ring_shaft.png) |
| retaining_ring_hole | `make_retaining_ring_hole(hole_d)` | D8 / D10 / D12 / D16 / D20 / D25（GB/T 893.1） | ![](../build123d_parts_lib/parts/retainers/cache/retaining_ring_hole.png) |

> 模块路径：`build123d_parts_lib.parts.retainers.<slug>`。YAML：`retainers.yaml`。

---

## 🔧 modules/ — 功能模块

| Slug | Factory | 说明 |
|------|---------|------|
| threaded_insert_boss | `make_m3_boss(...)` | FDM 热压铜螺母柱（M3×5-OD4.2 默认） |
| snap_fit_latch | `make_snap_latch(...)` | 悬臂卡扣 |
| leg_segment | `make_leg_segment(...)` | 四足机器人腿段模板 |
| foot_cap | `make_foot_cap(...)` | 机器狗脚掌帽 |

## 🎨 generators/ — 参数化生成器

| Slug | Entry | 返回 |
|------|-------|------|
| vents | `make_vent_pattern(target_face, ...)` | Sketch |
| clearance | `get_clearance_diameter(m_size, fit)` | float (mm) |

## 🏗 templates/ — 项目模板

| Slug | Entry | 场景 |
|------|-------|------|
| sg90_bracket | `make_sg90_bracket(...)` | SG90 舵机安装座 |
| pcb_enclosure | `make_pcb_enclosure(...)` | PCB 外壳（MVP） |

## 🧪 materials/ — 工程元数据

| 文件 | 内容概要 |
|------|---------|
| `materials/densities.yaml` | 20+ 种材料密度（塑料/光敏/金属/木材） |
| `materials/fits.yaml` | ISO H7/h6 + H7/k6 公差配合 + 3D 打印经验间隙 |

---

## 命名约定

- **文件名**：小写 + 下划线，同族共用一个文件（`socket_head_screw.py` 覆盖 M2-M10）
- **Factory 函数**：`make_<snake_case>`，首参常为 `size: str` 或 `model: str` 做多规格查表
- **NamedTuple**：规格表统一用 `<Type>Spec` 命名（`ScrewSpec` / `BearingSpec` / `ServoSpec`）
- **cache/**：每个 factory 一个代表 `.step` + `.png`。需要其他规格时直接调 factory 重新生成。

---

## 快速入门

```python
from build123d_parts_lib.parts.fasteners.socket_head_screw import make_socket_head_screw
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.servos.standard_servo import make_servo

screw   = make_socket_head_screw(size="M3", length=10)
bearing = make_ball_bearing("608ZZ")
servo   = make_servo("MG996R")
```

重建全部代表 STEP + PNG：
```bash
cd lib/parts-lib
python scripts/build_cache.py
```

---

## 统计（2026-04-27）

- **Factory 文件**：19 个 `.py`（6 紧固 + 3 轴承 + 4 销轴 + 3 舵机 + 3 传动 + 2 卡簧）
- **参数化规格**：100+ 条（通过 NamedTuple 查表）
- **cache**：每 factory 1 STEP + 1 PNG（共 21 组）
- **YAML 条目**：80+ 条

---

## 未来扩充

见 `docs/parts-roadmap.md`（P2 路线图）：
- P2：MGN 导轨 / 滚珠丝杠 / 联轴器 / 步进电机 / 齿轮参数化 / O 型圈
