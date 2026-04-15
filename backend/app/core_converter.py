from __future__ import annotations

import json
import sys
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from plc_converter import (  # noqa: E402
    analyze_awl_source,
    build_conversion_scaffold,
    build_target_profile,
)


def get_target_profile() -> dict:
    return build_target_profile().to_dict()


def bootstrap_conversion(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
) -> dict:
    return build_conversion_scaffold(
        sequence_name=sequence_name,
        awl_source=awl_source,
        source_name=source_name,
    ).to_dict()


def analyze_conversion(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
) -> dict:
    return analyze_awl_source(
        sequence_name=sequence_name,
        awl_source=awl_source,
        source_name=source_name,
    ).to_dict()


def export_conversion_bundle(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
    output_dir: str = "data/output/generated",
) -> dict:
    analysis = analyze_awl_source(
        sequence_name=sequence_name,
        awl_source=awl_source,
        source_name=source_name,
    ).to_dict()

    data_output_root = (PROJECT_ROOT / "data" / "output").resolve()
    relative_output = Path(output_dir)
    if relative_output.is_absolute():
        relative_output = Path(*relative_output.parts[1:])

    # Normalizza path legacy/varianti mantenendo sempre output sotto data/output.
    parts_lower = [part.lower() for part in relative_output.parts]
    if len(parts_lower) >= 2 and parts_lower[0] == "data" and parts_lower[1] == "output":
        relative_output = Path(*relative_output.parts[2:])
    elif parts_lower and parts_lower[0] == "output":
        relative_output = Path(*relative_output.parts[1:])

    destination = (data_output_root / relative_output).resolve()
    if data_output_root not in destination.parents and destination != data_output_root:
        raise ValueError(
            "outputDir deve rimanere dentro la cartella data/output/ del progetto."
        )
    destination.mkdir(parents=True, exist_ok=True)

    written_files: list[str] = []
    for preview in analysis["artifact_previews"]:
        file_path = destination / preview["file_name"]
        file_path.write_text(preview["content"], encoding="utf-8")
        written_files.append(str(file_path))

    report_path = destination / f"{analysis['scaffold']['sequence_name']}_analysis.json"
    report_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    written_files.append(str(report_path))

    return {
        "sequenceName": analysis["scaffold"]["sequence_name"],
        "outputDirectory": str(destination),
        "writtenFiles": written_files,
        "analysis": analysis,
    }
