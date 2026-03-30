from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "service": "backend",
        "project": "PLConversionTool",
    }


def test_project_summary() -> None:
    client = TestClient(app)
    res = client.get("/api/project-summary")
    assert res.status_code == 200

    payload = res.json()
    assert payload["project"] == "PLConversionTool"
    assert "targets" in payload
    assert "repositoryAreas" in payload
