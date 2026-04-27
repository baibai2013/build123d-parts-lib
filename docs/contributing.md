# 贡献指引

> 加新零件/模块/模板的标准流程。保持一致性是库长期价值的关键。

---

## 1. 选类别

| 类别 | 放什么 | 不放什么 |
|------|--------|---------|
| `parts/` | 单个标准件的实体（SG90、M3 螺丝、608ZZ） | 多零件组合（→ modules） |
| `modules/` | 多零件组合（热压螺母柱、铰链） | 单零件（→ parts） |
| `generators/` | 参数化特征函数（散热孔、公差表查） | 完整零件（→ parts） |
| `templates/` | 整机/项目起手（SG90 支架、PCB 壳） | 通用组件（→ modules） |
| `materials/` | 数据文件（YAML），密度、公差 | 代码（→ generators） |

**决策树**：
- "这是一个独立零件吗？" → `parts/`
- "是多个零件组合成的单元吗？" → `modules/`
- "这是返回 Sketch/Part/数值的函数吗？" → `generators/`
- "用户填参数就得一个可用项目起手吗？" → `templates/`
- "纯数据无代码吗？" → `materials/`

---

## 2. 文件规范

### Python 文件头

```python
"""<一句话描述 + 参数来源>.

Source: <参数引用，若有>
License: MIT
"""
from __future__ import annotations

from build123d import ...
```

### Factory 函数约定

```python
def make_<name>(
    param1: float = <default>,
    param2: float = <default>,
) -> Part:
    """<一句话功能>.

    Args:
        param1: <含义 + 单位 + 默认值理由>
        ...

    几何：
        - 原点在哪
        - +X/+Y/+Z 方向对应什么
    """
    # 参数检查（可选）
    if param1 <= 0:
        raise ValueError(...)

    with BuildPart() as p:
        # 实现...

    return p.part


if __name__ == "__main__":
    # 可运行 entry：生成 cache STEP
    from build123d import export_step
    p = make_<name>()
    export_step(p, "/tmp/<name>.step")
    print(f"OK: volume={p.volume:.1f} mm³")
```

---

## 3. 添加测试

每个新 `.py` 对应 `tests/test_<category>.py` 里加：

```python
def test_<name>_default():
    p = make_<name>()
    assert p.is_valid
    bb = p.bounding_box().size
    # 合理尺寸断言
    assert abs(bb.X - expected_x) < tolerance
```

**烟测试要求（MVP 标准）**：
- 能 import
- 默认参数能 build 出有效 BRep
- bbox 在合理范围
- 参数校验（预期抛 ValueError 的情况 `pytest.raises`）

---

## 4. Cache 文件

parts/ 下每个零件生成一个默认参数的 `cache/*.step`：

1. 在 `scripts/rebuild_cache.py` 的 `REGISTRY` 注册新条目
2. 运行 `python3 scripts/rebuild_cache.py` 生成
3. commit 时把 cache/ 下的 .step 一起提交（双存策略）

---

## 5. 文档更新

- `docs/parts-index.md`：表格中加一行
- `CHANGELOG.md`：在 Unreleased 或下一版本号下加 `### Added`
- 若加了新**类别**：同步更新 `README.md` 的类别表

---

## 6. 来源与 License 注意

**借鉴外部代码时**，在文件头或函数前明确标注：

```python
# 参考：gumyr/bd_warehouse@a1b2c3d gears.py#L45-89 (Apache-2.0)
```

**禁止借鉴**：
- 未标 License 的代码
- GPL/AGPL/LGPL 代码（传染性，本库 MIT 不兼容）
- 商业/专有代码

**允许借鉴**：
- MIT / BSD / Apache-2.0 / Unlicense / CC0
- 标明来源 + commit + 文件 + 行号

---

## 7. 与 build123d-cad skill 的集成

若新零件对应 skill 的 `data-sources/*.yaml` 条目，**建议同步改 skill**：

```yaml
# build123d-cad/references/data-sources/servos.yaml
<YOUR_PART>:
  ...
  parts_lib:                              # ★ 新增
    module: build123d_parts_lib.<category>.<name>
    factory: make_<name>
    cache_step: <category>/<name>/cache/<name>.step
```

这样 AI 用 `spec_lookup.py` 查该零件时会自动看到实体入口。

---

## 8. PR checklist

- [ ] 选对了类别
- [ ] 文件头 docstring 含 License + Source
- [ ] Factory 函数命名为 `make_<snake_case>`
- [ ] 参数有 type hints + 默认值
- [ ] `if __name__ == "__main__":` 能跑通
- [ ] `tests/test_<cat>.py` 加了对应测试
- [ ] `pytest tests/` 全绿
- [ ] `docs/parts-index.md` 更新
- [ ] `CHANGELOG.md` 更新
- [ ] 若借鉴外部代码，标注了来源和 License
