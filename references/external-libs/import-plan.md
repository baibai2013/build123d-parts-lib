# 外部标准件库参数化导入方案

> 版本：v1.0 · 2026-04-28
> 目标：为 `tools/importers/` 建立系统化的外部数据源 → YAML + Python 转换管道，
> 标准：工业级精度（confidence ≥ 4）、许可证兼容（MIT/BSD/Apache-2.0 only）、详细参数。

---

## 一、候选库评估矩阵

| 库 | 许可证 | 数据格式 | 标准体系 | 参数完整度 | 自动化难度 | 综合评级 |
|----|--------|----------|----------|------------|------------|----------|
| **BOLTS** | MIT + CC-BY ✅ | YAML + JSON | ISO/DIN/ANSI/JIS/BSI | ★★★★★ | 低（直接解析） | **S** |
| **bd_warehouse** | Apache-2.0 ✅ | Python NamedTuple | ANSI/ISO | ★★★★☆ | 中（解析 Python） | **A** |
| **ISO/DIN 标准文档** | 数据公知 ✅ | PDF/表格 | ISO/DIN/GB | ★★★★★ | 高（手工） | **A** |
| **KHK Gears 目录** | 产品公知 ✅ | HTML/PDF | JIS B 1701 | ★★★★★ | 中（爬取/解析） | **A** |
| **SKF/NSK 轴承手册** | 产品公知 ✅ | PDF/HTML | ISO 15/ABEC | ★★★★★ | 中（已部分完成） | **B** |
| **McMaster-Carr** | 产品公知 ✅ | 网页/STEP | ANSI/ASME | ★★★★☆ | 中（爬取） | **B** |
| **MISUMI** | 产品公知 ✅ | 网页 API | ISO/DIN/JIS/GB | ★★★★★ | 中（API） | **B** |
| **FreeCAD FastenersWB** | LGPL-2.1 ❌ | Python | ISO/DIN/EN/ASME | ★★★★★ | 低 | **淘汰（许可证）** |
| **NopSCADlib** | GPL ❌ | OpenSCAD | — | ★★★☆☆ | — | **淘汰（许可证）** |
| **MCAD (OpenSCAD)** | GPL ❌ | OpenSCAD | — | ★★★☆☆ | — | **淘汰（许可证）** |

---

## 二、推荐选用库与理由

### S 级：BOLTS（首选，最高优先）

**GitHub**: https://github.com/boltsparts/BOLTS
**许可证**: MIT（代码） + CC-BY（数据）→ 完全兼容

**理由**：
- 数据已是 YAML，字段结构与本库非常接近，可用脚本直接转换
- 覆盖 ISO 4762 / DIN 912 / ISO 4032 / DIN 934 / ISO 7089 / 铝型材（B type）等
- 每个 spec 含 `dimensions`、`standard`、`source` — 与本库 schema 对齐
- 不需要爬取网页，直接 clone 仓库解析

**可转换的品类**：
| BOLTS 类别 | 本库目标路径 | 状态 |
|------------|-------------|------|
| 内六角螺丝 ISO 4762 | parts/fasteners/socket_head_screw.py | P0 已完成，用于补全 M1/M12+ |
| 外六角螺栓 ISO 4017 | parts/fasteners/hex_bolt.py | P1 已完成，用于验证 |
| 六角螺母 ISO 4032 | parts/fasteners/nut_hex.py | 已完成，用于验证 |
| 平垫圈 ISO 7089 | parts/fasteners/washer.py | 已完成，用于验证 |
| 铝型材 B type (20x20 etc) | parts/extrusions/（新增） | **P2 新品类** |
| 管接头 / 管螺纹 | parts/fittings/（新增） | **P2 新品类** |

---

### A 级：bd_warehouse（build123d 原生，第二优先）

**GitHub**: https://github.com/gumyr/bd_warehouse
**许可证**: Apache-2.0 → 兼容

