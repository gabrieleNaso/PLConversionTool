from __future__ import annotations

import re

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


def analyze_awl_source(
    sequence_name: str | None,
    awl_source: str,
    include_fc_block: bool = True,
    source_name: str | None = None,
) -> ConversionAnalysis:
    scaffold = build_conversion_scaffold(
        sequence_name=sequence_name,
        awl_source=awl_source,
        include_fc_block=include_fc_block,
        source_name=source_name,
    )
    source_label = source_name or f"{scaffold.sequence_name}.awl"
    networks = _parse_networks(awl_source)
    ir = _build_ir(scaffold.sequence_name, source_label, networks)
    graph_topology = _build_graph_topology(ir)
    issues = _validate_ir(ir, graph_topology)
    previews = _build_artifact_previews(scaffold, ir, graph_topology)
    return ConversionAnalysis(
        scaffold=scaffold,
        ir=ir,
        graph_topology=graph_topology,
        validation_issues=issues,
        artifact_previews=previews,
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

    assumptions = [
        "Il parser usa euristiche incrementali sui pattern AWL piu' frequenti.",
        "Le transizioni vengono dedotte da step letti nello stesso network e step attivati tramite S/=.",
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

    step_nodes = [
        GraphStepNode(
            name=step.name,
            step_no=index + 1,
            init=step.name == entry_step,
            source_step=step.name,
            action_networks=step.action_networks,
        )
        for index, step in enumerate(ordered_steps)
    ]

    transition_nodes = [
        GraphTransitionNode(
            name=transition.transition_id,
            transition_no=index + 1,
            source_step=transition.source_step,
            target_step=transition.target_step,
            guard_expression=transition.guard_expression,
            network_index=transition.network_index,
        )
        for index, transition in enumerate(ir.transitions)
    ]

    transitions_by_source: dict[str, list[GraphTransitionNode]] = {}
    for transition in transition_nodes:
        transitions_by_source.setdefault(transition.source_step, []).append(transition)

    branch_nodes: list[GraphBranchNode] = []
    branch_by_owner: dict[str, GraphBranchNode] = {}
    for source_step, items in transitions_by_source.items():
        if len(items) <= 1:
            continue
        branch = GraphBranchNode(
            name=f"B_{source_step}",
            branch_type="AltBegin",
            owner_step=source_step,
            transition_targets=[item.name for item in items],
        )
        branch_nodes.append(branch)
        branch_by_owner[source_step] = branch

    connections: list[GraphConnection] = []
    for transition in transition_nodes:
        source_ref = transition.source_step
        if transition.source_step in branch_by_owner:
            branch = branch_by_owner[transition.source_step]
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
        connections.append(
            GraphConnection(
                source_ref=transition.name,
                target_ref=transition.target_step,
                link_type="Direct",
            )
        )

    warnings: list[str] = []
    outgoing_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    incoming_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    for transition in transition_nodes:
        outgoing_counts[transition.source_step] = outgoing_counts.get(transition.source_step, 0) + 1
        incoming_counts[transition.target_step] = incoming_counts.get(transition.target_step, 0) + 1

    for step_name, count in outgoing_counts.items():
        if count > 1 and step_name not in branch_by_owner:
            warnings.append(
                f"Il passo {step_name} ha {count} uscite: servira' introdurre branch target dedicati."
            )

    for step_name, count in incoming_counts.items():
        if step_name != entry_step and count > 1:
            warnings.append(
                f"Il passo {step_name} riceve {count} ingressi: potrebbe servire un join o link Jump."
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
    for warning in graph_topology.warnings:
        issues.append(
            ValidationIssue(
                level="warning",
                code="GRAPH_TOPOLOGY_WARNING",
                message=warning,
            )
        )
    return issues


def _build_artifact_previews(scaffold, ir: AwlIR, graph_topology: GraphTopology) -> list[ArtifactPreview]:
    profile = build_target_profile()
    step_runtime_lines = "\n".join(
        (
            f'      <Member Name="{step.name}" Datatype="{profile.step_runtime_type}">'
            f'<Attribute Name="SNO" Value="{step.step_no}" /></Member>'
        )
        for step in graph_topology.step_nodes
    )
    transition_runtime_lines = "\n".join(
        (
            f'      <Member Name="{transition.name}" Datatype="{profile.transition_runtime_type}">'
            f'<Attribute Name="TNO" Value="{transition.transition_no}" /></Member>'
        )
        for transition in graph_topology.transition_nodes
    )
    steps_xml = "\n".join(
        (
            f'      <Step Name="{step.name}" SNO="{step.step_no}" '
            f'Init="{str(step.init).lower()}" SourceStep="{step.source_step}" />'
        )
        for step in graph_topology.step_nodes
    )
    transitions_xml = "\n".join(
        (
            f'      <Transition Name="{transition.name}" TNO="{transition.transition_no}" '
            f'Source="{transition.source_step}" Target="{transition.target_step}" '
            f'Guard="{transition.guard_expression}" Network="{transition.network_index}" />'
        )
        for transition in graph_topology.transition_nodes
    )
    branches_xml = "\n".join(
        (
            f'      <Branch Name="{branch.name}" BranchType="{branch.branch_type}" '
            f'OwnerStep="{branch.owner_step}" />'
        )
        for branch in graph_topology.branch_nodes
    )
    connections_xml = "\n".join(
        (
            f'      <Connection SourceRef="{connection.source_ref}" '
            f'TargetRef="{connection.target_ref}" LinkType="{connection.link_type}" />'
        )
        for connection in graph_topology.connections
    )
    db_members = "\n".join(
        f'      <Member Name="{memory.name}" Comment="{memory.role}" />' for memory in ir.memories
    )
    fc_comments = "\n".join(
        f"// {output.name} <- {output.action} (network {output.network_index})" for output in ir.outputs
    )

    graph_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<Document>\n'
        f'  <Engineering version="{profile.tia_portal_version}" />\n'
        f'  <SW.Blocks.FB Name="{ir.sequence_name}">\n'
        f'    <AttributeList>\n'
        f'      <ProgrammingLanguage>GRAPH</ProgrammingLanguage>\n'
        f'      <GraphVersion>2.0</GraphVersion>\n'
        f'    </AttributeList>\n'
        f'    <Interface>\n'
        f'      <Section Name="Static">\n'
        f'      <Member Name="RT_DATA" Datatype="{profile.graph_runtime_type}" />\n'
        f"{transition_runtime_lines}\n"
        f"{step_runtime_lines}\n"
        f'      </Section>\n'
        f'    </Interface>\n'
        f'    <Sequence>\n'
        f"{steps_xml}\n"
        f"{transitions_xml}\n"
        f'      <Branches>\n'
        f"{branches_xml}\n"
        f'      </Branches>\n'
        f'      <Connections>\n'
        f"{connections_xml}\n"
        f'      </Connections>\n'
        f'    </Sequence>\n'
        f'  </SW.Blocks.FB>\n'
        f'</Document>\n'
    )
    db_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<Document>\n'
        f'  <SW.Blocks.GlobalDB Name="{ir.sequence_name}_Companion">\n'
        f'    <Sections>\n'
        f'      <Section Name="Map" />\n'
        f'      <Section Name="Diag" />\n'
        f'      <Section Name="Cmd" />\n'
        f'    </Sections>\n'
        f'    <Members>\n'
        f"{db_members}\n"
        f'    </Members>\n'
        f'  </SW.Blocks.GlobalDB>\n'
        f'</Document>\n'
    )
    fc_xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<Document>\n'
        f'  <SW.Blocks.FC Name="{ir.sequence_name}_Support">\n'
        f'    <AttributeList>\n'
        f'      <ProgrammingLanguage>LAD</ProgrammingLanguage>\n'
        f'    </AttributeList>\n'
        f'    <Source><![CDATA[\n'
        f"{fc_comments}\n"
        f'    ]]></Source>\n'
        f'  </SW.Blocks.FC>\n'
        f'</Document>\n'
    )

    previews = [
        ArtifactPreview(
            artifact_type="graph_fb",
            file_name=scaffold.artifact_plan.graph_fb_name,
            content=graph_xml,
        ),
        ArtifactPreview(
            artifact_type="companion_db",
            file_name=scaffold.artifact_plan.companion_db_name,
            content=db_xml,
        ),
    ]
    if scaffold.artifact_plan.support_fc_name:
        previews.append(
            ArtifactPreview(
                artifact_type="support_fc",
                file_name=scaffold.artifact_plan.support_fc_name,
                content=fc_xml,
            )
        )
    return previews


