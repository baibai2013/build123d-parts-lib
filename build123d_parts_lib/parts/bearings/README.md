# Bearings — 轴承

工业级深沟球轴承实体，包含外圈、内圈、滚珠、保持架四个组件。

---

## 覆盖零件

| Slug | Factory | 支持型号 |
|------|---------|---------|
| `ball_bearing` | `make_ball_bearing(model)` | 608ZZ / 624ZZ / 625ZZ / 626ZZ / 6000ZZ / 6001-2RS / 6002ZZ |
| `mr_bearing` | `make_mr_bearing(model)` | MR63ZZ / MR74ZZ / MR84ZZ / MR85ZZ / MR104ZZ |
| `flanged_bearing` | `make_flanged_bearing(model)` | F688ZZ / F693ZZ / F623ZZ / F624ZZ / F625ZZ / F684ZZ |

尺寸数据来源：`bearings.yaml` / `lm_bearings.yaml`

---

## 几何特点（工业级）

所有深沟球轴承由 `_bearing_geometry.py::make_deep_groove_bearing_compound()` 生成，共享同一套核心几何：

```
外圈（outer ring）
  └─ 内侧带环面滚道沟槽（torus subtraction raceway groove）

内圈（inner ring）
  └─ 外侧带环面滚道沟槽

滚珠（steel balls × N 颗）
  └─ 均匀分布在节圆上（PolarLocations on pitch circle）

保持架（cage）
  └─ 圆柱环，带等间距球窝（Sphere subtraction pockets）
```

### 设计系数

| 参数 | 计算方式 | 说明 |
|------|---------|------|
| `d_ball` | `min(gap × 0.58, B × 0.85)` | 受径向间隙和轴承宽度双重约束 |
| `r_groove` | `d_ball × 0.52` | 沟槽半径略大于球（4% 润滑间隙） |
| `n_balls` | `max(6, int(2π·r_pc / (d_ball × 1.6)))` | 由节圆周长推导，最少 6 颗 |

---

## 返回类型

所有 factory 返回 `Compound`，子件带 label + 金属色：

```python
Compound
├─ "{MODEL}/outer_ring"   # Color("lightgray")  钢色
├─ "{MODEL}/inner_ring"   # Color("lightgray")  钢色
├─ "{MODEL}/cage"         # Color("goldenrod")  铜黄色
├─ "{MODEL}/ball_00"      # Color("silver")     镜面钢
├─ "{MODEL}/ball_01"
└─ ...  (N 颗，N 由型号尺寸决定)
```

**法兰轴承**额外包含：
```
└─ "{MODEL}/flange"       # Color("lightgray")  法兰盘
```

---

## 使用示例

```python
from build123d_parts_lib.parts.bearings.ball_bearing import make_ball_bearing
from build123d_parts_lib.parts.bearings.mr_bearing import make_mr_bearing
from build123d_parts_lib.parts.bearings.flanged_bearing import make_flanged_bearing
from build123d import export_step

# 标准深沟球轴承
b608 = make_ball_bearing("608ZZ")
export_step(b608, "608zz.step")

# 微型轴承
mr85 = make_mr_bearing("MR85ZZ")

# 法兰轴承
f688 = make_flanged_bearing("F688ZZ")

# 访问子件（如获取外圈）
outer = next(c for c in b608.children if "outer_ring" in c.label)
print(f"outer ring volume: {outer.volume:.2f} mm³")
```

---

## 模块结构

```
bearings/
├─ _bearing_geometry.py   # 共享几何核心（raceway + balls + cage）
├─ ball_bearing.py         # 深沟球轴承 factory
├─ mr_bearing.py           # MR 微型轴承 factory
├─ flanged_bearing.py      # 法兰球轴承 factory
├─ linear_bushing.py       # 直线轴承（独立实现）
├─ bearings.yaml           # 深沟球轴承 / MR / 法兰尺寸数据
├─ lm_bearings.yaml        # LM 直线轴承尺寸数据
└─ cache/                  # 预生成 STEP + PNG
   ├─ ball_bearing.step / .png
   ├─ mr_bearing.step / .png
   └─ flanged_bearing.step / .png
```

---

## Cache 管理

```bash
# 重建 bearings 类别 cache（代表规格）
python scripts/build_cache.py --only bearings

# 导出指定型号
python scripts/build_cache.py --only ball_bearing --model 6000ZZ
# → cache/ball_bearing_6000zz.step + .png

# 验证 cache 与 factory 一致性
python scripts/verify_cache.py --only bearings
```

验证层级：L1 文件存在、L2 bbox Δ < 0.5 mm（主断言）、L3 体积 Δ < 10%。

---

## STEP 往返说明

保持架含球窝（Compound 带子孔）经 OCP XDE 导出 STEP 后，`import_step` 回来的某些 Solid 法向可能翻转（`volume` 为负）。`verify_cache.py` 用 `abs(s.volume)` 消除此差异。bbox 主断言不受影响，几何外形保真。
