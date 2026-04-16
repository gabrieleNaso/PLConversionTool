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

from app.core_converter import export_conversion_bundle_from_ir  # noqa: E402

try:
    from openpyxl import load_workbook
except ModuleNotFoundError as exc:  # pragma: no cover - runtime guard
    raise SystemExit(
        "Modulo mancante: openpyxl. Installa le dipendenze backend (pip install -r backend/requirements.txt)."
    ) from exc


def _slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_") or "Sequence"


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _pick(row: dict[str, object], *keys: str) -> object:
    for key in keys:
        if key in row and row[key] is not None and _cell_text(row[key]):
            return row[key]
    for key in keys:
        if key in row:
            return row[key]
    return None


def _split_list(value: object) -> list[str]:
    text = _cell_text(value)
    if not text:
        return []
    return [item.strip() for item in re.split(r"[|,;]", text) if item.strip()]


def _split_int_list(value: object) -> list[int]:
    items: list[int] = []
    for token in _split_list(value):
        match = re.search(r"-?\d+", token)
        if match:
            items.append(int(match.group(0)))
    return items


def _int_or_default(value: object, default: int) -> int:
    text = _cell_text(value)
    if not text:
        return default
    match = re.search(r"-?\d+", text)
    if not match:
        return default
    return int(match.group(0))


def _int_or_none(value: object) -> int | None:
    text = _cell_text(value)
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    if not match:
        return None
    parsed = int(match.group(0))
    return parsed if parsed > 0 else None


def _read_sheet_rows(path: Path, sheet_name: str) -> list[dict[str, object]]:
    workbook = load_workbook(path, data_only=True)
    if sheet_name not in workbook.sheetnames:
        return []
    sheet = workbook[sheet_name]
    values = list(sheet.iter_rows(values_only=True))
    if not values:
        return []
    headers = [_cell_text(item) for item in values[0]]
    rows: list[dict[str, object]] = []
    for row in values[1:]:
        if not any(_cell_text(item) for item in row):
            continue
        item = {header: cell for header, cell in zip(headers, row) if header}
        if item:
            rows.append(item)
    return rows


def _read_meta(path: Path) -> dict[str, str]:
    rows = _read_sheet_rows(path, "meta")
    meta: dict[str, str] = {}
    for row in rows:
        key = _cell_text(row.get("key")).lower()
        value = _cell_text(row.get("value"))
        if key:
            meta[key] = value
    return meta


