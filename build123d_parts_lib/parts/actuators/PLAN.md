# QDD 关节模组 — CAD 建模计划表

> **目标**：为 BOM.md 中的 6 件 3D 打印件 + 最终装配体建出参数化 build123d 模型，  
> 全部导出 STEP，打印件额外导出 STL。  
> **执行 skill**：`build123d-cad`（multi-part playbook）  
> **参考 BOM**：`parts/actuators/BOM.md`

---

## 模组关键参数（建模前锁定）

```python
# 谐波参数
flex_teeth      = 100      # 柔轮齿数
ring_teeth      = 102      # 刚轮齿数（= 柔轮 + 2）
module_m        = 0.3      # 模数
reduction_ratio = 50       # 减速比 = flex_teeth / 2

# 外形参数
outer_dia       = 45.0     # 模组外径 mm
axial_length    = 45.0     # 模组轴向总长 mm

# 电机（4010 外转子）
stator_od       = 40.0     # 定子外径 mm
stator_h        = 10.0     # 定子高度 mm
rotor_shaft_d   = 5.0      # 转子轴径 mm（h6 配合）
motor_bearing_f = 8.0      # 前轴承外径 MR84ZZ mm
motor_bearing_r = 6.0      # 后轴承外径 MR63ZZ mm

# 谐波减速器（有轴承设计 2026-05-11 重新设计）
wave_gen_d_long  = 21.45   # 波发生器凸轮长轴 mm（轴承内圈接触面）← 有轴承设计修正
wave_gen_d_short = 20.25   # 波发生器凸轮短轴 mm（长轴差1.2mm，δ=±0.3mm/side 驱动啮合）
wave_gen_bearing = (20.85, 26.85, 3.0)  # 薄截面深沟球 ID×OD×W；OD=柔轮内孔（26.85mm）
flex_spline_od   = 32.0    # 柔轮外径 mm
flex_wall_t     = 1.2      # 柔轮壁厚 mm（TPU 打印关键）
flex_cup_inner  = 26.85    # 柔轮内孔直径 mm（=2×cup_inner_r，波发生器直接接触面）
output_bearing  = (12.0, 28.0, 8.0)  # 7001C 角接触 ID×OD×W

# 编码器
encoder_pcb_d   = 20.0     # PCB 直径 mm
encoder_mag_d   = 6.0      # 磁钢直径 mm
encoder_mag_h   = 3.0      # 磁钢高度 mm
```

---

## 里程碑总览

| 里程碑 | 内容 | 产出 | 状态 |
|--------|------|------|:----:|
| **M0** | 参数确认 + 比例预览 | OCP bounding box proxy | ⬜ |
| **M1** | parts-lib 缺口补充（2 个新轴承） | `thin_section_bearing.py` `angular_contact_bearing.py` | ⬜ |
| **M2** | 3D 打印件建模（6 件） | 6 个 `.py` + STEP + STL | ⬜ |
| **M3** | 装配体 + 爆炸展开图 | `assembly.py` `exploded.py` | ⬜ |
| **M4** | 验证 + Cache 入库 | 通过三层验证，cache STEP/PNG 更新 | ⬜ |

---

## M0 — 比例预览（OCP Bounding Box Proxy）

**目的**：在建模前确认各零件比例和装配位置，不浪费建模时间。  
**方法**：build123d Algebra Mode，用 `Cylinder` / `Box` 占位。  
**输出文件**：`tests/qdd_module_proxy.py`

| 占位体 | 几何 | 颜色 |
|--------|------|------|
| 电机定子 | `Cylinder(r=20, h=10)` | steelblue |
| 谐波减速器区域 | `Cylinder(r=18, h=20)` | orange |
| 输出法兰 | `Cylinder(r=20, h=8)` | green |
| 编码器后盖 | `Cylinder(r=15, h=6)` | gray |

**确认门**：OCP 中旋转确认比例 → 进入 M1。

---

## M1 — parts-lib 缺口补充

### M1-1 薄截面深沟球轴承

