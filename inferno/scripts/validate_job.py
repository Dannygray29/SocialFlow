#!/usr/bin/env python3
import json
import sys
from pathlib import Path

REQUIRED = {"id", "title", "script", "platforms"}

def validate(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    missing = REQUIRED - data.keys()
    if missing:
        raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
    if not isinstance(data["script"], str) or not data["script"].strip():
        raise ValueError("script must be a non-empty string")
    if not isinstance(data["platforms"], list) or not data["platforms"]:
        raise ValueError("platforms must be a non-empty list")
    if any(p not in {"youtube", "tiktok"} for p in data["platforms"]):
        raise ValueError("platforms may only contain youtube and tiktok")
    if data.get("aspect_ratio", "9:16") != "9:16":
        raise ValueError("Inferno MVP requires 9:16")
    return data

if __name__ == "__main__":
    try:
        job = validate(Path(sys.argv[1]))
        print(json.dumps(job, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        raise SystemExit(1)
