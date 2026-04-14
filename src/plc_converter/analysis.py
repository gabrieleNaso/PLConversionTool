from __future__ import annotations

import re
import hashlib
from xml.sax.saxutils import escape

from .domain import (
    ArtifactPreview,
    AwlIR,
    AwlInstruction,
    AwlNetwork,
    ConversionAnalysis,
    GraphBranchNode,
    FaultCandidate,
    GraphConnection,
    GraphStepNode,
    GraphTopology,
    GraphTransitionNode,
    MemberIR,
    MemoryCandidate,
    OutputCandidate,
    StepCandidate,
    TimerCandidate,
    TransitionCandidate,
    ValidationIssue,
)
from .scaffold import build_conversion_scaffold, build_target_profile


STEP_RE = re.compile(r"\bS\d+\b", re.IGNORECASE)
TIMER_RE = re.compile(r"\bT\d+\b", re.IGNORECASE)
PRESET_RE = re.compile(r"\bS5T#[^\s,;]+", re.IGNORECASE)
MEMORY_RE = re.compile(r"\bM\d+(?:\.\d+)?\b", re.IGNORECASE)
OUTPUT_RE = re.compile(r"\bA\d+(?:\.\d+)?\b", re.IGNORECASE)
EXTERNAL_RE = re.compile(r"\b(?:E|I|DB|DI|PE|PA)\w*(?:\.\w+)*\b", re.IGNORECASE)
TOKEN_RE = re.compile(r"\b[A-Z_]\w*(?:\.\w+)*\b", re.IGNORECASE)
CONDITION_OPCODES = {"U", "UN", "O", "ON", "A", "AN", "X", "XN"}
ACTION_OPCODES = {"S", "R", "="}
JUMP_OPCODES = {"JC", "JCN", "JU"}
TIMER_OPCODES = {"SD", "SE", "SP", "SS", "SF"}
SUPPORT_BLOCK_SCHEMA = {
    "io": {"token": "IO", "file_token": "io"},
    "diag": {"token": "DIAG", "file_token": "diag"},
    "mode": {"token": "MODE", "file_token": "mode"},
    "network": {"token": "N", "file_token": "n"},
    "hmi": {"token": "HMI", "file_token": "hmi"},
    "aux": {"token": "AUX", "file_token": "aux"},
    "transitions": {"token": "TRANSITIONS", "file_token": "transitions"},
    "output": {"token": "OUTPUT", "file_token": "output"},
}

DB_FAMILY_PREFIX = {
    "base": "DB11",
    "sequence": "DB12",
    "ext": "DB18",
    "aux": "DB19",
    "hmi": "DB_HMI",
}

FC_FAMILY_PREFIX = {
    "hmi": "FC02",
    "aux": "FC03",
    "transitions": "FC04",
    "output": "FC06",
}

DB_FAMILY_NUMBER_BASE = {
    "base": 1100,
    "sequence": 1200,
    "ext": 1800,
    "aux": 1900,
    "hmi": 1700,
}

FC_FAMILY_NUMBER_BASE = {
    "hmi": 200,
    "aux": 300,
    "transitions": 400,
    "output": 600,
}

SUPPORT_FAMILY_OVERRIDES = {
    "hmi": {"db_family": "hmi", "fc_family": "hmi"},
    "aux": {"db_family": "aux", "fc_family": "aux"},
    "transitions": {"db_family": "sequence", "fc_family": "transitions"},
    "output": {"db_family": "sequence", "fc_family": "output"},
}


def analyze_awl_source(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
) -> ConversionAnalysis:
    awl_source = _normalize_awl_source(awl_source)
    scaffold = build_conversion_scaffold(
        sequence_name=sequence_name,
        awl_source=awl_source,
        source_name=source_name,
    )
    source_label = source_name or f"{scaffold.sequence_name}.awl"
    networks = _parse_networks(awl_source)
    ir = _build_ir(scaffold.sequence_name, source_label, networks)
    graph_topology = _build_graph_topology(ir)
    issues = _validate_ir(ir, graph_topology)
    previews = _build_artifact_previews(scaffold, ir, graph_topology)
    manifest = _build_artifact_manifest(previews)
    return ConversionAnalysis(
        scaffold=scaffold,
        ir=ir,
        graph_topology=graph_topology,
        validation_issues=issues,
        artifact_previews=previews,
        artifact_manifest=manifest,
    )


def _normalize_awl_source(awl_source: str) -> str:
    if "```" not in awl_source:
        return awl_source

    blocks = _extract_markdown_awl_blocks(awl_source)
    if not blocks:
        return awl_source

    normalized_blocks: list[str] = []
    for index, block in enumerate(blocks, start=1):
        cleaned_block = block.strip()
        if not cleaned_block:
            continue
        if re.search(r"^\s*NETWORK\b", cleaned_block, flags=re.IGNORECASE | re.MULTILINE):
            normalized_blocks.append(cleaned_block)
            continue
        normalized_blocks.append(f"NETWORK {index}\n{cleaned_block}")

    if not normalized_blocks:
        return awl_source
    return "\n\n".join(normalized_blocks).strip() + "\n"