| 项目 | 内容 |
|------|------|
| **文件** | `parts/bearings/thin_section_bearing.py` |
| **规格** | Φ17×Φ23×3.5（波发生器用）；可扩展参数化支持其他尺寸 |
| **几何方法** | `revolve()` 在 `BuildSketch(Plane.XZ)` 上画截面后旋转 |
| **YAML 更新** | `parts/bearings/bearings.yaml` 新增条目 |
| **验证** | `bbox ≈ (23, 23, 3.5)`；`is_valid`；STEP 重导入体积差 < 0.1% |
| **工时估算** | 1.5 h |
| **依赖** | 无 |
| **状态** | ⬜ |

### M1-2 角接触球轴承 7001C

| 项目 | 内容 |
|------|------|
| **文件** | `parts/bearings/angular_contact_bearing.py` |
| **规格** | 7001C：Φ12×Φ28×8（输出主轴承）；参数化支持 7000/7001/7002 系列 |
| **几何方法** | `revolve()` + 内外圈截面，不建滚珠（占位即可） |
| **YAML 更新** | `parts/bearings/bearings.yaml` 新增条目 |
| **验证** | `bbox ≈ (28, 28, 8)`；DB 对背装配时总宽 16 mm |
| **工时估算** | 1.5 h |
| **依赖** | 无 |
| **状态** | ⬜ |

---

## M2 — 3D 打印件建模（6 件）

优先级排序：主外壳最复杂（集成刚轮齿形）→ 柔轮（薄壁 TPU）→ 波发生器凸轮 → 其余。

---

### M2-1 主外壳 / 刚轮一体件

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/housing_circular_spline.py` |
| **功能** | 外壳 + 刚轮齿形内壁 + 输出轴承座 + 端盖安装螺纹孔 |
| **外形** | Φ45 mm × 30 mm，内腔 Φ32 mm |
| **几何方法** | `Cylinder` 抽壳 + 内壁刚轮齿形（`gggears` 或根实体逐齿融合）+ `PolarLocations` 螺纹孔 |
| **打印材料** | **PA12 SLS**（推荐）/ ASA FDM（降级） |
| **关键公差** | 轴承座 Φ28 H7（与 7001C 配合）；刚轮内径齿形精度 ±0.05 mm |
| **STEP + STL** | 两份导出 |
| **工时估算** | **4 h**（最复杂件）|
| **依赖** | M1-2（7001C 轴承确认外径 28 mm）|
| **状态** | ⬜ |

> ⚠️ **刚轮齿形渲染**：102 齿大型非凸多边形，必须用"根实体 + 逐齿 Algebra Mode 融合"（见 build123d-cad SKILL.md §大型非凸多边形面）。

---

### M2-2 柔轮（Flex Spline）

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/flex_spline.py` |
| **功能** | 薄壁弹性齿轮，传递谐波减速输出 |
| **外形** | Φ32 mm × 20 mm，壁厚 1.2 mm，100 齿 m=0.3 |
| **几何方法** | 根圆柱 `Cylinder` + 逐齿融合（渐开线齿形）+ 底部法兰 `extrude` |
| **打印材料** | **TPU 95A**，层高 0.08 mm，喷嘴 0.25 mm，100% 填充 |
| **关键尺寸** | 壁厚均匀性 ±0.05 mm；齿顶高 = m × 1.0 = 0.3 mm |
| **STEP + STL** | 两份导出 |
| **工时估算** | **4 h**（齿形 + 薄壁）|
| **依赖** | M1-1（薄截面轴承确认波发生器尺寸）|
| **状态** | ⬜ |

> ⚠️ **TPU 打印注意**：柔轮是全模组最关键的 3D 打印件，打完必须用游标卡尺量壁厚 3 处，偏差 > 0.1 mm 需重打。

---

