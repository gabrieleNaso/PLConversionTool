from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "case"


def _find_generated_bundle(generated_root: Path, sequence_name: str) -> Path:
    bundle = generated_root / sequence_name.lower()
    if not bundle.exists():
        raise FileNotFoundError(f"Generated bundle not found: {bundle}")
    return bundle


def _find_generated_json_pair(bundle_dir: Path, name_prefix: str) -> tuple[Path, Path]:
    ir_candidates = sorted(
        [p for p in bundle_dir.glob("*_ir.json") if p.is_file()],
        key=lambda p: p.name.lower(),
    )
    if name_prefix:
        prefix_lower = (name_prefix + "_").lower()
        preferred = [p for p in ir_candidates if p.name.lower().startswith(prefix_lower)]
        if preferred:
            ir_candidates = preferred

    if not ir_candidates:
        raise FileNotFoundError(f"No *_ir.json found in: {bundle_dir}")

    ir_src = ir_candidates[0]
    analysis_src = bundle_dir / ir_src.name.replace("_ir.json", "_analysis.json")
    if not analysis_src.exists():
        raise FileNotFoundError(f"Missing analysis json for: {ir_src.name} (expected {analysis_src.name})")

    return ir_src, analysis_src


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate and snapshot expected JSON outputs for a single case input file. "
            "Writes cases/expected_output/<case_id>/{ir.json,analysis.json}."
        )
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the case input file (recommended under cases/input/).",
    )
    parser.add_argument(
        "--generated-root",
        default="work/output/generated",
        help="Generated bundles root folder (default: work/output/generated).",
    )
    parser.add_argument(
        "--name-prefix",
        default="Case",
        help="Sequence name prefix used for generation (default: Case).",
    )
    parser.add_argument(
        "--expected-root",
        default="cases/expected_output",
        help="Expected output root folder (default: cases/expected_output).",
    )
    args = parser.parse_args()

    input_path = (PROJECT_ROOT / args.input).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    generated_root = (PROJECT_ROOT / args.generated_root).resolve()
    expected_root = (PROJECT_ROOT / args.expected_root).resolve()
    expected_root.mkdir(parents=True, exist_ok=True)

    case_id = _slugify(input_path.stem)
    sequence_name = f"{args.name_prefix}_{case_id}"

    subprocess.run(
        [
            "python3",
            str(PROJECT_ROOT / "scripts" / "generate_from_input.py"),
            "--input-dir",
            str(input_path.parent.relative_to(PROJECT_ROOT)),
            "--output-root",
            str(generated_root.relative_to(PROJECT_ROOT)),
            "--name-prefix",
            str(args.name_prefix),
            "--source",
            input_path.name,
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )

    bundle_dir = _find_generated_bundle(generated_root=generated_root, sequence_name=sequence_name)
    ir_src, analysis_src = _find_generated_json_pair(bundle_dir=bundle_dir, name_prefix=str(args.name_prefix))

    expected_dir = expected_root / case_id
    if expected_dir.exists():
        shutil.rmtree(expected_dir)
    expected_dir.mkdir(parents=True, exist_ok=True)

    json.loads(ir_src.read_text(encoding="utf-8"))
    json.loads(analysis_src.read_text(encoding="utf-8"))

    shutil.copy2(ir_src, expected_dir / "ir.json")
    shutil.copy2(analysis_src, expected_dir / "analysis.json")

    print(f"[OK] {input_path.name} -> {expected_dir.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
