# tools/importers — 外部标准件库参数化导入工具

将外部 CAD 标准件库的参数数据转换为本库的 YAML + Python 格式。

详细方案见：[references/external-libs/import-plan.md](../../references/external-libs/import-plan.md)

---

## 子目录说明

| 目录 | 来源库 | 状态 |
|------|--------|------|
| `schema/` | 本库 YAML schema 定义 + 验证器 | ⬜ 待建 |
| `bolts/` | BOLTS 开源标准件库（MIT + CC-BY） | ⬜ 待建 |
| `bd_warehouse/` | bd_warehouse（Apache-2.0，build123d 原生） | ⬜ 待建 |
| `iso_standards/` | ISO/DIN/GB 标准文档数据表（O 型圈/直线轴承等） | ⬜ 待建 |
| `khk_gears/` | KHK Gears 目录（JIS B 1701 齿轮参数） | ⬜ 待建 |
| `output/` | 生成的 YAML 草稿（人工审核后移入 parts/） | ⬜ |

---

## 使用流程

```
外部数据源
    ↓ importers/<source>/<xxx>_to_yaml.py
output/<category>.yaml（草稿）
    ↓ schema/validate.py
parts/<category>/<name>.yaml（正式入库）
    ↓ 手工写 / 包装 factory 函数
parts/<category>/<name>.py
```

---

## 入库质量门槛

- `confidence ≥ 4`（来自标准文档或主流厂商 datasheet）
- `aliases` ≥ 3 种常见叫法
- `source.primary` 含有效 URL
- 体积/bbox 与标准文档偏差 < 5%
- `pytest tests/` 全绿后才可 commit
