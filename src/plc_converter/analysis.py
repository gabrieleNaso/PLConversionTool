from __future__ import annotations

import copy
import hashlib
import re
from xml.sax.saxutils import escape

from .domain import (
    ArtifactPlan,
    ArtifactPreview,
    AwlIR,
    AwlInstruction,
    AwlNetwork,
    ConversionRoadmap,
    ConversionAnalysis,
    ConversionScaffold,
    GraphBranchNode,
    FaultCandidate,
    GraphConnection,
    GraphStepNode,
    GraphTopology,
    GraphTransitionNode,
    MemberIR,
    MemoryCandidate,
    OutputCandidate,
    SourceAnalysis,
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
OUTPUT_RE = re.compile(r"\b(?:A|Q)\d+(?:\.\d+)?\b", re.IGNORECASE)
EXTERNAL_RE = re.compile(
    r"\b(?:"
    r"[EIQA]\d+(?:\.\d+)?"
    r"|DB\d+(?:\.(?:DB[XBWD]\d+(?:\.\d+)?|D[IBD]\d+))?"
    r"|(?:DI|PE|PA)\d+(?:\.\d+)?"
    r")\b",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"\b[A-Z_]\w*(?:\.\w+)*\b", re.IGNORECASE)
CONDITION_OPCODES = {"U", "UN", "O", "ON", "A", "AN", "X", "XN"}
ACTION_OPCODES = {"S", "R", "="}
JUMP_OPCODES = {"JC", "JCN", "JU"}
TIMER_OPCODES = {"SD", "SE", "SP", "SS", "SF"}
SUPPORT_BLOCK_SCHEMA = {
    "io": {"token": "IO", "file_token": "io"},
    "diag": {"token": "ALARMS", "file_token": "alarms"},
    "mode": {"token": "LEV2", "file_token": "lev2"},
    "network": {"token": "N", "file_token": "n"},
    "external": {"token": "EXT", "file_token": "ext"},
    "parameters": {"token": "PARAMETERS", "file_token": "parameters"},
    "hmi": {"token": "HMI", "file_token": "hmi"},
    "aux": {"token": "AUX", "file_token": "aux"},
    "transitions": {"token": "TRANSITIONS", "file_token": "transitions"},
    "output": {"token": "OUTPUT", "file_token": "output"},
}

DB_FAMILY_PREFIX = {
    "base": "DB11",
    "hmi": "DB12",
    "aux": "DB13",
    "transitions": "DB14",
    "graph": "DB15",
    "sequence": "DB16",
    "lev2": "DB17",
    "ext": "DB18",
    "output": "DB19",
}

FC_FAMILY_PREFIX = {
    "base": "FC11",
    "hmi": "FC12",
    "aux": "FC13",
    "transitions": "FC14",
    "sequence": "FC16",
    "lev2": "FC17",
    "ext": "FC18",
    "output": "FC19",
}

DB_FAMILY_NUMBER_BASE = {
    "base": 1100,
    "hmi": 1200,
    "aux": 1300,
    "transitions": 1400,
    "graph": 1500,
    "sequence": 1600,
    "lev2": 1700,
    "ext": 1800,
    "output": 1900,
}

FC_FAMILY_NUMBER_BASE = {
    "base": 1100,
    "hmi": 1200,
    "aux": 1300,
    "transitions": 1400,
    "sequence": 1600,
    "lev2": 1700,
    "output": 1900,
}

SUPPORT_FAMILY_OVERRIDES = {
    "diag": {"db_family": "base", "fc_family": "base"},
    "io": {"db_family": "sequence", "fc_family": "sequence"},
    "mode": {"db_family": "lev2", "fc_family": "lev2"},
    "external": {"db_family": "ext"},
    "parameters": {"db_family": "aux"},
    "hmi": {"db_family": "hmi", "fc_family": "hmi"},
    "aux": {"db_family": "output", "fc_family": "aux"},
    "transitions": {"db_family": "transitions", "fc_family": "transitions"},
    "output": {"db_family": "sequence", "fc_family": "sequence"},
}

TIA_MEMBER_NAME_MAX_LEN = 96
TIA_RESERVED_KEYWORDS = {
    "AND",
    "OR",
    "NOT",
    "XOR",
    "TRUE",
    "FALSE",
}

# Experimental translation rules must be opt-in. Keeping this off by default
# prevents unintended topology inflation (e.g. synthetic S100/S101 branches).
ENABLE_TRACKING_TRANSLATION_RULE = False

EXTERNAL_DB_IDS = {81, 82, 202}


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


def analyze_ir_payload(
    ir_payload: dict,
    sequence_name: str | None = None,
    source_name: str | None = None,
) -> ConversionAnalysis:
    ir = _ir_from_payload(ir_payload=ir_payload, sequence_name=sequence_name, source_name=source_name)
    scaffold = _build_ir_scaffold(ir)
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


def _ir_from_payload(
    ir_payload: dict,
    sequence_name: str | None = None,
    source_name: str | None = None,
) -> AwlIR:
    raw_sequence = sequence_name or ir_payload.get("sequence_name") or "Sequence"
    normalized_sequence = re.sub(r"[^A-Za-z0-9]+", "_", str(raw_sequence)).strip("_") or "Sequence"
    source_label = source_name or ir_payload.get("source_name") or f"{normalized_sequence}_ir.json"

    networks_payload = ir_payload.get("networks") or []
    networks: list[AwlNetwork] = []
    for fallback_index, raw_network in enumerate(networks_payload, start=1):
        network_index = _as_int(raw_network.get("index"), fallback_index)
        raw_lines = _as_str_list(raw_network.get("raw_lines"))
        instructions_payload = raw_network.get("instructions") or []
        instructions: list[AwlInstruction] = []
        for line_fallback, raw_instruction in enumerate(instructions_payload, start=1):
            args = _as_str_list(raw_instruction.get("args"))
            raw = str(raw_instruction.get("raw") or "").strip()
            if not raw:
                rendered_args = f" {' '.join(args)}" if args else ""
                raw = f"{str(raw_instruction.get('opcode') or '').upper()}{rendered_args}".strip()
            instructions.append(
                AwlInstruction(
                    line_no=_as_int(raw_instruction.get("line_no"), line_fallback),
                    network_index=network_index,
                    label=_as_optional_str(raw_instruction.get("label")),
                    opcode=str(raw_instruction.get("opcode") or "NOP").upper(),
                    args=args,
                    raw=raw,
                )
            )

        networks.append(
            AwlNetwork(
                index=network_index,
                title=_as_optional_str(raw_network.get("title")),
                raw_lines=raw_lines,
                instructions=instructions,
            )
        )

    transitions_payload = ir_payload.get("transitions") or []
    if not networks:
        synthetic_indexes = sorted(
            {
                _as_int(item.get("network_index"), 1)
                for item in transitions_payload
                if isinstance(item, dict)
            }
        )
        if not synthetic_indexes:
            synthetic_indexes = [1]
        networks = [
            AwlNetwork(index=index, title=f"IR_Network_{index}", raw_lines=[], instructions=[])
            for index in synthetic_indexes
        ]

    steps = [
        StepCandidate(
            name=str(item.get("name") or "").strip(),
            step_number=_as_positive_int(item.get("step_number")),
            source_networks=_as_int_list(item.get("source_networks")),
            activation_networks=_as_int_list(item.get("activation_networks")),
            action_networks=_as_int_list(item.get("action_networks")),
        )
        for item in (ir_payload.get("steps") or [])
        if str(item.get("name") or "").strip()
    ]

    transitions = [
        TransitionCandidate(
            transition_id=str(item.get("transition_id") or f"T{index}"),
            source_step=str(item.get("source_step") or "").strip(),
            target_step=str(item.get("target_step") or "").strip(),
            network_index=_as_int(item.get("network_index"), 1),
            guard_expression=str(item.get("guard_expression") or "TRUE"),
            guard_operands=_as_str_list(item.get("guard_operands")),
            jump_labels=_as_str_list(item.get("jump_labels")),
            flow_type=_normalize_flow_type(item.get("flow_type")),
            parallel_group=_as_optional_str(item.get("parallel_group")) or "",
        )
        for index, item in enumerate(transitions_payload, start=1)
        if str(item.get("source_step") or "").strip() and str(item.get("target_step") or "").strip()
    ]

    # Ensure topology consistency: every step referenced by transitions must exist
    # in the steps list, otherwise Graph connections can degrade to EndConnection.
    existing_step_names = {item.name for item in steps}
    for transition in transitions:
        for step_name in (transition.source_step, transition.target_step):
            if step_name and step_name not in existing_step_names:
                steps.append(StepCandidate(name=step_name))
                existing_step_names.add(step_name)
    timers = [
        TimerCandidate(
            source_timer=str(item.get("source_timer") or "").strip(),
            network_index=_as_int(item.get("network_index"), 1),
            kind=str(item.get("kind") or "SD").upper(),
            preset=_as_optional_str(item.get("preset")),
            trigger_operands=_as_str_list(item.get("trigger_operands")),
        )
        for item in (ir_payload.get("timers") or [])
        if str(item.get("source_timer") or "").strip()
    ]

    memories = [
        MemoryCandidate(
            name=str(item.get("name") or "").strip(),
            role=str(item.get("role") or "aux"),
            network_index=_as_int(item.get("network_index"), 1),
        )
        for item in (ir_payload.get("memories") or [])
        if str(item.get("name") or "").strip()
    ]

    faults = [
        FaultCandidate(
            name=str(item.get("name") or "").strip(),
            network_index=_as_int(item.get("network_index"), 1),
            evidence=str(item.get("evidence") or "").strip(),
        )
        for item in (ir_payload.get("faults") or [])
        if str(item.get("name") or "").strip()
    ]

    outputs = [
        OutputCandidate(
            name=str(item.get("name") or "").strip(),
            network_index=_as_int(item.get("network_index"), 1),
            action=str(item.get("action") or "="),
        )
        for item in (ir_payload.get("outputs") or [])
        if str(item.get("name") or "").strip()
    ]

    return AwlIR(
        sequence_name=normalized_sequence,
        source_name=source_label,
        networks=sorted(networks, key=lambda item: item.index),
        steps=steps,
        transitions=transitions,
        timers=timers,
        memories=memories,
        faults=faults,
        outputs=outputs,
        manual_logic_networks=_as_int_list(ir_payload.get("manual_logic_networks")),
        auto_logic_networks=_as_int_list(ir_payload.get("auto_logic_networks")),
        external_refs=sorted(set(_as_str_list(ir_payload.get("external_refs")))),
        strict_operand_catalog=bool(ir_payload.get("strict_operand_catalog", False)),
        operand_catalog=sorted(set(_as_str_list(ir_payload.get("operand_catalog")))),
        operand_datatypes=_as_str_dict(ir_payload.get("operand_datatypes")),
        operand_categories=_as_str_dict(ir_payload.get("operand_categories")),
        operand_notes=_as_str_dict(ir_payload.get("operand_notes")),
        operand_control_settings=_as_str_dict_dict(ir_payload.get("operand_control_settings")),
        operand_timer_settings=_as_str_dict_dict(ir_payload.get("operand_timer_settings")),
        support_members=_as_dict_list(ir_payload.get("support_members")),
        support_logic=_as_dict_list(ir_payload.get("support_logic")),
        assumptions=_as_str_list(ir_payload.get("assumptions"))
        or [
            "IR caricato da JSON esterno (es. Excel): verificare coerenza semantica delle guardie prima dell'import TIA."
        ],
    )


def _ensure_s1_entry_step(
    steps: list[StepCandidate],
    transitions: list[TransitionCandidate],
) -> None:
    step_names = [item.name for item in steps if item.name]
    if "S1" in step_names:
        return

    transition_refs = {
        token
        for item in transitions
        for token in (item.source_step, item.target_step)
        if token
    }

    # If transitions already reference S1, ensure steps contains it and keep
    # original sequence untouched.
    if "S1" in transition_refs:
        steps.insert(0, StepCandidate(name="S1"))
        return

    # Pick the real entry step and rename it to S1 so topology is preserved
    # without adding synthetic jumps/transitions.
    incoming_targets = {item.target_step for item in transitions if item.target_step}
    entry_candidates = [name for name in step_names if name not in incoming_targets]

    preferred = next(
        (
            name
            for name in entry_candidates
            if name and name.lower() in {"init", "start", "inizio"}
        ),
        None,
    )
    if preferred is None and entry_candidates:
        preferred = entry_candidates[0]

    if preferred is None:
        preferred = next((item.source_step for item in transitions if item.source_step), None)

    if preferred is None and step_names:
        preferred = step_names[0]

    if preferred:
        _rename_step_token(preferred, "S1", steps, transitions)
        return

    steps.insert(0, StepCandidate(name="S1"))


def _rename_step_token(
    original: str,
    replacement: str,
    steps: list[StepCandidate],
    transitions: list[TransitionCandidate],
) -> None:
    if not original or original == replacement:
        if replacement and all(item.name != replacement for item in steps):
            steps.insert(0, StepCandidate(name=replacement))
        return

    replaced = False
    for item in steps:
        if item.name == original:
            item.name = replacement
            replaced = True

    for item in transitions:
        if item.source_step == original:
            item.source_step = replacement
            replaced = True
        if item.target_step == original:
            item.target_step = replacement
            replaced = True

    if not replaced and replacement and all(item.name != replacement for item in steps):
        steps.insert(0, StepCandidate(name=replacement))


def _next_transition_id(transitions: list[TransitionCandidate]) -> str:
    used = {item.transition_id for item in transitions}
    index = 1
    while True:
        candidate = f"T{index}"
        if candidate not in used:
            return candidate
        index += 1


def _apply_translation_rules(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
) -> None:
    if not transitions:
        return

    context = _derive_translation_context(step_map, transitions)

    # Rule family 1: recovery branch synthesis (generalized, not source-specific).
    entry_step = context.get("entry_step", "")
    has_high_entry_outgoing = any(
        item.source_step == entry_step and _step_number_from_token(item.target_step) >= 29
        for item in transitions
    )
    if entry_step and context.get("cycle_target_step") and has_high_entry_outgoing:
        _augment_fault_branch(step_map, transitions, context)
        _augment_end_step(step_map, transitions, context)
        _augment_recycle_split_branch(step_map, transitions, context)

    # Rule 2: tracking micro-flow extraction (opt-in).
    if ENABLE_TRACKING_TRANSLATION_RULE:
        _augment_tracking_branch(step_map, transitions)


def _augment_fault_branch(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
    context: dict[str, str],
) -> None:
    if any(item.name == "S30_Fault" or item.step_number == 30 for item in step_map.values()):
        return

    entry_step = context.get("entry_step", "")
    fault_target_step = context.get("fault_target_step", "")
    if not entry_step or not fault_target_step:
        return

    fault_seed = next(
        (
            item
            for item in transitions
            if item.source_step == entry_step
            and item.target_step == fault_target_step
            and _transition_looks_fault_related(item)
        ),
        None,
    )
    if fault_seed is None:
        fault_seed = next(
            (
                item
                for item in transitions
                if item.source_step == entry_step and item.target_step == fault_target_step
            ),
            None,
        )
    if fault_seed is None:
        return

    fault_step_name = "S30_Fault"
    step_map[fault_step_name] = StepCandidate(
        name=fault_step_name,
        step_number=30,
        source_networks=[fault_seed.network_index],
        activation_networks=[fault_seed.network_index],
    )

    if not _has_transition_between(transitions, fault_seed.source_step, fault_step_name):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=fault_seed.source_step,
                target_step=fault_step_name,
                network_index=fault_seed.network_index,
                guard_expression=fault_seed.guard_expression or "TRUE",
                guard_operands=list(fault_seed.guard_operands),
                jump_labels=list(fault_seed.jump_labels),
            )
        )

    entry = entry_step if entry_step in step_map else _infer_default_trs_source_step(step_map)
    if entry and entry != fault_step_name and not _has_transition_between(transitions, fault_step_name, entry):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=fault_step_name,
                target_step=entry,
                network_index=fault_seed.network_index,
                guard_expression="TRUE",
                guard_operands=[],
                jump_labels=[],
            )
        )


def _augment_end_step(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
    context: dict[str, str],
) -> None:
    if any(item.name == "S28_END" or item.step_number == 28 for item in step_map.values()):
        return

    cycle_target = context.get("cycle_target_step", "")
    if not cycle_target:
        return

    cycle_seed = next(
        (
            item
            for item in transitions
            if item.target_step == cycle_target and _step_number_from_token(item.source_step) >= 20
        ),
        None,
    )
    if cycle_seed is None:
        return

    end_step_name = "S28_END"
    step_map[end_step_name] = StepCandidate(
        name=end_step_name,
        step_number=28,
        source_networks=[cycle_seed.network_index],
        activation_networks=[cycle_seed.network_index],
    )
    cycle_seed.target_step = end_step_name

    if not _has_transition_between(transitions, end_step_name, cycle_target):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=end_step_name,
                target_step=cycle_target,
                network_index=cycle_seed.network_index,
                guard_expression="TRUE",
                guard_operands=[],
                jump_labels=[],
            )
        )


def _augment_recycle_split_branch(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
    context: dict[str, str],
) -> None:
    recycle_source = context.get("recycle_source_step", "")
    recycle_forward = context.get("recycle_forward_target_step", "")
    recycle_back = context.get("cycle_target_step", "")
    if not recycle_source or not recycle_forward or not recycle_back:
        return
    if recycle_source not in step_map or recycle_back not in step_map:
        return
    if not _has_transition_between(transitions, recycle_source, recycle_forward):
        return
    if _has_transition_between(transitions, recycle_source, recycle_back):
        return

    seed = next(
        (
            item
            for item in transitions
            if item.source_step == recycle_source and item.target_step == recycle_forward
        ),
        None,
    )
    network_index = seed.network_index if seed else 0
    transitions.append(
        TransitionCandidate(
            transition_id=_next_transition_id(transitions),
            source_step=recycle_source,
            target_step=recycle_back,
            network_index=network_index,
            guard_expression="TRUE",
            guard_operands=[],
            jump_labels=[],
        )
    )


def _derive_translation_context(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
) -> dict[str, str]:
    context: dict[str, str] = {}
    if not transitions:
        return context

    step_names = set(step_map.keys())
    numbered_steps = [name for name in step_names if _step_number_from_token(name) > 0]
    if "S1" in step_names:
        context["entry_step"] = "S1"
    elif numbered_steps:
        context["entry_step"] = min(numbered_steps, key=_step_number_from_token)

    cycle_candidates = [
        item.target_step
        for item in transitions
        if _step_number_from_token(item.source_step) >= 20
        and _step_number_from_token(item.target_step) > 0
        and _step_number_from_token(item.target_step) < _step_number_from_token(item.source_step)
    ]
    if cycle_candidates:
        entry_step = context.get("entry_step", "")
        non_entry_candidates = [name for name in cycle_candidates if name != entry_step]
        candidates_for_scoring = non_entry_candidates or cycle_candidates
        # Most frequent recycle target (typically S3 in legacy sequencers).
        scores: dict[str, int] = {}
        for name in candidates_for_scoring:
            scores[name] = scores.get(name, 0) + 1
        context["cycle_target_step"] = sorted(scores.items(), key=lambda kv: (-kv[1], _step_number_from_token(kv[0])))[0][0]

    entry_step = context.get("entry_step", "")
    if entry_step:
        fault_transition = next(
            (
                item
                for item in transitions
                if item.source_step == entry_step and _transition_looks_fault_related(item)
            ),
            None,
        )
        if fault_transition is None:
            # Fallback: choose an entry outgoing step that has a return edge to entry
            # and looks like a high-priority state (high step number).
            entry_outgoing = [
                item for item in transitions if item.source_step == entry_step and item.target_step != entry_step
            ]
            ranked = sorted(
                entry_outgoing,
                key=lambda item: _step_number_from_token(item.target_step),
                reverse=True,
            )
            for candidate in ranked:
                target = candidate.target_step
                if _step_number_from_token(target) < 30:
                    continue
                if _has_transition_between(transitions, target, entry_step):
                    fault_transition = candidate
                    break
        if fault_transition is not None:
            context["fault_target_step"] = fault_transition.target_step

        # Recycle split source: low/mid step forwarding to a higher step
        # while the sequence also has a recycle target.
        recycle_seed = next(
            (
                item
                for item in transitions
                if item.source_step != entry_step
                and _step_number_from_token(item.source_step) >= 6
                and _step_number_from_token(item.source_step) <= 10
                and _step_number_from_token(item.target_step) > _step_number_from_token(item.source_step)
                and _step_number_from_token(item.target_step) >= 10
                and _step_number_from_token(item.target_step) <= 18
            ),
            None,
        )
        if recycle_seed is not None:
            context["recycle_source_step"] = recycle_seed.source_step
            context["recycle_forward_target_step"] = recycle_seed.target_step

    return context


