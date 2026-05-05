from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _collect_xml_files(root: Path) -> list[Path]:
    return sorted(
        [p for p in root.rglob("*.xml") if p.is_file()],
        key=lambda p: str(p).lower(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert an expected_output folder containing reference XML files into an analysis.json "
            "compatible with the generator output schema (scaffold + artifact_previews)."
        )
    )
    parser.add_argument(
        "--expected-dir",
        default="cases/expected_output/expected_output1",
        help="Expected output directory containing XML files (default: cases/expected_output/expected_output1).",
    )
    parser.add_argument(
        "--sequence-name",
        default=None,
        help="Optional sequence name to store in scaffold (default: inferred from folder name).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for analysis.json (default: <expected-dir>/analysis.json).",
    )
    args = parser.parse_args()

    expected_dir = (PROJECT_ROOT / args.expected_dir).resolve()
    if not expected_dir.exists():
        raise FileNotFoundError(f"Expected dir not found: {expected_dir}")

    xml_files = _collect_xml_files(expected_dir)
    if not xml_files:
        raise FileNotFoundError(f"No XML files found under: {expected_dir}")

    sequence_name = args.sequence_name or expected_dir.name
    output_path = (PROJECT_ROOT / args.output).resolve() if args.output else expected_dir / "analysis.json"

    artifact_previews = []
    manifest_files = []
    for xml_path in xml_files:
        rel_name = xml_path.relative_to(expected_dir).as_posix()
        content = xml_path.read_text(encoding="utf-8")
        artifact_previews.append(
            {
                "artifact_type": "xml_reference",
                "file_name": rel_name,
                "content": content,
            }
        )
        manifest_files.append(rel_name)

    analysis = {
        "scaffold": {
            "sequence_name": sequence_name,
            "target_profile": {},
            "source_analysis": {"kind": "expected_xml_reference"},
            "artifact_plan": {"kind": "reference_only"},
            "graph_static_contract": {},
            "global_db_sections": [],
            "orchestration_flow": [],
            "roadmap": [],
            "assumptions": [
                "Questo analysis.json e' derivato da XML di riferimento (expected_output).",
                "Non contiene IR ricostruito automaticamente: serve per confrontare artefatti XML.",
            ],
        },
        "ir": None,
        "graph_topology": None,
        "validation_issues": [],
        "artifact_previews": artifact_previews,
        "artifact_manifest": {
            "kind": "expected_output_reference",
            "written_files": manifest_files,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote {output_path.relative_to(PROJECT_ROOT)} (xml files: {len(xml_files)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

