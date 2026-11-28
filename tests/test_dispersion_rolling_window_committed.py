"""Committed-disk verdict pin for scripts/dispersion_rolling_window.py (DISP-003-REGIME-002).

The static suite (test_dispersion_rolling_window.py) only exercises the pure
seams (``assign_states`` / ``window_label`` / ``window_metrics``) on synthetic
fixtures -- nothing re-derives the committed artifact's load-bearing
rolling-window robustness numbers (per-window n_high/n_low, high_low_diff_net_1x,
2025-10 leave-one-out delta fractions, per-window labels, overall label) from the
REAL committed canonical block. If that committed artifact drifted, was
truncated, or was written against a different block, no test would catch it --
the same single-source-of-truth hazard the committed-disk pins for the
tail-influence (DISP-003-TAILAUDIT-001), state-representativeness
(DISP-003-STATEAUDIT-001), maturity-timeline (H35), independent-recomputation
(H37), frozen-tree (H38), expanding-universe (H33), point-in-time-eligibility
(H57), final-integrity and H10-fresh-integrity audits already close.

This module re-runs the SAME read-only audit pipeline (``main``) against the
committed canonical block, redirecting ``OUT_DIR``/``OUT_PATH`` to a temp dir so
the committed artifact is never written, and pins the committed artifact's
load-bearing fields (status, overall_label, baseline, anchor-reproduction check,
every per-window result, decision thresholds) to that fresh recomputation. Only
``computed_utc`` is allowed to differ between the committed artifact and a fresh
run. Read-only; path constants are derived from ``__file__`` so the test is
CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "dispersion_rolling_window.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_rolling_dispersion_window_20261028.json"
)

spec = importlib.util.spec_from_file_location("rolling_window_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _run_with_block(block_path: Path):
    """Run the audit against ``block_path`` with OUT_DIR/OUT_PATH redirected.

    The committed artifact is never written: OUT_DIR and OUT_PATH are redirected
    to a temp dir and the module globals are restored in ``finally``. Returns the
    parsed fresh output. Raises AssertionError if ``main`` returns nonzero (the
    W=365 anchor reproduction gate rejects a block that does not reproduce the
    canonical anchor).
    """
    # The audit's main() prints OUT_PATH.relative_to(ROOT), so the redirect
    # target must live under ROOT; TemporaryDirectory(dir=ROOT) keeps that
    # invariant and is cleaned up on exit.
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        tmp_dir = Path(tmp)
        old_block, old_dir, old_out = mod.BLOCK_PATH, mod.OUT_DIR, mod.OUT_PATH
        try:
            mod.BLOCK_PATH = block_path
            mod.OUT_DIR = tmp_dir
            mod.OUT_PATH = tmp_dir / "audit.json"
            rc = mod.main()
        finally:
            mod.BLOCK_PATH, mod.OUT_DIR, mod.OUT_PATH = old_block, old_dir, old_out
        if rc != 0:
            raise AssertionError(
                "rolling-window audit main() returned a nonzero exit code "
                f"({rc}); the W=365 anchor reproduction gate rejected the block"
            )
        return _load(tmp_dir / "audit.json")


class CommittedRollingWindowVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [mod.BLOCK_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)
        cls.fresh = _run_with_block(mod.BLOCK_PATH)

    def test_fresh_audit_label_and_status(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(res["overall_label"], "ROLLING_FRAGILE")
        self.assertEqual(
            res["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-002",
        )
        self.assertEqual(
            res["audit_id"], "H004V106_ROLLING_DISPERSION_WINDOW_20261028"
        )
        self.assertEqual(res["anchor_reproduction_check"]["match"], True)
        self.assertEqual(res["anchor_reproduction_check"]["W"], 365)

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed canonical block;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed rolling-window audit drifted from a fresh recomputation "
            "against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["overall_label"], "ROLLING_FRAGILE")
        self.assertEqual(c["status"], "EXPLORATORY_ONLY")
        base = c["baseline"]
        self.assertEqual(base["n_formations"], 608)
        self.assertEqual(base["n_high"], 61)
        self.assertEqual(base["n_low"], 90)
        self.assertEqual(base["n_mid"], 457)
        self.assertEqual(base["date_first"], "2025-01-01")
        self.assertEqual(base["date_last"], "2026-08-31")
        self.assertEqual(base["data_cutoff_utc"], "2026-09-30T00:00:00Z")
        self.assertAlmostEqual(
            base["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )
        arc = c["anchor_reproduction_check"]
        self.assertEqual(arc["W"], 365)
        self.assertEqual(arc["match"], True)
        self.assertAlmostEqual(
            arc["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )

        # Every predeclared window must be present, adequate and SIGN_POSITIVE,
        # with the exact per-window counts and diffs pinned.
        results = c["window_results"]
        self.assertEqual([w["W"] for w in results], [30, 90, 180, 270, 365])
        for w in results:
            self.assertTrue(w["adequate"], msg=f"W={w['W']} not adequate")
            self.assertEqual(w["label"], "SIGN_POSITIVE", msg=f"W={w['W']} label")
            self.assertGreater(w["n_high"], 0)
            self.assertGreater(w["n_low"], 0)
        by_w = {w["W"]: w for w in results}
        self.assertEqual(by_w[30]["n_high"], 95)
        self.assertEqual(by_w[30]["n_low"], 134)
        self.assertAlmostEqual(
            by_w[30]["high_low_diff_net_1x"], 0.3147853837979608, places=12
        )
        self.assertAlmostEqual(
            by_w[30]["delta_fraction_vs_full"], -0.7732329918694754, places=12
        )
        self.assertEqual(by_w[365]["n_high"], 61)
        self.assertEqual(by_w[365]["n_low"], 90)
        self.assertAlmostEqual(
            by_w[365]["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )
        self.assertAlmostEqual(
            by_w[365]["delta_fraction_vs_full"], -0.9958744782509185, places=12
        )

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        self.assertEqual(_sha256(mod.BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["baseline"]["high_low_diff_net_1x"],
            self.fresh["baseline"]["high_low_diff_net_1x"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped overall label) must not equal a
        # fresh recomputation, so the committed-disk comparison is sensitive to
        # drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["overall_label"] = (
            "ROLLING_ROBUST"
            if self.committed["overall_label"] != "ROLLING_ROBUST"
            else "ROLLING_FRAGILE"
        )
        self.assertNotEqual(tampered["overall_label"], self.fresh["overall_label"])

        # A single perturbed per-window diff must also diverge from the fresh run.
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["window_results"][0]["high_low_diff_net_1x"] += 1.0
        self.assertNotEqual(
            tampered2["window_results"][0]["high_low_diff_net_1x"],
            self.fresh["window_results"][0]["high_low_diff_net_1x"],
        )

        # A block whose formations are perturbed must be REJECTED by the W=365
        # anchor reproduction gate (main returns nonzero), proving the pipeline
        # genuinely reads and validates the real committed block rather than
        # rubber-stamping it. The real block file is only read, never written.
        block = _load(mod.BLOCK_PATH)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            old_block, old_dir, old_out = mod.BLOCK_PATH, mod.OUT_DIR, mod.OUT_PATH
            try:
                mod.BLOCK_PATH = drift_block
                mod.OUT_DIR = Path(tmp)
                mod.OUT_PATH = Path(tmp) / "audit.json"
                rc = mod.main()
            finally:
                mod.BLOCK_PATH, mod.OUT_DIR, mod.OUT_PATH = old_block, old_dir, old_out
        self.assertNotEqual(
            rc, 0,
            msg="a block that does not reproduce the W=365 anchor must be rejected",
        )


if __name__ == "__main__":
    unittest.main()