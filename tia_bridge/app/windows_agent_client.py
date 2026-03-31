from __future__ import annotations

import httpx

from app.schemas import JobRequest


class WindowsAgentError(Exception):
    pass


class WindowsAgentClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_health(self) -> dict:
        return await self._request("GET", "/health")

    async def get_status(self) -> dict:
        return await self._request("GET", "/api/status")

    async def get_diagnostics(self) -> dict:
        return await self._request("GET", "/api/openness/diagnostics")

    async def queue_job(self, operation: str, payload: JobRequest) -> dict:
        normalized_payload = payload.model_dump()
        normalized_payload["operation"] = operation
        return await self._request("POST", f"/api/jobs/{operation}", json=normalized_payload)

    async def list_jobs(self) -> dict | list:
        return await self._request("GET", "/api/jobs")

    async def get_job(self, job_id: str) -> dict:
        return await self._request("GET", f"/api/jobs/{job_id}")

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            raise WindowsAgentError(
                f"Windows agent ha risposto con HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise WindowsAgentError(
                f"Impossibile raggiungere il Windows agent su {self.base_url}: {exc}"
            ) from exc
