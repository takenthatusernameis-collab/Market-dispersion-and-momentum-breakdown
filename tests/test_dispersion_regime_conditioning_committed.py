"""Committed-disk verdict pin for scripts/dispersion_regime_conditioning.py (DISP-003-REGIME-001).

The static suite (test_dispersion_regime_conditioning.py) only checks the committed
artifact's INTERNAL self-consistency (its labels match its own recomputed thresholds,
its decile buckets sum to the header count) -- nothing re-derives the committed
artifact's load-bearing numbers from the REAL committed canonical forward block. If
that committed artifact drifted, was truncated, or was written against a different
canonical block, no test would catch it -- the same single-source-of-truth hazard the
committed-disk pins for the state-representativeness (H40), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38), expanding-universe (H33),
final-integrity and H10-fresh-integrity audits already close.

This module re-runs the SAME read-only audit pipeline against the committed canonical
block (writing only to a temp path under the repository root, never the committed
artifact, because ``main()`` prints ``OUT_PATH.relative_to(ROOT)``) and pins the
committed artifact's load-bearing fields (status, baseline header, continuous-
association label/rho, regime-split label/median, 2025-10 conditioning delta, decile
bucket count/coverage, conclusion) to that fresh recomputation. Only ``computed_utc``
(a wall-clock timestamp) is allowed to differ between the committed artifact and a
fresh run. Read-only and stdlib-only (the audit module imports no numpy/pandas); path
constants are re-anchored to the repository root in ``setUpClass`` so the test is
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
SPEC_PATH = ROOT / "scripts" / "dispersion_regime_conditioning.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_dispersion_regime_conditioning_20261028.json"
)

spec = importlib.util.spec_from_file_location("regime_conditioning_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copy of the frozen canonical hash so a coordinated change to a frozen
# artifact still fails even if a module constant were edited.
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.OUT_PATH = (
        art / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json"
    )


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _run_with_block(block_path: Path):
    """Run the audit against ``block_path`` with OUT_PATH redirected to a temp file.

    The temp file is created under ROOT (not the system temp dir) because ``main()``
    ends with ``OUT_PATH.relative_to(ROOT)``; a path outside ROOT would raise. The
    committed artifact is never written: only a temporary OUT_PATH is used and the
    module globals are restored in ``finally``. Returns the parsed fresh output.
    """
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        tmp_out = Path(tmp) / "audit.json"
        old_block, old_out = mod.BLOCK_PATH, mod.OUT_PATH
        try:
            mod.BLOCK_PATH = block_path
            mod.OUT_PATH = tmp_out
            rc = mod.main()
        finally:
            mod.BLOCK_PATH, mod.OUT_PATH = old_block, old_out
        if rc != 0:
            raise AssertionError("regime-conditioning main() returned a nonzero exit code")
        return _load(tmp_out)


class CommittedDispersionRegimeConditioningVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
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
        self.assertEqual(
            res["experiment_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-REGIME-001",
        )
        self.assertEqual(
            res["audit_id"], "H004V106_DISPERSION_REGIME_CONDITIONING_20261028"
        )
        self.assertEqual(
            res["A_continuous_dispersion_spread_association"]["label"],
            "WEAK_CONTINUOUS_ASSOCIATION",
        )
        self.assertEqual(
            res["B_dispersion_regime_split"]["label"],
            "REGIME_SPARSE_OR_SIGN_FLIP",
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
            msg="committed dispersion-regime-conditioning audit drifted from a fresh "
            "recomputation against the committed canonical block",
        )

    def test_committed_artifact_pin_values(self):
        c = self.committed
        b = c["baseline"]
        self.assertEqual(b["n_formations"], 608)
        self.assertEqual(b["n_high"], 61)
        self.assertEqual(b["n_low"], 90)
        self.assertEqual(b["n_mid"], 457)
        self.assertEqual(b["date_first"], "2025-01-01")
        self.assertEqual(b["date_last"], "2026-08-31")
        self.assertEqual(b["data_cutoff_utc"], "2026-09-30T00:00:00Z")
        self.assertAlmostEqual(
            b["high_low_diff_net_1x"], 0.6165223953929935, places=12
        )
        cont = c["A_continuous_dispersion_spread_association"]
        self.assertEqual(cont["label"], "WEAK_CONTINUOUS_ASSOCIATION")
        self.assertAlmostEqual(
            cont["excluding_2025_10"]["spearman_rho"], -0.1528563204260193, places=12
        )
        regime = c["B_dispersion_regime_split"]
        self.assertEqual(regime["label"], "REGIME_SPARSE_OR_SIGN_FLIP")
        self.assertAlmostEqual(
            regime["median_dispersion"], 0.12242231649895832, places=12
        )
        self.assertAlmostEqual(
            c["C_2025_10_conditioning"]["delta_fraction_vs_baseline"],
            -0.8487210159492462,
            places=12,
        )
        buckets = c["D_dispersion_decile_buckets"]["buckets"]
        self.assertEqual(c["D_dispersion_decile_buckets"]["n_buckets"], 10)
        self.assertEqual(len(buckets), 10)
        self.assertEqual(sum(bk["n"] for bk in buckets), 608)

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
        # A tampered committed artifact (a flipped regime label) must not equal a
        # fresh recomputation, so the committed-disk comparison is sensitive to drift.
        tampered = json.loads(json.dumps(self.committed))
        tampered["B_dispersion_regime_split"]["label"] = (
            "REGIME_ROBUST"
            if self.committed["B_dispersion_regime_split"]["label"]
            != "REGIME_ROBUST"
            else "REGIME_SPARSE_OR_SIGN_FLIP"
        )
        self.assertNotEqual(
            tampered["B_dispersion_regime_split"]["label"],
            self.fresh["B_dispersion_regime_split"]["label"],
        )

        # A block whose high-state spreads are perturbed must move a RECOMPUTED
        # field, proving the pin is a real constraint on the committed canonical
        # block and not a rubber stamp. The baseline is copied from the block
        # header, but the all-formations high-minus-low diff (C.with_2025_10) is
        # recomputed from the formations, so perturbing one high-state spread must
        # move it. The real block file is only read, never written.
        block = _load(mod.BLOCK_PATH)
        for row in block["formations"]:
            if row["state"] == "high":
                row["spread_net_1x"] = row["spread_net_1x"] + 1.0
                break
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            drift_block = Path(tmp) / "block.json"
            drift_block.write_text(json.dumps(block), encoding="utf-8")
            drifted = _run_with_block(drift_block)
        self.assertNotEqual(
            drifted["C_2025_10_conditioning"]["with_2025_10"][
                "high_low_diff_net_1x"
            ],
            self.committed["C_2025_10_conditioning"]["with_2025_10"][
                "high_low_diff_net_1x"
            ],
        )


if __name__ == "__main__":
    unittest.main()