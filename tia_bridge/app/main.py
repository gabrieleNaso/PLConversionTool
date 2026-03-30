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
    return {
        "status": "ok",
        "service": "tia-bridge",
        "project": "PLConversionTool",
        "mode": "stub",
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
    return {
        "service": "tia-bridge",
        "role": (
            "Boundary service per import, compile, export e confronto verso un "
            "ambiente TIA Portal/Openness."
        ),
        "responsibilities": [
            "ricevere artefatti XML dal backend applicativo",
            "preparare job di import/export verso il layer TIA",
            "mantenere separata l'orchestrazione Openness dalla logica di generazione",
        ],
        "runtimeNotes": [
            "TIA Portal Openness richiede un ambiente Windows con installazione TIA compatibile.",
            "Nel container dev Linux il servizio resta un adapter pronto da collegare al target reale.",
        ],
        "watchedPaths": {
            "workspace": "/workspace",
            "output": "/workspace/output",
            "tmp": "/workspace/tmp",
        },
    }