def _has_transition_between(
    transitions: list[TransitionCandidate],
    source_step: str,
    target_step: str,
) -> bool:
    return any(item.source_step == source_step and item.target_step == target_step for item in transitions)


def _transition_looks_fault_related(item: TransitionCandidate) -> bool:
    text = " ".join(
        [
            str(item.guard_expression or ""),
            *[str(operand or "") for operand in item.guard_operands],
        ]
    ).upper()
    markers = ("EM", "EMERG", "FAULT", "ALARM", "ERROR")
    return any(marker in text for marker in markers)


def _step_number_from_token(token: str) -> int:
    match = re.fullmatch(r"S0*(\d+)", str(token or "").strip(), flags=re.IGNORECASE)
    if not match:
        return -1
    return int(match.group(1))


def _augment_tracking_branch(
    step_map: dict[str, StepCandidate],
    transitions: list[TransitionCandidate],
) -> None:
    if any(item.name == "S100_TRK_CHECK" or item.step_number == 100 for item in step_map.values()):
        return
    if any(item.name == "S101_TRK_TRANSFER" or item.step_number == 101 for item in step_map.values()):
        return

    seed = next((item for item in transitions if _is_tracking_seed_transition(item)), None)
    if seed is None:
        return

    source_step = str(seed.source_step or "").strip()
    original_target = str(seed.target_step or "").strip()
    if not source_step or not original_target or source_step == original_target:
        return

    check_step = "S100_TRK_CHECK"
    transfer_step = "S101_TRK_TRANSFER"
    step_map[check_step] = StepCandidate(
        name=check_step,
        step_number=100,
        source_networks=[seed.network_index],
        activation_networks=[seed.network_index],
    )
    step_map[transfer_step] = StepCandidate(
        name=transfer_step,
        step_number=101,
        source_networks=[seed.network_index],
        activation_networks=[seed.network_index],
    )

    # Redirect the seed transition into the tracking check step.
    seed.target_step = check_step

    if not _has_transition_between(transitions, check_step, original_target):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=check_step,
                target_step=original_target,
                network_index=seed.network_index,
                guard_expression="TRUE",
                guard_operands=[],
                jump_labels=[],
            )
        )

    tracking_ko_operand = _extract_negated_tracking_presence_operand(seed)
    if not _has_transition_between(transitions, check_step, transfer_step):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=check_step,
                target_step=transfer_step,
                network_index=seed.network_index,
                guard_expression=f"NOT {tracking_ko_operand}" if tracking_ko_operand else "TRUE",
                guard_operands=[tracking_ko_operand] if tracking_ko_operand else [],
                jump_labels=[],
            )
        )

    if not _has_transition_between(transitions, transfer_step, original_target):
        transitions.append(
            TransitionCandidate(
                transition_id=_next_transition_id(transitions),
                source_step=transfer_step,
                target_step=original_target,
                network_index=seed.network_index,
                guard_expression="TRUE",
                guard_operands=[],
                jump_labels=[],
            )
        )


def _is_tracking_seed_transition(item: TransitionCandidate) -> bool:
    operands = [str(op or "").strip().upper() for op in item.guard_operands if str(op or "").strip()]
    if len(operands) < 2:
        return False
    has_remote_step = any(re.fullmatch(r"DB\d+\.DBX6\.\d+", op, flags=re.IGNORECASE) for op in operands)
    has_remote_presence = any(re.fullmatch(r"DB\d+\.DBX23\.\d+", op, flags=re.IGNORECASE) for op in operands)
    if not (has_remote_step and has_remote_presence):
        return False

    source_no = _step_number_from_token(item.source_step)
    target_no = _step_number_from_token(item.target_step)
    if source_no < 0 or target_no < 0:
        return False
    # Keep it conservative: this branch usually appears in early cycle checks.
    if source_no > 10:
        return False
    return True


def _extract_negated_tracking_presence_operand(item: TransitionCandidate) -> str | None:
    clauses = _parse_guard_clauses(item.guard_expression, item.guard_operands)
    for clause in clauses:
        for operand, negated in clause:
            token = str(operand or "").strip().upper()
            if not token or not negated:
                continue
            if re.fullmatch(r"DB\d+\.DBX23\.\d+", token, flags=re.IGNORECASE):
                return token
    return None


def _build_ir_scaffold(ir: AwlIR) -> ConversionScaffold:
    network_count = len(ir.networks)
    line_count = sum(max(len(network.raw_lines), len(network.instructions), 1) for network in ir.networks)
    set_reset_count = sum(1 for output in ir.outputs if output.action in {"S", "R", "="})
    jump_count = sum(len(item.jump_labels) for item in ir.transitions)

    return ConversionScaffold(
        sequence_name=ir.sequence_name,
        target_profile=build_target_profile(),
        source_analysis=SourceAnalysis(
            source_kind="ir_json",
            source_name=ir.source_name,
            network_count=network_count,
            set_reset_count=set_reset_count,
            jump_count=jump_count,
            timer_hint_count=len(ir.timers),
            manual_mode_hint=bool(ir.manual_logic_networks),
            alarm_hint=bool(ir.faults),
            lines=line_count,
        ),
        artifact_plan=ArtifactPlan(
            graph_fb_name=f"FB_{ir.sequence_name}_GRAPH_auto.xml",
            global_db_name="",
            lad_fc_name=f"FC14_{ir.sequence_name}_transitions_lad_auto.xml",
            output_directory="data/output/",
            naming_notes=[
                "Naming allineato al flusso standard AWL per mantenere import e diff consistenti.",
            ],
        ),
        graph_static_contract=[
            "RT_DATA : G7_RTDataPlus_V2",
            "un member G7_TransitionPlus_V2 per ogni transition",
            "un member G7_StepPlus_V2 per ogni step",
        ],
        global_db_sections=["Cmd", "Fb", "Par", "En", "Diag", "Hmi", "Map"],
        orchestration_flow=[
            "excel/json source -> backend -> artifact previews",
            "backend genera bundle XML in data/output/",
            "tia-bridge importa e compila via windows agent",
        ],
        roadmap=ConversionRoadmap(
            phases=[
                "acquisizione IR da fonte esterna",
                "costruzione topologia GRAPH",
                "serializzazione XML baseline + support",
                "validazione/import in TIA",
            ],
            immediate_next_actions=[
                "validare gli identificatori step/transizione dell'IR",
                "controllare guard_expression e guard_operands nel report analysis",
            ],
            open_points=[
                "coerenza semantica tra rete originale e IR manuale",
            ],
        ),
        assumptions=ir.assumptions
        or [
            "IR compilato manualmente: verificare sempre i warning topologici prima dell'import.",
        ],
    )


def _as_optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_flow_type(value: object) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"parallel", "parallelo"}:
        return "parallel"
    return "alternative"


def _as_str_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[|,;]", text)
    return [part.strip() for part in parts if part.strip()]


def _as_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return default
    match = re.search(r"-?\d+", text)
    if not match:
        return default
    return int(match.group(0))


def _as_int_list(value: object) -> list[int]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_as_int(item) for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[|,;]", text)
    return [_as_int(part) for part in parts if str(part).strip()]


def _as_positive_int(value: object) -> int | None:
    parsed = _as_int(value, 0)
    return parsed if parsed > 0 else None


def _as_dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, object]] = []
    for element in value:
        if isinstance(element, dict):
            items.append(dict(element))
    return items


