"""Committed-disk verdict pin for scripts/audit_prereg_and_h10_fresh_references.py.

This audit is the single-source-of-truth guard that scans the DISP-003
preregistration markdown and the forward-block JSONs (canonical ``forward_block/``,
``forward_block_h10_fresh/`` and non-frozen ``forward_block_h10*`` variant dirs)
for stale path references, missing referenced files and frozen/git-HEAD hash
drift. Despite being load-bearing for durable-state integrity, the script had
**no test at all** before this module: nothing pinned a SPECIFIC committed
``PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_*.json`` artifact to an independent
recomputation, so a drifted, truncated or differently-scoped committed report
would go uncaught.

This module closes that gap by:

1. Re-running the SAME read-only pipeline (``run_audit``) against the committed
   preregistration and forward-block inputs on disk. ``run_audit`` writes nothing
   (the test never calls ``main()``), makes no network call and reads only
   committed local files.
2. Pinning the committed artifact's load-bearing fields (audit_id, pass,
   critical/errors/info, every scanned-file count, ``frozen_hashes_checked``,
   ``frozen_checks`` and every per-file row) to that fresh recomputation, with
   ``timestamp_utc`` fixed to the committed value.
3. Pinning the committed artifact sha256 to an independent literal so a swapped
   artifact is caught even if the test were regenerated to match it.
4. Proving the pin is a real constraint via synthetic-drift and input-perturbation
   self-tests.

Only the *informational* ``disk_sha256`` of non-frozen referenced source files
(``tests/*.py`` / ``scripts/*.py`` that a preregistration doc happens to name)
and the ``git_head_sha256`` / ``matches_git_head`` fields are normalised away
before the row comparison: those hashes are *defined* to reflect the current
working tree, so they legitimately move whenever a referenced source file is
edited (two such files changed after the committed report was generated). The
verdict, the frozen-block hashes and every structural field remain pinned. The
two frozen forward blocks are additionally pinned to independent literals.

Read-only and stdlib-only.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_prereg_and_h10_fresh_references.py"
COMMITTED_AUDIT = (
    ROOT
    / "research_state"
    / "PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261122T233217Z.json"
)

spec = importlib.util.spec_from_file_location("prereg_h10_ref_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the committed artifact sha256 so a coordinated change to the
# committed artifact still fails even if a module constant were edited.
EXPECTED_ARTIFACT_SHA256 = "b8075e2806175f014097d86c2dbfe314563b12bfed53241d31699ae5a16a3c91"

# The two frozen forward-block artifacts whose hashes the audit cross-checks.
FROZEN_CANONICAL = (
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"
)
FROZEN_H10_FRESH = (
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json"
)
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_H10_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _normalise(report: dict) -> dict:
    """Return a deep copy of ``report`` with the volatile per-reference hash
    fields removed so the committed artifact can be compared to a fresh run on
    its load-bearing fields only.

    ``disk_sha256`` / ``git_head_sha256`` / ``matches_git_head`` are defined to
    reflect the *current* working tree and git HEAD, so they move whenever a
    referenced (non-frozen) source file is edited or a new commit lands. They are
    not part of the audit's verdict. Everything else -- the pass flag, the
    critical/errors/info lists, all file counts, ``frozen_hashes_checked``,
    ``frozen_checks`` and the per-row structure (file, kind, severity, findings,
    path existence, frozen expectations) -- is pinned.
    """
    clone = copy.deepcopy(report)
    for row in clone.get("rows", []):
        for ref in row.get("path_refs", []):
            ref.pop("disk_sha256", None)
        for ref in row.get("references", []):
            ref.pop("disk_sha256", None)
            ref.pop("git_head_sha256", None)
            ref.pop("matches_git_head", None)
    return clone


class CommittedPreregAndH10FreshReferenceVerdictTests(unittest.TestCase):
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
        # the fresh result is identical to the committed artifact on every
        # load-bearing field. run_audit() writes nothing and reads only local inputs.
        cls.fresh = mod.run_audit(timestamp_utc=cls.committed["timestamp_utc"])

    def test_fresh_audit_id_and_pass(self):
        res = self.fresh
        self.assertEqual(res["audit_id"], "PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY")
        self.assertTrue(res["pass"], res)
        self.assertEqual(res["critical"], [])
        self.assertEqual(res["errors"], [])

    def test_committed_artifact_matches_fresh_recomputation(self):
        # Every load-bearing field must be reproduced from the committed inputs
        # with the committed timestamp fixed; only the volatile per-reference
        # working-tree hashes are normalised (see module docstring).
        self.assertEqual(
            _normalise(self.committed),
            _normalise(self.fresh),
            msg="committed prereg-and-h10-fresh reference-consistency artifact "
            "drifted from a fresh recomputation against the committed inputs",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["audit_id"], "PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY")
        self.assertEqual(c["prereg_files_scanned"], 20)
        self.assertEqual(c["frozen_prereg_files_scanned"], 0)
        self.assertEqual(c["disp003_frozen_prereg_files_scanned"], 4)
        self.assertEqual(c["h10_json_files_scanned"], 1)
        self.assertEqual(c["h10_variant_json_files_scanned"], 2)
        self.assertEqual(c["forward_block_json_files_scanned"], 1)
        self.assertEqual(c["files_scanned"], 28)
        self.assertEqual(c["critical"], [])
        self.assertEqual(c["errors"], [])
        self.assertEqual(c["info"], [])
        self.assertTrue(c["pass"])
        # Every per-file row is non-CRITICAL (OK only) and the row count matches.
        self.assertEqual(sorted({r["severity"] for r in c["rows"]}), ["OK"])
        self.assertEqual(len(c["rows"]), 28)

    def test_frozen_hashes_checked_match_disk(self):
        checked = self.committed["frozen_hashes_checked"]
        self.assertEqual(checked[FROZEN_CANONICAL], EXPECTED_CANONICAL)
        self.assertEqual(checked[FROZEN_H10_FRESH], EXPECTED_H10_FRESH)
        # The on-disk frozen blocks must still hash to the pinned literals.
        self.assertEqual(_sha256(ROOT / FROZEN_CANONICAL), EXPECTED_CANONICAL)
        self.assertEqual(_sha256(ROOT / FROZEN_H10_FRESH), EXPECTED_H10_FRESH)
        # Both frozen_checks must match frozen and not drift.
        self.assertEqual(len(self.committed["frozen_checks"]), 2)
        for chk in self.committed["frozen_checks"]:
            with self.subTest(path=chk["path"]):
                self.assertTrue(chk["matches_frozen"], chk)
                self.assertFalse(chk["git_head_drift"], chk)

    def test_artifact_sha256_matches_independent_literal(self):
        # Pin the committed artifact sha256 to an independent literal so a swapped
        # artifact is caught even if the test were regenerated to match it.
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_ARTIFACT_SHA256)

    def test_run_audit_is_deterministic(self):
        # Two fresh runs at the same fixed timestamp must be identical on their
        # load-bearing fields.
        again = mod.run_audit(timestamp_utc=self.committed["timestamp_utc"])
        self.assertEqual(_normalise(again), _normalise(self.fresh))

    def test_synthetic_drift_is_detected(self):
        # A tampered committed verdict (pass flipped) must not equal a fresh run.
        tampered = json.loads(json.dumps(self.committed))
        tampered["pass"] = False
        self.assertNotEqual(_normalise(tampered)["pass"], self.fresh["pass"])

        # A tampered file count must not equal a fresh recomputation.
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["files_scanned"] = self.committed["files_scanned"] + 1
        self.assertNotEqual(
            _normalise(tampered2)["files_scanned"], self.fresh["files_scanned"]
        )

        # A tampered frozen hash pin must not equal a fresh recomputation.
        tampered3 = json.loads(json.dumps(self.committed))
        tampered3["frozen_hashes_checked"][FROZEN_CANONICAL] = "0" * 64
        self.assertNotEqual(
            _normalise(tampered3)["frozen_hashes_checked"][FROZEN_CANONICAL],
            self.fresh["frozen_hashes_checked"][FROZEN_CANONICAL],
        )

        # Dropping a per-file row must not equal a fresh recomputation.
        tampered4 = json.loads(json.dumps(self.committed))
        tampered4["rows"] = tampered4["rows"][:-1]
        self.assertNotEqual(_normalise(tampered4)["rows"], self.fresh["rows"])

    def test_input_perturbation_changes_result(self):
        # Pointing the audit at an empty preregistration dir must move the
        # recomputed counts, proving the pin is sensitive to the committed inputs
        # and not a rubber stamp. The real prereg dir is only read, never written.
        with tempfile.TemporaryDirectory() as td:
            perturbed = mod.run_audit(
                prereg_dir=Path(td), timestamp_utc=self.committed["timestamp_utc"]
            )
        self.assertEqual(perturbed["prereg_files_scanned"], 0)
        self.assertNotEqual(perturbed["files_scanned"], self.committed["files_scanned"])
        # After restoration the module must reproduce the committed verdict again.
        self.assertEqual(
            _normalise(mod.run_audit(timestamp_utc=self.committed["timestamp_utc"])),
            _normalise(self.fresh),
        )


if __name__ == "__main__":
    unittest.main()