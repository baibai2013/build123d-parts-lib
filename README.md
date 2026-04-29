# build123d-parts-lib

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![build123d](https://img.shields.io/badge/build123d-0.10+-green)](https://github.com/gumyr/build123d)

> **Reusable CAD parts for [build123d](https://github.com/gumyr/build123d) projects** — 标准件实体、功能模块、生成器函数、项目模板、材料元数据，长期累积，跨项目复用。

配套 [build123d-cad skill](https://github.com/baibai2013/build123d-cad) 使用；参数体系由 skill 的 `data-sources/*.yaml` 维护，本库负责**可 import 的 CAD 代码**。

---

## 安装

**方式一：submodule + editable install（推荐）**

```bash
cd my-project
git submodule add https://github.com/baibai2013/build123d-parts-lib.git lib/parts-lib
pip install -e lib/parts-lib
```

**方式二：独立 clone + editable install**

```bash
git clone https://github.com/baibai2013/build123d-parts-lib.git
pip install -e build123d-parts-lib
```

---

## 快速上手

```python
# 1. 直接用零件实体
from build123d_parts_lib.parts.servos.sg90 import make_sg90
servo = make_sg90()

# 2. 功能模块（多零件组合）
from build123d_parts_lib.modules.threaded_insert_boss import make_m3_boss
boss = make_m3_boss(insert_length=5, height=8)

# 3. 生成器函数（参数化特征）
from build123d_parts_lib.generators.clearance import get_clearance_diameter
d = get_clearance_diameter("M3", "medium")   # → 3.4 mm (FDM 推荐)

# 4. 项目模板（填参数起项目）
from build123d_parts_lib.templates.sg90_bracket import make_sg90_bracket
bracket = make_sg90_bracket(wall_thickness=2.5, print_clearance=0.3)

# 5. 元数据（密度 / 公差）
import yaml, importlib.resources as r
densities = yaml.safe_load(
    r.files("build123d_parts_lib.materials").joinpath("densities.yaml").read_text()
)
mass_g = servo.volume / 1000 * densities["plastics"]["PLA"]
```

---

## 5 大类内容

### 📦 A. `parts/` — 标准件实体

完整 3D 实体，可直接调用 factory 函数或 `import_step()`。

> **完整零件清单**：见 **[docs/parts-index.md](docs/parts-index.md)**（含每类预览图、Factory 签名、覆盖规格）。

当前覆盖 7 大类、38 个 factory 文件、200+ 参数化规格：

| 类别 | 代表零件 | 模块前缀 |
|------|---------|---------|
| 🔩 Fasteners（紧固件） | 内六角/沉头/圆头/十字螺丝、六角/法兰/蝶形螺母、弹簧垫 · 铜柱 · 拉铆螺母… | `parts.fasteners` |
| ⚙️ Bearings（轴承） | 深沟球轴承 / MR 微型 / 法兰 / 直线轴承 LM series | `parts.bearings` |
| 📍 Pins & Shafts（销轴） | 圆柱销 / 开口销 / 弹性销 / 光轴 | `parts.pins` |
| 🤖 Servos（舵机） | SG90 / MG90S / MG996R / DS3218 + 舵盘 | `parts.servos` |
| ⚙️ Transmission（传动） | GT2 皮带轮 / 皮带 / 平行键 | `parts.transmission` |
| 🔘 Retainers（卡簧） | 轴用 / 孔用弹性挡圈 | `parts.retainers` |
| 🔵 Seals（密封） | O 型圈（ISO 3601-1 / GB/T 3452.1） | `parts.seals` |

> **紧固件几何简化说明**：本库所有紧固件（螺栓、螺钉等）均采用**光杆**表示，不建模真实螺纹。
> YAML 中保留 `pitch` 参数供螺纹孔计算用，装配仿真精度足够。
> 如需带螺纹的标准 STEP 文件，可从以下来源下载：
>
> | 平台 | 地址 | 说明 |
> |------|------|------|
> | McMaster-Carr | [mcmaster.com](https://www.mcmaster.com) | 质量最高，带真实螺纹，推荐首选 |
> | TraceParts | [traceparts.com](https://www.traceparts.com) | 注册免费，规格最全 |
> | PARTcommunity | [partcommunity.com](https://partcommunity.com) | 免费，多格式支持 |
> | 3DFindit | [3dfindit.com](https://www.3dfindit.com) | 聚合多厂商含 Bossard |

### 🔧 B. `modules/` — 功能模块

多零件组合，覆盖高频装配场景。

| 模块 | 入口 | 用途 |
|------|------|------|
| 热压铜螺母柱 | `modules.threaded_insert_boss:make_m3_boss` | FDM 打印件螺丝固定标配 |
| FDM 卡扣 | `modules.snap_fit_latch:make_snap_latch` | 盖板/壳体免螺丝固定 |

### 🎨 C. `generators/` — 生成器函数

参数化特征，返回 Sketch/Part/数值。

| 生成器 | 入口 | 输出 |
|--------|------|------|
| 散热孔阵列 | `generators.vents:make_vent_pattern` | Sketch |
| 螺丝通孔直径 | `generators.clearance:get_clearance_diameter` | float |

### 🏗 D. `templates/` — 项目模板

填几个参数就得可用零件，新项目 0→1 的起点。

| 模板 | 入口 | 场景 |
|------|------|------|
| SG90 安装座 | `templates.sg90_bracket:make_sg90_bracket` | 舵机安装 |
| PCB 外壳 | `templates.pcb_enclosure:make_pcb_enclosure` | 电子产品开壳 |

### 🧪 E. `materials/` — 工程元数据

YAML 格式，查表用。

| 文件 | 内容 |
|------|------|
| `materials/densities.yaml` | 材料密度（PLA/ABS/铝/钢/…） |
| `materials/fits.yaml` | ISO 公差配合 + 3D 打印经验间隙 |

---

## 和 build123d-cad skill 的集成

skill 侧的 `data-sources/*.yaml` 维护**参数数据**（SG90 尺寸、M3 规格）；本库维护**可 import 的 CAD 代码**。两者通过 YAML 里的 `parts_lib:` 字段关联：

```yaml
# skill 的 data-sources/servos.yaml
SG90:
  body: {length: 22.8, ...}
  parts_lib:
    module: build123d_parts_lib.parts.servos.sg90
    factory: make_sg90
    cache_step: cache/sg90.step
```

`spec_lookup.py` 命中 SG90 时会额外打印 parts-lib 入口，AI 便知道"参数来自 YAML，实体用 parts-lib"。

---

## 开发与贡献

### 运行测试

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

### 重建 cache STEP 文件

改了零件源码后：

```bash
python scripts/build_cache.py                        # 重建 bundle 全部代表规格
python scripts/build_cache.py --only bearings        # 只重建指定类别
python scripts/build_cache.py --only ball_bearing --model 6000ZZ  # 导出指定型号
python scripts/verify_cache.py                       # 验证 cache 与 factory 一致性
python scripts/verify_cache.py --only bearings       # 只验证指定类别
```

### 加新零件（贡献指引）

见 [docs/contributing.md](docs/contributing.md)。

核心规则：
- 按类别放入 `parts/` / `modules/` / `generators/` / `templates/` / `materials/`
- 文件头 docstring 必带：License、Source、参数说明
- 新 `.py` 必带对应 `tests/test_*.py` 烟测试
- 公开 repo 来源的代码必须带 `# 参考：repo@commit file#L... (License)`

---

## 版本策略

[语义版本](https://semver.org/)。本库处于 `0.x`，API 可能不稳定。稳定后进 `1.0`。

历史：见 [CHANGELOG.md](CHANGELOG.md)。

---

## License

MIT — 见 [LICENSE](LICENSE)。
