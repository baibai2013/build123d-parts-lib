# transmission — 传动件标准库

机器人 / 3D 打印机 / CNC 场景常用传动标准件，均以 build123d 参数化建模，
导出 STEP 格式缓存，由 `transmission.yaml` 统一索引。

---

## 目录结构

```
transmission/
├── README.md                   # 本文件
├── transmission.yaml           # 所有规格索引（alias / dimensions / factory / cache）
├── timing_pulley_gt2.py        # GT2 同步带轮
├── timing_belt_gt2.py          # GT2 同步带（闭环）
├── key_parallel.py             # 平键（ISO 2491 / DIN 6885A）
├── spur_gear.py                # 直齿轮（ISO 54 / DIN 867）★ 计划中
└── cache/                      # 预生成 .step 文件
```

---

## 已有零件

### 1. GT2 同步带轮 `timing_pulley_gt2.py`

| 参数 | 说明 |
|------|------|
| 标准 | GT2（Gates Rubber / RepRap 社区） |
| 齿距 | 2.0 mm |
| 支持齿数 | 16T / 20T / 30T / 40T |
| 支持孔径 | ⌀5 / ⌀8 mm |
| 总高 | 8.0 mm（法兰各 1.0 mm + 带槽 6.0 mm） |
| 简化级别 | ★★☆☆☆ — 两端法兰 + 圆柱本体，无精确齿形 |

**坐标原点**：几何中心，Z 轴为旋转轴，`Z ∈ [-4, +4]` mm。

```python
from build123d_parts_lib.parts.transmission.timing_pulley_gt2 import make_gt2_pulley
part = make_gt2_pulley(teeth=20, bore_d=5.0)
```

---

### 2. GT2 同步带 `timing_belt_gt2.py`

| 参数 | 说明 |
|------|------|
| 标准 | GT2（2 mm 齿距，6 mm 宽） |
| 支持周长 | 110 / 158 / 200 / 280 / 380 mm |
| 带厚 | 1.38 mm |
| 简化级别 | ★☆☆☆☆ — 跑道形中空管，无齿形 |

**坐标原点**：带环几何中心，带宽沿 Z 方向，环形在 XY 平面展开。

```python
from build123d_parts_lib.parts.transmission.timing_belt_gt2 import make_gt2_belt
part = make_gt2_belt(length=200.0, width=6.0, pulley_d=12.7)
```

---

### 3. 平键 `key_parallel.py`

| 参数 | 说明 |
|------|------|
| 标准 | ISO 2491 / DIN 6885A（圆头 A 型） |
| 支持规格 | 3×3 / 4×4 / 5×5 / 6×6 / 8×7 mm |
| 标准长度 | 10 ~ 50 mm（各规格见下表） |
| 简化级别 | ★★★★☆ — 跑道形截面，几何准确 |

**坐标原点**：底面中心，长度沿 X，宽度沿 Y，高度沿 +Z。

| 规格 | 适配轴径 | 标准长度 (mm) |
|------|----------|---------------|
| 3×3  | ⌀6 ~ ⌀8   | 10, 12, 16, 20 |
| 4×4  | ⌀8 ~ ⌀10  | 10, 12, 16, 20, 25 |
| 5×5  | ⌀10 ~ ⌀12 | 16, 20, 25, 32, 40 |
| 6×6  | ⌀14 ~ ⌀16 | 20, 25, 32, 40, 50 |
| 8×7  | ⌀18 ~ ⌀22 | 25, 32, 40, 50 |

```python
from build123d_parts_lib.parts.transmission.key_parallel import make_parallel_key
part = make_parallel_key(width=5.0, height=5.0, length=20.0)
```

---

## 计划中零件

### 4. 直齿轮 `spur_gear.py` *(计划中)*

| 参数 | 说明 |
|------|------|
| 标准 | ISO 54 / DIN 867（模数系列） |
| 齿廓 | 渐开线（Involute），工业级精确建模 |
| 压力角 | 20°（标准） |
| 标准模数 | 0.5 / 0.8 / 1.0 / 1.25 / 1.5 / 2.0 / 2.5 / 3.0 mm |
| 简化级别 | ★★★★★ — 精确 involute 齿形 + 齿根圆角 |

优先规格：

| 模数 | 齿数 | 孔径 | 典型用途 |
|------|------|------|---------|
| m1.0 | 16T  | ⌀5   | 小型减速箱驱动齿轮 |
| m1.0 | 20T  | ⌀5   | 小型减速箱从动齿轮 |
| m1.0 | 32T  | ⌀8   | 关节减速级 |
| m1.0 | 40T  | ⌀8   | 高减速比从动轮 |
| m2.0 | 12T  | ⌀6   | 最小齿数限制（无根切） |
| m2.0 | 20T  | ⌀8   | 机器人关节标准配对 |
| m2.0 | 30T  | ⌀8   | 1.5× 减速 |
| m2.0 | 40T  | ⌀10  | 2× 减速 |

### 5. 锥齿轮 `bevel_gear.py` *(远期)*

90° 换向传动，差速器 / 机器人关节用。

### 6. 蜗轮蜗杆 `worm_gear.py` *(远期)*

大减速比（10:1 ~ 80:1）+ 自锁，关节驱动器用。

---

## 坐标系约定（全库统一）

| 零件类型 | 旋转轴 | 原点位置 |
|----------|--------|----------|
| 带轮 / 齿轮 / 法兰 | Z 轴 | 几何中心 |
| 带（线性） | 长度沿 X | 几何中心 |
| 键 / 线性件 | 长度沿 X | 底面中心 |

---

## 添加新规格流程

1. 在 `transmission.yaml` 新增条目（`aliases` / `dimensions` / `factory` / `cache`）
2. 在对应 `*.py` 的 `if __name__ == "__main__"` 添加规格并运行生成 cache
3. OCP 截图验证形状与关键尺寸
4. 更新 `__init__.py` 导出

---

## 参考标准

| 标准 | 内容 |
|------|------|
| GT2 (Gates Rubber) | 2 mm 齿距同步带 / 带轮 |
| ISO 2491 / DIN 6885A | 平键（圆头 A 型） |
| ISO 54 / DIN 867 | 渐开线直齿轮模数系列 |
| ISO 1328-1 | 齿轮精度等级 |
| ISO 23509 | 锥齿轮 |
