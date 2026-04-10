from __future__ import annotations

import re
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
    source_name: str | None = None,
) -> ConversionAnalysis:
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
    step_no_by_name = {step.name: step.step_no for step in step_nodes}

    transition_nodes = [
        GraphTransitionNode(
            name=transition.transition_id,
            transition_no=index + 1,
            source_step=transition.source_step,
            target_step=transition.target_step,
            guard_expression=transition.guard_expression,
            network_index=transition.network_index,
            db_block_name=_global_db_block_name(ir),
            db_member_name=_transition_db_member_name(transition),
        )
        for index, transition in enumerate(ir.transitions)
    ]

    # GRAPH often rejects terminal steps without a following element.
    # Add a deterministic fallback transition to the entry step for steps
    # that would otherwise remain without outgoing transitions.
    outgoing_from_ir: dict[str, int] = {}
    for transition in transition_nodes:
        outgoing_from_ir[transition.source_step] = outgoing_from_ir.get(transition.source_step, 0) + 1

    next_transition_no = len(transition_nodes) + 1
    for step in ordered_steps:
        if outgoing_from_ir.get(step.name, 0) > 0:
            continue
        if step.name != "S29":
            continue
        if step.name == entry_step and len(ordered_steps) == 1:
            continue

        synthetic_name = f"T_AUTO_{step.name}"
        transition_nodes.append(
            GraphTransitionNode(
                name=synthetic_name,
                transition_no=next_transition_no,
                source_step=step.name,
                target_step=entry_step,
                guard_expression="TRUE",
                network_index=0,
                db_block_name=_global_db_block_name(ir),
                db_member_name=_transition_db_member_name_from_values(synthetic_name, "TRUE"),
            )
        )
        next_transition_no += 1

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
                link_type=(
                    "Jump"
                    if step_no_by_name.get(transition.target_step, 10**9)
                    <= step_no_by_name.get(transition.source_step, -1)
                    else "Direct"
                ),
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
    return previews


