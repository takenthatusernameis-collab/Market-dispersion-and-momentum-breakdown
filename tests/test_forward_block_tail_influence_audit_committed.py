"""Committed-disk verdict pin for scripts/forward_block_tail_influence.py (DISP-003-TAILAUDIT-001).

The static suite (test_forward_block_tail_influence.py) only checks the committed
artifact's INTERNAL self-consistency (its label matches its own thresholds, its
baseline matches the canonical block header) -- nothing re-derives the committed
artifact's load-bearing tail-sensitivity numbers (trimming / winsorization /
single-formation leave-one-out deltas, state stats, tail-concentration shares)
from the REAL committed canonical block. If that committed artifact drifted, was
truncated, or was written against a different block, no test would catch it -- the
same single-source-of-truth hazard the committed-disk pins for the
state-representativeness (DISP-003-STATEAUDIT-001), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38), expanding-universe (H33),
point-in-time-eligibility (H57), final-integrity and H10-fresh-integrity audits
already close.

This module re-runs the SAME read-only audit pipeline (``main``) against the
committed canonical block, redirecting OUT_PATH to a temp file so the committed
artifact is never written, and pins the committed artifact's load-bearing fields
(label, status, baseline, state counts/stats, trimming/winsorization/LOO deltas,
decision thresholds) to that fresh recomputation. Only ``computed_utc`` is allowed
to differ between the committed artifact and a fresh run. Read-only; path constants
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
SPEC_PATH = ROOT / "scripts" / "forward_block_tail_influence.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_forward_block_tail_influence_20261029.json"
)

spec = importlib.util.spec_from_file_location("tail_influence_committed", SPEC_PATH)
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
    """Run the audit against ``block_path`` with OUT_PATH redirected to a temp file.

    The committed artifact is never written: only a temporary OUT_PATH is used and
    the module global is restored in ``finally``. Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_out = Path(tmp) / "audit.json"
        old_block, old_out = mod.BLOCK_PATH, mod.OUT_PATH
        try:
            mod.BLOCK_PATH = block_path
            mod.OUT_PATH = tmp_out
            rc = mod.main()
        finally:
            mod.BLOCK_PATH, mod.OUT_PATH = old_block, old_out
        if rc != 0:
            raise AssertionError("tail-influence audit main() returned a nonzero exit code")
        return _load(tmp_out)


class CommittedTailInfluenceAuditVerdictTests(unittest.TestCase):
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
        self.assertEqual(res["conclusion"], "TAIL_ROBUST")
        self.assertEqual(res["decision_rule"]["label"], "TAIL_ROBUST")
        self.assertEqual(
            res["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-TAILAUDIT-001",
        )
        self.assertEqual(
            res["audit_id"], "H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_20261029"
        )

    def test_committed_artifact_matches_fresh_recomputation(self):
        # The whole artifact must be reproduced from the committed canonical block;
        # only computed_utc (a wall-clock timestamp) is allowed to differ.
        c = dict(self.committed)
        f = dict(self.fresh)
        c.pop("computed_utc", None)
        f.pop("computed_utc", None)
        self.assertEqual(
            c, f,
            msg="committed tail-influence audit drifted from a fresh recomputation "
            "against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["baseline_high_low_diff_net_1x"], 0.6165223953929935)
        self.assertEqual(c["n_formations"], 608)
        self.assertEqual(c["state_counts"], {"high": 61, "low": 90, "mid": 457})
        self.assertEqual(c["date_first"], "2025-01-01")
        self.assertEqual(c["date_last"], "2026-08-31")
        self.assertEqual(c["data_cutoff_utc"], "2026-09-30T00:00:00Z")
        self.assertAlmostEqual(
            c["state_stats"]["high"]["mean"], 0.539961300958885, places=12
        )
        self.assertEqual(c["state_stats"]["high"]["n"], 61)
        self.assertAlmostEqual(
            c["state_stats"]["low"]["mean"], -0.07656109443410872, places=12
        )
        self.assertEqual(c["state_stats"]["low"]["n"], 90)
        self.assertAlmostEqual(
            c["trimming"]["k_3"]["delta_frac_vs_baseline"],
            -0.10990402177240673,
            places=12,
        )
        self.assertAlmostEqual(
            c["winsorization"]["p_0.1"]["delta_frac_vs_baseline"],
            -0.10862518974594956,
            places=12,
        )
        loo = c["single_formation_leave_one_out"]
        self.assertEqual(loo["n_formations_tested"], 151)
        self.assertAlmostEqual(
            loo["max_abs_delta_frac_vs_baseline"], 0.06233636196005241, places=12
        )
        rule = c["decision_rule"]
        self.assertEqual(rule["trim_k3_threshold_frac"], 0.20)
        self.assertEqual(rule["winsor_p010_threshold_frac"], 0.20)
        self.assertEqual(rule["loo_threshold_frac"], 0.10)
        self.assertEqual(rule["label"], "TAIL_ROBUST")
        self.assertEqual(c["conclusion"], "TAIL_ROBUST")

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
        # A tampered committed artifact (a flipped label) must not equal a fresh
        # recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["decision_rule"]["label"] = (
            "TAIL_SENSITIVE"
            if self.committed["decision_rule"]["label"] != "TAIL_SENSITIVE"
            else "TAIL_ROBUST"
        )
        self.assertNotEqual(
            tampered["decision_rule"]["label"],
            self.fresh["decision_rule"]["label"],
        )

        # A block whose high-state spreads are perturbed must move a RECOMPUTED
        # field, proving the pin is a real constraint on the committed canonical
        # block and not a rubber stamp. The baseline is copied from the block
        # header, but state_stats/trimming means are recomputed from the formations,
        # so they must move. The real block file is only read, never written.
        block = _load(mod.BLOCK_PATH)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory() as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            drifted = _run_with_block(drift_block)
        self.assertNotEqual(
            drifted["state_stats"]["high"]["mean"],
            self.committed["state_stats"]["high"]["mean"],
        )
        self.assertNotEqual(
            drifted["trimming"]["k_3"]["delta_frac_vs_baseline"],
            self.committed["trimming"]["k_3"]["delta_frac_vs_baseline"],
        )


if __name__ == "__main__":
    unittest.main()