**理由**：
- 同为 build123d 生态，可以**直接包装**而非重写
- 含 Nut、Bolt、Washer、Bearing（含锥形滚子）、Gear 等族
- 参数来源是 ANSI/ISO 标准，数据质量高
- 最大价值：**齿轮（Gear）和锥形轴承（TaperRollerBearing）** — 本库暂缺

**处理策略**：不完全转换，而是：
1. 在本库 YAML 中注明 `upstream: bd_warehouse`
2. Python factory 函数包装 `bd_warehouse.XXX`，保持接口一致
3. 只在需要解耦时才独立实现几何

**可引入品类**：
| bd_warehouse 类别 | 本库目标 | 优先级 |
|-------------------|---------|--------|
| `Nut` 族 | 验证/补全 | 已有，用于核对 |
| `TaperRollerBearing` | parts/bearings/taper_roller_bearing.py | P1-3 |
| `AngularContactBearing` | parts/bearings/angular_contact_bearing.py | P1-3 |
| `NeedleBearing` | parts/bearings/needle_bearing.py | P1-3 |
| `Gear` (spur/helical) | parts/gears/spur_gear.py | P2-2 |

---

### A 级：ISO/DIN 标准文档（最高精度，手工提取）

**来源**：
- ISO 标准：https://www.iso.org/（部分免费预览）
- GB 标准：https://openstd.samr.gov.cn/（国内免费）
- DIN 标准：各参考手册

**适用场景**：P1-4 密封件、P1-5 直线轴承 — 这些 bd_warehouse/BOLTS 均不覆盖

| 标准号 | 品类 | 目标文件 |
|--------|------|---------|
| ISO 3601-1 / GB/T 3452.1 | O 型圈（公制） | parts/seals/oring.py |
| GB/T 13871 | 旋转轴唇形密封（油封） | parts/seals/oil_seal.py |
| ISO 10736 / JIS B 2403 | 推力球轴承 | parts/bearings/thrust_bearing.py |
| ISO 3245 / JIS B 2604 | 直线轴承 LM 系列 | parts/bearings/linear_bushing.py |

---

### A 级：KHK Gears 目录（齿轮专项，工业级）

**官网**: https://khkgears.net
**许可证**: 目录参数为公开产品数据，可参考

**理由**：
- KHK 是日本最大标准齿轮厂商，参数来源 JIS B 1701（齿轮国际标准）
- 网站按模数/齿数/材质/精度等级提供 STEP + DXF 下载
- 齿轮几何公式是标准公开知识，不存在许可证问题

**可转换品类**：
| 类别 | 标准 | 规格范围 | 目标文件 |
|------|------|---------|---------|
| 直齿圆柱齿轮（Spur） | JIS B 1701 | 模数 0.5~3，Z 10~100 | parts/gears/spur_gear.py |
| 斜齿圆柱齿轮（Helical） | JIS B 1701 | 模数 1~2，β 15°/20° | parts/gears/helical_gear.py |
| 直锥齿轮（Bevel） | JIS B 1701 | 模数 1/1.5/2，1:1/2:1 | parts/gears/bevel_gear.py |
| 蜗轮蜗杆（Worm/Worm Gear） | JIS B 1704 | 模数 1/1.5/2 | parts/gears/worm_gear.py |
| 齿条（Rack） | JIS B 1701 | 模数 1/2，标准长度 | parts/gears/rack.py |

---

## 三、新品类优先级（补充 P1 + P2）

基于路线图，以下是需要新建 YAML + Python 的品类，按优先级排序：

### P1 补齐（M4 里程碑）

