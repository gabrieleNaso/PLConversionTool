import os


def get_bridge_mode() -> str:
    return os.getenv("TIA_BRIDGE_MODE", "stub").strip().lower() or "stub"


def get_windows_agent_url() -> str | None:
    explicit_url = os.getenv("TIA_WINDOWS_AGENT_URL", "").strip()
    if explicit_url:
        return explicit_url.rstrip("/")

    host = os.getenv("TIA_WINDOWS_HOST", "").strip()
    if not host:
        return None

    transport = os.getenv("TIA_WINDOWS_TRANSPORT", "http").strip() or "http"
    port = os.getenv("TIA_WINDOWS_AGENT_PORT", "8050").strip() or "8050"
    return f"{transport}://{host}:{port}"


def get_runtime_paths() -> dict[str, str]:
    return {
        "workspace": os.getenv("TIA_PROJECT_ROOT", "/workspace").strip() or "/workspace",
        "output": os.getenv("TIA_OUTPUT_DIR", "/workspace/data/output").strip() or "/workspace/data/output",
        "tmp": os.getenv("TIA_TMP_DIR", "/workspace/data/tmp").strip() or "/workspace/data/tmp",
    }


def get_remote_target() -> dict[str, str | None]:
    return {
        "vmwareNetworkMode": os.getenv("TIA_VMWARE_NETWORK_MODE", "bridged").strip() or "bridged",
        "transport": os.getenv("TIA_WINDOWS_TRANSPORT", "http").strip() or "http",
        "host": os.getenv("TIA_WINDOWS_HOST", "").strip() or None,
        "port": os.getenv("TIA_WINDOWS_AGENT_PORT", "8050").strip() or "8050",
        "agentUrl": get_windows_agent_url(),
    }
