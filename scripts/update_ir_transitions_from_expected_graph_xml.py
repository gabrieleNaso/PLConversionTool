from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GRAPH_NS = "http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"
NS = {"g": GRAPH_NS}


class DSU:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def _add(self, x: str) -> None:
        if x not in self.parent:
            self.parent[x] = x

    def find(self, x: str) -> str:
        self._add(x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


_SAN_RE = re.compile(r"[^0-9A-Za-z_]+")


def sanitize_component(name: str) -> str:
    # Preserve case, but normalize separators and drop unsupported chars.
    name = name.replace(":", "_").replace(" ", "_").replace("-", "_").replace("/", "_")
    name = _SAN_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def symbol_to_operand(components: list[str]) -> str:
    if not components:
        return "UNKNOWN"
    return ".".join(sanitize_component(c) for c in components if c.strip())


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | None = None
    items: tuple["Expr", ...] = ()

    def operands(self) -> set[str]:
        if self.kind == "var" and self.value:
            return {self.value}
        acc: set[str] = set()
        for it in self.items:
            acc |= it.operands()
        return acc

    def to_str(self) -> str:
        if self.kind == "var":
            return str(self.value)
        if self.kind == "not":
            inner = self.items[0]
            s = inner.to_str()
            if inner.kind in {"var", "not"}:
                return f"NOT ({s})" if inner.kind == "var" else f"NOT ({s})"
            return f"NOT ({s})"
        if self.kind == "and":
            parts = [it.to_str() for it in self.items]
            if len(parts) == 1:
                return parts[0]
            return "(" + " AND ".join(parts) + ")"
        if self.kind == "or":
            parts = [it.to_str() for it in self.items]
            if len(parts) == 1:
                return parts[0]
            return "(" + " OR ".join(parts) + ")"
        return "UNKNOWN_EXPR"


def _expr_and(a: Expr, b: Expr) -> Expr:
    # flatten
    if a.kind == "and" and b.kind == "and":
        return Expr("and", items=a.items + b.items)
    if a.kind == "and":
        return Expr("and", items=a.items + (b,))
    if b.kind == "and":
        return Expr("and", items=(a,) + b.items)
    return Expr("and", items=(a, b))


def _expr_or(items: list[Expr]) -> Expr:
    flat: list[Expr] = []
    for it in items:
        if it.kind == "or":
            flat.extend(it.items)
        else:
            flat.append(it)
    if not flat:
        return Expr("var", value="TRUE")  # should not happen
    if len(flat) == 1:
        return flat[0]
    return Expr("or", items=tuple(flat))


def parse_flgnet_to_expr(flgnet: ET.Element) -> Expr:
    # Map Access UId -> operand string.
    access_operands: dict[str, str] = {}
    for acc in flgnet.findall(".//g:Access", NS):
        uid = acc.attrib.get("UId")
        if not uid:
            continue
        comps = [c.attrib.get("Name", "") for c in acc.findall(".//g:Component", NS)]
        access_operands[uid] = symbol_to_operand(comps)

    # Map Part UId -> (name, negated?)
    part_name: dict[str, str] = {}
    contact_negated: set[str] = set()
    or_card: dict[str, int] = {}
    for part in flgnet.findall(".//g:Part", NS):
        uid = part.attrib.get("UId")
        name = part.attrib.get("Name")
        if not uid or not name:
            continue
        part_name[uid] = name
        if name == "Contact" and list(part.findall(".//g:Negated", NS)):
            contact_negated.add(uid)
        if name == "O":
            tv = part.find("./g:TemplateValue[@Name='Card']", NS)
            if tv is not None and (tv.text or "").strip().isdigit():
                or_card[uid] = int((tv.text or "").strip())

    # DSU on endpoints to build nets.
    dsu = DSU()

    def endpoint_id(tag: str, uid: str | None = None, name: str | None = None, wire_uid: str | None = None) -> str:
        if tag == "Powerrail":
            return "Powerrail"
        if tag == "NameCon":
            return f"NameCon:{uid}:{name}"
        if tag == "IdentCon":
            return f"IdentCon:{uid}"
        return f"Unknown:{wire_uid}:{tag}:{uid}:{name}"

    wires = flgnet.findall(".//g:Wire", NS)
    for w in wires:
        wuid = w.attrib.get("UId", "")
        endpoints: list[str] = []
        for child in list(w):
            local = child.tag.split("}")[-1]
            if local == "Powerrail":
                endpoints.append(endpoint_id("Powerrail", wire_uid=wuid))
            elif local == "NameCon":
                endpoints.append(endpoint_id("NameCon", uid=child.attrib.get("UId"), name=child.attrib.get("Name"), wire_uid=wuid))
            elif local == "IdentCon":
                endpoints.append(endpoint_id("IdentCon", uid=child.attrib.get("UId"), wire_uid=wuid))
        if len(endpoints) >= 2:
            first = endpoints[0]
            for e in endpoints[1:]:
                dsu.union(first, e)

    def net_of_namecon(uid: str, name: str) -> str:
        return dsu.find(endpoint_id("NameCon", uid=uid, name=name))

    def net_of_identcon(uid: str) -> str:
        return dsu.find(endpoint_id("IdentCon", uid=uid))

    def net_of_namecon_if_exists(uid: str, name: str) -> str | None:
        eid = endpoint_id("NameCon", uid=uid, name=name)
        if eid not in dsu.parent:
            return None
        return dsu.find(eid)

    power_net = dsu.find("Powerrail")

    # Build expressions along nets.
    expr_at_net: dict[str, Expr] = {power_net: Expr("var", value="TRUE")}

    # For stable evaluation, iterate until no changes (these FlgNets are DAGs).
    changed = True
    for _ in range(50):
        if not changed:
            break
        changed = False

        # Contacts
        for uid, name in part_name.items():
            if name != "Contact":
                continue
            in_net = net_of_namecon(uid, "in")
            out_net = net_of_namecon(uid, "out")
            op_net = net_of_namecon(uid, "operand")

            if in_net not in expr_at_net:
                continue
            # operand comes from an Access via IdentCon
            operand_var: str | None = None
            for acc_uid, op in access_operands.items():
                if net_of_identcon(acc_uid) == op_net:
                    operand_var = op
                    break
            if operand_var is None:
                continue
            leaf = Expr("var", value=operand_var)
            if uid in contact_negated:
                leaf = Expr("not", items=(leaf,))
            new_expr = _expr_and(expr_at_net[in_net], leaf)
            if expr_at_net.get(out_net) != new_expr:
                expr_at_net[out_net] = new_expr
                changed = True

        # OR gates
        for uid, name in part_name.items():
            if name != "O":
                continue
            in_terms: list[Expr] = []
            for idx in range(1, (or_card.get(uid, 2) + 1)):
                in_port = f"in{idx}"
                in_net = net_of_namecon_if_exists(uid, in_port)
                if in_net is None:
                    continue
                if in_net in expr_at_net:
                    in_terms.append(expr_at_net[in_net])
            out_net = net_of_namecon(uid, "out")
            if in_terms:
                new_expr = _expr_or(in_terms)
                if expr_at_net.get(out_net) != new_expr:
                    expr_at_net[out_net] = new_expr
                    changed = True

        # Comparators (Gt) -> boolean leaf placeholder derived from connected operands.
        for uid, name in part_name.items():
            if name != "Gt":
                continue
            out_net = net_of_namecon(uid, "out")
            # A very conservative placeholder; generator can later refine to a typed compare.
            placeholder = Expr("var", value="GT_COND")
            if expr_at_net.get(out_net) != placeholder:
                expr_at_net[out_net] = placeholder
                changed = True

    # Transition coil consumes its 'in' net.
    trcoils = [uid for uid, n in part_name.items() if n == "TrCoil"]
    if not trcoils:
        return Expr("var", value="TRUE")
    coil_uid = trcoils[0]
    in_net = net_of_namecon(coil_uid, "in")
    return expr_at_net.get(in_net, Expr("var", value="TRUE"))


def _ensure_operand(ir: dict, operand: str, category: str, datatype: str) -> None:
    if operand not in ir["operand_categories"]:
        ir["operand_categories"][operand] = category
    if operand not in ir["operand_datatypes"]:
        ir["operand_datatypes"][operand] = datatype

    # operand_catalog is a list[str]; append if missing.
    if operand not in ir["operand_catalog"]:
        ir["operand_catalog"].append(operand)


def main() -> int:
    ap = argparse.ArgumentParser(description="Update IR transition guard logic from a reference GRAPH Sequence.xml (expected_output).")
    ap.add_argument("--ir-json", required=True, help="Path to IR json to patch in-place.")
    ap.add_argument("--expected-sequence-xml", required=True, help="Path to expected GRAPH sequence xml (e.g. 05 ... Sequence.xml).")
    ap.add_argument("--dry-run", action="store_true", help="Do not write, only print summary.")
    args = ap.parse_args()

    ir_path = (PROJECT_ROOT / args.ir_json).resolve()
    xml_path = (PROJECT_ROOT / args.expected_sequence_xml).resolve()

    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    xml_text = xml_path.read_text(encoding="utf-8-sig")
    root = ET.fromstring(xml_text)

    graph = root.find(".//g:Graph", NS)
    if graph is None:
        raise RuntimeError("Graph node not found in expected sequence xml.")

    expected_transitions = graph.findall(".//g:Sequence/g:Transitions/g:Transition", NS)
    by_number: dict[str, tuple[str, Expr]] = {}
    for t in expected_transitions:
        num = t.attrib.get("Number")
        name = t.attrib.get("Name", "")
        flgnet = t.find("./g:FlgNet", NS)
        if not num or flgnet is None:
            continue
        expr = parse_flgnet_to_expr(flgnet)
        by_number[str(int(num))] = (name, expr)

    patched = 0
    missing = 0
    for tr in ir.get("transitions", []):
        tid = tr.get("transition_id") or ""
        m = re.match(r"^T(\d{3})_", tid)
        if not m:
            continue
        num = str(int(m.group(1)))
        if num not in by_number:
            missing += 1
            continue
        _, expr = by_number[num]
        expr_str = expr.to_str().replace("TRUE AND ", "").replace("(TRUE AND ", "(")
        # Keep explicit unconditional transitions as "(TRUE)" so the generator doesn't
        # inject a fallback Transitions.TR operand for an otherwise empty condition.
        tr["guard_expression"] = "(TRUE)" if expr_str.strip().upper() == "TRUE" else expr_str
        tr["guard_operands"] = sorted(o for o in expr.operands() if o not in {"TRUE"})
        patched += 1

        for op in tr["guard_operands"]:
            if op == "TRUE":
                continue
            if op == "GT_COND":
                _ensure_operand(ir, op, category="transitions", datatype="Bool")
            elif op.startswith("DB") or op.startswith("I") or op.startswith("Q"):
                _ensure_operand(ir, op, category="external", datatype="Bool")
            else:
                _ensure_operand(ir, op, category="db", datatype="Bool")

    summary = {
        "patched_transitions": patched,
        "missing_in_expected": missing,
        "expected_transitions_parsed": len(by_number),
    }
    print(json.dumps(summary, indent=2))

    if not args.dry_run:
        ir_path.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Updated {ir_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
