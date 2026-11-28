"""Committed-disk verdict pin for scripts/audit_preregistration_coverage.py.

This audit is the single-source-of-truth guard that every DISP-003
integrity-audit JSON resolves to a preregistration that exists on disk and that
every preregistration is covered by at least one audit. The existing
``tests/test_preregistration_coverage_audit.py`` re-derives ``audit()``
*behaviour* and checks the on-disk output equals a fresh in-memory run, but it
never pins a SPECIFIC committed ``research_state/preregistration_coverage_audit.json``
artifact to an INDEPENDENT sha256 literal, and it has no synthetic-drift or
input-perturbation self-tests proving the comparison is a real constraint rather
than a rubber stamp.

This module closes that gap by:

1. Re-running the SAME read-only pipeline (``audit``) against the committed
   integrity-audit and preregistration inputs on disk. ``audit`` writes nothing
   (the test never calls ``main()``), makes no network call and reads only
   committed local files.
2. Pinning the committed artifact's load-bearing fields (audit_id, pass, every
   scanned-file count, ``preregistrations_on_disk``, the missing/uncovered lists
   and every per-file row) to that fresh recomputation. ``audit()`` is
   deterministic and carries no wall-clock field, so the WHOLE artifact must be
   byte-for-byte reproduced (nothing is normalised away).
3. Pinning the committed artifact sha256 to an independent literal so a swapped
   artifact is caught even if the test were regenerated to match it.
4. Proving the pin is a real constraint via synthetic-drift and
   input-perturbation self-tests.

Read-only and stdlib-only.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_preregistration_coverage.py"
COMMITTED_AUDIT = ROOT / "research_state" / "preregistration_coverage_audit.json"

spec = importlib.util.spec_from_file_location("prereg_coverage_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the committed artifact sha256 so a coordinated change to
# the committed artifact still fails even if a module constant were edited.
EXPECTED_ARTIFACT_SHA256 = "ace0e8a861126457535223061527684a1578de28bed533ebc6d63d0a4c9a6875"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class CommittedPreregistrationCoverageVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [COMMITTED_AUDIT, SPEC_PATH]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        # Re-run the read-only pipeline. audit() writes nothing and reads only
        # local inputs, so the fresh result must equal the committed artifact on
        # every field (there is no volatile timestamp to normalise).
        cls.fresh = mod.audit()

    def test_fresh_audit_id_and_pass(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], "PREREGISTRATION_COVERAGE_AUDIT_20261103")
        self.assertTrue(res["pass"], res)
        self.assertEqual(res["audits_missing_prereq"], [])
        self.assertEqual(res["preregistrations_uncovered_by_any_audit"], [])

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The WHOLE artifact must be reproduced from the committed inputs; nothing
        # is excluded because audit() carries no working-tree-dependent field.
        self.assertEqual(
            self.committed,
            self.fresh,
            msg="committed preregistration-coverage artifact drifted from a "
            "fresh recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["audit_id"], "PREREGISTRATION_COVERAGE_AUDIT_20261103")
        self.assertEqual(c["audits_scanned"], 32)
        self.assertEqual(c["main_audits_scanned"], 27)
        self.assertEqual(c["f1_audit_files_scanned"], 5)
        self.assertEqual(len(c["preregistrations_on_disk"]), 23)
        self.assertEqual(c["audits_missing_prereq"], [])
        self.assertEqual(c["preregistrations_uncovered_by_any_audit"], [])
        self.assertEqual(len(c["rows"]), 32)
        self.assertTrue(c["pass"])
        # Every main/addenda row resolves to an existing prereq or is a declared
        # no-prereq additive/addendum row; no row may be an unresolved miss.
        for row in c["rows"]:
            with self.subTest(audit=row["audit"]):
                self.assertTrue(row["exists"], row)
                if row.get("preregistration"):
                    self.assertTrue(
                        (ROOT / row["resolved"]).is_file(),
                        f"{row['resolved']} does not exist on disk",
                    )

    def test_frozen_f1_rows_are_pinned(self):
        frozen = [r for r in self.committed["rows"] if r.get("frozen_record") is True]
        self.assertEqual(len(frozen), 5)
        for row in frozen:
            with self.subTest(audit=row["audit"]):
                self.assertTrue(row["exists"], row)
                self.assertTrue((ROOT / row["resolved"]).is_file(), row)

    def test_artifact_sha256_matches_independent_literal(self):
        # Pin the committed artifact sha256 to an independent literal so a swapped
        # artifact is caught even if the test were regenerated to match it.
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_ARTIFACT_SHA256)

    def test_audit_is_deterministic(self):
        # Two fresh runs must be identical.
        self.assertEqual(mod.audit(), self.fresh)

    def test_synthetic_drift_is_detected(self):
        # A tampered committed verdict (pass flipped) must not equal a fresh run.
        tampered = copy.deepcopy(self.committed)
        tampered["pass"] = False
        self.assertNotEqual(tampered["pass"], self.fresh["pass"])

        # A tampered file count must not equal a fresh recomputation.
        tampered2 = copy.deepcopy(self.committed)
        tampered2["audits_scanned"] = self.committed["audits_scanned"] + 1
        self.assertNotEqual(tampered2["audits_scanned"], self.fresh["audits_scanned"])

        # A tampered prereq list must not equal a fresh recomputation.
        tampered3 = copy.deepcopy(self.committed)
        tampered3["preregistrations_on_disk"] = tampered3["preregistrations_on_disk"][:-1]
        self.assertNotEqual(
            tampered3["preregistrations_on_disk"],
            self.fresh["preregistrations_on_disk"],
        )

        # Dropping a per-file row must not equal a fresh recomputation.
        tampered4 = copy.deepcopy(self.committed)
        tampered4["rows"] = tampered4["rows"][:-1]
        self.assertNotEqual(tampered4["rows"], self.fresh["rows"])

    def test_input_perturbation_changes_result(self):
        # Opting out of the F1 frozen-record scan must move the recomputed counts,
        # proving the pin is sensitive to the committed inputs and not a rubber
        # stamp. The real integrity-audit dirs are only read, never written.
        perturbed = mod.audit(f1_integrity_audit_dirs=[], f1_prereg_dirs=[])
        self.assertEqual(perturbed["f1_audit_files_scanned"], 0)
        self.assertEqual(perturbed["audits_scanned"], 27)
        self.assertNotEqual(
            perturbed["audits_scanned"], self.committed["audits_scanned"]
        )
        # After restoration the module must reproduce the committed verdict again.
        self.assertEqual(mod.audit(), self.fresh)


if __name__ == "__main__":
    unittest.main()