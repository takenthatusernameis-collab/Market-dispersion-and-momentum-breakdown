"""Committed-disk verdict pin for scripts/audit_integrity_audit_references.py.

The static suite (test_integrity_audit_reference_consistency.py) re-derives
``run_audit()`` *behaviour* (pass / critical / errors / files_scanned / frozen
hashes) but never pins a SPECIFIC committed
``INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_*.json`` artifact's load-bearing fields to
an independent recomputation. The repository carries 50+ such committed
reference-consistency artifacts; if the newest one drifted, was truncated, or was
written against different inputs, no test would catch it because the static test
only re-runs the pipeline and checks the live verdict, not the committed bytes.

This module closes that single-source-of-truth gap by:

1. Re-running the SAME read-only audit pipeline (``run_audit``) against the
   committed ``integrity_audit/`` inputs on disk.
2. Pinning the committed artifact's load-bearing fields (audit_id, files_scanned,
   main/frozen file counts, critical/errors/info, pass, frozen_hashes_checked,
   frozen_git_head_checks, and every per-file row) to that fresh recomputation.
   ``timestamp_utc`` is fixed to the committed value so the WHOLE artifact is
   reproduced byte-for-byte; nothing is excluded.
3. Pinning the committed artifact sha256 to an independent literal so a swapped
   artifact is caught even if the test were regenerated to match it.
4. Proving the pin is a real constraint via synthetic-drift self-tests.

Read-only and stdlib-only. ``run_audit()`` writes nothing (the test never calls
``main()``), makes no network call, and reads only committed local files.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_integrity_audit_references.py"
COMMITTED_AUDIT = (
    ROOT
    / "research_state"
    / "INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261126T181256Z.json"
)

spec = importlib.util.spec_from_file_location("integrity_audit_ref_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the committed artifact sha256 so a coordinated change to the
# committed artifact still fails even if a module constant were edited.
EXPECTED_ARTIFACT_SHA256 = "99a8d1601d5681f67de4ae21d97d3e6de8e9aeb76544edf4f53cee2fa170ac39"

# The two frozen forward-block artifacts whose hashes the audit cross-checks.
FROZEN_CANONICAL = (
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"
)
FROZEN_H10_FRESH = (
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json"
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class CommittedIntegrityAuditReferenceVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [COMMITTED_AUDIT, SPEC_PATH]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        # Re-run the read-only pipeline with the committed wall-clock timestamp so
        # the fresh result is byte-identical to the committed artifact. run_audit()
        # writes nothing and reads only committed local inputs.
        cls.fresh = mod.run_audit(timestamp_utc=cls.committed["timestamp_utc"])

    def test_fresh_audit_id_and_pass(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], "INTEGRITY_AUDIT_REFERENCE_CONSISTENCY")
        self.assertTrue(res["pass"], res)
        self.assertEqual(res["critical"], [])
        self.assertEqual(res["errors"], [])

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed inputs with the
        # committed timestamp fixed; nothing is excluded, so any drift (a truncated
        # row, a flipped verdict, a changed file count) is caught.
        self.assertEqual(
            self.committed,
            self.fresh,
            msg="committed integrity-audit reference-consistency artifact drifted "
            "from a fresh recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["audit_id"], "INTEGRITY_AUDIT_REFERENCE_CONSISTENCY")
        self.assertEqual(c["files_scanned"], 32)
        self.assertEqual(c["main_integrity_audit_files_scanned"], 27)
        self.assertEqual(c["frozen_integrity_audit_files_scanned"], 5)
        self.assertEqual(c["critical"], [])
        self.assertEqual(c["errors"], [])
        self.assertEqual(len(c["info"]), 21)
        self.assertTrue(c["pass"])
        # Every per-file row is non-CRITICAL (OK or INFO only).
        self.assertEqual(sorted({r["severity"] for r in c["rows"]}), ["INFO", "OK"])
        self.assertEqual(len(c["rows"]), 32)

    def test_frozen_hashes_checked_match_disk(self):
        checked = self.committed["frozen_hashes_checked"]
        self.assertEqual(
            checked[FROZEN_CANONICAL],
            "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
        )
        self.assertEqual(
            checked[FROZEN_H10_FRESH],
            "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
        )
        # The two frozen_git_head_checks must both match frozen and not drift.
        self.assertEqual(len(self.committed["frozen_git_head_checks"]), 2)
        for chk in self.committed["frozen_git_head_checks"]:
            with self.subTest(path=chk["path"]):
                self.assertTrue(chk["matches_frozen"], chk)
                self.assertFalse(chk["git_head_drift"], chk)

    def test_artifact_sha256_matches_independent_literal(self):
        # Pin the committed artifact sha256 to an independent literal so a swapped
        # artifact is caught even if the test were regenerated to match it.
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_ARTIFACT_SHA256)

    def test_synthetic_drift_is_detected(self):
        # A tampered committed verdict (pass flipped) must not equal a fresh run.
        tampered = json.loads(json.dumps(self.committed))
        tampered["pass"] = False
        self.assertNotEqual(tampered["pass"], self.fresh["pass"])

        # A tampered file count must not equal a fresh recomputation.
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["files_scanned"] = self.committed["files_scanned"] + 1
        self.assertNotEqual(tampered2["files_scanned"], self.fresh["files_scanned"])

        # A tampered frozen hash pin must not equal a fresh recomputation.
        tampered3 = json.loads(json.dumps(self.committed))
        tampered3["frozen_hashes_checked"][FROZEN_CANONICAL] = "0" * 64
        self.assertNotEqual(
            tampered3["frozen_hashes_checked"][FROZEN_CANONICAL],
            self.fresh["frozen_hashes_checked"][FROZEN_CANONICAL],
        )

        # Dropping a per-file row must not equal a fresh recomputation.
        tampered4 = json.loads(json.dumps(self.committed))
        tampered4["rows"] = tampered4["rows"][:-1]
        self.assertNotEqual(tampered4["rows"], self.fresh["rows"])


if __name__ == "__main__":
    unittest.main()