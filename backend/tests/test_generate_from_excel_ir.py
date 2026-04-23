from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.generate_from_excel_ir import (  # noqa: E402
    _build_transitions_from_rows,
    _infer_operands_from_expression,
    _read_support_logic_rows,
)


def test_infer_operands_from_expression_extracts_unique_tokens() -> None:
    operands = _infer_operands_from_expression("(M_START AND NOT M_STOP) OR DB81.DBX0.0")
    assert operands == ["M_START", "M_STOP", "DB81.DBX0.0"]


def test_build_transitions_infers_guard_operands_when_column_is_empty() -> None:
    rows = [
        {
            "from_step": "S1",
            "to_step": "S2",
            "condition_expression": "F1 AND NOT F2",
            "operands_used_in_condition": "",
        }
    ]
    transitions = _build_transitions_from_rows(rows)
    assert len(transitions) == 1
    assert transitions[0]["guard_operands"] == ["F1", "F2"]


def test_support_fc_infers_condition_operands_from_expression(tmp_path: Path) -> None:
    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)
    sheet = workbook.create_sheet("support_fc")
    sheet.append(
        [
            "category",
            "member_name",
            "result_member",
            "condition_expression",
            "condition_operands",
            "comment",
            "network",
        ]
    )
    sheet.append(
        [
            "aux",
            "",
            "AUX_CMD",
            "AUX_SIG AND NOT AUX_BLOCK",
            "",
            "Rete AUX",
            1,
        ]
    )
    excel_path = tmp_path / "support_fc.xlsx"
    workbook.save(excel_path)

    rows = _read_support_logic_rows(excel_path)
    assert len(rows) == 1
    assert rows[0]["condition_operands"] == ["AUX_SIG", "AUX_BLOCK"]
