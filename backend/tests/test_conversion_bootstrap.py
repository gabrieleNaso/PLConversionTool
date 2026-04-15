from fastapi.testclient import TestClient

from app.main import app


def test_conversion_profile_exposes_validated_target() -> None:
    client = TestClient(app)
    res = client.get("/api/conversion/profile")
    assert res.status_code == 200

    payload = res.json()
    assert payload["tia_portal_version"] == "V20"
    assert "SW.Blocks.FB" in payload["supported_artifacts"]
    assert "Cmd" in payload["recommended_db_sections"]


def test_conversion_bootstrap_builds_initial_scaffold() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/bootstrap",
        json={
            "sequenceName": "Bottling Line",
            "sourceName": "bottling_line.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK",
                    "      U     M10.0",
                    "      S     M20.0",
                    "      R     M21.0",
                    "      JC    NEXT",
                    "NEXT: NOP 0",
                ]
            ),
        },
    )
    assert res.status_code == 200

    payload = res.json()
    assert payload["sequence_name"] == "Bottling_Line"
    assert (
        payload["artifact_plan"]["graph_fb_name"] == "FB_Bottling_Line_GRAPH_auto.xml"
    )
    assert (
        payload["artifact_plan"]["global_db_name"]
        == "DB12_Bottling_Line_seq_global_auto.xml"
    )
    assert (
        payload["artifact_plan"]["lad_fc_name"]
        == "FC04_Bottling_Line_transitions_lad_auto.xml"
    )
    assert payload["source_analysis"]["network_count"] == 1
    assert payload["source_analysis"]["set_reset_count"] == 2
    assert payload["source_analysis"]["jump_count"] == 1


def test_conversion_analyze_builds_ir_and_artifact_previews() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Mixer Line",
            "sourceName": "mixer_line.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      U     S1",
                    "      U     M10.0",
                    "      SD    T1",
                    "      U     T1",
                    "      S     S29",
                    "      R     S1",
                    "      JC    NEXT",
                    "NETWORK 2",
                    "      U     S29",
                    "      =     A4.0",
                    "      U     Manual_Mode",
                    "      S     M20.0",
                    "NEXT: NOP 0",
                ]
            ),
        },
    )
    assert res.status_code == 200

    payload = res.json()
    assert payload["ir"]["sequence_name"] == "Mixer_Line"
    assert len(payload["ir"]["steps"]) >= 2
    assert payload["ir"]["transitions"][0]["source_step"] == "S1"
    assert payload["ir"]["transitions"][0]["target_step"] == "S29"
    assert payload["ir"]["timers"][0]["source_timer"] == "T1"
    assert payload["ir"]["manual_logic_networks"] == [2]
    assert len(payload["artifact_manifest"]["baseline"]) == 3
    assert len(payload["artifact_manifest"]["support_io"]) >= 2
    assert len(payload["artifact_manifest"]["support_network"]) >= 2
    assert len(payload["artifact_manifest"]["support_transitions"]) >= 2
    assert len(payload["artifact_manifest"]["support_output"]) >= 2
    assert len(payload["artifact_manifest"]["support_aux"]) >= 2
    assert payload["graph_topology"]["entry_step"] == "S1"
    assert payload["graph_topology"]["step_nodes"][0]["init"] is True
    assert payload["graph_topology"]["connections"][0]["source_ref"] == "S1"
    assert any(
        preview["artifact_type"] == "graph_fb"
        for preview in payload["artifact_previews"]
    )
    assert any(
        "<Connections>" in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )
    assert any(
        '<SW.Blocks.CompileUnit ID="3" CompositionName="CompileUnits">'
        in preview["content"]
        and 'Graph xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"'
        in preview["content"]
        and "<StepRef Number=" in preview["content"]
        and "<TransitionRef Number=" in preview["content"]
        and "<AlarmsSettings>" in preview["content"]
        and 'CompositionName="Title"' in preview["content"]
        and '<Member Name="SNO" Datatype="Int"><StartValue Informative="true">'
        in preview["content"]
        and '<Component Name="DB12_Mixer_Line_SEQ_Global" />' in preview["content"]
        and '<Component Name="T1_Guard_M10_0_AND_T1" />' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )
    assert any(
        '<SW.Blocks.GlobalDB ID="0">' in preview["content"]
        and "<MemoryLayout>Optimized</MemoryLayout>" in preview["content"]
        and '<Member Name="T1_Guard_M10_0_AND_T1" Datatype="Bool">'
        in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "global_db"
    )
    assert any(
        '<SW.Blocks.FC ID="0">' in preview["content"]
        and 'FlgNet xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5"'
        in preview["content"]
        and '<Component Name="DB12_Mixer_Line_SEQ_Global" />' in preview["content"]
        and '<Component Name="T1_Guard_M10_0_AND_T1" />' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "lad_fc"
    )
    assert (
        any(
            issue["code"] == "NO_MANUAL_LOGIC" for issue in payload["validation_issues"]
        )
        is False
    )
    assert (
        any(
            issue["code"] == "PACKAGE_COHERENCE_ERROR"
            for issue in payload["validation_issues"]
        )
        is False
    )
    assert any(
        preview["artifact_type"] == "support_global_db_io"
        and '<SW.Blocks.GlobalDB ID="0">' in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_io"
        and '<SW.Blocks.FC ID="0">' in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_global_db_diag"
        and '<SW.Blocks.GlobalDB ID="0">' in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_diag"
        and '<SW.Blocks.FC ID="0">' in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_global_db_mode"
        and "MODE_MANUAL_ACTIVE" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_mode"
        and '<SW.Blocks.FC ID="0">' in preview["content"]
        and '<Component Name="Mixer_Line_MODE_Global" />' in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_global_db_network"
        and "Network 1 Global" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_network"
        and "_N1_" in preview["content"]
        and "_LAD" in preview["content"]
        for preview in payload["artifact_previews"]
    )


