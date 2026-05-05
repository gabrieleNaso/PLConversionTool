from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "case"


def _copy_json_outputs(bundle_dir: Path, expected_root: Path, name_prefix: str) -> int:
    copied = 0
    ir_paths = [p for p in bundle_dir.glob("*_ir.json") if p.is_file()]
    for ir_path in sorted(ir_paths, key=lambda p: p.name.lower()):
        if name_prefix and not ir_path.name.lower().startswith((name_prefix + "_").lower()):
            continue

        analysis_path = bundle_dir / ir_path.name.replace("_ir.json", "_analysis.json")
        if not analysis_path.exists():
            continue

        # Derive case_id from "<NamePrefix>_<something>_ir.json"
        stem = ir_path.name[: -len("_ir.json")]
        if name_prefix and stem.lower().startswith((name_prefix + "_").lower()):
            stem = stem[len(name_prefix) + 1 :]
        case_id = _slugify(stem)

        expected_dir = expected_root / case_id
        expected_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ir_path, expected_dir / "ir.json")
        shutil.copy2(analysis_path, expected_dir / "analysis.json")
        copied += 2

    return copied


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Snapshot expected JSON outputs for cases/: copies *_ir.json and *_analysis.json "
            "from a generated output root into cases/expected_output/."
        )
    )
    parser.add_argument(
        "--generated-root",
        default="work/output/generated",
        help="Generated bundles root folder (default: work/output/generated).",
    )
    parser.add_argument(
        "--expected-root",
        default="cases/expected_output",
        help="Expected output root folder (default: cases/expected_output).",
    )
    parser.add_argument(
        "--name-prefix",
        default="Case",
        help="Only snapshot JSON files starting with '<prefix>_' (default: Case).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove non-JSON files from expected-dir before copying.",
    )
    args = parser.parse_args()

    generated_root = (PROJECT_ROOT / args.generated_root).resolve()
    expected_root = (PROJECT_ROOT / args.expected_root).resolve()
    expected_root.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for path in expected_root.iterdir():
            if path.name == ".gitkeep":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    if not generated_root.exists():
        raise SystemExit(f"Generated root not found: {generated_root}")

    name_prefix = str(args.name_prefix).rstrip("_")
    total = 0
    for bundle_dir in sorted([p for p in generated_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        total += _copy_json_outputs(
            bundle_dir=bundle_dir,
            expected_root=expected_root,
            name_prefix=name_prefix,
        )

    print(f"Copied JSON files: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
