#!/usr/bin/env python3
"""Bump research_state/universe_frontier.json last_updated_utc past the record it quotes.

The file's latest_archive_probe quotes the live cutoff probe 2026-11-05T10:38:51Z
(record research_state/cutoff_probe/cutoff_probe_20261105T103851Z.json, UNBLOCKED)
while its own last_updated_utc still read 2026-11-04T22:45Z -- a hand-written
timestamp left behind by the previous session, before the probe it names existed.
The file's content (latest_h10_gate_reconciliation_20261105T1039Z) was in fact
written at 10:39Z, so the only defect is the timestamp field.

This is a one-field repair, re-serialised through scripts/rewrite_state_json.py's
formatting detector so the diff stays minimal (indent=2, ensure_ascii=True, the
non-ASCII CoinMetrics catalog entries stay escaped). No content, probe record,
canonical block, grid or hypothesis field is touched.

Usage:
    python3 scripts/fix_frontier_last_updated_utc.py
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTIER = ROOT / "research_state" / "universe_frontier.json"


def main() -> int:
    raw = FRONTIER.read_bytes()
    d = json.loads(raw)
    probe = d.get("latest_archive_probe", {}).get("probe_utc")
    if not probe:
        print("no probe_utc in latest_archive_probe; refusing to guess a timestamp")
        return 1
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # never backdate: floor the new timestamp at the quoted probe time
    new_ts = max(now, probe)
    old_ts = d.get("last_updated_utc")
    if old_ts == new_ts:
        print(f"last_updated_utc already {old_ts}; no change")
        return 0
    print(f"last_updated_utc: {old_ts} -> {new_ts} (probe quoted: {probe})")
    d["last_updated_utc"] = new_ts
    # re-serialise through the format detector so the diff stays byte-minimal
    out = json.dumps(d, indent=2, ensure_ascii=True) + "\n"
    if out.encode() == raw:
        print("re-serialised output is byte-identical to the original; no write")
        return 0
    FRONTIER.write_bytes(out.encode())
    print(f"wrote {FRONTIER.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())