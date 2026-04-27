# 标准件参数化路线图（Parts Roadmap）

> 从 **SolidWorks Toolbox** / **ISO/GB 标准** / **厂商 datasheet** 三类源头出发，
> 按机器人 + 机电项目的使用频率，分 P0/P1/P2 逐步参数化到 parts-lib。

---

## 🎯 设计原则

1. **同一标准族共享 `.py`**：一个文件 + `NamedTuple` 规格表，参数化所有规格
   - ✅ `socket_head_screw.py` → M2/M2.5/M3/M4/M5 共用
   - ✅ `mr_bearing.py` → MR63/74/84/85/104 共用
   - ❌ 避免 `m3_iso4762.py` + `m4_iso4762.py` 分开

2. **YAML 与 Python 同目录**：每个 `parts/<category>/` 内一个 `<category>.yaml`
3. **SW Toolbox 路径标注**：便于用户在 SW 中对照查验
4. **建模保留装配关键特征**：安装孔、配合面、公差槽；不建螺纹、齿形等细节
5. **cache STEP 按需生成**：运行 `python xxx.py` 即生成

### 状态图例

| 标记 | 含义 |
|------|------|
| ✅ | 已完成 |
| 🟡 | 进行中 / 部分完成 |
| ⬜ | 计划中 |
| 🚫 | 暂不做（原因见 notes） |

---

## 📦 当前快照（2026-04-27）

| 类别 | 规格数 | 文件 |
|------|--------|------|
| 螺丝 (Socket Head) | 5 | `parts/fasteners/socket_head_screw.py` |
| 深沟球轴承 | 4 | （skill data-sources，未建 py） |
| MR 微型轴承 | 5 | `parts/bearings/mr_bearing.py` |
| 圆柱销 | 4 | `parts/pins/pin_cylindrical.py` |
| 舵机 | 1 | `parts/servos/sg90.py`（MG90S 共用） |

---

## 🔴 P0：刚性需求（机器狗/机电项目必备）  ✅ **已全部完成（2026-04-27）**

**完成 P0 后，90% 的机器人 MVP 项目不再缺标准件。**

### P0-1 紧固件补完 ✅

| 条目 | 规格清单 | 实现文件 | 状态 |
|------|----------|---------|------|
| **内六角圆柱头螺丝** | M2 / M2.5 / M3 / M4 / M5 | `socket_head_screw.py` | ✅ |
| **内六角沉头螺丝** | M2 / M2.5 / M3 / M4 / M5 | `countersunk_screw.py` | ✅ |
| **六角标准/薄/尼龙锁** | M2-M5（ISO4032 / GB6172 / DIN985） | `nut_hex.py` | ✅ |
| **平垫圈 + 弹簧垫圈** | 平垫 M2-M5 / 弹簧 M3-M5 | `washer.py` | ✅ |
| **热压铜螺母** | M2.5×4 / M3×5 / M4×6 / M5×8 | `threaded_insert.py` | ✅ |

### P0-2 轴承补完 ✅

| 条目 | 规格清单 | 实现文件 | 状态 |
|------|----------|---------|------|
| **深沟球轴承（通用）** | 608 / 624 / 625 / 626 / 6000 / 6001-2RS / 6002 | `ball_bearing.py` | ✅ |
| **MR 微型轴承** | MR63 / 74 / 84 / 85 / 104 | `mr_bearing.py` | ✅ |
| **法兰微型轴承** | F688 / F693 / F623 / F624 / F625 / F684 | `flanged_bearing.py` | ✅ |

### P0-3 销与轴 ✅

| 条目 | 规格清单 | 实现文件 | 状态 |
|------|----------|---------|------|
| **圆柱销（淬硬）** | D3 / D4 / D5 / D6（GB/T 119.1） | `pin_cylindrical.py` | ✅ |
| **开口销** | D1.5 / D2 / D2.5 / D3（ISO 1234） | `pin_split.py` | ✅ |
| **弹性圆柱销** | D3 / D4 / D5 / D6（ISO 8752） | `pin_spring.py` | ✅ |
| **精密光轴** | D4 / D5 / D6 / D8（MISUMI PSFJ） | `shaft_smooth.py` | ✅ |

### P0-4 舵机补完 ✅