| 优先级 | 品类 | 数据来源 | 新建文件 |
|--------|------|---------|---------|
| 🔴 P1-3a | 推力球轴承 F8-16M / F10-18M | ISO 10736 / NSK | bearings/thrust_bearing.py + thrust_bearing.yaml |
| 🔴 P1-3b | 角接触球轴承 7001/7002 | ISO 15 / SKF | bearings/angular_contact_bearing.py + .yaml |
| 🔴 P1-3c | 滚针轴承 HK0608/0808/1010 | ISO 3245 / INA | bearings/needle_bearing.py + .yaml |
| 🟡 P1-4a | O 型圈（公制）ID 3~30mm | GB/T 3452.1 / ISO 3601 | seals/oring.py + oring.yaml |
| 🟡 P1-4b | 旋转轴油封 TC 型 D8~20 | GB/T 13871 | seals/oil_seal.py + oil_seal.yaml |
| 🟡 P1-5a | 直线轴承 LM6UU~LM12UU | MISUMI LMUU / ISO | bearings/linear_bushing.py + .yaml |
| 🟡 P1-5b | 法兰直线轴承 LMF8UU/10UU | MISUMI LMFUU | 同上（合并到 linear_bushing.py） |
| 🟡 P1-5c | 滑动轴套 ⌀3~⌀10 | MISUMI SGLF | bearings/plain_bushing.py + .yaml |

### P2 扩展（M5+ 按需）

| 优先级 | 品类 | 数据来源 | 新建文件 |
|--------|------|---------|---------|
| ⬜ P2-1a | MGN 直线导轨 MGN7/9/12/15 | 厂商 datasheet | linear/mgn_rail.py + .yaml |
| ⬜ P2-1b | 联轴器 D5-5/D8-8/弹性 | MISUMI / 标准 | linear/coupling.py + .yaml |
| ⬜ P2-2a | 直齿圆柱齿轮 m0.5~m3 | JIS B 1701 / KHK | gears/spur_gear.py + .yaml |
| ⬜ P2-2b | 锥齿轮 1:1/2:1 | JIS B 1701 / KHK | gears/bevel_gear.py + .yaml |
| ⬜ P2-2c | 蜗轮蜗杆 m1/m2 | JIS B 1704 / KHK | gears/worm_gear.py + .yaml |
| ⬜ P2-3a | 步进电机 NEMA14/17/23 | NEMA 标准 / datasheet | motors/stepper_nema.py + .yaml |
| ⬜ P2-3b | 无刷电机 2204/2812/4108 | 厂商 datasheet | motors/bldc_motor.py + .yaml |
| ⬜ P2-4 | 铝型材 20x20/30x30/40x40 | BOLTS B-type / Misumi | extrusions/aluminum_extrusion.py + .yaml |

---

## 四、tools/importers/ 目录结构

```
tools/
└── importers/
    ├── README.md                        # 工具说明
    ├── schema/
    │   ├── part_schema.yaml             # 本库 YAML schema 完整定义
    │   └── validate.py                  # schema 验证器（pydantic）
    ├── bolts/
    │   ├── README.md                    # BOLTS 导入说明
    │   ├── bolts_to_yaml.py             # BOLTS YAML → 本库 YAML 映射脚本
    │   └── field_map.yaml               # 字段名称映射表
    ├── bd_warehouse/
    │   ├── README.md
    │   ├── bdw_scan.py                  # 扫描 bd_warehouse 可用品类
    │   └── bdw_wrap_template.py         # 包装 bd_warehouse 的 factory 模板
    ├── iso_standards/
    │   ├── README.md
    │   ├── oring_iso3601.yaml           # O 型圈 ISO 3601 原始数据表
    │   ├── lm_bearing_misumi.yaml       # LM 直线轴承 MISUMI 数据表
    │   └── extract_to_schema.py         # 原始数据 → 本库 YAML
    ├── khk_gears/
    │   ├── README.md
    │   ├── gear_formulas.py             # 渐开线齿轮几何公式（公知）
    │   ├── spur_gear_params.yaml        # 直齿轮规格表（从 KHK 目录提取）
    │   └── khk_to_yaml.py              # 转换脚本
    └── output/                          # 生成的 YAML 草稿（需人工审核后移入 parts/）
        └── .gitkeep
```

---

## 五、YAML Schema 规范（本库标准）

转换所有外部数据时，必须满足以下字段：

