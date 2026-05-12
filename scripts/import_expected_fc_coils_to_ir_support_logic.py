from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass

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


@dataclass(frozen=True)
class Expr:
    kind: str
    value: str | None = None
    items: tuple["Expr", ...] = ()

    def operands(self) -> set[str]:
        if self.kind == "var" and self.value:
            if str(self.value).startswith("#"):
                return set()
            return {self.value}
        if self.kind == "cmp" and self.value:
            # value is "OP|lhs|rhs"
            parts = self.value.split("|", 2)
            if len(parts) == 3:
                _, lhs, rhs = parts
                acc: set[str] = set()
                if lhs and not lhs.startswith("#"):
                    acc.add(lhs)
                if rhs and not rhs.startswith("#"):
                    acc.add(rhs)
                return acc
        acc: set[str] = set()
        for it in self.items:
            acc |= it.operands()
        return acc

    def to_str(self) -> str:
        if self.kind == "var":
            val = str(self.value)
            return val[1:] if val.startswith("#") else val
        if self.kind == "cmp" and self.value:
            op, lhs, rhs = (self.value.split("|", 2) + ["", "", ""])[:3]
            op = op.upper()
            symbol = {"EQ": "==", "NE": "<>", "GT": ">", "GE": ">=", "LT": "<", "LE": "<="}.get(op, "==")
            if not lhs:
                lhs = "UNKNOWN"
            if not rhs:
                rhs = "UNKNOWN"
            if lhs.startswith("#"):
                lhs = lhs[1:]
            if rhs.startswith("#"):
                rhs = rhs[1:]
            return f"({lhs} {symbol} {rhs})"
        if self.kind == "not":
            return f"NOT ({self.items[0].to_str()})"
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


_SAN_RE = re.compile(r"[^0-9A-Za-z_]+")


