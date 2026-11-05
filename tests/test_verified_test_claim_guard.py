#!/usr/bin/env python3
"""Regression guards for the verified test-suite claim.

The run manifest's ``latest_verified_test_claim`` field (e.g.
``"229/229/0"``) is a durable-state narrative that drifts whenever tests are
added, removed or repaired. It drifted from the real suite count
(229 vs the observed 236) with no guard to catch it -- the same
single-source-of-truth hazard class already guarded for
``next_sequence_number``.

These guards pin the manifest claim to the machine-readable snapshot written
by ``scripts/record_test_claim.py`` and to the actual test inventory, so a
stale or malformed claim fails the build.
"""

import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "research_state"
MANIFEST_PATH = STATE / "run_manifest.json"
SNAPSHOT_PATH = STATE / "verified_test_claim_claim_snapshot.json"
CLAIM_FORMAT = re.compile(r"^(\d+)/(\d+)/(\d+)$")


def _load(path):
    with open(path) as f:
        return json.load(f)


class TestVerifiedTestClaimGuard(unittest.TestCase):
    def setUp(self):
        self.manifest = _load(MANIFEST_PATH)
        if not SNAPSHOT_PATH.exists():
            self.skipTest(
                "no verified_test_claim snapshot yet; run "
                "scripts/record_test_claim.py to create it"
            )
        self.snapshot = _load(SNAPSHOT_PATH)

    def test_claim_format_is_run_run_failures(self):
        claim = self.manifest["latest_verified_test_claim"]
        m = CLAIM_FORMAT.match(claim)
        self.assertIsNotNone(
            m, f"latest_verified_test_claim {claim!r} is not run/run/failures"
        )
        run, run2, failures = (int(g) for g in m.groups())
        self.assertEqual(run, run2, "run count must equal the ok count")
        self.assertEqual(failures, self.snapshot["tests_failures"])

    def test_manifest_claim_matches_snapshot(self):
        self.assertEqual(
            self.manifest["latest_verified_test_claim"],
            self.snapshot["claim"],
            "manifest latest_verified_test_claim must match the snapshot "
            "written by scripts/record_test_claim.py",
        )

    def test_manifest_references_snapshot(self):
        referenced = self.manifest.get("latest_verified_test_claim_snapshot")
        self.assertEqual(
            referenced,
            str(SNAPSHOT_PATH.relative_to(ROOT)),
            "manifest must reference the snapshot path written by "
            "scripts/record_test_claim.py",
        )

    def test_snapshot_run_matches_suite_summary(self):
        self.assertEqual(self.snapshot["tests_run"], self.snapshot["tests_ok"])
        self.assertEqual(self.snapshot["tests_failures"], 0)
        self.assertGreater(self.snapshot["tests_run"], 0)

    def test_snapshot_fingerprint_matches_inventory(self):
        # Re-derive the fingerprint from the on-disk .py inventory so the
        # snapshot cannot pin a stale input set.
        files = []
        for d in ("tests", "scripts"):
            for p in sorted((ROOT / d).rglob("*.py")):
                if "__pycache__" in p.parts:
                    continue
                files.append((p.relative_to(ROOT).as_posix(), p.read_bytes()))
        files.sort(key=lambda t: t[0])
        h = hashlib.sha256()
        for rel, data in files:
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(data)
            h.update(b"\0")
        self.assertEqual(
            h.hexdigest(),
            self.snapshot["input_fingerprint"],
            "snapshot input_fingerprint does not match the on-disk .py inventory",
        )
        self.assertEqual(
            len(files),
            self.snapshot["input_file_count"],
            "snapshot input_file_count does not match the on-disk .py inventory",
        )


if __name__ == "__main__":
    unittest.main()