from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLGNET_NS = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
GRAPH_NS = "http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"
IF_NS = "http://www.siemens.com/automation/Openness/SW/Interface/v5"


def _load_db_name_to_declared(bundle_dir: Path) -> dict[str, set[str]]:
    declared_by_db: dict[str, set[str]] = {}
    db_files = list(bundle_dir.glob("DB*_auto.xml")) + list(bundle_dir.glob("ZZ_DB*_auto.xml"))
    for p in db_files:
        try:
            root = ET.fromstring(p.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        name_el = root.find(".//Name")
        db_name = (name_el.text or "").strip() if name_el is not None else ""
        if not db_name:
            continue

        sections = root.find(f".//{{{IF_NS}}}Sections")
        decl: set[str] = set()

        def rec(elem: ET.Element, prefix: str = "") -> None:
            for child in list(elem):
                if child.tag == f"{{{IF_NS}}}Member":
                    nm = (child.attrib.get("Name") or "").strip()
                    if nm:
                        path = nm if not prefix else f"{prefix}.{nm}"
                        decl.add(path)
                        rec(child, path)
                    else:
                        rec(child, prefix)
                else:
                    rec(child, prefix)

        if sections is not None:
            rec(sections, "")
        declared_by_db[db_name] = decl
    return declared_by_db


def _collect_accesses_from_xml(xml_path: Path) -> list[tuple[str, str]]:
    text = xml_path.read_text(encoding="utf-8-sig")
    root = ET.fromstring(text)
    accesses: list[tuple[str, str]] = []

    # FlgNet based
    for acc in root.findall(f".//{{{FLGNET_NS}}}Access"):
        comps = [c.attrib.get("Name") for c in acc.findall(f".//{{{FLGNET_NS}}}Component") if c.attrib.get("Name")]
        if comps:
            accesses.append((comps[0], ".".join(comps[1:])))

    # Graph based
    for acc in root.findall(f".//{{{GRAPH_NS}}}Access"):
        comps = [c.attrib.get("Name") for c in acc.findall(f".//{{{GRAPH_NS}}}Component") if c.attrib.get("Name")]
        if comps:
            accesses.append((comps[0], ".".join(comps[1:])))
    return accesses


def main() -> int:
    ap = argparse.ArgumentParser(description="Check that every GlobalVariable access in a bundle resolves to a declared DB member.")
    ap.add_argument("--bundle-dir", required=True, help="Bundle directory under work/output/generated/<slug>.")
    ap.add_argument("--out", default=None, help="Optional output markdown report.")
    args = ap.parse_args()

    bundle_dir = (PROJECT_ROOT / args.bundle_dir).resolve()
    if not bundle_dir.exists():
        raise SystemExit(f"Bundle dir not found: {bundle_dir}")

    declared_by_db = _load_db_name_to_declared(bundle_dir)

    xml_files = sorted([p for p in bundle_dir.glob("*.xml") if p.is_file()], key=lambda p: p.name.lower())
    missing: list[dict[str, str]] = []
    total_accesses = 0

    for xml_path in xml_files:
        for db_name, member_path in _collect_accesses_from_xml(xml_path):
            total_accesses += 1
            if db_name not in declared_by_db:
                missing.append({"file": xml_path.name, "db": db_name, "member": member_path, "reason": "db_not_found"})
                continue
            if member_path and member_path not in declared_by_db[db_name]:
                missing.append({"file": xml_path.name, "db": db_name, "member": member_path, "reason": "member_not_declared"})

    summary = {"xml_files": len(xml_files), "accesses": total_accesses, "missing": len(missing)}
    print(json.dumps(summary, indent=2))

    if args.out:
        out_path = (PROJECT_ROOT / args.out).resolve()
        lines = ["# Bundle symbol resolution", "", "## Summary", "", f"- xml_files: {len(xml_files)}", f"- accesses: {total_accesses}", f"- missing: {len(missing)}", ""]
        if missing:
            lines += ["## Missing", ""]
            for item in missing[:500]:
                lines.append(f"- `{item['file']}`: `{item['db']}.{item['member']}` ({item['reason']})")
            if len(missing) > 500:
                lines.append(f"- ... ({len(missing)-500} more)")
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[OK] Wrote {out_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

