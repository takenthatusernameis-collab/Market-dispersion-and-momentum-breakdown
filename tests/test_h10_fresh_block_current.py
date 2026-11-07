"""Regression guard for the H10 fresh sealed forward block.

The committed artifact at
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/
forward_block_evaluation.json was produced by an older build of
scripts/eval_forward_block.py that did not yet emit the additive
overlap_aware_uncertainty section. The durable state therefore claimed
"idempotent re-run verified byte-identical" against code that no longer
reproduces the artifact, and H10's preregistration (sec 3 step 6) requires the
overlap-aware section to be present.

This test pins the committed H10 fresh block against the CURRENT evaluator:
it must (a) carry the overlap_aware_uncertainty section, (b) reproduce its
outcome fields from a fresh subprocess run into a throwaway directory, and
(c) leave the canonical H004V106 block untouched. It is a build guard, not a
claim about the economic result: the block is intentionally IMMATURE
(n_high=0, n_low=0) and may never be promoted.

Pure stdlib + subprocess; no network, no frozen artifact modified.
"""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"
FRESH = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
EVAL = ROOT / "scripts" / "eval_forward_block.py"

CANONICAL_SHA = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"


def _has_module(name: str) -> bool:
    """dep-light probe: True when the named module imports."""
    try:
        __import__(name)
        return True
    except Exception:
        return False


class H10FreshBlockCurrentGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fb = json.loads(FRESH.read_text(encoding="utf-8"))

    def test_committed_block_carries_overlap_aware_uncertainty(self):
        # H10 prereg sec 3 step 6: HAC/overlap-aware uncertainty must be
        # reported. A block predating that code path is stale, not canonical.
        self.assertIn("overlap_aware_uncertainty", self.fb)
        ua = self.fb["overlap_aware_uncertainty"]
        self.assertEqual(ua["status"], "IMMATURE")
        self.assertEqual(
            ua["reason"], "need n_high>0 and n_low>0 for overlap-aware interval"
        )

    def test_committed_block_is_immature_with_expected_fields(self):
        # Outcome fields must match the frozen, pre-declared H10 configuration.
        self.assertEqual(self.fb["status"], "OK")
        self.assertEqual(self.fb["forward_block_start"], "2026-09-30")
        self.assertEqual(self.fb["forward_block_end"], "2026-09-30")
        self.assertEqual(self.fb["data_cutoff_utc"], "2026-10-31T00:00:00Z")
        self.assertEqual(self.fb["last_allowed_formation_date"], "2026-09-30")
        self.assertEqual(self.fb["n_formations"], 1)
        self.assertEqual(self.fb["n_high"], 0)
        self.assertEqual(self.fb["n_low"], 0)
        self.assertEqual(self.fb["n_mid"], 1)
        self.assertIsNone(self.fb["high_low_diff_net_1x"])
        self.assertIsNone(self.fb["high_low_diff_gross"])
        self.assertGreaterEqual(self.fb["eligible_assets_per_date"]["min"], 20)
        self.assertTrue(self.fb["block_sealed"])
        self.assertEqual(len(self.fb["formations"]), 1)
        self.assertEqual(self.fb["formations"][0]["formation_date"], "2026-09-30")
        self.assertEqual(self.fb["formations"][0]["state"], "mid")
        self.assertEqual(self.fb["evaluated_utc"], "2026-11-02T15:18:56Z")

    def test_committed_block_carries_confirmatory_gate_fields(self):
        # H10 prereg sec 4.2 declares confirmatory-gate fields in the fresh block.
        # The block is IMMATURE (n_high=0, n_low=0) so claim is disallowed and
        # Holm significance is pending caller evaluation.
        self.assertIn("confirmatory_claim_allowed", self.fb)
        self.assertFalse(self.fb["confirmatory_claim_allowed"])
        self.assertIn("confirmatory_holm_significant", self.fb)
        self.assertIsNone(self.fb["confirmatory_holm_significant"])
        self.assertIn("economic_significance_met", self.fb)
        self.assertFalse(self.fb["economic_significance_met"])
        self.assertEqual(self.fb["economic_significance_threshold"], 0.05)
        self.assertIn("high_low_diff_net_1x_abs", self.fb)
        self.assertIsNone(self.fb["high_low_diff_net_1x_abs"])
        self.assertEqual(self.fb["min_state_formations"], 5)
        self.assertIn("state_count_floor_met", self.fb)
        self.assertFalse(self.fb["state_count_floor_met"])
        self.assertIn("confirmatory_note", self.fb)
        expected_prefix = (
            "gate: |high_low_diff_net_1x|=None >= 0.05 -> False; "
            "n_high=0>= 5 and n_low=0>=5 -> False; "
            "Holm-significance across the complete 216-cell family at alpha_k = 0.025 "
            "-> None (pending caller)"
        )
        self.assertTrue(
            self.fb["confirmatory_note"].startswith(expected_prefix),
            msg=f"confirmatory_note prefix mismatch: {self.fb['confirmatory_note']!r}",
        )

    @unittest.skipUnless(
        _has_module("numpy"), "scripts/eval_forward_block.py subprocess requires numpy"
    )
    def test_reproducibility_against_current_evaluator(self):
        # A fresh subprocess run must reproduce the committed outcome, overlap-aware,
        # and confirmatory-gate fields exactly. We seed the throwaway dir with the
        # committed artifact so the evaluator's no-op guard preserves evaluated_utc
        # (it preserves only when overwriting an existing file whose seal fields match).
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "h10_repro"
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(FRESH, out_dir / "forward_block_evaluation.json")
            r = subprocess.run(
                ["python", str(EVAL), "--forward-block-start", "2026-09-30",
                 "--data-cutoff", "2026-10-31", "--output-dir", str(out_dir),
                 "--look-number", "1"],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            produced = json.loads(
                (out_dir / "forward_block_evaluation.json").read_text(encoding="utf-8")
            )
            for key in (
                "forward_block_start", "forward_block_end", "data_cutoff_utc",
                "last_allowed_formation_date", "n_formations", "n_high", "n_low",
                "n_mid", "high_low_diff_net_1x", "high_low_diff_gross",
                "block_sealed", "block_sealing_rule", "evaluated_utc",
                "confirmatory_claim_allowed", "confirmatory_holm_significant",
                "confirmatory_note", "economic_significance_met",
                "economic_significance_threshold", "high_low_diff_net_1x_abs",
                "min_state_formations", "state_count_floor_met",
            ):
                self.assertEqual(
                    produced[key], self.fb[key],
                    msg=f"field {key!r} drifted from committed H10 fresh block",
                )
            self.assertEqual(
                produced["overlap_aware_uncertainty"],
                self.fb["overlap_aware_uncertainty"],
            )

    def test_canonical_block_untouched_and_hash_pinned(self):
        # The canonical H004V106 block is read-only input; this guard re-runs the
        # evaluator only into throwaway dirs, so the canonical file must be
        # byte-identical to the committed blob at all times.
        disk = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
        git = subprocess.run(
            ["git", "show", f"HEAD:{CANONICAL.relative_to(ROOT)}"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(git.returncode, 0, msg=git.stderr)
        git_hash = hashlib.sha256(git.stdout.encode()).hexdigest()
        self.assertEqual(disk, git_hash)
        self.assertEqual(disk, CANONICAL_SHA)


if __name__ == "__main__":
    unittest.main()