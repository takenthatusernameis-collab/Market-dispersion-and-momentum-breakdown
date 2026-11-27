"""Committed-disk verdict pin for scripts/forward_block_cluster_bootstrap.py
(DISP-003-FORWARD-BLOCK-CLUSTER-BOOTSTRAP, H004V106 forward block).

The static suite (test_forward_block_cluster_bootstrap.py) only checks the
committed artifact's INTERNAL self-consistency and a few finiteness properties
(artifact exists, does not modify the canonical block, baseline matches the
canonical block header, bootstrap values finite) -- nothing re-derives the
committed artifact's load-bearing cluster-bootstrap numbers (per-month
high-minus-low diffs, effective independent-cluster count, bootstrap mean/median/
SE, percentile CI, ci_includes_zero) from the REAL committed canonical block. If
that committed artifact drifted, was truncated, or was written against a
different block, no test would catch it -- the same single-source-of-truth hazard
the committed-disk pins for the state-representativeness (DISP-003-STATEAUDIT-001),
maturity-timeline (H35), independent-recomputation (H37), frozen-tree (H38),
expanding-universe (H33), point-in-time-eligibility (H57), final-integrity,
H10-fresh-integrity and tail-influence audits already close.

This module re-runs the SAME read-only audit pipeline (``main``) against the
committed canonical block, redirecting OUT_PATH to a temp file so the committed
artifact is never written, and pins the committed artifact's load-bearing fields
(status, baseline, formation/month/cluster counts, bootstrap distribution, CI,
per-month diffs) to that fresh recomputation. Only ``computed_utc`` is allowed to
differ between the committed artifact and a fresh run. Read-only; path constants
are derived from ``__file__`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_cluster_bootstrap.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_forward_block_cluster_bootstrap_20261029.json"
)

spec = importlib.util.spec_from_file_location("cluster_bootstrap_committed", SPEC_PATH)
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


def _run_with_block(block_path: Path, root: Path | None = None):
    """Run the audit against ``block_path`` with OUT_PATH redirected to a temp file.

    The committed artifact is never written: only a temporary OUT_PATH is used and
    the module globals are restored in ``finally``. ``root`` optionally overrides
    the module ROOT so a drift block written outside the repo tree still satisfies
    the script's ``BLOCK_PATH.relative_to(ROOT)`` audited_artifact derivation.
    Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_out = Path(tmp) / "audit.json"
        old_block, old_out, old_root = mod.BLOCK_PATH, mod.OUT_PATH, mod.ROOT
        try:
            mod.BLOCK_PATH = block_path
            mod.OUT_PATH = tmp_out
            if root is not None:
                mod.ROOT = root
            mod.main()
        finally:
            mod.BLOCK_PATH, mod.OUT_PATH, mod.ROOT = old_block, old_out, old_root
        return _load(tmp_out)


class CommittedClusterBootstrapAuditVerdictTests(unittest.TestCase):
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

    def test_fresh_audit_identity_and_status(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
        )
        self.assertEqual(
            res["audit_id"], "H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_20261029"
        )
        self.assertEqual(
            res["audited_artifact"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        )
        self.assertEqual(res["data_cutoff_utc"], "2026-09-30T00:00:00Z")

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed canonical block;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed cluster-bootstrap audit drifted from a fresh recomputation "
            "against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["n_formations"], 608)
        self.assertEqual(c["n_months"], 20)
        self.assertEqual(c["n_clusters_with_both_states"], 2)
        self.assertEqual(c["date_first"], "2025-01-01")
        self.assertEqual(c["date_last"], "2026-08-31")
        # Baseline is recomputed from the per-formation spreads (mean high - mean
        # low); it differs from the block header in the last digit because the
        # header value is stored independently of this recomputation.
        self.assertAlmostEqual(
            c["baseline_high_low_diff_net_1x"], 0.6165223953929937, places=12
        )
        self.assertEqual(c["n_boot"], 1999)
        self.assertEqual(c["rng_seed"], 20261029)
        self.assertAlmostEqual(
            c["bootstrap_mean"], 0.5238509947544793, places=12
        )
        self.assertAlmostEqual(
            c["bootstrap_median"], 0.5734807428121175, places=12
        )
        self.assertAlmostEqual(c["bootstrap_se"], 0.37459041702928986, places=12)
        self.assertEqual(len(c["ci_95_percentile"]), 2)
        self.assertAlmostEqual(
            c["ci_95_percentile"][0], -0.11788862432121286, places=12
        )
        self.assertAlmostEqual(
            c["ci_95_percentile"][1], 1.1431406242679565, places=12
        )
        self.assertTrue(c["ci_includes_zero"])
        self.assertEqual(len(c["month_level_diffs"]), 20)

    def test_frozen_hash_matches_committed_artifact(self):
        # The audit reads the committed canonical block; pin its sha256 to an
        # independent literal so a swapped block is caught even if the committed
        # artifact were regenerated to match it.
        self.assertEqual(_sha256(mod.BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(
            self.committed["baseline_high_low_diff_net_1x"],
            self.fresh["baseline_high_low_diff_net_1x"],
        )

    def test_synthetic_drift_is_detected(self):
        # A tampered committed artifact (a flipped status) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["status"] = (
            "CONFIRMATORY"
            if self.committed["status"] != "CONFIRMATORY"
            else "EXPLORATORY_ONLY"
        )
        self.assertNotEqual(tampered["status"], self.fresh["status"])

        # A block whose high-state spreads are perturbed must move a RECOMPUTED
        # field, proving the pin is a real constraint on the committed canonical
        # block and not a rubber stamp. The baseline is recomputed from the
        # formations, so adding to a single high spread must move it. The real
        # block file is only read, never written.
        block = _load(mod.BLOCK_PATH)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory() as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            drifted = _run_with_block(drift_block, root=Path(tmp))
        self.assertNotEqual(
            drifted["baseline_high_low_diff_net_1x"],
            self.committed["baseline_high_low_diff_net_1x"],
        )


if __name__ == "__main__":
    unittest.main()