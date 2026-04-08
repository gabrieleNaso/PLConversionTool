from __future__ import annotations

from pathlib import Path, PureWindowsPath
from uuid import uuid4

from app.schemas import JobRequest
from app.windows_agent_client import WindowsAgentClient


def _iter_xml_files(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.rglob("*.xml") if path.is_file()],
        key=lambda item: str(item).lower(),
    )


async def stage_import_artifact(
    client: WindowsAgentClient,
    request: JobRequest,
    workspace_root: str,
) -> JobRequest:
    if request.operation != "import":
        return request

    source_path = Path(request.artifactPath)
    if not source_path.exists() and not source_path.is_absolute():
        source_path = Path(workspace_root) / request.artifactPath

    if not source_path.exists():
        return request

    remote_status = await client.get_status()
    remote_temp_directory = remote_status.get("tempDirectory")
    if not remote_temp_directory:
        return request

    stage_root = PureWindowsPath(remote_temp_directory) / "bridge_uploads" / uuid4().hex

    if source_path.is_file():
        remote_file = stage_root / source_path.name
        await client.upload_file(remote_file, source_path.read_bytes())
        return request.model_copy(update={"artifactPath": str(remote_file)})

    xml_files = _iter_xml_files(source_path)
    if not xml_files:
        return request

    for xml_file in xml_files:
        relative_path = xml_file.relative_to(source_path)
        remote_file = stage_root / PureWindowsPath(*relative_path.parts)
        await client.upload_file(remote_file, xml_file.read_bytes())

    return request.model_copy(update={"artifactPath": str(stage_root)})
