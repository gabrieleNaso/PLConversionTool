#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core_converter import export_conversion_bundle_from_ir  # noqa: E402


def _slugify(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").strip())
    token = token.strip("_")
    while "__" in token:
        token = token.replace("__", "_")
    return token or "sequence"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate XML bundles from an IR JSON payload (skip AWL parsing)."
    )
    parser.add_argument("--ir-json", required=True, help="Path to IR JSON file.")
    parser.add_argument(
        "--output-root",
        default="work/output/generated",
        help="Output root folder (default: work/output/generated).",
    )
    parser.add_argument(
        "--sequence-name",
        default=None,
        help="Override sequence_name inside the IR JSON.",
    )
    parser.add_argument(
        "--target-profile",
        default=None,
        help="Target profile name (e.g. romania). Overrides env PLC_TARGET_PROFILE.",
    )
    args = parser.parse_args()

    if args.target_profile:
        os.environ["PLC_TARGET_PROFILE"] = str(args.target_profile).strip()

    ir_path = Path(args.ir_json)
    if not ir_path.is_absolute():
        ir_path = (PROJECT_ROOT / ir_path).resolve()
    if not ir_path.exists():
        raise SystemExit(f"IR JSON not found: {ir_path}")

    ir_payload = json.loads(ir_path.read_text(encoding="utf-8"))
    if not isinstance(ir_payload, dict):
        raise SystemExit("IR JSON must be a JSON object.")

    sequence_name = str(args.sequence_name or ir_payload.get("sequence_name") or "").strip()
    if not sequence_name:
        raise SystemExit("Missing sequence_name (set it in JSON or pass --sequence-name).")
    ir_payload["sequence_name"] = sequence_name
    source_name = str(ir_payload.get("source_name") or ir_path.name).strip() or ir_path.name
    if args.target_profile:
        ir_payload["target_profile_name"] = str(args.target_profile).strip().lower()

    output_root = (PROJECT_ROOT / args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    bundle_dir = output_root / _slugify(sequence_name).lower()
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_dir_relative = bundle_dir.relative_to(PROJECT_ROOT)

    # Keep a copy of the IR next to generated XMLs for traceability.
    ir_json_copy = bundle_dir / f"{_slugify(sequence_name)}_ir.json"
    ir_json_copy.write_text(json.dumps(ir_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    result = export_conversion_bundle_from_ir(
        sequence_name=sequence_name,
        ir_payload=ir_payload,
        source_name=source_name,
        output_dir=str(bundle_dir_relative),
    )
    print(f"[OK] {ir_path.name} -> {result['outputDirectory']}")
    print(f"[IR] {ir_json_copy}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
