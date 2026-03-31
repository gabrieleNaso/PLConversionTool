from fastapi import FastAPI, HTTPException

from app.config import get_bridge_mode, get_remote_target, get_runtime_paths, get_windows_agent_url
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
        remoteReachable=await probe_remote_health(),
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
        return await get_windows_agent_client().queue_job(operation, normalized_request)
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/jobs")
async def list_jobs() -> dict | list:
    if get_bridge_mode() != "real":
        return [job.model_dump() for job in stub_jobs.list_jobs()]

    try:
        return await get_windows_agent_client().list_jobs()
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
        return await get_windows_agent_client().get_job(job_id)
    except (HTTPException, WindowsAgentError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
