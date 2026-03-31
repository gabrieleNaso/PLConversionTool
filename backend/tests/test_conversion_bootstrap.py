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
            "includeFcBlock": True,
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
    assert payload["artifact_plan"]["support_fc_name"] == "FC_Bottling_Line_support_auto.xml"
    assert payload["source_analysis"]["network_count"] == 1
    assert payload["source_analysis"]["set_reset_count"] == 2
    assert payload["source_analysis"]["jump_count"] == 1
