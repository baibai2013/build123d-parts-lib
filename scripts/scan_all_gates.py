"""scan_all_gates.py — D0 + D1 + D2 全量扫描。
周期性健康检查入口，每两周运行一次。

扫描内容：
  D0  所有 d0/*_ops.yaml 文件（操作序列文档完整性）
  D1  所有 YAML 规格文件中已知 slug 的内部几何字段（按 YAML_SCAN_MAP 配置）
  D2  所有 factory .py 文件的代码结构（GEOMETRY_INVARIANTS / assert / fallback warn）

用法 / Usage:
    python scripts/scan_all_gates.py          # 完整扫描，输出摘要
    python scripts/scan_all_gates.py --d0     # 只跑 D0
    python scripts/scan_all_gates.py --d1     # 只跑 D1
    python scripts/scan_all_gates.py --d2     # 只跑 D2
    python scripts/scan_all_gates.py --json   # 输出 JSON 结果（供 CI 集成）

退出码 / Exit codes:
    0 = 全部 PASS / SKIP
    1 = 任意 FAIL

License: MIT
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

PARTS_ROOT = REPO_ROOT / "build123d_parts_lib" / "parts"

# ── D1 扫描配置：(yaml_path, slug, sample_model) ─────────────────────────────
# 每次新增有内部几何的 slug 时，在此补充一行。
YAML_SCAN_MAP: list[tuple[str, str, str]] = [
    ("build123d_parts_lib/parts/bearings/bearings.yaml",    "ball_bearing",    "608ZZ"),
    ("build123d_parts_lib/parts/bearings/bearings.yaml",    "mr_bearing",      "MR63ZZ"),
    ("build123d_parts_lib/parts/bearings/bearings.yaml",    "flanged_bearing", "F688ZZ"),
    # 新增示例（取消注释并补充实际型号）：
    # ("build123d_parts_lib/parts/servos/servos.yaml",      "standard_servo",  "SG90"),
    # ("build123d_parts_lib/parts/transmission/gears.yaml", "spur_gear",       "M2Z20"),
]


# ── 导入子模块 ────────────────────────────────────────────────────────────────

from check_d0_ops  import validate_ops_file
from check_d1_yaml import check as d1_check
from check_d2_code import check_file as d2_check


# ── 运行各层 ──────────────────────────────────────────────────────────────────

def run_d0() -> list[dict]:
    results = []
    paths = sorted(PARTS_ROOT.glob("*/d0/*_ops.yaml"))
    for p in paths:
        r = validate_ops_file(p)
        r["gate"] = "D0"
        r["label"] = p.parent.parent.name + "/" + r.get("slug", p.stem)
        results.append(r)
    return results


def run_d1() -> list[dict]:
    results = []
    for yaml_rel, slug, model in YAML_SCAN_MAP:
        yaml_path = REPO_ROOT / yaml_rel
        cat_dir = yaml_path.parent
        contract_path = cat_dir / "contracts" / f"{slug}_contract.yaml"

        r = d1_check(
            yaml_path,
            slug,
            model,
            contract_path if contract_path.exists() else None,
        )
        r["gate"]  = "D1"
        r["label"] = f"{slug}/{model}"
        results.append(r)
    return results


def run_d2() -> list[dict]:
    py_files = sorted(PARTS_ROOT.rglob("*.py"))
    factory_files = [
        f for f in py_files
        if not f.name.startswith("_") and f.name != "__init__.py"
    ]
    results = []
    for f in factory_files:
        r = d2_check(f)
        r["gate"]  = "D2"
        r["label"] = str(Path(r["file"]))
        results.append(r)
    return results


# ── 输出 ──────────────────────────────────────────────────────────────────────

def _icon(passed: bool) -> str:
    return "✓" if passed else "✗"


def print_summary(all_results: list[dict]) -> None:
    gate_counts: dict[str, dict] = {}
    for r in all_results:
        gate = r["gate"]
        gate_counts.setdefault(gate, {"pass": 0, "fail": 0, "skip": 0})
        if r["pass"]:
            gate_counts[gate]["pass"] += 1
        else:
            gate_counts[gate]["fail"] += 1

    print("\n" + "=" * 60)
    print("  scan_all_gates — 健康检查摘要")
    print("=" * 60)
    for gate, counts in sorted(gate_counts.items()):
        total = counts["pass"] + counts["fail"]
        status = "PASS" if counts["fail"] == 0 else "FAIL"
        print(f"  [{status}] {gate}  {counts['pass']}/{total} 通过")
    print("=" * 60)

    # 打印所有 FAIL 条目
    fails = [r for r in all_results if not r["pass"]]
    if fails:
        print(f"\n  {len(fails)} 项需要修复：\n")
        for r in fails:
            print(f"  [{r['gate']} FAIL] {r['label']}")
            for issue in r.get("issues", []):
                print(f"    ✗ {issue}")
            for check in r.get("checks", []):
                if check[1] == "FAIL":
                    print(f"    ✗ {check[2]}")
    else:
        print("\n  所有检查通过 ✓")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="D0+D1+D2 全量健康检查")
    parser.add_argument("--d0",   action="store_true", help="只跑 D0")
    parser.add_argument("--d1",   action="store_true", help="只跑 D1")
    parser.add_argument("--d2",   action="store_true", help="只跑 D2")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    run_all = not (args.d0 or args.d1 or args.d2)

    all_results: list[dict] = []
    if run_all or args.d0:
        all_results += run_d0()
    if run_all or args.d1:
        all_results += run_d1()
    if run_all or args.d2:
        all_results += run_d2()

    if args.json:
        # JSON 输出中把 checks list 简化一下
        out = []
        for r in all_results:
            out.append({
                "gate":   r["gate"],
                "label":  r["label"],
                "pass":   r["pass"],
                "issues": r.get("issues", []) + [
                    c[2] for c in r.get("checks", []) if c[1] == "FAIL"
                ],
            })
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print_summary(all_results)

    any_fail = any(not r["pass"] for r in all_results)
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