def _as_str_dict(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    items: dict[str, str] = {}
    for key, raw in value.items():
        key_text = str(key or "").strip()
        raw_text = str(raw or "").strip()
        if not key_text or not raw_text:
            continue
        items[key_text] = raw_text
    return items


def _as_str_dict_dict(value: object) -> dict[str, dict[str, str]]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, dict[str, str]] = {}
    for key, raw in value.items():
        key_text = str(key or "").strip()
        if not key_text or not isinstance(raw, dict):
            continue
        item: dict[str, str] = {}
        for sub_key, sub_raw in raw.items():
            sub_key_text = str(sub_key or "").strip()
            sub_raw_text = str(sub_raw or "").strip()
            if sub_key_text and sub_raw_text:
                item[sub_key_text] = sub_raw_text
        if item:
            out[key_text] = item
    return out


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
        trs_transitions = _collect_trs_transitions(
            network,
            default_source_step=_infer_default_trs_source_step(step_map),
        )

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

        if trs_transitions:
            for source_step, target, guard_expression, guard_ops in trs_transitions:
                if target == source_step:
                    continue
                transitions.append(
                    TransitionCandidate(
                        transition_id=f"T{len(transitions) + 1}",
                        source_step=source_step,
                        target_step=target,
                        network_index=network.index,
                        guard_expression=guard_expression if guard_expression else "TRUE",
                        guard_operands=guard_ops,
                        jump_labels=jump_labels,
                    )
                )
        elif pattern_transitions:
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

        for timer_name, timer_kind, preset, timer_triggers in _collect_timers_with_triggers(network):
            timers.append(
                TimerCandidate(
                    source_timer=timer_name,
                    network_index=network.index,
                    kind=timer_kind,
                    preset=preset,
                    trigger_operands=timer_triggers,
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
        external_refs.update(_collect_structured_external_aliases(network))

    if not transitions:
        transitions = _build_network_pattern_transitions(step_map, networks)

    if any(item.transition_id.startswith("T_NET_") for item in transitions):
        network_only = [
            item
            for item in transitions
            if item.source_step.startswith("N") and item.target_step.startswith("N")
        ]
        if network_only:
            transitions = network_only

    _apply_translation_rules(step_map, transitions)

    if transitions:
        referenced_steps = {item.source_step for item in transitions} | {
            item.target_step for item in transitions
        }
        step_map = {
            name: candidate for name, candidate in step_map.items() if name in referenced_steps
        }

    assumptions = [
        "Il parser usa euristiche incrementali sui pattern AWL piu' frequenti.",
        "Le transizioni vengono dedotte da step letti nello stesso network e step attivati tramite S/=.",
        "Se il sorgente non contiene step Sxx sufficienti, viene applicato un fallback sequenziale per network.",
        "Il bundle XML generato e' una baseline strutturale iniziale, non ancora un serializer TIA completo.",
    ]

    normalized_external_refs = _normalize_external_refs(external_refs)

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
        external_refs=normalized_external_refs,
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


def _merge_guard_expressions(expressions: list[str]) -> str:
    cleaned = [str(item or "").strip() for item in expressions if str(item or "").strip()]
    if not cleaned:
        return "TRUE"
    if any(item.upper() == "TRUE" for item in cleaned):
        return "TRUE"
    unique: list[str] = []
    for item in cleaned:
        if item not in unique:
            unique.append(item)
    if len(unique) == 1:
        return unique[0]
    return " OR ".join(f"({item})" for item in unique)


def _merge_guard_operands(groups: list[list[str]]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for operand in group:
            if operand not in merged:
                merged.append(operand)
    return merged


def _build_graph_topology(ir: AwlIR) -> GraphTopology:
    if any(step.step_number is not None for step in ir.steps):
        ordered_steps = sorted(
            ir.steps,
            key=lambda item: (
                item.step_number is None,
                item.step_number if item.step_number is not None else 10**9,
            ),
        )
    else:
        ordered_steps = list(ir.steps)
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

    # Drop orphan steps that are not referenced by any transition.
    # TIA GRAPH import rejects disconnected elements (e.g. "Init has no connection").
    if ir.transitions:
        referenced_steps = {
            str(item.source_step)
            for item in ir.transitions
            if str(item.source_step)
        } | {
            str(item.target_step)
            for item in ir.transitions
            if str(item.target_step)
        }
        orphan_steps = [item.name for item in ordered_steps if item.name not in referenced_steps]
        if orphan_steps:
            ordered_steps = [item for item in ordered_steps if item.name in referenced_steps]
            if not ordered_steps:
                ordered_steps = list(ir.steps)

    transition_targets = {transition.target_step for transition in ir.transitions}
    explicit_s1 = next((step for step in ordered_steps if step.name == "S1"), None)
    step_no_1 = next(
        (
            step
            for step in ordered_steps
            if step.step_number is not None and int(step.step_number) == 1
        ),
        None,
    )
    if explicit_s1 is not None:
        entry_step = explicit_s1.name
    elif step_no_1 is not None:
        entry_step = step_no_1.name
    else:
        entry_step = None
        for step in ordered_steps:
            if step.name not in transition_targets:
                entry_step = step.name
                break
        if entry_step is None:
            entry_step = ordered_steps[0].name

    warnings: list[str] = []
    if ir.transitions:
        referenced_steps = {
            str(item.source_step)
            for item in ir.transitions
            if str(item.source_step)
        } | {
            str(item.target_step)
            for item in ir.transitions
            if str(item.target_step)
        }
        orphan_steps = [item.name for item in ir.steps if item.name not in referenced_steps]
        if orphan_steps:
            warnings.append(
                "Rimossi step non connessi dal GRAPH: " + ", ".join(orphan_steps)
            )

    working_transitions = [
        TransitionCandidate(
            transition_id=item.transition_id,
            source_step=item.source_step,
            target_step=item.target_step,
            network_index=item.network_index,
            guard_expression=item.guard_expression,
            guard_operands=list(item.guard_operands),
            jump_labels=list(item.jump_labels),
            flow_type=item.flow_type,
            parallel_group=item.parallel_group,
        )
        for item in ir.transitions
    ]

    parallel_start_meta: dict[str, dict[str, object]] = {}
    by_source_parallel: dict[str, list[TransitionCandidate]] = {}
    for item in working_transitions:
        if item.flow_type == "parallel":
            by_source_parallel.setdefault(item.source_step, []).append(item)
    for source_step, items in by_source_parallel.items():
        grouped = [item for item in items if item.parallel_group]
        distinct_groups = {item.parallel_group for item in grouped}
        if len(distinct_groups) > 1:
            warnings.append(
                f"Parallel split su {source_step}: trovati piu' parallel_group ({', '.join(sorted(distinct_groups))}), "
                "usa un solo gruppo per ogni split."
            )
            continue

        candidates = grouped if grouped else items
        if len(candidates) < 2:
            continue
        keeper = candidates[0]
        removed = candidates[1:]
        keeper.guard_expression = _merge_guard_expressions([x.guard_expression for x in candidates])
        keeper.guard_operands = _merge_guard_operands([x.guard_operands for x in candidates])
        parallel_start_meta[source_step] = {
            "keeper": keeper.transition_id,
            "targets": [x.target_step for x in candidates],
            "group": keeper.parallel_group,
        }
        removed_names = {x.transition_id for x in removed}
        working_transitions = [x for x in working_transitions if x.transition_id not in removed_names]
        if removed_names:
            warnings.append(
                f"Parallel split su {source_step}: consolidate {len(candidates)} transizioni in {keeper.transition_id}."
            )

    parallel_join_meta: dict[tuple[str, str], dict[str, object]] = {}
    by_target_parallel: dict[tuple[str, str], list[TransitionCandidate]] = {}
    for item in working_transitions:
        if item.flow_type == "parallel":
            key = (item.target_step, item.parallel_group or "__AUTO__")
            by_target_parallel.setdefault(key, []).append(item)
    for (target_step, group_key), items in by_target_parallel.items():
        sources = {x.source_step for x in items}
        if len(items) < 2 or len(sources) < 2:
            continue
        keeper = items[0]
        removed = items[1:]
        keeper.guard_expression = _merge_guard_expressions([x.guard_expression for x in items])
        keeper.guard_operands = _merge_guard_operands([x.guard_operands for x in items])
        parallel_join_meta[(target_step, keeper.parallel_group or "__AUTO__")] = {
            "keeper": keeper.transition_id,
            "sources": [x.source_step for x in items],
            "group": keeper.parallel_group,
        }
        removed_names = {x.transition_id for x in removed}
        working_transitions = [x for x in working_transitions if x.transition_id not in removed_names]
        if removed_names:
            warnings.append(
                f"Parallel join su {target_step}: consolidate {len(items)} transizioni in {keeper.transition_id}."
            )

    transition_nodes = [
        GraphTransitionNode(
            name=transition.transition_id,
            transition_no=index + 1,
            source_step=transition.source_step,
            target_step=transition.target_step,
            guard_expression=transition.guard_expression or "TRUE",
            guard_operands=list(transition.guard_operands or []),
            network_index=transition.network_index,
            db_block_name=_transitions_db_block_name(ir),
            db_member_name=_support_member_name(
                transition.transition_id, "TR", strict_excel_mode=ir.strict_operand_catalog
            ),
        )
        for index, transition in enumerate(working_transitions)
    ]
    next_synthetic_network = (
        max((transition.network_index for transition in transition_nodes if transition.network_index), default=0)
        + 1
    )

    branch_nodes: list[GraphBranchNode] = []
    next_branch_no = 1
    next_transition_no = len(transition_nodes) + 1

    all_steps = list(ordered_steps)
    special_step_numbers = {1, 29, 30, 32}
    reserved_step_numbers = set(special_step_numbers)
    used_step_numbers: set[int] = set()
    step_nodes: list[GraphStepNode] = []
    next_sequential = 1

    for step in all_steps:
        explicit_step_no = step.step_number if step.step_number and step.step_number > 0 else None
        if explicit_step_no is None:
            token_step_no = _step_number_from_token(step.name)
            if token_step_no > 0:
                explicit_step_no = token_step_no
        if explicit_step_no is not None and explicit_step_no not in used_step_numbers:
            step_no = explicit_step_no
        elif explicit_step_no is not None and explicit_step_no in used_step_numbers:
            warnings.append(
                f"Numero step duplicato ({explicit_step_no}) rilevato per '{step.name}': assegnato un numero progressivo libero."
            )
            while next_sequential in used_step_numbers or next_sequential in reserved_step_numbers:
                next_sequential += 1
            step_no = next_sequential
            next_sequential += 1
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

    entry_node = next((node for node in step_nodes if node.init), None)
    if entry_node and entry_node.step_no != 1:
        current_one = next((node for node in step_nodes if node.step_no == 1), None)
        if current_one and current_one is not entry_node:
            current_one.step_no = entry_node.step_no
        entry_node.step_no = 1
    step_nodes.sort(key=lambda node: node.step_no)

    step_no_by_name = {step.name: step.step_no for step in step_nodes}
    step_name_by_no = {step.step_no: step.name for step in step_nodes}

    reserved_chain_numbers = [29, 30, 32]
    present_reserved_numbers = [number for number in reserved_chain_numbers if number in step_name_by_no]
    if present_reserved_numbers:
        existing_incoming = {transition.target_step for transition in transition_nodes}
        first_reserved_name = step_name_by_no[present_reserved_numbers[0]]
        if first_reserved_name not in existing_incoming and first_reserved_name != entry_step:
            transition_name = f"T_CHAIN_{entry_step}_TO_{first_reserved_name}"
            transition_nodes.append(
                GraphTransitionNode(
                    name=transition_name,
                    transition_no=next_transition_no,
                    source_step=entry_step,
                    target_step=first_reserved_name,
                    guard_expression="FALSE",
                    guard_operands=[],
                    network_index=next_synthetic_network,
                    db_block_name=_transitions_db_block_name(ir),
                    db_member_name=_transition_db_member_name_from_values(transition_name, "FALSE"),
                )
            )
            next_transition_no += 1
            next_synthetic_network += 1
            existing_incoming.add(first_reserved_name)

        for prev_number, next_number in zip(present_reserved_numbers, present_reserved_numbers[1:]):
            prev_name = step_name_by_no[prev_number]
            next_name = step_name_by_no[next_number]
            if next_name in existing_incoming:
                continue
            transition_name = f"T_CHAIN_{prev_name}_TO_{next_name}"
            transition_nodes.append(
                GraphTransitionNode(
                    name=transition_name,
                    transition_no=next_transition_no,
                    source_step=prev_name,
                    target_step=next_name,
                    guard_expression="FALSE",
                    guard_operands=[],
                    network_index=next_synthetic_network,
                    db_block_name=_transitions_db_block_name(ir),
                    db_member_name=_transition_db_member_name_from_values(transition_name, "FALSE"),
                )
            )
            next_transition_no += 1
            next_synthetic_network += 1
            existing_incoming.add(next_name)

    existing_incoming = {transition.target_step for transition in transition_nodes}
    for meta in parallel_start_meta.values():
        for target in (meta.get("targets") or []):
            if isinstance(target, str) and target:
                existing_incoming.add(target)
    for step in ordered_steps:
        if step.name == entry_step or step.name in existing_incoming:
            continue
        transition_name = f"T_CHAIN_{entry_step}_TO_{step.name}"
        if any(node.name == transition_name for node in transition_nodes):
            transition_name = f"{transition_name}_{next_transition_no}"
        transition_nodes.append(
            GraphTransitionNode(
                name=transition_name,
                transition_no=next_transition_no,
                source_step=entry_step,
                target_step=step.name,
                guard_expression="FALSE",
                guard_operands=[],
                network_index=next_synthetic_network,
                db_block_name=_transitions_db_block_name(ir),
                db_member_name=_transition_db_member_name_from_values(transition_name, "FALSE"),
            )
        )
        next_transition_no += 1
        next_synthetic_network += 1
        existing_incoming.add(step.name)

    parallel_declared_targets = {
        str(target)
        for meta in parallel_start_meta.values()
        for target in (meta.get("targets") or [])
        if str(target)
    }
    if parallel_declared_targets:
        transition_nodes = [
            item
            for item in transition_nodes
            if not (
                item.name.startswith("T_CHAIN_")
                and item.source_step == entry_step
                and item.target_step in parallel_declared_targets
            )
        ]

    # Keep the initial flow explicit: first transition must leave the init step.
    # This avoids Graph imports where the sequencer appears to start from a
    # non-init branch node.
    transition_nodes.sort(
        key=lambda item: (
            0 if item.source_step == entry_step else 1,
            item.transition_no,
        )
    )
    for index, item in enumerate(transition_nodes, start=1):
        item.transition_no = index

    _assign_unique_transition_db_member_names(transition_nodes)

    transitions_by_source: dict[str, list[GraphTransitionNode]] = {}
    for transition in transition_nodes:
        transitions_by_source.setdefault(transition.source_step, []).append(transition)

    parallel_start_by_source: dict[str, GraphBranchNode] = {}
    parallel_start_keeper_by_transition: dict[str, GraphBranchNode] = {}
    parallel_start_targets_by_source: dict[str, list[str]] = {}
    parallel_join_keeper_by_transition: dict[str, GraphBranchNode] = {}
    parallel_join_sources_by_transition: dict[str, list[str]] = {}

    branch_by_source_step: dict[str, GraphBranchNode] = {}
    for source_step, items in transitions_by_source.items():
        if source_step in parallel_start_meta:
            meta = parallel_start_meta[source_step]
            keeper_name = str(meta.get("keeper") or "")
            keeper_node = next((item for item in items if item.name == keeper_name), None)
            if keeper_node is not None:
                targets = [str(item) for item in (meta.get("targets") or []) if str(item)]
                targets = sorted(targets, key=lambda name: step_no_by_name.get(name, 10**9))
                branch = GraphBranchNode(
                    name=f"PB_{source_step}",
                    branch_no=next_branch_no,
                    branch_type="SimBegin",
                    owner_step=source_step,
                    incoming_refs=[keeper_name],
                    outgoing_refs=targets,
                )
                next_branch_no += 1
                branch_nodes.append(branch)
                parallel_start_by_source[source_step] = branch
                parallel_start_keeper_by_transition[keeper_name] = branch
                parallel_start_targets_by_source[source_step] = targets
                continue

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

    for (target_step, _group_key), meta in parallel_join_meta.items():
        keeper_name = str(meta.get("keeper") or "")
        keeper_node = next((item for item in transition_nodes if item.name == keeper_name), None)
        if keeper_node is None:
            continue
        sources = [str(item) for item in (meta.get("sources") or []) if str(item)]
        sources = sorted(sources, key=lambda name: step_no_by_name.get(name, 10**9))
        branch = GraphBranchNode(
            name=f"PJ_{target_step}",
            branch_no=next_branch_no,
            branch_type="SimEnd",
            owner_step=target_step,
            incoming_refs=sources,
            outgoing_refs=[keeper_name],
        )
        next_branch_no += 1
        branch_nodes.append(branch)
        parallel_join_keeper_by_transition[keeper_name] = branch
        parallel_join_sources_by_transition[keeper_name] = sources

    connections: list[GraphConnection] = []
    direct_incoming_counts: dict[str, int] = {step.name: 0 for step in ordered_steps}
    for transition in transition_nodes:
        if transition.name in parallel_start_keeper_by_transition:
            branch = parallel_start_keeper_by_transition[transition.name]
            connections.append(
                GraphConnection(
                    source_ref=transition.source_step,
                    target_ref=transition.name,
                    link_type="Direct",
                )
            )
            connections.append(
                GraphConnection(
                    source_ref=transition.name,
                    target_ref=branch.name,
                    link_type="Direct",
                )
            )
            for index, target_step in enumerate(parallel_start_targets_by_source.get(transition.source_step, [])):
                if target_step == entry_step:
                    link_type = "Jump"
                else:
                    link_type = "Direct"
                    if direct_incoming_counts.get(target_step, 0) > 0:
                        link_type = "Jump"
                if link_type == "Direct":
                    direct_incoming_counts[target_step] = direct_incoming_counts.get(target_step, 0) + 1
                connections.append(
                    GraphConnection(
                        source_ref=branch.name,
                        target_ref=target_step,
                        link_type=link_type,
                    )
                )
            continue

        if transition.name in parallel_join_keeper_by_transition:
            branch = parallel_join_keeper_by_transition[transition.name]
            for source_step in parallel_join_sources_by_transition.get(transition.name, []):
                if any(
                    connection.source_ref == source_step
                    and connection.target_ref == branch.name
                    for connection in connections
                ):
                    continue
                connections.append(
                    GraphConnection(
                        source_ref=source_step,
                        target_ref=branch.name,
                        link_type="Direct",
                    )
                )
            connections.append(
                GraphConnection(
                    source_ref=branch.name,
                    target_ref=transition.name,
                    link_type="Direct",
                )
            )
            target_link_type = "Direct"
            if transition.target_step == entry_step:
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
            continue

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
        if transition.target_step == entry_step and transition.source_step != entry_step:
            target_link_type = "Jump"
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

    sim_end_targets = {branch.owner_step for branch in branch_nodes if branch.branch_type == "SimEnd"}
    for step_name, count in incoming_counts.items():
        if step_name != entry_step and count > 1 and step_name not in sim_end_targets:
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


def _ensure_unique_step_name(candidate: str, existing: set[str]) -> str:
    if candidate not in existing:
        return candidate
    index = 2
    while f"{candidate}_{index}" in existing:
        index += 1
    return f"{candidate}_{index}"


def _ensure_unique_transition_name(candidate: str, existing: set[str]) -> str:
    if candidate not in existing:
        return candidate
    index = 2
    while f"{candidate}_{index}" in existing:
        index += 1
    return f"{candidate}_{index}"


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
    expected_db_name = _transitions_db_block_name(ir)
    transition_db_names = {item.db_block_name for item in graph_topology.transition_nodes}
    if transition_db_names and transition_db_names != {expected_db_name}:
        issues.append(
            ValidationIssue(
                level="error",
                code="PACKAGE_COHERENCE_ERROR",
                message=(
                    "Le transition GRAPH non referenziano tutte lo stesso DB transitions del pacchetto."
                ),
                context=", ".join(sorted(transition_db_names)),
            )
        )

    db_members = _expected_transitions_db_member_names(graph_topology)
    referenced_members = {item.db_member_name for item in graph_topology.transition_nodes}
    missing_members = sorted(referenced_members - db_members)
    if missing_members:
        issues.append(
            ValidationIssue(
                level="error",
                code="PACKAGE_COHERENCE_ERROR",
                message=(
                    "Il pacchetto referenzia member transizione non dichiarati nel DB transitions."
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

    if ir.strict_operand_catalog:
        allowed = _strict_allowed_guard_operands(ir)
        unknown_operands: set[str] = set()
        for transition in ir.transitions:
            for operand in transition.guard_operands:
                if not _is_allowed_guard_operand(operand, allowed):
                    unknown_operands.add(operand)
        if unknown_operands:
            issues.append(
                ValidationIssue(
                    level="warning",
                    code="STRICT_OPERAND_CATALOG_WARNING",
                    message=(
                        "Modalita' strict Excel: alcuni operandi guard non sono nel catalogo operands "
                        "e non verranno materializzati nei DB."
                    ),
                    context=", ".join(sorted(unknown_operands)),
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
    _ = span
    suffix = _block_type_suffix(seed)
    return base + suffix


def _block_type_suffix(seed: str) -> int:
    _ = seed
    return 3


def _build_artifact_previews(scaffold, ir: AwlIR, graph_topology: GraphTopology) -> list[ArtifactPreview]:
    profile = build_target_profile()
    graph_xml = _build_graph_fb_xml(profile, ir, graph_topology)
    fc_xml = _build_lad_fc_xml(ir, graph_topology)

    previews = [
        ArtifactPreview(
            artifact_type="graph_fb",
            file_name=scaffold.artifact_plan.graph_fb_name,
            content=graph_xml,
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
        "support_external": [],
        "support_transitions": [],
        "support_output": [],
        "support_hmi": [],
        "support_aux": [],
        "other": [],
    }
    for preview in previews:
        item = {"artifactType": preview.artifact_type, "fileName": preview.file_name}
        if preview.artifact_type in {"graph_fb", "lad_fc"}:
            manifest["baseline"].append(item)
        elif preview.artifact_type in {"support_global_db_io", "support_lad_fc_io"}:
            manifest["support_io"].append(item)
        elif preview.artifact_type in {"support_global_db_diag", "support_lad_fc_diag"}:
            manifest["support_diag"].append(item)
        elif preview.artifact_type in {"support_global_db_mode", "support_lad_fc_mode"}:
            manifest["support_mode"].append(item)
        elif preview.artifact_type in {"support_global_db_network", "support_lad_fc_network"}:
            manifest["support_network"].append(item)
        elif preview.artifact_type in {"support_global_db_external"}:
            manifest["support_external"].append(item)
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
    symbol_home_db_map = _build_support_symbol_home_db_map(ir)
    guard_members_by_category = _collect_transition_guard_members_by_category(ir)
    timer_trigger_members_by_category = _collect_timer_trigger_support_members_by_category(ir)
    member_datatypes = _support_operand_datatypes(ir)
    operand_notes = _support_operand_notes(ir)
    timer_configs = _support_timer_configs(ir)
    derived_actions = (
        _derive_awl_action_logic_rows(ir)
        if not ir.strict_operand_catalog
        else {"aux": [], "io": [], "hmi": [], "diag": [], "transitions": []}
    )
    diag_db_name, diag_fc_name, diag_db_file, diag_fc_file, diag_db_base, diag_fc_base = _support_block_names(
        ir.sequence_name, "diag"
    )
    hmi_db_name, hmi_fc_name, hmi_db_file, hmi_fc_file, hmi_db_base, hmi_fc_base = _support_block_names(
        ir.sequence_name, "hmi"
    )
    aux_db_name, aux_fc_name, aux_db_file, aux_fc_file, aux_db_base, aux_fc_base = _support_block_names(
        ir.sequence_name, "aux"
    )
    tr_db_name, tr_fc_name, tr_db_file, tr_fc_file, tr_db_base, tr_fc_base = _support_block_names(
        ir.sequence_name, "transitions"
    )
    io_db_name, _, io_db_file, _, io_db_base, _ = _support_block_names(
        ir.sequence_name, "io"
    )
    _, output_fc_name, _, output_fc_file, _, output_fc_base = _support_block_names(
        ir.sequence_name, "output"
    )
    mode_db_name, mode_fc_name, mode_db_file, mode_fc_file, mode_db_base, mode_fc_base = _support_block_names(
        ir.sequence_name, "mode"
    )
    ext_db_name, _, ext_db_file, _, ext_db_base, _ = _support_block_names(ir.sequence_name, "external")
    par_db_name, _, par_db_file, _, par_db_base, _ = _support_block_names(ir.sequence_name, "parameters")

    diag_logic = _excel_support_logic_rows(ir, "diag")
    if not ir.strict_operand_catalog:
        diag_logic = diag_logic + derived_actions.get("diag", [])
    diag_members = (
        (_excel_support_members(ir, "diag") or _collect_diag_support_members(ir))
        + guard_members_by_category.get("diag", [])
        + timer_trigger_members_by_category.get("diag", [])
    )
    diag_db_members, diag_fc_members = _prepare_support_members(ir, "diag", diag_members, diag_logic)

    hmi_logic = _excel_support_logic_rows(ir, "hmi")
    if not ir.strict_operand_catalog:
        hmi_logic = hmi_logic + derived_actions.get("hmi", [])
    hmi_members = (
        (_excel_support_members(ir, "hmi") or _collect_hmi_support_members(ir))
        + guard_members_by_category.get("hmi", [])
        + timer_trigger_members_by_category.get("hmi", [])
    )
    hmi_db_members, hmi_fc_members = _prepare_support_members(ir, "hmi", hmi_members, hmi_logic)

    aux_logic = _excel_support_logic_rows(ir, "aux")
    # For AWL sources, emit timer FB calls in AUX LAD so that timer operands
    # used in guards map coherently to IEC_TIMER instances + *_DONE bits.
    if not ir.strict_operand_catalog:
        aux_logic = aux_logic + _derive_awl_timer_logic_rows(ir)
        aux_logic = aux_logic + derived_actions.get("aux", [])
    aux_members = (
        (_excel_support_members(ir, "aux") or _collect_aux_support_members(ir))
        + guard_members_by_category.get("aux", [])
        + timer_trigger_members_by_category.get("aux", [])
    )
    aux_db_members, aux_fc_members = _prepare_support_members(ir, "aux", aux_members, aux_logic)

    transitions_logic = _excel_support_logic_rows(ir, "transitions")
    if not ir.strict_operand_catalog:
        transitions_logic = transitions_logic + derived_actions.get("transitions", [])
    transitions_members = (
        (_excel_support_members(ir, "transitions") or _collect_transitions_support_members(ir, []))
        + guard_members_by_category.get("transitions", [])
    )
    transitions_merged_members = _merge_support_members_with_logic(transitions_members, transitions_logic)
    transitions_db_members = _prepare_support_db_members(ir, "transitions", transitions_merged_members)
    transitions_fc_members = _dedupe_named_members(
        [(name, comment) for name, comment in transitions_merged_members if str(name or "").strip()]
    )

    io_logic = _excel_support_logic_rows(ir, "io")
    output_logic = _excel_support_logic_rows(ir, "output")
    io_output_logic = io_logic + output_logic
    if not ir.strict_operand_catalog:
        io_output_logic = io_output_logic + derived_actions.get("io", [])
    io_members = _excel_support_members(ir, "io")
    output_members = _excel_support_members(ir, "output")
    io_output_members = (
        io_members
        + output_members
        + guard_members_by_category.get("io", [])
        + timer_trigger_members_by_category.get("io", [])
    )
    if not io_output_members:
        io_output_members = _collect_output_family_members(ir)
    output_db_members, output_fc_members = _prepare_support_members(
        ir, "io", io_output_members, io_output_logic
    )

    mode_logic = _excel_support_logic_rows(ir, "mode")
    mode_members = _excel_support_members(ir, "mode") or _collect_mode_support_members(ir)
    mode_db_members, mode_fc_members = _prepare_support_members(ir, "mode", mode_members, mode_logic)

    external_members = _excel_support_members(ir, "external") or _collect_external_support_members(ir)
    external_db_members = _prepare_support_db_members(ir, "external", external_members)

    parameters_members = _collect_parameters_support_members(ir)
    parameters_db_members = _prepare_support_db_members(ir, "parameters", parameters_members)

    # Always create the full expected block set, even when empty.
    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_diag",
            file_name=diag_db_file,
            content=_build_support_global_db_xml(
                block_name=diag_db_name,
                title=f"{ir.sequence_name} Alarms DB",
                members=diag_db_members,
                member_datatypes=member_datatypes,
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
                support_members=diag_fc_members,
                db_members=[name for name, _ in diag_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=diag_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                number_seed=f"{ir.sequence_name}_DIAG_FC",
                number_base=diag_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_hmi",
            file_name=hmi_db_file,
            content=_build_support_global_db_xml(
                block_name=hmi_db_name,
                title=f"{ir.sequence_name} HMI DB",
                members=hmi_db_members,
                member_datatypes=member_datatypes,
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
                support_members=hmi_fc_members,
                db_members=[name for name, _ in hmi_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=hmi_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                number_seed=f"{ir.sequence_name}_HMI_FC",
                number_base=hmi_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_aux",
            file_name=aux_db_file,
            content=_build_support_global_db_xml(
                block_name=aux_db_name,
                title=f"{ir.sequence_name} Aux DB",
                members=aux_db_members,
                member_datatypes=member_datatypes,
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
                support_members=aux_fc_members,
                db_members=[name for name, _ in aux_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=aux_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                number_seed=f"{ir.sequence_name}_AUX_FC",
                number_base=aux_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_transitions",
            file_name=tr_db_file,
            content=_build_support_global_db_xml(
                block_name=tr_db_name,
                title=f"{ir.sequence_name} Transitions DB",
                members=transitions_db_members,
                member_datatypes=member_datatypes,
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
                support_members=transitions_fc_members,
                db_members=[name for name, _ in transitions_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=transitions_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                prefer_current_db_for_unmapped=True,
                number_seed=f"{ir.sequence_name}_TRANSITIONS_FC",
                number_base=tr_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_io",
            file_name=io_db_file,
            content=_build_support_global_db_xml(
                block_name=io_db_name,
                title=f"{ir.sequence_name} IO DB",
                members=output_db_members,
                member_datatypes=member_datatypes,
                number_seed=f"{ir.sequence_name}_IO_DB",
                number_base=io_db_base,
            ),
        )
    )
    previews.append(
        ArtifactPreview(
            artifact_type="support_lad_fc_output",
            file_name=output_fc_file,
            content=_build_support_lad_fc_xml(
                fc_name=output_fc_name,
                title=f"{ir.sequence_name} Output LAD",
                db_name=io_db_name,
                support_members=output_fc_members,
                db_members=[name for name, _ in output_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=io_output_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                number_seed=f"{ir.sequence_name}_OUTPUT_FC",
                number_base=output_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_mode",
            file_name=mode_db_file,
            content=_build_support_global_db_xml(
                block_name=mode_db_name,
                title=f"{ir.sequence_name} LEV2 DB",
                members=mode_db_members,
                member_datatypes=member_datatypes,
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
                title=f"{ir.sequence_name} LEV2 LAD",
                db_name=mode_db_name,
                support_members=mode_fc_members,
                db_members=[name for name, _ in mode_db_members],
                symbol_home_db_map=symbol_home_db_map,
                member_datatypes=member_datatypes,
                operand_notes=operand_notes,
                timer_configs=timer_configs,
                logic_rows=mode_logic,
                allow_member_fallback=not ir.strict_operand_catalog,
                number_seed=f"{ir.sequence_name}_MODE_FC",
                number_base=mode_fc_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_external",
            file_name=ext_db_file,
            content=_build_support_global_db_xml(
                block_name=ext_db_name,
                title=f"{ir.sequence_name} External DB",
                members=external_db_members,
                member_datatypes=member_datatypes,
                number_seed=f"{ir.sequence_name}_EXTERNAL_DB",
                number_base=ext_db_base,
            ),
        )
    )

    previews.append(
        ArtifactPreview(
            artifact_type="support_global_db_parameters",
            file_name=par_db_file,
            content=_build_support_global_db_xml(
                block_name=par_db_name,
                title=f"{ir.sequence_name} Parameters DB",
                members=parameters_db_members,
                member_datatypes=member_datatypes,
                number_seed=f"{ir.sequence_name}_PARAMETERS_DB",
                number_base=par_db_base,
            ),
        )
    )

    return previews


def _build_graph_fb_xml(profile, ir: AwlIR, graph_topology: GraphTopology) -> str:
    fb_number = _stable_block_number(f"{ir.sequence_name}_FB", base=DB_FAMILY_NUMBER_BASE["graph"], span=100)
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
    symbol_home_db_map = _build_support_symbol_home_db_map(ir)
    operand_aliases = _build_awl_operand_alias_map(ir)
    transitions_xml = "\n".join(
        _render_graph_transition(
            transition,
            strict_excel_mode=ir.strict_operand_catalog,
            symbol_home_db_map=symbol_home_db_map,
            operand_aliases=operand_aliases,
        )
        for transition in graph_topology.transition_nodes
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
        '    <Comment Informative="true">\n'
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
    if db_number // 100 == 15:
        raise ValueError("DB15xx e' riservato al DB istanza GRAPH generato da TIA.")
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
    member_datatypes: dict[str, str] | None = None,
    number_base: int = 400,
    number_span: int = 200,
) -> str:
    db_number = _stable_block_number(number_seed, base=number_base, span=number_span)
    if db_number // 100 == 15:
        raise ValueError("DB15xx e' riservato al DB istanza GRAPH generato da TIA.")
    unique_members = _dedupe_named_members(members)
    datatype_map = member_datatypes or {}
    member_irs = [
        MemberIR(
            name=member_name,
            datatype=datatype_map.get(member_name, "Bool"),
            comment=member_comment,
        )
        for member_name, member_comment in unique_members
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
    support_members: list[tuple[str, str]],
    db_members: list[str],
    symbol_home_db_map: dict[str, str] | None,
    member_datatypes: dict[str, str] | None,
    operand_notes: dict[str, str] | None,
    timer_configs: dict[str, dict[str, str]] | None,
    number_seed: str,
    logic_rows: list[dict[str, object]] | None = None,
    allow_member_fallback: bool = True,
    prefer_current_db_for_unmapped: bool = False,
    number_base: int = 600,
    number_span: int = 200,
) -> str:
    fc_number = _stable_block_number(number_seed, base=number_base, span=number_span)
    temp_members = "\n".join(
        f'    <Member Name="{escape(member)}" Datatype="Bool" />'
        for member in dict.fromkeys(db_members)
    )
    if not temp_members:
        temp_members = '    <Member Name="PACKET_READY" Datatype="Bool" />'
    compile_units = _build_support_lad_compile_units(
        db_name=db_name,
        support_members=support_members,
        db_members=db_members,
        symbol_home_db_map=symbol_home_db_map or {},
        member_datatypes=member_datatypes or {},
        operand_notes=operand_notes or {},
        timer_configs=timer_configs or {},
        logic_rows=logic_rows or [],
        allow_member_fallback=allow_member_fallback,
        prefer_current_db_for_unmapped=prefer_current_db_for_unmapped,
    )
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
        '      <MultilingualText ID="FFFF0" CompositionName="Title">\n'
        '        <ObjectList>\n'
        '          <MultilingualTextItem ID="FFFF1" CompositionName="Items">\n'
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
        # For DB member comments, Openness/TIA shows them more reliably
        # when emitted in the simple Comment + MultiLanguageText form.
        lines.append(f"{inner_indent}<Comment>")
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
    # Excel strict mode: ownership is handled by dedicated support DB families.
    # Keep sequence DB free from duplicated symbols.
    if ir.strict_operand_catalog:
        return [MemberIR(name="NoData", datatype="Bool")]

    members: list[MemberIR] = []
    allowed_guard_operands = _strict_allowed_guard_operands(ir)

    for transition in graph_topology.transition_nodes:
        guard_member = transition.db_member_name
        members.append(
            MemberIR(
                name=guard_member,
                datatype="Bool",
                comment=f"Transition guard for {transition.name}",
            )
        )
        for operand in transition.guard_operands:
            if not _is_allowed_guard_operand(operand, allowed_guard_operands):
                continue
            members.append(
                MemberIR(
                    name=_guard_operand_db_member_name(operand, strict_excel_mode=ir.strict_operand_catalog),
                    datatype="Bool",
                    comment=f"Guard operand {operand}",
                )
            )

    for memory in ir.memories:
        members.append(
            MemberIR(
                name=_excel_preserving_db_member_name(memory.name, strict_excel_mode=ir.strict_operand_catalog),
                datatype="Bool",
                comment=memory.role,
            )
        )

    for timer in ir.timers:
        members.append(
            MemberIR(
                name=_excel_preserving_db_member_name(timer.source_timer, strict_excel_mode=ir.strict_operand_catalog),
                datatype="IEC_TIMER",
                version="1.0",
                comment=f"Timer {timer.source_timer} ({timer.kind})",
            )
        )

    if not members:
        members.append(MemberIR(name="NoData", datatype="Bool"))
    return _dedupe_member_irs(members)


def _expected_global_db_member_names(ir: AwlIR, graph_topology: GraphTopology) -> set[str]:
    names = {transition.db_member_name for transition in graph_topology.transition_nodes}
    allowed_guard_operands = _strict_allowed_guard_operands(ir)
    for transition in graph_topology.transition_nodes:
        names.update(
            _guard_operand_db_member_name(operand, strict_excel_mode=ir.strict_operand_catalog)
            for operand in transition.guard_operands
            if _is_allowed_guard_operand(operand, allowed_guard_operands)
        )
    names.update(_excel_preserving_db_member_name(memory.name, strict_excel_mode=ir.strict_operand_catalog) for memory in ir.memories)
    names.update(
        _excel_preserving_db_member_name(timer.source_timer, strict_excel_mode=ir.strict_operand_catalog)
        for timer in ir.timers
    )
    if not names:
        names.add("NoData")
    return names


def _expected_transitions_db_member_names(graph_topology: GraphTopology) -> set[str]:
    names = {item.db_member_name for item in graph_topology.transition_nodes if item.db_member_name}
    if not names:
        names.add("NoData")
    return names


def _strict_allowed_guard_operands(ir: AwlIR) -> set[str] | None:
    if not ir.strict_operand_catalog:
        return None
    raw_items = list(ir.operand_catalog)
    raw_items.extend(item.name for item in ir.memories)
    raw_items.extend(item.name for item in ir.faults)
    raw_items.extend(item.name for item in ir.outputs)
    raw_items.extend(item.source_timer for item in ir.timers)
    allowed: set[str] = set()
    for item in raw_items:
        token = str(item or "").strip()
        if not token:
            continue
        allowed.add(token.upper())
        allowed.add(_normalize_symbol_name(token, token).upper())
    return allowed


def _normalize_plc_datatype(datatype: str) -> str:
    raw = str(datatype or "").strip().lower()
    aliases = {
        "bool": "Bool",
        "boolean": "Bool",
        "int": "Int",
        "integer": "Int",
        "dint": "DInt",
        "udint": "UDInt",
        "real": "Real",
        "byte": "Byte",
        "word": "Word",
        "dword": "DWord",
        "time": "Time",
        "timer": "IEC_TIMER",
        "iec_timer": "IEC_TIMER",
        "counter": "IEC_COUNTER",
        "iec_counter": "IEC_COUNTER",
        "ctu": "IEC_COUNTER",
        "ctd": "IEC_COUNTER",
        "ctud": "IEC_COUNTER",
        "string": "String",
    }
    if not raw:
        return "Bool"
    return aliases.get(raw, str(datatype).strip() or "Bool")


def _support_operand_datatypes(ir: AwlIR) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw_name, raw_datatype in ir.operand_datatypes.items():
        normalized_name = _support_member_name(raw_name, "", strict_excel_mode=True)
        if not normalized_name:
            continue
        mapping[normalized_name] = _normalize_plc_datatype(raw_datatype)
    # AWL path: timers are implicit and must be typed explicitly, otherwise
    # support DBs default to Bool and LAD ends up wiring timer instances into coils.
    for timer in ir.timers:
        timer_name = _support_member_name(timer.source_timer, "", strict_excel_mode=True)
        if timer_name:
            mapping.setdefault(timer_name, "IEC_TIMER")
    return mapping


def _support_operand_notes(ir: AwlIR) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw_name, raw_note in ir.operand_notes.items():
        note = str(raw_note or "").strip()
        if not note:
            continue
        normalized_name = _support_member_name(raw_name, "", strict_excel_mode=True)
        if normalized_name:
            mapping.setdefault(normalized_name, note)
        raw_token = str(raw_name or "").strip()
        if raw_token:
            mapping.setdefault(raw_token, note)
    return mapping


def _timer_part_name(timer_kind: str) -> str:
    raw = str(timer_kind or "").strip().lower()
    if raw in {"t_off", "tof"}:
        return "TOF"
    if raw in {"t_p", "tp"}:
        return "TP"
    return "TON"


def _normalize_timer_preset_literal(raw_value: str) -> str:
    token = str(raw_value or "").strip().upper()
    if not token:
        return "T#1S"
    if token.startswith("S5T#"):
        return f"T#{token[4:]}"
    if token.startswith("T#"):
        return token
    return f"T#{token}"


def _counter_part_name(counter_kind: str) -> str:
    raw = str(counter_kind or "").strip().lower()
    if raw in {"ctd", "down", "count_down"}:
        return "CTD"
    if raw in {"ctud", "up_down"}:
        return "CTUD"
    return "CTU"


def _support_timer_configs(ir: AwlIR) -> dict[str, dict[str, str]]:
    configs: dict[str, dict[str, str]] = {}
    for raw_name, settings in ir.operand_control_settings.items():
        normalized_name = _support_member_name(raw_name, "", strict_excel_mode=True)
        if not normalized_name:
            continue
        datatype = _normalize_plc_datatype(ir.operand_datatypes.get(raw_name, ""))
        kind = str(settings.get("kind") or "").strip()
        value = str(settings.get("value") or "").strip()
        if datatype == "IEC_TIMER":
            preset = _normalize_timer_preset_literal(value or "T#1S")
            configs[normalized_name] = {
                "part_name": _timer_part_name(kind),
                "value": preset,
                "control_family": "timer",
            }
        elif datatype == "IEC_COUNTER":
            pv = value or "1"
            configs[normalized_name] = {
                "part_name": _counter_part_name(kind),
                "value": pv,
                "control_family": "counter",
            }
    for raw_name, settings in ir.operand_timer_settings.items():
        normalized_name = _support_member_name(raw_name, "", strict_excel_mode=True)
        if not normalized_name:
            continue
        if normalized_name in configs:
            continue
        kind = str(settings.get("kind") or "").strip()
        preset = _normalize_timer_preset_literal(str(settings.get("preset") or "").strip() or "T#1S")
        configs[normalized_name] = {
            "part_name": _timer_part_name(kind),
            "value": preset,
            "control_family": "timer",
        }
    for timer in ir.timers:
        normalized_name = _support_member_name(timer.source_timer, "", strict_excel_mode=True)
        if not normalized_name:
            continue
        if normalized_name in configs:
            continue
        preset = _normalize_timer_preset_literal(str(timer.preset or "").strip() or "T#1S")
        configs[normalized_name] = {
            "part_name": _timer_part_name(timer.kind),
            "value": preset,
            "control_family": "timer",
        }
    return configs


def _resolve_logic_symbol_path(
    operand: str,
    member_datatypes: dict[str, str],
) -> tuple[str, list[str]]:
    token = str(operand or "").strip()
    if not token:
        return "", []
    # AWL address-like operands (e.g. I30.1, Q24.0, M49.0, DB202.DBX32.0)
    # must be treated as a single leaf symbol, not as dotted struct access.
    if _is_address_like_operand(token.upper()):
        base_name = _support_member_name(token, "", strict_excel_mode=True)
        if not base_name:
            return "", []
        return base_name, [base_name]
    raw_parts = [part for part in token.split(".") if part]
    if not raw_parts:
        return "", []

    base_name = _support_member_name(raw_parts[0], "", strict_excel_mode=True)
    if not base_name:
        return "", []

    if len(raw_parts) > 1:
        return base_name, [base_name, *raw_parts[1:]]

    _ = member_datatypes
    return base_name, [base_name]


def _is_allowed_guard_operand(operand: str, allowed: set[str] | None) -> bool:
    if allowed is None:
        return True
    token = str(operand or "").strip()
    if not token:
        return False
    if token.upper() in allowed:
        return True
    normalized = _normalize_symbol_name(token, token).upper()
    return normalized in allowed


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
            db_block_name=_transitions_db_block_name(ir),
            db_member_name=_transition_db_member_name_from_values("T1", "PACKET_READY"),
        )
    ]
    for index, transition in enumerate(guard_targets):
        unit_id = format(base_id + (index * 5), "X")
        comment_id = format(base_id + (index * 5) + 1, "X")
        comment_item_id = format(base_id + (index * 5) + 2, "X")
        title_id = format(base_id + (index * 5) + 3, "X")
        title_item_id = format(base_id + (index * 5) + 4, "X")
        target_db_name = escape(transition.db_block_name or _transitions_db_block_name(ir))
        target_member_name = escape(transition.db_member_name)
        aux_member_name = escape(transition.db_member_name)
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
            f"{_render_multilingual_text_items(comment_item_id, f'Network {transition.network_index}', indent='              ')}\n"
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


def _build_support_lad_compile_units(
    db_name: str,
    support_members: list[tuple[str, str]],
    db_members: list[str],
    symbol_home_db_map: dict[str, str],
    member_datatypes: dict[str, str],
    operand_notes: dict[str, str],
    timer_configs: dict[str, dict[str, str]],
    logic_rows: list[dict[str, object]] | None = None,
    allow_member_fallback: bool = True,
    prefer_current_db_for_unmapped: bool = False,
) -> str:
    db_member_set = set(db_members)
    units: list[str] = []
    if logic_rows:
        base_id = 3
        grouped_rows: list[tuple[int, list[dict[str, object]]]] = []
        by_network: dict[int, list[dict[str, object]]] = {}
        for row_index, logic_row in enumerate(logic_rows):
            result_member = str(logic_row.get("result_member") or "").strip()
            if not result_member:
                continue
            network_no = _as_positive_int(logic_row.get("network_index")) or (row_index + 1)
            if network_no not in by_network:
                by_network[network_no] = []
                grouped_rows.append((network_no, by_network[network_no]))
            by_network[network_no].append(logic_row)

        for index, (_, network_rows) in enumerate(grouped_rows):
            flgnet_fragments: list[str] = []
            comment = ""
            for logic_row in network_rows:
                result_member = str(logic_row.get("result_member") or "").strip()
                if not result_member:
                    continue
                condition_expression = str(logic_row.get("condition_expression") or "TRUE")
                condition_operands = _as_str_list(logic_row.get("condition_operands"))
                coil_mode = str(logic_row.get("coil_mode") or "").strip()
                explicit_comment = str(logic_row.get("comment") or "").strip()
                if not comment and explicit_comment:
                    comment = explicit_comment
                _ = operand_notes
                flgnet_fragments.append(
                    _build_support_logic_flgnet(
                        db_name=db_name,
                        result_member=result_member,
                        condition_expression=condition_expression,
                        condition_operands=condition_operands,
                        db_members=db_member_set,
                        symbol_home_db_map=symbol_home_db_map,
                        member_datatypes=member_datatypes,
                        timer_configs=timer_configs,
                        coil_mode=coil_mode,
                        prefer_current_db_for_unmapped=prefer_current_db_for_unmapped,
                    )
                )
            if not flgnet_fragments:
                continue
            unit_id = format(base_id + (index * 5), "X")
            comment_id = format(base_id + (index * 5) + 1, "X")
            comment_item_id = format(base_id + (index * 5) + 2, "X")
            title_id = format(base_id + (index * 5) + 3, "X")
            title_item_id = format(base_id + (index * 5) + 4, "X")
            flgnet_xml = _merge_support_logic_flgnets(flgnet_fragments)
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
                + _render_multilingual_text_items(comment_item_id, comment, indent="              ")
                + "\n"
                '            </ObjectList>\n'
                '          </MultilingualText>\n'
                '          <MultilingualText ID="'
                + title_id
                + '" CompositionName="Title">\n'
                '            <ObjectList>\n'
                '              <MultilingualTextItem ID="'
                + title_item_id
                + '" CompositionName="Items">\n'
                '                <AttributeList>\n'
                '                  <Culture>en-US</Culture>\n'
                f'                  <Text>{escape(comment)}</Text>\n'
                '                </AttributeList>\n'
                '              </MultilingualTextItem>\n'
                '            </ObjectList>\n'
                '          </MultilingualText>\n'
                '        </ObjectList>\n'
                '      </SW.Blocks.CompileUnit>'
            )
        if units:
            return "\n".join(units)

    if not allow_member_fallback:
        return ""

    unique_members = _dedupe_named_members(
        [
            (name, comment)
            for name, comment in support_members
            if str(name or "").strip()
        ]
    )
    if not unique_members:
        unique_members = [("PACKET_READY", "PACKET_READY support network")]
    base_id = 3
    for index, (member_name, member_comment) in enumerate(unique_members):
        # Keep fallback network comments strictly explicit from Excel.
        fallback_comment = str(member_comment or "").strip()
        unit_id = format(base_id + (index * 5), "X")
        comment_id = format(base_id + (index * 5) + 1, "X")
        comment_item_id = format(base_id + (index * 5) + 2, "X")
        title_id = format(base_id + (index * 5) + 3, "X")
        title_item_id = format(base_id + (index * 5) + 4, "X")
        flgnet_xml = _build_support_logic_flgnet(
            db_name=db_name,
            result_member=member_name,
            condition_expression=member_name,
            condition_operands=[member_name],
            db_members=db_member_set,
            symbol_home_db_map=symbol_home_db_map,
            member_datatypes=member_datatypes,
            timer_configs=timer_configs,
            coil_mode="",
            prefer_current_db_for_unmapped=prefer_current_db_for_unmapped,
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
            + _render_multilingual_text_items(comment_item_id, fallback_comment, indent="              ")
            + "\n"
            '            </ObjectList>\n'
            '          </MultilingualText>\n'
            '          <MultilingualText ID="'
            + title_id
            + '" CompositionName="Title">\n'
            '            <ObjectList>\n'
                '              <MultilingualTextItem ID="'
                + title_item_id
                + '" CompositionName="Items">\n'
                '                <AttributeList>\n'
                '                  <Culture>en-US</Culture>\n'
                f'                  <Text>{escape(fallback_comment)}</Text>\n'
                '                </AttributeList>\n'
                '              </MultilingualTextItem>\n'
                '            </ObjectList>\n'
                '          </MultilingualText>\n'
                '        </ObjectList>\n'
                '      </SW.Blocks.CompileUnit>'
        )
    return "\n".join(units)


def _merge_support_logic_flgnets(flgnet_fragments: list[str]) -> str:
    if not flgnet_fragments:
        return ""
    if len(flgnet_fragments) == 1:
        return flgnet_fragments[0]
    ns = "http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"
    flgnet_tag = f"{{{ns}}}FlgNet"
    parts_tag = f"{{{ns}}}Parts"
    wires_tag = f"{{{ns}}}Wires"
    wire_tag = f"{{{ns}}}Wire"
    powerrail_tag = f"{{{ns}}}Powerrail"
    namecon_tag = f"{{{ns}}}NameCon"

    merged_xml = _extract_flgnet_element_xml(flgnet_fragments[0])
    merged_flgnet = _parse_xml_element(merged_xml)
    if merged_flgnet is None or merged_flgnet.tag != flgnet_tag:
        return flgnet_fragments[0]
    merged_parts = merged_flgnet.find(parts_tag)
    merged_wires = merged_flgnet.find(wires_tag)
    if merged_parts is None or merged_wires is None:
        return flgnet_fragments[0]
    primary_powerrail_wire = _find_powerrail_wire(merged_wires, wire_tag, powerrail_tag)

    for index, fragment in enumerate(flgnet_fragments[1:], start=1):
        fragment_xml = _extract_flgnet_element_xml(fragment)
        fragment_flgnet = _parse_xml_element(fragment_xml)
        if fragment_flgnet is None or fragment_flgnet.tag != flgnet_tag:
            continue
        _offset_element_uids(fragment_flgnet, index * 1000)
        fragment_parts = fragment_flgnet.find(parts_tag)
        fragment_wires = fragment_flgnet.find(wires_tag)
        if fragment_parts is None or fragment_wires is None:
            continue

        fragment_powerrail_wires = [
            wire
            for wire in list(fragment_wires.findall(wire_tag))
            if wire.find(powerrail_tag) is not None
        ]
        if primary_powerrail_wire is None and fragment_powerrail_wires:
            primary_powerrail_wire = copy.deepcopy(fragment_powerrail_wires[0])
            merged_wires.append(primary_powerrail_wire)
            fragment_powerrail_wires = fragment_powerrail_wires[1:]
        for pwire in fragment_powerrail_wires:
            if primary_powerrail_wire is not None:
                for child in list(pwire):
                    if child.tag == namecon_tag:
                        primary_powerrail_wire.append(copy.deepcopy(child))
            fragment_wires.remove(pwire)

        for node in list(fragment_parts):
            merged_parts.append(copy.deepcopy(node))
        for node in list(fragment_wires):
            merged_wires.append(copy.deepcopy(node))

    return f"<NetworkSource>{_serialize_xml_element(merged_flgnet)}</NetworkSource>"


def _extract_flgnet_element_xml(network_source_xml: str) -> str:
    match = re.search(r"(<FlgNet\b[^>]*>.*?</FlgNet>)", network_source_xml, flags=re.DOTALL)
    if not match:
        return ""
    return match.group(1)


def _parse_xml_element(xml_text: str):
    if not xml_text:
        return None
    try:
        from xml.etree import ElementTree as ET

        return ET.fromstring(xml_text)
    except Exception:
        return None


def _serialize_xml_element(element) -> str:
    from xml.etree import ElementTree as ET

    xml = ET.tostring(element, encoding="unicode")
    xml = xml.replace("<ns0:", "<").replace("</ns0:", "</")
    xml = xml.replace('xmlns:ns0="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"', 'xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"')
    return xml


def _find_powerrail_wire(wires_element, wire_tag: str, powerrail_tag: str):
    for wire in list(wires_element.findall(wire_tag)):
        if wire.find(powerrail_tag) is not None:
            return wire
    return None


def _offset_element_uids(element, uid_offset: int) -> None:
    for node in element.iter():
        raw_uid = node.attrib.get("UId")
        if not raw_uid:
            continue
        try:
            node.attrib["UId"] = str(int(raw_uid) + uid_offset)
        except ValueError:
            continue


def _build_support_logic_flgnet(
    db_name: str,
    result_member: str,
    condition_expression: str,
    condition_operands: list[str],
    db_members: set[str],
    symbol_home_db_map: dict[str, str],
    member_datatypes: dict[str, str],
    timer_configs: dict[str, dict[str, str]],
    coil_mode: str = "",
    prefer_current_db_for_unmapped: bool = False,
) -> str:
    next_uid = 21

    def alloc_uid() -> int:
        nonlocal next_uid
        current = next_uid
        next_uid += 1
        return current

    normalized_result = _support_member_name(result_member, "", strict_excel_mode=True)
    normalized_coil_mode = str(coil_mode or "").strip().lower()
    coil_part_name = "Coil"
    if normalized_coil_mode in {"set", "s"}:
        coil_part_name = "SCoil"
    elif normalized_coil_mode in {"reset", "r"}:
        coil_part_name = "RCoil"
    guard_clauses = _parse_guard_clauses(condition_expression, condition_operands)
    guard_clauses, common_terms = _factor_common_guard_terms(guard_clauses)
    clause_contact_uids: list[list[int]] = []
    parts_lines: list[str] = []
    wires_lines: list[str] = []

    def _owner_db_name(symbol_name: str) -> str:
        if symbol_name in db_members:
            return db_name
        if symbol_name in symbol_home_db_map:
            return symbol_home_db_map[symbol_name]
        if prefer_current_db_for_unmapped:
            return db_name
        return ""

    def _timer_candidate_for_operand(operand: str, negated: bool) -> tuple[str, str, str, str] | None:
        if negated:
            return None
        normalized_operand, operand_path = _resolve_logic_symbol_path(operand, member_datatypes)
        if not normalized_operand:
            return None
        if len(operand_path) != 1:
            return None
        cfg = timer_configs.get(normalized_operand) or {}
        datatype = _normalize_plc_datatype(member_datatypes.get(normalized_operand, ""))
        if not cfg and datatype != "IEC_TIMER" and datatype != "IEC_COUNTER" and "COUNTER" not in datatype.upper():
            return None
        control_family = cfg.get("control_family") or ("counter" if "COUNTER" in datatype.upper() else "timer")
        if control_family == "counter":
            part_name = cfg.get("part_name") or "CTU"
            value = cfg.get("value") or "1"
        else:
            part_name = cfg.get("part_name") or "TON"
            value = cfg.get("value") or "T#1S"
        return normalized_operand, part_name, value, control_family

    active_timer_name = ""
    active_timer_part = ""
    active_timer_preset = ""
    active_timer_family = ""

    # Special case: if the coil is a *_DONE bool, infer the underlying timer instance
    # without requiring the timer symbol itself to appear in the boolean expression.
    if normalized_result.endswith("_DONE"):
        base_candidate = normalized_result[: -len("_DONE")]
        cfg = timer_configs.get(base_candidate) or {}
        datatype = _normalize_plc_datatype(member_datatypes.get(base_candidate, ""))
        control_family = cfg.get("control_family") or ("counter" if "COUNTER" in datatype.upper() else "timer")
        if datatype in {"IEC_TIMER", "IEC_COUNTER"} or cfg:
            active_timer_name = base_candidate
            active_timer_part = cfg.get("part_name") or ("CTU" if control_family == "counter" else "TON")
            active_timer_preset = cfg.get("value") or ("1" if control_family == "counter" else "T#1S")
            active_timer_family = "counter" if control_family == "counter" else "timer"
    scan_terms = [common_terms, *guard_clauses]
    if not active_timer_name:
        for clause in scan_terms:
            for operand, negated in clause:
                candidate = _timer_candidate_for_operand(operand, negated)
                if candidate:
                    active_timer_name = candidate[0]
                    active_timer_part = candidate[1]
                    active_timer_preset = candidate[2]
                    active_timer_family = candidate[3]
                    break
            if active_timer_name:
                break

    def _render_access(symbol_name: str, symbol_path: list[str], access_uid: int) -> list[str]:
        target_db_name = _owner_db_name(symbol_name)

        if target_db_name:
            return [
                f'    <Access Scope="GlobalVariable" UId="{access_uid}">\n',
                "      <Symbol>\n",
                f'        <Component Name="{escape(target_db_name)}" />\n',
                "".join(f'        <Component Name="{escape(component)}" />\n' for component in symbol_path),
                "      </Symbol>\n",
                "    </Access>\n",
            ]
        return [
            f'    <Access Scope="GlobalVariable" UId="{access_uid}">\n',
            "      <Symbol>\n",
            "".join(f'        <Component Name="{escape(component)}" />\n' for component in symbol_path),
            "      </Symbol>\n",
            "    </Access>\n",
        ]

    has_true_clause = any(not clause for clause in guard_clauses)
    for clause in guard_clauses:
        if not clause:
            continue
        contact_uids: list[int] = []
        for operand, negated in clause:
            normalized_operand, operand_path = _resolve_logic_symbol_path(operand, member_datatypes)
            if not normalized_operand:
                continue
            if active_timer_name and normalized_operand == active_timer_name and len(operand_path) == 1:
                continue
            access_uid = alloc_uid()
            contact_uid = alloc_uid()
            parts_lines.extend(_render_access(normalized_operand, operand_path, access_uid))
            if negated:
                parts_lines.extend(
                    [
                        f'    <Part Name="Contact" UId="{contact_uid}">\n',
                        '      <Negated Name="operand" />\n',
                        "    </Part>\n",
                    ]
                )
            else:
                parts_lines.append(f'    <Part Name="Contact" UId="{contact_uid}" />\n')

            wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'    <Wire UId="{wire_uid}">\n',
                    f'      <IdentCon UId="{access_uid}" />\n',
                    f'      <NameCon UId="{contact_uid}" Name="operand" />\n',
                    "    </Wire>\n",
                ]
            )
            contact_uids.append(contact_uid)
        if contact_uids:
            clause_contact_uids.append(contact_uids)

    coil_access_uid = alloc_uid()
    coil_uid = alloc_uid()
    parts_lines.extend(_render_access(normalized_result, [normalized_result], coil_access_uid))
    parts_lines.append(f'    <Part Name="{coil_part_name}" UId="{coil_uid}" />\n')
    coil_operand_wire_uid = alloc_uid()
    wires_lines.extend(
        [
            f'    <Wire UId="{coil_operand_wire_uid}">\n',
            f'      <IdentCon UId="{coil_access_uid}" />\n',
            f'      <NameCon UId="{coil_uid}" Name="operand" />\n',
            "    </Wire>\n",
        ]
    )

    clause_outs: list[int] = []
    if clause_contact_uids and not has_true_clause:
        powerrail_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{powerrail_wire_uid}">\n',
                "      <Powerrail />\n",
            ]
        )
        for branch in clause_contact_uids:
            if branch:
                wires_lines.append(f'      <NameCon UId="{branch[0]}" Name="in" />\n')
        wires_lines.append("    </Wire>\n")

    for branch in clause_contact_uids:
        for prev_uid, next_contact_uid in zip(branch, branch[1:]):
            serial_wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'    <Wire UId="{serial_wire_uid}">\n',
                    f'      <NameCon UId="{prev_uid}" Name="out" />\n',
                    f'      <NameCon UId="{next_contact_uid}" Name="in" />\n',
                    "    </Wire>\n",
                ]
            )
        if branch:
            clause_outs.append(branch[-1])

    logic_output_uid: int | None = None
    if len(clause_outs) > 1:
        or_uid = alloc_uid()
        parts_lines.extend(
            [
                f'    <Part Name="O" UId="{or_uid}">\n',
                f'      <TemplateValue Name="Card" Type="Cardinality">{len(clause_outs)}</TemplateValue>\n',
                "    </Part>\n",
            ]
        )
        for index, out_uid in enumerate(clause_outs, start=1):
            in_wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'    <Wire UId="{in_wire_uid}">\n',
                    f'      <NameCon UId="{out_uid}" Name="out" />\n',
                    f'      <NameCon UId="{or_uid}" Name="in{index}" />\n',
                    "    </Wire>\n",
                ]
            )
        logic_output_uid = or_uid
    elif clause_outs:
        logic_output_uid = clause_outs[0]

    for operand, negated in common_terms:
        normalized_operand, operand_path = _resolve_logic_symbol_path(operand, member_datatypes)
        if not normalized_operand:
            continue
        if active_timer_name and normalized_operand == active_timer_name and len(operand_path) == 1:
            continue
        access_uid = alloc_uid()
        contact_uid = alloc_uid()
        parts_lines.extend(_render_access(normalized_operand, operand_path, access_uid))
        if negated:
            parts_lines.extend(
                [
                    f'    <Part Name="Contact" UId="{contact_uid}">\n',
                    '      <Negated Name="operand" />\n',
                    "    </Part>\n",
                ]
            )
        else:
            parts_lines.append(f'    <Part Name="Contact" UId="{contact_uid}" />\n')

        operand_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{operand_wire_uid}">\n',
                f'      <IdentCon UId="{access_uid}" />\n',
                f'      <NameCon UId="{contact_uid}" Name="operand" />\n',
                "    </Wire>\n",
            ]
        )

        in_wire_uid = alloc_uid()
        if logic_output_uid is None:
            wires_lines.extend(
                [
                    f'    <Wire UId="{in_wire_uid}">\n',
                    "      <Powerrail />\n",
                    f'      <NameCon UId="{contact_uid}" Name="in" />\n',
                    "    </Wire>\n",
                ]
            )
        else:
            wires_lines.extend(
                [
                    f'    <Wire UId="{in_wire_uid}">\n',
                    f'      <NameCon UId="{logic_output_uid}" Name="out" />\n',
                    f'      <NameCon UId="{contact_uid}" Name="in" />\n',
                    "    </Wire>\n",
                ]
            )
        logic_output_uid = contact_uid

    if active_timer_name:
        preset_access_uid = alloc_uid()
        timer_uid = alloc_uid()
        timer_instance_uid = alloc_uid()
        open_con_uid = alloc_uid()

        constant_scope = "LiteralConstant" if active_timer_family == "counter" else "TypedConstant"
        constant_lines: list[str] = [
            f'    <Access Scope="{constant_scope}" UId="{preset_access_uid}">\n',
            "      <Constant>\n",
        ]
        if active_timer_family == "counter":
            constant_lines.append("        <ConstantType>Int</ConstantType>\n")
        constant_lines.append(
            f'        <ConstantValue>{escape(active_timer_preset or ("1" if active_timer_family == "counter" else "T#1S"))}</ConstantValue>\n'
        )
        constant_lines.extend(
            [
                "      </Constant>\n",
                "    </Access>\n",
            ]
        )
        parts_lines.extend(constant_lines)

        instance_components: list[str] = []
        owner_db = _owner_db_name(active_timer_name)
        if owner_db:
            instance_components.append(owner_db)
        instance_components.append(active_timer_name)

        parts_lines.extend(
            [
                f'    <Part Name="{escape(active_timer_part or "TON")}" Version="1.0" UId="{timer_uid}">\n',
                f'      <Instance Scope="GlobalVariable" UId="{timer_instance_uid}">\n',
                *[f'        <Component Name="{escape(component)}" />\n' for component in instance_components],
                "      </Instance>\n",
                (
                    '      <TemplateValue Name="value_type" Type="Type">Int</TemplateValue>\n'
                    if active_timer_family == "counter"
                    else '      <TemplateValue Name="time_type" Type="Type">Time</TemplateValue>\n'
                ),
                "    </Part>\n",
            ]
        )

        control_input_pin = "IN"
        control_value_pin = "PT"
        control_aux_pin = "ET"
        required_counter_pins: list[str] = []
        if active_timer_family == "counter":
            if (active_timer_part or "").upper() == "CTD":
                control_input_pin = "CD"
                required_counter_pins = ["LD"]
            elif (active_timer_part or "").upper() == "CTUD":
                control_input_pin = "CU"
                required_counter_pins = ["R", "LD"]
            else:
                control_input_pin = "CU"
                required_counter_pins = ["R"]
            control_value_pin = "PV"
            control_aux_pin = "CV"

        if logic_output_uid is not None:
            in_wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'    <Wire UId="{in_wire_uid}">\n',
                    f'      <NameCon UId="{logic_output_uid}" Name="out" />\n',
                    f'      <NameCon UId="{timer_uid}" Name="{control_input_pin}" />\n',
                    "    </Wire>\n",
                ]
            )
        else:
            timer_true_wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'    <Wire UId="{timer_true_wire_uid}">\n',
                    "      <Powerrail />\n",
                    f'      <NameCon UId="{timer_uid}" Name="{control_input_pin}" />\n',
                    "    </Wire>\n",
                ]
            )

        pt_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{pt_wire_uid}">\n',
                f'      <IdentCon UId="{preset_access_uid}" />\n',
                f'      <NameCon UId="{timer_uid}" Name="{control_value_pin}" />\n',
                "    </Wire>\n",
            ]
        )

        q_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{q_wire_uid}">\n',
                f'      <NameCon UId="{timer_uid}" Name="Q" />\n',
                f'      <NameCon UId="{coil_uid}" Name="in" />\n',
                "    </Wire>\n",
            ]
        )

        et_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{et_wire_uid}">\n',
                f'      <NameCon UId="{timer_uid}" Name="{control_aux_pin}" />\n',
                f'      <OpenCon UId="{open_con_uid}" />\n',
                "    </Wire>\n",
            ]
        )

        if active_timer_family == "counter" and required_counter_pins:
            for pin_name in required_counter_pins:
                false_access_uid = alloc_uid()
                parts_lines.extend(
                    [
                        f'    <Access Scope="LiteralConstant" UId="{false_access_uid}">\n',
                        "      <Constant>\n",
                        "        <ConstantValue>FALSE</ConstantValue>\n",
                        "      </Constant>\n",
                        "    </Access>\n",
                    ]
                )
                pin_wire_uid = alloc_uid()
                wires_lines.extend(
                    [
                        f'    <Wire UId="{pin_wire_uid}">\n',
                        f'      <IdentCon UId="{false_access_uid}" />\n',
                        f'      <NameCon UId="{timer_uid}" Name="{pin_name}" />\n',
                        "    </Wire>\n",
                    ]
                )
    elif logic_output_uid is not None:
        final_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{final_wire_uid}">\n',
                f'      <NameCon UId="{logic_output_uid}" Name="out" />\n',
                f'      <NameCon UId="{coil_uid}" Name="in" />\n',
                "    </Wire>\n",
            ]
        )
    else:
        true_wire_uid = alloc_uid()
        wires_lines.extend(
            [
                f'    <Wire UId="{true_wire_uid}">\n',
                "      <Powerrail />\n",
                f'      <NameCon UId="{coil_uid}" Name="in" />\n',
                "    </Wire>\n",
            ]
        )

    return (
        '          <NetworkSource><FlgNet xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5">\n'
        "  <Parts>\n"
        f'{"".join(parts_lines)}'
        "  </Parts>\n"
        "  <Wires>\n"
        f'{"".join(wires_lines)}'
        "  </Wires>\n"
        "</FlgNet></NetworkSource>"
    )


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
        '    <Access Scope="GlobalVariable" UId="24">\n'
        '      <Symbol>\n'
        f'        <Component Name="{db_name}" />\n'
        f'        <Component Name="{member_name}" />\n'
        '      </Symbol>\n'
        '    </Access>\n'
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
        '    <Wire UId="34">\n'
        '      <IdentCon UId="24" />\n'
        '      <NameCon UId="23" Name="operand" />\n'
        '    </Wire>\n'
        '  </Wires>\n'
        '</FlgNet></NetworkSource>'
    )


