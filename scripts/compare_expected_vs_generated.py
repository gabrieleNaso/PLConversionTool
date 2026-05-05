from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _normalize_xml_for_hash(xml_text: str) -> str:
    # Best-effort normalization for stable hashing:
    # - normalize newlines
    # - collapse runs of whitespace between tags and around '='
    # Do NOT try to canonicalize attribute order (too heavy for now).
    xml_text = xml_text.replace("\r\n", "\n").replace("\r", "\n")
    xml_text = re.sub(r"[ \t]+", " ", xml_text)
    xml_text = re.sub(r">\s+<", "><", xml_text)
    return xml_text.strip()


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text))


def _extract_block_type(xml_text: str) -> str | None:
    m = re.search(r"<SW\\.Blocks\\.(FB|FC|GlobalDB)\\b", xml_text)
    return m.group(1) if m else None


def _extract_name(xml_text: str) -> str | None:
    m = re.search(r"<Name>([^<]+)</Name>", xml_text)
    if m:
        return m.group(1).strip()
    m = re.search(r'Name=\"Name\"\\s+Value=\"([^\"]+)\"', xml_text)
    if m:
        return m.group(1).strip()
    return None


def _extract_block_signature(xml_text: str) -> str:
    block_type = _extract_block_type(xml_text) or "Unknown"
    name = _extract_name(xml_text) or "Unknown"
    return f"{block_type}:{name}"


def _metrics(xml_text: str) -> dict[str, int]:
    return {
        "len": len(xml_text),
        "compile_units": xml_text.count("SW.Blocks.CompileUnit"),
        "flgnets": xml_text.count("<FlgNet"),
        "networks": xml_text.count("<Network") + xml_text.count("<FlgNet"),
        "parts": xml_text.count("<Part"),
        "global_vars": xml_text.count("GlobalVariable"),
        "component": xml_text.count("Component"),
        "wire": xml_text.count("<Wire"),
    }


def _classify_artifact(file_name: str, xml_text: str) -> str:
    lower = file_name.lower()
    if lower.endswith(".xml"):
        if "sequence" in lower or ("graph" in lower and "fb" in lower):
            return "graph_fb"
        if "transitions" in lower and "fc" in lower:
            return "fc_transitions"
        if "alarms" in lower and "fc" in lower:
            return "fc_alarms"
        if "hmi" in lower and "fc" in lower:
            return "fc_hmi"
        if "aux" in lower and "fc" in lower:
            return "fc_aux"
        if "output" in lower and "fc" in lower:
            return "fc_output"
        if "lev2" in lower and "fc" in lower:
            return "fc_lev2"
        if "parameters" in lower:
            return "db_parameters"
        if "transitions" in lower and "db" in lower:
            return "db_transitions"
        if "alarms" in lower and "db" in lower:
            return "db_alarms"
        if "hmi" in lower and "db" in lower:
            return "db_hmi"
        if "aux" in lower and "db" in lower:
            return "db_aux"
        if ("i-o" in lower or "i_o" in lower or ("io" in lower and "db" in lower)):
            return "db_io"
        if "lev2" in lower and "db" in lower:
            return "db_lev2"
        if "ext" in lower and "db" in lower:
            return "db_ext"
        if "graph_db" in lower or ("graph" in lower and "db" in lower):
            return "db_graph"
    # fallback: infer from signature
    sig = _extract_block_signature(xml_text).lower()
    if sig.startswith("fb:"):
        return "graph_fb"
    if "transitions" in sig:
        return "fc_transitions"
    if "alarms" in sig:
        return "fc_alarms"
    if " hmi" in sig or sig.endswith("hmi"):
        return "fc_hmi"
    if " aux" in sig or sig.endswith("aux"):
        return "fc_aux"
    if " output" in sig or sig.endswith("output"):
        return "fc_output"
    if " lev2" in sig or sig.endswith("lev2"):
        return "fc_lev2"
    if "parameters" in sig:
        return "db_parameters"
    if "i-o" in sig or "i_o" in sig:
        return "db_io"
    return "other"


@dataclass(frozen=True)
class Artifact:
    file_name: str
    artifact_type: str | None
    content: str

    @property
    def signature(self) -> str:
        return _extract_block_signature(self.content)

    @property
    def kind(self) -> str:
        return _classify_artifact(self.file_name, self.content)

    @property
    def norm_hash(self) -> str:
        return _sha16(_normalize_xml_for_hash(self.content))