### M2-3 波发生器凸轮

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/wave_generator_cam.py` |
| **功能** | 椭圆凸轮，套上薄截面轴承后撑开柔轮 |
| **外形** | 椭圆截面，长轴 17 mm / 短轴 15.5 mm，高 14 mm |
| **几何方法** | `BuildSketch` 椭圆 + `extrude` + 中心轴孔 Φ5 H7 + 键槽 |
| **打印材料** | **光固化树脂（SLA）** 首选；PETG 降级 |
| **关键公差** | 中心孔 Φ5 H7（配合转子轴 h6）；椭圆度 ±0.1 mm |
| **STEP + STL** | 两份导出 |
| **工时估算** | 2 h |
| **依赖** | 无（尺寸已知）|
| **状态** | ⬜ |

---

### M2-4 输出法兰

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/output_flange.py` |
| **功能** | 连接柔轮输出端，传递扭矩到外部负载 |
| **外形** | Φ40 mm × 8 mm，6× M2 PCD 34 mm 安装孔，中心 Φ12 轴孔 |
| **几何方法** | `Cylinder` + `Hole` + `PolarLocations` |
| **打印材料** | PETG |
| **工时估算** | 1 h |
| **依赖** | M2-2（柔轮输出端法兰直径确认）|
| **状态** | ⬜ |

---

### M2-5 电机前端盖

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/motor_endcap_front.py` |
| **功能** | 电机前端轴承座 + 与主外壳连接 |
| **外形** | Φ45 mm × 5 mm，轴承座 Φ8 H7，4× M3 安装孔 |
| **几何方法** | `Cylinder` + `Hole` + `PolarLocations` |
| **打印材料** | PETG |
| **工时估算** | 1 h |
| **依赖** | M2-1（主外壳螺孔位置确认）|
| **状态** | ⬜ |

---

### M2-6 编码器后盖

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/encoder_cover.py` |
| **功能** | AS5047P PCB 安装 + 编码器磁钢对中定位槽 |
| **外形** | Φ30 mm × 6 mm，PCB 安装柱 Φ20 mm，磁钢槽 Φ6.2×3.5 |
| **几何方法** | `Cylinder` + `PolarLocations` PCB 安装孔 + 磁钢槽 `Hole` |
| **打印材料** | PETG |
| **工时估算** | 1 h |
| **依赖** | 无 |
| **状态** | ⬜ |

---

## M3 — 装配体 + 爆炸展开

### M3-1 完整装配

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/assembly.py` |
| **方法** | `Compound` + `RigidJoint`（固定装配），OCP 多色展示 |
| **产出** | `assembly.step`（含所有零件位置）|
| **验证** | `do_children_intersect()` = False（无干涉）|
| **工时估算** | 2 h |
| **依赖** | M2 全部完成 |
| **状态** | ⬜ |

### M3-2 爆炸展开图

| 项目 | 内容 |
|------|------|
| **文件** | `parts/actuators/exploded.py` |
| **方法** | OCP `Animation`，沿轴向炸开，16 s 循环 |
| **工时估算** | 1 h |
| **依赖** | M3-1 |
| **状态** | ⬜ |

---

## M4 — 验证 + Cache 入库

| 任务 | 方法 | 通过条件 |
|------|------|---------|
| 三层验证（每个 .py） | `is_valid` + `bbox` + STEP 重导入体积差 | 全部 < 0.1% 偏差 |
| 打印件壁厚检查 | 柔轮壁厚断言 ≥ 1.1 mm | Pass |
| Cache STEP 生成 | `scripts/build_cache.py` 新增代表规格 | 无 `[FAIL]` |
| Cache PNG 生成 | OCP 截图（优先）/ VTK 兜底 | 几何可辨认 |
| `parts-index.md` 更新 | 新增 actuators 类别行 | — |

---

## 关键约束备忘

| 约束 | 数值 | 原因 |
|------|------|------|
| 柔轮壁厚均匀性 | ±0.05 mm | 壁厚不均 → 谐波运行噪声 / 疲劳裂纹 |
| 波发生器凸轮同心度 | ≤ 0.02 mm | 偏心 → 柔轮单侧磨损 |
| 编码器磁钢对中 | ≤ 0.5 mm | 超出 → AS5047P 线性度下降 |
| 轴承座配合（主轴承） | Φ28 **H7** / 轴 **g6** | 间隙配合保证可拆性 |
| 热嵌铜螺母嵌入深度 | ≥ 螺母高度 + 0.5 mm | 防拔出 |
| 3D 打印非受力件最小壁厚 | 1.5 mm（PETG FDM） | 打印强度下限 |

---

## 文件树（完成后）

```
parts/actuators/
├── __init__.py
├── BOM.md                        ✅ 已完成
├── PLAN.md                       ✅ 本文件
├── housing_circular_spline.py    ⬜ M2-1
├── flex_spline.py                ⬜ M2-2
├── wave_generator_cam.py         ⬜ M2-3
├── output_flange.py              ⬜ M2-4
├── motor_endcap_front.py         ⬜ M2-5
├── encoder_cover.py              ⬜ M2-6
├── assembly.py                   ⬜ M3-1
├── exploded.py                   ⬜ M3-2
└── cache/
    ├── housing_circular_spline.step
    ├── housing_circular_spline.png
    ├── flex_spline.step
    └── ...
