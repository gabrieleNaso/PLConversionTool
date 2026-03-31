from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel


SUPPORTED_OPERATIONS = ("import", "compile", "export")


class JobRequest(BaseModel):
    operation: str = ""
    artifactPath: str
    projectPath: str | None = None
    notes: str | None = None


class JobResponse(BaseModel):
    jobId: str
    status: str
    operation: str
    artifactPath: str
    projectPath: str | None = None
    notes: str | None = None
    detail: str | None = None


class TiaJob(BaseModel):
    jobId: str
    operation: str
    artifactPath: str
    projectPath: str | None = None
    notes: str | None = None
    status: str
    detail: str | None = None
    createdAtUtc: datetime
    updatedAtUtc: datetime


class RemoteTarget(BaseModel):
    vmwareNetworkMode: str
    transport: str
    host: str | None = None
    port: str
    agentUrl: str | None = None


class BridgeHealth(BaseModel):
    status: str
    service: str
    project: str
    mode: str
    remoteTargetConfigured: bool
    remoteAgentUrl: str | None = None
    remoteHost: str | None = None
    remotePort: str | None = None
    remoteReachable: bool | None = None


class BridgeStatus(BaseModel):
    service: str
    role: str
    mode: str
    supportedOperations: list[str]
    responsibilities: list[str]
    runtimeNotes: list[str]
    remoteTarget: RemoteTarget
    watchedPaths: dict[str, str]
    remoteAgentStatus: dict | None = None


class DiagnosticsResponse(BaseModel):
    service: str
    mode: str
    tiaPortalVersion: str
    siemensAssemblyDirectory: str
    siemensAssemblyDirectoryExists: bool
    siemensEngineeringAssemblyPath: str
    siemensEngineeringAssemblyExists: bool
    defaultProjectPath: str | None = None
    defaultProjectPathExists: bool
    launchUi: bool
    notes: list[str]


class StubJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, TiaJob] = {}

    def create_job(self, request: JobRequest, operation: str) -> JobResponse:
        now = datetime.now(timezone.utc)
        job_id = f"stub-{uuid4().hex}"
        job = TiaJob(
            jobId=job_id,
            operation=operation,
            artifactPath=request.artifactPath,
            projectPath=request.projectPath,
            notes=request.notes,
            status="completed",
            detail="Job completato in modalita' stub dal tia-bridge.",
            createdAtUtc=now,
            updatedAtUtc=now,
        )
        self._jobs[job_id] = job

        return JobResponse(
            jobId=job.jobId,
            status=job.status,
            operation=job.operation,
            artifactPath=job.artifactPath,
            projectPath=job.projectPath,
            notes=job.notes,
            detail=job.detail,
        )

    def list_jobs(self) -> list[TiaJob]:
        return sorted(
            self._jobs.values(),
            key=lambda item: item.createdAtUtc,
            reverse=True,
        )

    def get_job(self, job_id: str) -> TiaJob | None:
        return self._jobs.get(job_id)


def build_stub_diagnostics() -> DiagnosticsResponse:
    return DiagnosticsResponse(
        service="tia-windows-agent",
        mode="stub",
        tiaPortalVersion="V20",
        siemensAssemblyDirectory="C:\\Program Files\\Siemens\\Automation\\Portal V20\\PublicAPI\\V20",
        siemensAssemblyDirectoryExists=False,
        siemensEngineeringAssemblyPath=(
            "C:\\Program Files\\Siemens\\Automation\\Portal V20\\PublicAPI\\V20\\Siemens.Engineering.dll"
        ),
        siemensEngineeringAssemblyExists=False,
        defaultProjectPath=None,
        defaultProjectPathExists=False,
        launchUi=False,
        notes=[
            "Il tia-bridge e' in modalita' stub: nessuna chiamata remota verso la VM Windows.",
            "Configura TIA_WINDOWS_AGENT_URL e TIA_BRIDGE_MODE=real per attivare il boundary reale.",
        ],
    )
