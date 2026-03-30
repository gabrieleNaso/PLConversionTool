from fastapi import FastAPI

from app.project_context import build_project_summary


app = FastAPI(
    title="PLConversionTool Backend",
    version="0.1.0",
    description="API di supporto al progetto di conversione PLC AWL -> GRAPH XML.",
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
