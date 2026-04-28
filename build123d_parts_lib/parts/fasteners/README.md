# fasteners — 紧固件参数化零件库

build123d 参数化紧固件库，用于 CAD 装配预览、3D 打印参考与仿真建模。所有零件几何通过 build123d revolve/extrude 构造，可直接导出 STEP。

---

## 1. 概述 · Overview

- **定位**：标准紧固件参数化模型（ISO / DIN / GB），适合作为装配参考与 3D 打印样品
- **几何风格**：工业级细节，包含 ISO 锯齿螺纹、十字槽锥度、内六角凹槽、头部倒角等可见结构
- **不适合**：高精度装配公差仿真（螺纹为可视化几何，非真实啮合面）
- **规格数据**：`fasteners.yaml`（YAML 驱动，带数据来源与置信度）
- **缓存产物**：`cache/*.step`，由 `scripts/rebuild_cache.py` 批量生成

---

## 2. 支持的标件类型 · Supported Types

### 螺丝 · Screws

| 模块 | 标准 | 头型 × 驱动 | 规格 | 入口函数 |
|------|------|------------|------|---------|
| `socket_head_screw.py` | ISO 4762 | 圆柱头 × 内六角 | M2 – M10 | `make_socket_head_screw(size, length)` |
| `countersunk_screw.py` | ISO 10642 | 沉头 × 内六角 | M2 – M5 | `make_countersunk_screw(size, length)` |
| `screw_button_hex.py` | ISO 7380 | 圆头（球冠）× 内六角 | M3 – M5 | `make_button_hex_screw(size, length)` |
| `screw_csk_phillips.py` | ISO 7046 | 沉头 × 十字槽 | M3 – M5 | `make_csk_phillips_screw(size, length)` |
| `screw_csk_slotted.py` | ISO 2009 | 沉头 × 一字槽 | M3 – M5 | `make_csk_slotted_screw(size, length)` |
| `screw_pan_phillips.py` | ISO 7045 | 圆头盘 × 十字槽 | M3 – M5 | `make_pan_phillips_screw(size, length)` |
| `screw_pan_slotted.py` | ISO 1580 | 圆头盘 × 一字槽 | M3 – M5 | `make_pan_slotted_screw(size, length)` |

### 螺栓 · Bolts

| 模块 | 标准 | 规格 | 入口函数 |
|------|------|------|---------|
| `hex_bolt.py` | DIN 933 / ISO 4017 | M4 – M10 | `make_hex_bolt(size, length)` |

### 螺母 · Nuts

| 模块 | 标准 | 外形 | 规格 | 入口函数 |
|------|------|------|------|---------|
| `nut_hex.py` | ISO 4032 / GB/T 6172 / DIN 985 | 六角 / 薄六角 / 尼龙锁紧 | M2 – M10 | `make_hex_nut(size, standard)` |
| `nut_cap.py` | DIN 1587 | 盖形（半球顶） | M3 – M5 | `make_cap_nut(size)` |
| `nut_flange.py` | DIN 6923 | 法兰（底盘） | M3 – M5 | `make_flange_nut(size)` |
| `nut_wing.py` | DIN 315 | 蝶形（两侧翼片） | M3 – M5 | `make_wing_nut(size)` |
| `nut_square.py` | DIN 562 | 方形（四棱） | M3 – M5 | `make_square_nut(size)` |
| `nut_tslot.py` | 2020/3030 铝型材 | T 型（嵌槽） | M3 – M5 | `make_tslot_nut(size)` |

### 垫圈 · Washers

| 模块 | 标准 | 规格 | 入口函数 |
|------|------|------|---------|
| `washer.py` | ISO 7089 (平垫) / GB/T 93 (弹垫) | M2 – M5 | `make_washer(size, type_)` |

### 嵌件 · Inserts

| 模块 | 标准 | 规格 | 入口函数 |
|------|------|------|---------|
| `threaded_insert.py` | Ruthex RX / InsertEZ（FDM 热熔） | M2.5 – M5 | `make_threaded_insert(size)` |

---

## 3. 快速上手 · Quick Start

```python
from build123d_parts_lib.parts.fasteners.socket_head_screw import make_socket_head_screw
from build123d_parts_lib.parts.fasteners.screw_button_hex  import make_button_hex_screw
from build123d_parts_lib.parts.fasteners.nut_hex           import make_hex_nut
from build123d_parts_lib.parts.fasteners.nut_cap           import make_cap_nut
from build123d_parts_lib.parts.fasteners.nut_tslot         import make_tslot_nut
from build123d_parts_lib.parts.fasteners.washer            import make_washer
from build123d import export_step

# ISO 4762 内六角圆柱头螺丝
screw = make_socket_head_screw(size="M4", length=12)

# ISO 7380 内六角圆头螺丝（球冠头）
btn = make_button_hex_screw(size="M4", length=10)

# 六角螺母（ISO 4032 标准 / DIN 985 尼龙锁紧）
nut_std   = make_hex_nut(size="M4", standard="ISO4032")
nut_nyloc = make_hex_nut(size="M4", standard="DIN985")

# 盖形螺母
cap = make_cap_nut(size="M4")

# 2020 铝型材 T 型螺母
tnut = make_tslot_nut(size="M4")

# 平垫
washer = make_washer(size="M4", type_="flat")
```

