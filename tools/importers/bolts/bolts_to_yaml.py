"""Convert BOLTS .blt files to parts-lib YAML format.

Source: https://github.com/boltsparts/BOLTS  (MIT + CC-BY)
License: MIT

Usage:
    python bolts_to_yaml.py /path/to/BOLTS/data/hex_socket_head.blt
    python bolts_to_yaml.py /path/to/BOLTS/data/ --category extrusion
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

TODAY = date.today().isoformat()

CONFIDENCE_MAP = {
    "ISO": 5, "DIN": 5, "ANSI": 5, "JIS": 5, "GB": 5,
    "BS": 4, "EN": 4,
}

FACTORY_MAP = {
    "hex_socket_head": {
        "module": "build123d_parts_lib.parts.fasteners.socket_head_screw",
        "fn": "make_socket_head_screw",
    },
    "hex_bolt": {
        "module": "build123d_parts_lib.parts.fasteners.hex_bolt",
        "fn": "make_hex_bolt",
    },
    "hex_nut": {
        "module": "build123d_parts_lib.parts.fasteners.nut_hex",
        "fn": "make_hex_nut",
    },
    "washer": {
        "module": "build123d_parts_lib.parts.fasteners.washer",
        "fn": "make_washer",
    },
}


def _infer_confidence(standards: list[str]) -> int:
    for s in standards:
        for prefix, score in CONFIDENCE_MAP.items():
            if s.upper().startswith(prefix):
                return score
    return 3


def _parse_blt(path: Path) -> dict[str, Any]:
    """Parse a BOLTS .blt YAML file and return raw data."""
    with path.open() as f:
        return yaml.safe_load(f)


def _extract_standard_str(standards: list[dict]) -> str:
    parts = []
    for s in standards:
        body = s.get("body", "")
        std = s.get("standard", "")
        if body and std:
            parts.append(f"{body} {std}")
        elif std:
            parts.append(std)
    return " / ".join(parts) if parts else "unknown"


def _extract_aliases(names: dict, part_id: str) -> list[str]:
    aliases = []
    name = names.get("name", {})
    if nice := name.get("nice"):
        aliases.append(nice)
    if short := name.get("short"):
        if short not in aliases:
            aliases.append(short)
    for v in name.get("versions", []):
        if v not in aliases:
            aliases.append(v)
    # ensure part_id itself is in aliases
    key_lower = part_id.lower()
    if key_lower not in [a.lower() for a in aliases]:
        aliases.append(key_lower)
    return aliases[:8]  # cap at 8


def convert_class(bolts_class: dict, category: str) -> dict[str, Any]:
    """Convert one BOLTS class definition to parts-lib YAML dict."""
    result = {}

    class_id = bolts_class.get("id", "unknown")
    standards = bolts_class.get("standards", [])
    names = bolts_class.get("names", {})
    parameters = bolts_class.get("parameters", {})
    source_info = bolts_class.get("source", {})

    std_str = _extract_standard_str(standards)
    confidence = _infer_confidence([s.get("standard", "") for s in standards])
    aliases = _extract_aliases(names, class_id)

    # flatten dimension tables — take first table row as defaults
    dimensions: dict[str, Any] = {"unit": "mm"}
    tables = parameters.get("tables", [])
    if tables:
        first = tables[0]
        columns = first.get("columns", [])
        data = first.get("data", {})
        # use first data row
        if data:
            first_key = next(iter(data))
            values = data[first_key]
            for col, val in zip(columns, values):
                if isinstance(val, (int, float)):
                    dimensions[col] = float(val)

    factory_info = FACTORY_MAP.get(category, {
        "module": f"build123d_parts_lib.parts.{category}.{category}",
        "fn": f"make_{category}",
    })
    part_key = class_id.upper().replace("-", "_")

    entry = {
        "aliases": aliases,
        "standard": std_str,
        "type": category.replace("_", "-"),
        "dimensions": dimensions,
        "source": {
            "primary": source_info.get("url", "https://github.com/boltsparts/BOLTS"),
            "confidence": confidence,
            "last_verified": TODAY,
        },
        "factory": {
            "module": factory_info["module"],
            "fn": factory_info["fn"],
            "args": {"size": class_id},
            "cache": f"cache/{class_id.lower()}.step",
        },
        "notes": source_info.get("description", ""),
    }
    result[part_key] = entry
    return result


def convert_file(blt_path: Path, category: str | None = None) -> dict[str, Any]:
    """Convert a full .blt file."""
    raw = _parse_blt(blt_path)
    cat = category or blt_path.stem
    output: dict[str, Any] = {}

    classes = raw.get("classes", [])
    for cls in classes:
        converted = convert_class(cls, cat)
        output.update(converted)

    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert BOLTS .blt to parts-lib YAML")
    parser.add_argument("input", help="Path to .blt file or directory")
    parser.add_argument("--category", help="Override category name")
    parser.add_argument("--output", help="Output YAML file (default: stdout)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    result: dict[str, Any] = {}
    if input_path.is_file():
        result = convert_file(input_path, args.category)
    else:
        for blt in sorted(input_path.glob("*.blt")):
            result.update(convert_file(blt, args.category))

    out_yaml = yaml.dump(result, allow_unicode=True, sort_keys=False, default_flow_style=False)

    if args.output:
        Path(args.output).write_text(out_yaml)
        print(f"Written to {args.output}  ({len(result)} parts)")
    else:
        print(out_yaml)


if __name__ == "__main__":
    main()