```

---

*计划表版本：2026-04-29 | 执行时更新状态列*

---

## 电机原材料 + 备选轴承 建模计划（2026-05-09 追加，2026-05-09 重制）

> **背景**：BOM.md 中 E1/E2/E3/P1 共 4 类尚未建模，用户确认全部实现。  
> **执行原则**：每个零件完成几何后必须先走 `/cad-vision-verify`，通过 `verdict=PASS` 后再走标件入库流程（actuator 专属件走 A5，标准件 needle_bearing 走完整 A1-A5）。  
> **cache 规范**：每个 factory 只入 1 对 `<slug>.step` + `<slug>.png`，多角度验证图留在 `verify_temp/`，不提交。

---

### 关键尺寸链（已验算）

```
stator tooth-tip OD = 40 mm
+ air_gap 0.25 mm           → magnet_inner_r = 20.25 mm
+ magnet_t 2 mm             → magnet_outer_r = 22.25 mm
+ shell_wall 1.5 mm         → rotor_shell_OD = 47.5 mm  ← 电机段超出 Φ45mm 约束（方案 A）
```

### 装配关系（cross_refs）

```
rotor_shaft ──同轴──→ motor_stator（穿过 stator_id=14 内孔）
rotor_shaft ──同轴压配──→ motor_rotor_shell（中心孔 Φ5）
motor_stator ──气隙 0.25mm──→ arc_magnet × 14
motor_rotor_shell ──包裹定子──→ motor_stator（r 方向）
rotor_shaft ──键槽对位──→ wave_generator_cam（key_w=2.0, key_hub_depth=1.2, +Y）
```

---

### 里程碑总览

| # | 里程碑 | 文件 | 关键尺寸 | 状态 |
|---|--------|------|---------|:----:|
| E-1 | 转子轴 | `actuators/rotor_shaft.py` | Φ5 h6 × 45 mm，DIN 6885 键槽 2×1.0，前轴颈 Φ4×3，M3 盲孔 | 🔨 代码完成，待验证入库 |
| E-2 | 电机定子 | `actuators/motor_stator.py` | 4010，OD=40 mm，H=10 mm，12 槽，yoke_od=28 mm | ⬜ |
| E-3 | 外转子壳 + 弧形磁钢 | `actuators/motor_rotor.py` | 壳 Φ47.5×12，14 极；磁钢 α=19.3°，t=2 mm | ⬜ |
| P1 | 滚针轴承（标准件） | `bearings/needle_bearing.py` | HK0608 / HK0810 / HK1010，无内圈 | ⬜ |
| FIN | 装配体更新 | `actuators/assembly.py` | 电机子总成 z=28~42 mm | ⬜ |

---

### E-1 转子轴 — 执行流程

> 代码已完成（`rotor_shaft.py`），STEP 已在 `cache/rotor_shaft.step`，尚未走视觉验证和入库。

**Step 1 — Layer 0 验证（已通过，确认即可）**

```bash
cd /Users/liyijiang/work/build123d-parts-lib
python3 -m build123d_parts_lib.parts.actuators.rotor_shaft
# 期望：BRep + BBox ✓，STEP 写出，无报错
```

**Step 2 — Layer 1 视觉预览（OCP 截图）**

```python
from build123d_parts_lib.parts.actuators.rotor_shaft import make_rotor_shaft
from build123d_parts_lib._preview_ocp import save_preview_png_auto

