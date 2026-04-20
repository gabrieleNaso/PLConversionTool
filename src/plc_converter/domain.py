from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TargetProfile:
    tia_portal_version: str
    graph_version: str
    graph_runtime_type: str
    transition_runtime_type: str
    step_runtime_type: str
    supported_artifacts: list[str]
    required_graph_sections: list[str]
    recommended_db_sections: list[str]
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class SourceAnalysis:
    source_kind: str
    source_name: str
    network_count: int
    set_reset_count: int
    jump_count: int
    timer_hint_count: int
    manual_mode_hint: bool
    alarm_hint: bool
    lines: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ArtifactPlan:
    graph_fb_name: str
    global_db_name: str
    lad_fc_name: str
    output_directory: str
    naming_notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ConversionRoadmap:
    phases: list[str]
    immediate_next_actions: list[str]
    open_points: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ConversionScaffold:
    sequence_name: str
    target_profile: TargetProfile
    source_analysis: SourceAnalysis
    artifact_plan: ArtifactPlan
    graph_static_contract: list[str]
    global_db_sections: list[str]
    orchestration_flow: list[str]
    roadmap: ConversionRoadmap
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class AwlInstruction:
    line_no: int
    network_index: int
    label: str | None
    opcode: str
    args: list[str]
    raw: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class AwlNetwork:
    index: int
    title: str | None
    raw_lines: list[str]
    instructions: list[AwlInstruction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class StepCandidate:
    name: str
    step_number: int | None = None
    source_networks: list[int] = field(default_factory=list)
    activation_networks: list[int] = field(default_factory=list)
    action_networks: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class TransitionCandidate:
    transition_id: str
    source_step: str
    target_step: str
    network_index: int
    guard_expression: str
    guard_operands: list[str] = field(default_factory=list)
    jump_labels: list[str] = field(default_factory=list)
    flow_type: str = "alternative"
    parallel_group: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class TimerCandidate:
    source_timer: str
    network_index: int
    kind: str
    preset: str | None = None
    trigger_operands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class MemoryCandidate:
    name: str
    role: str
    network_index: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class FaultCandidate:
    name: str
    network_index: int
    evidence: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class OutputCandidate:
    name: str
    network_index: int
    action: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class AwlIR:
    sequence_name: str
    source_name: str
    networks: list[AwlNetwork]
    steps: list[StepCandidate]
    transitions: list[TransitionCandidate]
    timers: list[TimerCandidate]
    memories: list[MemoryCandidate]
    faults: list[FaultCandidate]
    outputs: list[OutputCandidate]
    manual_logic_networks: list[int] = field(default_factory=list)
    auto_logic_networks: list[int] = field(default_factory=list)
    external_refs: list[str] = field(default_factory=list)
    strict_operand_catalog: bool = False
    operand_catalog: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ValidationIssue:
    level: str
    code: str
    message: str
    context: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ArtifactPreview:
    artifact_type: str
    file_name: str
    content: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class MemberIR:
    name: str
    datatype: str
    version: str | None = None
    remanence: str | None = None
    attributes: list[tuple[str, str]] = field(default_factory=list)
    comment: str | None = None
    start_value: str | None = None
    children: list["MemberIR"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class GraphStepNode:
    name: str
    step_no: int
    init: bool
    source_step: str
    action_networks: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class GraphTransitionNode:
    name: str
    transition_no: int
    source_step: str
    target_step: str
    guard_expression: str
    network_index: int
    db_block_name: str
    db_member_name: str
    guard_operands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class GraphBranchNode:
    name: str
    branch_no: int
    branch_type: str
    owner_step: str
    incoming_refs: list[str] = field(default_factory=list)
    outgoing_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class GraphConnection:
    source_ref: str
    target_ref: str
    link_type: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class GraphTopology:
    step_nodes: list[GraphStepNode]
    transition_nodes: list[GraphTransitionNode]
    branch_nodes: list[GraphBranchNode]
    connections: list[GraphConnection]
    entry_step: str | None
    terminal_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ConversionAnalysis:
    scaffold: ConversionScaffold
    ir: AwlIR
    graph_topology: GraphTopology
    validation_issues: list[ValidationIssue]
    artifact_previews: list[ArtifactPreview]
    artifact_manifest: dict[str, list[dict[str, str]]]

    def to_dict(self) -> dict:
        return asdict(self)
