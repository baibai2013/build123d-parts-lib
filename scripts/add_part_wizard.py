#!/usr/bin/env python3
"""scripts/add_part_wizard.py

AI-assisted part parameter extraction from product pages or images.

Fetches a product URL (or reads a local image), calls Claude Vision API,
and outputs a YAML draft compatible with the build123d-parts-lib schema.

Usage:
    python scripts/add_part_wizard.py --url https://... --type servo --model MY_SERVO
    python scripts/add_part_wizard.py --image path/to/drawing.png --type servo --model MY_SERVO
    python scripts/add_part_wizard.py --url https://... --stdout   # print YAML to stdout only

Requirements:
    pip install anthropic
    ANTHROPIC_API_KEY must be set in the environment.
"""
from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("anthropic SDK not found. Run: pip install anthropic")


ROOT = Path(__file__).parent.parent
PARTS_DIR = ROOT / "build123d_parts_lib" / "parts"

CATEGORY_DIRS: dict[str, Path] = {
    "servo":   PARTS_DIR / "servos",
    "bearing": PARTS_DIR / "bearings",
    "motor":   PARTS_DIR / "actuators",
    "gearbox": PARTS_DIR / "actuators",
    "other":   PARTS_DIR,
}

# YAML templates embed the expected schema shape per category.
# Placeholders: MODEL_NAME, SOURCE_URL, TODAY_DATE
_SERVO_TEMPLATE = """\
MODEL_NAME:
  aliases: []
  body:
    length: null    # mm — TODO: from product page or dimension drawing
    width:  null    # mm
    height: null    # mm (body shell only, no shaft)
    unit:   mm
  mount:
    ear_width_total: null   # mm — TODO: total width including both ears
    ear_thickness:   null   # mm
    ear_z_offset:    null   # mm — ear centerline height from body bottom
    screw_hole_d:    null   # mm
    screw_pitch:     null   # mm — center-to-center of the two mount holes
  output:
    shaft_height_from_body_top: null   # mm
    total_height: null                 # mm — body + shaft
    spline: null                       # e.g. "25T"
  torque_kg_cm: null   # stall torque at rated voltage
  weight_g: null
  source:
    primary: "SOURCE_URL"
    confidence: 2
    last_verified: TODAY_DATE
  factory:
    module: build123d_parts_lib.parts.servos.standard_servo
    fn: make_servo
    args: {model: MODEL_NAME}
    cache: cache/model_name.step
  notes: "TODO: verify key dimensions against physical unit"
"""

_BEARING_TEMPLATE = """\
MODEL_NAME:
  aliases: []
  type: null          # e.g. deep-groove-ball-bearing, angular-contact
  standard: null      # e.g. "ISO 15 / JIS B1521"
  dimensions:
    d: null    # inner diameter mm
    D: null    # outer diameter mm
    B: null    # width mm
    unit: mm
  load:
    dynamic_c_n: null
    static_c0_n: null
    max_rpm_grease: null
  weight_g: null
  fit:
    press_fit_housing_d: null   # recommended housing bore (interference fit)
    shaft_d: null
  source:
    primary: "SOURCE_URL"
    confidence: 2
    last_verified: TODAY_DATE
  factory:
    module: null    # TODO: set after factory function is written
    fn: null
    args: {model: MODEL_NAME}
  notes: null
"""

_OTHER_TEMPLATE = """\
MODEL_NAME:
  aliases: []
  # TODO: choose and fill appropriate field structure for this part type
  dimensions:
    unit: mm
    # fill dimensional fields here (length, width, height, diameter, etc.)
  weight_g: null
  source:
    primary: "SOURCE_URL"
    confidence: 2
    last_verified: TODAY_DATE
  factory:
    module: null
    fn: null
  notes: "TODO: verify key dimensions"
"""

_TEMPLATES: dict[str, str] = {
    "servo":   _SERVO_TEMPLATE,
    "bearing": _BEARING_TEMPLATE,
    "motor":   _OTHER_TEMPLATE,
    "gearbox": _OTHER_TEMPLATE,
    "other":   _OTHER_TEMPLATE,
}

# Keywords that suggest an image is a dimension drawing (higher priority)
_DIM_KEYWORDS = ["dimension", "spec", "size", "drawing", "尺寸", "规格", "图纸", "datasheet", "dwg"]
_SKIP_SRC_KEYWORDS = ["logo", "icon", "pixel", "track", "avatar", "banner", "cart", "btn"]


