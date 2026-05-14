from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLGNET_NS = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
FNS = {"f": FLGNET_NS}


def _support_member_name_from_analysis(token: str) -> str:
    # Use the same implementation as the generator.
    import os
    import sys

    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    sys.path.insert(0, str(src_dir))
    try:
        from plc_converter.analysis import _support_member_name  # type: ignore
    except Exception:
        # Fallback: best-effort sanitization.
        import re

        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(token or "")).strip("_")
        cleaned = re.sub(r"_+", "_", cleaned).strip("_") or "Signal"
        if cleaned[0].isdigit():
            cleaned = f"N_{cleaned}"
        return cleaned[:96]
    return _support_member_name(str(token or ""), "", strict_excel_mode=True)


def _load_ir(ir_json: Path) -> dict:
    return json.loads(ir_json.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Decl:
    datatype: str


def _parse_db_member_types(bundle_dir: Path) -> dict[str, str]:
    """Map 'DB_NAME.member_path' -> Datatype from generated DB xml files."""
    mapping: dict[str, str] = {}
    for db_file in sorted(bundle_dir.glob("DB*_auto.xml")):
        if db_file.name.startswith("ZZ_"):
            continue
        root = ET.parse(db_file).getroot()
        db_name = (root.findtext(".//SW.Blocks.GlobalDB/AttributeList/Name") or "").strip()
        if not db_name:
            continue

        ns = "http://www.siemens.com/automation/Openness/SW/Interface/v5"
        static = root.find(f".//{{{ns}}}Section[@Name='Static']")
        if static is None:
            continue

        def walk(member: ET.Element, prefix: str) -> None:
            name = member.attrib.get("Name") or ""
            dtype = member.attrib.get("Datatype") or ""
            if not name:
                return
            path = f"{prefix}.{name}" if prefix else name
            full = f"{db_name}.{path}"
            if dtype:
                mapping[full] = dtype
            for child in member.findall(f"./{{{ns}}}Member"):
                walk(child, path)

        for top in static.findall(f"./{{{ns}}}Member"):
            walk(top, "")
    return mapping


def _const_type_to_plc(const_type: str) -> str:
    t = (const_type or "").strip()
    if not t:
        return ""
    up = t.upper()
    if up in {"BOOL"}:
        return "Bool"
    if up in {"INT"}:
        return "Int"
    if up in {"DINT"}:
        return "DInt"
    if up in {"REAL"}:
        return "Real"
    if up in {"LREAL"}:
        return "LReal"
    return t


def _symbol_components(access: ET.Element) -> list[str]:
    comps = []
    for c in access.findall(".//f:Component", FNS):
        n = (c.attrib.get("Name") or "").strip()
        if n:
            comps.append(n)
    return comps


def _access_operand_key(access: ET.Element) -> tuple[str, str]:
    scope = (access.attrib.get("Scope") or "").strip()
    if scope in {"LiteralConstant", "TypedConstant"}:
        ct = (access.findtext(".//f:ConstantType", namespaces=FNS) or "").strip()
        return ("const", _const_type_to_plc(ct))
    comps = _symbol_components(access)
    if comps:
        return ("sym", ".".join(comps))
    return ("", "")


def _build_net_dsu(flgnet: ET.Element) -> dict[str, str]:
    parent: dict[str, str] = {}

    def add(x: str) -> None:
        parent.setdefault(x, x)

    def find(x: str) -> str:
        add(x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    def eid(local: str, uid: str | None = None, name: str | None = None) -> str:
        if local == "Powerrail":
            return "Powerrail"
        if local == "NameCon":
            return f"NameCon:{uid}:{name}"
        if local == "IdentCon":
            return f"IdentCon:{uid}"
        return f"Unknown:{local}:{uid}:{name}"

    for w in flgnet.findall(".//f:Wire", FNS):
        endpoints: list[str] = []
        for child in list(w):
            local = child.tag.split("}")[-1]
            if local == "Powerrail":
                endpoints.append(eid("Powerrail"))
            elif local == "NameCon":
                endpoints.append(eid("NameCon", uid=child.attrib.get("UId"), name=child.attrib.get("Name")))
            elif local == "IdentCon":
                endpoints.append(eid("IdentCon", uid=child.attrib.get("UId")))
        if len(endpoints) >= 2:
            first = endpoints[0]
            for e in endpoints[1:]:
                union(first, e)
    return {k: find(k) for k in parent.keys()}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix operand_datatypes in IR based on MOVE src/dst types observed in a generated bundle.")
    ap.add_argument("--ir-json", required=True)
    ap.add_argument("--bundle-dir", required=True)
    ap.add_argument("--write", action="store_true", help="Write changes back to IR json.")
    args = ap.parse_args()

    ir_path = (PROJECT_ROOT / args.ir_json).resolve()
    bundle_dir = (PROJECT_ROOT / args.bundle_dir).resolve()

    ir = _load_ir(ir_path)
    operand_catalog = list(ir.get("operand_catalog", []) or [])
    token_by_member: dict[str, str] = {}
    for tok in operand_catalog:
        t = str(tok or "").strip()
        if not t:
            continue
        member = _support_member_name_from_analysis(t)
        token_by_member.setdefault(member, t)

    db_types = _parse_db_member_types(bundle_dir)

    fixes = []
    unresolved: list[dict[str, object]] = []

    for fc_file in sorted(bundle_dir.glob("FC*_auto.xml")):
        root = ET.parse(fc_file).getroot()
        for flgnet in root.findall(".//f:FlgNet", FNS):
            dsu = _build_net_dsu(flgnet)
            # Access uid -> (kind,value)
            access_by_uid: dict[str, tuple[str, str]] = {}
            for acc in flgnet.findall(".//f:Access", FNS):
                uid = acc.attrib.get("UId")
                if not uid:
                    continue
                access_by_uid[uid] = _access_operand_key(acc)

            # Move parts
            for part in flgnet.findall(".//f:Part", FNS):
                if (part.attrib.get("Name") or "").strip() != "Move":
                    continue
                puid = part.attrib.get("UId")
                if not puid:
                    continue
                net_in = dsu.get(f"NameCon:{puid}:in")
                if not net_in:
                    continue
                # Find src access connected to in
                srcs = []
                for uid, (k, v) in access_by_uid.items():
                    net = dsu.get(f"IdentCon:{uid}")
                    if net and net == net_in:
                        srcs.append((k, v))
                src_type = ""
                src_sym = ""
                for k, v in srcs:
                    if k == "const" and v:
                        src_type = v
                        break
                if not src_type:
                    for k, v in srcs:
                        if k == "sym" and v:
                            # symbol type from DB declarations if possible
                            src_sym = v
                            src_type = db_types.get(v, "")
                            if src_type:
                                break
                if not src_type:
                    unresolved.append(
                        {
                            "fc": fc_file.name,
                            "reason": "src_type_unknown",
                            "srcs": srcs,
                        }
                    )
                    continue

                # destinations: out1/out2...
                for out_idx in range(1, 9):
                    net_out = dsu.get(f"NameCon:{puid}:out{out_idx}")
                    if not net_out:
                        continue
                    dsts = []
                    for uid, (k, v) in access_by_uid.items():
                        net = dsu.get(f"IdentCon:{uid}")
                        if net and net == net_out and k == "sym" and v:
                            dsts.append(v)
                    for dst in dsts:
                        dst_type = db_types.get(dst, "")
                        if not dst_type:
                            unresolved.append(
                                {
                                    "fc": fc_file.name,
                                    "reason": "dst_type_unknown",
                                    "dst": dst,
                                    "src_type": src_type,
                                }
                            )
                            continue
                        if dst_type != src_type:
                            # Try to map member back to catalog token to patch operand_datatypes.
                            comps = dst.split(".")
                            member = comps[-1] if comps else ""
                            tok = token_by_member.get(member)
                            if tok:
                                current = str(ir.setdefault("operand_datatypes", {}).get(tok) or "").strip()
                                ir["operand_datatypes"][tok] = src_type
                                fixes.append(
                                    {
                                        "fc": fc_file.name,
                                        "dst": dst,
                                        "dst_type": dst_type,
                                        "src_type": src_type,
                                        "token": tok,
                                        "prev": current,
                                    }
                                )
                            else:
                                unresolved.append(
                                    {
                                        "fc": fc_file.name,
                                        "reason": "dst_token_not_mapped",
                                        "dst": dst,
                                        "dst_type": dst_type,
                                        "src_type": src_type,
                                    }
                                )

    result = {"fixes": fixes, "count": len(fixes), "unresolved": unresolved, "unresolved_count": len(unresolved)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.write and fixes:
        ir_path.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Updated {ir_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