def _extract_markdown_awl_blocks(raw_text: str) -> list[str]:
    pattern = re.compile(r"```(?:awl|il|stl|text)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)
    matches = [match.group(1) for match in pattern.finditer(raw_text)]
    if not matches:
        return []

    awl_like_blocks = [block for block in matches if _looks_like_awl_block(block)]
    return awl_like_blocks or matches


def _looks_like_awl_block(block: str) -> bool:
    heuristics = (
        r"\bNETWORK\b",
        r"^\s*(A|AN|O|ON|U|UN|=|S|R|L|T|SD|SE|SP|SS|SF|JC|JCN|JU)\b",
        r"\bS5T#",
        r"\bDB\d+\.",
        r"\b[QAEIM]\d+\.\d+\b",
    )
    return any(
        re.search(pattern, block, flags=re.IGNORECASE | re.MULTILINE)
        for pattern in heuristics
    )


def _parse_networks(awl_source: str) -> list[AwlNetwork]:
    lines = awl_source.splitlines()
    networks: list[AwlNetwork] = []
    current: list[str] = []
    current_title: str | None = None
    current_index = 1
    def flush() -> None:
        nonlocal current, current_title, current_index
        if not current:
            return
        networks.append(
            AwlNetwork(
                index=current_index,
                title=current_title,
                raw_lines=current,
                instructions=_parse_instructions(current, current_index),
            )
        )
        current = []
        current_title = None
        current_index += 1

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.upper().startswith("NETWORK"):
            flush()
            title = stripped[len("NETWORK") :].strip(" :\t")
            current_title = title or None
            continue
        current.append(raw_line)

    flush()

    if not networks and awl_source.strip():
        networks.append(
            AwlNetwork(
                index=1,
                title=None,
                raw_lines=[line for line in lines if line.strip()],
                instructions=_parse_instructions([line for line in lines if line.strip()], 1),
            )
        )
    return networks


def _parse_instructions(lines: list[str], network_index: int) -> list[AwlInstruction]:
    instructions: list[AwlInstruction] = []
    for offset, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        label: str | None = None
        body = stripped
        if ":" in stripped:
            possible_label, remainder = stripped.split(":", 1)
            if possible_label and " " not in possible_label:
                label = possible_label.strip()
                body = remainder.strip() or "NOP 0"

        parts = body.split()
        if not parts:
            continue

        opcode = parts[0].upper()
        args = parts[1:]
        instructions.append(
            AwlInstruction(
                line_no=offset,
                network_index=network_index,
                label=label,
                opcode=opcode,
                args=args,
                raw=stripped,
            )
        )
    return instructions


def _build_ir(sequence_name: str, source_name: str, networks: list[AwlNetwork]) -> AwlIR:
    step_map: dict[str, StepCandidate] = {}
    transitions: list[TransitionCandidate] = []
    timers: list[TimerCandidate] = []
    memories: dict[tuple[str, int], MemoryCandidate] = {}
    faults: dict[tuple[str, int], FaultCandidate] = {}
    outputs: dict[tuple[str, int], OutputCandidate] = {}
    manual_logic_networks: list[int] = []
    auto_logic_networks: list[int] = []
    external_refs: set[str] = set()

    for network in networks:
        step_refs = sorted(_collect_matches(network, STEP_RE))
        condition_operands = _collect_condition_operands(network)
        jump_labels = [instr.args[0] for instr in network.instructions if instr.opcode in JUMP_OPCODES and instr.args]
        step_targets = _collect_step_targets(network)
        pattern_transitions = _collect_transition_patterns(network)

        for step_name in step_refs:
            step_map.setdefault(step_name, StepCandidate(name=step_name)).source_networks.append(network.index)

        for target in step_targets:
            candidate = step_map.setdefault(target, StepCandidate(name=target))
            candidate.activation_networks.append(network.index)

        if step_refs and (_collect_output_targets(network) or _collect_memory_targets(network)):
            for step_name in step_refs:
                step_map.setdefault(step_name, StepCandidate(name=step_name)).action_networks.append(
                    network.index
                )

        if pattern_transitions:
            for source_step, target, guard_ops, pattern_jump_labels in pattern_transitions:
                if target == source_step:
                    continue
                transitions.append(
                    TransitionCandidate(
                        transition_id=f"T{len(transitions) + 1}",
                        source_step=source_step,
                        target_step=target,
                        network_index=network.index,
                        guard_expression=" AND ".join(guard_ops) if guard_ops else "TRUE",
                        guard_operands=guard_ops,
                        jump_labels=pattern_jump_labels,
                    )
                )
        else:
            for target in step_targets:
                for source_step in step_refs:
                    if target == source_step:
                        continue
                    transitions.append(
                        TransitionCandidate(
                            transition_id=f"T{len(transitions) + 1}",
                            source_step=source_step,
                            target_step=target,
                            network_index=network.index,
                            guard_expression=" AND ".join(condition_operands) if condition_operands else "TRUE",
                            guard_operands=condition_operands,
                            jump_labels=jump_labels,
                        )
                    )

        for timer_name, timer_kind, preset in _collect_timers(network):
            timers.append(
                TimerCandidate(
                    source_timer=timer_name,
                    network_index=network.index,
                    kind=timer_kind,
                    preset=preset,
                    trigger_operands=condition_operands,
                )
            )

        for memory_name in _collect_matches(network, MEMORY_RE):
            memories[(memory_name, network.index)] = MemoryCandidate(
                name=memory_name,
                role=_classify_memory_role(network),
                network_index=network.index,
            )

        for output_name, action in _collect_output_targets(network):
            outputs[(output_name, network.index)] = OutputCandidate(
                name=output_name,
                network_index=network.index,
                action=action,
            )

        for token in _collect_fault_tokens(network):
            faults[(token, network.index)] = FaultCandidate(
                name=token,
                network_index=network.index,
                evidence=_first_matching_line(network, token),
            )

        if _network_has_keyword(network, ("man", "manual")):
            manual_logic_networks.append(network.index)
        if _network_has_keyword(network, ("auto", "automatic")):
            auto_logic_networks.append(network.index)

        external_refs.update(_collect_matches(network, EXTERNAL_RE))

    if not transitions:
        transitions = _build_network_pattern_transitions(step_map, networks)

    for reserved_step in ("S1", "S29", "S30", "S32"):
        step_map.setdefault(reserved_step, StepCandidate(name=reserved_step))

    assumptions = [
        "Il parser usa euristiche incrementali sui pattern AWL piu' frequenti.",
        "Le transizioni vengono dedotte da step letti nello stesso network e step attivati tramite S/=.",
        "Se il sorgente non contiene step Sxx sufficienti, viene applicato un fallback sequenziale per network.",
        "Il bundle XML generato e' una baseline strutturale iniziale, non ancora un serializer TIA completo.",
    ]

    return AwlIR(
        sequence_name=sequence_name,
        source_name=source_name,
        networks=networks,
        steps=_dedupe_step_networks(step_map),
        transitions=transitions,
        timers=timers,
        memories=sorted(memories.values(), key=lambda item: (item.name, item.network_index)),
        faults=sorted(faults.values(), key=lambda item: (item.name, item.network_index)),
        outputs=sorted(outputs.values(), key=lambda item: (item.name, item.network_index)),
        manual_logic_networks=manual_logic_networks,
        auto_logic_networks=auto_logic_networks,
        external_refs=sorted(external_refs),
        assumptions=assumptions,
    )


def _build_network_pattern_transitions(
    step_map: dict[str, StepCandidate],
    networks: list[AwlNetwork],
) -> list[TransitionCandidate]:
    meaningful = [network for network in networks if _network_is_transition_candidate(network)]
    if len(meaningful) < 2:
        return []

    label_to_network: dict[str, int] = {}
    for network in meaningful:
        for instr in network.instructions:
            if instr.label:
                label_to_network[instr.label.upper()] = network.index

    ordered_step_names: list[str] = []
    step_by_network: dict[int, str] = {}
    for network in meaningful:
        step_name = f"N{network.index}"
        candidate = step_map.setdefault(step_name, StepCandidate(name=step_name))
        candidate.source_networks.append(network.index)
        candidate.activation_networks.append(network.index)
        ordered_step_names.append(step_name)
        step_by_network[network.index] = step_name

    transitions: list[TransitionCandidate] = []
    for index, source_network in enumerate(meaningful):
        source_step = step_by_network[source_network.index]
        operands = _collect_condition_operands(source_network)
        guard_expression = " AND ".join(operands) if operands else "TRUE"
        successors: list[int] = []

        # Structural default: flow continues to next meaningful network.
        if index + 1 < len(meaningful):
            successors.append(meaningful[index + 1].index)

        # Semantic jump flow: when labels are available, wire explicit jump targets.
        for instr in source_network.instructions:
            if instr.opcode not in JUMP_OPCODES or not instr.args:
                continue
            label = _normalize_operand_token(instr.args[0])
            if not label:
                continue
            target_network = label_to_network.get(label)
            if target_network is not None:
                successors.append(target_network)

        for target_network_index in dict.fromkeys(successors):
            target_step = step_by_network.get(target_network_index)
            if not target_step or target_step == source_step:
                continue
            transitions.append(
                TransitionCandidate(
                    transition_id=f"T_NET_{source_network.index}_{target_network_index}",
                    source_step=source_step,
                    target_step=target_step,
                    network_index=source_network.index,
                    guard_expression=guard_expression,
                    guard_operands=operands,
                    jump_labels=[
                        _normalize_operand_token(instr.args[0])
                        for instr in source_network.instructions
                        if instr.opcode in JUMP_OPCODES and instr.args
                    ],
                )
            )

    return transitions


def _network_is_transition_candidate(network: AwlNetwork) -> bool:
    if any(instr.opcode in ACTION_OPCODES | CONDITION_OPCODES | TIMER_OPCODES for instr in network.instructions):
        return True
    return bool(_collect_output_targets(network) or _collect_memory_targets(network))


def _build_graph_topology(ir: AwlIR) -> GraphTopology:
    ordered_steps = sorted(ir.steps, key=lambda item: _step_sort_key(item.name))
    if not ordered_steps:
        return GraphTopology(
            step_nodes=[],
            transition_nodes=[],
            branch_nodes=[],
            connections=[],
            entry_step=None,
            terminal_steps=[],
            warnings=["Nessun passo disponibile per costruire il GRAPH target."],
        )

    transition_targets = {transition.target_step for transition in ir.transitions}
    entry_step = None
    for step in ordered_steps:
        if step.name not in transition_targets:
            entry_step = step.name
            break
    if entry_step is None:
        entry_step = ordered_steps[0].name
    for step in ordered_steps:
        if step.name.lower() == "s1":
            entry_step = step.name
            break

    transition_nodes = [
        GraphTransitionNode(
            name=transition.transition_id,
            transition_no=index + 1,
            source_step=transition.source_step,
            target_step=transition.target_step,
            guard_expression=transition.guard_expression,
            guard_operands=transition.guard_operands,
            network_index=transition.network_index,
            db_block_name=_global_db_block_name(ir),
            db_member_name=_transition_db_member_name(transition),
        )
        for index, transition in enumerate(ir.transitions)
    ]
    next_synthetic_network = (
        max((transition.network_index for transition in transition_nodes if transition.network_index), default=0)
        + 1
    )

    branch_nodes: list[GraphBranchNode] = []
    next_branch_no = 1
    next_transition_no = len(transition_nodes) + 1

    all_steps = list(ordered_steps)
    reserved_step_numbers = {1, 29, 30, 32}
    reserved_step_names = {f"S{num}" for num in reserved_step_numbers}
    used_step_numbers: set[int] = set()
    step_nodes: list[GraphStepNode] = []
    next_sequential = 1

    for step in all_steps:
        if step.name in reserved_step_names:
            step_no = int(step.name[1:])
        else:
            while next_sequential in used_step_numbers or next_sequential in reserved_step_numbers:
                next_sequential += 1
            step_no = next_sequential
            next_sequential += 1

        if step_no in used_step_numbers:
            candidate = 1
            while candidate in used_step_numbers or candidate in reserved_step_numbers:
                candidate += 1
            step_no = candidate
        used_step_numbers.add(step_no)

        step_nodes.append(
            GraphStepNode(
                name=step.name,
                step_no=step_no,
                init=step.name == entry_step,
                source_step=step.name,
                action_networks=step.action_networks,
            )
        )
    step_no_by_name = {step.name: step.step_no for step in step_nodes}

    # GRAPH rejects terminal steps without a following element.
    # Add a deterministic hold transition so terminal steps remain valid
    # without changing the nominal process flow.
    outgoing_from_ir: dict[str, int] = {}
    for transition in transition_nodes:
        outgoing_from_ir[transition.source_step] = outgoing_from_ir.get(transition.source_step, 0) + 1

    for step in ordered_steps:
        if outgoing_from_ir.get(step.name, 0) > 0:
            continue
        if step.name == entry_step and len(ordered_steps) == 1:
            continue
        synthetic_name = f"T_HOLD_{step.name}"
        transition_nodes.append(
            GraphTransitionNode(
                name=synthetic_name,
                transition_no=next_transition_no,
                source_step=step.name,
                # Keep terminal steps topologically closed without introducing
                # self-loop incoming edges that can destabilize GRAPH editing.
                target_step=entry_step,
                guard_expression="FALSE",
                guard_operands=[],
                network_index=next_synthetic_network,
                db_block_name=_global_db_block_name(ir),
                db_member_name=_transition_db_member_name_from_values(synthetic_name, "FALSE"),
            )
        )
        next_transition_no += 1
        next_synthetic_network += 1

    reserved_chain = ["S29", "S30", "S32"]
    present_reserved = [name for name in reserved_chain if name in step_no_by_name]
    if present_reserved:
        existing_incoming = {transition.target_step for transition in transition_nodes}
        first_reserved = present_reserved[0]
        if first_reserved not in existing_incoming and first_reserved != entry_step:
            transition_name = f"T_CHAIN_{entry_step}_TO_{first_reserved}"
            transition_nodes.append(
                GraphTransitionNode(
                    name=transition_name,
                    transition_no=next_transition_no,
                    source_step=entry_step,
                    target_step=first_reserved,
                    guard_expression="FALSE",
                    guard_operands=[],
                    network_index=next_synthetic_network,
                    db_block_name=_global_db_block_name(ir),
                    db_member_name=_transition_db_member_name_from_values(transition_name, "FALSE"),
                )
            )
            next_transition_no += 1
            next_synthetic_network += 1
            existing_incoming.add(first_reserved)

        for prev_step, next_step in zip(present_reserved, present_reserved[1:]):
            if next_step in existing_incoming:
                continue
            transition_name = f"T_CHAIN_{prev_step}_TO_{next_step}"
            transition_nodes.append(
                GraphTransitionNode(
                    name=transition_name,
                    transition_no=next_transition_no,
                    source_step=prev_step,
                    target_step=next_step,
                    guard_expression="FALSE",
                    guard_operands=[],
                    network_index=next_synthetic_network,
                    db_block_name=_global_db_block_name(ir),
                    db_member_name=_transition_db_member_name_from_values(transition_name, "FALSE"),
                )
            )
            next_transition_no += 1
            next_synthetic_network += 1
            existing_incoming.add(next_step)

    transitions_by_source: dict[str, list[GraphTransitionNode]] = {}
    for transition in transition_nodes:
        transitions_by_source.setdefault(transition.source_step, []).append(transition)

    branch_by_source_step: dict[str, GraphBranchNode] = {}
    for source_step, items in transitions_by_source.items():
        if len(items) <= 1:
            continue
        branch = GraphBranchNode(
            name=f"B_{source_step}",
            branch_no=next_branch_no,
            branch_type="AltBegin",
            owner_step=source_step,
            incoming_refs=[source_step],
            outgoing_refs=[item.name for item in items],
        )
        next_branch_no += 1
        branch_nodes.append(branch)
        branch_by_source_step[source_step] = branch
    connections: list[GraphConnection] = []
    direct_incoming_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    for transition in transition_nodes:
        source_ref = transition.source_step
        if transition.source_step in branch_by_source_step:
            branch = branch_by_source_step[transition.source_step]
            if not any(
                connection.source_ref == branch.owner_step and connection.target_ref == branch.name
                for connection in connections
            ):
                connections.append(
                    GraphConnection(
                        source_ref=branch.owner_step,
                        target_ref=branch.name,
                        link_type="Direct",
                    )
                )
            source_ref = branch.name
        connections.append(
            GraphConnection(
                source_ref=source_ref,
                target_ref=transition.name,
                link_type="Direct",
            )
        )
        target_link_type = "Direct"
        has_direct_incoming = direct_incoming_counts.get(transition.target_step, 0) > 0
        if transition.target_step != entry_step and has_direct_incoming:
            target_link_type = "Jump"
        if (
            target_link_type == "Direct"
            and has_direct_incoming
            and step_no_by_name.get(transition.target_step, 10**9)
            <= step_no_by_name.get(transition.source_step, -1)
        ):
            target_link_type = "Jump"
        if target_link_type == "Direct":
            direct_incoming_counts[transition.target_step] = (
                direct_incoming_counts.get(transition.target_step, 0) + 1
            )
        connections.append(
            GraphConnection(
                source_ref=transition.name,
                target_ref=transition.target_step,
                link_type=target_link_type,
            )
        )

    warnings: list[str] = []
    outgoing_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    incoming_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    for transition in transition_nodes:
        outgoing_counts[transition.source_step] = outgoing_counts.get(transition.source_step, 0) + 1
        incoming_counts[transition.target_step] = incoming_counts.get(transition.target_step, 0) + 1

    for step_name, count in outgoing_counts.items():
        if count > 1 and step_name not in branch_by_source_step:
            warnings.append(
                f"Il passo {step_name} ha {count} uscite: servira' introdurre branch target dedicati."
            )

    for step_name, count in incoming_counts.items():
        if step_name != entry_step and count > 1:
            warnings.append(
                f"Il passo {step_name} riceve {count} ingressi: applicati Jump per evitare doppi Direct."
            )

    terminal_steps = [step.name for step in ordered_steps if outgoing_counts.get(step.name, 0) == 0]
    if len([step for step in step_nodes if step.init]) != 1:
        warnings.append("Il GRAPH target non ha un solo step iniziale determinato.")

    return GraphTopology(
        step_nodes=step_nodes,
        transition_nodes=transition_nodes,
        branch_nodes=branch_nodes,
        connections=connections,
        entry_step=entry_step,
        terminal_steps=terminal_steps,
        warnings=warnings,
    )


def _validate_ir(ir: AwlIR, graph_topology: GraphTopology) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not ir.networks:
        issues.append(
            ValidationIssue(
                level="error",
                code="NO_NETWORKS",
                message="Il sorgente AWL non contiene network o istruzioni analizzabili.",
            )
        )
    if not ir.steps:
        issues.append(
            ValidationIssue(
                level="warning",
                code="NO_STEPS",
                message="Nessun passo Sxx riconosciuto: il sequenziatore implicito non e' ancora ricostruibile.",
            )
        )
    if ir.steps and not ir.transitions:
        issues.append(
            ValidationIssue(
                level="warning",
                code="NO_TRANSITIONS",
                message="Sono stati trovati step ma nessuna transizione dedotta dai network correnti.",
            )
        )
    if not ir.outputs:
        issues.append(
            ValidationIssue(
                level="info",
                code="NO_OUTPUTS",
                message="Nessuna uscita Axx rilevata; il bundle FC/DB potrebbe restare minimale.",
            )
        )
    if not ir.manual_logic_networks:
        issues.append(
            ValidationIssue(
                level="info",
                code="NO_MANUAL_LOGIC",
                message="Nessuna rete con indizi di manuale trovata nel sorgente.",
            )
        )
    if not graph_topology.step_nodes:
        issues.append(
            ValidationIssue(
                level="error",
                code="NO_GRAPH_STEPS",
                message="Il mapper GRAPH non e' riuscito a produrre step target.",
            )
        )
    if ir.transitions and not graph_topology.connections:
        issues.append(
            ValidationIssue(
                level="error",
                code="NO_GRAPH_CONNECTIONS",
                message="Sono presenti transizioni IR ma nessuna connessione topologica GRAPH.",
            )
        )
    package_issues = _validate_package_coherence(ir, graph_topology)
    issues.extend(package_issues)
    issues.extend(_validate_operand_coherence(ir))
    for warning in graph_topology.warnings:
        issues.append(
            ValidationIssue(
                level="warning",
                code="GRAPH_TOPOLOGY_WARNING",
                message=warning,
            )
        )
    return issues


def _validate_package_coherence(ir: AwlIR, graph_topology: GraphTopology) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expected_db_name = _global_db_block_name(ir)
    transition_db_names = {item.db_block_name for item in graph_topology.transition_nodes}
    if transition_db_names and transition_db_names != {expected_db_name}:
        issues.append(
            ValidationIssue(
                level="error",
                code="PACKAGE_COHERENCE_ERROR",
                message=(
                    "Le transition GRAPH non referenziano tutte lo stesso GlobalDB del pacchetto."
                ),
                context=", ".join(sorted(transition_db_names)),
            )
        )

    db_members = _expected_global_db_member_names(ir, graph_topology)
    referenced_members = {item.db_member_name for item in graph_topology.transition_nodes}
    missing_members = sorted(referenced_members - db_members)
    if missing_members:
        issues.append(
            ValidationIssue(
                level="error",
                code="PACKAGE_COHERENCE_ERROR",
                message=(
                    "Il pacchetto referenzia member di guardia non dichiarati nel GlobalDB."
                ),
                context=", ".join(missing_members),
            )
        )

    stray_guard_members = sorted(
        member_name
        for member_name in db_members
        if "_Guard_" in member_name and member_name not in referenced_members
    )
    if stray_guard_members:
        issues.append(
            ValidationIssue(
                level="warning",
                code="PACKAGE_COHERENCE_WARNING",
                message=(
                    "Il GlobalDB contiene guard member che non risultano referenziati dal GRAPH corrente."
                ),
                context=", ".join(stray_guard_members),
            )
        )

    return issues


def _validate_operand_coherence(ir: AwlIR) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    bad_operands: set[str] = set()
    for transition in ir.transitions:
        for operand in transition.guard_operands:
            if not operand:
                continue
            if any(token in operand for token in ('"', "'", " ", ":", "-", ";")):
                bad_operands.add(operand)
    if bad_operands:
        issues.append(
            ValidationIssue(
                level="warning",
                code="OPERAND_NORMALIZATION_WARNING",
                message="Sono presenti operandi guard con token non canonici dopo il parsing.",
                context=", ".join(sorted(bad_operands)[:10]),
            )
        )

    if ir.transitions and all(item.transition_id.startswith("T_FALLBACK_") for item in ir.transitions):
        issues.append(
            ValidationIssue(
                level="warning",
                code="FALLBACK_TRANSITIONS_ONLY",
                message=(
                    "Le transizioni sono derivate solo via fallback sequenziale per network; "
                    "serve affinare il parser semantico per la logica AWL reale."
                ),
            )
        )
    return issues


def _stable_block_number(seed: str, base: int, span: int) -> int:
    if span <= 0:
        return base
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    value = int(digest[:8], 16)
    return base + (value % span)


def _build_artifact_previews(scaffold, ir: AwlIR, graph_topology: GraphTopology) -> list[ArtifactPreview]:
    profile = build_target_profile()
    graph_xml = _build_graph_fb_xml(profile, ir, graph_topology)
    db_xml = _build_global_db_xml(ir, graph_topology)
    fc_xml = _build_lad_fc_xml(ir, graph_topology)

    previews = [
        ArtifactPreview(
            artifact_type="graph_fb",
            file_name=scaffold.artifact_plan.graph_fb_name,
            content=graph_xml,
        ),
        ArtifactPreview(
            artifact_type="global_db",
            file_name=scaffold.artifact_plan.global_db_name,
            content=db_xml,
        ),
    ]
    previews.append(
        ArtifactPreview(
            artifact_type="lad_fc",
            file_name=scaffold.artifact_plan.lad_fc_name,
            content=fc_xml,
        )
    )
    previews.extend(_build_support_artifact_previews(ir))
    return previews


def _build_artifact_manifest(previews: list[ArtifactPreview]) -> dict[str, list[dict[str, str]]]:
    manifest: dict[str, list[dict[str, str]]] = {
        "baseline": [],
        "support_io": [],
        "support_diag": [],
        "support_mode": [],
        "support_network": [],
        "support_transitions": [],
        "support_output": [],
        "support_hmi": [],
        "support_aux": [],
        "other": [],
    }
    for preview in previews:
        item = {"artifactType": preview.artifact_type, "fileName": preview.file_name}
        if preview.artifact_type in {"graph_fb", "global_db", "lad_fc"}:
            manifest["baseline"].append(item)
        elif preview.artifact_type in {"support_global_db_io", "support_lad_fc_io"}:
            manifest["support_io"].append(item)
        elif preview.artifact_type in {"support_global_db_diag", "support_lad_fc_diag"}:
            manifest["support_diag"].append(item)
        elif preview.artifact_type in {"support_global_db_mode", "support_lad_fc_mode"}:
            manifest["support_mode"].append(item)
        elif preview.artifact_type in {"support_global_db_network", "support_lad_fc_network"}:
            manifest["support_network"].append(item)
        elif preview.artifact_type in {"support_global_db_transitions", "support_lad_fc_transitions"}:
            manifest["support_transitions"].append(item)
        elif preview.artifact_type in {"support_global_db_output", "support_lad_fc_output"}:
            manifest["support_output"].append(item)
        elif preview.artifact_type in {"support_global_db_hmi", "support_lad_fc_hmi"}:
            manifest["support_hmi"].append(item)
        elif preview.artifact_type in {"support_global_db_aux", "support_lad_fc_aux"}:
            manifest["support_aux"].append(item)
        else:
            manifest["other"].append(item)
    return manifest


def _build_support_artifact_previews(ir: AwlIR) -> list[ArtifactPreview]:
    previews: list[ArtifactPreview] = []

    io_members = _collect_io_support_members(ir)
    if io_members:
        (
            io_db_name,
            io_fc_name,
            io_db_file,
            io_fc_file,
            io_db_base,
            io_fc_base,
        ) = _support_block_names(ir.sequence_name, "io")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_io",
                file_name=io_db_file,
                content=_build_support_global_db_xml(
                    block_name=io_db_name,
                    title=f"{ir.sequence_name} IO Global",
                    members=io_members,
                    number_seed=f"{ir.sequence_name}_IO_DB",
                    number_base=io_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_io",
                file_name=io_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=io_fc_name,
                    title=f"{ir.sequence_name} IO LAD",
                    db_name=io_db_name,
                    members=[name for name, _ in io_members],
                    number_seed=f"{ir.sequence_name}_IO_FC",
                    number_base=io_fc_base,
                ),
            )
        )

    diag_members = _collect_diag_support_members(ir)
    if diag_members:
        (
            diag_db_name,
            diag_fc_name,
            diag_db_file,
            diag_fc_file,
            diag_db_base,
            diag_fc_base,
        ) = _support_block_names(ir.sequence_name, "diag")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_diag",
                file_name=diag_db_file,
                content=_build_support_global_db_xml(
                    block_name=diag_db_name,
                    title=f"{ir.sequence_name} Diag Global",
                    members=diag_members,
                    number_seed=f"{ir.sequence_name}_DIAG_DB",
                    number_base=diag_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_diag",
                file_name=diag_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=diag_fc_name,
                    title=f"{ir.sequence_name} Diag LAD",
                    db_name=diag_db_name,
                    members=[name for name, _ in diag_members],
                    number_seed=f"{ir.sequence_name}_DIAG_FC",
                    number_base=diag_fc_base,
                ),
            )
        )

    mode_members = _collect_mode_support_members(ir)
    if mode_members:
        (
            mode_db_name,
            mode_fc_name,
            mode_db_file,
            mode_fc_file,
            mode_db_base,
            mode_fc_base,
        ) = _support_block_names(ir.sequence_name, "mode")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_mode",
                file_name=mode_db_file,
                content=_build_support_global_db_xml(
                    block_name=mode_db_name,
                    title=f"{ir.sequence_name} Mode Global",
                    members=mode_members,
                    number_seed=f"{ir.sequence_name}_MODE_DB",
                    number_base=mode_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_mode",
                file_name=mode_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=mode_fc_name,
                    title=f"{ir.sequence_name} Mode LAD",
                    db_name=mode_db_name,
                    members=[name for name, _ in mode_members],
                    number_seed=f"{ir.sequence_name}_MODE_FC",
                    number_base=mode_fc_base,
                ),
            )
        )

    network_specs = _collect_network_support_specs(ir)
    for network_no, network_title, members in network_specs:
        suffix = _network_support_suffix(network_no, network_title)
        (
            network_db_name,
            network_fc_name,
            network_db_file,
            network_fc_file,
            network_db_base,
            network_fc_base,
        ) = _support_block_names(ir.sequence_name, "network", suffix=suffix)
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_network",
                file_name=network_db_file,
                content=_build_support_global_db_xml(
                    block_name=network_db_name,
                    title=f"{ir.sequence_name} Network {network_no} Global",
                    members=members,
                    number_seed=f"{ir.sequence_name}_{suffix}_DB",
                    number_base=network_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_network",
                file_name=network_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=network_fc_name,
                    title=f"{ir.sequence_name} Network {network_no} LAD ({network_title})",
                    db_name=network_db_name,
                    members=[name for name, _ in members],
                    number_seed=f"{ir.sequence_name}_{suffix}_FC",
                    number_base=network_fc_base,
                ),
            )
        )

    transitions_members = _collect_transitions_support_members(ir, network_specs)
    if transitions_members:
        (
            tr_db_name,
            tr_fc_name,
            tr_db_file,
            tr_fc_file,
            tr_db_base,
            tr_fc_base,
        ) = _support_block_names(ir.sequence_name, "transitions")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_transitions",
                file_name=tr_db_file,
                content=_build_support_global_db_xml(
                    block_name=tr_db_name,
                    title=f"{ir.sequence_name} Transitions Global",
                    members=transitions_members,
                    number_seed=f"{ir.sequence_name}_TRANSITIONS_DB",
                    number_base=tr_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_transitions",
                file_name=tr_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=tr_fc_name,
                    title=f"{ir.sequence_name} Transitions LAD",
                    db_name=tr_db_name,
                    members=[name for name, _ in transitions_members],
                    number_seed=f"{ir.sequence_name}_TRANSITIONS_FC",
                    number_base=tr_fc_base,
                ),
            )
        )

    output_members = _collect_output_family_members(ir)
    if output_members:
        (
            out_db_name,
            out_fc_name,
            out_db_file,
            out_fc_file,
            out_db_base,
            out_fc_base,
        ) = _support_block_names(ir.sequence_name, "output")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_output",
                file_name=out_db_file,
                content=_build_support_global_db_xml(
                    block_name=out_db_name,
                    title=f"{ir.sequence_name} Output Global",
                    members=output_members,
                    number_seed=f"{ir.sequence_name}_OUTPUT_DB",
                    number_base=out_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_output",
                file_name=out_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=out_fc_name,
                    title=f"{ir.sequence_name} Output LAD",
                    db_name=out_db_name,
                    members=[name for name, _ in output_members],
                    number_seed=f"{ir.sequence_name}_OUTPUT_FC",
                    number_base=out_fc_base,
                ),
            )
        )

    hmi_members = _collect_hmi_support_members(ir)
    if hmi_members:
        (
            hmi_db_name,
            hmi_fc_name,
            hmi_db_file,
            hmi_fc_file,
            hmi_db_base,
            hmi_fc_base,
        ) = _support_block_names(ir.sequence_name, "hmi")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_hmi",
                file_name=hmi_db_file,
                content=_build_support_global_db_xml(
                    block_name=hmi_db_name,
                    title=f"{ir.sequence_name} HMI Global",
                    members=hmi_members,
                    number_seed=f"{ir.sequence_name}_HMI_DB",
                    number_base=hmi_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_hmi",
                file_name=hmi_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=hmi_fc_name,
                    title=f"{ir.sequence_name} HMI LAD",
                    db_name=hmi_db_name,
                    members=[name for name, _ in hmi_members],
                    number_seed=f"{ir.sequence_name}_HMI_FC",
                    number_base=hmi_fc_base,
                ),
            )
        )

    aux_members = _collect_aux_support_members(ir)
    if aux_members:
        (
            aux_db_name,
            aux_fc_name,
            aux_db_file,
            aux_fc_file,
            aux_db_base,
            aux_fc_base,
        ) = _support_block_names(ir.sequence_name, "aux")
        previews.append(
            ArtifactPreview(
                artifact_type="support_global_db_aux",
                file_name=aux_db_file,
                content=_build_support_global_db_xml(
                    block_name=aux_db_name,
                    title=f"{ir.sequence_name} Aux Global",
                    members=aux_members,
                    number_seed=f"{ir.sequence_name}_AUX_DB",
                    number_base=aux_db_base,
                ),
            )
        )
        previews.append(
            ArtifactPreview(
                artifact_type="support_lad_fc_aux",
                file_name=aux_fc_file,
                content=_build_support_lad_fc_xml(
                    fc_name=aux_fc_name,
                    title=f"{ir.sequence_name} Aux LAD",
                    db_name=aux_db_name,
                    members=[name for name, _ in aux_members],
                    number_seed=f"{ir.sequence_name}_AUX_FC",
                    number_base=aux_fc_base,
                ),
            )
        )

    return previews