def test_conversion_analyze_builds_alt_branch_for_multi_exit_step() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Branchy Line",
            "sourceName": "branchy.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      U     S1",
                    "      U     M10.0",
                    "      S     S2",
                    "NETWORK 2",
                    "      U     S1",
                    "      U     M11.0",
                    "      S     S3",
                ]
            ),
        },
    )
    assert res.status_code == 200

    payload = res.json()
    assert payload["graph_topology"]["entry_step"] == "S1"
    assert len(payload["graph_topology"]["transition_nodes"]) >= 2
    assert payload["graph_topology"]["branch_nodes"][0]["branch_type"] == "AltBegin"
    assert payload["graph_topology"]["branch_nodes"][0]["branch_no"] == 1
    assert payload["graph_topology"]["connections"][0]["target_ref"] == "B_S1"
    assert any(
        preview["artifact_type"] == "lad_fc" for preview in payload["artifact_previews"]
    )
    assert any(
        '<Branch Number="1" Type="AltBegin"' in preview["content"]
        and '<BranchRef Number="1" In="' in preview["content"]
        and '<BranchRef Number="1" Out="' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )


def test_conversion_analyze_sanitizes_and_dedupes_long_transition_member_names() -> None:
    client = TestClient(app)
    long_guard = (
        "DB106.DBX6.2 AND DB105.DBX23.4 AND DB106.DBX25.1 AND M30.1 "
        "AND DB106.DBX25.3 AND DB162.DBX23.1 AND DB107.DBX6.2 AND DB107.DBX23.3"
    )
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Long Guard Line",
            "sourceName": "long_guard.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      U     S1",
                    "      U     DB106.DBX6.2",
                    "      U     DB105.DBX23.4",
                    "      U     DB106.DBX25.1",
                    "      U     M30.1",
                    "      U     DB106.DBX25.3",
                    "      U     DB162.DBX23.1",
                    "      U     DB107.DBX6.2",
                    "      U     DB107.DBX23.3",
                    "      S     S2",
                    "NETWORK 2",
                    "      U     S1",
                    "      U     DB106.DBX6.2",
                    "      U     DB105.DBX23.4",
                    "      U     DB106.DBX25.1",
                    "      U     M30.1",
                    "      U     DB106.DBX25.3",
                    "      U     DB162.DBX23.1",
                    "      U     DB107.DBX6.2",
                    "      U     DB107.DBX23.3",
                    "      S     S3",
                ]
            ),
        },
    )
    assert res.status_code == 200

    payload = res.json()
    names = [
        node["db_member_name"]
        for node in payload["graph_topology"]["transition_nodes"]
        if node["guard_expression"] == long_guard
    ]
    assert len(names) >= 2
    assert len(set(names)) == len(names)
    assert all(len(name) <= 96 for name in names)
    assert all("_Guard_" in name for name in names)