def _fetch_page(url: str) -> tuple[str, list[tuple[str, bytes]]]:
    """Fetch product page; return (page_text, [(mime_type, image_bytes), ...]).

    Attempts to download up to 4 product images.  Prefers images whose URL or
    alt text suggests they are dimension drawings.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible)"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Extract plain text (strip tags, collapse whitespace)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()

    # Collect img (src, alt) pairs
    img_candidates: list[tuple[str, str]] = []
    for m in re.finditer(r'<img\b([^>]*)>', html, re.IGNORECASE):
        attrs = m.group(1)
        src_m = re.search(r'\bsrc=["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        alt_m = re.search(r'\balt=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        if not src_m:
            continue
        src = src_m.group(1).strip()
        alt = alt_m.group(1).lower() if alt_m else ""
        if any(kw in src.lower() for kw in _SKIP_SRC_KEYWORDS):
            continue
        img_candidates.append((src, alt))

    # Sort: images with dimension keywords come first
    def _priority(item: tuple[str, str]) -> int:
        combined = (item[0] + item[1]).lower()
        return -sum(1 for kw in _DIM_KEYWORDS if kw in combined)

    img_candidates.sort(key=_priority)

    parsed_base = urllib.parse.urlparse(url)
    base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"

    images: list[tuple[str, bytes]] = []
    for src, _ in img_candidates:
        if len(images) >= 4:
            break
        # Resolve URL
        if src.startswith("//"):
            src = parsed_base.scheme + ":" + src
        elif src.startswith("/"):
            src = base_origin + src
        elif not src.startswith("http"):
            src = url.rsplit("/", 1)[0] + "/" + src
        try:
            with urllib.request.urlopen(src, timeout=10) as r:
                data = r.read()
            if len(data) < 3_000:   # skip tiny icons
                continue
            mime = mimetypes.guess_type(src)[0] or "image/jpeg"
            if not mime.startswith("image/"):
                continue
            images.append((mime, data))
        except Exception:
            continue

    # Cap text at 6000 chars to stay within token budget
    return text[:6_000], images


def _build_system_prompt(part_type: str, model_name: str, source_url: str) -> str:
    today = date.today().isoformat()
    template = (
        _TEMPLATES.get(part_type, _OTHER_TEMPLATE)
        .replace("MODEL_NAME", model_name)
        .replace("SOURCE_URL", source_url)
        .replace("TODAY_DATE", today)
    )
    type_hint = part_type if part_type != "other" else "unknown — please identify from the content"
    return f"""\
You are a mechanical engineering assistant helping build a parametric CAD parts library.

Task: Extract dimensional and performance parameters from the supplied product page \
content (text + images) and output a single YAML entry for the build123d-parts-lib schema.

Rules:
- Use `null` for any field you cannot confidently extract; add a short `# TODO` comment.
- Confidence scale: 5=official standard, 4=manufacturer datasheet, 3=manufacturer page, 2=estimated/inferred.
- All dimensions in mm, weight in g, servo torque in kg·cm.
- Output ONLY the YAML block — no prose, no markdown fences.
- If the part type differs from the template, adapt the field structure accordingly.
- Part type hint: {type_hint}

YAML template (fill and adapt):

{template}"""


def _call_claude(system: str, content: list[dict]) -> str:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2048,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": content}],
    )
    raw = response.content[0].text.strip()
    # Strip markdown fences if the model added them
    raw = re.sub(r"^```(?:yaml)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-assisted part parameter extraction (product page → YAML draft).",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src_group = parser.add_mutually_exclusive_group(required=True)
    src_group.add_argument("--url",   help="Product page URL")
    src_group.add_argument("--image", help="Local image/screenshot path")
    parser.add_argument(
        "--type",
        choices=list(CATEGORY_DIRS),
        default="other",
        help="Part category hint (default: other = auto-detect)",
    )
    parser.add_argument("--model", default="MY_PART", help="Part model name, e.g. DS3225MG")
    parser.add_argument("--out",   help="Output directory (default: parts/<type>/drafts/)")
    parser.add_argument("--stdout", action="store_true", help="Print YAML to stdout; skip file write")
    args = parser.parse_args()

    # --- Gather content ---
    if args.url:
        print(f"Fetching {args.url} …", file=sys.stderr)
        try:
            text, images = _fetch_page(args.url)
        except Exception as exc:
            sys.exit(f"Failed to fetch URL: {exc}")
        print(f"  text: {len(text)} chars, images: {len(images)}", file=sys.stderr)
        source_url = args.url
    else:
        img_path = Path(args.image)
        if not img_path.exists():
            sys.exit(f"File not found: {img_path}")
        mime = mimetypes.guess_type(str(img_path))[0] or "image/jpeg"
        text = ""
        images = [(mime, img_path.read_bytes())]
        source_url = f"local file: {img_path.name}"
        print(f"Using image: {img_path} ({mime})", file=sys.stderr)

    # --- Build multimodal message ---
    content: list[dict] = []
    if text:
        content.append({"type": "text", "text": f"Product page text content:\n\n{text}"})
    for mime, data in images:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime,
                "data": base64.standard_b64encode(data).decode(),
            },
        })
    if not content:
        sys.exit("No content to analyze (empty page and no images)")
    content.append({
        "type": "text",
        "text": (
            "Extract all available parameters from the above content and output the YAML entry. "
            "Fill every field you can find; mark the rest with null + # TODO."
        ),
    })

    system = _build_system_prompt(args.type, args.model, source_url)

    # --- Call Claude ---
    print("Calling Claude Vision API …", file=sys.stderr)
    try:
        yaml_text = _call_claude(system, content)
    except anthropic.APIError as exc:
        sys.exit(f"Claude API error: {exc}")

    if args.stdout:
        print(yaml_text)
        return

    # --- Save draft ---
    out_dir = Path(args.out) if args.out else CATEGORY_DIRS.get(args.type, PARTS_DIR) / "drafts"
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", args.model.lower()).strip("_")
    out_file = out_dir / f"{slug}_draft.yaml"
    out_file.write_text(yaml_text + "\n", encoding="utf-8")

    print(f"\nDraft saved → {out_file}", file=sys.stderr)
    print("Next steps:", file=sys.stderr)
    print(f"  1. Review and fill TODO fields in {out_file}", file=sys.stderr)
    print(f"  2. python scripts/check_d1_yaml.py --yaml {out_file} --slug {slug}", file=sys.stderr)


if __name__ == "__main__":
    main()
