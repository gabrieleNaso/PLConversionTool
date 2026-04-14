from __future__ import annotations

import re

from .domain import (
    ArtifactPlan,
    ConversionRoadmap,
    ConversionScaffold,
    SourceAnalysis,
    TargetProfile,
)


def build_target_profile() -> TargetProfile:
    return TargetProfile(
        tia_portal_version="V20",
        graph_version="GRAPH V2",
        graph_runtime_type="G7_RTDataPlus_V2",
        transition_runtime_type="G7_TransitionPlus_V2",
        step_runtime_type="G7_StepPlus_V2",
        supported_artifacts=[
            "SW.Blocks.FB",
            "SW.Blocks.GlobalDB",
            "SW.Blocks.FC",
        ],
        required_graph_sections=[
            "Interface",
            "Static",
            "Steps",
            "Transitions",
            "Branches",
            "Connections",
            "FlgNet LAD per transition",
        ],
        recommended_db_sections=["Cmd", "Fb", "Par", "En", "Diag", "Hmi", "Map"],
        notes=[
            "Il GRAPH deve mantenere gli statici runtime interni obbligatori.",
            "Il GlobalDB del pacchetto va generato in aggiunta, non in sostituzione degli statici GRAPH.",
            "La conversione include il trio baseline (FB GRAPH + GlobalDB + FC LAD) e puo' aggiungere DB/FC di supporto quando l'AWL richiede separazione funzionale.",
        ],
    )


def build_conversion_scaffold(
    sequence_name: str | None,
    awl_source: str,
    source_name: str | None = None,
) -> ConversionScaffold:
    normalized_name = _normalize_sequence_name(sequence_name or source_name or "Sequence")
    source_analysis = _analyze_awl_source(awl_source, source_name or f"{normalized_name}.awl")
    target_profile = build_target_profile()

    artifact_plan = ArtifactPlan(
        graph_fb_name=f"FB_{normalized_name}_GRAPH_auto.xml",
        global_db_name=f"DB12_{normalized_name}_seq_global_auto.xml",
        lad_fc_name=f"FC04_{normalized_name}_transitions_lad_auto.xml",
        output_directory="data/output/",
        naming_notes=[
            "Il naming resta deterministico e allineato alle convenzioni di repository.",
            "Usare suffissi semanticamente utili solo quando distinguono una variante reale.",
        ],
    )

    roadmap = ConversionRoadmap(
        phases=[
            "analisi AWL e identificazione stati impliciti",
            "costruzione del modello intermedio della macchina a stati",
            "mappatura verso steps, transitions, branches e connections GRAPH",
            "generazione XML di FB GRAPH, GlobalDB e FC LAD del pacchetto",
            "validazione via tia-bridge e Windows agent",
        ],
        immediate_next_actions=[
            "formalizzare il parser AWL nel core src/",
            "definire il modello intermedio StateMachine con step e transizioni esplicite",
            "aggiungere serializer XML separati per FB GRAPH, GlobalDB e FC LAD",
        ],
        open_points=[
            "criteri deterministici per riconoscere branch paralleli o alternativi da AWL",
            "mappatura sistematica timer/interblocchi/consensi nel modello intermedio",
            "regole di naming simbolico per variabili e mapping AWL -> GRAPH",
        ],
    )

    assumptions = [
        "L'input AWL puo' contenere una logica sequenziale distribuita su set/reset, jump e timer.",
        "L'output finale deve sempre privilegiare importabilita' TIA e struttura esplicita del GRAPH.",
        "Ogni conversione produce sempre il pacchetto baseline FB GRAPH + GlobalDB + FC LAD, con eventuali blocchi FC/DB aggiuntivi derivati dall'IR.",
    ]

    return ConversionScaffold(
        sequence_name=normalized_name,
        target_profile=target_profile,
        source_analysis=source_analysis,
        artifact_plan=artifact_plan,
        graph_static_contract=[
            "RT_DATA : G7_RTDataPlus_V2",
            "un member G7_TransitionPlus_V2 per ogni transition",
            "un member G7_StepPlus_V2 per ogni step",
        ],
        global_db_sections=target_profile.recommended_db_sections,
        orchestration_flow=[
            "backend genera o aggiorna il bundle XML",
            "tia-bridge orchestra import/compile/export",
            "tia_windows_agent esegue Openness nella VM Windows",
        ],
        roadmap=roadmap,
        assumptions=assumptions,
    )


def _analyze_awl_source(awl_source: str, source_name: str) -> SourceAnalysis:
    stripped_source = awl_source.strip()
    lines = [line for line in stripped_source.splitlines() if line.strip()]

    return SourceAnalysis(
        source_kind="awl",
        source_name=source_name,
        network_count=_count_matches(lines, r"^\s*NETWORK\b"),
        set_reset_count=_count_matches(lines, r"^\s*[SR]\s"),
        jump_count=_count_matches(lines, r"^\s*J(CN?|U)\b"),
        timer_hint_count=_count_matches(lines, r"\bT\d+\b"),
        manual_mode_hint=bool(re.search(r"\b(man|manual)\b", stripped_source, re.IGNORECASE)),
        alarm_hint=bool(re.search(r"\b(alarm|fault|error)\b", stripped_source, re.IGNORECASE)),
        lines=len(lines),
    )


def _count_matches(lines: list[str], pattern: str) -> int:
    regex = re.compile(pattern, re.IGNORECASE)
    return sum(1 for line in lines if regex.search(line))


def _normalize_sequence_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return cleaned or "Sequence"