def _load_artifacts_from_analysis(path: Path) -> tuple[dict[str, Any], list[Artifact]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    artifacts: list[Artifact] = []
    for p in payload.get("artifact_previews", []) or []:
        if not isinstance(p, dict):
            continue
        file_name = p.get("file_name")
        content = p.get("content")
        if not isinstance(file_name, str) or not isinstance(content, str):
            continue
        artifacts.append(
            Artifact(
                file_name=file_name,
                artifact_type=p.get("artifact_type") if isinstance(p.get("artifact_type"), str) else None,
                content=content,
            )
        )
    return payload, artifacts


def _find_best_match(expected: Artifact, generated_by_kind: dict[str, list[Artifact]]) -> Artifact | None:
    candidates = generated_by_kind.get(expected.kind, [])
    if not candidates:
        return None
    # Prefer same block type (FB/FC/DB) and then closest size.
    exp_sig = expected.signature.split(":", 1)[0]
    same_type = [c for c in candidates if c.signature.split(":", 1)[0] == exp_sig]
    pool = same_type or candidates
    return min(pool, key=lambda c: abs(len(c.content) - len(expected.content)))


def _diff_summary(a: str, b: str) -> dict[str, int]:
    a_lines = a.splitlines()
    b_lines = b.splitlines()
    sm = difflib.SequenceMatcher(a=a_lines, b=b_lines)
    inserted = deleted = replaced = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert":
            inserted += j2 - j1
        elif tag == "delete":
            deleted += i2 - i1
        elif tag == "replace":
            replaced += max(i2 - i1, j2 - j1)
    return {"inserted_lines": inserted, "deleted_lines": deleted, "replaced_lines": replaced}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare expected (analysis.json-like) vs generated analysis.json and write a Markdown report."
    )
    parser.add_argument(
        "--expected",
        default="cases/expected_output/expected_output1/AWL romania FC102.json",
        help="Expected JSON path containing artifact_previews (default: cases/expected_output/expected_output1/AWL romania FC102.json).",
    )
    parser.add_argument(
        "--generated",
        default="work/output/generated/input_awl_romania_fc102/Input_AWL_romania_FC102_analysis.json",
        help="Generated analysis JSON path (default: work/output/generated/input_awl_romania_fc102/Input_AWL_romania_FC102_analysis.json).",
    )
    parser.add_argument(
        "--out",
        default="work/tmp/compare_expected_output1_vs_generated_fc102.md",
        help="Markdown report output path (default: work/tmp/compare_expected_output1_vs_generated_fc102.md).",
    )
    args = parser.parse_args()

    expected_path = (PROJECT_ROOT / args.expected).resolve()
    generated_path = (PROJECT_ROOT / args.generated).resolve()
    out_path = (PROJECT_ROOT / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    expected_payload, expected_artifacts = _load_artifacts_from_analysis(expected_path)
    generated_payload, generated_artifacts = _load_artifacts_from_analysis(generated_path)

    generated_by_kind: dict[str, list[Artifact]] = {}
    for a in generated_artifacts:
        generated_by_kind.setdefault(a.kind, []).append(a)

    lines: list[str] = []
    lines.append("# Compare expected vs generated")
    lines.append("")
    lines.append(f"- expected: `{expected_path.relative_to(PROJECT_ROOT)}`")
    lines.append(f"- generated: `{generated_path.relative_to(PROJECT_ROOT)}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- expected artifacts: {len(expected_artifacts)}")
    lines.append(f"- generated artifacts: {len(generated_artifacts)}")
    exact_matches = len({a.norm_hash for a in expected_artifacts} & {a.norm_hash for a in generated_artifacts})
    lines.append(f"- exact matches (normalized hash): {exact_matches}")
    lines.append("")

    kinds = sorted(set([a.kind for a in expected_artifacts] + [a.kind for a in generated_artifacts]))
    lines.append("## Per-kind counts")
    for k in kinds:
        e = sum(1 for a in expected_artifacts if a.kind == k)
        g = sum(1 for a in generated_artifacts if a.kind == k)
        lines.append(f"- `{k}`: expected {e}, generated {g}")
    lines.append("")

    lines.append("## Detailed comparison (best-effort pairing by kind)")
    for kind in kinds:
        e_list = [a for a in expected_artifacts if a.kind == kind]
        if not e_list:
            continue
        lines.append(f"### {kind}")
        for exp_art in e_list:
            match = _find_best_match(exp_art, generated_by_kind)
            if match is None:
                lines.append(f"- expected `{exp_art.file_name}` -> no generated match")
                continue
            exp_m = _metrics(exp_art.content)
            gen_m = _metrics(match.content)
            diff_m = _diff_summary(_normalize_xml_for_hash(exp_art.content), _normalize_xml_for_hash(match.content))
            lines.append(f"- expected `{exp_art.file_name}` ({exp_art.signature})")
            lines.append(f"  - generated `{match.file_name}` ({match.signature})")
            lines.append(f"  - expected metrics: {exp_m}")
            lines.append(f"  - generated metrics: {gen_m}")
            lines.append(f"  - diff (normalized): {diff_m}")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Wrote {out_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