几何约定（所有零件通用）：
- **原点**：零件底面几何中心
- **Z 轴**：轴向（螺杆方向 / 螺母高度方向）
- **默认单位**：毫米（mm）

---

## 4. 文件索引 · File Index

| 文件 | 职责 |
|------|------|
| `__init__.py` | 包入口（空） |
| `_thread_utils.py` | **共用**：`make_external_thread(d, pitch, length)` + `make_internal_thread(d, pitch, length)` — ISO 锯齿螺纹 revolve 几何 |
| `socket_head_screw.py` | ISO 4762 内六角圆柱头螺丝（头 + 内六角凹槽 + ISO 螺纹杆） |
| `countersunk_screw.py` | ISO 10642 内六角沉头螺丝（锥形头 + 内六角凹槽 + ISO 螺纹杆） |
| `screw_button_hex.py` | ISO 7380 内六角圆头螺丝（球冠头 + 内六角凹槽 + ISO 螺纹杆） |
| `screw_csk_phillips.py` | ISO 7046 十字沉头螺丝（锥形头 + 十字槽凹 + ISO 螺纹杆） |
| `screw_csk_slotted.py` | ISO 2009 一字沉头螺丝（锥形头 + 一字槽凹 + ISO 螺纹杆） |
| `screw_pan_phillips.py` | ISO 7045 十字圆盘头螺丝（盘形头 + 十字槽凹 + ISO 螺纹杆） |
| `screw_pan_slotted.py` | ISO 1580 一字圆盘头螺丝（盘形头 + 一字槽凹 + ISO 螺纹杆） |
| `hex_bolt.py` | DIN 933 外六角螺栓（六角头 + ISO 螺纹杆 + 杆端 45° 倒角） |
| `nut_hex.py` | 六角螺母：ISO 4032（标准）/ GB/T 6172（薄）/ DIN 985（尼龙锁紧，含顶部圆柱尼龙圈） |
| `nut_cap.py` | DIN 1587 盖形螺母（六角底 + 半球顶 dome + 盲孔内螺纹） |
| `nut_flange.py` | DIN 6923 法兰螺母（圆盘法兰底 + 六角柱体 + 贯通内螺纹） |
| `nut_wing.py` | DIN 315 蝶形螺母（圆柱轮毂 + 两侧翼片 + 圆角外端 + 贯通内螺纹） |
| `nut_square.py` | DIN 562 方形螺母（正方形棱柱 + 四棱竖边倒角 + 贯通内螺纹） |
| `nut_tslot.py` | 2020/3030 铝型材 T 型螺母（T 截面体：宽头 + 窄茎 + 贯通内螺纹） |
| `washer.py` | 垫圈：ISO 7089 平垫 / GB/T 93 弹垫（对角切口） |
| `threaded_insert.py` | FDM 热熔嵌件（阶梯外形 + 上段环形倒刺 + 内螺纹） |
| `fasteners.yaml` | 规格数据 + factory 注册表（数据源 + 置信度 + 生成路径） |
| `cache/` | `rebuild_cache.py` 生成的 STEP / PNG 产物 |

---

## 5. YAML schema · 规格数据格式

每个条目由顶级 `KEY:` 组织（例如 `M3_ISO4762`），字段分类：

```yaml
M3_ISO4762:
  aliases: [M3, m3, M3-DIN912, ...]            # 搜索别名
  standard: "ISO 4762 / DIN 912"               # 对应国际 / 国标
  type: hex-socket-head-cap-screw              # 类型 tag（区分 make 函数路由）

  thread:                                      # 螺纹几何
    d: 3.0                                     # 公称大径 mm
    pitch: 0.50                                # 粗牙螺距 mm
    unit: mm

  head:                                        # 头部几何（螺丝 / 螺栓）
    dk: 5.5                                    # 头外径
    k: 3.0                                     # 头高
    s: 2.5                                     # 内六角对边宽（或外六角对边宽）

  dimensions:                                  # 螺母 / 垫圈尺寸
    s: 5.5                                     # 对边宽 / across flats
    m: 2.4                                     # 螺母高度
    id: 3.2                                    # 垫圈内径
    od: 7.0                                    # 垫圈外径
    t:  0.5                                    # 垫圈厚度

  clearance_hole:                              # 过孔推荐
    close_fit:  3.2
    medium_fit: 3.4
    loose_fit:  3.6

  counterbore:                                 # 沉孔推荐（socket head only）
    diameter: 5.7
    depth:    3.2

  common_lengths_mm: [5, 6, 8, 10, 12, 16]     # 常用长度列表

  source:                                      # 数据来源（可追溯）
    primary: https://www.bossard.com
    confidence: 5                              # 1–5，5 = 最可靠
    last_verified: 2026-04-28

  factory:                                     # ★ 生成入口（rebuild_cache 读取）
    module: build123d_parts_lib.parts.fasteners.socket_head_screw
    fn: make_socket_head_screw
    args: {size: "M3", length: 10}
    cache: cache/m3_iso4762_L10.step

  notes: ISO 4762 M3 内六角螺丝；常用 3D 打印件装配规格。
```

