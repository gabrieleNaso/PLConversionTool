#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
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


def _list_bundle_dirs(output_root: Path, prefix: str | None, bundle: str | None) -> list[Path]:
    if not output_root.exists():
        return []
    candidates = [p for p in output_root.iterdir() if p.is_dir()]
    if bundle:
        candidates = [p for p in candidates if p.name.lower() == bundle.lower()]
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


def _is_name_collision(detail: str | None) -> bool:
    if not detail:
        return False
    lowered = detail.lower()
    return "block name" in lowered and "already exists" in lowered


def _extract_colliding_name(detail: str | None) -> str | None:
    if not detail:
        return None
    match = re.search(r"The block name '([^']+)' is invalid", detail, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _split_trailing_number(name: str) -> tuple[str, int | None]:
    match = re.match(r"^(.*?)(\d+)$", name)
    if not match:
        return name, None
    stem = match.group(1)
    number = int(match.group(2))
    return stem, number


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _build_renamed_bundle(
    source_bundle_dir: Path,
    source_name: str,
    target_name: str,
    retry_index: int,
) -> Path:
    retry_root = source_bundle_dir.parent / "_auto_renamed_imports"
    retry_root.mkdir(parents=True, exist_ok=True)
    target_dir = retry_root / f"{source_bundle_dir.name}__retry{retry_index}_{target_name}"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_bundle_dir, target_dir)

    # Rename filenames first so references remain coherent with updated payload.
    files = sorted(target_dir.rglob("*"), key=lambda p: len(p.name), reverse=True)
    for file_path in files:
        if not file_path.is_file():
            continue
        if source_name in file_path.name:
            new_name = file_path.name.replace(source_name, target_name)
            file_path.rename(file_path.with_name(new_name))

    # Update textual content in XML/JSON/notes.
    for file_path in target_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".xml", ".json", ".txt", ".md"}:
            continue
        text = _read_text(file_path)
        updated = text.replace(source_name, target_name)
        if updated != text:
            _write_text(file_path, updated)

    return target_dir


def _queue_import_job(base_url: str, payload: dict) -> str | None:
    response = _http_json("POST", f"{base_url}/api/tia/jobs/import", payload, timeout=60.0)
    import_job_id = response.get("JobId") or response.get("jobId")
    return import_job_id


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import generated bundles in data/output/generated into a TIA project via backend API."
    )
    parser.add_argument("--backend-url", default=os.getenv("BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--output-root", default="data/output/generated")
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
    parser.add_argument(
        "--bundle",
        default=os.getenv("TIA_IMPORT_BUNDLE"),
        help="Import only the bundle directory with this exact name.",
    )
    parser.add_argument("--save-project", action="store_true", default=True)
    parser.add_argument("--no-save-project", action="store_false", dest="save_project")
    parser.add_argument("--wait", action="store_true", help="Wait for import completion (and show status).")
    parser.add_argument(
        "--max-name-collision-retries",
        type=int,
        default=12,
        help="Automatic retries when TIA reports duplicate block name (default: 12).",
    )
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
    bundle_dirs = _list_bundle_dirs(output_root, args.prefix, args.bundle)
    if not bundle_dirs:
        print(f"No bundles found in {output_root}")
        return 0

    for bundle_dir in bundle_dirs:
        current_bundle_dir = bundle_dir
        retry_index = 0
        current_name: str | None = None
        base_name: str | None = None
        next_suffix = 1

        while True:
            artifact_path = str(current_bundle_dir.relative_to(PROJECT_ROOT))
            payload = {
                "artifactPath": artifact_path,
                "projectPath": args.project_path,
                "targetPath": args.target_path,
                "targetName": None,
                "saveProject": bool(args.save_project),
                "notes": f"batch import {bundle_dir.name}",
            }
            import_job_id = _queue_import_job(args.backend_url, payload)
            suffix_note = f" [retry {retry_index}]" if retry_index else ""
            print(f"[QUEUED{suffix_note}] {current_bundle_dir.name} import={import_job_id}")

            if not import_job_id:
                break

            final = _poll_job(args.backend_url, import_job_id, args.wait_timeout_s)
            status = (final.get("Status") or final.get("status") or "").lower()
            detail = final.get("Detail") or final.get("detail")

            if status == "completed":
                print(f"[IMPORT completed] {current_bundle_dir.name}")
                if args.wait and detail:
                    print(f"  detail: {detail}")
                break

            if (
                status == "blocked"
                and _is_name_collision(detail)
                and retry_index < args.max_name_collision_retries
            ):
                blocked_name = _extract_colliding_name(detail)
                if not blocked_name:
                    break
                if base_name is None:
                    stem, suffix = _split_trailing_number(blocked_name)
                    base_name = stem
                    next_suffix = (suffix + 1) if suffix is not None else 1

                retry_index += 1
                next_name = f"{base_name}{next_suffix}"
                next_suffix += 1
                source_name = current_name or blocked_name
                current_bundle_dir = _build_renamed_bundle(
                    current_bundle_dir,
                    source_name=source_name,
                    target_name=next_name,
                    retry_index=retry_index,
                )
                current_name = next_name
                print(
                    f"[RENAME] Collisione nome blocco '{blocked_name}'. "
                    f"Riprovo con '{next_name}'."
                )
                continue

            print(f"[IMPORT {status or 'unknown'}] {current_bundle_dir.name} {detail or ''}".strip())
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
