# 零件索引

> 按类别 + 名称快速查找。新加零件时更新此文件。
> 详细规格见各 `parts/<category>/<category>.yaml`，路线图见 `docs/parts-roadmap.md`。
>
> 🖼 每行末尾的预览图由 `scripts/build_cache.py` 从各 factory 的"代表规格"渲染生成。
> 重新生成：`python scripts/build_cache.py`。

---

## 📦 parts/ — 标准件实体

### 🔩 Fasteners（紧固件）

**螺丝 / Screws**

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `socket_head_screw`<br>内六角圆柱头螺钉 | `make_socket_head_screw(size, length)` | M2 / M2.5 / M3 / M4 / M5 / M6 / M8 / M10（ISO 4762） | ![](../build123d_parts_lib/parts/fasteners/cache/socket_head_screw.png) |
| `countersunk_screw`<br>内六角沉头螺钉 | `make_countersunk_screw(size, length)` | M2 / M2.5 / M3 / M4 / M5（ISO 10642） | ![](../build123d_parts_lib/parts/fasteners/cache/countersunk_screw.png) |
| `screw_button_hex`<br>内六角扁圆头螺钉 | `make_button_head_screw(size, length)` | M2 / M3 / M4 / M5 / M6（ISO 7380-1） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_button_hex.png) |
| `screw_csk_phillips`<br>十字沉头螺钉 | `make_csk_phillips_screw(size, length)` | M2 / M3 / M4 / M5（ISO 7046） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_csk_phillips.png) |
| `screw_csk_slotted`<br>一字沉头螺钉 | `make_csk_slotted_screw(size, length)` | M2 / M3 / M4 / M5（ISO 2009） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_csk_slotted.png) |
| `screw_pan_phillips`<br>十字圆头螺钉 | `make_pan_phillips_screw(size, length)` | M2 / M3 / M4 / M5（ISO 7045） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_pan_phillips.png) |
| `screw_pan_slotted`<br>一字圆头螺钉 | `make_pan_slotted_screw(size, length)` | M2 / M3 / M4 / M5（ISO 1580） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_pan_slotted.png) |
| `hex_bolt`<br>外六角螺栓 | `make_hex_bolt(size, length)` | M4 / M5 / M6 / M8 / M10（DIN 933） | ![](../build123d_parts_lib/parts/fasteners/cache/hex_bolt.png) |
| `screw_carriage`<br>马车螺丝 | `make_carriage_bolt(size, length)` | M4 / M5（DIN 603） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_carriage.png) |
| `screw_set`<br>紧定螺丝 | `make_set_screw(size, length, tip)` | M3 / M4 / M5（ISO 4026/4028/4029） | ![](../build123d_parts_lib/parts/fasteners/cache/screw_set.png) |

**螺母 / Nuts**

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `nut_hex`<br>六角螺母 | `make_hex_nut(size, standard)` | ISO4032 / GB6172 / DIN985（M2-M10） | ![](../build123d_parts_lib/parts/fasteners/cache/hex_nut.png) |
| `nut_flange`<br>法兰螺母 | `make_flange_nut(size)` | M3 / M4 / M5（DIN 6923） | ![](../build123d_parts_lib/parts/fasteners/cache/nut_flange.png) |
| `nut_cap`<br>盖形螺母 | `make_cap_nut(size)` | M3 / M4 / M5（DIN 1587） | ![](../build123d_parts_lib/parts/fasteners/cache/nut_cap.png) |
| `nut_square`<br>方形螺母 | `make_square_nut(size)` | M3 / M4 / M5（DIN 562） | ![](../build123d_parts_lib/parts/fasteners/cache/nut_square.png) |
| `nut_wing`<br>蝶形螺母 | `make_wing_nut(size)` | M3 / M4 / M5（DIN 315） | ![](../build123d_parts_lib/parts/fasteners/cache/nut_wing.png) |
| `nut_tslot`<br>T 型螺母 | `make_tslot_nut(size)` | M3 / M4 / M5（2020 铝型材） | ![](../build123d_parts_lib/parts/fasteners/cache/nut_tslot.png) |

