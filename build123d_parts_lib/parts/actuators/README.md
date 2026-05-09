# parts/actuators — QDD 谐波减速关节模组

**4010 外转子无刷电机 + 谐波减速器 一体化关节**，外径 Φ45 mm（电机段 Φ47.5 mm），轴向 45 mm，减速比 50:1。

---

## 文件清单

### 主体零件模块

| 文件 | Factory | 状态 | 说明 |
|------|---------|:----:|------|
| `housing_circular_spline.py` | `make_housing_circular_spline()` | ✅ | 主外壳 + 刚轮一体件，Φ45×30 mm，102 齿 m0.3，PA12/ASA |
| `flex_spline.py` | `make_flex_spline()` | ✅ | 柔轮，Φ32×20 mm，100 齿 m0.3，壁厚 1.2 mm，TPU 95A |
| `wave_generator_cam.py` | `make_wave_generator_cam()` | ✅ | 波发生器凸轮，椭圆 17×15.5×14 mm，SLA 树脂 |
| `output_flange.py` | `make_output_flange()` | ✅ | 输出法兰，Φ40×8 mm，6×M2 PCD34，PETG |
| `motor_endcap_front.py` | `make_motor_endcap_front()` | ✅ | 电机前端盖，Φ45×5 mm，Φ8 H7 轴承座，4×M3，PETG |
| `encoder_cover.py` | `make_encoder_cover()` | ✅ | 编码器后盖，Φ30×6 mm，磁钢盲孔 Φ6.2×3.5，PETG |
| `rotor_shaft.py` | `make_rotor_shaft()` | ✅ | 转子轴，Φ5 h6×45 mm，DIN 6885 键槽 2×1.0，精密磨削 |
| `motor_stator.py` | `make_motor_stator()` | ✅ | 定子铁芯，Φ40×10 mm，12 槽，yoke Φ28，穿轴孔 Φ14 |
| `motor_stator.py` | `make_stator_winding()` | ✅ | 铜线绕组，12 槽导体 + 24 端线圈弧段 |
| **`rotor_shell.py`** | `make_rotor_shell()` | ✅ | 外转子壳，Φ47.5×12 mm，壁厚 1.5 mm，14 个磁钢定位槽 |
| **`arc_magnet.py`** | `make_arc_magnet()` | ✅ | 弧形磁钢（单片），内 r=20.25 mm，t=2 mm，圆心角 23.1° |
| `motor_controller.py` | `make_motor_controller()` | ✅ | FOC 驱动板，Φ40×1.6 mm，6×MOSFET + MCU + 相线接口 |

### 装配 / 辅助文件

| 文件 | 说明 |
|------|------|
| `motor_rotor.py` | 转子总成 Compound：`make_motor_rotor()` = rotor_shell + 14×arc_magnet |
| `assembly.py` | 全模组装配体，加载 cache/ STEP 并定位 → `cache/assembly.step` |
| `exploded.py` | OCP Animation 爆炸展开，16 s 循环 |
| `validate_actuators.py` | 三层验证脚本（BRep + bbox + STEP 圆形比较） |
| `qdd_module_proxy.py` | M0 代理预览（占位体）|
| `verify_flex_spline_visual.py` | 柔轮目视验证脚本 |
| `verify_m23_m26_visual.py` | M2-3/M2-6 目视验证脚本 |

### 文档

| 文件 | 说明 |
|------|------|
| `BOM.md` | 完整物料清单（标准件 + 购买件 + 打印件） |
| `PLAN.md` | 建模计划表 + 里程碑进度（M0~M4 + E1~E3 + P1） |
| `README.md` | 本文件 |

---

## 模块依赖关系

```
arc_magnet.py          ← 磁钢尺寸常量（n_poles, magnet_inner_r, magnet_h …）
    ↑
rotor_shell.py         ← 从 arc_magnet 导入尺寸，切槽型与磁钢精确匹配
    ↑
motor_rotor.py         ← Compound(rotor_shell + 14×arc_magnet)
    ↑
assembly.py            ← 加载所有零件 STEP，定位装配
```

---

## 关键参数

| 参数 | 值 |
|------|----|
| 谐波减速比 | 50:1 |
| 柔轮齿数 | 100 |
| 刚轮齿数 | 102 |
| 齿模数 | 0.3 mm |
| 外径（壳体） | Φ45 mm |
| 电机段外径 | Φ47.5 mm（外转子超出 Φ45 约束，已确认） |
| 轴向总长 | 45 mm |
| 极数 | 14（7 对极） |
| 定子槽数 | 12（12N14P） |
| 气隙 | 0.25 mm |
| 输出轴承 | 7001C，Φ12×Φ28×8 mm（角接触球轴承） |
| 波发生器轴承 | TS17x23x3.5（薄截面深沟球轴承） |

---

## 弧形磁钢采购规格（淘宝）

> 关键词：**瓦形磁钢 无刷电机 钕铁硼**

| 参数 | 规格 |
|------|------|
| 形状 | 瓦形 / 弧形 (tile / arc) |
| 内径（ID） | **40.5 mm** |
| 外径（OD） | **44.5 mm** |
| 高度 | **10 mm** |
| 圆心角 | **23°**（或标注 23.1°，360/14×0.9） |
| 充磁方向 | **径向充磁**（radially magnetised） |
| 极性排列 | N/S 交替（alternate）× 14 片一套 |
| 材料牌号 | N38SH（推荐）或 N35~N45 |
| 数量 | **14 片** / 台 |

> **备注**：若供应商无 23° 现货，可接受 22°~24° 弧角，采购后用游标卡尺核查弦长（内弧弦长 ≈ 2×20.25×sin(11.57°) ≈ 8.12 mm）。

---

## 常用命令

```bash
# 验证所有 actuator 零件（三层）
python build123d_parts_lib/parts/actuators/validate_actuators.py

# 重建 actuators cache（STEP + PNG）
python scripts/build_cache.py --only actuators

# 重建单个零件 cache
python scripts/build_cache.py --only rotor_shell
python scripts/build_cache.py --only arc_magnet

# 直接运行单个零件脚本（Layer 0 快速验证）
python -m build123d_parts_lib.parts.actuators.arc_magnet
python -m build123d_parts_lib.parts.actuators.rotor_shell
python -m build123d_parts_lib.parts.actuators.motor_rotor

# 装配体预览（需 OCP vscode 运行）
python build123d_parts_lib/parts/actuators/assembly.py
```

---

## 轴向装配堆叠（Z 坐标）

```
z =  -8 ~  0  : output_flange          输出法兰
z =   0 ~  8  : angular_contact_bearing 主输出轴承 7001C
z =   0 ~ 30  : housing_circular_spline 主外壳/刚轮
z =   0 ~ 20  : flex_spline            柔轮
z =   3 ~ 17  : thin_section_bearing   波发生器轴承
z =   3 ~ 17  : wave_generator_cam     波发生器凸轮
z =  30 ~ 35  : motor_endcap_front     电机前端盖
z =  35 ~ 41  : encoder_cover          编码器后盖
z =   0 ~ 45  : rotor_shaft            转子轴（穿通）
z =  28 ~ 38  : motor_stator           4010 定子铁芯
z =  28 ~ 38  : motor_stator_winding   铜线绕组
z =  28 ~ 40  : rotor_shell            外转子壳（超出 Φ45 包络）
z =  28 ~ 38  : arc_magnet × 14        弧形磁钢阵列
z =  30 ~ 31.6: motor_controller       FOC 驱动板
```