def _build_graph_fb_xml(profile, ir: AwlIR, graph_topology: GraphTopology) -> str:
    fb_number = _stable_block_number(f"{ir.sequence_name}_FB", base=100, span=100)
    static_members = [
        '    <Member Name="RT_DATA" Datatype="G7_RTDataPlus_V2" Version="1.0" />'
    ]
    static_members.extend(
        (
            f'    <Member Name="{escape(transition.name)}" Datatype="{profile.transition_runtime_type}" Version="1.0">\n'
            '      <AttributeList>\n'
            '        <BooleanAttribute Name="ExternalAccessible" SystemDefined="true">false</BooleanAttribute>\n'
            '      </AttributeList>\n'
            '      <Comment Informative="true">\n'
            f'        <MultiLanguageText Lang="en-US">Transition structure</MultiLanguageText>\n'
            '      </Comment>\n'
            '      <Sections>\n'
            '        <Section Name="None">\n'
            f'          <Member Name="TNO" Datatype="Int"><StartValue Informative="true">{transition.transition_no}</StartValue></Member>\n'
            '        </Section>\n'
            '      </Sections>\n'
            '    </Member>'
        )
        for transition in graph_topology.transition_nodes
    )
    static_members.extend(
        (
            f'    <Member Name="{escape(step.name)}" Datatype="{profile.step_runtime_type}" Version="1.0">\n'
            '      <AttributeList>\n'
            '        <BooleanAttribute Name="ExternalAccessible" SystemDefined="true">false</BooleanAttribute>\n'
            '      </AttributeList>\n'
            '      <Comment Informative="true">\n'
            '        <MultiLanguageText Lang="en-US">Step structure</MultiLanguageText>\n'
            '      </Comment>\n'
            '      <Sections>\n'
            '        <Section Name="None">\n'
            f'          <Member Name="SNO" Datatype="Int"><StartValue Informative="true">{step.step_no}</StartValue></Member>\n'
            '          <Member Name="T_MAX" Datatype="Time"><StartValue Informative="true">T#10S</StartValue></Member>\n'
            '          <Member Name="T_WARN" Datatype="Time"><StartValue Informative="true">T#7S</StartValue></Member>\n'
            '          <Member Name="H_SV_FLT" Datatype="Byte"><StartValue Informative="true">16#04</StartValue></Member>\n'
            '        </Section>\n'
            '      </Sections>\n'
            '    </Member>'
        )
        for step in graph_topology.step_nodes
    )
    seen_temp_timers: set[str] = set()
    temp_member_lines: list[str] = []
    for timer in ir.timers:
        temp_name = f"ET_{timer.source_timer}"
        if temp_name in seen_temp_timers:
            continue
        seen_temp_timers.add(temp_name)
        temp_member_lines.append(
            f'    <Member Name="{escape(temp_name)}" Datatype="Time" />'
        )
    temp_members = "\n".join(dict.fromkeys(temp_member_lines))
    if not temp_members:
        temp_members = ""

    steps_xml = "\n".join(_render_graph_step(step) for step in graph_topology.step_nodes)
    transitions_xml = "\n".join(
        _render_graph_transition(transition) for transition in graph_topology.transition_nodes
    )
    branches_xml = "\n".join(_render_graph_branch(branch) for branch in graph_topology.branch_nodes)
    connections_xml = "\n".join(
        _render_graph_connection(connection, graph_topology) for connection in graph_topology.connections
    )
    branches_block = "    <Branches />\n"
    if branches_xml:
        branches_block = f"    <Branches>\n{branches_xml}\n    </Branches>\n"

    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        f'  <Engineering version="{profile.tia_portal_version}" />\n'
        '  <SW.Blocks.FB ID="0">\n'
        '    <AttributeList>\n'
        '      <GraphVersion>2.0</GraphVersion>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Base">\n'
        '    <Sections Datatype="GRAPH_BASE" Version="1.0">\n'
        '      <Section Name="Input" />\n'
        '      <Section Name="Output" />\n'
        '      <Section Name="InOut" />\n'
        '      <Section Name="Static" />\n'
        '    </Sections>\n'
        '  </Section>\n'
        '  <Section Name="Input">\n'
        '    <Member Name="ACK_EF" Datatype="Bool" />\n'
        '  </Section>\n'
        '  <Section Name="Output" />\n'
        '  <Section Name="InOut" />\n'
        '  <Section Name="Static">\n'
        f"{_join_lines(static_members)}\n"
        '  </Section>\n'
        '  <Section Name="Temp">\n'
        f"{temp_members}\n"
        '  </Section>\n'
        '  <Section Name="Constant" />\n'
        '</Sections></Interface>\n'
        f'      <Name>{escape(ir.sequence_name)}</Name>\n'
        '      <Namespace />\n'
        f'      <Number>{fb_number}</Number>\n'
        '      <ProgrammingLanguage>GRAPH</ProgrammingLanguage>\n'
        '      <SetENOAutomatically>false</SetENOAutomatically>\n'
        '    </AttributeList>\n'
        '    <ObjectList>\n'
        '      <MultilingualText ID="1" CompositionName="Comment">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="2" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        '              <Text />\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '      <SW.Blocks.CompileUnit ID="3" CompositionName="CompileUnits">\n'
        '        <AttributeList>\n'
        '          <NetworkSource><Graph xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5">\n'
        '  <PreOperations>\n'
        '    <PermanentOperation ProgrammingLanguage="LAD" />\n'
        '  </PreOperations>\n'
        '  <Sequence>\n'
        '    <Title />\n'
        '    <Comment>\n'
        '      <MultiLanguageText Lang="en-US" />\n'
        '    </Comment>\n'
        '    <Steps>\n'
        f"{steps_xml}\n"
        '    </Steps>\n'
        '    <Transitions>\n'
        f"{transitions_xml}\n"
        '    </Transitions>\n'
        f"{branches_block}"
        '    <Connections>\n'
        f"{connections_xml}\n"
        '    </Connections>\n'
        '  </Sequence>\n'
        '  <PostOperations>\n'
        '    <PermanentOperation ProgrammingLanguage="LAD" />\n'
        '  </PostOperations>\n'
        '  <AlarmsSettings>\n'
        '    <AlarmSupervisionCategories>\n'
        '      <AlarmSupervisionCategory Id="1" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="2" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="3" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="4" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="5" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="6" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="7" DisplayClass="0" />\n'
        '      <AlarmSupervisionCategory Id="8" DisplayClass="0" />\n'
        '    </AlarmSupervisionCategories>\n'
        '    <AlarmInterlockCategory Id="1" />\n'
        '    <AlarmSubcategory1Interlock Id="0" />\n'
        '    <AlarmSubcategory2Interlock Id="0" />\n'
        '    <AlarmCategorySupervision Id="1" />\n'
        '    <AlarmSubcategory1Supervision Id="0" />\n'
        '    <AlarmSubcategory2Supervision Id="0" />\n'
        '    <AlarmWarningCategory Id="2" />\n'
        '    <AlarmSubcategory1Warning Id="0" />\n'
        '    <AlarmSubcategory2Warning Id="0" />\n'
        '  </AlarmsSettings>\n'
        '</Graph></NetworkSource>\n'
          '          <ProgrammingLanguage>GRAPH</ProgrammingLanguage>\n'
        '        </AttributeList>\n'
        '        <ObjectList>\n'
        '          <MultilingualText ID="4" CompositionName="Comment">\n'
        '            <ObjectList>\n'
        '              <MultilingualTextItem ID="5" CompositionName="Items">\n'
        '                <AttributeList>\n'
        '                  <Culture>en-US</Culture>\n'
        '                  <Text />\n'
        '                </AttributeList>\n'
        '              </MultilingualTextItem>\n'
        '            </ObjectList>\n'
        '          </MultilingualText>\n'
        '          <MultilingualText ID="6" CompositionName="Title">\n'
        '            <ObjectList>\n'
        '              <MultilingualTextItem ID="7" CompositionName="Items">\n'
        '                <AttributeList>\n'
        '                  <Culture>en-US</Culture>\n'
        f'                  <Text>{escape(ir.sequence_name)}</Text>\n'
        '                </AttributeList>\n'
        '              </MultilingualTextItem>\n'
        '            </ObjectList>\n'
        '          </MultilingualText>\n'
        '        </ObjectList>\n'
      '      </SW.Blocks.CompileUnit>\n'
        '      <MultilingualText ID="8" CompositionName="Title">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="9" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        f'              <Text>{escape(ir.sequence_name)}</Text>\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '    </ObjectList>\n'
        '  </SW.Blocks.FB>\n'
        '</Document>\n'
    )