**垫片 / 嵌件 / 其他**

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `washer`<br>垫片 | `make_washer(size, type_)` | 平垫 ISO7089（M2-M5） + 弹簧垫 GB93（M3-M5） | ![](../build123d_parts_lib/parts/fasteners/cache/washer_flat.png) |
| `threaded_insert`<br>热压铜螺母 | `make_threaded_insert(size)` | M2.5 / M3 / M4 / M5 | ![](../build123d_parts_lib/parts/fasteners/cache/threaded_insert.png) |
| `rivet_nut`<br>拉铆螺母 | `make_rivet_nut(size)` | M3 / M4（安装前形态） | ![](../build123d_parts_lib/parts/fasteners/cache/rivet_nut.png) |
| `standoff_hex`<br>六角铜柱 | `make_hex_standoff(size, length, type_)` | M3 / M4，FF / MF | ![](../build123d_parts_lib/parts/fasteners/cache/standoff_hex.png) |
| `pin_spring`<br>开口弹簧销 | `make_spring_pin(nominal_d, length)` | D3 / D4（DIN 1481，带缝模型） | ![](../build123d_parts_lib/parts/fasteners/cache/pin_spring.png) |

> 模块路径统一为 `build123d_parts_lib.parts.fasteners.<slug>`。YAML：`fasteners.yaml`。

### ⚙️ Bearings（轴承）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `ball_bearing`<br>深沟球轴承 | `make_ball_bearing(model)` | 608ZZ / 624ZZ / 625ZZ / 626ZZ / 6000ZZ / 6001-2RS / 6002ZZ | ![](../build123d_parts_lib/parts/bearings/cache/ball_bearing.png) |
| `mr_bearing`<br>微型球轴承 | `make_mr_bearing(model)` | MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR104ZZ | ![](../build123d_parts_lib/parts/bearings/cache/mr_bearing.png) |
| `flanged_bearing`<br>法兰球轴承 | `make_flanged_bearing(model)` | F688ZZ / F693ZZ / F623ZZ / F624ZZ / F625ZZ / F684ZZ | ![](../build123d_parts_lib/parts/bearings/cache/flanged_bearing.png) |
| `linear_bushing`<br>直线轴承 | `make_linear_bushing(model)` | LM6UU / LM8UU / LM10UU / LM12UU / LMF8UU / LMF10UU（ISO 10736） | ![](../build123d_parts_lib/parts/bearings/cache/linear_bushing.png) |

> 模块路径：`build123d_parts_lib.parts.bearings.<slug>`。YAML：`bearings.yaml` / `lm_bearings.yaml`。
>
> ⚙️ **工业级几何**（ball_bearing / mr_bearing / flanged_bearing）：外圈 + 内圈均带环面滚道沟槽，真实滚珠均匀分布节圆，保持架带球窝。返回 `Compound`（子件含 outer_ring / inner_ring / cage / ball_NN label）。共享核心：`_bearing_geometry.py`。详见 [bearings/README.md](../build123d_parts_lib/parts/bearings/README.md)。

### 📍 Pins & Shafts（销与光轴）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `pin_cylindrical`<br>圆柱销 | `make_cylindrical_pin(diameter, length)` | D3 / D4 / D5 / D6（GB/T 119.1） | ![](../build123d_parts_lib/parts/pins/cache/pin_cylindrical.png) |
| `pin_split`<br>开口销 | `make_split_pin(diameter, length)` | D1.5 / D2 / D2.5 / D3（ISO 1234） | ![](../build123d_parts_lib/parts/pins/cache/pin_split.png) |
| `pin_spring`<br>弹性圆柱销 | `make_spring_pin(diameter, length)` | D3 / D4 / D5 / D6（ISO 8752） | ![](../build123d_parts_lib/parts/pins/cache/pin_spring.png) |
| `shaft_smooth`<br>光轴 | `make_smooth_shaft(diameter, length)` | D4 / D5 / D6 / D8（MISUMI PSFJ） | ![](../build123d_parts_lib/parts/pins/cache/shaft_smooth.png) |

> 模块路径：`build123d_parts_lib.parts.pins.<slug>`。YAML：`pins.yaml`。

### 🤖 Servos（舵机）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `standard_servo`<br>标准舵机 | `make_servo(model)` | SG90 / MG90S / MG996R / DS3218 | ![](../build123d_parts_lib/parts/servos/cache/standard_servo.png) |
| `servo_horn`<br>舵盘 | `make_servo_horn(type_)` | single / double / cross / disc | ![](../build123d_parts_lib/parts/servos/cache/servo_horn.png) |