def _build_graph_fb_xml(profile, ir: AwlIR, graph_topology: GraphTopology) -> str:
    static_members = ["    <Member Name=\"RT_DATA\" Datatype=\"G7_RTDataPlus_V2\" />"]
    static_members.extend(
        (
            f'    <Member Name="{escape(transition.name)}" Datatype="{profile.transition_runtime_type}">\n'
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
            f'    <Member Name="{escape(step.name)}" Datatype="{profile.step_runtime_type}">\n'
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
        temp_members = "    <Member Name=\"SEQ_TEMP\" Datatype=\"Bool\" />"

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
        '      <Section Name="Temp" />\n'
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
        '      <Number>1</Number>\n'
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
    members = _build_global_db_members(ir, graph_topology)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<Document>\n'
        '  <Engineering version="V20" />\n'
        '  <SW.Blocks.GlobalDB ID="0">\n'
        '    <AttributeList>\n'
        '      <Interface><Sections xmlns="http://www.siemens.com/automation/Openness/SW/Interface/v5">\n'
        '  <Section Name="Static">\n'
        f"{members}\n"
        '  </Section>\n'
        '</Sections></Interface>\n'
        '      <MemoryLayout>Optimized</MemoryLayout>\n'
        '      <MemoryReserve>100</MemoryReserve>\n'
        f'      <Name>{escape(ir.sequence_name)}_Global</Name>\n'
        '      <Namespace />\n'
        '      <Number>1</Number>\n'
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
        f'              <Text>{escape(ir.sequence_name)} Global</Text>\n'
        '            </AttributeList>\n'
        '          </MultilingualTextItem>\n'
        '        </ObjectList>\n'
        '      </MultilingualText>\n'
        '    </ObjectList>\n'
        '  </SW.Blocks.GlobalDB>\n'
        '</Document>\n'
    )


def _build_lad_fc_xml(ir: AwlIR, graph_topology: GraphTopology) -> str:
    temp_members = _build_lad_temp_members(ir)
    compile_units = _build_lad_compile_units(ir, graph_topology)
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
        f'      <Name>{escape(ir.sequence_name)}_LAD</Name>\n'
        '      <Namespace />\n'
        '      <Number>2</Number>\n'
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


def _build_global_db_members(ir: AwlIR, graph_topology: GraphTopology) -> str:
    members: list[str] = []

    for transition in graph_topology.transition_nodes:
        guard_member = transition.db_member_name
        members.append(
            (
                f'    <Member Name="{escape(guard_member)}" Datatype="Bool">\n'
                '      <Comment Informative="true">\n'
                f'        <MultiLanguageText Lang="en-US">Transition guard for {escape(transition.name)}</MultiLanguageText>\n'
                '      </Comment>\n'
                '    </Member>'
            )
        )

    for memory in ir.memories:
        members.append(
            (
                f'    <Member Name="{escape(_db_member_name(memory.name))}" Datatype="Bool">\n'
                '      <Comment Informative="true">\n'
                f'        <MultiLanguageText Lang="en-US">{escape(memory.role)}</MultiLanguageText>\n'
                '      </Comment>\n'
                '    </Member>'
            )
        )

    if not members:
        members.append('    <Member Name="NoData" Datatype="Bool" />')
    return "\n".join(dict.fromkeys(members))


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
        units.append(
            '      <SW.Blocks.CompileUnit ID="'
            + unit_id
            + '" CompositionName="CompileUnits">\n'
            '        <AttributeList>\n'
            '          <NetworkSource><FlgNet xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5">\n'
            '  <Parts>\n'
            '    <Access Scope="GlobalVariable" UId="21">\n'
            '      <Symbol>\n'
            f'        <Component Name="{target_db_name}" />\n'
            f'        <Component Name="{target_member_name}" />\n'
            '      </Symbol>\n'
            '    </Access>\n'
            '    <Part Name="Contact" UId="22" />\n'
            '    <Access Scope="GlobalVariable" UId="23">\n'
            '      <Symbol>\n'
            f'        <Component Name="{target_db_name}" />\n'
            f'        <Component Name="{target_member_name}" />\n'
            '      </Symbol>\n'
            '    </Access>\n'
            '    <Part Name="Coil" UId="24" />\n'
            '  </Parts>\n'
            '  <Wires>\n'
            '    <Wire UId="25">\n'
            '      <Powerrail />\n'
            '      <NameCon UId="22" Name="in" />\n'
            '    </Wire>\n'
            '    <Wire UId="26">\n'
            '      <IdentCon UId="21" />\n'
            '      <NameCon UId="22" Name="operand" />\n'
            '    </Wire>\n'
            '    <Wire UId="27">\n'
            '      <NameCon UId="22" Name="out" />\n'
            '      <NameCon UId="24" Name="in" />\n'
            '    </Wire>\n'
            '    <Wire UId="28">\n'
            '      <IdentCon UId="23" />\n'
            '      <NameCon UId="24" Name="operand" />\n'
            '    </Wire>\n'
            '  </Wires>\n'
            '</FlgNet></NetworkSource>\n'
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


def _render_graph_step(step: GraphStepNode) -> str:
    return (
        f'      <Step Number="{step.step_no}" Init="{str(step.init).lower()}" '
        f'Name="{escape(step.name)}" MaximumStepTime="T#10S" WarningTime="T#7S">\n'
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
    return (
        f'      <Transition IsMissing="false" Name="{escape(transition.name)}" '
        f'Number="{transition.transition_no}" ProgrammingLanguage="LAD">\n'
        '        <FlgNet>\n'
        '          <Parts>\n'
        '            <Access Scope="GlobalVariable" UId="21">\n'
        '              <Symbol>\n'
        f'                <Component Name="{escape(transition.db_block_name)}" />\n'
        f'                <Component Name="{escape(transition.db_member_name)}" />\n'
        '              </Symbol>\n'
        '            </Access>\n'
        '            <Part Name="Contact" UId="22" />\n'
        '            <Part Name="TrCoil" UId="23" />\n'
        '          </Parts>\n'
        '          <Wires>\n'
        '            <Wire UId="24">\n'
        '              <Powerrail />\n'
        '              <NameCon UId="22" Name="in" />\n'
        '            </Wire>\n'
        '            <Wire UId="25">\n'
        '              <IdentCon UId="21" />\n'
        '              <NameCon UId="22" Name="operand" />\n'
        '            </Wire>\n'
        '            <Wire UId="26">\n'
        '              <NameCon UId="22" Name="out" />\n'
        '              <NameCon UId="23" Name="in" />\n'
        '            </Wire>\n'
        '          </Wires>\n'
        '        </FlgNet>\n'
        '      </Transition>'
    )


def _render_graph_branch(branch: GraphBranchNode) -> str:
    return f'      <Branch Number="1" Name="{escape(branch.name)}" Type="{escape(branch.branch_type)}" />'


def _render_graph_connection(connection: GraphConnection, graph_topology: GraphTopology) -> str:
    return (
        '      <Connection>\n'
        '        <NodeFrom>\n'
        f'{_render_graph_node_ref(connection.source_ref, graph_topology)}\n'
        '        </NodeFrom>\n'
        '        <NodeTo>\n'
        f'{_render_graph_node_ref(connection.target_ref, graph_topology)}\n'
        '        </NodeTo>\n'
        f'        <LinkType>{escape(connection.link_type)}</LinkType>\n'
        '      </Connection>'
    )


def _render_graph_node_ref(ref: str, graph_topology: GraphTopology) -> str:
    step = next((item for item in graph_topology.step_nodes if item.name == ref), None)
    if step is not None:
        return f'          <StepRef Number="{step.step_no}" />'
    transition = next((item for item in graph_topology.transition_nodes if item.name == ref), None)
    if transition is not None:
        return f'          <TransitionRef Number="{transition.transition_no}" />'
    branch = next((item for item in graph_topology.branch_nodes if item.name == ref), None)
    if branch is not None:
        return f'          <BranchRef Name="{escape(branch.name)}" />'
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
    return f"{ir.sequence_name}_Global"


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
