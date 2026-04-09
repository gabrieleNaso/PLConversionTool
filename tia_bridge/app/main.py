from fastapi import FastAPI, HTTPException

from app.artifact_stager import stage_import_artifact
from app.config import get_bridge_mode, get_remote_target, get_runtime_paths, get_windows_agent_url
from app.export_sync import ExportSyncContext, stage_export_target, sync_exported_artifact
from app.schemas import (
    SUPPORTED_OPERATIONS,
    BridgeHealth,
    BridgeStatus,
    JobRequest,
    RemoteTarget,
    StubJobStore,
    build_stub_diagnostics,
)
from app.windows_agent_client import WindowsAgentClient, WindowsAgentError


app = FastAPI(
    title="PLConversionTool TIA Bridge",
    version="0.1.0",
    description=(
        "Adapter di orchestrazione verso TIA Portal Openness separato dal backend "
        "di generazione XML."
    ),
)

stub_jobs = StubJobStore()
export_sync_jobs: dict[str, ExportSyncContext] = {}


def get_windows_agent_client() -> WindowsAgentClient:
    base_url = get_windows_agent_url()
    if not base_url:
        raise HTTPException(
            status_code=503,
            detail="Windows agent non configurato. Imposta TIA_WINDOWS_AGENT_URL o host/porta.",
        )
    return WindowsAgentClient(base_url=base_url)


async def probe_remote_health() -> bool | None:
    if get_bridge_mode() != "real":
        return None

    try:
        client = get_windows_agent_client()
        await client.get_health()
        return True
    except (HTTPException, WindowsAgentError):
        return False


@app.get("/health")
async def health() -> BridgeHealth:
    remote_target = get_remote_target()
    return BridgeHealth(
        status="ok",
        service="tia-bridge",
        project="PLConversionTool",
        mode=get_bridge_mode(),
        remoteTargetConfigured=bool(remote_target["agentUrl"] or remote_target["host"]),
        remoteAgentUrl=remote_target["agentUrl"],
        remoteHost=remote_target["host"],
        remotePort=remote_target["port"],
        remoteReachable=None,
    )


@app.get("/")
def root() -> dict:
    return {
        "message": "PLConversionTool TIA bridge online",
        "docs": "/docs",
        "health": "/health",
        "status": "/api/status",
    }

@app.get("/api/status")
async def status() -> BridgeStatus:
    remote_status = None
    if get_bridge_mode() == "real":
        try:
            remote_status = await get_windows_agent_client().get_status()
        except (HTTPException, WindowsAgentError) as exc:
            remote_status = {"status": "unreachable", "detail": str(exc)}

    return BridgeStatus(
        service="tia-bridge",
        role=(
            "Boundary service per import, compile, export e confronto verso un "
            "ambiente TIA Portal/Openness remoto."
        ),
        mode=get_bridge_mode(),
        supportedOperations=list(SUPPORTED_OPERATIONS),
        responsibilities=[
            "ricevere artefatti XML dal backend applicativo",
            "preparare job di import/export verso il layer TIA sulla VM Windows",
            "mantenere separata l'orchestrazione Openness dalla logica di generazione",
        ],
        runtimeNotes=[
            "TIA Portal Openness richiede un ambiente Windows con installazione TIA compatibile.",
            "Il container Linux non parla con le DLL Openness in modo nativo: serve un agent sul lato Windows.",
        ],
        remoteTarget=RemoteTarget(**get_remote_target()),
        watchedPaths=get_runtime_paths(),
        remoteAgentStatus=remote_status,
    )


@app.get("/api/openness/diagnostics")
async def openness_diagnostics() -> dict:
    if get_bridge_mode() != "real":
        return build_stub_diagnostics().model_dump()

    try:
        return await get_windows_agent_client().get_diagnostics()
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/jobs/{operation}", status_code=202)
async def queue_job(operation: str, request: JobRequest) -> dict:
    if operation not in SUPPORTED_OPERATIONS:
        raise HTTPException(status_code=404, detail=f"Operazione non supportata: {operation}")

    normalized_request = request.model_copy(update={"operation": operation})
    if get_bridge_mode() != "real":
        return stub_jobs.create_job(normalized_request, operation).model_dump()

    try:
        client = get_windows_agent_client()
        staged_request = await stage_import_artifact(
            client,
            normalized_request,
            get_runtime_paths()["workspace"],
        )
        staged_request, export_context = await stage_export_target(
            client,
            staged_request,
            get_runtime_paths()["workspace"],
        )
        response = await client.queue_job(operation, staged_request)
        response_job_id = response.get("jobId") or response.get("JobId")
        if export_context is not None and response_job_id:
            export_sync_jobs[response_job_id] = export_context
            if "artifactPath" in response:
                response["artifactPath"] = export_context.local_path
            if "ArtifactPath" in response:
                response["ArtifactPath"] = export_context.local_path
        return response
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/jobs")
async def list_jobs() -> dict | list:
    if get_bridge_mode() != "real":
        return [job.model_dump() for job in stub_jobs.list_jobs()]

    try:
        client = get_windows_agent_client()
        jobs = await client.list_jobs()
        if isinstance(jobs, list):
            return [await _maybe_sync_export_job(client, job) for job in jobs]
        return jobs
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    if get_bridge_mode() != "real":
        job = stub_jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job non trovato.")
        return job.model_dump()

    try:
        client = get_windows_agent_client()
        job = await client.get_job(job_id)
        return await _maybe_sync_export_job(client, job)
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _maybe_sync_export_job(client: WindowsAgentClient, job: dict) -> dict:
    job_id = job.get("JobId") or job.get("jobId")
    if not job_id or job_id not in export_sync_jobs:
        return job

    context = export_sync_jobs[job_id]
    status = (job.get("Status") or job.get("status") or "").lower()
    if status == "completed" and not context.synced:
        await sync_exported_artifact(client, context)

    job["ArtifactPath"] = context.local_path
    detail = job.get("Detail") or job.get("detail") or ""
    if context.synced and "Ubuntu sync" not in detail:
        detail = f"{detail} Ubuntu sync completato verso '{context.local_path}'.".strip()
    if "Detail" in job:
        job["Detail"] = detail
    else:
        job["detail"] = detail
    return job