part = make_rotor_shaft()
save_preview_png_auto(part, "build123d_parts_lib/parts/actuators/cache/rotor_shaft.png",
                      title="QDD Rotor Shaft  Φ5h6×45")
```

视觉检查清单：键槽可见 / 前轴颈台阶清晰 / 后端盲孔开口可见 / 两端倒角 C0.3 / 无破面

**Step 3 — Layer 2 `/cad-vision-verify`（标准件入库门控）**

```python
import sys; sys.path.insert(0, "/Users/liyijiang/.agents/skills/cad-vision-verify/scripts")
from verify_loop import verify_standard_part
from build123d_parts_lib.parts.actuators.rotor_shaft import make_rotor_shaft

result = verify_standard_part(
    solid         = make_rotor_shaft(),
    slug          = "rotor_shaft",
    model         = "QDD_5h6x45",
    yaml_path     = None,           # actuator 专属件，无独立 YAML
    contract_path = None,
    verify_temp   = "./verify_temp",
)
print(result["verdict"])  # 需 PASS 才进 Step 4
```

**Step 4 — 入库 A5（verdict=PASS 后）**

```bash
# 在 scripts/build_cache.py _rep_bundle() 中已有条目，直接运行
python3 scripts/build_cache.py --only rotor_shaft
# 确认 cache/rotor_shaft.step + cache/rotor_shaft.png 存在且无多角度副产物
```

更新 `validate_actuators.py`：
```python
("rotor_shaft", make_rotor_shaft, 5.0, 45.0, 0.2, 0.2, False),
```

---

### E-2 电机定子 — 执行流程

> **几何**：12 槽外定子，单体 Part（不含绕组线圈，工程简化）。

**关键参数**：

| 参数 | 值 |
|------|---|
| stator_od | 40.0 mm（齿顶外径） |
| stator_h | 10.0 mm |
| yoke_od | 28.0 mm（轭部外径，= 内腔边界） |
| stator_id | 14.0 mm（穿轴内孔） |
| n_slots | 12 |
| slot_depth | ≈ 6.0 mm（= (stator_od - yoke_od) / 2） |
| slot_opening | ≈ 2.5 mm |

**建模策略**：外圆柱（Φ40×10）+ 内孔（Φ14）+ 12 槽（PolarLocations + 矩形切槽）

**Step 1 — A3 建模**：写 `actuators/motor_stator.py`，`make_motor_stator() -> Part`

**Step 2 — Layer 0**：`python3 -m build123d_parts_lib.parts.actuators.motor_stator`  
期望：`bbox ≈ (40, 40, 10)`，`volume` 合理，`is_valid` 或 `volume > 0`（12 槽布尔可能触发 soft is_valid）

**Step 3 — Layer 1**：OCP/VTK 截图，检查槽开口均匀、内孔贯通、无破面

**Step 4 — Layer 2 `/cad-vision-verify`**：

```python
result = verify_standard_part(
    solid         = make_motor_stator(),
    slug          = "motor_stator",
    model         = "4010_12slot",
    yaml_path     = None,
    contract_path = None,
    verify_temp   = "./verify_temp",
)
```

视觉检查重点：TOP 视角可数 12 槽开口 / FRONT 可见齿高 / 内孔贯通

**Step 5 — A5 入库**：
- `scripts/build_cache.py` 新增条目 `("actuators", "motor_stator", make_motor_stator, {}, "QDD Motor Stator 4010 12-slot")`
- `validate_actuators.py` 新增：`("motor_stator", make_motor_stator, 40.0, 10.0, 1.0, 0.2, True)`

---

### E-3 外转子壳 + 弧形磁钢 — 执行流程

> **几何**：两个独立 Part：外转子壳（薄壁圆筒 + 端板）+ 弧形磁钢 × 14（PolarLocations）。

**关键参数**：

| 参数 | 值 |
|------|---|
| rotor_shell_od | 47.5 mm |
| rotor_shell_h | 12.0 mm |
| shell_wall_t | 1.5 mm |
| center_bore_d | 5.0 mm（配转子轴 h6） |
| n_poles | 14 |
| magnet_t | 2.0 mm |
| magnet_inner_r | 20.25 mm |
| magnet_arc_angle | 360/14 × 0.9 ≈ 23.1°（极弧系数 0.9） |
| magnet_h | 10.0 mm（同定子高） |

**建模策略**：
- 转子壳：外圆柱抽壳 + 端板 + 中心轴孔
- 弧形磁钢：`BuildSketch` 弧形截面（内外半径 + 极弧角）+ extrude × 14（PolarLocations）
- 两者分别 `make_rotor_shell()` / `make_arc_magnet()` 独立 factory，`make_motor_rotor()` 返回 Compound

**Step 1 — A3 建模**：写 `actuators/motor_rotor.py`

**Step 2 — Layer 0**：
```bash
python3 -m build123d_parts_lib.parts.actuators.motor_rotor
# 期望：shell bbox ≈ (47.5, 47.5, 12)；磁钢 bbox ≈ (44.5, 44.5, 10)
```

**Step 3 — Layer 1**：OCP 截图，检查 14 极弧形磁钢均匀分布、转子壳端板完整

**Step 4 — Layer 2 `/cad-vision-verify`**（外转子壳 + 磁钢分别验证）：

```python
# 转子壳
result_shell = verify_standard_part(
    solid="rotor_shell", model="QDD_47.5x12", yaml_path=None, contract_path=None,
    verify_temp="./verify_temp")