def test_conversion_analyze_parses_split_timer_operand_as_t_number() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Split Timer",
            "sourceName": "split_timer.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      A     S1",
                    "      L     S5T#10S",
                    "      SD    T 209",
                    "      A     T 209",
                    "      S     S2",
                ]
            ),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    global_db = next(
        preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "global_db"
    )
    assert '<Member Name="T209" Datatype="IEC_TIMER" Version="1.0">' in global_db
    assert '<Member Name="T" Datatype="IEC_TIMER" Version="1.0">' not in global_db
    assert "_Guard_T209" in global_db


def test_conversion_analyze_dedupes_aux_members_by_name() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Aux Dedupe",
            "sourceName": "aux_dedupe.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      U     S1",
                    "      S     M6.0",
                    "NETWORK 2",
                    "      U     S2",
                    "      S     M6.0",
                ]
            ),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    aux_db = next(
        preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "support_global_db_aux"
    )
    assert aux_db.count('<Member Name="AUX_MEM_M6_0" Datatype="Bool">') == 1


def test_conversion_analyze_canonicalizes_step_tokens_with_leading_zeros() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Step Canon",
            "sourceName": "step_canon.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      A     S01",
                    "      S     S2",
                    "NETWORK 2",
                    "      A     S1",
                    "      S     S3",
                ]
            ),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    step_names = {item["name"] for item in payload["ir"]["steps"]}
    assert "S1" in step_names
    assert "S01" not in step_names


def test_conversion_analyze_uses_jump_for_multi_entry_step() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Merge Line",
            "sourceName": "merge.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      U     S1",
                    "      U     M10.0",
                    "      S     S3",
                    "NETWORK 2",
                    "      U     S2",
                    "      U     M11.0",
                    "      S     S3",
                    "NETWORK 3",
                    "      U     S3",
                    "      U     M12.0",
                    "      S     S4",
                ]
            ),
        },
    )
    assert res.status_code == 200

    payload = res.json()
    assert not any(
        branch["branch_type"] == "SimEnd" and branch["owner_step"] == "S3"
        for branch in payload["graph_topology"]["branch_nodes"]
    )
    assert any(
        connection["source_ref"] in {"T1", "T2"}
        and connection["target_ref"] == "S3"
        and connection["link_type"] == "Jump"
        for connection in payload["graph_topology"]["connections"]
    )
    assert any(
        connection["source_ref"] in {"T1", "T2"}
        and connection["target_ref"] == "S3"
        and connection["link_type"] == "Direct"
        for connection in payload["graph_topology"]["connections"]
    )
    assert not any(
        'Type="SimEnd"' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )


def test_conversion_analyze_preserves_or_not_logic_for_trs_transitions() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "TRS Bool",
            "sourceName": "trs_bool.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      A     M06.S14",
                    "      A(",
                    "          O     M06.UP",
                    "          O     DB202.DBX74.1",
                    "      )",
                    "      JNB   _001",
                    "      L     18",
                    "      T     M06.Trs",
                    "_001: NOP 0",
                    "NETWORK 2",
                    "      A(",
                    "          O     M06.S29",
                    "          O     M06.S32",
                    "      )",
                    "      AN    DB106.DBX25.5",
                    "      AN    M47.1",
                    "      JNB   _002",
                    "      L     1",
                    "      T     M06.Trs",
                    "_002: NOP 0",
                ]
            ),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    transitions = payload["ir"]["transitions"]
    assert any(
        item["source_step"] == "S14"
        and item["target_step"] == "S18"
        and " OR " in item["guard_expression"]
        for item in transitions
    )
    s1_transitions = [
        item
        for item in transitions
        if item["target_step"] == "S1" and item["source_step"] in {"S29", "S32"}
    ]
    assert len(s1_transitions) == 2
    assert all(" OR " in item["guard_expression"] for item in s1_transitions)
    assert all("NOT DB106.DBX25.5" in item["guard_expression"] for item in s1_transitions)
    assert all("NOT M47.1" in item["guard_expression"] for item in s1_transitions)


def test_conversion_analyze_detects_q_outputs_as_output_targets() -> None:
    client = TestClient(app)
    res = client.post(
        "/api/conversion/analyze",
        json={
            "sequenceName": "Q Outputs",
            "sourceName": "q_outputs.awl",
            "awlSource": "\n".join(
                [
                    "NETWORK 1",
                    "      A     S29",
                    "      =     Q40.2",
                ]
            ),
        },
    )
    assert res.status_code == 200
    payload = res.json()
    outputs = payload["ir"]["outputs"]
    assert any(item["name"] == "Q40.2" and item["action"] == "=" for item in outputs)
