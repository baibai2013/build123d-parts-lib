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

# 谐波减速器
wave_gen_d_long = 17.0     # 波发生器长轴 mm
wave_gen_d_short= 15.5     # 波发生器短轴 mm（≈ 长轴 - 1.5）
wave_gen_bearing= (17.0, 23.0, 3.5)  # 薄截面轴承 ID×OD×W
flex_spline_od  = 32.0     # 柔轮外径 mm
flex_wall_t     = 1.2      # 柔轮壁厚 mm（TPU 打印关键）
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