def _build_global_db_xml(ir: AwlIR, graph_topology: GraphTopology) -> str:
    db_number = _stable_block_number(
        f"{ir.sequence_name}_DB_SEQ", base=DB_FAMILY_NUMBER_BASE["sequence"], span=100
    )
    members = _build_global_db_member_irs(ir, graph_topology)
    members_xml = _render_member_irs(members)
    block_name = _global_db_block_name(ir)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        '  <Engineering version="V20" />\n'
        '  <SW.Blocks.GlobalDB ID="0">\n'
        '    <AttributeList>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Static">\n'
        f"{members_xml}\n"
        '  </Section>\n'
        '</Sections></Interface>\n'
        '      <MemoryLayout>Optimized</MemoryLayout>\n'
        '      <MemoryReserve>100</MemoryReserve>\n'
        f'      <Name>{escape(block_name)}</Name>\n'
        '      <Namespace />\n'
        f'      <Number>{db_number}</Number>\n'
        '      <ProgrammingLanguage>DB</ProgrammingLanguage>\n'
        '    </AttributeList>\n'
        '    <ObjectList>\n'
        '      <MultilingualText ID="1" CompositionName="Comment">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="2" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        '              <Text />\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '      <MultilingualText ID="3" CompositionName="Title">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="4" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        f'              <Text>{escape(block_name)}</Text>\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '    </ObjectList>\n'
        '  </SW.Blocks.GlobalDB>\n'
        '</Document>\n'
    )


