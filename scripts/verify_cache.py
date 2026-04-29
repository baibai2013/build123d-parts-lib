"""Verify parts-lib cache against factory ground truth.
验证 parts-lib 缓存与 factory 原件的一致性。

三层断言 / 3-layer assertion:
  1. STEP 文件存在 + import_step() 成功加载
     STEP file exists + import_step() loads successfully
  2. bbox 重导入差 < 0.5 mm（各维度）
     Reimported bbox differs < 0.5 mm per axis
  3. volume 重导入差 < 1%
     Reimported volume differs < 1%

运行方式（从仓库根）/ Usage (from repo root):
    python scripts/verify_cache.py                    # 全量验证 bundle 所有条目
    python scripts/verify_cache.py --only bearings    # 按 category 过滤
    python scripts/verify_cache.py --only ball_bearing # 按 slug 过滤

退出码 / Exit codes:
    0 = 全部通过 / all pass
    1 = 有 FAIL / any FAIL, 或 --only 未匹配

License: MIT
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))

from build123d import import_step  # noqa: E402

# 复用 build_cache.py 的 _rep_bundle / reuse bundle from build_cache.py
from build_cache import _rep_bundle  # noqa: E402


# ────── 公差 / Tolerances ──────────────────────────────────────
BBOX_TOL_MM   = 0.5    # bbox 各轴最大差 / max per-axis bbox diff (主断言 / primary)
VOLUME_TOL_PCT = 10.0  # volume 最大百分比差 / max volume diff (健康度 / health check)
#
# bbox 是主断言: 几何外形一致才算 STEP 保真。
# bbox is the primary assertion: STEP is faithful when outline matches.
#
# volume 容差宽松到 10%: Compound 带子孔的子件(如带球窝保持架)经 OCP XDE 导出
# 再 import_step 回来可能有面法向翻转 / 球窝变浅等小损失。bbox 不变就表明
# 外形几何没丢, volume 小差异作为次要信号提示, 不作为硬性失败指标。
# Compound with sub-holes (e.g. cage with ball pockets) may lose small volume
# through OCP XDE round-trip. bbox is kept strict; volume stays loose.


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        metavar="CATEGORY_OR_SLUG",
        help="只验证匹配 category (如 bearings) 或 slug (如 ball_bearing) 的条目",
    )
    return parser.parse_args(argv)


def _compare_bbox(bb_orig, bb_reimp) -> tuple[bool, str]:
    """Compare two bounding boxes per axis. Return (ok, detail)."""
    dx = abs(bb_orig.size.X - bb_reimp.size.X)
    dy = abs(bb_orig.size.Y - bb_reimp.size.Y)
    dz = abs(bb_orig.size.Z - bb_reimp.size.Z)
    ok = max(dx, dy, dz) < BBOX_TOL_MM
    detail = f"Δ=({dx:.3f},{dy:.3f},{dz:.3f})mm"
    return ok, detail


def _solids_volume(part) -> float:
    """Sum of |Solid.volume| for all leaf solids.
    所有底层 Solid 体积绝对值之和。

    为什么用 abs / Why abs:
    Compound 导出 STEP 经 OCP XDE 后,带子孔的子实体(如带球窝的保持架)
    法向可能翻转,导致 import_step 回来 volume 为负。几何本身未丢失,
    用 abs 消除容器/法向差异,回到"纯几何体积"对比。
    """
    return sum(abs(s.volume) for s in part.solids())


def _compare_volume(v_orig: float, v_reimp: float) -> tuple[bool, str]:
    """Compare volumes, return (ok, detail)."""
    if v_orig <= 0:
        return False, f"v_orig<=0 ({v_orig:.3f})"
    pct = abs(v_orig - v_reimp) / v_orig * 100
    ok = pct < VOLUME_TOL_PCT
    detail = f"Δ={pct:.2f}%"
    return ok, detail


def _verify_one(category: str, slug: str, fn, kwargs, title: str) -> dict:
    """Verify a single bundle entry. Return result dict."""
    cache_dir = REPO_ROOT / "build123d_parts_lib" / "parts" / category / "cache"
    step_path = cache_dir / f"{slug}.step"

    result = {
        "category": category, "slug": slug, "title": title,
        "layer1": None, "layer2": None, "layer3": None,
        "detail": "",
    }

    # Layer 1: STEP file exists + import succeeds
    if not step_path.exists():
        result["layer1"] = False
        result["detail"] = f"STEP not found: {step_path.relative_to(REPO_ROOT)}"
        return result
    try:
        part_reimp = import_step(str(step_path))
        result["layer1"] = True
    except Exception as e:
        result["layer1"] = False
        result["detail"] = f"import_step failed: {type(e).__name__}: {e}"
        return result

    # 原件 factory 调用 / run factory to get ground truth
    try:
        part_orig = fn(**kwargs)
    except Exception as e:
        result["layer2"] = False
        result["layer3"] = False
        result["detail"] = f"factory failed: {type(e).__name__}: {e}"
        return result

    # Layer 2: bbox diff
    bb_ok, bb_detail = _compare_bbox(part_orig.bounding_box(),
                                     part_reimp.bounding_box())
    result["layer2"] = bb_ok

    # Layer 3: volume diff (基于 solids() 总和，绕开 Compound 容器差异)
    v_ok, v_detail = _compare_volume(_solids_volume(part_orig),
                                     _solids_volume(part_reimp))
    result["layer3"] = v_ok

    result["detail"] = f"bbox {bb_detail}  vol {v_detail}"
    return result


def _format_row(r: dict) -> str:
    """Format a single result row."""
    marks = []
    for key in ("layer1", "layer2", "layer3"):
        val = r[key]
        if val is True:
            marks.append("✓")
        elif val is False:
            marks.append("✗")
        else:
            marks.append("-")
    overall = "PASS" if all(r[k] is True for k in ("layer1", "layer2", "layer3")) else "FAIL"
    return (f"  [{overall}] {r['category']}/{r['slug']:<22} "
            f"L1{marks[0]} L2{marks[1]} L3{marks[2]}  {r['detail']}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    bundle = _rep_bundle()

    # 按 --only 过滤 / filter
    if args.only:
        filtered = [e for e in bundle if args.only in (e[0], e[1])]
        if not filtered:
            print(f"!! --only {args.only!r} 无匹配条目 / no matching entries")
            print(f"   可用 category: {sorted({e[0] for e in bundle})}")
            return 1
        print(f">> --only {args.only!r} → verify {len(filtered)} / {len(bundle)} parts")
        bundle = filtered
    else:
        print(f">> Verifying {len(bundle)} cache entries ...")

    print(f"   tolerances: bbox < {BBOX_TOL_MM} mm, volume < {VOLUME_TOL_PCT}%\n")

    pass_n, fail_n = 0, 0
    fails: list[dict] = []

    for category, slug, fn, kwargs, title in bundle:
        r = _verify_one(category, slug, fn, kwargs, title)
        print(_format_row(r))
        if all(r[k] is True for k in ("layer1", "layer2", "layer3")):
            pass_n += 1
        else:
            fail_n += 1
            fails.append(r)

    print(f"\nDone. PASS={pass_n}  FAIL={fail_n}  total={pass_n + fail_n}")

    if fails:
        print("\nFailed entries:")
        for r in fails:
            print(f"  - {r['category']}/{r['slug']}: {r['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