| 条目 | 规格 | 实现文件 | 状态 |
|------|------|---------|------|
| **标准舵机壳（覆盖 9g + 40 系）** | SG90 / MG90S / MG996R / DS3218 | `standard_servo.py` | ✅ |
| **舵机摇臂（horn）** | single / double / cross / disc（25T） | `servo_horn.py` | ✅ |

**P0 成果汇总**：16 个 factory `.py` · 80+ 规格 · 64 个 cache STEP · 60+ YAML 条目。

---

## 🟡 P1：常用扩展（一半以上项目会用）

**P0 之后，补齐这些能覆盖 95% 机电设计场景。**

### P1-1 传动件

| 条目 | 规格清单 | 实现文件 | 状态 |
|------|----------|---------|------|
| **同步带轮 GT2** | 16T / 20T / 30T / 40T × ⌀5 / ⌀8 孔 | `transmission/timing_pulley_gt2.py` | ✅ |
| **同步带 GT2** | L110 / L158 / L200 / L280 / L380 | `transmission/timing_belt_gt2.py` | ✅ |
| **轴用卡簧** | D4 / D5 / D6 / D8 / D10 / D12 | `retainers/retaining_ring_shaft.py` | ✅ |
| **孔用卡簧** | D8 / D10 / D12 / D16 / D20 / D25 | `retainers/retaining_ring_hole.py` | ✅ |
| **平键** | 3×3 / 4×4 / 5×5 / 6×6 / 8×7（ISO 2491） | `transmission/key_parallel.py` | ✅ |

### P1-2 大规格紧固件 ✅

| 条目 | 规格 | 实现 | 状态 |
|------|------|------|------|
| **内六角螺丝 M6/M8/M10** | 扩展现有 socket_head_screw.py | `fasteners/socket_head_screw.py` | ✅ |
| **六角螺母 M6/M8/M10** | 三标准（ISO4032 / GB6172 / DIN985） | `fasteners/nut_hex.py` | ✅ |
| **外六角螺栓 M4~M10** | DIN 933 全螺纹 | `fasteners/hex_bolt.py` | ✅ |

### P1-3 轴承扩展

| 条目 | 规格 | 备注 |
|------|------|------|
| **推力球轴承** | F8-16M / F10-18M | `thrust_bearing.py` |
| **角接触球轴承** | 7000 系列（7001/7002） | `angular_contact_bearing.py` |
| **滚针轴承** | HK0608 / HK0808 / HK1010 | `needle_bearing.py` |

### P1-4 密封件

| 条目 | 规格 | 来源 |
|------|------|------|
| **O 型圈（公制）** | 内径 3~30mm ×线径 1.5 / 2 / 2.5 | `GB/T 3452.1` |
| **油封** | TC 型 D8~20 | `GB/T 13871` |

> `oring.py` 单文件参数化所有内径+线径；`oil_seal.py` 同理。

### P1-5 滑动件

| 条目 | 规格 | 备注 |
|------|------|------|
| **直线轴承** | LM6UU / LM8UU / LM10UU / LM12UU | `linear_bushing.py` |
| **法兰直线轴承** | LMF8UU / LMF10UU | 同上 |
| **滑动轴套（铜/聚合物）** | ⌀3~⌀10，长 5/8/10mm | `plain_bushing.py` |

---

## 🟢 P2：专项扩展（特定项目才用）

**P0+P1 之后仍未覆盖的，按项目需求临时补充。**

### P2-1 直线系统

| 条目 | 规格 | 备注 |
|------|------|------|
| **MGN 直线导轨** | MGN7 / MGN9 / MGN12 / MGN15 | 含 C/H 滑块两型 |
| **SBR/SHF 光轴支座** | SHF8 / SHF10 / SHF12 | 配 D8~D12 光轴 |
| **T 型丝杠** | T8×2 / T8×8，L100~500 | 梯形螺纹 |
| **滚珠丝杠 + 螺母** | SFU1204 / SFU1605 / SFU2005 | 含 BK/BF 支撑座 |
| **联轴器** | 刚性 D5-5 / D8-8；弹性 D5-8 / D8-10 | `coupling.py` |

### P2-2 齿轮

| 条目 | 规格 | 备注 |
|------|------|------|
| **直齿圆柱齿轮** | 模数 0.5 / 1 / 1.5 / 2，齿数 10~60 | 已有 `08_gear_spur_v2.py` 可推广 |
| **锥齿轮** | 1:1 / 2:1 / 3:1，模数 1/1.5 | 复杂，查外部库 |
| **蜗轮蜗杆** | 模数 1 / 2 | 复杂，查外部库 |
| **行星齿轮组** | 参数化（太阳/行星/内齿圈） | 高级模板 |

