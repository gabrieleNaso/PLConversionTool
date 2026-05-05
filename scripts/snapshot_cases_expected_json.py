from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _copy_json_outputs(bundle_dir: Path, expected_dir: Path, name_prefix: str) -> int:
    copied = 0
    for path in bundle_dir.iterdir():
        if not path.is_file():
            continue
        if not (path.name.endswith("_ir.json") or path.name.endswith("_analysis.json")):
            continue
        if name_prefix and not path.name.startswith(name_prefix):
            continue
        shutil.copy2(path, expected_dir / path.name)
        copied += 1
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
        "--expected-dir",
        default="cases/expected_output",
        help="Expected output folder (default: cases/expected_output).",
    )
    parser.add_argument(
        "--name-prefix",
        default="Case_",
        help="Only snapshot JSON files starting with this prefix (default: Case_).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove non-JSON files from expected-dir before copying.",
    )
    args = parser.parse_args()

    generated_root = (PROJECT_ROOT / args.generated_root).resolve()
    expected_dir = (PROJECT_ROOT / args.expected_dir).resolve()
    expected_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for path in expected_dir.iterdir():
            if path.name == ".gitkeep":
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    if not generated_root.exists():
        raise SystemExit(f"Generated root not found: {generated_root}")

    total = 0
    for bundle_dir in sorted([p for p in generated_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        total += _copy_json_outputs(
            bundle_dir=bundle_dir,
            expected_dir=expected_dir,
            name_prefix=str(args.name_prefix),
        )

    print(f"Copied JSON files: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