def _excel_support_members(ir: AwlIR, category: str) -> list[tuple[str, str]]:
    normalized_category = str(category or "").strip().lower()
    if not normalized_category:
        return []
    members: list[tuple[str, str]] = []
    for item in ir.support_members:
        raw_category = str(item.get("category") or "").strip().lower()
        if raw_category != normalized_category:
            continue
        raw_name = str(item.get("member_name") or "").strip()
        if not raw_name:
            continue
        member_name = _support_member_name(raw_name, "", strict_excel_mode=True)
        comment = str(item.get("comment") or "").strip()
        members.append((member_name, comment))
    return _dedupe_named_members(members)


def _excel_support_logic_rows(
    ir: AwlIR,
    category: str,
) -> list[dict[str, object]]:
    normalized_category = str(category or "").strip().lower()
    if not normalized_category:
        return []

    rows: list[dict[str, object]] = []
    for item in ir.support_logic:
        raw_category = str(item.get("category") or "").strip().lower()
        if raw_category != normalized_category:
            continue

        item_network = _as_positive_int(item.get("network_index"))

        result_raw = str(item.get("result_member") or "").strip()
        if not result_raw:
            continue
        result_member = _support_member_name(result_raw, "", strict_excel_mode=True)

        operands = [
            _support_member_name(str(token).strip(), "", strict_excel_mode=True)
            for token in _as_str_list(item.get("condition_operands"))
            if str(token).strip()
        ]

        condition_expression = str(item.get("condition_expression") or "").strip()
        if not condition_expression and operands:
            condition_expression = " AND ".join(operands)
        if not condition_expression:
            condition_expression = "TRUE"

        rows.append(
            {
                "result_member": result_member,
                "condition_expression": condition_expression,
                "condition_operands": operands,
                "coil_mode": str(item.get("coil_mode") or "").strip(),
                "comment": str(item.get("comment") or "").strip(),
                "network_index": item_network,
            }
        )
    rows.sort(
        key=lambda row: (
            _as_positive_int(row.get("network_index")) or 10**9,
            str(row.get("result_member") or ""),
        )
    )
    return rows


