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
    companion_db_name: str
    support_fc_name: str | None
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
    companion_db_sections: list[str]
    orchestration_flow: list[str]
    roadmap: ConversionRoadmap
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