> 模块路径：`build123d_parts_lib.parts.servos.<slug>`。YAML：`servos.yaml`。`sg90.py` 原文件保留向后兼容。

### ⚙️ Transmission（传动件）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `timing_pulley_gt2`<br>GT2 同步带轮 | `make_gt2_pulley(teeth, bore_d)` | 16T / 20T / 30T / 40T × ⌀5 / ⌀8 | ![](../build123d_parts_lib/parts/transmission/cache/timing_pulley_gt2.png) |
| `timing_belt_gt2`<br>GT2 同步带 | `make_gt2_belt(length, width, pulley_d)` | L110 / L158 / L200 / L280 / L380 | ![](../build123d_parts_lib/parts/transmission/cache/timing_belt_gt2.png) |
| `key_parallel`<br>平行键 | `make_parallel_key(width, height, length)` | 3×3 / 4×4 / 5×5 / 6×6 / 8×7（ISO 2491） | ![](../build123d_parts_lib/parts/transmission/cache/key_parallel.png) |

> 模块路径：`build123d_parts_lib.parts.transmission.<slug>`。YAML：`transmission.yaml`。

### 🔘 Retainers（卡簧）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `retaining_ring_shaft`<br>轴用弹性挡圈 | `make_retaining_ring_shaft(shaft_d)` | D4 / D5 / D6 / D8 / D10 / D12（GB/T 894.1） | ![](../build123d_parts_lib/parts/retainers/cache/retaining_ring_shaft.png) |
| `retaining_ring_hole`<br>孔用弹性挡圈 | `make_retaining_ring_hole(hole_d)` | D8 / D10 / D12 / D16 / D20 / D25（GB/T 893.1） | ![](../build123d_parts_lib/parts/retainers/cache/retaining_ring_hole.png) |

> 模块路径：`build123d_parts_lib.parts.retainers.<slug>`。YAML：`retainers.yaml`。

### 🔵 Seals（密封件）

| Slug | Factory | 覆盖规格 | 预览 |
|------|---------|---------|:----:|
| `oring`<br>O 型圈 | `make_oring(d1, d2)` | d2：1.5 / 2.0 / 2.5 / 3.5 mm，12 个常用规格（ISO 3601-1 / GB/T 3452.1） | ![](../build123d_parts_lib/parts/seals/cache/oring.png) |

> 模块路径：`build123d_parts_lib.parts.seals.<slug>`。YAML：`oring.yaml`。

---

## 🔧 modules/ — 功能模块

| Slug | Factory | 说明 |
|------|---------|------|
| `threaded_insert_boss`<br>热压铜螺母柱 | `make_m3_boss(...)` | FDM 热压铜螺母柱（M3×5-OD4.2 默认） |
| `snap_fit_latch`<br>悬臂卡扣 | `make_snap_latch(...)` | 悬臂卡扣 |
| `leg_segment`<br>腿段模板 | `make_leg_segment(...)` | 四足机器人腿段模板 |
| `foot_cap`<br>脚掌帽 | `make_foot_cap(...)` | 机器狗脚掌帽 |

## 🎨 generators/ — 参数化生成器

| Slug | Entry | 返回 |
|------|-------|------|
| `vents`<br>散热孔阵列 | `make_vent_pattern(target_face, ...)` | Sketch |
| `clearance`<br>螺丝通孔直径 | `get_clearance_diameter(m_size, fit)` | float (mm) |

## 🏗 templates/ — 项目模板

| Slug | Entry | 场景 |
|------|-------|------|
| `sg90_bracket`<br>SG90 安装座 | `make_sg90_bracket(...)` | SG90 舵机安装座 |
| `pcb_enclosure`<br>PCB 外壳 | `make_pcb_enclosure(...)` | PCB 外壳（MVP） |

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

## 统计（2026-04-28）

- **Factory 文件**：43 个 `.py`（26 紧固 + 4 轴承 + 4 销轴 + 3 舵机 + 3 传动 + 2 卡簧 + 1 密封）
- **参数化规格**：220+ 条（通过 NamedTuple 查表）
- **cache**：每 factory 1 STEP + 1 PNG
- **YAML 条目**：200+ 条

---

## 未来扩充

见 `docs/parts-roadmap.md`（P2 路线图）：
- P2：MGN 导轨 / 滚珠丝杠 / 联轴器 / 步进电机 / 齿轮参数化 / O 型圈
