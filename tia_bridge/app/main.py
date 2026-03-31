import os

from fastapi import FastAPI


app = FastAPI(
    title="PLConversionTool TIA Bridge",
    version="0.1.0",
    description=(
        "Adapter di orchestrazione verso TIA Portal Openness separato dal backend "
        "di generazione XML."
    ),
)


@app.get("/health")
def health() -> dict:
    remote_agent_url = os.getenv("TIA_WINDOWS_AGENT_URL", "").strip()
    remote_host = os.getenv("TIA_WINDOWS_HOST", "").strip()
    remote_port = os.getenv("TIA_WINDOWS_AGENT_PORT", "").strip()

    return {
        "status": "ok",
        "service": "tia-bridge",
        "project": "PLConversionTool",
        "mode": os.getenv("TIA_BRIDGE_MODE", "stub"),
        "remoteTargetConfigured": bool(remote_agent_url or remote_host),
        "remoteAgentUrl": remote_agent_url or None,
        "remoteHost": remote_host or None,
        "remotePort": remote_port or None,
    }


@app.get("/")
def root() -> dict:
    return {
        "message": "PLConversionTool TIA bridge online",
        "docs": "/docs",
        "health": "/health",
        "status": "/api/status",
    }


@app.get("/api/status")
def status() -> dict:
    remote_agent_url = os.getenv("TIA_WINDOWS_AGENT_URL", "").strip()
    remote_host = os.getenv("TIA_WINDOWS_HOST", "").strip()
    remote_port = os.getenv("TIA_WINDOWS_AGENT_PORT", "8050").strip()
    remote_transport = os.getenv("TIA_WINDOWS_TRANSPORT", "http").strip()
    vmware_network = os.getenv("TIA_VMWARE_NETWORK_MODE", "bridged").strip()

    return {
        "service": "tia-bridge",
        "role": (
            "Boundary service per import, compile, export e confronto verso un "
            "ambiente TIA Portal/Openness remoto."
        ),
        "responsibilities": [
            "ricevere artefatti XML dal backend applicativo",
            "preparare job di import/export verso il layer TIA sulla VM Windows",
            "mantenere separata l'orchestrazione Openness dalla logica di generazione",
        ],
        "runtimeNotes": [
            "TIA Portal Openness richiede un ambiente Windows con installazione TIA compatibile.",
            "Il container Linux non parla con le DLL Openness in modo nativo: serve un agent sul lato Windows.",
        ],
        "remoteTarget": {
            "vmwareNetworkMode": vmware_network,
            "transport": remote_transport,
            "agentUrl": remote_agent_url or None,
            "host": remote_host or None,
            "port": remote_port,
        },
        "watchedPaths": {
            "workspace": "/workspace",
            "output": "/workspace/output",
            "tmp": "/workspace/tmp",
        },
    }