def _step_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", name)
    if match:
        return int(match.group(1)), name
    return 10**9, name


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
        candidate = instr.args[0].rstrip(",")
        if STEP_RE.fullmatch(candidate):
            continue
        operands.append(candidate.upper())
    return _dedupe_list(operands)


def _collect_step_targets(network: AwlNetwork) -> list[str]:
    targets: list[str] = []
    for instr in network.instructions:
        if instr.opcode not in {"S", "="}:
            continue
        if not instr.args:
            continue
        candidate = instr.args[0].rstrip(",").upper()
        if STEP_RE.fullmatch(candidate):
            targets.append(candidate)
    return _dedupe_list(targets)


def _collect_timers(network: AwlNetwork) -> list[tuple[str, str, str | None]]:
    timers: list[tuple[str, str, str | None]] = []
    for instr in network.instructions:
        preset = None
        if instr.opcode in TIMER_OPCODES and instr.args:
            timer_name = instr.args[0].rstrip(",").upper()
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
        candidate = instr.args[0].rstrip(",").upper()
        if MEMORY_RE.fullmatch(candidate):
            targets.append((candidate, instr.opcode))
    return targets


def _collect_output_targets(network: AwlNetwork) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for instr in network.instructions:
        if instr.opcode not in ACTION_OPCODES or not instr.args:
            continue
        candidate = instr.args[0].rstrip(",").upper()
        if OUTPUT_RE.fullmatch(candidate):
            targets.append((candidate, instr.opcode))
    return targets


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
