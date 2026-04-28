# importers/bolts — BOLTS 标准件库导入

**来源**: https://github.com/boltsparts/BOLTS
**许可证**: MIT（代码） + CC-BY（数据） — 兼容本库 MIT

## 使用前准备

```bash
git clone https://github.com/boltsparts/BOLTS /tmp/BOLTS
```

## 可导入品类

| BOLTS 目录 | 本库目标 | 备注 |
|-----------|---------|------|
| `data/hex_socket_head.blt` | parts/fasteners/ | 验证/补全 M1-M20 |
| `data/hex_bolt.blt` | parts/fasteners/ | 验证 DIN 933 |
| `data/hex_nut.blt` | parts/fasteners/ | 验证 ISO 4032 |
| `data/washer.blt` | parts/fasteners/ | 验证 ISO 7089 |
| `data/extrusion.blt` | parts/extrusions/（新） | B type 铝型材 |

## 字段映射（BOLTS → 本库）

| BOLTS 字段 | 本库字段 | 备注 |
|-----------|---------|------|
| `id` | YAML key（大写） | |
| `names.name.nice` | aliases[0] | |
| `standards[].body` + `standards[].standard` | standard | |
| `parameters.tables` | dimensions | 按规格展开 |
| `source.url` | source.primary | |
| `source.description` | notes | |

## 脚本

```bash
python bolts_to_yaml.py /tmp/BOLTS/data/hex_socket_head.blt \
    --output ../../output/fasteners_bolts.yaml
python ../schema/validate.py ../../output/fasteners_bolts.yaml
```