### P2-3 电机

| 条目 | 规格 | 备注 |
|------|------|------|
| **步进电机** | NEMA14 / NEMA17 / NEMA23 | 壳体 + 法兰 + 轴，不含线圈 |
| **BLDC 电机** | 2204 / 2812 / 4108（无人机/机器狗常用） | 壳体 + 轴伸 |
| **减速电机** | GA12-N20 / GM25-370 | 含减速箱外形 |

### P2-4 连杆/关节

| 条目 | 规格 | 备注 |
|------|------|------|
| **杆端关节轴承** | SA5T / SA6T / SA8T（米制螺纹） | `rod_end.py` |
| **万向节** | D6×L10 / D8×L16 | `universal_joint.py` |
| **球头拉杆** | M3/M4 两端球头 | 四足韧带/推杆 |

### P2-5 气动/液压（暂低优先）

| 条目 | 规格 | 备注 |
|------|------|------|
| **气缸（标准 ISO 15552）** | ⌀16 / ⌀20 / ⌀25 | 大体积，外形占位即可 |
| **快插接头** | PC4-M5 / PC6-01 | 3D 打印机常用 |

---

## 🛠 SW Toolbox 导出实践

从 SW Toolbox 提取参数的标准流程（供开发者参照）：

```
SW Toolbox → 选定标准族 → 选规格  → 右键 "Create Part"
         → 另存 STEP → 用以下方法提取参数：

1. 直接读 STEP：bounding box + 关键特征半径（不够精确）
2. 查 ISO/GB 标准文档：获取权威数值（推荐）
3. Toolbox XML 配置文件：C:\SOLIDWORKS Data\browser\...（批量提取）
```

**推荐优先级**：ISO/GB 标准文档 > 厂商 datasheet > Toolbox 实测 > 其它

---

## 📝 提交新标准件检查清单

给每个 PR / commit 使用：

- [ ] 参数来源（ISO 标准号 / GB 标准号 / 厂商 URL）已在 YAML `source.primary` 中标注
- [ ] `confidence` 已评估（5=标准文档，4=厂商 datasheet，3=行业习惯，2=实测，1=估算）
- [ ] 同族规格用同一 `.py` 文件 + `NamedTuple` 表（不允许 5 个规格 5 个文件）
- [ ] `aliases` 涵盖 3 种以上常见叫法（大小写/连字符/缩写）
- [ ] Factory 函数有默认参数，`__main__` 直接跑能生成所有规格的 cache STEP
- [ ] `docs/parts-index.md` 已更新对应行
- [ ] 体积/bbox 与标准文档或 datasheet 对比偏差 < 5%

---

## 🎯 里程碑节奏建议

| 阶段 | 目标 | 状态 |
|------|------|------|
| **M1** | P0-1 + P0-2（螺母/垫片/深沟轴承 py） | ✅ 2026-04-27（subagent 并行） |
| **M2** | P0-3 + P0-4（开口销/大舵机/摇臂） | ✅ 2026-04-27（subagent 并行） |
| **M3** | P1-1 + P1-2（GT2 + 卡簧 + 平键 + M6-M10 + DIN 933） | ✅ 2026-04-27（subagent 并行 + 预览图系统） |
| **M4** | P1-3 + P1-4 + P1-5（轴承扩展 + 密封 + 直线轴承） | ⬜ 2 周 |
| **M5+** | P2 按项目需求逐条触发 | ⬜ 按需 |

---

## 📚 参考源

- SolidWorks Toolbox 标准库路径：`C:\SOLIDWORKS Data\browser\`
- 中国国家标准文档：[GB 在线查阅](https://openstd.samr.gov.cn/)
- ISO 标准：[iso.org](https://www.iso.org/)
- 轴承厂商：SKF / NSK / NMB / Boca Bearings
- 紧固件厂商：Bossard / Fastenal / MonotaRO
- 机器人电子元件：Servodatabase / ServoDB / Pololu
- 标准件超市：[Misumi](https://www.misumi-china.com.cn/)（详图+STEP 下载）

---

> 🤝 **贡献方式**：在 PR 中按"提交检查清单"全部勾选，并更新本文件相应条目的状态标记。
