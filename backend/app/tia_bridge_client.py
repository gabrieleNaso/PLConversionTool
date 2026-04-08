from __future__ import annotations

import os

import httpx


class TiaBridgeClientError(Exception):
    pass


class TiaBridgeClient:
    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = (
            base_url
            or os.getenv("TIA_BRIDGE_INTERNAL_URL", "http://tia-bridge:8010").strip()
            or "http://tia-bridge:8010"
        ).rstrip("/")
        self.timeout = timeout

    async def get_health(self) -> dict:
        return await self._request("GET", "/health")

    async def get_status(self) -> dict:
        return await self._request("GET", "/api/status")

    async def get_diagnostics(self) -> dict:
        return await self._request("GET", "/api/openness/diagnostics")

    async def list_jobs(self) -> dict | list:
        return await self._request("GET", "/api/jobs")

    async def get_job(self, job_id: str) -> dict:
        return await self._request("GET", f"/api/jobs/{job_id}")

    async def queue_job(self, operation: str, payload: dict) -> dict:
        normalized_payload = {
            "operation": operation,
            "artifactPath": payload.get("artifactPath", ""),
            "projectPath": payload.get("projectPath"),
            "targetPath": payload.get("targetPath"),
            "targetName": payload.get("targetName"),
            "saveProject": bool(payload.get("saveProject", False)),
            "notes": payload.get("notes"),
        }
        return await self._request("POST", f"/api/jobs/{operation}", json=normalized_payload)

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip() or exc.response.reason_phrase
            raise TiaBridgeClientError(
                f"TIA bridge ha risposto con HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise TiaBridgeClientError(
                f"Impossibile raggiungere il TIA bridge su {self.base_url}: {exc}"
            ) from exc