def _merge_support_members_with_logic(
    members: list[tuple[str, str]],
    logic_rows: list[dict[str, object]],
) -> list[tuple[str, str]]:
    merged = list(members)
    existing = {name for name, _ in merged}
    for row in logic_rows:
        row_comment = str(row.get("comment") or "").strip()
        result_member = str(row.get("result_member") or "").strip()
        if result_member and result_member not in existing:
            merged.append((result_member, row_comment))
            existing.add(result_member)
        for operand in _as_str_list(row.get("condition_operands")):
            token = str(operand or "").strip()
            if token and token not in existing:
                merged.append((token, row_comment))
                existing.add(token)
        # Make variables usable across FC categories even when the user
        # writes only the boolean expression and leaves condition_operands empty.
        expression = str(row.get("condition_expression") or "").strip()
        for token in re.findall(r"[A-Za-z_]\w*(?:\.\w+)*", expression):
            if token.upper() in {"AND", "OR", "NOT", "TRUE", "FALSE"}:
                continue
            normalized = _support_member_name(token, "", strict_excel_mode=True)
            if normalized and normalized not in existing:
                merged.append((normalized, row_comment))
                existing.add(normalized)
    return _dedupe_named_members(merged)


def _strict_support_db_catalog(ir: AwlIR) -> set[str] | None:
    if not ir.strict_operand_catalog:
        return None
    allowed: set[str] = set()
    for token in ir.operand_catalog:
        raw = str(token or "").strip()
        if not raw:
            continue
        allowed.add(_support_member_name(raw, "", strict_excel_mode=True))
    return allowed


