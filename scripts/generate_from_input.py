#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core_converter import analyze_conversion, export_conversion_bundle_from_ir  # noqa: E402
from app.core_converter import analyze_conversion_project  # noqa: E402


SUPPORTED_EXTENSIONS = {".awl", ".txt", ".md"}


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return cleaned or "Sequence"


def _extract_awl_from_markdown(raw_text: str) -> str:
    fenced_blocks = re.findall(
        r"```(?:awl|il|stl|text)?\s*\n(.*?)```",
        raw_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not fenced_blocks:
        return raw_text

    selected_blocks = [block.strip() for block in fenced_blocks if _looks_like_awl_block(block)]
    if not selected_blocks:
        selected_blocks = [block.strip() for block in fenced_blocks]

    normalized_blocks: list[str] = []
    for index, block in enumerate(selected_blocks, start=1):
        if not block:
            continue
        if re.search(r"^\s*NETWORK\b", block, flags=re.IGNORECASE | re.MULTILINE):
            normalized_blocks.append(block)
        else:
            normalized_blocks.append(f"NETWORK {index}\n{block}")

    if not normalized_blocks:
        return raw_text
    return "\n\n".join(normalized_blocks).strip() + "\n"


def _looks_like_awl_block(block: str) -> bool:
    heuristics = (
        r"\bNETWORK\b",
        r"^\s*(A|AN|O|ON|U|UN|=|S|R|L|T|SD|SE|SP|SS|SF|JC|JCN|JU)\b",
        r"\bS5T#",
        r"\bDB\d+\.",
        r"\b[QAEIM]\d+\.\d+\b",
    )
    return any(
        re.search(pattern, block, flags=re.IGNORECASE | re.MULTILINE)
        for pattern in heuristics
    )


def _load_awl_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".md":
        return _extract_awl_from_markdown(raw)
    return raw


def _extract_block_id(path: Path, raw_text: str) -> str | None:
    # Prefer explicit markdown header: "# FC102 : ..." etc.
    header_match = re.search(
        r"^\s*#\s*(FC|FB|OB)\s*0*(\d+)\b",
        raw_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    if header_match:
        return f"{header_match.group(1).upper()}{int(header_match.group(2))}"
    # Fallback to filename if it embeds the block id.
    name_match = re.search(r"\b(FC|FB|OB)\s*0*(\d+)\b", path.stem, flags=re.IGNORECASE)
    if name_match:
        return f"{name_match.group(1).upper()}{int(name_match.group(2))}"
    return None


def _collect_sources(input_dir: Path, source: str | None, prefix: str | None) -> list[Path]:
    candidates = [
        item
        for item in input_dir.iterdir()
        if item.is_file() and item.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if source:
        candidates = [item for item in candidates if item.name.lower() == source.lower()]
    if prefix:
        candidates = [item for item in candidates if item.name.lower().startswith(prefix.lower())]
    return sorted(candidates, key=lambda item: item.name.lower())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate XML bundles from AWL files in an input folder."
    )
    parser.add_argument(
        "--input-dir",
        default="data/input",
        help="Input folder containing .awl/.txt/.md sources (default: data/input).",
    )
    parser.add_argument(
        "--output-root",
        default="data/output/generated",
        help="Output root folder (default: data/output/generated).",
    )
    parser.add_argument(
        "--name-prefix",
        default="Auto",
        help="Sequence name prefix used for generated bundles (default: Auto).",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Generate only this exact source filename from input dir.",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Generate only sources whose filename starts with this prefix.",
    )
    args = parser.parse_args()

    input_dir = (PROJECT_ROOT / args.input_dir).resolve()
    output_root = (PROJECT_ROOT / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    input_dir.mkdir(parents=True, exist_ok=True)

    sources = _collect_sources(input_dir, args.source, args.prefix)
    if not sources:
        print(f"No source files found in: {input_dir}")
        print("Add .awl, .txt, or .md files and run again.")
        return 0

    # Project scan: index all blocks available in the input folder so the converter
    # can resolve CALL dependencies (e.g. sequencer FC32) when those sources exist.
    project_blocks: dict[str, str] = {}
    for candidate in _collect_sources(input_dir, None, args.prefix):
        raw_text = candidate.read_text(encoding="utf-8")
        block_id = _extract_block_id(candidate, raw_text)
        if not block_id:
            continue
        project_blocks.setdefault(block_id, _extract_awl_from_markdown(raw_text) if candidate.suffix.lower() == ".md" else raw_text)

    generated = 0
    for source in sources:
        raw_text = source.read_text(encoding="utf-8")
        awl_source = _extract_awl_from_markdown(raw_text) if source.suffix.lower() == ".md" else raw_text
        if "NETWORK" not in awl_source.upper() and source.suffix.lower() != ".md":
            print(f"Skipping {source.name}: no AWL NETWORK found.")
            continue
        entry_block_id = _extract_block_id(source, raw_text)

        base_name = _slugify(source.stem)
        sequence_name = _slugify(f"{args.name_prefix}_{base_name}")
        bundle_dir = output_root / sequence_name.lower()
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        bundle_dir_relative = bundle_dir.relative_to(PROJECT_ROOT)

        analysis = (
            analyze_conversion_project(
                sequence_name=sequence_name,
                awl_source=awl_source,
                source_name=source.name,
                project_blocks=project_blocks,
                entry_block_id=entry_block_id,
            )
            if project_blocks
            else analyze_conversion(
                sequence_name=sequence_name,
                awl_source=awl_source,
                source_name=source.name,
            )
        )
        ir_payload = analysis.get("ir")
        if not isinstance(ir_payload, dict):
            print(f"Skipping {source.name}: analysis IR non disponibile.")
            continue

        ir_json_path = bundle_dir / f"{sequence_name}_ir.json"
        ir_json_path.write_text(json.dumps(ir_payload, indent=2), encoding="utf-8")

        result = export_conversion_bundle_from_ir(
            sequence_name=sequence_name,
            ir_payload=ir_payload,
            source_name=source.name,
            output_dir=str(bundle_dir_relative),
        )
        # Preserve project-level warnings/metadata (e.g. missing called blocks) which would
        # otherwise be lost when re-analyzing from IR.
        analysis_json_path = bundle_dir / f"{sequence_name}_analysis.json"
        analysis_json_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
        generated += 1
        print(f"[OK] {source.name} -> {result['outputDirectory']}")
        print(f"[IR] {ir_json_path}")

    print(f"Done. Generated bundles: {generated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