# 磁钢（TOP 视角需可数 14 块）
result_magnet = verify_standard_part(
    solid="arc_magnet_array", model="14pole_23deg", yaml_path=None, contract_path=None,
    verify_temp="./verify_temp")
```

**Step 5 — A5 入库**：
- `build_cache.py` 新增 `motor_rotor_shell` + `arc_magnet` 两条代表规格
- `validate_actuators.py` 新增：
  ```python
  ("motor_rotor_shell", ..., 47.5, 12.0, 1.0, 0.2, False),
  ("arc_magnet",        ..., 44.5, 10.0, 1.0, 0.2, True),
  ```

---

### P1 滚针轴承（标准件）— 完整 A1-A5 执行流程

> 这是唯一一个**纯标准件**，需走 standard-parts-playbook 完整 A1-A5。

**A1 — 数据收集**

目标规格：HK0608 / HK0810 / HK1010（冲压外圈，无内圈，滚针保持架）

| 型号 | d（内径）| D（外径）| B（宽）| 参考数据源 |
|------|---------|---------|-------|---------|
| HK0608 | 6 mm | 10 mm | 8 mm | INA/FAG HK catalog |
| HK0810 | 8 mm | 12 mm | 10 mm | INA/FAG HK catalog |
| HK1010 | 10 mm | 14 mm | 10 mm | INA/FAG HK catalog |

额外收集：`n_needles`（滚针数 ≈ 10）、`d_needle`（滚针直径 ≈ 1.5 mm）  
数据源：`WebSearch "INA HK0608 dimensions specifications"` → confidence ≥ 4

**A2 — YAML 条目 + Contract**

- YAML 新增至 `build123d_parts_lib/parts/bearings/bearings.yaml`（key：`HK0608` / `HK0810` / `HK1010`）
- Contract 新建：`parts/bearings/contracts/needle_bearing_contract.yaml`

Contract 骨架：
```yaml
slug: needle_bearing
part_class: drawn-cup-needle-bearing
compound_structure: null   # 单体 Part（工程简化，不建滚针）
visual_features:
  - name: outer_cup
    description: "薄壁冲压外圈，无内圈，内孔贯通可见"
    required: true
    views: [ISO, FRONT]
geometry_invariants:
  - description: "外圈内径必须大于内径"
    expr: "g['r_inner_cup'] > g['r_bore']"
  - description: "壁厚合理（冲压件 ~0.5 mm）"
    expr: "g['r_outer'] - g['r_inner_cup'] < 2.5"
```

**A3 — Python 模块**

文件：`build123d_parts_lib/parts/bearings/needle_bearing.py`  
Factory：`make_needle_bearing(model: str = "HK0608") -> Part`  
几何：外圈薄壁圆筒（revolve 截面）+ 两端倒角，工程简化不建滚针  
四层结构：`NeedleBearingSpec` NamedTuple + `_FALLBACK` + `_load_specs()` + `make_needle_bearing()`

**A4 — 三层验证**

```bash
# Layer 0
python3 -m build123d_parts_lib.parts.bearings.needle_bearing
# 期望：HK0608 bbox ≈ (10, 10, 8)；HK0810 ≈ (12, 12, 10)；HK1010 ≈ (14, 14, 10)