```yaml
<PART_ID>:
  aliases: [...]                    # 必填：3种以上常见叫法
  standard: "ISO XXXX / DIN XXX"   # 必填：标准号
  type: <snake-case-type>           # 必填：零件类型
  
  # 几何参数（必填，依类型选填）
  dimensions:
    <key>: <float>                  # 所有尺寸，mm
    unit: mm
  
  # 来源（必填）
  source:
    primary: <URL>                  # 标准文档或厂商官网
    confidence: <1-5>               # 5=标准文档，4=厂商datasheet，3=行业习惯
    last_verified: <YYYY-MM-DD>
  
  # 工厂函数（必填）
  factory:
    module: build123d_parts_lib.parts.<category>.<file>
    fn: make_<name>
    args: {<key>: <value>}
    cache: cache/<name>.step
  
  # 可选扩展
  weight_g: <float>
  fit:                              # 装配配合尺寸
    <key>: <float>
  notes: <一句中文说明>
```

**confidence 评级标准**：

| 分值 | 来源 |
|------|------|
| 5 | ISO / GB / DIN / JIS / ANSI 标准文档原文 |
| 4 | 主流厂商 datasheet（SKF / NSK / Bossard / Misumi） |
| 3 | 行业惯例 / 多厂商一致 |
| 2 | 实测/样品测量 |
| 1 | 估算/非正式来源 |

**最低入库标准：confidence ≥ 4**

---

## 六、许可证合规矩阵

| 外部库 | 许可证 | 代码可借用 | 数据可借用 | 操作 |
|--------|--------|-----------|-----------|------|
| BOLTS | MIT + CC-BY | ✅ | ✅ | 标注来源即可 |
| bd_warehouse | Apache-2.0 | ✅ | ✅ | 标注来源 + commit |
| ISO/DIN 标准文档 | 数据公知 | N/A | ✅ | 标注标准号 |
| KHK Gears 目录 | 产品公知 | N/A | ✅ | 标注来源 URL |
| SKF/NSK 手册 | 产品公知 | N/A | ✅ | 标注来源 URL |
| McMaster-Carr | 产品公知 | N/A | ✅ | 标注来源 URL |
| MISUMI | 产品公知 | N/A | ✅ | 标注来源 URL |
| FreeCAD FastenersWB | LGPL-2.1 | ❌ | ❌（关联） | 禁止 |
| NopSCADlib | GPL-3.0 | ❌ | ❌ | 禁止 |
| MCAD (OpenSCAD) | LGPL | ❌ | ❌ | 禁止 |

---

## 七、实施节奏建议

| 阶段 | 内容 | 工具 | 预期产出 |
|------|------|------|---------|
| **M4-A** | schema 验证器 + BOLTS 导入脚本 | `tools/importers/bolts/` | P1-3 轴承扩展 YAML |
| **M4-B** | ISO 数据表 → O 型圈 + 油封 YAML | `tools/importers/iso_standards/` | P1-4 密封件 |
| **M4-C** | MISUMI 直线轴承数据 → YAML | `tools/importers/iso_standards/` | P1-5 直线系统 |
| **M5-A** | KHK 齿轮公式 + 规格表 | `tools/importers/khk_gears/` | P2-2 齿轮族 |
| **M5-B** | bd_warehouse 包装 | `tools/importers/bd_warehouse/` | P2-3 电机族 |
| **M5-C** | BOLTS 铝型材导入 | `tools/importers/bolts/` | P2-4 铝型材 |

---

## 八、参考链接

| 资源 | 地址 |
|------|------|
| BOLTS GitHub | https://github.com/boltsparts/BOLTS |
| bd_warehouse GitHub | https://github.com/gumyr/bd_warehouse |
| KHK Gears 在线选型 | https://khkgears.net |
| SKF 轴承 CAD 数据 | https://www.skf.com |
| NSK 轴承手册 | https://www.nsk.com |
| ISO 标准在线查阅 | https://www.iso.org |
| GB 标准在线查阅 | https://openstd.samr.gov.cn |
| MISUMI CAD 库 | https://us.misumi-ec.com/vona2/cad/ |
| McMaster-Carr | https://www.mcmaster.com |
| FreeCAD FCGear（参考公式） | https://github.com/looooo/freecad.gears |
