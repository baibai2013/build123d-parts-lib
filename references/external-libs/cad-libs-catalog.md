# CAD 外部标准件库资源总目录

> 搜集时间：2026-04-28
> 目的：评估可转为参数化 YAML + Python 的外部数据源，供 `tools/importers/` 参考

---

## 一、在线零件库平台（免费注册/下载）

| 名称 | 简介 | 地址 |
|------|------|------|
| TraceParts | 1亿+零件，70+CAD格式，ISO/DIN/JIS/ANSI | https://www.traceparts.com |
| GrabCAD Library | 社区共享，300万+模型，STEP/IGES/DWG | https://grabcad.com/library |
| PARTcommunity (CADENAS) | 600+厂商目录，150+CAD格式，含AutoCAD直连插件 | https://b2b.partcommunity.com |
| parts.cadenas.de | CADENAS 直接搜索下载入口 | https://parts.cadenas.de |
| 3D ContentCentral | SolidWorks 官方平台，180万+免费模型 | https://www.3dcontentcentral.com |
| McMaster-Carr | 工业供应商，所有产品直接提供STEP/DXF，**无需账号** | https://www.mcmaster.com |
| MISUMI USA | 2000万+可配置件，STEP/IGES 即时生成 | https://us.misumi-ec.com/vona2/cad/ |
| MISUMI Europe | MISUMI 欧洲站 | https://eu.misumi-ec.com/vona2/cad/ |

---

## 二、AutoCAD 官方/商业插件

| 名称 | 简介 | 地址 |
|------|------|------|
| AutoCAD Mechanical Toolset | 订阅内含，700,000+标准件，ISO/DIN/ANSI/JIS/GB | https://www.autodesk.com/products/autocad/included-toolsets/autocad-mechanical |
| Autodesk Content Center | Inventor 专属，900,000+标准件 | https://www.autodesk.com/products/inventor/content-center |
| Autodesk App Store | 官方插件市场 | https://apps.autodesk.com |
| Nuts & Bolts 3D | AutoCAD 内参数化螺母/螺栓插件 | https://apps.autodesk.com/ACD/en/Detail/Index?id=appstore.exchange.autodesk.com%3Anutsandbolts3d |
| CADBlocksFree | 免费AutoCAD块库，含管件/结构钢/标准件 | https://www.cadblocksfree.com |

---

## 三、开源参数化零件库（GitHub）

### build123d / CadQuery 系（⭐ 许可证兼容 Apache-2.0）

| 名称 | 简介 | 地址 |
|------|------|------|
| bd_warehouse | **build123d 官方**标准件库（螺栓/轴承/齿轮等） | https://github.com/gumyr/bd_warehouse |
| build123d | Python 参数化 CAD 框架本体（OCCT 内核） | https://github.com/gumyr/build123d |
| cq-warehouse | CadQuery 版标准件库（同作者） | https://github.com/gumyr/cq-warehouse |
| cq-parts | CadQuery 机械零件库框架 | https://github.com/fragmuffin/cq-parts |
| cq-kit | CadQuery 扩展工具库（型材/紧固件/硬件件） | https://github.com/michaelgale/cq-kit |
| cadquery-contrib | CadQuery 社区脚本/模型仓库 | https://github.com/CadQuery/cadquery-contrib |

### BOLTS 系（⭐ 多平台，许可证兼容 MIT/CC-BY）

| 名称 | 简介 | 地址 |
|------|------|------|
| BOLTS | 开源标准件库，支持FreeCAD/OpenSCAD/Blender，含ISO/DIN | https://github.com/boltsparts/BOLTS |
| BOLTS 官网 | 文档与下载 | https://boltsparts.github.io |

### OpenSCAD 系（⚠️ 注意 GPL 许可）

| 名称 | 简介 | 地址 |
|------|------|------|
| MCAD | OpenSCAD 官方元库（螺栓/齿轮/马达等） | https://github.com/openscad/MCAD |
| NopSCADlib | 面向3D打印的大型硬件库（电子件/紧固件） | https://github.com/nophead/NopSCADlib |
| threadlib | 精准螺纹建模库（Metric/UNC/UNF） | https://github.com/adrianschlatter/threadlib |
| OpenSCAD-fasteners | 参数化紧固件库，多种头型 | https://github.com/More-Wrong/OpenSCAD-fasteners |

---

## 四、FreeCAD 零件库与插件

| 名称 | 简介 | 地址 |
|------|------|------|
| FreeCAD-library | 官方社区零件库（紧固件/电子元件/型材） | https://github.com/FreeCAD/FreeCAD-library |
| Fasteners Workbench | ISO/DIN/EN/ASME 紧固件，参数化自动匹配孔径 | https://github.com/shaise/FreeCAD_FastenersWB |
| FCGear Workbench | 渐开线/斜齿/锥齿/蜗轮/链轮参数化生成 | https://github.com/looooo/freecad.gears |
| FreeCAD-addons | 所有插件索引仓库 | https://github.com/FreeCAD/FreeCAD-addons |
| FreeCAD Wiki — Parts Library | 安装说明 | https://wiki.freecad.org/Parts_Library |
| FreeCAD Wiki — Fasteners | 完整紧固件类型文档 | https://wiki.freecad.org/Fasteners_Workbench |
| FreeCAD Wiki — FCGear | 齿轮参数文档 | https://wiki.freecad.org/FCGear_Workbench |

---

## 五、品牌厂商官方 CAD 数据（精确工业模型）

| 名称 | 简介 | 地址 |
|------|------|------|
| SKF 轴承 | 官方STEP/DXF/DWG，全产品线 | https://www.skf.com |
| NSK 轴承 | 全系列STEP格式免费下载 | https://www.nsk.com |
| FAG/Schaeffler | 官方精确3D模型，STEP/DXF | https://www.schaeffler.com |
| KHK Gears（小原齿车工业） | 按模数/齿数参数化选择，STEP+DXF 免费 | https://khkgears.net |
| Würth 紧固件 | DIN/ISO 官方精确模型，STEP/IGES/DXF | https://www.wuerth-industrie.com/web/en/wuerthindustrie/cad_daten/cad_daten.php |

---

## 六、中文/国内资源

| 名称 | 简介 | 地址 |
|------|------|------|
| 沐风网 | 国内最大机械CAD图库，GB标准件DWG，免费 | https://www.mfcad.com/tuzhi/jixiezero/ |
| CAD之家 | GB+ISO标准件图块，紧固件/轴承/齿轮 | https://www.cadhome.com.cn/cad_detail_list_78.html |
| 中望CAD标准件图库 | GB 标准螺钉/销/键/弹簧 AutoCAD 图块 | https://www.zwsoft.cn/news/cadjiaocheng/biaozhunjian-tukuDaQ.html |
| 土木在线机械标准件 | 国标紧固件/轴承/联轴器二维CAD图块 | https://down.co188.com/cad/jixie/biaozhunjian/ |

---

## 七、GitHub Topic 入口

- https://github.com/topics/parametric-cad — 参数化CAD相关仓库汇总
- https://github.com/topics/build123d — build123d 相关仓库汇总
