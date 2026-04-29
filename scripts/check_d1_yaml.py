"""D1 Gate: YAML data completeness check.
D1 门控：YAML 数据完整性检查。

在 A1.4 草稿 YAML 确认之后、进入 A2 之前运行。
检查 YAML 中是否有足够的字段来支撑 contract 里的每一条 geometry_invariants.expr。

核心问题：contract expr 里引用的每个 g['key']，
         在 YAML 中都有对应的源数据字段吗？

用法 / Usage:
    python scripts/check_d1_yaml.py --yaml parts/bearings/bearings.yaml \\
        --slug ball_bearing --model 608ZZ \\
        --contract parts/bearings/contracts/ball_bearing_contract.yaml

    # 不指定 contract（仅查必要字段清单）
    python scripts/check_d1_yaml.py --yaml parts/bearings/bearings.yaml \\
        --slug ball_bearing --model 608ZZ

退出码 / Exit codes:
    0 = PASS
    1 = FAIL（有缺失字段）

License: MIT
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

# ── 每类 slug 必须在 YAML 里提供的内部几何字段（来自 A1.3.1 表）──────────────

REQUIRED_GEOMETRY_FIELDS: dict[str, list[str]] = {
    "ball_bearing":    ["d_ball_mm", "n_balls"],
    "mr_bearing":      ["d_ball_mm", "n_balls"],
    "flanged_bearing": ["d_ball_mm", "n_balls"],
    "linear_bushing":  ["ball_dia_mm", "n_circuit"],
    "standard_servo":  ["output_shaft_d"],          # shaft_spline_teeth 可选
    "spur_gear":       ["m", "z", "pressure_angle_deg"],
    "timing_pulley":   ["teeth", "pitch_mm", "belt_width_mm"],
}

# ── 从 contract 提取 g-dict key ───────────────────────────────────────────────

def _g_keys_from_contract(contract_path: Path) -> set[str]:
    """从 contract YAML geometry_invariants 提取所有 g['key'] 引用。"""
    if not contract_path or not contract_path.exists():
        return set()
    doc = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    exprs = " ".join(
        inv.get("expr", "")
        for inv in doc.get("geometry_invariants", [])
    )
    return set(re.findall(r"g\['(\w+)'\]", exprs))


# ── 主检查函数 ────────────────────────────────────────────────────────────────

def check(yaml_path: Path, slug: str, model: str,
          contract_path: Path | None = None) -> dict:
    """
    Returns:
        pass   — bool
        issues — list[str]
        warns  — list[str]  (confidence 低或 [unverified] 标注)
    """
    issues: list[str] = []
    warns:  list[str] = []

    # 读 YAML
    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return {"pass": False, "issues": [f"YAML 解析失败: {e}"], "warns": []}

    if model not in data:
        return {
            "pass": False,
            "issues": [f"型号 '{model}' 不在 {yaml_path.name} 中"],
            "warns": [],
        }

    entry = data[model]

    # 1. confidence 检查
    confidence = (entry.get("source") or {}).get("confidence", 0)
    if confidence < 4:
        warns.append(
            f"source.confidence={confidence}（< 4），来源可靠性不足；"
            "建议补充 ISO/制造商文档"
        )

    # 2. [unverified] 检查
    notes = str(entry.get("notes", ""))
    geometry_raw = str(entry.get("geometry", ""))
    if "[unverified]" in notes or "[unverified]" in geometry_raw:
        warns.append("存在 [unverified] 标注，入库前需核实")

    # 3. 必要内部几何字段检查（来自 REQUIRED_GEOMETRY_FIELDS 表）
    required = REQUIRED_GEOMETRY_FIELDS.get(slug, [])
    geometry = entry.get("geometry") or {}
    for field in required:
        if field not in geometry:
            issues.append(
                f"[MISSING] geometry.{field}  "
                f"— {slug} 的 geometry_invariants 需要此字段"
            )
        elif str(geometry[field]).startswith("<"):
            issues.append(
                f"[PLACEHOLDER] geometry.{field} = '{geometry[field]}'  "
                "— 仍是模板占位符，未填实际值"
            )

    # 4. contract g-dict key 覆盖检查（如果提供了 contract）
    if contract_path:
        g_keys = _g_keys_from_contract(contract_path)
        if g_keys:
            # 这是启发式检查：g-dict key 通常与 geometry 字段同名或可由其计算
            # 只报告与 YAML geometry 字段完全不相关的 key（人工确认）
            geometry_keys = set(geometry.keys()) | set(entry.keys())
            unknown_g_keys = {
                k for k in g_keys
                # g-dict key 由工厂函数计算，不一定直接在 YAML 中
                # 只警告不在任何 YAML 字段中出现的 key
                if k not in geometry_keys and k not in str(entry)
            }
            if unknown_g_keys:
                warns.append(
                    f"contract expr 引用了以下 g-dict key，"
                    f"未能在 YAML 中找到对应字段（可能是工厂函数内部计算量，需人工确认）: "
                    f"{sorted(unknown_g_keys)}"
                )

    return {"pass": len(issues) == 0, "issues": issues, "warns": warns}


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="D1 Gate: YAML data completeness")
    parser.add_argument("--yaml",     required=True, help="YAML 规格文件路径")
    parser.add_argument("--slug",     required=True, help="Factory slug, e.g. ball_bearing")
    parser.add_argument("--model",    required=True, help="型号 key, e.g. 608ZZ")
    parser.add_argument("--contract", help="contract YAML 路径（可选，用于 g-dict key 覆盖检查）")
    args = parser.parse_args()

    yaml_path     = Path(args.yaml)
    contract_path = Path(args.contract) if args.contract else None

    result = check(yaml_path, args.slug, args.model, contract_path)
    status = "PASS" if result["pass"] else "FAIL"

    print(f"\nD1 Gate [{status}] — {args.slug} / {args.model}")

    for issue in result["issues"]:
        print(f"  ✗ {issue}")
    for warn in result["warns"]:
        print(f"  ⚠ {warn}")

    if result["pass"] and not result["warns"]:
        print("  所有必要字段存在，confidence 充足，可进入 A2")
    elif result["pass"]:
        print("  字段完整（有警告，建议处理后再进入 A2）")

    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
