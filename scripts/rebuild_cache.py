#!/usr/bin/env python3
"""Regenerate all cache/*.step files from .py sources.

Run when：
- 库参数调整（比如 SG90_BODY_L 变了）
- CI 校验 cache 是否过期
- 首次 clone 后想重建所有 step

Usage:
    python3 scripts/rebuild_cache.py
    python3 scripts/rebuild_cache.py --verify-only  # 仅检查是否存在
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build123d import export_step

# 注册需要生成 cache 的零件
REGISTRY = [
    {
        "name": "sg90",
        "factory": "build123d_parts_lib.parts.servos.sg90:make_sg90",
        "cache_path": "build123d_parts_lib/parts/servos/cache/sg90.step",
        "args": {},
    },
    {
        "name": "m3_iso4762_L10",
        "factory": "build123d_parts_lib.parts.fasteners.m3_iso4762:make_m3_screw",
        "cache_path": "build123d_parts_lib/parts/fasteners/cache/m3_iso4762_L10.step",
        "args": {"length": 10},
    },
]


def load_factory(ref: str):
    """'module.path:func' → 调用对象。"""
    module_path, func_name = ref.split(":")
    mod = __import__(module_path, fromlist=[func_name])
    return getattr(mod, func_name)


def rebuild(verify_only: bool = False) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    failed = 0
    for item in REGISTRY:
        cache_path = repo_root / item["cache_path"]
        if verify_only:
            status = "✓" if cache_path.exists() else "✗ MISSING"
            print(f"  {status}  {item['name']:<20} → {item['cache_path']}")
            if not cache_path.exists():
                failed += 1
            continue

        # 生成
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            factory = load_factory(item["factory"])
            part = factory(**item["args"])
            export_step(part, str(cache_path))
            print(f"  ✓  {item['name']:<20} → {item['cache_path']} "
                  f"(volume={part.volume:.1f} mm³)")
        except Exception as e:
            print(f"  ✗  {item['name']:<20} FAILED: {e}")
            failed += 1
    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild all cache/*.step files")
    parser.add_argument("--verify-only", action="store_true",
                        help="仅检查 cache 是否存在，不重建")
    args = parser.parse_args(argv)

    print(f"{'Verifying' if args.verify_only else 'Rebuilding'} {len(REGISTRY)} cached parts...")
    print()
    failed = rebuild(verify_only=args.verify_only)
    print()
    if failed:
        print(f"⚠ {failed} failed")
        return 1
    print("✅ all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