def _build_support_global_db_xml(
    block_name: str,
    title: str,
    members: list[tuple[str, str]],
    number_seed: str,
    number_base: int = 400,
    number_span: int = 200,
) -> str:
    db_number = _stable_block_number(number_seed, base=number_base, span=number_span)
    member_irs = [
        MemberIR(name=member_name, datatype="Bool", comment=member_comment)
        for member_name, member_comment in members
    ]
    if not member_irs:
        member_irs = [MemberIR(name="NoData", datatype="Bool")]
    members_xml = _render_member_irs(member_irs)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        '  <Engineering version="V20" />\n'
        '  <SW.Blocks.GlobalDB ID="0">\n'
        '    <AttributeList>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Static">\n'
        f"{members_xml}\n"
        '  </Section>\n'
        '</Sections></Interface>\n'
        '      <MemoryLayout>Optimized</MemoryLayout>\n'
        '      <MemoryReserve>100</MemoryReserve>\n'
        f'      <Name>{escape(block_name)}</Name>\n'
        '      <Namespace />\n'
        f'      <Number>{db_number}</Number>\n'
        '      <ProgrammingLanguage>DB</ProgrammingLanguage>\n'
        '    </AttributeList>\n'
        '    <ObjectList>\n'
        '      <MultilingualText ID="1" CompositionName="Comment">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="2" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        '              <Text />\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '      <MultilingualText ID="3" CompositionName="Title">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="4" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        f'              <Text>{escape(title)}</Text>\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '    </ObjectList>\n'
        '  </SW.Blocks.GlobalDB>\n'
        '</Document>\n'
    )


def _build_lad_fc_xml(ir: AwlIR, graph_topology: GraphTopology) -> str:
    fc_number = _stable_block_number(
        f"{ir.sequence_name}_FC_TRANSITIONS",
        base=FC_FAMILY_NUMBER_BASE["transitions"],
        span=100,
    )
    temp_members = _build_lad_temp_members(ir)
    compile_units = _build_lad_compile_units(ir, graph_topology)
    block_name = _lad_fc_block_name(ir)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        '  <Engineering version="V20" />\n'
        '  <SW.Blocks.FC ID="0">\n'
        '    <AttributeList>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Input" />\n'
        '  <Section Name="Output" />\n'
        '  <Section Name="InOut" />\n'
        '  <Section Name="Temp">\n'
        f"{temp_members}\n"
        '  </Section>\n'
        '  <Section Name="Constant" />\n'
        '  <Section Name="Return">\n'
        '    <Member Name="Ret_Val" Datatype="Void" />\n'
        '  </Section>\n'
        '</Sections></Interface>\n'
        '      <MemoryLayout>Optimized</MemoryLayout>\n'
        f'      <Name>{escape(block_name)}</Name>\n'
        '      <Namespace />\n'
        f'      <Number>{fc_number}</Number>\n'
        '      <ProgrammingLanguage>LAD</ProgrammingLanguage>\n'
        '      <SetENOAutomatically>false</SetENOAutomatically>\n'
        '    </AttributeList>\n'
        '    <ObjectList>\n'
        '      <MultilingualText ID="1" CompositionName="Comment">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="2" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        '              <Text />\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        f"{compile_units}\n"
        '    </ObjectList>\n'
        '  </SW.Blocks.FC>\n'
        '</Document>\n'
    )


def _build_support_lad_fc_xml(
    fc_name: str,
    title: str,
    db_name: str,
    members: list[str],
    number_seed: str,
    number_base: int = 600,
    number_span: int = 200,
) -> str:
    fc_number = _stable_block_number(number_seed, base=number_base, span=number_span)
    temp_members = "\n".join(
        f'    <Member Name="{escape(member)}" Datatype="Bool" />'
        for member in dict.fromkeys(members)
    )
    if not temp_members:
        temp_members = '    <Member Name="PACKET_READY" Datatype="Bool" />'
    compile_units = _build_support_lad_compile_units(db_name=db_name, members=members)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        '  <Engineering version="V20" />\n'
        '  <SW.Blocks.FC ID="0">\n'
        '    <AttributeList>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Input" />\n'
        '  <Section Name="Output" />\n'
        '  <Section Name="InOut" />\n'
        '  <Section Name="Temp">\n'
        f"{temp_members}\n"
        '  </Section>\n'
        '  <Section Name="Constant" />\n'
        '  <Section Name="Return">\n'
        '    <Member Name="Ret_Val" Datatype="Void" />\n'
        '  </Section>\n'
        '</Sections></Interface>\n'
        '      <MemoryLayout>Optimized</MemoryLayout>\n'
        f'      <Name>{escape(fc_name)}</Name>\n'
        '      <Namespace />\n'
        f'      <Number>{fc_number}</Number>\n'
        '      <ProgrammingLanguage>LAD</ProgrammingLanguage>\n'
        '      <SetENOAutomatically>false</SetENOAutomatically>\n'
        '    </AttributeList>\n'
        '    <ObjectList>\n'
        '      <MultilingualText ID="1" CompositionName="Comment">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="2" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        '              <Text />\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        f"{compile_units}\n"
        '      <MultilingualText ID="F0" CompositionName="Title">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="F1" CompositionName="Items">\n'
        '            <AttributeList>\n'
        '              <Culture>en-US</Culture>\n'
        f'              <Text>{escape(title)}</Text>\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '    </ObjectList>\n'
        '  </SW.Blocks.FC>\n'
        '</Document>\n'
    )


def _render_member_irs(members: list[MemberIR], indent: str = "    ") -> str:
    rendered = [_emit_member_ir(member, indent) for member in members]
    return "\n".join(rendered) if rendered else f'{indent}<Member Name="NoData" Datatype="Bool" />'


