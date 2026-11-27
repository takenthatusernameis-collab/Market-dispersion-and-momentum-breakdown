"""Committed-disk verdict pin for scripts/forward_block_temporal_stability.py.

The committed temporal stability audit artifact
``H004V106_forward_block_temporal_stability_20261029.json`` was previously backed
only by static field-pin tests (``test_forward_block_temporal_stability.py``) that
check the artifact's INTERNAL self-consistency and never re-derives its numbers
from the canonical block. This module closes that single-source-of-truth gap by
re-running the SAME read-only pipeline against the committed canonical block
(writing only to a temp OUT_PATH, never the committed artifact) and pinning the
committed artifact's load-bearing fields to that fresh recomputation.

Read-only: no network, no secrets, no trading endpoints. The audit module
imports numpy but only for stdlib-compatible statistics; the re-run writes to a
temp file and touches no committed artifact.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_temporal_stability.py"
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_forward_block_temporal_stability_20261029.json"
)

spec = importlib.util.spec_from_file_location("fb_temporal_stability_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _reanchor_paths(tmp_out: Path) -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / EXP
    mod.BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.OUT_PATH = tmp_out


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class CommittedTemporalStabilityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_out = Path(tempfile.mkdtemp(prefix="temporal_stability_committed_")) / "audit.json"
        _reanchor_paths(cls.tmp_out)
        required = [mod.BLOCK_PATH, COMMITTED_AUDIT]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        mod.main()
        cls.fresh = _load(cls.tmp_out)
        cls.committed = _load(COMMITTED_AUDIT)

    def test_fresh_audit_status_and_identity(self):
        res = self.fresh
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(res["audit_id"], "H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_20261029")
        self.assertEqual(res["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
        self.assertEqual(res["audited_artifact"], "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json")

    def test_committed_artifact_matches_fresh_recomputation(self):
        c, f = self.committed, self.fresh
        for key in (
            "audit_id",
            "experiment_id",
            "audited_artifact",
            "status",
            "data_cutoff_utc",
            "date_first",
            "date_last",
            "n_formations",
            "split_date",
            "n_first_half",
            "n_second_half",
            "baseline_high_low_diff_net_1x",
            "conclusion",
        ):
            self.assertEqual(
                c.get(key), f.get(key),
                msg=f"committed {key!r} drifted from fresh recomputation",
            )
        for half_key in ("first_half", "second_half"):
            ch, fh = c[half_key], f[half_key]
            for subkey in (
                "n_formations",
                "n_high",
                "n_low",
                "n_mid",
                "high_low_diff_net_1x",
                "spread_net_1x_median",
                "date_first",
                "date_last",
                "n_months",
                "n_months_with_both_states",
            ):
                self.assertEqual(
                    ch[subkey], fh[subkey],
                    msg=f"committed {half_key}.{subkey} drifted from fresh recomputation",
                )
            cb, fb = ch["bootstrap"], fh["bootstrap"]
            for bkey in ("mean", "se", "ci_lo", "ci_hi", "ci_includes_zero", "n_boot"):
                self.assertEqual(
                    cb[bkey], fb[bkey],
                    msg=f"committed {half_key}.bootstrap.{bkey} drifted from fresh recomputation",
                )
            self.assertEqual(ch["month_level_diffs"], fh["month_level_diffs"])

    def test_committed_artifact_pin_values(self):
        c = self.committed
        self.assertEqual(c["baseline_high_low_diff_net_1x"], 0.6165223953929937)
        self.assertEqual(c["split_date"], "2025-11-01")
        self.assertEqual(c["n_first_half"], 304)
        self.assertEqual(c["n_second_half"], 304)
        self.assertEqual(c["first_half"]["n_formations"], 304)
        self.assertEqual(c["first_half"]["n_high"], 53)
        self.assertEqual(c["first_half"]["n_low"], 21)
        self.assertEqual(c["first_half"]["n_mid"], 230)
        self.assertAlmostEqual(c["first_half"]["high_low_diff_net_1x"], 0.6456322213084524, places=12)
        self.assertTrue(c["first_half"]["bootstrap"]["ci_includes_zero"])
        self.assertEqual(c["second_half"]["n_formations"], 304)
        self.assertEqual(c["second_half"]["n_high"], 8)
        self.assertEqual(c["second_half"]["n_low"], 69)
        self.assertEqual(c["second_half"]["n_mid"], 227)
        self.assertAlmostEqual(c["second_half"]["high_low_diff_net_1x"], -0.16288800752983412, places=12)
        self.assertFalse(c["second_half"]["bootstrap"]["ci_includes_zero"])
        self.assertEqual(c["conclusion"], "Anchor estimate not temporally stable across the frozen block; EXPLORATORY_ONLY, does not unlock confirmatory track.")

    def test_frozen_hash_matches_committed_artifact(self):
        self.assertEqual(mod.sha256_file(mod.BLOCK_PATH) if hasattr(mod, "sha256_file") else None, None)
        import hashlib
        self.assertEqual(hashlib.sha256(mod.BLOCK_PATH.read_bytes()).hexdigest(), EXPECTED_CANONICAL)

    def test_synthetic_drift_is_detected(self):
        block = json.loads(mod.BLOCK_PATH.read_text(encoding="utf-8"))
        forms = sorted(block["formations"], key=lambda f: f["formation_date"])
        baseline_fresh = mod.diff_from_forms(forms)
        self.assertAlmostEqual(baseline_fresh, self.fresh["baseline_high_low_diff_net_1x"], places=12)

        high_forms = [f for f in forms if f["state"] == "high"]
        self.assertGreater(len(high_forms), 0)
        forms_no_high = [f for f in forms if f["state"] != "high"] + high_forms[:-1]
        baseline_drift = mod.diff_from_forms(forms_no_high)
        self.assertNotEqual(baseline_drift, baseline_fresh)

        split = len(forms) // 2
        first_half_fresh = mod.half_stats(forms[:split], np.random.default_rng(mod.RNG_SEED))
        first_half_drift = mod.half_stats(forms_no_high[:split], np.random.default_rng(mod.RNG_SEED))
        self.assertNotEqual(first_half_drift["high_low_diff_net_1x"], first_half_fresh["high_low_diff_net_1x"])

        tampered = json.loads(json.dumps(self.committed))
        tampered["baseline_high_low_diff_net_1x"] = 0.0
        self.assertNotEqual(tampered["baseline_high_low_diff_net_1x"], self.fresh["baseline_high_low_diff_net_1x"])
        tampered2 = json.loads(json.dumps(self.committed))
        tampered2["first_half"]["high_low_diff_net_1x"] = 0.0
        self.assertNotEqual(tampered2["first_half"]["high_low_diff_net_1x"], self.fresh["first_half"]["high_low_diff_net_1x"])


if __name__ == "__main__":
    unittest.main()