#!/usr/bin/env python3
"""Durable-state guard: a state file's last_updated_utc must not predate the
record it quotes.

research_state/universe_frontier.json's latest_archive_probe quotes a live
cutoff probe (2026-11-05T10:38:51Z) while its own last_updated_utc read
2026-11-04T22:45Z -- i.e. the file claimed to be current before the record it
names existed, and its content (latest_h10_gate_reconciliation_20261105T1039Z)
had in fact been written at 10:39Z. A hand-written timestamp that drifts behind
the evidence it summarises is the same single-source-of-truth hazard class as
a stale canonical-block sha256: the durable state looks internally consistent
while describing an event it has not yet recorded, and every downstream reader
that trusts last_updated_utc (including the next agent's "verify current state
before acting" step) gets a wrong answer.

Note this guard is deliberately scoped to each file's OWN last_updated_utc
against the probe IT quotes. It does NOT assert that the registry's
last_updated_utc trails the frontier's: the two files are updated in separate
batches (the registry is bumped when a hypothesis is allocated, the frontier
when the catalog or the gate summary moves), so a registry that is older than
the frontier is normal and correct. Asserting that coupling would be the same
class of error as the staleness this guard exists to catch.

Read-only, stdlib-only: parses the state JSON files and compares timestamps.
Makes no network call and touches no artifact.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _ts(value):
    """Normalise a 'YYYY-MM-DDTHH:MM:SSZ' string to a bare comparable string."""
    if not value:
        return None
    return value.replace("Z", "").split(".")[0]


class StateTimestampNotStaleTests(unittest.TestCase):
    def test_frontier_last_updated_not_before_quoted_probe(self):
        frontier = _load(STATE / "universe_frontier.json")
        lu = frontier.get("last_updated_utc")
        probe = frontier.get("latest_archive_probe", {}).get("probe_utc")
        self.assertIsNotNone(lu, "universe_frontier.json last_updated_utc missing")
        self.assertIsNotNone(probe,
                             "universe_frontier.json latest_archive_probe.probe_utc missing")
        self.assertGreaterEqual(
            _ts(lu), _ts(probe),
            f"universe_frontier.json last_updated_utc {lu} predates the probe it "
            f"quotes {probe} -- the file was last touched before the record it names",
        )

    def test_manifest_last_updated_not_before_quoted_probe(self):
        manifest = _load(STATE / "run_manifest.json")
        lu = manifest.get("last_updated_utc")
        probe = manifest.get("latest_archive_probe", {}).get("probe_utc")
        self.assertIsNotNone(lu, "run_manifest.json last_updated_utc missing")
        self.assertIsNotNone(probe,
                             "run_manifest.json latest_archive_probe.probe_utc missing")
        self.assertGreaterEqual(
            _ts(lu), _ts(probe),
            f"run_manifest.json last_updated_utc {lu} predates the probe it quotes {probe}",
        )


if __name__ == "__main__":
    unittest.main()