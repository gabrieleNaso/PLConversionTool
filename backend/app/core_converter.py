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
    analyze_ir_payload,
    build_conversion_scaffold,
    build_target_profile,
)
from plc_converter.excel_export import export_excel_from_ir  # noqa: E402

try:
    # Optional API (may be missing during hot-reload / partial sync).
    from plc_converter import analyze_awl_project  # type: ignore  # noqa: E402
except ImportError:  # pragma: no cover
    analyze_awl_project = None  # type: ignore[assignment]


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


def analyze_conversion_project(
    sequence_name: str | None,
    awl_source: str,
    project_blocks: dict[str, str],
    source_name: str | None = None,
    entry_block_id: str | None = None,
) -> dict:
    if analyze_awl_project is None:
        raise RuntimeError(
            "Backend non supporta analyze_awl_project (API non disponibile). "
            "Aggiorna/restarta i servizi oppure usa analyze_conversion (single-file)."
        )
    return analyze_awl_project(
        sequence_name=sequence_name,
        awl_source=awl_source,
        project_blocks=project_blocks,
        source_name=source_name,
        entry_block_id=entry_block_id,
    ).to_dict()


def analyze_conversion_from_ir(
    sequence_name: str | None,
    ir_payload: dict,
    source_name: str | None = None,
) -> dict:
    return analyze_ir_payload(
        ir_payload=ir_payload,
        sequence_name=sequence_name,
        source_name=source_name,
    ).to_dict()


def export_conversion_bundle(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
    output_dir: str = "work/output/generated",
) -> dict:
    analysis = analyze_awl_source(
        sequence_name=sequence_name,
        awl_source=awl_source,
        source_name=source_name,
    ).to_dict()
    return _write_bundle(analysis=analysis, output_dir=output_dir)

def export_conversion_bundle_from_ir(
    sequence_name: str | None,
    ir_payload: dict,
    source_name: str | None = None,
    output_dir: str = "work/output/generated",
) -> dict:
    analysis = analyze_ir_payload(
        ir_payload=ir_payload,
        sequence_name=sequence_name,
        source_name=source_name,
    ).to_dict()
    return _write_bundle(analysis=analysis, output_dir=output_dir)


def _write_bundle(analysis: dict, output_dir: str) -> dict:
    data_output_root = (PROJECT_ROOT / "work" / "output").resolve()
    relative_output = Path(output_dir)
    if relative_output.is_absolute():
        relative_output = Path(*relative_output.parts[1:])

    # Normalizza path legacy/varianti mantenendo sempre output sotto work/output/.
    parts_lower = [part.lower() for part in relative_output.parts]
    if len(parts_lower) >= 2 and parts_lower[0] == "data" and parts_lower[1] == "output":
        relative_output = Path(*relative_output.parts[2:])
    elif parts_lower and parts_lower[0] == "output":
        relative_output = Path(*relative_output.parts[1:])
    elif len(parts_lower) >= 2 and parts_lower[0] == "work" and parts_lower[1] == "output":
        relative_output = Path(*relative_output.parts[2:])

    destination = (data_output_root / relative_output).resolve()
    if data_output_root not in destination.parents and destination != data_output_root:
        raise ValueError(
            "outputDir deve rimanere dentro la cartella work/output/ del progetto."
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

    ir_payload = analysis.get("ir")
    if isinstance(ir_payload, dict):
        excel_path = destination / f"{analysis['scaffold']['sequence_name']}_from_ir.xlsx"
        export_excel_from_ir(ir_payload, excel_path)
        written_files.append(str(excel_path))

    return {
        "sequenceName": analysis["scaffold"]["sequence_name"],
        "outputDirectory": str(destination),
        "writtenFiles": written_files,
        "analysis": analysis,
    }
