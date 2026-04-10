from fastapi import FastAPI, HTTPException

from app.core_converter import (
    analyze_conversion,
    bootstrap_conversion,
    export_conversion_bundle,
    get_target_profile,
)
from app.project_context import build_project_summary
from app.tia_bridge_client import TiaBridgeClient, TiaBridgeClientError


app = FastAPI(
    title="PLConversionTool Backend",
    version="0.1.0",
    description="API per la conversione PLC AWL -> pacchetto XML GRAPH + GlobalDB + FC LAD.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "backend", "project": "PLConversionTool"}


@app.get("/")
def root() -> dict:
    return {
        "message": "PLConversionTool backend online",
        "docs": "/docs",
        "health": "/health",
        "project_summary": "/api/project-summary",
    }


@app.get("/api/project-summary")
def project_summary() -> dict:
    return build_project_summary()


@app.get("/api/conversion/profile")
def conversion_profile() -> dict:
    return get_target_profile()


@app.post("/api/conversion/bootstrap")
def conversion_bootstrap(payload: dict) -> dict:
    awl_source = (payload.get("awlSource") or "").strip()
    if not awl_source:
        raise HTTPException(status_code=400, detail="awlSource e' obbligatorio.")

    return bootstrap_conversion(
        sequence_name=payload.get("sequenceName"),
        awl_source=awl_source,
        source_name=payload.get("sourceName"),
    )


@app.post("/api/conversion/analyze")
def conversion_analyze(payload: dict) -> dict:
    awl_source = (payload.get("awlSource") or "").strip()
    if not awl_source:
        raise HTTPException(status_code=400, detail="awlSource e' obbligatorio.")

    return analyze_conversion(
        sequence_name=payload.get("sequenceName"),
        awl_source=awl_source,
        source_name=payload.get("sourceName"),
    )


@app.post("/api/conversion/export")
def conversion_export(payload: dict) -> dict:
    awl_source = (payload.get("awlSource") or "").strip()
    if not awl_source:
        raise HTTPException(status_code=400, detail="awlSource e' obbligatorio.")

    try:
        return export_conversion_bundle(
            sequence_name=payload.get("sequenceName"),
            awl_source=awl_source,
            source_name=payload.get("sourceName"),
            output_dir=payload.get("outputDir", "output/generated"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/tia/overview")
async def tia_overview() -> dict:
    client = TiaBridgeClient()
    overview = {
        "service": "backend",
        "bridgeConfiguredUrl": client.base_url,
        "bridgeHealth": {"status": "unreachable", "service": "tia-bridge"},
        "bridgeStatus": {
            "service": "tia-bridge",
            "mode": "unknown",
            "supportedOperations": [],
        },
    }

    try:
        overview["bridgeHealth"] = await client.get_health()
        overview["bridgeStatus"] = await client.get_status()
    except TiaBridgeClientError as exc:
        overview["bridgeStatus"] = {
            "service": "tia-bridge",
            "mode": "unreachable",
            "supportedOperations": [],
            "detail": str(exc),
        }

    return overview


@app.get("/api/tia/openness/diagnostics")
async def tia_openness_diagnostics() -> dict:
    try:
        return await TiaBridgeClient().get_diagnostics()
    except TiaBridgeClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/tia/jobs")
async def tia_jobs() -> dict | list:
    try:
        return await TiaBridgeClient().list_jobs()
    except TiaBridgeClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/tia/jobs/{job_id}")
async def tia_job(job_id: str) -> dict:
    try:
        return await TiaBridgeClient().get_job(job_id)
    except TiaBridgeClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/tia/jobs/{operation}", status_code=202)
async def queue_tia_job(operation: str, payload: dict) -> dict:
    if operation not in {"import", "compile", "export"}:
        raise HTTPException(status_code=404, detail=f"Operazione non supportata: {operation}")

    if not payload.get("artifactPath"):
        raise HTTPException(status_code=400, detail="artifactPath e' obbligatorio.")

    try:
        return await TiaBridgeClient().queue_job(operation, payload)
    except TiaBridgeClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