def _emit_member_ir(member: MemberIR, indent: str) -> str:
    attrs: list[str] = []
    if member.version:
        attrs.append(f'Version="{escape(member.version)}"')
    if member.remanence:
        attrs.append(f'Remanence="{escape(member.remanence)}"')
    attr_blob = (" " + " ".join(attrs)) if attrs else ""
    lines = [f'{indent}<Member Name="{escape(member.name)}" Datatype="{escape(member.datatype)}"{attr_blob}>']
    inner_indent = indent + "  "

    if member.attributes:
        lines.append(f"{inner_indent}<AttributeList>")
        for name, value in member.attributes:
            lines.append(
                f'{inner_indent}  <BooleanAttribute Name="{escape(name)}" SystemDefined="true">{escape(value)}</BooleanAttribute>'
            )
        lines.append(f"{inner_indent}</AttributeList>")

    if member.comment:
        lines.append(f'{inner_indent}<Comment Informative="true">')
        lines.append(
            f'{inner_indent}  <MultiLanguageText Lang="en-US">{escape(member.comment)}</MultiLanguageText>'
        )
        lines.append(f"{inner_indent}</Comment>")

    if member.start_value:
        lines.append(f"{inner_indent}<StartValue>{escape(member.start_value)}</StartValue>")

    for child in member.children:
        lines.append(_emit_member_ir(child, inner_indent))

    lines.append(f"{indent}</Member>")
    return "\n".join(lines)


def _dedupe_member_irs(members: list[MemberIR]) -> list[MemberIR]:
    seen: set[tuple[str, str, str | None]] = set()
    unique: list[MemberIR] = []
    for member in members:
        key = (member.name, member.datatype, member.version)
        if key in seen:
            continue
        seen.add(key)
        unique.append(member)
    return unique


def _build_global_db_member_irs(ir: AwlIR, graph_topology: GraphTopology) -> list[MemberIR]:
    members: list[MemberIR] = []

    for transition in graph_topology.transition_nodes:
        guard_member = transition.db_member_name
        members.append(
            MemberIR(
                name=guard_member,
                datatype="Bool",
                comment=f"Transition guard for {transition.name}",
            )
        )

    for memory in ir.memories:
        members.append(
            MemberIR(
                name=_db_member_name(memory.name),
                datatype="Bool",
                comment=memory.role,
            )
        )

    for timer in ir.timers:
        members.append(
            MemberIR(
                name=_db_member_name(timer.source_timer),
                datatype="IEC_TIMER",
                version="1.0",
                comment=f"Timer {timer.source_timer} ({timer.kind})",
                start_value=timer.preset,
            )
        )

    if not members:
        members.append(MemberIR(name="NoData", datatype="Bool"))
    return _dedupe_member_irs(members)


def _expected_global_db_member_names(ir: AwlIR, graph_topology: GraphTopology) -> set[str]:
    names = {transition.db_member_name for transition in graph_topology.transition_nodes}
    names.update(_db_member_name(memory.name) for memory in ir.memories)
    names.update(_db_member_name(timer.source_timer) for timer in ir.timers)
    if not names:
        names.add("NoData")
    return names


def _build_lad_temp_members(ir: AwlIR) -> str:
    members: list[str] = []
    for output in ir.outputs:
        members.append(f'    <Member Name="{escape(_db_member_name(output.name))}" Datatype="Bool" />')
    for memory in ir.memories:
        members.append(f'    <Member Name="{escape(_db_member_name(memory.name))}" Datatype="Bool" />')
    if not members:
        members.append('    <Member Name="PACKET_READY" Datatype="Bool" />')
    return "\n".join(dict.fromkeys(members))


def _build_lad_compile_units(ir: AwlIR, graph_topology: GraphTopology) -> str:
    units: list[str] = []
    base_id = 3
    guard_targets = graph_topology.transition_nodes or [
        GraphTransitionNode(
            name="T1",
            transition_no=1,
            source_step="S1",
            target_step="S2",
            guard_expression="PACKET_READY",
            network_index=0,
            db_block_name=_global_db_block_name(ir),
            db_member_name=_transition_db_member_name_from_values("T1", "PACKET_READY"),
        )
    ]
    for index, transition in enumerate(guard_targets):
        unit_id = format(base_id + (index * 5), "X")
        comment_id = format(base_id + (index * 5) + 1, "X")
        comment_item_id = format(base_id + (index * 5) + 2, "X")
        title_id = format(base_id + (index * 5) + 3, "X")
        title_item_id = format(base_id + (index * 5) + 4, "X")
        target_db_name = escape(_global_db_block_name(ir))
        target_member_name = escape(transition.db_member_name)
        aux_member = transition.db_member_name
        if ir.memories:
            aux_member = _db_member_name(ir.memories[0].name)
        aux_member_name = escape(aux_member)
        flgnet_xml = _build_lad_pattern(
            pattern="guard_chain",
            db_name=target_db_name,
            member_name=target_member_name,
            aux_member=aux_member_name,
        )
        units.append(
            '      <SW.Blocks.CompileUnit ID="'
            + unit_id
            + '" CompositionName="CompileUnits">\n'
            '        <AttributeList>\n'
            f"{flgnet_xml}\n"
            '          <ProgrammingLanguage>LAD</ProgrammingLanguage>\n'
            '        </AttributeList>\n'
            '        <ObjectList>\n'
            f'          <MultilingualText ID="{comment_id}" CompositionName="Comment">\n'
            '            <ObjectList>\n'
            f'              <MultilingualTextItem ID="{comment_item_id}" CompositionName="Items">\n'
            '                <AttributeList>\n'
            '                  <Culture>en-US</Culture>\n'
            f'                  <Text>Network {transition.network_index}</Text>\n'
            '                </AttributeList>\n'
            '              </MultilingualTextItem>\n'
            '            </ObjectList>\n'
            '          </MultilingualText>\n'
            f'          <MultilingualText ID="{title_id}" CompositionName="Title">\n'
            '            <ObjectList>\n'
            f'              <MultilingualTextItem ID="{title_item_id}" CompositionName="Items">\n'
            '                <AttributeList>\n'
            '                  <Culture>en-US</Culture>\n'
            f'                  <Text>{escape(target_member_name)}</Text>\n'
            '                </AttributeList>\n'
            '              </MultilingualTextItem>\n'
            '            </ObjectList>\n'
            '          </MultilingualText>\n'
            '        </ObjectList>\n'
            '      </SW.Blocks.CompileUnit>'
        )
    return "\n".join(units)


def _build_support_lad_compile_units(db_name: str, members: list[str]) -> str:
    units: list[str] = []
    unique_members = list(dict.fromkeys(member for member in members if member))
    if not unique_members:
        unique_members = ["PACKET_READY"]
    base_id = 3
    for index, member_name in enumerate(unique_members):
        unit_id = format(base_id + (index * 3), "X")
        comment_id = format(base_id + (index * 3) + 1, "X")
        comment_item_id = format(base_id + (index * 3) + 2, "X")
        flgnet_xml = _build_lad_pattern(
            pattern="single_contact_coil",
            db_name=escape(db_name),
            member_name=escape(member_name),
            aux_member=None,
        )
        units.append(
            '      <SW.Blocks.CompileUnit ID="'
            + unit_id
            + '" CompositionName="CompileUnits">\n'
            '        <AttributeList>\n'
            f"{flgnet_xml}\n"
            '          <ProgrammingLanguage>LAD</ProgrammingLanguage>\n'
            '        </AttributeList>\n'
            '        <ObjectList>\n'
            '          <MultilingualText ID="'
            + comment_id
            + '" CompositionName="Comment">\n'
            '            <ObjectList>\n'
            '              <MultilingualTextItem ID="'
            + comment_item_id
            + '" CompositionName="Items">\n'
            '                <AttributeList>\n'
            '                  <Culture>en-US</Culture>\n'
            f'                  <Text>{escape(member_name)} support network</Text>\n'
            '                </AttributeList>\n'
            '              </MultilingualTextItem>\n'
            '            </ObjectList>\n'
            '          </MultilingualText>\n'
            '        </ObjectList>\n'
            '      </SW.Blocks.CompileUnit>'
        )
    return "\n".join(units)


_LAD_PATTERN_LIBRARY = {"guard_chain", "single_contact_coil"}


def _build_lad_pattern(
    pattern: str,
    db_name: str,
    member_name: str,
    aux_member: str | None,
) -> str:
    if pattern not in _LAD_PATTERN_LIBRARY:
        raise ValueError(f"Unsupported LAD pattern: {pattern}")

    if pattern == "guard_chain":
        if not aux_member:
            raise ValueError("guard_chain requires aux_member")
        return (
            '          <NetworkSource><FlgNet xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5">\n'
            '  <Parts>\n'
            '    <Access Scope="GlobalVariable" UId="21">\n'
            '      <Symbol>\n'
            f'        <Component Name="{db_name}" />\n'
            f'        <Component Name="{member_name}" />\n'
            '      </Symbol>\n'
            '    </Access>\n'
            '    <Part Name="Contact" UId="22" />\n'
            '    <Access Scope="GlobalVariable" UId="23">\n'
            '      <Symbol>\n'
            f'        <Component Name="{db_name}" />\n'
            f'        <Component Name="{aux_member}" />\n'
            '      </Symbol>\n'
            '    </Access>\n'
            '    <Part Name="Contact" UId="24" />\n'
            '    <Access Scope="GlobalVariable" UId="25">\n'
            '      <Symbol>\n'
            f'        <Component Name="{db_name}" />\n'
            f'        <Component Name="{member_name}" />\n'
            '      </Symbol>\n'
            '    </Access>\n'
            '    <Part Name="Coil" UId="26" />\n'
            '  </Parts>\n'
            '  <Wires>\n'
            '    <Wire UId="31">\n'
            '      <Powerrail />\n'
            '      <NameCon UId="22" Name="in" />\n'
            '    </Wire>\n'
            '    <Wire UId="32">\n'
            '      <IdentCon UId="21" />\n'
            '      <NameCon UId="22" Name="operand" />\n'
            '    </Wire>\n'
            '    <Wire UId="33">\n'
            '      <NameCon UId="22" Name="out" />\n'
            '      <NameCon UId="24" Name="in" />\n'
            '    </Wire>\n'
            '    <Wire UId="34">\n'
            '      <IdentCon UId="23" />\n'
            '      <NameCon UId="24" Name="operand" />\n'
            '    </Wire>\n'
            '    <Wire UId="35">\n'
            '      <NameCon UId="24" Name="out" />\n'
            '      <NameCon UId="26" Name="in" />\n'
            '    </Wire>\n'
            '    <Wire UId="36">\n'
            '      <IdentCon UId="25" />\n'
            '      <NameCon UId="26" Name="operand" />\n'
            '    </Wire>\n'
            '  </Wires>\n'
            '</FlgNet></NetworkSource>'
        )

    return (
        '          <NetworkSource><FlgNet xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5">\n'
        '  <Parts>\n'
        '    <Access Scope="GlobalVariable" UId="21">\n'
        '      <Symbol>\n'
        f'        <Component Name="{db_name}" />\n'
        f'        <Component Name="{member_name}" />\n'
        '      </Symbol>\n'
        '    </Access>\n'
        '    <Part Name="Contact" UId="22" />\n'
        '    <Part Name="Coil" UId="23" />\n'
        '  </Parts>\n'
        '  <Wires>\n'
        '    <Wire UId="31">\n'
        '      <Powerrail />\n'
        '      <NameCon UId="22" Name="in" />\n'
        '    </Wire>\n'
        '    <Wire UId="32">\n'
        '      <IdentCon UId="21" />\n'
        '      <NameCon UId="22" Name="operand" />\n'
        '    </Wire>\n'
        '    <Wire UId="33">\n'
        '      <NameCon UId="22" Name="out" />\n'
        '      <NameCon UId="23" Name="in" />\n'
        '    </Wire>\n'
        '  </Wires>\n'
        '</FlgNet></NetworkSource>'
    )


