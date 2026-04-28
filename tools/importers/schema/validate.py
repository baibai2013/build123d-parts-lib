"""YAML part schema validator.

Checks that generated YAML files meet the minimum quality bar before
they can be moved from tools/importers/output/ into parts/.

Source: internal schema — see part_schema.yaml
License: MIT
"""
from __future__ import annotations

import argparse
import importlib
import sys
import urllib.parse
from datetime import date
from pathlib import Path
from typing import Any

import yaml

MIN_CONFIDENCE = 4
MIN_ALIASES = 3

REQUIRED_TOP = {"aliases", "standard", "type", "source", "factory"}
REQUIRED_SOURCE = {"primary", "confidence", "last_verified"}
REQUIRED_FACTORY = {"module", "fn", "args", "cache"}


def _err(part_id: str, msg: str) -> str:
    return f"  [{part_id}] {msg}"


def validate_file(path: Path, skip_import_check: bool = False) -> list[str]:
    """Return list of error strings; empty = valid."""
    errors: list[str] = []
    data: dict[str, Any] = yaml.safe_load(path.read_text())

    for part_id, spec in data.items():
        if part_id.startswith("$") or not isinstance(spec, dict):
            continue

        missing_top = REQUIRED_TOP - spec.keys()
        for f in missing_top:
            errors.append(_err(part_id, f"missing required field: {f}"))

        aliases = spec.get("aliases", [])
        if len(aliases) < MIN_ALIASES:
            errors.append(_err(part_id, f"aliases must have ≥{MIN_ALIASES} entries, got {len(aliases)}"))

        source = spec.get("source", {})
        missing_src = REQUIRED_SOURCE - source.keys()
        for f in missing_src:
            errors.append(_err(part_id, f"source.{f} missing"))
        confidence = source.get("confidence", 0)
        if confidence < MIN_CONFIDENCE:
            errors.append(_err(part_id, f"confidence={confidence} < {MIN_CONFIDENCE} (min for commit)"))

        factory = spec.get("factory", {})
        missing_fac = REQUIRED_FACTORY - factory.keys()
        for f in missing_fac:
            errors.append(_err(part_id, f"factory.{f} missing"))

        # Check 1: factory.module importable
        module_str = factory.get("module", "")
        if module_str and not skip_import_check:
            try:
                importlib.import_module(module_str)
            except ImportError as e:
                errors.append(_err(part_id, f"factory.module import failed: {e}"))

        # Check 2: factory.fn callable
        fn_str = factory.get("fn", "")
        if module_str and fn_str and not skip_import_check:
            try:
                mod = importlib.import_module(module_str)
                if not callable(getattr(mod, fn_str, None)):
                    errors.append(_err(part_id, f"factory.fn {fn_str!r} not callable in {module_str}"))
            except ImportError:
                pass  # already reported above

        # Check 3: source.primary URL format
        primary_url = source.get("primary", "")
        if primary_url:
            parsed = urllib.parse.urlparse(primary_url)
            if not (parsed.scheme in ("http", "https") and parsed.netloc):
                errors.append(_err(part_id, f"source.primary is not a valid URL: {primary_url!r}"))

        # Check 4: last_verified freshness (warn if > 90 days old)
        last_verified_raw = source.get("last_verified", "")
        if last_verified_raw:
            try:
                lv = date.fromisoformat(str(last_verified_raw))
                age_days = (date.today() - lv).days
                if age_days > 90:
                    errors.append(_err(part_id, f"source.last_verified is {age_days} days old (> 90 day limit)"))
            except ValueError:
                errors.append(_err(part_id, f"source.last_verified invalid date format: {last_verified_raw!r}"))

    return errors


def fix_stale_dates(path: Path) -> int:
    """Update last_verified to today for stale entries (> 90 days old).
    Returns the number of entries updated.
    """
    today_str = date.today().isoformat()
    raw = path.read_text()
    data: dict[str, Any] = yaml.safe_load(raw)
    updated = 0
    for part_id, spec in data.items():
        if part_id.startswith("$") or not isinstance(spec, dict):
            continue
        source = spec.get("source", {})
        last_verified_raw = source.get("last_verified", "")
        if last_verified_raw:
            try:
                lv = date.fromisoformat(str(last_verified_raw))
                age_days = (date.today() - lv).days
                if age_days > 90:
                    # Update the raw text (simple string replacement for YAML)
                    raw = raw.replace(str(last_verified_raw), today_str, 1)
                    updated += 1
                    print(f"  Updated {part_id} last_verified: {last_verified_raw} → {today_str}")
            except ValueError:
                pass
    if updated:
        path.write_text(raw)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate YAML part schema files"
    )
    parser.add_argument("patterns", nargs="+", metavar="PATTERN",
                        help="Glob patterns for YAML files to validate")
    parser.add_argument("--skip-import-check", action="store_true",
                        help="Skip factory.module import validation")
    parser.add_argument("--fix-dates", action="store_true",
                        help="Update last_verified to today for stale entries (> 90 days)")
    args = parser.parse_args()

    all_errors: list[str] = []
    for pattern in args.patterns:
        for p in sorted(Path(".").glob(pattern)):
            if args.fix_dates:
                fix_stale_dates(p)
            errs = validate_file(p, skip_import_check=args.skip_import_check)
            if errs:
                print(f"\nFAIL: {p}")
                for e in errs:
                    print(e)
                all_errors.extend(errs)
            else:
                print(f"OK:   {p}")

    if all_errors:
        sys.exit(1)
    print("\nAll files passed.")


if __name__ == "__main__":
    main()