# Layer 1 — OCP/VTK 截图
# 检查：薄壁外圈清晰 / 内孔贯通 / 两端倒角 / 无破面

# Layer 2 — /cad-vision-verify
python3 /Users/liyijiang/.agents/skills/cad-vision-verify/scripts/verify_loop.py \
  --mode standard-part \
  --slug needle_bearing \
  --model HK0608 \
  --yaml build123d_parts_lib/parts/bearings/bearings.yaml \
  --contract build123d_parts_lib/parts/bearings/contracts/needle_bearing_contract.yaml \
  --verify-temp ./verify_temp
# verdict=PASS（score ≥ 80）才进 A5
```

**A5 — 入库收尾**

```bash
# build_cache.py 新增代表规格 HK0608
# ("bearings", "needle_bearing", make_needle_bearing, {"model": "HK0608"}, "Needle Bearing  HK0608")
python3 scripts/build_cache.py --only needle_bearing

# 更新 docs/parts-index.md（bearings 表格新增一行）
# 更新 skill data-sources: ~/.agents/skills/build123d-cad/references/data-sources/bearings.yaml
# Commit 两个 repo（parts-lib + skill）
```

---

### FIN — 装配体更新

> 依赖 E-1/E-2/E-3 全部 `verdict=PASS` 入库后执行。

更新 `actuators/assembly.py`：在已有 6 件装配基础上加入电机子总成（z=28~42 mm）：
- `motor_stator` 固定在 z=28 mm，`RigidJoint`
- `rotor_shaft` 穿过定子内孔（Φ14），同轴
- `motor_rotor` 套在定子外（气隙 0.25 mm），随轴转动
- 14 块弧形磁钢与转子壳随轴旋转

验证：`assembly.do_children_intersect() == False`（无干涉）

---

### 进度追踪

| # | 步骤 | 完成标志 | 状态 |
|---|------|---------|:----:|
| E-1-1 | rotor_shaft Layer 0 验证 | `is_valid` + bbox ✓ | ✅ |
| E-1-2 | rotor_shaft Layer 1 截图 | `cache/rotor_shaft.png` 存在 | ✅ |
| E-1-3 | rotor_shaft Layer 2 verify | `verdict=PASS` | ✅ |
| E-1-4 | rotor_shaft A5 入库 | `build_cache.py` ✓，validate 条目 ✓ | ✅ |
| E-2-1 | motor_stator A3 建模 | `motor_stator.py` 完成 | ✅ |
| E-2-2 | motor_stator Layer 0/1 | bbox ≈ (40,40,10) ✓ | ✅ |
| E-2-3 | motor_stator Layer 2 verify | `verdict=PASS` | ✅ |
| E-2-4 | motor_stator A5 入库 | build_cache ✓ | ✅ |
| E-3-1 | motor_rotor A3 建模 | `motor_rotor.py` 完成 | ✅ |
| E-3-2 | motor_rotor Layer 0/1 | shell + magnet bbox ✓ | ✅ |
| E-3-3 | motor_rotor Layer 2 verify | `verdict=PASS`（壳+磁钢各一次）| ✅ |
| E-3-4 | motor_rotor A5 入库 | build_cache ✓（2 条目）| ✅ |
| P1-1 | needle_bearing A1 数据收集 | INA/FAG HK 三型号尺寸确认 | ✅ |
| P1-2 | needle_bearing A2 YAML+Contract | bearings.yaml ✓，contract ✓ | ✅ |
| P1-3 | needle_bearing A3 建模 | `needle_bearing.py` 完成 | ✅ |
| P1-4 | needle_bearing A4 三层验证 | `verdict=PASS` | ✅ |
| P1-5 | needle_bearing A5 入库 | build_cache ✓，skill YAML ✓，index ✓ | ✅ |
| FIN | assembly.py 电机子总成 | volume=86273mm³, STEP RT 0.0084% ✓ | ✅ |

*计划版本：2026-05-09 重制*

---

## 2026-05-11 设计修正记录

### FIX-1 波发生器凸轮椭圆参数错误

**问题**：`wave_generator_cam.py` 原始长轴 27.0 mm / 短轴 26.5 mm，差值仅 0.5 mm，  
单侧形变量 δ = 0.075 mm < 0.3 mm 需求 → 柔轮齿与刚轮齿始终无法啮合。

**根因**：设计阶段椭圆直径误用了薄截面轴承 OD（Φ23 mm 附近），而非基于  
柔轮内孔几何计算（cup_inner_r = 13.425 mm → 内孔 Φ26.85 mm + 2×0.3 mm 变形量）。

**修正**：
```python
wave_gen_d_long  = 27.45  # +0.3 mm/side 形变量，齿进入刚轮啮合区
wave_gen_d_short = 26.25  # −0.3 mm/side 间隙，齿脱离刚轮区
# 验证：required_δ = m × (ring_teeth − flex_teeth) / 2 = 0.3 × 2/2 = 0.3 mm ✓
```

**Layer 0 验证**：`bbox ≈ (27.45, 26.25, 14.00)` + `aspect_diff=1.20mm ✓`

---

### FIX-2 柔轮法兰缺少 M2 热嵌铜螺母孔

**问题**：`flex_spline.py` 原始法兰无 M2 安装孔，而 `output_flange.py` 有 6×M2 间隙孔  
（Ø2.4mm，PCD 34mm）→ 柔轮与输出法兰无法物理连接，无法传递扭矩。

**修正**：在法兰面（z=0，输出端）新增 6×M2 热嵌铜螺母盲孔：Ø3.5 mm，深 4 mm，PCD 34 mm。

---

### FIX-4 波发生器凸轮改为有轴承设计

**问题**：原无轴承设计（SLA 凸轮 Φ27.45×Φ26.25 直接滑接 TPU 柔轮内孔 + PTFE 润滑）  
在 >200 rpm 高速高占空比工况下，动摩擦界面持续产热，TPU 内孔随温升逐渐软化失圆；  
对仿生狗步态（峰值 ~300 rpm）不可靠，不适合量产。

**根因**：无轴承设计以省去薄截面轴承为代价，引入了持续摩擦界面。

**修正**：恢复薄截面轴承（Φ20.85×Φ26.85×3 mm，定制规格）：

```python
# 推导（有轴承设计）：
# flex_inner_r = cup_inner_r = 13.425 mm，δ = 0.3 mm/side，bearing_wall = 3.0 mm
# cam_long_r  = flex_inner_r + δ − bearing_wall = 13.425 + 0.3 − 3.0 = 10.725 mm
# cam_short_r = flex_inner_r − δ − bearing_wall = 13.425 − 0.3 − 3.0 = 10.125 mm
wave_gen_d_long  = 21.45   # = 2 × 10.725 mm（轴承内圈长轴接触面）
wave_gen_d_short = 20.25   # = 2 × 10.125 mm
wave_gen_bearing = (20.85, 26.85, 3.0)  # ID×OD×W；OD 精配柔轮内孔 26.85 mm
```

**Layer 0 验证预期**：`bbox ≈ (21.45, 20.25, 14.00)` + `aspect_diff=1.20 mm ✓`

---

### FIX-3 柔轮 BRep 无效导致法兰+杯体融合失败

**问题**：100 次逐齿 Algebra Mode ADD 操作后，`cup_tube.is_valid=False`  
（OCC BRep 校验无法通过，但几何体积正确）。`flange + cup_positioned` BRep fuse  
因无效操作数静默失败，只返回法兰（Z=3mm）而非完整柔轮（Z=20mm）。

**修正**：Step 6 改为 `Compound(children=[flange, cup_positioned])`，绕过 BRep fuse。  
此为 `assembly.py` 中已文档化的标准做法（含 100 齿布尔历史的零件 is_valid=False 属已知行为）。

**Layer 0 验证**：`volume=3882 mm³ ≥ 3500 ✓`，`bbox.Z=20.0 mm ✓`
