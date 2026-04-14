#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _http_json(method: str, url: str, payload: dict | None = None, timeout: float = 30.0) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}: {body}") from exc


def _list_bundle_dirs(output_root: Path, prefix: str | None) -> list[Path]:
    if not output_root.exists():
        return []
    candidates = [p for p in output_root.iterdir() if p.is_dir()]
    if prefix:
        candidates = [p for p in candidates if p.name.lower().startswith(prefix.lower())]
    return sorted(candidates, key=lambda p: p.name.lower())


def _poll_job(base_url: str, job_id: str, timeout_s: int) -> dict:
    deadline = time.time() + timeout_s
    last = {}
    while time.time() < deadline:
        last = _http_json("GET", f"{base_url}/api/tia/jobs/{job_id}", timeout=30.0)
        status = (last.get("Status") or last.get("status") or "").lower()
        if status in {"completed", "blocked", "failed"}:
            return last
        time.sleep(2.5)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import generated bundles in output/generated into a TIA project via backend API."
    )
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--output-root", default="output/generated")
    parser.add_argument(
        "--project-path",
        default=os.getenv("TIA_PROJECT_PATH", ""),
        help="Windows path to .ap20 project (or set TIA_PROJECT_PATH).",
    )
    parser.add_argument(
        "--target-path",
        default=os.getenv("TIA_TARGET_PATH", "Program blocks/generati da tool"),
        help='TIA target path (default: "Program blocks/generati da tool").',
    )
    parser.add_argument("--prefix", default=os.getenv("TIA_IMPORT_PREFIX"))
    parser.add_argument("--save-project", action="store_true", default=True)
    parser.add_argument("--no-save-project", action="store_false", dest="save_project")
    parser.add_argument("--wait", action="store_true", help="Wait for import completion (and show status).")
    parser.add_argument(
        "--wait-timeout-s",
        type=int,
        default=600,
        help="Timeout seconds for --wait (default: 600).",
    )
    args = parser.parse_args()

    if not args.project_path.strip():
        raise SystemExit("Missing --project-path (or env TIA_PROJECT_PATH).")

    output_root = (PROJECT_ROOT / args.output_root).resolve()
    bundle_dirs = _list_bundle_dirs(output_root, args.prefix)
    if not bundle_dirs:
        print(f"No bundles found in {output_root}")
        return 0

    for bundle_dir in bundle_dirs:
        artifact_path = str(bundle_dir.relative_to(PROJECT_ROOT))
        payload = {
            "artifactPath": artifact_path,
            "projectPath": args.project_path,
            "targetPath": args.target_path,
            "targetName": None,
            "saveProject": bool(args.save_project),
            "notes": f"batch import {bundle_dir.name}",
        }
        response = _http_json("POST", f"{args.backend_url}/api/tia/jobs/import", payload, timeout=60.0)
        import_job_id = response.get("JobId") or response.get("jobId")
        compile_job_id = response.get("AutoCompileJobId")
        print(f"[QUEUED] {bundle_dir.name} import={import_job_id} autoCompile={compile_job_id}")

        if args.wait and import_job_id:
            final = _poll_job(args.backend_url, import_job_id, args.wait_timeout_s)
            status = final.get("Status") or final.get("status")
            detail = final.get("Detail") or final.get("detail")
            print(f"[IMPORT {status}] {bundle_dir.name} {detail or ''}".strip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

