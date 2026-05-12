from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Clear artifact_overrides from an IR JSON (in-place).")
    ap.add_argument("--ir-json", required=True)
    args = ap.parse_args()

    path = (PROJECT_ROOT / args.ir_json).resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("IR JSON must be an object.")
    removed = 0
    if "artifact_overrides" in payload and payload["artifact_overrides"]:
        removed = len(payload.get("artifact_overrides") or {})
    payload["artifact_overrides"] = {}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"cleared_overrides": removed}, indent=2))
    print(f"[OK] Updated {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