> **factory 约定**：`rebuild_cache.py` 扫描所有 `.yaml`，遇到带 `factory.cache` 的条目即：`importlib.import_module(factory.module).<factory.fn>(**factory.args)` → `export_step(part, cache)`。

---

## 6. 缓存重建 · Cache Rebuild

脚本位置：[scripts/rebuild_cache.py](../../../../scripts/rebuild_cache.py)

```bash
cd /Users/liyijiang/work/build123d-parts-lib

# 全量重建 STEP
python3 scripts/rebuild_cache.py

# 按 key 过滤（大小写不敏感，支持部分匹配）
python3 scripts/rebuild_cache.py --filter M4            # 所有 M4 规格
python3 scripts/rebuild_cache.py --filter fasteners     # 只构建 fasteners 目录
python3 scripts/rebuild_cache.py --filter insert        # 只构建含 "insert" 的 key

# 生成预览 PNG grid（需 ocp_vscode 运行于 3939/4567）
python3 scripts/rebuild_cache.py --filter M4 --preview
```

输出：
- `cache/*.step` — 二进制 CAD 产物
- `cache/*.png` — 单零件预览（iso 视角）
- `preview_new.png` — 本次构建的 PIL 拼图 grid

---

## 7. 扩展指南 · Extending the Library

### 7.1 添加新规格（YAML-only）

如需在现有类型上新增规格（如给 `socket_head_screw` 加 M12），只需：

1. 在 `fasteners.yaml` 追加条目，复制 M10 模板
2. 在对应 `.py` 的 `_FALLBACK_SPECS` 可选追加后备数据
3. 运行 `rebuild_cache.py --filter M12`

`_load_specs()` 会自动从 YAML 合并数据；无需改 Python。

### 7.2 添加新类型（新 `.py` + YAML type）

需新增模块时（如 `set_screw.py`）：

1. 新建 `.py`，实现 `make_xxx(size, ...)` 函数（可复用 `_thread_utils`）
2. 模块末尾加 `__main__` 块，批量导出 `cache/`
3. 在 `fasteners.yaml` 添加条目，`factory.module` 指向新模块、`factory.fn` 指向入口函数、`type` 字段起唯一 tag
4. 单元测试：`python3 -m build123d_parts_lib.parts.fasteners.set_screw`

**共用工具**：
- 内 / 外螺纹 → `from ._thread_utils import make_external_thread, make_internal_thread`
- 六角外接圆半径 → `r = s / math.sqrt(3)`

---

## 8. 计划支持的类型（待补齐）· Planned Additions

以下类型在实际装配建模中较常见，尚未实现：

### 紧定螺丝 · Set Screws / Grub Screws

| 类型 | 标准 | 端部形式 |
|------|------|---------|
| 内六角紧定螺丝（平端） | ISO 4026 | 平头 |
| 内六角紧定螺丝（锥端） | ISO 4028 | 锥尖 |
| 内六角紧定螺丝（杯形端） | ISO 4029 | 杯形凹 |

> 常见于电机轴联轴器、皮带轮等轴孔固定场景，M3/M4/M5 高频使用。

### 六角铜柱隔离柱 · Hex Standoffs / Spacers

| 类型 | 说明 |
|------|------|
| 双通（内螺纹两端） | 用于 PCB 叠层、面板固定 |
| 单通（一端内螺纹 + 一端外螺纹） | 用于螺丝柱延伸 |

> 3D 打印 + PCB 装配中极高频使用（M3 铜柱 H=5/8/10/12mm）。

### 其他紧固件

| 类型 | 标准 | 说明 |
|------|------|------|
| 圆头方颈螺栓（马车螺栓） | DIN 603 | 圆头 + 方颈防转，木结构与型材连接 |
| 盲孔铆螺母（拉铆螺母） | — | 薄板件内螺纹，M3/M4 常用 |
| 弹簧销（卷销） | DIN 1481 | 轴向弹性定位销 |

---

## License

MIT. 数据源见各 YAML 条目 `source.primary`。