def _collect_io_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for output in ir.outputs:
        members.append((_support_member_name(output.name, "Q"), f"Output mapping {output.name}"))
    for ext in ir.external_refs:
        if ext.startswith(("A", "Q")):
            continue
        family = _classify_operand_family(ext)
        members.append((_support_member_name(ext, family), f"External reference {ext} ({family})"))
    return list(dict.fromkeys(members))


def _collect_diag_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for timer in ir.timers:
        members.append((_support_member_name(timer.source_timer, "T"), f"Timer diagnostic {timer.source_timer}"))
    for fault in ir.faults:
        members.append((_support_member_name(fault.name, "F"), f"Fault diagnostic {fault.name}"))
    return list(dict.fromkeys(members))


def _collect_mode_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    if ir.manual_logic_networks:
        members.append(
            (
                "MODE_MANUAL_ACTIVE",
                f"Manual mode networks {','.join(str(i) for i in sorted(set(ir.manual_logic_networks)))}",
            )
        )
    if ir.auto_logic_networks:
        members.append(
            (
                "MODE_AUTO_ACTIVE",
                f"Auto mode networks {','.join(str(i) for i in sorted(set(ir.auto_logic_networks)))}",
            )
        )
    if ir.manual_logic_networks and ir.auto_logic_networks:
        members.append(("MODE_INTERLOCK_OK", "Manual/Auto arbitration coherence"))
    return members


def _collect_transitions_support_members(
    ir: AwlIR,
    network_specs: list[tuple[int, str, list[tuple[str, str]]]],
) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for transition in ir.transitions:
        member = _support_member_name(transition.transition_id, "TR")
        members.append((member, f"Transition edge {transition.source_step}->{transition.target_step}"))
    for network_no, _, _ in network_specs:
        members.append((f"TR_NETWORK_{network_no}_ACTIVE", f"Transition network {network_no} active"))
    return list(dict.fromkeys(members))


def _collect_output_family_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for output in ir.outputs:
        member = _support_member_name(output.name, "OUT_CMD")
        members.append((member, f"Output command {output.action} {output.name}"))
    return list(dict.fromkeys(members))


def _collect_hmi_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for ext in ir.external_refs:
        candidate = ext.upper()
        if any(marker in candidate for marker in ("HMI", "OPIN", "OPOUT", "DB81", "DB82")):
            member = _support_member_name(candidate, "HMI")
            members.append((member, f"HMI/Operator reference {candidate}"))
    return list(dict.fromkeys(members))


def _collect_aux_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for memory in ir.memories:
        member = _support_member_name(memory.name, "AUX_MEM")
        members.append((member, f"Aux memory ({memory.role}) {memory.name}"))
    for timer in ir.timers:
        member = _support_member_name(timer.source_timer, "AUX_TIMER")
        members.append((member, f"Aux timer {timer.source_timer}"))
    return list(dict.fromkeys(members))


def _collect_network_support_specs(ir: AwlIR) -> list[tuple[int, str, list[tuple[str, str]]]]:
    specs: list[tuple[int, str, list[tuple[str, str]]]] = []
    for network in ir.networks:
        network_members: list[tuple[str, str]] = []
        for operand in _collect_condition_operands(network):
            family = _classify_operand_family(operand)
            member = _support_member_name(operand, f"COND_{family}")
            network_members.append((member, f"Condition operand {operand} ({family})"))
        for output_name, action in _collect_output_targets(network):
            member = _support_member_name(output_name, "OUT")
            network_members.append((member, f"Output action {action} {output_name}"))
        for memory_name, action in _collect_memory_targets(network):
            member = _support_member_name(memory_name, "MEM")
            network_members.append((member, f"Memory action {action} {memory_name}"))
        unique_members = list(dict.fromkeys(network_members))
        if not unique_members:
            continue
        specs.append((network.index, network.title or f"NETWORK {network.index}", unique_members))
    return specs


def _support_member_name(raw_symbol: str, prefix: str) -> str:
    normalized = _normalize_symbol_name(raw_symbol, f"{prefix}_SIGNAL")
    return _db_member_name(f"{prefix}_{normalized}")


def _network_support_suffix(network_no: int, network_title: str) -> str:
    title_slug = _normalize_symbol_name(network_title, f"N{network_no}")
    if not title_slug:
        return f"N{network_no}"
    title_slug = title_slug[:20]
    return f"N{network_no}_{title_slug}"


def _support_block_names(
    sequence_name: str,
    category: str,
    suffix: str | None = None,
) -> tuple[str, str, str, str, int, int]:
    schema = SUPPORT_BLOCK_SCHEMA.get(category)
    if schema is None:
        token = _normalize_symbol_name(category, category.upper())
        file_token = token.lower()
    else:
        token = schema["token"]
        file_token = schema["file_token"]

    family_override = SUPPORT_FAMILY_OVERRIDES.get(category, {})
    db_family = family_override.get("db_family")
    fc_family = family_override.get("fc_family")
    db_prefix = DB_FAMILY_PREFIX.get(db_family) if db_family else None
    fc_prefix = FC_FAMILY_PREFIX.get(fc_family) if fc_family else None
    db_number_base = DB_FAMILY_NUMBER_BASE.get(db_family, 400)
    fc_number_base = FC_FAMILY_NUMBER_BASE.get(fc_family, 600)

    if suffix:
        block_token = _normalize_symbol_name(suffix, suffix)
        file_suffix = block_token.lower()
    else:
        block_token = token
        file_suffix = file_token

    if db_prefix:
        db_name = f"{db_prefix}_{sequence_name}_{block_token}_Global"
        db_file = f"{db_prefix}_{sequence_name}_{file_suffix}_global_auto.xml"
    else:
        db_name = f"{sequence_name}_{block_token}_Global"
        db_file = f"DB_{sequence_name}_{file_suffix}_global_auto.xml"

    if fc_prefix:
        fc_name = f"{fc_prefix}_{sequence_name}_{block_token}_LAD"
        fc_file = f"{fc_prefix}_{sequence_name}_{file_suffix}_lad_auto.xml"
    else:
        fc_name = f"{sequence_name}_{block_token}_LAD"
        fc_file = f"FC_{sequence_name}_{file_suffix}_lad_auto.xml"

    return db_name, fc_name, db_file, fc_file, db_number_base, fc_number_base


def _classify_operand_family(operand: str) -> str:
    candidate = operand.upper()
    if re.fullmatch(r"[IE]\d+(?:\.\d+)?", candidate):
        return "IN"
    if re.fullmatch(r"[AQ]\d+(?:\.\d+)?", candidate):
        return "OUT"
    if re.fullmatch(r"M\d+(?:\.\d+)?", candidate):
        return "MEM"
    if re.fullmatch(r"T\d+", candidate):
        return "TIMER"
    if re.fullmatch(r"DB\d+\.DB[XBWD]\d+(?:\.\d+)?", candidate):
        return "DBEXT"
    if candidate.startswith("DB"):
        return "DB"
    return "SIG"


def _render_graph_step(step: GraphStepNode) -> str:
    step_name = str(step.step_no)
    return (
        f'      <Step Number="{step.step_no}" Init="{str(step.init).lower()}" '
        f'Name="{escape(step_name)}" MaximumStepTime="T#10S" WarningTime="T#7S">\n'
        '        <Actions>\n'
        '          <Action />\n'
        '        </Actions>\n'
        '        <Supervisions>\n'
        '          <Supervision ProgrammingLanguage="LAD">\n'
        f"{_render_empty_graph_net('SvCoil')}\n"
        '          </Supervision>\n'
        '        </Supervisions>\n'
        '        <Interlocks>\n'
        '          <Interlock ProgrammingLanguage="LAD">\n'
        f"{_render_empty_graph_net('IlCoil')}\n"
        '          </Interlock>\n'
        '        </Interlocks>\n'
        '      </Step>'
    )


def _render_graph_transition(transition: GraphTransitionNode) -> str:
    access_uid = 21
    contact_uid = 22
    trcoil_uid = 23
    parts_lines = [
        f'            <Access Scope="GlobalVariable" UId="{access_uid}">\n',
        '              <Symbol>\n',
        f'                <Component Name="{escape(transition.db_block_name)}" />\n',
        f'                <Component Name="{escape(transition.db_member_name)}" />\n',
        '              </Symbol>\n',
        '            </Access>\n',
        f'            <Part Name="Contact" UId="{contact_uid}" />\n',
        f'            <Part Name="TrCoil" UId="{trcoil_uid}" />\n',
    ]
    wires_lines = [
        '            <Wire UId="24">\n',
        '              <Powerrail />\n',
        f'              <NameCon UId="{contact_uid}" Name="in" />\n',
        '            </Wire>\n',
        '            <Wire UId="25">\n',
        f'              <IdentCon UId="{access_uid}" />\n',
        f'              <NameCon UId="{contact_uid}" Name="operand" />\n',
        '            </Wire>\n',
        '            <Wire UId="26">\n',
        f'              <NameCon UId="{contact_uid}" Name="out" />\n',
        f'              <NameCon UId="{trcoil_uid}" Name="in" />\n',
        '            </Wire>\n',
    ]

    return (
        f'      <Transition IsMissing="false" Name="{escape(transition.name)}" '
        f'Number="{transition.transition_no}" ProgrammingLanguage="LAD">\n'
        '        <FlgNet>\n'
        '          <Parts>\n'
        f'{"".join(parts_lines)}'
        '          </Parts>\n'
        '          <Wires>\n'
        f'{"".join(wires_lines)}'
        '          </Wires>\n'
        '        </FlgNet>\n'
        '      </Transition>'
    )


