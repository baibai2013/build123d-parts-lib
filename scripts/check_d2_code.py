"""D2 Gate: Factory code structure check.
D2 门控：工厂函数代码结构检查。

在 A3 代码编写之后、进入 A4 验证之前运行。
检查三个二元条件（全部 yes/no，不需要人来判断"可不可读"）：

  1. GEOMETRY_INVARIANTS 是否以 list 形式存在于模块顶层
  2. _assert_geometry_invariants 是否只是 for 循环（无 inline assert）
  3. _load_specs 中 fallback 计算是否有 warnings.warn

注意：若工厂函数无内部几何（纯外形件），条件 1/2 返回 SKIP（非 FAIL）。
条件 3 对所有有 _load_specs 的工厂函数有效。

用法 / Usage:
    python scripts/check_d2_code.py build123d_parts_lib/parts/bearings/ball_bearing.py

    # 扫描所有 factory py 文件
    python scripts/check_d2_code.py --all

退出码 / Exit codes:
    0 = PASS（或全 SKIP）
    1 = 任意 FAIL

License: MIT
"""
from __future__ import annotations

import ast
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTS_ROOT = REPO_ROOT / "build123d_parts_lib" / "parts"

# ── AST 检查函数 ──────────────────────────────────────────────────────────────

def _check_geometry_invariants(tree: ast.AST) -> tuple[str, str]:
    """
    检查 GEOMETRY_INVARIANTS 是否在模块顶层定义为 list。
    Returns: (status, message)  status = "PASS" | "FAIL" | "SKIP"
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not (isinstance(target, ast.Name) and target.id == "GEOMETRY_INVARIANTS"):
                continue
            if isinstance(node.value, ast.List):
                n_items = len(node.value.elts)
                return "PASS", f"GEOMETRY_INVARIANTS 是 list（{n_items} 条）✓"
            else:
                type_name = type(node.value).__name__
                return "FAIL", (
                    f"GEOMETRY_INVARIANTS 存在但类型是 {type_name}，"
                    "应为 list[tuple[str, Callable]]"
                )
    return "SKIP", "GEOMETRY_INVARIANTS 未定义（纯外形件可忽略）"


def _check_assert_fn(tree: ast.AST) -> tuple[str, str]:
    """
    检查 _assert_geometry_invariants 是否只包含 for 循环。
    Returns: (status, message)
    """
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef)
                and node.name == "_assert_geometry_invariants"):
            continue
        # 忽略 docstring
        body = [
            s for s in node.body
            if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))
        ]
        if len(body) == 1 and isinstance(body[0], ast.For):
            return "PASS", "_assert_geometry_invariants 只含 for 循环 ✓"
        inline_asserts = [s for s in body if isinstance(s, ast.Assert)]
        if inline_asserts:
            return "FAIL", (
                f"_assert_geometry_invariants 含 {len(inline_asserts)} 个 inline assert，"
                "绕过了 GEOMETRY_INVARIANTS 单一真相——请改为 for 循环"
            )
        return "FAIL", (
            f"_assert_geometry_invariants 结构异常（{len(body)} 条语句，非 for 循环）"
        )
    return "SKIP", "_assert_geometry_invariants 未定义（纯外形件可忽略）"


def _check_fallback_warning(source: str, tree: ast.AST) -> tuple[str, str]:
    """
    检查 _load_specs 中 fallback 计算路径是否有 warnings.warn。
    Returns: (status, message)
    """
    has_load_specs = any(
        isinstance(node, ast.FunctionDef) and node.name == "_load_specs"
        for node in ast.walk(tree)
    )
    if not has_load_specs:
        return "SKIP", "_load_specs 未找到（非标准件可忽略）"

    has_warn = "warnings.warn" in source
    # 探测常见的 fallback 计算模式
    fallback_patterns = ["_FALLBACK", "fallback", "* 0.", "ratio", "estimate"]
    has_fallback_code = any(p in source for p in fallback_patterns)

    if has_fallback_code and not has_warn:
        return "FAIL", (
            "检测到 fallback 计算逻辑但未发现 warnings.warn——"
            "内部几何字段缺失时必须打印 WARNING，不得静默降级"
        )
    if has_warn:
        return "PASS", "fallback 降级路径有 warnings.warn ✓"
    return "PASS", "_load_specs 存在，未发现 fallback 计算路径 ✓"


# ── 检查单文件 ────────────────────────────────────────────────────────────────

def check_file(py_path: Path) -> dict:
    source = py_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(py_path))
    except SyntaxError as e:
        return {
            "pass": False,
            "file": str(py_path),
            "checks": [("语法", "FAIL", f"语法解析失败: {e}")],
        }

    s1, m1 = _check_geometry_invariants(tree)
    s2, m2 = _check_assert_fn(tree)
    s3, m3 = _check_fallback_warning(source, tree)

    checks = [
        ("GEOMETRY_INVARIANTS 为 lambda list", s1, m1),
        ("_assert_geometry_invariants 为 for 循环", s2, m2),
        ("fallback 降级有 warnings.warn", s3, m3),
    ]
    # FAIL 时整体 FAIL；SKIP 不算 FAIL
    overall = all(s in ("PASS", "SKIP") for _, s, _ in checks)
    return {"pass": overall, "file": str(py_path.relative_to(REPO_ROOT)), "checks": checks}


def _print_result(result: dict) -> None:
    any_fail = not result["pass"]
    status = "FAIL" if any_fail else "PASS"
    print(f"\nD2 Gate [{status}] — {result['file']}")
    for name, s, msg in result["checks"]:
        icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "–"}.get(s, "?")
        print(f"  [{icon}] {name}: {msg}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="D2 Gate: factory code structure check")
    parser.add_argument("file", nargs="?", help="Factory Python 文件路径")
    parser.add_argument("--all", action="store_true", help="扫描 parts/ 下所有 factory .py")
    args = parser.parse_args()

    if args.all:
        py_files = sorted(PARTS_ROOT.rglob("*.py"))
        # 跳过 __init__ 和工具模块
        factory_files = [
            f for f in py_files
            if not f.name.startswith("_") and f.name != "__init__.py"
        ]
        any_fail = False
        for f in factory_files:
            result = check_file(f)
            _print_result(result)
            if not result["pass"]:
                any_fail = True
        sys.exit(1 if any_fail else 0)

    if not args.file:
        parser.error("请指定文件路径，或使用 --all 扫描全部")

    result = check_file(Path(args.file))
    _print_result(result)
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
