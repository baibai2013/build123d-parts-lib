"""D0 Gate: Operation sequence documentation check.
D0 门控：建模操作序列文档检查。

在 A1.0 四问法之后、进入 A2 之前运行。
检查 parts/<cat>/d0/<slug>_ops.yaml 是否存在且结构完整。

约定：每个有非平凡内部几何的 slug 必须有一个操作序列文件。
该文件记录"机械师操作序列"，是 geometry_invariants 的来源依据。

用法 / Usage:
    # 初始化模板（首次使用）
    python scripts/check_d0_ops.py --slug ball_bearing --category bearings --init

    # 验证已有文件
    python scripts/check_d0_ops.py --slug ball_bearing --category bearings

    # 扫描所有已有 d0 文件
    python scripts/check_d0_ops.py --all

退出码 / Exit codes:
    0 = PASS
    1 = FAIL 或文件缺失（--init 时输出模板并返回 1）

License: MIT
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTS_ROOT = REPO_ROOT / "build123d_parts_lib" / "parts"

# 每个 slug 的最少操作步数（少于此数视为未认真填写）
MIN_STEPS: dict[str, int] = {
    "ball_bearing": 5,
    "mr_bearing": 5,
    "flanged_bearing": 5,
    "linear_bushing": 4,
    "standard_servo": 3,
    "spur_gear": 4,
    "timing_pulley": 3,
}
DEFAULT_MIN_STEPS = 3

# ── 模板 ──────────────────────────────────────────────────────────────────────

_TEMPLATE = """\
# D0 操作序列文档 — {slug}
# 用机械师语言描述建模步骤，布尔减料从序列里自然浮现。
# 每个 requires 条目对应一个 geometry_invariants.expr 里的约束。

slug: {slug}
part_class: <填写零件类型，例: deep-groove-ball-bearing>

operations:
  - step: 1
    action: "<取外形毛坯，例: 取外径圆柱>"
    requires: null          # 无可达条件

  - step: 2
    action: "<车/铣第一个内部特征，例: 车内孔>"
    requires:
      dim: "<对应 g-dict key，例: r_outer_inner>"
      reachability: "<可达条件，例: 车刀直径 < 内孔直径>"

  - step: 3
    action: "<减料特征，例: 磨滚道沟槽>"
    requires:
      dim: "<g-dict key，例: r_groove>"
      reachability: "<可达条件，例: 砂轮半径 < 沟槽管半径>"

  # 继续补充步骤……

# 从上述序列推导出的 geometry_invariants（填写后复制到 contract.yaml）：
# - description: "<可达条件描述>"
#   expr: "g['<dim>'] <运算符> <阈值表达式>"
"""


# ── 验证逻辑 ──────────────────────────────────────────────────────────────────

def _d0_path(category: str, slug: str) -> Path:
    return PARTS_ROOT / category / "d0" / f"{slug}_ops.yaml"


def _find_d0_path(slug: str) -> Path | None:
    """在所有 category 下查找 slug 的 d0 文件。"""
    for cat_dir in PARTS_ROOT.iterdir():
        if not cat_dir.is_dir():
            continue
        p = cat_dir / "d0" / f"{slug}_ops.yaml"
        if p.exists():
            return p
    return None


def validate_ops_file(path: Path) -> dict:
    """验证操作序列文件结构是否完整。"""
    issues = []
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return {"pass": False, "issues": [f"YAML 解析失败: {e}"]}

    if not doc:
        return {"pass": False, "issues": ["文件为空或只有注释"]}

    slug = doc.get("slug", "")
    if not slug:
        issues.append("缺少 slug 字段")

    if not doc.get("part_class") or "<" in str(doc.get("part_class", "")):
        issues.append("part_class 未填写（仍是模板占位符）")

    ops = doc.get("operations", [])
    if not ops:
        issues.append("operations 列表为空")
    else:
        min_steps = MIN_STEPS.get(slug, DEFAULT_MIN_STEPS)
        if len(ops) < min_steps:
            issues.append(
                f"operations 只有 {len(ops)} 步，{slug} 要求至少 {min_steps} 步"
            )

        # 检查是否有任意一步填写了 requires（减料可达条件）
        steps_with_requires = [
            op for op in ops
            if op.get("requires") and not str(op.get("requires")).startswith("<")
        ]
        if not steps_with_requires:
            issues.append(
                "没有任何步骤填写了 requires（减料可达条件）——操作序列不完整"
            )

        # 检查是否有模板占位符未替换
        for op in ops:
            action = str(op.get("action", ""))
            if "<" in action:
                issues.append(
                    f"step {op.get('step', '?')}: action 仍是模板占位符，请替换"
                )
                break

    return {"pass": len(issues) == 0, "slug": slug, "path": str(path), "issues": issues}


# ── 初始化模板 ────────────────────────────────────────────────────────────────

def init_template(category: str, slug: str) -> Path:
    out = _d0_path(category, slug)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        print(f"  已存在，跳过覆盖: {out}")
    else:
        out.write_text(_TEMPLATE.format(slug=slug), encoding="utf-8")
        print(f"  模板已生成: {out}")
        print("  → 用编辑器填写操作序列，完成后重新运行此脚本验证。")
    return out


# ── 主逻辑 ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="D0 Gate: operation sequence check")
    parser.add_argument("--slug", help="Factory slug (e.g. ball_bearing)")
    parser.add_argument("--category", help="Parts category (e.g. bearings)")
    parser.add_argument("--init", action="store_true",
                        help="生成空白模板（文件不存在时）")
    parser.add_argument("--all", action="store_true",
                        help="扫描所有已有的 d0 文件")
    args = parser.parse_args()

    if args.all:
        paths = sorted(PARTS_ROOT.glob("*/d0/*_ops.yaml"))
        if not paths:
            print("未找到任何 d0 文件（运行 --init 创建模板）")
            sys.exit(0)
        any_fail = False
        for p in paths:
            result = validate_ops_file(p)
            status = "PASS" if result["pass"] else "FAIL"
            print(f"  [D0 {status}] {p.parent.parent.name}/{result.get('slug', p.stem)}")
            for issue in result["issues"]:
                print(f"    ✗ {issue}")
            if not result["pass"]:
                any_fail = True
        sys.exit(1 if any_fail else 0)

    if not args.slug:
        parser.error("--slug 必须指定（或使用 --all 扫描全部）")

    if args.init:
        if not args.category:
            parser.error("--init 需要同时指定 --category")
        init_template(args.category, args.slug)
        path = _d0_path(args.category, args.slug)
        # 初始化后尝试验证
        result = validate_ops_file(path)
        if not result["pass"]:
            sys.exit(1)   # 模板未填写时正常 FAIL，提示用户填写
        sys.exit(0)

    # 普通验证模式
    path = _find_d0_path(args.slug)
    if path is None:
        print(f"\nD0 Gate [FAIL] — {args.slug}")
        print(f"  ✗ d0 文件不存在")
        print(f"  → 运行: python scripts/check_d0_ops.py --slug {args.slug} --category <cat> --init")
        sys.exit(1)

    result = validate_ops_file(path)
    status = "PASS" if result["pass"] else "FAIL"
    print(f"\nD0 Gate [{status}] — {args.slug}")
    print(f"  文件: {path}")
    for issue in result["issues"]:
        print(f"  ✗ {issue}")
    if result["pass"]:
        print("  操作序列文档完整，可进入 A2")
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
