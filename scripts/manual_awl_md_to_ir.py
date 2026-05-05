#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Segment:
    number: int
    title: str
    lines: list[str] = field(default_factory=list)

    def awl_raw_lines(self) -> list[str]:
        raw: list[str] = []
        in_block = False
        for line in self.lines:
            fence = line.strip()
            if fence.startswith("```") and fence.lower().startswith("```awl"):
                in_block = True
                continue
            if fence.startswith("```") and in_block:
                in_block = False
                continue
            if in_block:
                raw.append(line.rstrip("\n"))
        return [line for line in raw if line.strip()]


SEGMENT_RE = re.compile(r"^##\s+Segmento\s+(\d+)\s*-\s*(.+?)\s*$", flags=re.IGNORECASE)


def _read_segments(md_text: str) -> list[Segment]:
    segments: list[Segment] = []
    current: Segment | None = None
    for line in md_text.splitlines():
        match = SEGMENT_RE.match(line)
        if match:
            if current is not None:
                segments.append(current)
            current = Segment(number=int(match.group(1)), title=match.group(2).strip(), lines=[])
            continue
        if current is not None:
            current.lines.append(line)
    if current is not None:
        segments.append(current)
    return segments


def _extract_table_rows(md_text: str, start_header: str, end_header: str) -> list[list[str]]:
    start_idx = md_text.lower().find(start_header.lower())
    if start_idx < 0:
        return []
    end_idx = md_text.lower().find(end_header.lower(), start_idx)
    if end_idx < 0:
        end_idx = len(md_text)
    block = md_text[start_idx:end_idx]
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        # Skip header/separator lines.
        if all(re.fullmatch(r"-+", cell.replace(" ", "")) for cell in parts):
            continue
        rows.append(parts)
    return rows


def _parse_steps(md_text: str) -> list[dict[str, object]]:
    rows = _extract_table_rows(md_text, "## 4.1", "## 4.2")
    steps: list[dict[str, object]] = []
    for row in rows:
        step_cell = row[0]
        match = re.search(r"`(S\d+)`", step_cell, flags=re.IGNORECASE)
        if not match:
            continue
        step_name = match.group(1).upper()
        step_no = int(step_name[1:])
        evidence = " ".join(row[2:])
        net_matches = re.findall(r"Segmento\s+(\d+)", evidence, flags=re.IGNORECASE)
        nets = [int(x) for x in net_matches]
        steps.append(
            {
                "name": step_name,
                "step_number": step_no,
                "source_networks": nets,
                "activation_networks": [],
                "action_networks": nets,
            }
        )
    # Stable ordering.
    steps.sort(key=lambda item: int(str(item.get("step_number") or 10**9)))
    return steps


def _guard_operands_from_condition(condition: str) -> list[str]:
    # Very small heuristic: keep only PLC-like tokens (M/I/Q/DB..).
    tokens: list[str] = []
    for raw in re.split(r"\s+", condition.strip()):
        token = raw.strip("()`,")
        if not token:
            continue
        upper = token.upper()
        if upper in {"AND", "OR", "NOT"}:
            continue
        if re.fullmatch(r"(?:DB\d+\.DBX\d+(?:\.\d+)?|[MIQAE]\d+(?:\.\d+)?)", token, flags=re.IGNORECASE):
            tokens.append(token)
    # Dedupe preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for item in tokens:
        key = item.upper()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _expand_transitions(
    md_text: str,
    step_names: list[str],
) -> list[dict[str, object]]:
    rows = _extract_table_rows(md_text, "## 4.2", "## 4.3")
    transitions: list[dict[str, object]] = []

    # Map known transitions to the segment where the AWL evidence is discussed in this doc.
    default_network = {
        ("S01", "S02"): 17,
        ("S02", "S03"): 19,
        ("S29", "S01"): 20,
        ("S32", "S01"): 20,
    }
    any_network = {
        "S29": 21,
        "S32": 23,
    }

    tid = 1
    for row in rows:
        src = row[0]
        dst = row[1]
        cond = " ".join(row[2:]).strip()
        src_steps: list[str] = []
        dst_steps: list[str] = []

        src_match = re.findall(r"`(S\d+)`", src, flags=re.IGNORECASE)
        dst_match = re.findall(r"`(S\d+)`", dst, flags=re.IGNORECASE)
        if src_match:
            src_steps = [s.upper() for s in src_match]
        elif "any" in src.lower():
            src_steps = [s for s in step_names if s != (dst_match[0].upper() if dst_match else "")]
        if dst_match:
            dst_steps = [dst_match[0].upper()]

        if not src_steps or not dst_steps:
            continue
        target = dst_steps[0]

        # Normalize condition to tool-friendly boolean expression.
        guard_expr = cond
        guard_expr = guard_expr.replace(" AND ", " AND ").replace(" OR ", " OR ")
        guard_expr = re.sub(r"\bAND\b", "AND", guard_expr, flags=re.IGNORECASE)
        guard_expr = re.sub(r"\bOR\b", "OR", guard_expr, flags=re.IGNORECASE)
        guard_expr = re.sub(r"\bNOT\b", "NOT", guard_expr, flags=re.IGNORECASE)

        for source in src_steps:
            if source == target:
                continue
            net_idx = default_network.get((source, target))
            if net_idx is None and "any" in src.lower():
                net_idx = any_network.get(target, 1)
            if net_idx is None:
                net_idx = 1
            transitions.append(
                {
                    "transition_id": f"TR{tid:03d}_{source}_{target}",
                    "source_step": source,
                    "target_step": target,
                    "network_index": net_idx,
                    "guard_expression": guard_expr,
                    "guard_operands": _guard_operands_from_condition(cond),
                    "jump_labels": [],
                    "flow_type": "alternative",
                    "parallel_group": "",
                }
            )
            tid += 1
    return transitions


