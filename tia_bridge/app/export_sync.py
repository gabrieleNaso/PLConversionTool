from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from uuid import uuid4

from app.schemas import JobRequest
from app.windows_agent_client import WindowsAgentClient


@dataclass
class ExportSyncContext:
    local_path: str
    remote_path: str
    is_directory: bool
    synced: bool = False


def _resolve_linux_path(artifact_path: str, workspace_root: str) -> Path:
    candidate = Path(artifact_path)
    if candidate.is_absolute():
        return candidate
    return Path(workspace_root) / artifact_path


async def stage_export_target(
    client: WindowsAgentClient,
    request: JobRequest,
    workspace_root: str,
) -> tuple[JobRequest, ExportSyncContext | None]:
    if request.operation != "export":
        return request, None

    remote_status = await client.get_status()
    remote_temp_directory = remote_status.get("tempDirectory") or remote_status.get("TempDirectory")
    if not remote_temp_directory:
        return request, None

    local_target = _resolve_linux_path(request.artifactPath, workspace_root)
    is_directory = local_target.suffix.lower() != ".xml"

    if is_directory:
        local_target.mkdir(parents=True, exist_ok=True)
    else:
        local_target.parent.mkdir(parents=True, exist_ok=True)

    if is_directory:
        remote_target = PureWindowsPath(remote_temp_directory) / "bridge_exports" / uuid4().hex
    else:
        remote_target = (
            PureWindowsPath(remote_temp_directory)
            / "bridge_exports"
            / uuid4().hex
            / local_target.name
        )

    staged_request = request.model_copy(update={"artifactPath": str(remote_target)})
    context = ExportSyncContext(
        local_path=str(local_target),
        remote_path=str(remote_target),
        is_directory=is_directory,
    )
    return staged_request, context


async def sync_exported_artifact(
    client: WindowsAgentClient,
    context: ExportSyncContext,
) -> None:
    local_target = Path(context.local_path)

    if context.is_directory:
        listing = await client.list_files(context.remote_path)
        files = listing.get("Files") or listing.get("files") or []
        local_target.mkdir(parents=True, exist_ok=True)
        for relative_path in files:
            file_payload = await client.read_file(str(PureWindowsPath(context.remote_path) / relative_path))
            await _write_downloaded_file(local_target / _to_linux_relative_path(relative_path), file_payload)
    else:
        local_target.parent.mkdir(parents=True, exist_ok=True)
        file_payload = await client.read_file(context.remote_path)
        await _write_downloaded_file(local_target, file_payload)

    context.synced = True


async def _write_downloaded_file(local_path: Path, file_payload: dict) -> None:
    content_base64 = file_payload.get("ContentBase64") or file_payload.get("contentBase64") or ""
    content = base64.b64decode(content_base64)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(content)


def _to_linux_relative_path(relative_path: str) -> Path:
    return Path(*PureWindowsPath(relative_path).parts)