def sanitize_component(name: str) -> str:
    name = name.replace(":", "_").replace(" ", "_").replace("-", "_").replace("/", "_")
    name = _SAN_RE.sub("_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def symbol_to_operand(components: list[str]) -> str:
    if not components:
        return "UNKNOWN"
    return ".".join(sanitize_component(c) for c in components if c.strip())


def _expr_and(a: Expr, b: Expr) -> Expr:
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
        return Expr("var", value="TRUE")
    if len(flat) == 1:
        return flat[0]
    return Expr("or", items=tuple(flat))


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FLGNET_NS = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
FNS = {"f": FLGNET_NS}


def _collect_multilang_text_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    # Prefer en-US, fallback to first.
    items = node.findall(".//MultilingualTextItem")
    for it in items:
        culture = (it.findtext("./AttributeList/Culture") or "").strip()
        text = (it.findtext("./AttributeList/Text") or "").strip()
        if culture.lower() == "en-us" and text:
            return text
    for it in items:
        text = (it.findtext("./AttributeList/Text") or "").strip()
        if text:
            return text
    return ""


def _extract_operand_from_access(acc: ET.Element) -> str:
    scope = (acc.attrib.get("Scope") or "").strip()
    if scope in {"LiteralConstant", "TypedConstant"}:
        const_value = (acc.findtext(".//f:ConstantValue", namespaces=FNS) or "").strip()
        const_type = (acc.findtext(".//f:ConstantType", namespaces=FNS) or "").strip()
        if const_value:
            return f"#{const_type}:{const_value}" if const_type else f"#{const_value}"
    comps = [c.attrib.get("Name", "") for c in acc.findall(".//f:Component", FNS)]
    return symbol_to_operand(comps)


def parse_flgnet_coil_rows(flgnet: ET.Element) -> list[dict[str, object]]:
    # Access UId -> operand token.
    access_operands: dict[str, str] = {}
    for acc in flgnet.findall(".//f:Access", FNS):
        uid = acc.attrib.get("UId")
        if not uid:
            continue
        access_operands[uid] = _extract_operand_from_access(acc)

    # Part types and negations (for contacts only).
    part_name: dict[str, str] = {}
    contact_negated: set[str] = set()
    or_card: dict[str, int] = {}
    for part in flgnet.findall(".//f:Part", FNS):
        uid = part.attrib.get("UId")
        name = part.attrib.get("Name")
        if not uid or not name:
            continue
        part_name[uid] = name
        if name == "Contact" and list(part.findall(".//f:Negated", FNS)):
            contact_negated.add(uid)
        if name == "O":
            tv = part.find("./f:TemplateValue[@Name='Card']", FNS)
            if tv is not None and (tv.text or "").strip().isdigit():
                or_card[uid] = int((tv.text or "").strip())

    # DSU nets from wires.
    dsu = DSU()

    def endpoint_id(tag: str, uid: str | None = None, name: str | None = None) -> str:
        if tag == "Powerrail":
            return "Powerrail"
        if tag == "NameCon":
            return f"NameCon:{uid}:{name}"
        if tag == "IdentCon":
            return f"IdentCon:{uid}"
        return f"Unknown:{tag}:{uid}:{name}"

    for w in flgnet.findall(".//f:Wire", FNS):
        endpoints: list[str] = []
        for child in list(w):
            local = child.tag.split("}")[-1]
            if local == "Powerrail":
                endpoints.append(endpoint_id("Powerrail"))
            elif local == "NameCon":
                endpoints.append(endpoint_id("NameCon", uid=child.attrib.get("UId"), name=child.attrib.get("Name")))
            elif local == "IdentCon":
                endpoints.append(endpoint_id("IdentCon", uid=child.attrib.get("UId")))
        if len(endpoints) >= 2:
            first = endpoints[0]
            for e in endpoints[1:]:
                dsu.union(first, e)

    def net_of_namecon(uid: str, name: str) -> str:
        return dsu.find(endpoint_id("NameCon", uid=uid, name=name))

    def net_of_namecon_if_exists(uid: str, name: str) -> str | None:
        eid = endpoint_id("NameCon", uid=uid, name=name)
        if eid not in dsu.parent:
            return None
        return dsu.find(eid)

    def net_of_identcon(uid: str) -> str:
        return dsu.find(endpoint_id("IdentCon", uid=uid))

    power_net = dsu.find("Powerrail")
    expr_at_net: dict[str, Expr] = {power_net: Expr("var", value="TRUE")}
    # Store IdentCon operands by net for comparator input capture.
    operand_at_net: dict[str, str] = {}
    for acc_uid, op in access_operands.items():
        operand_at_net[net_of_identcon(acc_uid)] = op

    # Evaluate: contacts (series AND), OR gates, and selected function blocks.
    changed = True
    for _ in range(80):
        if not changed:
            break
        changed = False

        for uid, name in part_name.items():
            if name != "Contact":
                continue
            in_net = net_of_namecon(uid, "in")
            out_net = net_of_namecon(uid, "out")
            op_net = net_of_namecon(uid, "operand")
            if in_net not in expr_at_net:
                continue
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

        for uid, name in part_name.items():
            if name != "O":
                continue
            in_terms: list[Expr] = []
            for idx in range(1, (or_card.get(uid, 2) + 1)):
                in_net = net_of_namecon_if_exists(uid, f"in{idx}")
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

        # Timers: treat Q as the boolean condition at IN (enable is implicit in FlgNet wiring).
        for uid, name in part_name.items():
            if name not in {"TON", "TOF", "TP"}:
                continue
            in_net = net_of_namecon_if_exists(uid, "IN")
            out_q = net_of_namecon_if_exists(uid, "Q")
            if in_net is None or out_q is None:
                continue
            if in_net not in expr_at_net:
                continue
            new_expr = expr_at_net[in_net]
            if expr_at_net.get(out_q) != new_expr:
                expr_at_net[out_q] = new_expr
                changed = True

        # MOVE blocks: treat ENO as the boolean enable at EN.
        for uid, name in part_name.items():
            if name != "Move":
                continue
            en_net = net_of_namecon_if_exists(uid, "en")
            eno_net = net_of_namecon_if_exists(uid, "eno")
            if en_net is None or eno_net is None:
                continue
            if en_net not in expr_at_net:
                continue
            new_expr = expr_at_net[en_net]
            if expr_at_net.get(eno_net) != new_expr:
                expr_at_net[eno_net] = new_expr
                changed = True

        # PBox (pulse/edge helper): treat OUT as IN for boolean gating purposes.
        for uid, name in part_name.items():
            if name != "PBox":
                continue
            in_net = net_of_namecon_if_exists(uid, "in")
            out_net = net_of_namecon_if_exists(uid, "out")
            if in_net is None or out_net is None:
                continue
            if in_net not in expr_at_net:
                continue
            new_expr = expr_at_net[in_net]
            if expr_at_net.get(out_net) != new_expr:
                expr_at_net[out_net] = new_expr
                changed = True

        # SR latch: approximate q as (operand OR s), and ignore resets for gating.
        # This avoids generating unconditional coils when the FlgNet uses SR blocks.
        for uid, name in part_name.items():
            if name not in {"Sr", "RS", "SR"}:
                continue
            q_net = net_of_namecon_if_exists(uid, "q")
            s_net = net_of_namecon_if_exists(uid, "s")
            op_net = net_of_namecon_if_exists(uid, "operand")
            if q_net is None or s_net is None or op_net is None:
                continue
            if s_net not in expr_at_net:
                continue
            operand_token = operand_at_net.get(op_net)
            if not operand_token:
                continue
            new_expr = _expr_or([Expr("var", value=operand_token), expr_at_net[s_net]])
            if expr_at_net.get(q_net) != new_expr:
                expr_at_net[q_net] = new_expr
                changed = True

        # Comparators / numeric predicate blocks: we don't model the numeric comparison yet.
        # These blocks produce a boolean output from (pre AND comparison(in1,in2)).
        # If we ignore them completely, downstream coils become unconditional (TRUE).
        for uid, name in part_name.items():
            if name not in {"Eq", "Ne", "Gt", "Ge", "Lt", "Le"}:
                continue
            pre_net = net_of_namecon_if_exists(uid, "pre")
            out_net = net_of_namecon_if_exists(uid, "out")
            in1_net = net_of_namecon_if_exists(uid, "in1")
            in2_net = net_of_namecon_if_exists(uid, "in2")
            if pre_net is None or out_net is None or in1_net is None or in2_net is None:
                continue
            if pre_net not in expr_at_net:
                continue
            lhs = operand_at_net.get(in1_net, "")
            rhs = operand_at_net.get(in2_net, "")
            cmp = Expr("cmp", value=f"{name.upper()}|{lhs}|{rhs}")
            new_expr = _expr_and(expr_at_net[pre_net], cmp)
            if expr_at_net.get(out_net) != new_expr:
                expr_at_net[out_net] = new_expr
                changed = True

    # Extract coil writes: Coil/SCoil/RCoil
    rows: list[dict[str, object]] = []
    for coil_uid, name in part_name.items():
        if name not in {"Coil", "SCoil", "RCoil"}:
            continue
        in_net = net_of_namecon(coil_uid, "in")
        op_net = net_of_namecon(coil_uid, "operand")
        expr = expr_at_net.get(in_net, Expr("var", value="TRUE"))

        target: str | None = None
        for acc_uid, op in access_operands.items():
            if net_of_identcon(acc_uid) == op_net:
                target = op
                break
        if not target:
            continue

        # If the boolean is gated by a comparator, capture it explicitly so the generator can
        # re-create the expected LAD (Eq/Ne/Gt/Ge/Lt/Le) instead of falling back to contacts.
        cmp_expr: Expr | None = None
        pre_expr: Expr | None = None
        if expr.kind == "cmp":
            cmp_expr = expr
            pre_expr = Expr("var", value="TRUE")
        elif expr.kind == "and":
            cmp_terms = [it for it in expr.items if it.kind == "cmp"]
            if len(cmp_terms) == 1:
                cmp_expr = cmp_terms[0]
                others = [it for it in expr.items if it is not cmp_expr]
                pre_expr = Expr("var", value="TRUE")
                for it in others:
                    pre_expr = _expr_and(pre_expr, it)

        expr_str = expr.to_str().replace("TRUE AND ", "").replace("(TRUE AND ", "(").strip()
        if expr_str.upper() == "TRUE":
            expr_str = "(TRUE)"
        operands = sorted(o for o in expr.operands() if o and o != "TRUE")
        coil_mode = "set" if name == "SCoil" else "reset" if name == "RCoil" else ""
        row: dict[str, object] = {
            "result_member": target,
            "condition_expression": expr_str,
            "condition_operands": operands,
            "coil_mode": coil_mode,
        }
        if cmp_expr is not None and pre_expr is not None and cmp_expr.value:
            op, lhs, rhs = (cmp_expr.value.split("|", 2) + ["", "", ""])[:3]
            row["kind"] = "compare"
            row["compare_op"] = op.upper()
            row["compare_lhs"] = lhs
            row["compare_rhs"] = rhs
            pre_str = pre_expr.to_str().replace("TRUE AND ", "").replace("(TRUE AND ", "(").strip()
            if pre_str.upper() == "TRUE":
                pre_str = "(TRUE)"
            row["pre_expression"] = pre_str
            row["pre_operands"] = sorted(o for o in pre_expr.operands() if o and o != "TRUE")
        rows.append(row)
    return rows


def _guess_category_for_symbol(symbol: str) -> str:
    top = (symbol.split(".", 1)[0] if symbol else "").upper()
    if top.endswith("_HMI") or "HMI" in top:
        return "hmi"
    if "LEV2" in top:
        return "lev2"
    if top.startswith("DB") or top.startswith("I") or top.startswith("Q"):
        return "external"
    if "MEMORY" in symbol.upper() or ".MEMORY." in symbol.upper():
        return "aux"
    return "output"


def main() -> int:
    ap = argparse.ArgumentParser(description="Import Coil/SCoil/RCoil networks from an expected FC XML into IR support_logic.")
    ap.add_argument("--ir-json", required=True, help="IR json to patch in-place.")
    ap.add_argument("--expected-fc-xml", required=True, help="Expected FC XML (LAD) containing FlgNet networks.")
    ap.add_argument("--category", default="output", help="support_logic.category to set for imported rows (default: output).")
    ap.add_argument("--start-network-index", type=int, default=20000, help="Base network_index for imported rows.")
    ap.add_argument(
        "--purge-from-index",
        action="store_true",
        help="Before importing, remove existing support_logic rows for the same category with network_index >= start-network-index.",
    )
    args = ap.parse_args()

    ir_path = (PROJECT_ROOT / args.ir_json).resolve()
    fc_path = (PROJECT_ROOT / args.expected_fc_xml).resolve()
    ir = json.loads(ir_path.read_text(encoding="utf-8"))
    if args.purge_from_index:
        cat = str(args.category).strip().lower()
        base = int(args.start_network_index)
        kept = []
        removed = 0
        for row in ir.get("support_logic", []) or []:
            rcat = str(row.get("category") or "").strip().lower()
            idx = int(row.get("network_index") or 0)
            if rcat == cat and idx >= base:
                removed += 1
                continue
            kept.append(row)
        ir["support_logic"] = kept
        print(json.dumps({"purged_rows": removed, "category": cat, "from_index": base}, indent=2))
    xml_text = fc_path.read_text(encoding="utf-8-sig")
    root = ET.fromstring(xml_text)

    compile_units = root.findall(".//SW.Blocks.CompileUnit")
    imported = 0
    next_index = int(args.start_network_index)

    for cu in compile_units:
        title = _collect_multilang_text_text(cu.find("./ObjectList/MultilingualText[@CompositionName='Title']"))
        flgnet = cu.find(".//f:FlgNet", FNS)
        if flgnet is None:
            continue
        base_network_index = next_index
        for row in parse_flgnet_coil_rows(flgnet):
            row["category"] = str(args.category)
            row.setdefault("network_title", title)
            row.setdefault("comment", "")
            # Keep all rows from the same CompileUnit grouped under the same network_index
            # so the generator can merge them into a single CompileUnit, mirroring TIA exports.
            row.setdefault("network_index", base_network_index)
            ir.setdefault("support_logic", []).append(row)
            imported += 1

            # Ensure operand metadata exists for target + operands.
            for token in [row["result_member"], *list(row.get("condition_operands") or [])]:
                tok = str(token or "").strip()
                if not tok or tok.upper() in {"TRUE", "FALSE"}:
                    continue
                ir.setdefault("operand_datatypes", {}).setdefault(tok, "Bool")
                ir.setdefault("operand_categories", {}).setdefault(tok, _guess_category_for_symbol(tok))
                if tok not in ir.setdefault("operand_catalog", []):
                    ir["operand_catalog"].append(tok)

        # advance to next compile unit index
        if flgnet is not None:
            next_index += 1

    ir_path.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"imported_rows": imported, "next_network_index": next_index}, indent=2))
    print(f"[OK] Updated {ir_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
