#!/usr/bin/env python3
"""Regenerate all cache/*.step files from YAML factory entries.
从 YAML factory 条目自动重建所有 cache/*.step 文件。

Auto-discovers all parts registered in YAML files under build123d_parts_lib/parts/
自动发现 build123d_parts_lib/parts/ 下所有 YAML 文件中注册的零件。

Usage:
    python3 scripts/rebuild_cache.py
    python3 scripts/rebuild_cache.py --verify-only
    python3 scripts/rebuild_cache.py --filter bearings
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

import yaml
from build123d import export_step

REPO_ROOT = Path(__file__).resolve().parents[1]
PARTS_DIR = REPO_ROOT / "build123d_parts_lib" / "parts"


def discover_parts(filter_cat: str | None = None) -> list[dict]:
    """Auto-discover all parts from YAML factory entries.
    自动从 YAML factory 条目发现所有零件。
    """
    parts = []
    for yaml_file in sorted(PARTS_DIR.rglob("*.yaml")):
        # skip files in cache subdirectory
        if "cache" in yaml_file.parts:
            continue
        try:
            raw = yaml.safe_load(yaml_file.read_text())
        except Exception:
            continue
        if not isinstance(raw, dict):
            continue
        for key, entry in raw.items():
            if not isinstance(entry, dict):
                continue
            factory = entry.get("factory")
            if not factory:
                continue
            cache_rel = factory.get("cache", "")
            if not cache_rel:
                continue
            if filter_cat and filter_cat not in str(yaml_file):
                continue
            parts.append({
                "name": key,
                "module": factory["module"],
                "fn": factory["fn"],
                "args": factory.get("args", {}),
                "cache_path": yaml_file.parent / cache_rel,
            })
    return parts


def rebuild(verify_only: bool = False, filter_cat: str | None = None) -> int:
    """Rebuild or verify cache files.
    重建或验证缓存文件。
    """
    parts = discover_parts(filter_cat)
    print(f"Discovered {len(parts)} parts")
    failed = 0

    for item in parts:
        cache_path = item["cache_path"]
        if verify_only:
            status = "✓" if cache_path.exists() else "✗ MISSING"
            print(f"  {status}  {item['name']:<24} → {cache_path.name}")
            if not cache_path.exists():
                failed += 1
            continue

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            mod = importlib.import_module(item["module"])
            fn = getattr(mod, item["fn"])
            part = fn(**item["args"])
            export_step(part, str(cache_path))
            print(f"  ✓  {item['name']:<24} → {cache_path.name}  (vol={part.volume:.1f}mm³)")
        except Exception as e:
            print(f"  ✗  {item['name']:<24} FAILED: {e}")
            failed += 1

    return failed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild all cache/*.step files")
    parser.add_argument("--verify-only", action="store_true", help="仅检查 cache 是否存在")
    parser.add_argument("--filter", metavar="CATEGORY", help="只处理含此字符串的分类路径")
    args = parser.parse_args(argv)

    failed = rebuild(verify_only=args.verify_only, filter_cat=args.filter)
    if failed:
        print(f"\n⚠ {failed} failed")
        return 1
    print("\n✅ all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
