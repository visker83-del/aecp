#!/usr/bin/env python3
"""Generate or verify a deterministic file index for the public repository."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "INDEX.json"
EXCLUDED_PARTS = {"__pycache__", ".git"}
EXCLUDED_NAMES = {".DS_Store"}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path == INDEX or path.name in EXCLUDED_NAMES or any(part in EXCLUDED_PARTS for part in relative.parts):
        return False
    if path.suffix == ".pyc" or relative.as_posix() == "results/run_meta.json":
        return False
    return path.is_file()


def build() -> dict:
    entries = []
    for path in sorted((path for path in ROOT.rglob("*") if included(path)), key=lambda item: item.relative_to(ROOT).as_posix()):
        data = path.read_bytes()
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return {"index_version": "1.0", "file_count": len(entries), "files": entries}


def render(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(build())
    if args.check:
        if not INDEX.exists() or INDEX.read_bytes() != expected:
            print("INDEX.json is stale; run python3 tools/make_index.py")
            return 1
        print("INDEX.json is current")
        return 0
    INDEX.write_bytes(expected)
    print(f"wrote {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
