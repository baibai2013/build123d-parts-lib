#!/usr/bin/env python3
"""Regenerate all cache/*.step files from YAML factory entries.
从 YAML factory 条目自动重建所有 cache/*.step 文件。

Auto-discovers all parts registered in YAML files under build123d_parts_lib/parts/
自动发现 build123d_parts_lib/parts/ 下所有 YAML 文件中注册的零件。

Usage:
    python3 scripts/rebuild_cache.py
    python3 scripts/rebuild_cache.py --verify-only
    python3 scripts/rebuild_cache.py --filter bearings
    python3 scripts/rebuild_cache.py --preview   # render PNG for parts missing one
"""
from __future__ import annotations

import argparse
import importlib
import sys
import time
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
            if filter_cat and (
                filter_cat.upper() not in key.upper()
                and filter_cat.lower() not in str(yaml_file).lower()
            ):
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


def preview_missing(filter_cat: str | None = None) -> int:
    """为 cache 中有 STEP 但无 PNG 的零件渲染缩略图，最后汇总为一张图。
    Render PNG thumbnails for parts that have a STEP file but no PNG,
    then save a single combined summary image.

    Returns the number of parts rendered.
    """
    try:
        import ocp_vscode
        from build123d import import_step
    except ImportError as e:
        print(f"  ✗  preview requires ocp_vscode and build123d: {e}")
        return 0

    ocp_vscode.set_port(3939)

    # 扫描所有 cache 目录下的 STEP 文件 / scan all STEP files under cache dirs
    new_parts: list[tuple[str, object]] = []
    for step_file in sorted(PARTS_DIR.rglob("cache/*.step")):
        if filter_cat and filter_cat.lower() not in str(step_file).lower():
            continue
        png_file = step_file.with_suffix(".png")
        if png_file.exists():
            continue
        try:
            part = import_step(str(step_file))
            ocp_vscode.show(part, names=[step_file.stem],
                            reset_camera=ocp_vscode.Camera.RESET)
            time.sleep(1.5)
            ocp_vscode.save_screenshot(str(png_file))
            print(f"  ✓ PNG  {step_file.stem}")
            new_parts.append((step_file.stem, part))
        except Exception as e:
            print(f"  ✗ PNG  {step_file.stem}: {e}")

    if not new_parts:
        print("  (no new parts to preview)")
        return 0

    # 汇总图：用 PIL 拼贴各零件的个人 PNG，避免 3D 等轴相机导致对角线布局
    # Summary: tile individual part PNGs with PIL — avoids isometric-camera diagonal
    png_paths = []
    for name, _part in new_parts:
        for step_file in PARTS_DIR.rglob(f"cache/{name}.step"):
            candidate = step_file.with_suffix(".png")
            if candidate.exists():
                png_paths.append(candidate)
                break

    summary_path = REPO_ROOT / "preview_new.png"
    try:
        from PIL import Image as PILImage
        COLS = 8
        def _white_bg(im: "PILImage.Image") -> "PILImage.Image":
            """Replace near-black OCP background pixels with white."""
            import numpy as np
            arr = np.array(im.convert("RGB"))
            dark = (arr[:, :, 0] < 30) & (arr[:, :, 1] < 30) & (arr[:, :, 2] < 30)
            arr[dark] = 255
            return PILImage.fromarray(arr)

        imgs = [_white_bg(PILImage.open(p)) for p in png_paths]
        tile_w = max(img.width  for img in imgs)
        tile_h = max(img.height for img in imgs)
        rows = (len(imgs) + COLS - 1) // COLS
        grid = PILImage.new("RGB", (COLS * tile_w, rows * tile_h), color=(255, 255, 255))
        for idx, img in enumerate(imgs):
            col = idx % COLS
            row = idx // COLS
            x = col * tile_w + (tile_w - img.width)  // 2
            y = row * tile_h + (tile_h - img.height) // 2
            grid.paste(img, (x, y))
        grid.save(str(summary_path))
    except Exception as e:
        print(f"  ✗ PIL summary failed: {e}")

    print(f"\n  Summary → {summary_path}")
    return len(new_parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rebuild all cache/*.step files")
    parser.add_argument("--verify-only", action="store_true", help="仅检查 cache 是否存在")
    parser.add_argument("--filter", metavar="CATEGORY", help="只处理含此字符串的分类路径")
    parser.add_argument("--preview", action="store_true",
                        help="为无 PNG 的 STEP 缓存件渲染缩略图，输出一张汇总图")
    args = parser.parse_args(argv)

    if args.preview:
        n = preview_missing(filter_cat=args.filter)
        print(f"\n✅ previewed {n} new parts")
        return 0

    failed = rebuild(verify_only=args.verify_only, filter_cat=args.filter)
    if failed:
        print(f"\n⚠ {failed} failed")
        return 1
    print("\n✅ all OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