def _prepare_support_members(
    ir: AwlIR,
    category: str,
    members: list[tuple[str, str]],
    logic_rows: list[dict[str, object]],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    merged = _merge_support_members_with_logic(members, logic_rows)
    db_members = _prepare_support_db_members(ir, category, merged)
    fc_members = _dedupe_named_members(
        [(name, comment) for name, comment in merged if str(name or "").strip()]
    )
    return _dedupe_named_members(db_members), fc_members


def _prepare_support_db_members(
    ir: AwlIR,
    category: str,
    members: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    allowed = _strict_support_db_catalog(ir)
    operand_notes = _support_operand_notes(ir)
    explicit_excel_comments = _explicit_excel_member_comments(ir)
    current_db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, category)
    owner_db_map = _build_support_symbol_home_db_map(ir)
    filtered = [
        (name, comment)
        for name, comment in members
        if owner_db_map.get(name, current_db_name) == current_db_name
    ]
    if allowed is not None:
        filtered = [(name, comment) for name, comment in filtered if name in allowed]

    enriched: list[tuple[str, str]] = []
    for name, comment in filtered:
        # In strict Excel mode, avoid auto-generated comments:
        # keep only explicit Excel comments and operands.note.
        if ir.strict_operand_catalog:
            base_comment = str(explicit_excel_comments.get(name) or "").strip()
        else:
            base_comment = str(comment or "").strip()
        note_comment = str(operand_notes.get(name) or "").strip()
        if note_comment and base_comment:
            if note_comment in base_comment:
                final_comment = base_comment
            else:
                final_comment = f"{note_comment} | {base_comment}"
        else:
            final_comment = note_comment or base_comment
        enriched.append((name, final_comment))
    return _dedupe_named_members(enriched)


def _explicit_excel_member_comments(ir: AwlIR) -> dict[str, str]:
    comments: dict[str, str] = {}

    for item in ir.support_members:
        raw_name = str(item.get("member_name") or "").strip()
        raw_comment = str(item.get("comment") or "").strip()
        if not raw_name or not raw_comment:
            continue
        normalized = _support_member_name(raw_name, "", strict_excel_mode=True)
        if normalized:
            comments.setdefault(normalized, raw_comment)

    return comments


def _build_support_symbol_home_db_map(ir: AwlIR) -> dict[str, str]:
    # 1) Explicit ownership from operands sheet (Excel strict mode).
    explicit_category_map: dict[str, str] = {
        "alarm": "diag",
        "aux": "aux",
        "memory": "aux",
        "hmi": "hmi",
        "external": "external",
        "output": "io",
        "lv2": "mode",
        "lev2": "mode",
        "mode": "mode",
        "transition": "transitions",
        "transitions": "transitions",
    }
    mapping: dict[str, str] = {}
    allowed = _strict_support_db_catalog(ir)
    for raw_name, raw_category in ir.operand_categories.items():
        operand_name = str(raw_name or "").strip()
        category = explicit_category_map.get(str(raw_category or "").strip().lower())
        if not operand_name or not category:
            continue
        member_name = _support_member_name(operand_name, "", strict_excel_mode=True)
        if allowed is not None and member_name not in allowed:
            continue
        db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, category)
        mapping.setdefault(member_name, db_name)

    guard_members_by_category = _collect_transition_guard_members_by_category(ir)
    operand_aliases = _build_awl_operand_alias_map(ir)

    # 2) Heuristic fallback from support members and inferred collections.
    category_sources: list[tuple[str, list[tuple[str, str]]]] = [
        # Priority order matters: explicit/specialized families first.
        ("hmi", _excel_support_members(ir, "hmi") or _collect_hmi_support_members(ir)),
        ("diag", ( _excel_support_members(ir, "diag") or _collect_diag_support_members(ir)) + guard_members_by_category.get("diag", [])),
        ("aux", _excel_support_members(ir, "aux") or _collect_aux_support_members(ir)),
        ("transitions", ( _excel_support_members(ir, "transitions") or _collect_transitions_support_members(ir, [])) + guard_members_by_category.get("transitions", [])),
        ("io", ( _excel_support_members(ir, "io") or _collect_io_support_members(ir)) + guard_members_by_category.get("io", [])),
        # Outputs are physically hosted in the IO DB artifact (DB16 family).
        ("io", _excel_support_members(ir, "output") or _collect_output_family_members(ir)),
        ("external", _excel_support_members(ir, "external") or _collect_external_support_members(ir)),
        ("mode", _excel_support_members(ir, "mode") or _collect_mode_support_members(ir)),
        ("hmi", guard_members_by_category.get("hmi", [])),
        ("aux", guard_members_by_category.get("aux", [])),
    ]
    for category, members in category_sources:
        db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, category)
        for name, _ in _dedupe_named_members(members):
            token = str(name or "").strip()
            if not token:
                continue
            if allowed is not None and token not in allowed:
                continue
            mapping.setdefault(token, db_name)

    # 3) AWL symbolic aliases: ensure that "nice" names still resolve to the
    # correct owner DB even when logic rows reference the alias instead of the
    # raw address operand.
    for address_key, alias_norm in operand_aliases.items():
        category = _support_category_for_guard_operand(address_key)
        db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, category)
        alias_member = _support_member_name(alias_norm, "", strict_excel_mode=True)
        if alias_member and (allowed is None or alias_member in allowed):
            mapping.setdefault(alias_member, db_name)
        # Also support the sanitized address-style member name as a fallback key.
        address_member = _support_member_name(address_key, "", strict_excel_mode=True)
        if address_member and (allowed is None or address_member in allowed):
            mapping.setdefault(address_member, db_name)

    # 4) Synthetic AWL locals: keep them in AUX (DB19..).
    # Detect "L 1.0" style locals in raw lines and reserve their synthesized names.
    aux_db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, "aux")
    for network in ir.networks:
        for raw_line in network.raw_lines:
            for match in re.findall(r"\bL\s+(\d+(?:\.\d+)?)\b", raw_line, flags=re.IGNORECASE):
                local_token = f"L{match}"
                synth = _support_member_name(f"N{network.index}_{_normalize_operand_token(local_token)}", "", strict_excel_mode=True)
                if synth and (allowed is None or synth in allowed):
                    mapping[synth] = aux_db_name
    return mapping


def _collect_io_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for output in ir.outputs:
        members.append(
            (
                _support_member_name(output.name, "Q", strict_excel_mode=ir.strict_operand_catalog),
                f"Output mapping {output.name}",
            )
        )
    return list(dict.fromkeys(members))


def _collect_timer_trigger_support_members_by_category(
    ir: AwlIR,
) -> dict[str, list[tuple[str, str]]]:
    operand_aliases = _build_awl_operand_alias_map(ir)
    grouped: dict[str, list[tuple[str, str]]] = {
        "io": [],
        "aux": [],
        "hmi": [],
        "diag": [],
        "transitions": [],
    }
    for timer in ir.timers:
        timer_name = str(timer.source_timer or "").strip()
        for raw in (timer.trigger_operands or []):
            operand = str(raw or "").strip()
            if not operand:
                continue
            category = _support_category_for_guard_operand(operand)
            alias = operand_aliases.get(_normalize_operand_token(operand), "")
            member = _support_member_name(alias or operand, "", strict_excel_mode=True)
            if not member:
                continue
            grouped.setdefault(category, []).append((member, f"Timer trigger {timer_name}"))
    return {k: _dedupe_named_members(v) for k, v in grouped.items()}


def _collect_external_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    operand_aliases = _build_awl_operand_alias_map(ir)
    members: list[tuple[str, str]] = []
    for ext in ir.external_refs:
        if not _is_external_integration_operand(ext):
            continue
        normalized = _normalize_operand_token(ext)
        alias = operand_aliases.get(normalized, "")
        if not alias:
            shortcut = re.fullmatch(r"DB\d+\.(P\d{3}|L\d{3})", str(ext or "").strip(), flags=re.IGNORECASE)
            if shortcut:
                alias = shortcut.group(1).upper()
        symbol = alias or ext
        members.append(
            (
                _support_member_name(symbol, "", strict_excel_mode=True),
                f"External reference {symbol}",
            )
        )
    return list(dict.fromkeys(members))


def _is_external_integration_operand(operand: str) -> bool:
    token = str(operand or "").strip().upper()
    if not token:
        return False
    db_addr = re.fullmatch(r"DB(\d+)\.DB[XBWD]\d+(?:\.\d+)?", token)
    if db_addr:
        return int(db_addr.group(1)) in EXTERNAL_DB_IDS
    if token.startswith("DB81.") or token.startswith("DB82.") or token.startswith("DB202."):
        return True
    if re.fullmatch(r"(?:DI|PE|PA)\d+(?:\.\d+)?", token):
        return True
    return False


def _collect_diag_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for timer in ir.timers:
        members.append(
            (
                _support_member_name(timer.source_timer, "T", strict_excel_mode=ir.strict_operand_catalog),
                f"Timer diagnostic {timer.source_timer}",
            )
        )
    for fault in ir.faults:
        members.append(
            (
                _support_member_name(fault.name, "F", strict_excel_mode=ir.strict_operand_catalog),
                f"Fault diagnostic {fault.name}",
            )
        )
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
        member = _support_member_name(transition.transition_id, "TR", strict_excel_mode=ir.strict_operand_catalog)
        members.append((member, f"Transition edge {transition.source_step}->{transition.target_step}"))
    if not ir.strict_operand_catalog:
        for network_no, _, _ in network_specs:
            members.append((f"TR_NETWORK_{network_no}_ACTIVE", f"Transition network {network_no} active"))
    return list(dict.fromkeys(members))


def _collect_output_family_members(ir: AwlIR) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    for output in ir.outputs:
        member = _support_member_name(output.name, "OUT_CMD", strict_excel_mode=ir.strict_operand_catalog)
        members.append((member, f"Output command {output.action} {output.name}"))
    return list(dict.fromkeys(members))


def _collect_hmi_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    operand_aliases = _build_awl_operand_alias_map(ir)
    members: list[tuple[str, str]] = []
    for ext in ir.external_refs:
        candidate = ext.upper()
        if any(marker in candidate for marker in ("HMI", "OPIN", "OPOUT", "DB81", "DB82")):
            normalized = _normalize_operand_token(ext)
            alias = operand_aliases.get(normalized, "")
            if not alias:
                shortcut = re.fullmatch(r"DB\d+\.(P\d{3}|L\d{3})", str(ext or "").strip(), flags=re.IGNORECASE)
                if shortcut:
                    alias = shortcut.group(1).upper()
            symbol = alias or candidate
            member = _support_member_name(symbol, "", strict_excel_mode=True)
            members.append((member, f"HMI/Operator reference {symbol}"))
    for memory in ir.memories:
        if str(memory.role).lower() == "hmi":
            member = _support_member_name(memory.name, "HMI", strict_excel_mode=ir.strict_operand_catalog)
            members.append((member, f"HMI tagged memory {memory.name}"))
    return list(dict.fromkeys(members))


def _collect_aux_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    operand_aliases = _build_awl_operand_alias_map(ir)
    members: list[tuple[str, str]] = []
    for memory in ir.memories:
        raw = str(memory.name or "").strip()
        alias = operand_aliases.get(_normalize_operand_token(raw), "")
        member = _support_member_name(alias or raw, "", strict_excel_mode=True)
        members.append((member, f"Aux memory ({memory.role}) {alias or member}"))
    for timer in ir.timers:
        raw = str(timer.source_timer or "").strip()
        alias = operand_aliases.get(_normalize_operand_token(raw), "")
        member = _support_member_name(alias or raw, "", strict_excel_mode=True)
        members.append((member, f"Aux timer {alias or member}"))
        # Timer operands (e.g. T50) are used as bool contacts in AWL via the
        # "done" bit. Model this explicitly as a separate BOOL member.
        done_member = _guard_operand_db_member_name(raw, strict_excel_mode=False)
        members.append((done_member, f"Aux timer done {alias or member}"))
    return list(dict.fromkeys(members))


def _collect_parameters_support_members(ir: AwlIR) -> list[tuple[str, str]]:
    # PARAMETERS DB: keep control-like operands (timers/counters and non-bool process values)
    # in a stable place without inventing ad-hoc symbols.
    operand_aliases = _build_awl_operand_alias_map(ir)
    members: list[tuple[str, str]] = []
    datatype_map = _support_operand_datatypes(ir)
    for operand in ir.operand_catalog:
        token = str(operand or "").strip()
        if not token:
            continue
        alias = operand_aliases.get(_normalize_operand_token(token), "")
        symbol = alias or token
        datatype = _normalize_plc_datatype(datatype_map.get(token, ""))
        if datatype in {"IEC_TIMER", "IEC_COUNTER"}:
            member = _support_member_name(symbol, "PAR", strict_excel_mode=ir.strict_operand_catalog)
            members.append((member, f"Parameter/control operand {symbol} ({datatype})"))
            continue
        if datatype not in {"", "Bool"}:
            member = _support_member_name(symbol, "PAR", strict_excel_mode=ir.strict_operand_catalog)
            members.append((member, f"Parameter operand {symbol} ({datatype})"))
    # AWL fallback: derive DBW/DBD/DBB operands from symbolic lines when the
    # operand catalog is not populated (typical markdown AWL path).
    pattern = re.compile(
        r'"([^"]+)"\s*(?:\.\s*([A-Za-z0-9_]+))?\s+'
        r'(DB\d+\.DB([WDB])\d+)',
        flags=re.IGNORECASE,
    )
    for network in ir.networks:
        for raw_line in network.raw_lines:
            body = raw_line.split("--", 1)[0]
            match = pattern.search(body)
            if not match:
                continue
            symbolic_base = str(match.group(1) or "").strip()
            symbolic_leaf = str(match.group(2) or "").strip()
            address = str(match.group(3) or "").strip().upper()
            db_kind = str(match.group(4) or "").strip().upper()
            dtype = {"B": "Byte", "W": "Int", "D": "DInt"}.get(db_kind, "Int")
            alias = symbolic_leaf or _derive_symbol_alias_from_base(symbolic_base)
            symbol = alias or address
            member = _support_member_name(symbol, "PAR", strict_excel_mode=ir.strict_operand_catalog)
            members.append((member, f"Parameter operand {symbol} ({dtype})"))
    return list(dict.fromkeys(members))


def _collect_network_support_specs(ir: AwlIR) -> list[tuple[int, str, list[tuple[str, str]]]]:
    specs: list[tuple[int, str, list[tuple[str, str]]]] = []
    for network in ir.networks:
        network_members: list[tuple[str, str]] = []
        for operand in _collect_condition_operands(network):
            family = _classify_operand_family(operand)
            member = _support_member_name(operand, f"COND_{family}", strict_excel_mode=ir.strict_operand_catalog)
            network_members.append((member, f"Condition operand {operand} ({family})"))
        for output_name, action in _collect_output_targets(network):
            member = _support_member_name(output_name, "OUT", strict_excel_mode=ir.strict_operand_catalog)
            network_members.append((member, f"Output action {action} {output_name}"))
        for memory_name, action in _collect_memory_targets(network):
            member = _support_member_name(memory_name, "MEM", strict_excel_mode=ir.strict_operand_catalog)
            network_members.append((member, f"Memory action {action} {memory_name}"))
        unique_members = list(dict.fromkeys(network_members))
        if not unique_members:
            continue
        specs.append((network.index, network.title or f"NETWORK {network.index}", unique_members))
    return specs


def _support_member_name(raw_symbol: str, prefix: str, *, strict_excel_mode: bool = False) -> str:
    if strict_excel_mode:
        return _excel_preserving_db_member_name(raw_symbol, strict_excel_mode=True)
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
    db_number_base = DB_FAMILY_NUMBER_BASE.get(db_family, DB_FAMILY_NUMBER_BASE["sequence"])
    fc_number_base = FC_FAMILY_NUMBER_BASE.get(fc_family, FC_FAMILY_NUMBER_BASE["sequence"])

    if suffix:
        block_token = _normalize_symbol_name(suffix, suffix)
        file_suffix = block_token.lower()
    else:
        block_token = token
        file_suffix = file_token

    if db_prefix:
        db_name = f"{db_prefix}_{sequence_name}_{block_token}_DB"
        db_file = f"{db_prefix}_{sequence_name}_{file_suffix}_db_auto.xml"
    else:
        db_name = f"{sequence_name}_{block_token}_DB"
        db_file = f"DB_{sequence_name}_{file_suffix}_db_auto.xml"

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


def _support_category_for_guard_operand(operand: str) -> str:
    token = str(operand or "").strip().upper()
    if not token:
        return "transitions"
    if re.fullmatch(r"L\d+(?:\.\d+)?", token):
        return "aux"
    if re.fullmatch(r"N\d+_L\d+_\d+(?:_\d+)?", token):
        return "aux"
    if re.fullmatch(r"[AQ]\d+(?:\.\d+)?", token) or re.fullmatch(r"[IE]\d+(?:\.\d+)?", token):
        return "io"
    if re.fullmatch(r"M\d+(?:\.\d+)?", token) or re.fullmatch(r"T\d+", token):
        return "aux"
    db_match = re.fullmatch(r"DB(\d+)\.DB[XBWD]\d+(?:\.\d+)?", token)
    if db_match:
        db_no = int(db_match.group(1))
        if db_no in {81, 82}:
            return "hmi"
        if db_no >= 200:
            return "diag"
        if 100 <= db_no < 200:
            return "io"
        return "io"
    if token.startswith("DB81.") or token.startswith("DB82."):
        return "hmi"
    if token.startswith("DB202."):
        return "diag"
    return "transitions"


def _collect_transition_guard_members_by_category(
    ir: AwlIR,
) -> dict[str, list[tuple[str, str]]]:
    operand_aliases = _build_awl_operand_alias_map(ir)
    grouped: dict[str, list[tuple[str, str]]] = {
        "io": [],
        "aux": [],
        "hmi": [],
        "diag": [],
        "transitions": [],
    }
    used_names_by_category: dict[str, set[str]] = {key: set() for key in grouped}
    raw_to_member_by_category: dict[str, dict[str, str]] = {key: {} for key in grouped}
    for transition in ir.transitions:
        for operand in transition.guard_operands:
            raw = str(operand or "").strip()
            if not raw:
                continue
            category = _support_category_for_guard_operand(raw)
            raw_key = raw.upper()
            existing_member = raw_to_member_by_category[category].get(raw_key)
            if existing_member:
                comment_symbol = operand_aliases.get(raw_key, "") or existing_member
                grouped[category].append((existing_member, f"Guard operand {comment_symbol}"))
                continue
            # Keep guard members literal to AWL operands (TIA-sanitized),
            # avoiding synthetic prefixes such as TR_OP_/AUX_MEM_.
            alias = operand_aliases.get(raw_key, "")
            if category == "aux" and TIMER_RE.fullmatch(raw.upper()):
                member = _guard_operand_db_member_name(raw, strict_excel_mode=False)
            else:
                member = _support_member_name(alias or raw, "", strict_excel_mode=True)
            if member in used_names_by_category[category]:
                member = _support_member_name(f"{raw}_{transition.transition_id}", "", strict_excel_mode=True)
            used_names_by_category[category].add(member)
            raw_to_member_by_category[category][raw_key] = member
            comment_symbol = alias or member
            grouped[category].append((member, f"Guard operand {comment_symbol}"))
    return {category: _dedupe_named_members(items) for category, items in grouped.items()}


def _build_awl_operand_alias_map(ir: AwlIR) -> dict[str, str]:
    alias_map: dict[str, str] = {}
    alias_owner: dict[str, str] = {}
    pattern = re.compile(
        r'"([^"]+)"\s*(?:\.\s*([A-Za-z0-9_]+))?\s+'
        r'(DB\d+\.DB[XBWD]\d+(?:\.\d+)?|[AQEIMT]\d+(?:\.\d+)?)',
        flags=re.IGNORECASE,
    )
    for network in ir.networks:
        for raw_line in network.raw_lines:
            body, _, comment = raw_line.partition("--")
            match = pattern.search(body)
            if not match:
                continue
            symbolic_base = str(match.group(1) or "").strip()
            symbolic_leaf = str(match.group(2) or "").strip()
            address_raw = str(match.group(3) or "").strip()
            address_key = _normalize_operand_token(address_raw)
            if not address_key:
                continue
            base_alias = _derive_symbol_alias_from_base(symbolic_base)
            comment_alias = _derive_symbol_alias_from_comment(comment)
            # Prefer the *literal* symbolic leaf when present (e.g. "LLALM".DB202_DBX32_0),
            # even if it looks address-like. This keeps generated DB members stable and meaningful.
            if symbolic_leaf:
                alias_candidate = symbolic_leaf
            elif comment_alias:
                alias_candidate = comment_alias
            else:
                alias_candidate = base_alias
            alias_norm = _normalize_symbol_name(alias_candidate, "")
            if not alias_norm:
                continue
            owner = alias_owner.get(alias_norm)
            if owner and owner != address_key:
                if symbolic_leaf:
                    disambiguator = symbolic_leaf
                elif comment_alias and comment_alias != alias_norm:
                    disambiguator = comment_alias
                else:
                    disambiguator = _stable_hash_token(address_key, size=6)
                expanded_seed = f"{base_alias}_{disambiguator}" if base_alias else f"{alias_norm}_{disambiguator}"
                expanded = _normalize_symbol_name(expanded_seed, alias_norm)
                if expanded and alias_owner.get(expanded) not in {None, address_key}:
                    expanded = _normalize_symbol_name(f"{alias_norm}_{_stable_hash_token(address_key, size=8)}", alias_norm)
                alias_norm = expanded or alias_norm
            alias_map.setdefault(address_key, alias_norm)
            alias_owner.setdefault(alias_norm, address_key)
    return alias_map