def build_ir_from_excel(path: Path, sequence_name: str | None = None) -> tuple[str, str, dict]:
    meta = _read_meta(path)
    base_name = sequence_name or meta.get("sequence_name") or path.stem
    normalized_sequence = _slugify(base_name)
    source_name = meta.get("source_name") or path.name

    networks: list[dict[str, object]] = []
    for idx, row in enumerate(_read_sheet_rows(path, "networks"), start=1):
        networks.append(
            {
                "index": _int_or_default(
                    _pick(row, "network_index", "index"),
                    idx,
                ),
                "title": _cell_text(
                    _pick(row, "network_title", "title")
                ) or None,
                "raw_lines": _split_list(
                    _pick(row, "network_lines_for_traceability", "raw_lines")
                ),
            }
        )

    steps: list[dict[str, object]] = []
    for row in _read_sheet_rows(path, "steps"):
        name = _cell_text(_pick(row, "step_name", "name"))
        if not name:
            continue
        steps.append(
            {
                "name": name,
                "step_number": _int_or_none(
                    _pick(row, "numero_step", "step_number", "step_no", "numero", "number")
                ),
                "source_networks": _split_int_list(
                    _pick(
                        row,
                        "networks_where_step_is_read",
                        "source_networks",
                    )
                ),
                "activation_networks": _split_int_list(
                    _pick(
                        row,
                        "networks_where_step_is_activated",
                        "activation_networks",
                    )
                ),
                "action_networks": _split_int_list(
                    _pick(
                        row,
                        "networks_with_step_actions",
                        "action_networks",
                    )
                ),
            }
        )

    transitions: list[dict[str, object]] = []
    for idx, row in enumerate(_read_sheet_rows(path, "transitions"), start=1):
        source_step = _cell_text(_pick(row, "from_step", "source_step"))
        target_step = _cell_text(_pick(row, "to_step", "target_step"))
        if not source_step or not target_step:
            continue
        transitions.append(
            {
                "transition_id": _cell_text(_pick(row, "transition_id")) or f"T{idx}",
                "source_step": source_step,
                "target_step": target_step,
                "network_index": _int_or_default(
                    _pick(row, "condition_network_index", "network_index"),
                    1,
                ),
                "guard_expression": _cell_text(
                    _pick(row, "condition_expression", "guard_expression")
                ) or "TRUE",
                "guard_operands": _split_list(
                    _pick(row, "operands_used_in_condition", "guard_operands")
                ),
                "jump_labels": _split_list(
                    _pick(row, "jump_labels_used", "jump_labels")
                ),
            }
        )

    timers: list[dict[str, object]] = []
    for row in _read_sheet_rows(path, "timers"):
        source_timer = _cell_text(_pick(row, "timer_name", "source_timer"))
        if not source_timer:
            continue
        timers.append(
            {
                "source_timer": source_timer,
                "network_index": _int_or_default(
                    _pick(row, "defined_in_network_index", "network_index"),
                    1,
                ),
                "kind": (
                    _cell_text(_pick(row, "timer_instruction_kind", "kind")) or "SD"
                ).upper(),
                "preset": _cell_text(
                    _pick(row, "timer_preset_value", "preset")
                ) or None,
                "trigger_operands": _split_list(
                    _pick(row, "timer_trigger_operands", "trigger_operands")
                ),
            }
        )

    memories: list[dict[str, object]] = []
    for row in _read_sheet_rows(path, "memories"):
        name = _cell_text(_pick(row, "memory_operand", "name"))
        if not name:
            continue
        memories.append(
            {
                "name": name,
                "role": _cell_text(_pick(row, "memory_role", "role")) or "aux",
                "network_index": _int_or_default(
                    _pick(row, "found_in_network_index", "network_index"),
                    1,
                ),
            }
        )

    faults: list[dict[str, object]] = []
    for row in _read_sheet_rows(path, "faults"):
        name = _cell_text(_pick(row, "fault_tag", "name"))
        if not name:
            continue
        faults.append(
            {
                "name": name,
                "network_index": _int_or_default(
                    _pick(row, "found_in_network_index", "network_index"),
                    1,
                ),
                "evidence": _cell_text(_pick(row, "fault_evidence", "evidence")),
            }
        )

    outputs: list[dict[str, object]] = []
    for row in _read_sheet_rows(path, "outputs"):
        name = _cell_text(_pick(row, "output_operand", "name"))
        if not name:
            continue
        outputs.append(
            {
                "name": name,
                "network_index": _int_or_default(
                    _pick(row, "found_in_network_index", "network_index"),
                    1,
                ),
                "action": _cell_text(_pick(row, "write_action", "action")) or "=",
            }
        )

    ir_payload = {
        "sequence_name": normalized_sequence,
        "source_name": source_name,
        "networks": networks,
        "steps": steps,
        "transitions": transitions,
        "timers": timers,
        "memories": memories,
        "faults": faults,
        "outputs": outputs,
        "manual_logic_networks": _split_int_list(meta.get("manual_logic_networks")),
        "auto_logic_networks": _split_int_list(meta.get("auto_logic_networks")),
        "external_refs": _split_list(meta.get("external_refs")),
        "assumptions": _split_list(meta.get("assumptions")),
    }
    return normalized_sequence, source_name, ir_payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate XML bundle from a manual Excel IR workbook (.xlsx)."
    )
    parser.add_argument("--excel", required=True, help="Path to Excel workbook (.xlsx).")
    parser.add_argument(
        "--output-root",
        default="data/output/generated",
        help="Output root folder (default: data/output/generated).",
    )
    parser.add_argument(
        "--sequence-name",
        default=None,
        help="Optional override for sequence name.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clean target bundle folder before generation.",
    )
    args = parser.parse_args()

    excel_path = (PROJECT_ROOT / args.excel).resolve()
    if not excel_path.exists():
        raise SystemExit(f"Excel file not found: {excel_path}")

    sequence_name, source_name, ir_payload = build_ir_from_excel(
        path=excel_path,
        sequence_name=args.sequence_name,
    )

    output_root = (PROJECT_ROOT / args.output_root).resolve()
    bundle_dir = output_root / sequence_name.lower()
    if bundle_dir.exists() and not args.keep_existing:
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_relative = bundle_dir.relative_to(PROJECT_ROOT)

    ir_json_path = bundle_dir / f"{sequence_name}_ir.json"
    ir_json_path.write_text(json.dumps(ir_payload, indent=2), encoding="utf-8")

    result = export_conversion_bundle_from_ir(
        sequence_name=sequence_name,
        ir_payload=ir_payload,
        source_name=source_name,
        output_dir=str(bundle_relative),
    )
    print(f"[OK] {excel_path.name} -> {result['outputDirectory']}")
    print(f"[IR] {ir_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
