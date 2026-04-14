#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core_converter import export_conversion_bundle  # noqa: E402


SUPPORTED_EXTENSIONS = {".awl", ".txt", ".md"}


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return cleaned or "Sequence"


def _extract_awl_from_markdown(raw_text: str) -> str:
    fenced_blocks = re.findall(r"```(?:awl|text)?\s*\n(.*?)```", raw_text, flags=re.IGNORECASE | re.DOTALL)
    for block in fenced_blocks:
        if "NETWORK" in block.upper():
            return block.strip() + "\n"
    return raw_text


def _load_awl_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".md":
        return _extract_awl_from_markdown(raw)
    return raw


def _collect_sources(input_dir: Path) -> list[Path]:
    return sorted(
        [
            item
            for item in input_dir.iterdir()
            if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
        ],
        key=lambda item: item.name.lower(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate XML bundles from AWL files in an input folder."
    )
    parser.add_argument(
        "--input-dir",
        default="input",
        help="Input folder containing .awl/.txt/.md sources (default: input).",
    )
    parser.add_argument(
        "--output-root",
        default="output/generated",
        help="Output root folder (default: output/generated).",
    )
    parser.add_argument(
        "--name-prefix",
        default="Auto",
        help="Sequence name prefix used for generated bundles (default: Auto).",
    )
    args = parser.parse_args()

    input_dir = (PROJECT_ROOT / args.input_dir).resolve()
    output_root = (PROJECT_ROOT / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    sources = _collect_sources(input_dir)
    if not sources:
        print(f"No source files found in: {input_dir}")
        print("Add .awl, .txt, or .md files and run again.")
        return 0

    generated = 0
    for source in sources:
        awl_source = _load_awl_text(source)
        if "NETWORK" not in awl_source.upper():
            print(f"Skipping {source.name}: no AWL NETWORK found.")
            continue

        base_name = _slugify(source.stem)
        sequence_name = _slugify(f"{args.name_prefix}_{base_name}")
        bundle_dir = output_root / sequence_name.lower()
        bundle_dir_relative = bundle_dir.relative_to(PROJECT_ROOT)

        result = export_conversion_bundle(
            sequence_name=sequence_name,
            awl_source=awl_source,
            source_name=source.name,
            output_dir=str(bundle_dir_relative),
        )
        generated += 1
        print(f"[OK] {source.name} -> {result['outputDirectory']}")

    print(f"Done. Generated bundles: {generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
