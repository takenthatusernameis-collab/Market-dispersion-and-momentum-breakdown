#!/usr/bin/env python3
"""Append a session record to research_state/run_manifest.json and repoint
session_record_latest.

The manifest's existing convention (see run_manifest.json) is that each
session record is stored as a top-level key ``session_record_<stem>``, the
ordered list of record keys lives under ``session_records``, and
``session_record_latest`` names the newest record. This script follows that
convention exactly: it inserts/overwrites the top-level key, appends the key to
``session_records`` (idempotently), repoints ``session_record_latest`` and sets
``last_updated_utc``.

Pure stdlib; no market data; no network.

Usage:
    python3 scripts/record_session_record.py <session_record.json>
    cat session_record.json | python3 scripts/record_session_record.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research_state" / "run_manifest.json"

REQUIRED = ("session_id", "timestamp_utc", "action", "outcome", "verification")


def load_payload(source):
    if source == "-":
        return json.load(sys.stdin)
    with open(source, encoding="utf-8") as fh:
        return json.load(fh)


def record_key(payload):
    """Map a session_id to the manifest's top-level key shape.

    Assumes ``payload["session_id"]`` has already passed the ``session_`` prefix
    check performed by ``main``; raises ValueError if called on a bare id.
    """
    sid = payload["session_id"]
    if not sid.startswith("session_"):
        raise ValueError(f"session_id must start with 'session_': {sid!r}")
    return sid if sid.startswith("session_record_") else f"session_record_{sid[len('session_'):]}"


def main(argv):
    if len(argv) > 1:
        sys.exit("usage: record_session_record.py [session_record.json|-]")
    payload = load_payload(argv[0] if argv else "-")
    missing = [k for k in REQUIRED if not payload.get(k)]
    if missing:
        sys.exit(f"session record missing required fields: {missing}")
    sid = payload["session_id"]
    if not sid.startswith("session_"):
        sys.exit(f"session_id must start with 'session_': {sid!r}")
    key = record_key(payload)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest[key] = payload
    ids = manifest.setdefault("session_records", [])
    if key not in ids:
        ids.append(key)
    manifest["session_record_latest"] = key
    manifest["last_updated_utc"] = payload["timestamp_utc"]
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[record_session_record] wrote {key}; session_record_latest -> {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))