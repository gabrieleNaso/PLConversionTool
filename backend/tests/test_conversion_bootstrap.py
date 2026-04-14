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
    assert payload["artifact_plan"]["graph_fb_name"] == "FB_Bottling_Line_GRAPH_auto.xml"
    assert payload["artifact_plan"]["global_db_name"] == "DB_Bottling_Line_global_auto.xml"
    assert payload["artifact_plan"]["lad_fc_name"] == "FC_Bottling_Line_lad_auto.xml"
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
        preview["artifact_type"] == "graph_fb" for preview in payload["artifact_previews"]
    )
    assert any(
        "<Connections>" in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )
    assert any(
        '<SW.Blocks.CompileUnit ID="3" CompositionName="CompileUnits">' in preview["content"]
        and 'Graph xmlns="http://www.siemens.com/automation/Openness/SW/NetworkSource/Graph/v5"'
        in preview["content"]
        and "<StepRef Number=" in preview["content"]
        and "<TransitionRef Number=" in preview["content"]
        and "<AlarmsSettings>" in preview["content"]
        and 'CompositionName="Title"' in preview["content"]
        and '<Member Name="SNO" Datatype="Int"><StartValue Informative="true">' in preview["content"]
        and '<Component Name="Mixer_Line_Global" />' in preview["content"]
        and '<Component Name="T1_Guard_M10_0_AND_T1" />' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "graph_fb"
    )
    assert any(
        "<SW.Blocks.GlobalDB ID=\"0\">" in preview["content"]
        and "<MemoryLayout>Optimized</MemoryLayout>" in preview["content"]
        and '<Member Name="T1_Guard_M10_0_AND_T1" Datatype="Bool">' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "global_db"
    )
    assert any(
        "<SW.Blocks.FC ID=\"0\">" in preview["content"]
        and "FlgNet xmlns=\"http://www.siemens.com/automation/Openness/SW/NetworkSource/FlgNet/v5\""
        in preview["content"]
        and '<Component Name="Mixer_Line_Global" />' in preview["content"]
        and '<Component Name="T1_Guard_M10_0_AND_T1" />' in preview["content"]
        for preview in payload["artifact_previews"]
        if preview["artifact_type"] == "lad_fc"
    )
    assert any(
        issue["code"] == "NO_MANUAL_LOGIC" for issue in payload["validation_issues"]
    ) is False
    assert any(
        issue["code"] == "PACKAGE_COHERENCE_ERROR" for issue in payload["validation_issues"]
    ) is False
    assert any(
        preview["artifact_type"] == "support_global_db_io"
        and "<SW.Blocks.GlobalDB ID=\"0\">" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_io"
        and "<SW.Blocks.FC ID=\"0\">" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_global_db_diag"
        and "<SW.Blocks.GlobalDB ID=\"0\">" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_diag"
        and "<SW.Blocks.FC ID=\"0\">" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_global_db_mode"
        and "MODE_MANUAL_ACTIVE" in preview["content"]
        for preview in payload["artifact_previews"]
    )
    assert any(
        preview["artifact_type"] == "support_lad_fc_mode"
        and "<SW.Blocks.FC ID=\"0\">" in preview["content"]
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