def _render_graph_branch(branch: GraphBranchNode) -> str:
    if branch.branch_type == "SimEnd":
        cardinality = len(branch.incoming_refs)
    else:
        cardinality = len(branch.outgoing_refs)
    return (
        f'      <Branch Number="{branch.branch_no}" Type="{escape(branch.branch_type)}" '
        f'Cardinality="{cardinality}" />'
    )


def _render_graph_connection(connection: GraphConnection, graph_topology: GraphTopology) -> str:
    return (
        '      <Connection>\n'
        '        <NodeFrom>\n'
        f'{_render_graph_node_ref(connection.source_ref, graph_topology, peer_ref=connection.target_ref, direction="from")}\n'
        '        </NodeFrom>\n'
        '        <NodeTo>\n'
        f'{_render_graph_node_ref(connection.target_ref, graph_topology, peer_ref=connection.source_ref, direction="to")}\n'
        '        </NodeTo>\n'
        f'        <LinkType>{escape(connection.link_type)}</LinkType>\n'
        '      </Connection>'
    )


def _render_graph_node_ref(
    ref: str,
    graph_topology: GraphTopology,
    peer_ref: str | None = None,
    direction: str | None = None,
) -> str:
    step = next((item for item in graph_topology.step_nodes if item.name == ref), None)
    if step is not None:
        return f'          <StepRef Number="{step.step_no}" />'
    transition = next((item for item in graph_topology.transition_nodes if item.name == ref), None)
    if transition is not None:
        return f'          <TransitionRef Number="{transition.transition_no}" />'
    branch = next((item for item in graph_topology.branch_nodes if item.name == ref), None)
    if branch is not None:
        if direction == "to":
            if peer_ref is not None:
                try:
                    in_index = branch.incoming_refs.index(peer_ref)
                except ValueError:
                    in_index = 0
                return f'          <BranchRef Number="{branch.branch_no}" In="{in_index}" />'
            return f'          <BranchRef Number="{branch.branch_no}" In="0" />'
        if direction == "from" and peer_ref is not None:
            try:
                out_index = branch.outgoing_refs.index(peer_ref)
            except ValueError:
                out_index = 0
            return f'          <BranchRef Number="{branch.branch_no}" Out="{out_index}" />'
        return f'          <BranchRef Number="{branch.branch_no}" In="0" />'
    return '          <EndConnection />'


def _render_empty_graph_net(coil_name: str) -> str:
    return (
        '            <FlgNet>\n'
        '              <Parts>\n'
        f'                <Part Name="{coil_name}" UId="21" />\n'
        '              </Parts>\n'
        '              <Wires>\n'
        '                <Wire UId="22">\n'
        '                  <Powerrail />\n'
        '                  <NameCon UId="21" Name="in" />\n'
        '                </Wire>\n'
        '              </Wires>\n'
        '            </FlgNet>'
    )


def _join_lines(lines: list[str]) -> str:
    return "\n".join(lines)


def _normalize_symbol_name(guard_expression: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", guard_expression).strip("_")
    return cleaned or fallback


def _db_member_name(raw_name: str) -> str:
    return raw_name.replace(".", "_")


def _global_db_block_name(ir: AwlIR) -> str:
    return f"{DB_FAMILY_PREFIX['sequence']}_{ir.sequence_name}_SEQ_Global"


def _lad_fc_block_name(ir: AwlIR) -> str:
    return f"{FC_FAMILY_PREFIX['transitions']}_{ir.sequence_name}_TRANSITIONS_LAD"


def _transition_db_member_name(transition: TransitionCandidate) -> str:
    return _transition_db_member_name_from_values(transition.transition_id, transition.guard_expression)


def _transition_db_member_name_from_values(transition_name: str, guard_expression: str) -> str:
    normalized = _normalize_symbol_name(guard_expression, transition_name)
    return f"{transition_name}_Guard_{normalized}"


def _step_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", name)
    if match:
        return int(match.group(1)), name
    return 10**9, name


def _graph_step_sort_key(name: str) -> tuple[int, int, str]:
    merge_match = re.match(r"JM_(S\d+)_(\d+)$", name)
    if merge_match:
        target_step = merge_match.group(1)
        index = int(merge_match.group(2))
        target_no, _ = _step_sort_key(target_step)
        return target_no, 0, f"{target_step}_{index}"

    step_no, raw_name = _step_sort_key(name)
    return step_no, 1, raw_name


def _collect_matches(network: AwlNetwork, pattern: re.Pattern[str]) -> set[str]:
    matches: set[str] = set()
    for line in network.raw_lines:
        for match in pattern.findall(line):
            matches.add(match.upper())
    return matches


def _collect_condition_operands(network: AwlNetwork) -> list[str]:
    operands: list[str] = []
    for instr in network.instructions:
        if instr.opcode not in CONDITION_OPCODES:
            continue
        if not instr.args:
            continue
        candidate = _select_instruction_operand(instr.args)
        if not candidate:
            continue
        if STEP_RE.fullmatch(candidate):
            continue
        operands.append(candidate)
    return _dedupe_list(operands)


def _collect_step_targets(network: AwlNetwork) -> list[str]:
    targets: list[str] = []
    for instr in network.instructions:
        if instr.opcode not in {"S", "="}:
            continue
        if not instr.args:
            continue
        candidate = _select_instruction_operand(instr.args)
        if not candidate:
            continue
        if STEP_RE.fullmatch(candidate):
            targets.append(candidate)
    return _dedupe_list(targets)


def _collect_transition_patterns(network: AwlNetwork) -> list[tuple[str, str, list[str], list[str]]]:
    transitions: list[tuple[str, str, list[str], list[str]]] = []
    current_step: str | None = None
    condition_operands: list[str] = []
    jump_guard: list[str] | None = None
    jump_labels: list[str] = []

    for instr in network.instructions:
        if instr.opcode in CONDITION_OPCODES and instr.args:
            operand = _select_instruction_operand(instr.args)
            if not operand:
                continue
            if STEP_RE.fullmatch(operand):
                current_step = operand
                condition_operands = []
                jump_guard = None
                jump_labels = []
                continue
            condition_operands.append(operand)

        if instr.opcode in JUMP_OPCODES and instr.args:
            label = _normalize_operand_token(instr.args[0])
            jump_guard = list(condition_operands)
            jump_labels = [label] if label else []

        if instr.opcode in {"S", "="} and instr.args:
            target = _select_instruction_operand(instr.args)
            if not target or not STEP_RE.fullmatch(target):
                continue
            if not current_step:
                continue
            guard_operands = jump_guard if jump_guard is not None else condition_operands
            guard_operands = _dedupe_list(guard_operands)
            transitions.append((current_step, target, guard_operands, jump_labels))

    return transitions


def _collect_timers(network: AwlNetwork) -> list[tuple[str, str, str | None]]:
    timers: list[tuple[str, str, str | None]] = []
    for instr in network.instructions:
        preset = None
        if instr.opcode in TIMER_OPCODES and instr.args:
            timer_name = _select_instruction_operand(instr.args)
            if not timer_name:
                continue
            preset = _extract_preset(network)
            timers.append((timer_name, instr.opcode, preset))
        for match in TIMER_RE.findall(instr.raw):
            timers.append((match.upper(), "LEGACY_TIMER", _extract_preset(network)))
    return _dedupe_timers(timers)


def _extract_preset(network: AwlNetwork) -> str | None:
    for line in network.raw_lines:
        match = PRESET_RE.search(line)
        if match:
            return match.group(0).upper()
    return None


def _collect_memory_targets(network: AwlNetwork) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for instr in network.instructions:
        if instr.opcode not in ACTION_OPCODES or not instr.args:
            continue
        candidate = _select_instruction_operand(instr.args)
        if not candidate:
            continue
        if MEMORY_RE.fullmatch(candidate):
            targets.append((candidate, instr.opcode))
    return targets


def _collect_output_targets(network: AwlNetwork) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for instr in network.instructions:
        if instr.opcode not in ACTION_OPCODES or not instr.args:
            continue
        candidate = _select_instruction_operand(instr.args)
        if not candidate:
            continue
        if OUTPUT_RE.fullmatch(candidate):
            targets.append((candidate, instr.opcode))
    return targets


def _select_instruction_operand(args: list[str]) -> str | None:
    cleaned: list[str] = []
    for raw_arg in args:
        if raw_arg == "--":
            break
        normalized = _normalize_operand_token(raw_arg)
        if normalized:
            cleaned.append(normalized)

    if not cleaned:
        return None

    preferred = next((item for item in cleaned if _is_address_like_operand(item)), None)
    return preferred or cleaned[0]


def _normalize_operand_token(token: str) -> str:
    value = token.strip().rstrip(",;").strip("()")
    value = value.strip().strip('"').strip("'")
    if not value:
        return ""
    value = value.replace(":", "_").replace("-", "_")
    value = re.sub(r"[^A-Za-z0-9_.]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value.upper()


def _is_address_like_operand(value: str) -> bool:
    patterns = (
        r"^(?:[QAEIMT]\d+(?:\.\d+)?)$",
        r"^DB\d+\.DB[XBWD]\d+(?:\.\d+)?$",
        r"^DB\d+\.D[IBD]\d+$",
    )
    return any(re.fullmatch(pattern, value, flags=re.IGNORECASE) for pattern in patterns)


def _collect_fault_tokens(network: AwlNetwork) -> list[str]:
    tokens: list[str] = []
    for line in network.raw_lines:
        for token in TOKEN_RE.findall(line):
            if any(marker in token.lower() for marker in ("fault", "alarm", "error", "emerg")):
                tokens.append(token.upper())
    return _dedupe_list(tokens)


def _network_has_keyword(network: AwlNetwork, keywords: tuple[str, ...]) -> bool:
    lowered = "\n".join(network.raw_lines).lower()
    return any(keyword in lowered for keyword in keywords)


def _classify_memory_role(network: AwlNetwork) -> str:
    lowered = "\n".join(network.raw_lines).lower()
    if "manual" in lowered or " man" in lowered:
        return "manual"
    if any(marker in lowered for marker in ("fault", "alarm", "error", "emerg")):
        return "fault"
    if STEP_RE.search(lowered.upper()):
        return "sequence"
    return "technical"


def _first_matching_line(network: AwlNetwork, token: str) -> str:
    for line in network.raw_lines:
        if token.lower() in line.lower():
            return line.strip()
    return network.raw_lines[0].strip() if network.raw_lines else token


def _dedupe_step_networks(step_map: dict[str, StepCandidate]) -> list[StepCandidate]:
    steps = sorted(step_map.values(), key=lambda item: item.name)
    for step in steps:
        step.source_networks = sorted(set(step.source_networks))
        step.activation_networks = sorted(set(step.activation_networks))
        step.action_networks = sorted(set(step.action_networks))
    return steps


def _dedupe_list(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _dedupe_timers(items: list[tuple[str, str, str | None]]) -> list[tuple[str, str, str | None]]:
    ordered: dict[tuple[str, str, str | None], None] = {}
    for item in items:
        ordered[item] = None
    return list(ordered.keys())