def _derive_symbol_alias_from_base(symbolic_base: str) -> str:
    token = str(symbolic_base or "").strip()
    if not token:
        return ""
    parts = re.split(r"[\s:/\-]+", token)
    parts = [item for item in parts if item]
    if not parts:
        return ""
    meaningful = [item for item in parts if len(item) > 1]
    if not meaningful:
        return parts[-1]
    if len(meaningful) == 1:
        return meaningful[0]
    return "_".join(meaningful[-2:])


def _derive_symbol_alias_from_comment(comment: str) -> str:
    raw = str(comment or "").strip()
    if not raw:
        return ""
    words = re.findall(r"[A-Za-z][A-Za-z0-9_]+", raw)
    words = [word for word in words if len(word) > 2][:4]
    if not words:
        return ""
    return "_".join(words)


def _render_graph_step(step: GraphStepNode) -> str:
    step_name = step.name or str(step.step_no)
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


def _render_graph_transition(
    transition: GraphTransitionNode,
    *,
    strict_excel_mode: bool = False,
    symbol_home_db_map: dict[str, str] | None = None,
    operand_aliases: dict[str, str] | None = None,
) -> str:
    next_uid = 21

    def alloc_uid() -> int:
        nonlocal next_uid
        current = next_uid
        next_uid += 1
        return current

    parts_lines: list[str] = []
    wires_lines: list[str] = []
    owner_db_map = symbol_home_db_map or {}
    alias_map = operand_aliases or {}

    def _operand_binding(operand: str) -> tuple[str, str]:
        raw = str(operand or "").strip()
        if not raw:
            return transition.db_block_name, transition.db_member_name
        canonical_member = _guard_operand_db_member_name(raw, strict_excel_mode=strict_excel_mode)
        strict_member = _support_member_name(raw, "", strict_excel_mode=True)
        alias_raw = alias_map.get(_normalize_operand_token(raw), "")
        alias_member = _support_member_name(alias_raw, "", strict_excel_mode=True) if alias_raw else ""
        # Try direct + normalized spellings to honor Excel strict names and
        # compatibility aliases produced by support member collectors.
        candidate_keys = [
            alias_member,
            canonical_member,
            strict_member,
            raw,
        ]
        # Non-strict AWL path: support DBs can prefix symbols by family
        # (e.g. AUX_MEM_M44_0, DBEXT_DB102_DBX6_0). Try compatible aliases.
        if not strict_excel_mode:
            family = _classify_operand_family(raw)
            candidate_keys.extend(
                [
                    _support_member_name(raw, family, strict_excel_mode=False),
                    _support_member_name(raw, f"COND_{family}", strict_excel_mode=False),
                    _support_member_name(raw, "AUX_MEM", strict_excel_mode=False),
                    _support_member_name(raw, "AUX_TIMER", strict_excel_mode=False),
                    _support_member_name(raw, "OUT_CMD", strict_excel_mode=False),
                    _support_member_name(raw, "HMI", strict_excel_mode=False),
                    _support_member_name(raw, "PAR", strict_excel_mode=False),
                ]
            )
            # Last resort: suffix match against known support symbols.
            for key in owner_db_map:
                if key == strict_member or key.endswith(f"_{strict_member}"):
                    candidate_keys.append(key)

        for key in candidate_keys:
            if key in owner_db_map:
                return owner_db_map[key], key
        return transition.db_block_name, canonical_member

    guard_clauses = _parse_guard_clauses(transition.guard_expression, transition.guard_operands)
    guard_clauses, common_terms = _factor_common_guard_terms(guard_clauses)
    clause_contact_uids: list[list[int]] = []
    has_true_clause = any(not clause for clause in guard_clauses)

    for clause in guard_clauses:
        if not clause:
            continue
        contact_uids: list[int] = []
        for operand, negated in clause:
            owner_db_name, owner_member_name = _operand_binding(operand)
            access_uid = alloc_uid()
            contact_uid = alloc_uid()
            parts_lines.extend(
                [
                    f'            <Access Scope="GlobalVariable" UId="{access_uid}">\n',
                    '              <Symbol>\n',
                    f'                <Component Name="{escape(owner_db_name)}" />\n',
                    f'                <Component Name="{escape(owner_member_name)}" />\n',
                    '              </Symbol>\n',
                    '            </Access>\n',
                ]
            )
            if negated:
                parts_lines.extend(
                    [
                        f'            <Part Name="Contact" UId="{contact_uid}">\n',
                        '              <Negated Name="operand" />\n',
                        '            </Part>\n',
                    ]
                )
            else:
                parts_lines.append(f'            <Part Name="Contact" UId="{contact_uid}" />\n')

            wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'            <Wire UId="{wire_uid}">\n',
                    f'              <IdentCon UId="{access_uid}" />\n',
                    f'              <NameCon UId="{contact_uid}" Name="operand" />\n',
                    '            </Wire>\n',
                ]
            )
            contact_uids.append(contact_uid)

        if contact_uids:
            clause_contact_uids.append(contact_uids)

    trcoil_uid = alloc_uid()
    parts_lines.append(f'            <Part Name="TrCoil" UId="{trcoil_uid}" />\n')

    logic_output_uid: int | None = None
    if clause_contact_uids and not has_true_clause:
        # Powerrail feeds all OR branches (one branch per clause).
        powerrail_wire_uid = alloc_uid()
        wires_lines.append(f'            <Wire UId="{powerrail_wire_uid}">\n')
        wires_lines.append('              <Powerrail />\n')
        for branch in clause_contact_uids:
            if branch:
                wires_lines.append(f'              <NameCon UId="{branch[0]}" Name="in" />\n')
        wires_lines.append('            </Wire>\n')

        clause_outs: list[int] = []
        for branch in clause_contact_uids:
            if not branch:
                continue
            for prev_uid, next_contact_uid in zip(branch, branch[1:]):
                serial_wire_uid = alloc_uid()
                wires_lines.extend(
                    [
                        f'            <Wire UId="{serial_wire_uid}">\n',
                        f'              <NameCon UId="{prev_uid}" Name="out" />\n',
                        f'              <NameCon UId="{next_contact_uid}" Name="in" />\n',
                        '            </Wire>\n',
                    ]
                )
            clause_outs.append(branch[-1])

        if len(clause_outs) > 1:
            or_uid = alloc_uid()
            parts_lines.extend(
                [
                    f'            <Part Name="O" UId="{or_uid}">\n',
                    f'              <TemplateValue Name="Card" Type="Cardinality">{len(clause_outs)}</TemplateValue>\n',
                    '            </Part>\n',
                ]
            )
            for index, out_uid in enumerate(clause_outs, start=1):
                in_wire_uid = alloc_uid()
                wires_lines.extend(
                    [
                        f'            <Wire UId="{in_wire_uid}">\n',
                        f'              <NameCon UId="{out_uid}" Name="out" />\n',
                        f'              <NameCon UId="{or_uid}" Name="in{index}" />\n',
                        '            </Wire>\n',
                    ]
                )
            logic_output_uid = or_uid
        elif clause_outs:
            logic_output_uid = clause_outs[0]

    if common_terms:
        for operand, negated in common_terms:
            owner_db_name, owner_member_name = _operand_binding(operand)
            access_uid = alloc_uid()
            contact_uid = alloc_uid()
            parts_lines.extend(
                [
                    f'            <Access Scope="GlobalVariable" UId="{access_uid}">\n',
                    '              <Symbol>\n',
                    f'                <Component Name="{escape(owner_db_name)}" />\n',
                    f'                <Component Name="{escape(owner_member_name)}" />\n',
                    '              </Symbol>\n',
                    '            </Access>\n',
                ]
            )
            if negated:
                parts_lines.extend(
                    [
                        f'            <Part Name="Contact" UId="{contact_uid}">\n',
                        '              <Negated Name="operand" />\n',
                        '            </Part>\n',
                    ]
                )
            else:
                parts_lines.append(f'            <Part Name="Contact" UId="{contact_uid}" />\n')

            operand_wire_uid = alloc_uid()
            wires_lines.extend(
                [
                    f'            <Wire UId="{operand_wire_uid}">\n',
                    f'              <IdentCon UId="{access_uid}" />\n',
                    f'              <NameCon UId="{contact_uid}" Name="operand" />\n',
                    '            </Wire>\n',
                ]
            )

            in_wire_uid = alloc_uid()
            if logic_output_uid is None:
                wires_lines.extend(
                    [
                        f'            <Wire UId="{in_wire_uid}">\n',
                        '              <Powerrail />\n',
                        f'              <NameCon UId="{contact_uid}" Name="in" />\n',
                        '            </Wire>\n',
                    ]
                )
            else:
                wires_lines.extend(
                    [
                        f'            <Wire UId="{in_wire_uid}">\n',
                        f'              <NameCon UId="{logic_output_uid}" Name="out" />\n',
                        f'              <NameCon UId="{contact_uid}" Name="in" />\n',
                        '            </Wire>\n',
                    ]
                )
            logic_output_uid = contact_uid

    final_wire_uid = alloc_uid()
    if logic_output_uid is None:
        # TRUE / empty condition: direct powerrail to transition coil.
        wires_lines.extend(
            [
                f'            <Wire UId="{final_wire_uid}">\n',
                '              <Powerrail />\n',
                f'              <NameCon UId="{trcoil_uid}" Name="in" />\n',
                '            </Wire>\n',
            ]
        )
    else:
        wires_lines.extend(
            [
                f'            <Wire UId="{final_wire_uid}">\n',
                f'              <NameCon UId="{logic_output_uid}" Name="out" />\n',
                f'              <NameCon UId="{trcoil_uid}" Name="in" />\n',
                '            </Wire>\n',
            ]
        )

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


def _parse_guard_clauses(guard_expression: str, guard_operands: list[str]) -> list[list[tuple[str, bool]]]:
    text = (guard_expression or "").strip()
    if not text or text.upper() == "TRUE":
        return []
    parsed = _parse_boolean_guard_to_dnf(text)
    if parsed is not None:
        return parsed

    if guard_operands:
        return [[(item, False) for item in guard_operands if item]]
    return []


def _factor_common_guard_terms(
    clauses: list[list[tuple[str, bool]]],
) -> tuple[list[list[tuple[str, bool]]], list[tuple[str, bool]]]:
    if not clauses:
        return [], []
    non_empty = [clause for clause in clauses if clause]
    if not non_empty:
        return clauses, []

    common_candidates = set(non_empty[0])
    for clause in non_empty[1:]:
        common_candidates &= set(clause)
    if not common_candidates:
        return clauses, []

    ordered_common: list[tuple[str, bool]] = []
    seen_common: set[tuple[str, bool]] = set()
    for token, negated in non_empty[0]:
        item = (token, negated)
        if item in common_candidates and item not in seen_common:
            ordered_common.append(item)
            seen_common.add(item)

    reduced: list[list[tuple[str, bool]]] = []
    for clause in clauses:
        reduced.append([item for item in clause if item not in seen_common])
    return reduced, ordered_common


def _parse_boolean_guard_to_dnf(expression: str) -> list[list[tuple[str, bool]]] | None:
    tokens = _tokenize_boolean_expression(expression)
    if tokens is None:
        return None
    if not tokens:
        return []
    node, index = _parse_boolean_or(tokens, 0)
    if node is None:
        return None
    if index != len(tokens):
        return None
    nnf = _boolean_to_nnf(node)
    clauses = _boolean_nnf_to_dnf(nnf)
    return _normalize_boolean_clauses(clauses)


def _tokenize_boolean_expression(expression: str) -> list[tuple[str, str]] | None:
    # Tokens: operators (AND/OR/NOT), parentheses, and operands.
    token_re = re.compile(
        r"\s*("
        r"\("                           # open paren
        r"|\)"                          # close paren
        r"|AND\b|OR\b|NOT\b"            # operators
        r"|[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)*"  # operand
        r")",
        flags=re.IGNORECASE,
    )
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(expression):
        match = token_re.match(expression, pos)
        if not match:
            return None
        raw = match.group(1)
        upper = raw.upper()
        if raw == "(":
            kind = "LPAREN"
        elif raw == ")":
            kind = "RPAREN"
        elif upper in {"AND", "OR", "NOT"}:
            kind = upper
        else:
            kind = "IDENT"
        tokens.append((kind, raw))
        pos = match.end()
    return tokens


def _parse_boolean_or(tokens: list[tuple[str, str]], index: int) -> tuple[tuple | None, int]:
    left, index = _parse_boolean_and(tokens, index)
    if left is None:
        return None, index
    while index < len(tokens) and tokens[index][0] == "OR":
        index += 1
        right, index = _parse_boolean_and(tokens, index)
        if right is None:
            return None, index
        left = ("or", left, right)
    return left, index


def _parse_boolean_and(tokens: list[tuple[str, str]], index: int) -> tuple[tuple | None, int]:
    left, index = _parse_boolean_unary(tokens, index)
    if left is None:
        return None, index
    while index < len(tokens) and tokens[index][0] == "AND":
        index += 1
        right, index = _parse_boolean_unary(tokens, index)
        if right is None:
            return None, index
        left = ("and", left, right)
    return left, index


def _parse_boolean_unary(tokens: list[tuple[str, str]], index: int) -> tuple[tuple | None, int]:
    if index >= len(tokens):
        return None, index
    kind, raw = tokens[index]
    if kind == "NOT":
        node, next_index = _parse_boolean_unary(tokens, index + 1)
        if node is None:
            return None, next_index
        return ("not", node), next_index
    if kind == "LPAREN":
        node, next_index = _parse_boolean_or(tokens, index + 1)
        if node is None:
            return None, next_index
        if next_index >= len(tokens) or tokens[next_index][0] != "RPAREN":
            return None, next_index
        return node, next_index + 1
    if kind == "IDENT":
        upper = raw.upper()
        if upper == "TRUE":
            return ("true",), index + 1
        if upper == "FALSE":
            return ("false",), index + 1
        return ("lit", raw), index + 1
    return None, index


def _boolean_to_nnf(node: tuple, negated: bool = False) -> tuple:
    kind = node[0]
    if kind == "lit":
        return ("lit", node[1], negated)
    if kind == "true":
        return ("false",) if negated else ("true",)
    if kind == "false":
        return ("true",) if negated else ("false",)
    if kind == "not":
        return _boolean_to_nnf(node[1], not negated)
    if kind == "and":
        left = _boolean_to_nnf(node[1], negated)
        right = _boolean_to_nnf(node[2], negated)
        return ("or", left, right) if negated else ("and", left, right)
    if kind == "or":
        left = _boolean_to_nnf(node[1], negated)
        right = _boolean_to_nnf(node[2], negated)
        return ("and", left, right) if negated else ("or", left, right)
    return ("false",)


def _boolean_nnf_to_dnf(node: tuple) -> list[list[tuple[str, bool]]]:
    kind = node[0]
    if kind == "true":
        return [[]]
    if kind == "false":
        return []
    if kind == "lit":
        return [[(str(node[1]), bool(node[2]))]]
    if kind == "or":
        return _boolean_nnf_to_dnf(node[1]) + _boolean_nnf_to_dnf(node[2])
    if kind == "and":
        left = _boolean_nnf_to_dnf(node[1])
        right = _boolean_nnf_to_dnf(node[2])
        if not left or not right:
            return []
        combined: list[list[tuple[str, bool]]] = []
        for left_clause in left:
            for right_clause in right:
                combined.append(left_clause + right_clause)
        return combined
    return []


def _normalize_boolean_clauses(
    clauses: list[list[tuple[str, bool]]],
) -> list[list[tuple[str, bool]]]:
    normalized: list[list[tuple[str, bool]]] = []
    seen: set[tuple[tuple[str, bool], ...]] = set()
    for clause in clauses:
        per_symbol: dict[str, bool] = {}
        contradictory = False
        for token, negated in clause:
            symbol = str(token or "").strip()
            if not symbol:
                continue
            previous = per_symbol.get(symbol)
            if previous is None:
                per_symbol[symbol] = bool(negated)
                continue
            if previous != bool(negated):
                contradictory = True
                break
        if contradictory:
            continue
        ordered_clause = tuple(sorted(per_symbol.items(), key=lambda item: item[0]))
        if ordered_clause in seen:
            continue
        seen.add(ordered_clause)
        normalized.append([(token, negated) for token, negated in ordered_clause])
    return normalized


def _split_top_level_boolean(expression: str, operator: str) -> list[str]:
    text = (expression or "").strip()
    if not text:
        return []

    op = operator.upper()
    parts: list[str] = []
    buff: list[str] = []
    depth = 0
    i = 0
    upper = text.upper()
    while i < len(text):
        ch = text[i]
        if ch == "(":
            depth += 1
            buff.append(ch)
            i += 1
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            buff.append(ch)
            i += 1
            continue
        if (
            depth == 0
            and upper[i : i + len(op)] == op
            and (i == 0 or not upper[i - 1].isalnum())
            and (i + len(op) >= len(text) or not upper[i + len(op)].isalnum())
        ):
            item = "".join(buff).strip()
            if item:
                parts.append(item)
            buff = []
            i += len(op)
            continue
        buff.append(ch)
        i += 1

    tail = "".join(buff).strip()
    if tail:
        parts.append(tail)
    return parts


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


def _render_multilingual_text_items(item_id_hex: str, text: str, indent: str = "") -> str:
    escaped_text = escape(text)
    return (
        f'{indent}<MultilingualTextItem ID="{item_id_hex}" CompositionName="Items">\n'
        f"{indent}  <AttributeList>\n"
        f"{indent}    <Culture>en-US</Culture>\n"
        f"{indent}    <Text>{escaped_text}</Text>\n"
        f"{indent}  </AttributeList>\n"
        f"{indent}</MultilingualTextItem>"
    )