TIMER_SD_RE = re.compile(r"^\s*SD\s+T\s*(\d+)\s*$", flags=re.IGNORECASE)
TIMER_L_RE = re.compile(r"^\s*L\s+(S5T#[A-Za-z0-9]+)\s*$", flags=re.IGNORECASE)


def _parse_timers(networks: list[dict[str, object]]) -> list[dict[str, object]]:
    timers: list[dict[str, object]] = []
    for net in networks:
        net_idx = int(net["index"])
        lines = [str(x) for x in (net.get("raw_lines") or [])]
        last_preset: str | None = None
        for line in lines:
            m_l = TIMER_L_RE.match(line)
            if m_l:
                last_preset = m_l.group(1)
                continue
            m_sd = TIMER_SD_RE.match(line)
            if m_sd:
                tno = int(m_sd.group(1))
                timers.append(
                    {
                        "source_timer": f"T{tno}",
                        "network_index": net_idx,
                        "kind": "SD",
                        "preset": last_preset,
                        "trigger_operands": [],
                    }
                )
                last_preset = None
    return timers


def build_manual_ir(md_path: Path, *, sequence_name: str) -> dict[str, object]:
    md_text = md_path.read_text(encoding="utf-8")
    segments = _read_segments(md_text)
    networks: list[dict[str, object]] = []
    for seg in segments:
        raw_lines = seg.awl_raw_lines()
        if not raw_lines:
            continue
        networks.append(
            {
                "index": seg.number,
                "title": seg.title,
                "raw_lines": raw_lines,
                "instructions": [],
            }
        )

    steps = _parse_steps(md_text)
    step_names = [str(item["name"]) for item in steps]
    transitions = _expand_transitions(md_text, step_names)
    timers = _parse_timers(networks)

    step_roles = {"S01": "entry", "S29": "manual", "S32": "emergency"}

    return {
        "sequence_name": sequence_name,
        "source_name": md_path.name,
        "networks": networks,
        "steps": steps,
        "transitions": transitions,
        "timers": timers,
        "memories": [],
        "faults": [],
        "outputs": [],
        "manual_logic_networks": [],
        "auto_logic_networks": [],
        "external_refs": [],
        "strict_operand_catalog": False,
        "operand_catalog": [],
        "operand_datatypes": {},
        "operand_categories": {},
        "operand_notes": {},
        "operand_control_settings": {},
        "operand_timer_settings": {},
        "support_members": [],
        "support_logic": [],
        "step_roles": step_roles,
        "assumptions": [
            "IR generato manualmente dal markdown (senza parser AWL automatico).",
            "Transizioni 'Any' espanse sui passi noti in tabella 4.1.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an IR JSON by manually parsing an AWL markdown document.")
    parser.add_argument("--source", required=True, help="Path to the AWL markdown file.")
    parser.add_argument("--sequence-name", required=True, help="IR sequence_name.")
    parser.add_argument("--out", required=True, help="Output IR JSON path.")
    args = parser.parse_args()

    src = Path(args.source)
    if not src.is_absolute():
        src = Path.cwd() / src
    src = src.resolve()
    if not src.exists():
        raise SystemExit(f"Source markdown not found: {src}")

    out = Path(args.out)
    if not out.is_absolute():
        out = Path.cwd() / out
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    payload = build_manual_ir(src, sequence_name=str(args.sequence_name))
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote manual IR: {out}")
    print(f"[NET] networks={len(payload.get('networks') or [])}")
    print(f"[STEP] steps={len(payload.get('steps') or [])}")
    print(f"[TR] transitions={len(payload.get('transitions') or [])}")
    print(f"[TMR] timers={len(payload.get('timers') or [])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
