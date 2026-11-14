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
stale or malformed claim fails the build. The snapshot now includes per-file
sha256 hashes so a fingerprint mismatch can name the exact drifted files.
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

# Directories whose .py files are the executable inputs to the recorded claim.
INPUT_DIRS = ("tests", "scripts")


def _load(path):
    with open(path) as f:
        return json.load(f)


def _inventory_fingerprint():
    """Deterministic sha256 over the sorted .py file inventory of the suite inputs.

    Returns the aggregate fingerprint and a list of per-file entries with
    path and sha256, so the guard can name exactly which files drifted.
    """
    files = []
    for d in INPUT_DIRS:
        for p in sorted((ROOT / d).rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            data = p.read_bytes()
            file_hash = hashlib.sha256(data).hexdigest()
            files.append({
                "path": p.relative_to(ROOT).as_posix(),
                "sha256": file_hash,
            })
    files.sort(key=lambda t: t["path"])
    h = hashlib.sha256()
    for f in files:
        h.update(f["path"].encode("utf-8"))
        h.update(b"\0")
        h.update(f["sha256"].encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest(), files


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
        # snapshot cannot pin a stale input set. The snapshot now includes
        # per-file sha256 hashes so we can name exactly which files drifted.
        fingerprint, on_disk_files = _inventory_fingerprint()
        snap_files = self.snapshot.get("input_files", [])

        # Build maps for easy comparison
        on_disk_map = {f["path"]: f["sha256"] for f in on_disk_files}
        snap_map = {f["path"]: f["sha256"] for f in snap_files} if isinstance(snap_files[0], dict) else {f: None for f in snap_files}

        # Find differences
        drifted = []
        for path, disk_hash in on_disk_map.items():
            if path not in snap_map:
                drifted.append(f"  + {path} (new file)")
            elif snap_map[path] != disk_hash:
                drifted.append(f"  ~ {path} (content changed)")

        for path in snap_map:
            if path not in on_disk_map:
                drifted.append(f"  - {path} (deleted)")

        self.assertEqual(
            fingerprint,
            self.snapshot["input_fingerprint"],
            "snapshot input_fingerprint does not match the on-disk .py inventory"
            + ("\nDrifted files:\n" + "\n".join(drifted) if drifted else ""),
        )
        self.assertEqual(
            len(on_disk_files),
            self.snapshot["input_file_count"],
            "snapshot input_file_count does not match the on-disk .py inventory",
        )


if __name__ == "__main__":
    unittest.main()