def _normalize_symbol_name(guard_expression: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", guard_expression).strip("_")
    return cleaned or fallback


def _db_member_name(raw_name: str) -> str:
    sanitized = raw_name.replace(".", "_")
    return _sanitize_tia_member_name(sanitized, fallback="Signal", seed=raw_name)


def _excel_preserving_db_member_name(raw_name: str, *, strict_excel_mode: bool) -> str:
    if strict_excel_mode:
        return _sanitize_tia_member_name(raw_name, fallback="Signal", seed=raw_name)
    return _db_member_name(raw_name)


def _guard_operand_db_member_name(operand: str, *, strict_excel_mode: bool = False) -> str:
    token = str(operand or "").strip()
    if strict_excel_mode:
        return _excel_preserving_db_member_name(token, strict_excel_mode=True)
    if TIMER_RE.fullmatch(token.upper()):
        return _db_member_name(f"{token}_DONE")
    return _db_member_name(token)


def _derive_awl_timer_logic_rows(ir: AwlIR) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    operand_aliases = _build_awl_operand_alias_map(ir)
    for timer in ir.timers:
        timer_name = str(timer.source_timer or "").strip()
        if not timer_name:
            continue
        trigger_ops_raw = [str(op or "").strip() for op in (timer.trigger_operands or []) if str(op or "").strip()]
        trigger_ops: list[str] = []
        for raw in trigger_ops_raw:
            alias = operand_aliases.get(_normalize_operand_token(raw), "")
            trigger_ops.append(_support_member_name(alias or raw, "", strict_excel_mode=True))
        trigger_ops = [op for op in trigger_ops if op]
        condition_expression = " AND ".join(trigger_ops) if trigger_ops else "TRUE"
        rows.append(
            {
                "result_member": _guard_operand_db_member_name(timer_name, strict_excel_mode=False),
                "condition_expression": condition_expression,
                "condition_operands": trigger_ops,
                "coil_mode": "",
                "comment": f"Aux timer {timer_name}",
                "network_index": int(timer.network_index or 0),
            }
        )
    rows.sort(
        key=lambda row: (
            _as_positive_int(row.get("network_index")) or 10**9,
            str(row.get("result_member") or ""),
        )
    )
    return rows


def _derive_awl_action_logic_rows(ir: AwlIR) -> dict[str, list[dict[str, object]]]:
    """
    Derive support_fc-like logic rows from raw AWL networks.

    Goal: keep the AWL behavior by materializing SET/RESET/ASSIGN operations
    into the correct support FC (AUX for M bits, OUTPUT for Q/A bits).
    """
    operand_aliases = _build_awl_operand_alias_map(ir)
    rows_by_category: dict[str, list[dict[str, object]]] = {
        "aux": [],
        "io": [],
        "hmi": [],
        "diag": [],
        "transitions": [],
    }

    def _map_symbol(raw: str, network_index: int) -> str:
        normalized = _normalize_operand_token(raw)
        if re.fullmatch(r"L\d+(?:\.\d+)?", normalized, flags=re.IGNORECASE):
            return _support_member_name(f"N{network_index}_{normalized}", "", strict_excel_mode=True)
        # In AWL, using "Txx" in boolean logic means the timer's done bit, not the IEC_TIMER instance.
        if TIMER_RE.fullmatch(normalized.upper()):
            return _support_member_name(f"{normalized}_DONE", "", strict_excel_mode=True)
        alias = operand_aliases.get(normalized, "")
        return _support_member_name(alias or raw, "", strict_excel_mode=True)

    def _rewrite_expression(expr: str, network_index: int, *, strip_locals: bool) -> tuple[str, list[str]]:
        tokens = _tokenize_boolean_expression(expr or "")
        if tokens is None:
            return "TRUE", []
        rewritten: list[str] = []
        operands: list[str] = []
        for kind, raw in tokens:
            if kind != "IDENT":
                rewritten.append(raw)
                continue
            upper = raw.upper()
            if upper in {"AND", "OR", "NOT", "TRUE", "FALSE"}:
                rewritten.append(upper)
                continue
            normalized = _normalize_operand_token(raw)
            if strip_locals and re.fullmatch(r"L\d+(?:\.\d+)?", normalized, flags=re.IGNORECASE):
                continue
            symbol = _map_symbol(raw, network_index)
            if not symbol:
                continue
            rewritten.append(symbol)
            operands.append(symbol)
        rendered = " ".join(rewritten).strip() or "TRUE"
        return rendered, _dedupe_list(operands)

    for network in ir.networks:
        condition_expression, condition_operands_raw = _collect_condition_logic(network)
        if not condition_expression:
            condition_expression = "TRUE"
        condition_expression, condition_operands = _rewrite_expression(
            condition_expression,
            network.index,
            strip_locals=False,
        )
        if not condition_operands and condition_operands_raw:
            for raw in condition_operands_raw:
                operand = _map_symbol(raw, network.index)
                if operand:
                    condition_operands.append(operand)
            condition_operands = _dedupe_list(condition_operands)
        if condition_operands and condition_expression == "TRUE":
            condition_expression = " AND ".join(condition_operands)

        for raw_target, action in _collect_memory_targets(network):
            result_member = _map_symbol(raw_target, network.index)
            if not result_member:
                continue
            coil_mode = ""
            if action == "S":
                coil_mode = "set"
            elif action == "R":
                coil_mode = "reset"
            rows_by_category["aux"].append(
                {
                    "result_member": result_member,
                    "condition_expression": condition_expression,
                    "condition_operands": list(condition_operands),
                    "coil_mode": coil_mode,
                    "comment": network.title or f"NETWORK {network.index}",
                    "network_index": network.index,
                }
            )

        for raw_target, action in _collect_local_targets(network):
            result_member = _map_symbol(raw_target, network.index)
            if not result_member:
                continue
            local_expr, local_ops = _rewrite_expression(
                condition_expression,
                network.index,
                strip_locals=True,
            )
            if local_ops and local_expr == "TRUE":
                local_expr = " AND ".join(local_ops)
            coil_mode = ""
            if action == "S":
                coil_mode = "set"
            elif action == "R":
                coil_mode = "reset"
            rows_by_category["aux"].append(
                {
                    "result_member": result_member,
                    "condition_expression": local_expr,
                    "condition_operands": list(local_ops),
                    "coil_mode": coil_mode,
                    "comment": network.title or f"NETWORK {network.index}",
                    "network_index": network.index,
                }
            )

        for raw_target, action in _collect_output_targets(network):
            result_member = _map_symbol(raw_target, network.index)
            if not result_member:
                continue
            coil_mode = ""
            if action == "S":
                coil_mode = "set"
            elif action == "R":
                coil_mode = "reset"
            rows_by_category["io"].append(
                {
                    "result_member": result_member,
                    "condition_expression": condition_expression,
                    "condition_operands": list(condition_operands),
                    "coil_mode": coil_mode,
                    "comment": network.title or f"NETWORK {network.index}",
                    "network_index": network.index,
                }
            )

        # Generic "=" / S/R to DB operands (e.g. DB202 alarms, DB82 opout, internal DB102 bits).
        for instr in network.instructions:
            if instr.opcode not in ACTION_OPCODES or not instr.args:
                continue
            raw_operand = _select_instruction_operand(instr.args)
            if not raw_operand:
                continue
            normalized = _normalize_operand_token(raw_operand)
            # Skip targets handled by specialized collectors above.
            if MEMORY_RE.fullmatch(normalized) or OUTPUT_RE.fullmatch(normalized) or re.fullmatch(r"L\d+(?:\.\d+)?", normalized):
                continue
            if not _is_address_like_operand(normalized) and not normalized.startswith("DB"):
                continue
            category = _support_category_for_guard_operand(normalized)
            # Route internal DB writes to IO when they belong to the sequence family.
            result_member = _map_symbol(raw_operand, network.index)
            if not result_member:
                continue
            coil_mode = ""
            if instr.opcode == "S":
                coil_mode = "set"
            elif instr.opcode == "R":
                coil_mode = "reset"
            rows_by_category.setdefault(category, []).append(
                {
                    "result_member": result_member,
                    "condition_expression": condition_expression,
                    "condition_operands": list(condition_operands),
                    "coil_mode": coil_mode,
                    "comment": network.title or f"NETWORK {network.index}",
                    "network_index": network.index,
                }
            )

    # Transitions support FC: materialize guard expressions into TR_* coils so the
    # generated TIA project is functional even without an Excel support sheet.
    for transition in ir.transitions:
        result_member = _support_member_name(str(transition.transition_id or "").strip(), "TR", strict_excel_mode=True)
        if not result_member:
            continue
        network_index = _as_positive_int(getattr(transition, "network_index", None)) or 0
        guard_expression_raw = str(getattr(transition, "guard_expression", "") or "").strip() or "TRUE"
        expr, ops = _rewrite_expression(guard_expression_raw, network_index, strip_locals=False)
        if not ops and getattr(transition, "guard_operands", None):
            mapped_ops: list[str] = []
            for raw in (transition.guard_operands or []):
                operand = _map_symbol(str(raw or ""), network_index)
                if operand:
                    mapped_ops.append(operand)
            ops = _dedupe_list(mapped_ops)
        if ops and (not expr or expr.strip().upper() == "TRUE"):
            expr = " AND ".join(ops)
        rows_by_category["transitions"].append(
            {
                "result_member": result_member,
                "condition_expression": expr or "TRUE",
                "condition_operands": list(_dedupe_list(ops)),
                "coil_mode": "",
                "comment": f"{transition.transition_id}: {transition.source_step}->{transition.target_step}",
                "network_index": network_index,
            }
        )

    for key in rows_by_category:
        rows_by_category[key].sort(
            key=lambda row: (
                _as_positive_int(row.get("network_index")) or 10**9,
                str(row.get("result_member") or ""),
            )
        )
    return rows_by_category


def _global_db_block_name(ir: AwlIR) -> str:
    return f"{DB_FAMILY_PREFIX['sequence']}_{ir.sequence_name}_SEQ_DB"


def _transitions_db_block_name(ir: AwlIR) -> str:
    db_name, _, _, _, _, _ = _support_block_names(ir.sequence_name, "transitions")
    return db_name


def _lad_fc_block_name(ir: AwlIR) -> str:
    return f"{FC_FAMILY_PREFIX['transitions']}_{ir.sequence_name}_TRANSITIONS_LAD"


def _transition_db_member_name(transition: TransitionCandidate) -> str:
    return _transition_db_member_name_from_values(transition.transition_id, transition.guard_expression)


def _transition_db_member_name_from_values(transition_name: str, guard_expression: str) -> str:
    normalized = _normalize_symbol_name(guard_expression, transition_name)
    raw = f"{transition_name}_Guard_{normalized}"
    fallback = f"{_normalize_symbol_name(transition_name, 'T')}_Guard"
    return _sanitize_tia_member_name(raw, fallback=fallback, seed=f"{transition_name}|{guard_expression}")


def _assign_unique_transition_db_member_names(transition_nodes: list[GraphTransitionNode]) -> None:
    used: set[str] = set()
    for node in transition_nodes:
        candidate = _transition_db_member_name_from_values(node.name, node.guard_expression)
        if candidate in used:
            digest = _stable_hash_token(
                f"{node.name}|{node.guard_expression}|{node.source_step}|{node.target_step}",
                size=6,
            )
            candidate = _sanitize_tia_member_name(
                f"{candidate}_{digest}",
                fallback=f"{_normalize_symbol_name(node.name, 'T')}_Guard_{digest}",
                seed=f"{node.name}|{node.transition_no}|{digest}",
            )
            suffix = 2
            while candidate in used:
                candidate = _sanitize_tia_member_name(
                    f"{candidate}_{suffix}",
                    fallback=f"{_normalize_symbol_name(node.name, 'T')}_Guard_{suffix}",
                    seed=f"{node.name}|{node.transition_no}|{suffix}",
                )
                suffix += 1
        node.db_member_name = candidate
        used.add(candidate)


def _sanitize_tia_member_name(raw_name: str, fallback: str, seed: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", raw_name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", fallback) or "Signal"
    if cleaned[0].isdigit():
        cleaned = f"N_{cleaned}"
    if cleaned.upper() in TIA_RESERVED_KEYWORDS:
        cleaned = f"{cleaned}_ID"
    if len(cleaned) > TIA_MEMBER_NAME_MAX_LEN:
        digest = _stable_hash_token(seed, size=8)
        keep = TIA_MEMBER_NAME_MAX_LEN - len(digest) - 1
        if keep <= 0:
            cleaned = digest[:TIA_MEMBER_NAME_MAX_LEN]
        else:
            cleaned = f"{cleaned[:keep]}_{digest}"
    return cleaned


def _stable_hash_token(seed: str, size: int = 8) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest().upper()
    return digest[: max(size, 1)]


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
            matches.add(_canonicalize_step_token(match.upper()))
    return matches


def _collect_structured_external_aliases(network: AwlNetwork) -> set[str]:
    aliases: set[str] = set()
    for raw_line in network.raw_lines:
        body = raw_line.split("--", 1)[0]
        if not body.strip():
            continue

        # Preserve OPIN/OPOUT naming contract when present in symbolic AWL tokens.
        # Example: "DB:OPIN".P437 DB81.DBX54.4 -> DB81.P437
        # Example: "DB:OPOUT".L045 DB82.DBX5.4 -> DB82.L045
        opin_match = re.search(r'"DB:OPIN"\s*\.\s*(P\d{3})\b', body, flags=re.IGNORECASE)
        if opin_match:
            aliases.add(f"DB81.{opin_match.group(1).upper()}")

        opout_match = re.search(r'"DB:OPOUT"\s*\.\s*(L\d{3})\b', body, flags=re.IGNORECASE)
        if opout_match:
            aliases.add(f"DB82.{opout_match.group(1).upper()}")
    return aliases


def _normalize_external_refs(items: set[str]) -> list[str]:
    normalized: set[str] = set()
    for raw in items:
        token = str(raw or "").strip().upper()
        if not token:
            continue

        # Drop generic noise captured by broad regex.
        if token in {"DB", "DI", "PE", "PA", "E", "I"}:
            continue
        if re.fullmatch(r"DB\d+", token):
            continue

        # Normalize legacy symbolic style DB202_DBX32_0 -> DB202.DBX32.0
        dotted = re.fullmatch(r"DB(\d+)_DB([XBWD])(\d+)_(\d+)", token)
        if dotted:
            token = f"DB{dotted.group(1)}.DB{dotted.group(2)}{dotted.group(3)}.{dotted.group(4)}"

        db_operand = re.fullmatch(r"DB(\d+)\.DB[XBWD]\d+(?:\.\d+)?", token)
        if db_operand and int(db_operand.group(1)) not in EXTERNAL_DB_IDS:
            # Internal sequence DBs are handled by support category ownership,
            # they are not external integration references.
            continue

        normalized.add(token)

    return sorted(normalized)


def _collect_condition_logic(network: AwlNetwork) -> tuple[str, list[str]]:
    tokens = _tokenize_condition_logic(network)
    if not tokens:
        return "TRUE", []
    expression, operands, _ = _parse_condition_expression(tokens, 0)
    if not expression:
        return "TRUE", _dedupe_list(operands)
    return expression, _dedupe_list(operands)


def _collect_condition_operands(network: AwlNetwork) -> list[str]:
    _, operands = _collect_condition_logic(network)
    return operands


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


def _collect_timers_with_triggers(
    network: AwlNetwork,
) -> list[tuple[str, str, str | None, list[str]]]:
    timers: list[tuple[str, str, str | None, list[str]]] = []
    condition_operands: list[str] = []
    for instr in network.instructions:
        if instr.opcode in CONDITION_OPCODES and instr.args:
            operand = _select_instruction_operand(instr.args)
            if not operand:
                continue
            if STEP_RE.fullmatch(operand):
                # Step marker resets the condition chain.
                condition_operands = []
                continue
            condition_operands.append(operand)

        if instr.opcode in TIMER_OPCODES and instr.args:
            timer_name = _select_instruction_operand(instr.args)
            if not timer_name:
                continue
            preset = _extract_preset(network)
            timers.append((timer_name, instr.opcode, preset, list(condition_operands)))

    seen: set[tuple[str, str, str | None, tuple[str, ...]]] = set()
    unique: list[tuple[str, str, str | None, list[str]]] = []
    for name, kind, preset, triggers in timers:
        key = (name, kind, preset, tuple(triggers))
        if key in seen:
            continue
        seen.add(key)
        unique.append((name, kind, preset, _dedupe_list(triggers)))
    return unique


def _collect_trs_transitions_with_fallback(
    network: AwlNetwork,
    default_source_step: str | None,
) -> list[tuple[str, str, str, list[str]]]:
    trs_target: tuple[str, str] | None = None
    for index, instr in enumerate(network.instructions):
        if instr.opcode != "L" or not instr.args:
            continue
        numeric = _normalize_operand_token(instr.args[0])
        if not re.fullmatch(r"\d+", numeric):
            continue
        for follower in network.instructions[index + 1 : index + 6]:
            if follower.opcode != "T":
                continue
            prefix = _extract_trs_prefix(follower.args)
            if not prefix:
                continue
            trs_target = (prefix, f"S{int(numeric)}")
            break
        if trs_target:
            break

    if not trs_target:
        return []

    prefix, target_step = trs_target
    source_steps: list[str] = []
    for instr in network.instructions:
        if instr.opcode not in CONDITION_OPCODES or not instr.args:
            continue
        for raw_arg in instr.args:
            token = _normalize_operand_token(raw_arg)
            match = re.fullmatch(rf"{re.escape(prefix)}\.S0*(\d+)", token)
            if match:
                source_steps.append(f"S{int(match.group(1))}")

    source_steps = _dedupe_list(source_steps)
    if not source_steps:
        fallback = _canonicalize_step_token(str(default_source_step or "").strip().upper())
        if fallback and STEP_RE.fullmatch(fallback) and fallback != target_step:
            source_steps = [fallback]
        else:
            return []

    guard_expression, guard_ops = _collect_condition_logic(network)
    return [(source_step, target_step, guard_expression, guard_ops) for source_step in source_steps]


def _collect_trs_transitions(
    network: AwlNetwork,
    default_source_step: str | None = None,
) -> list[tuple[str, str, str, list[str]]]:
    return _collect_trs_transitions_with_fallback(network, default_source_step=default_source_step)


def _infer_default_trs_source_step(step_map: dict[str, StepCandidate]) -> str | None:
    if "S1" in step_map:
        return "S1"
    step_tokens = [name for name in step_map if STEP_RE.fullmatch(str(name or ""))]
    if not step_tokens:
        return None
    try:
        return sorted(step_tokens, key=lambda item: int(str(item)[1:]))[0]
    except ValueError:
        return sorted(step_tokens)[0]


def _tokenize_condition_logic(network: AwlNetwork) -> list[dict[str, str]]:
    tokens: list[dict[str, str]] = []
    for raw_line in network.raw_lines:
        body = raw_line.split("--", 1)[0].strip()
        if not body:
            continue
        if ":" in body:
            possible_label, remainder = body.split(":", 1)
            if possible_label and " " not in possible_label:
                body = remainder.strip() or "NOP 0"
        if body == ")":
            tokens.append({"kind": "close"})
            continue

        parts = body.split()
        if not parts:
            continue

        opcode = parts[0].upper()
        if opcode.endswith("("):
            base = opcode[:-1]
            connector, negated = _logic_opcode_shape(base)
            if connector is None:
                continue
            tokens.append({"kind": "open", "connector": connector, "negated": "1" if negated else "0"})
            continue

        if opcode in CONDITION_OPCODES:
            if not parts[1:]:
                connector, _ = _logic_opcode_shape(opcode)
                if connector is not None:
                    tokens.append({"kind": "override", "connector": connector})
                continue
            operand = _select_instruction_operand(parts[1:])
            if not operand:
                continue
            connector, negated = _logic_opcode_shape(opcode)
            if connector is None:
                continue
            tokens.append(
                {
                    "kind": "atom",
                    "connector": connector,
                    "negated": "1" if negated else "0",
                    "operand": _canonicalize_step_token(operand),
                }
            )
    return tokens


def _logic_opcode_shape(opcode: str) -> tuple[str | None, bool]:
    base = opcode.upper()
    connector = "AND"
    if base in {"O", "ON"}:
        connector = "OR"
    if base in {"A", "AN", "O", "ON", "U", "UN", "X", "XN"}:
        return connector, base.endswith("N")
    return None, False


def _parse_condition_expression(
    tokens: list[dict[str, str]],
    start_index: int,
) -> tuple[str, list[str], int]:
    expression: str | None = None
    operands: list[str] = []
    pending_override: str | None = None
    index = start_index

    while index < len(tokens):
        token = tokens[index]
        kind = token.get("kind")
        if kind == "close":
            return expression or "", operands, index + 1
        if kind == "override":
            pending_override = token.get("connector")
            index += 1
            continue

        term_expr: str | None = None
        term_ops: list[str] = []
        connector = token.get("connector") or "AND"

        if kind == "atom":
            operand = token.get("operand") or ""
            if not STEP_RE.fullmatch(operand):
                term_ops = [operand]
                if token.get("negated") == "1":
                    term_expr = f"NOT {operand}"
                else:
                    term_expr = operand
            index += 1
        elif kind == "open":
            subexpr, subops, next_index = _parse_condition_expression(tokens, index + 1)
            index = next_index
            if subexpr:
                term_expr = f"({subexpr})"
                if token.get("negated") == "1":
                    term_expr = f"NOT {term_expr}"
            term_ops = subops
        else:
            index += 1
            continue

        if not term_expr:
            operands.extend(term_ops)
            continue

        effective_connector = pending_override or connector
        pending_override = None
        if expression is None:
            expression = term_expr
        else:
            expression = f"({expression} {effective_connector} {term_expr})"
        operands.extend(term_ops)

    return expression or "", operands, index


def _extract_trs_prefix(args: list[str]) -> str | None:
    for raw_arg in args:
        token = _normalize_operand_token(raw_arg)
        match = re.fullmatch(r"([A-Z0-9_]+)\.TRS", token)
        if match:
            return match.group(1)
    return None


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


def _collect_local_targets(network: AwlNetwork) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for instr in network.instructions:
        if instr.opcode not in ACTION_OPCODES or not instr.args:
            continue
        candidate = _select_instruction_operand(instr.args)
        if not candidate:
            continue
        normalized = _normalize_operand_token(candidate)
        if re.fullmatch(r"L\d+(?:\.\d+)?", normalized, flags=re.IGNORECASE):
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

    merged = _merge_split_address_operand(cleaned)
    if merged:
        cleaned = [merged, *cleaned]

    preferred = next((item for item in cleaned if _is_address_like_operand(item)), None)
    selected = preferred or cleaned[0]
    return _canonicalize_step_token(selected)


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


def _merge_split_address_operand(tokens: list[str]) -> str | None:
    if len(tokens) < 2:
        return None
    head, tail = tokens[0], tokens[1]
    if head not in {"A", "E", "I", "M", "Q", "T", "L"}:
        return None
    if not re.fullmatch(r"\d+(?:\.\d+)?", tail):
        return None
    return f"{head}{tail}"


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


def _dedupe_named_members(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    ordered: dict[str, str] = {}
    for name, comment in items:
        if name in ordered:
            continue
        ordered[name] = comment
    return list(ordered.items())


def _canonicalize_step_token(token: str) -> str:
    match = re.fullmatch(r"S0*(\d+)", token, flags=re.IGNORECASE)
    if not match:
        return token
    return f"S{int(match.group(1))}"
    allowed_guard_operands = _strict_allowed_guard_operands(ir)
