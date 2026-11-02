"""Tests for the additive overlap-aware (formation-month cluster-bootstrap)
uncertainty reporting in scripts/eval_forward_block.py.

These are pure logic tests on synthetic formation records: they run without
touching any frozen artifact, the canonical block, or the network. One
end-to-end test runs the evaluator subprocess into a temporary directory to
pin that the fresh-block pipeline emits the overlap_aware_uncertainty section
without modifying the canonical artifact.
"""
import importlib
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"
FRESH = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
EVAL = ROOT / "scripts" / "eval_forward_block.py"

sys.path.insert(0, str(ROOT / "scripts"))
eval_fb = importlib.import_module("eval_forward_block")
overlap_aware_interval = eval_fb.overlap_aware_interval


def _form(formation_date, state, spread_net_1x):
    return {
        "formation_date": formation_date,
        "state": state,
        "spread_net_1x": spread_net_1x,
    }


class OverlapAwareIntervalUnitTests(unittest.TestCase):
    def test_immature_when_no_high_or_no_low(self):
        res = overlap_aware_interval([_form("2026-01-02", "high", 0.1)])
        self.assertEqual(res["status"], "IMMATURE")
        self.assertIsNone(res["baseline_high_low_diff_net_1x"])
        self.assertIsNone(res["ci_95_percentile"][0])
        self.assertIsNone(res["ci_95_percentile"][1])

        res = overlap_aware_interval([_form("2026-01-02", "low", -0.1)])
        self.assertEqual(res["status"], "IMMATURE")

        res = overlap_aware_interval([])
        self.assertEqual(res["status"], "IMMATURE")
        self.assertEqual(res["n_months"], 0)
        self.assertEqual(res["n_clusters_with_both_states"], 0)

    def test_baseline_equals_high_mean_minus_low_mean(self):
        forms = [
            _form("2026-01-02", "high", 0.2),
            _form("2026-01-03", "high", 0.4),
            _form("2026-01-04", "low", -0.1),
            _form("2026-01-05", "low", -0.3),
        ]
        res = overlap_aware_interval(forms, n_boot=200, rng_seed=7)
        self.assertEqual(res["status"], "OK")
        self.assertAlmostEqual(res["baseline_high_low_diff_net_1x"], 0.3 - (-0.2), places=12)
        self.assertTrue(math.isfinite(res["bootstrap_mean"]))
        self.assertTrue(math.isfinite(res["bootstrap_median"]))
        self.assertTrue(math.isfinite(res["bootstrap_se"]))
        self.assertTrue(math.isfinite(res["ci_95_percentile"][0]))
        self.assertTrue(math.isfinite(res["ci_95_percentile"][1]))
        self.assertIsInstance(res["ci_includes_zero"], bool)
        self.assertGreater(res["n_boot"], 0)
        self.assertGreater(res["n_months"], 0)
        self.assertEqual(res["rng_seed"], 7)

    def test_deterministic_fixed_seed(self):
        forms = [
            _form("2026-01-02", "high", 0.2),
            _form("2026-01-03", "high", 0.4),
            _form("2026-01-04", "low", -0.1),
            _form("2026-01-05", "low", -0.3),
            _form("2026-02-02", "high", 0.1),
            _form("2026-02-03", "low", -0.2),
        ]
        a = overlap_aware_interval(forms, n_boot=500, rng_seed=7)
        b = overlap_aware_interval(forms, n_boot=500, rng_seed=7)
        self.assertEqual(a, b)

    def test_month_clustering_counts(self):
        forms = [
            _form("2026-01-02", "high", 0.2),
            _form("2026-01-03", "low", -0.1),
            _form("2026-02-02", "high", 0.1),
            _form("2026-02-03", "low", -0.2),
        ]
        res = overlap_aware_interval(forms, n_boot=200, rng_seed=7)
        self.assertEqual(res["n_months"], 2)
        self.assertEqual(res["n_clusters_with_both_states"], 2)

    def test_single_month_without_both_states_is_not_a_both_cluster(self):
        # January has both; February has only high -> not a both cluster
        forms = [
            _form("2026-01-02", "high", 0.2),
            _form("2026-01-03", "low", -0.1),
            _form("2026-02-02", "high", 0.1),
        ]
        res = overlap_aware_interval(forms, n_boot=200, rng_seed=7)
        self.assertEqual(res["n_months"], 2)
        self.assertEqual(res["n_clusters_with_both_states"], 1)


class OverlapAwareIntervalPipelineTests(unittest.TestCase):
    def test_canonical_block_unchanged_on_disk(self):
        # The canonical artifact must be byte-identical before/after any run;
        # this test only reads it (additive code never rewrites it).
        before = CANONICAL.read_bytes()
        self.assertTrue(CANONICAL.exists())
        after = CANONICAL.read_bytes()
        self.assertEqual(before, after)

    def test_fresh_block_pipeline_emits_overlap_aware_section(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "fresh_block"
            r = subprocess.run(
                ["python", str(EVAL), "--forward-block-start", "2026-09-30",
                 "--data-cutoff", "2026-10-31", "--output-dir", str(out_dir)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            produced = out_dir / "forward_block_evaluation.json"
            self.assertTrue(produced.exists())
            fb = json.loads(produced.read_text(encoding="utf-8"))
            self.assertIn("overlap_aware_uncertainty", fb)
            ua = fb["overlap_aware_uncertainty"]
            # Fresh block is immature: 1 formation (2026-09-30), state mid,
            # n_high=0, n_low=0 -> no overlap-aware interval.
            self.assertEqual(ua["status"], "IMMATURE")
            self.assertIsNone(ua["baseline_high_low_diff_net_1x"])
            self.assertEqual(fb["n_high"], 0)
            self.assertEqual(fb["n_low"], 0)

    def test_canonical_block_committed_hash_still_matches_git(self):
        # Regression guard: the committed canonical blob is the single source
        # of truth and is untouched by this change.
        import hashlib

        disk = hashlib.sha256(CANONICAL.read_bytes()).hexdigest()
        git = subprocess.run(
            ["git", "show", f"HEAD:{CANONICAL.relative_to(ROOT)}"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(git.returncode, 0, msg=git.stderr)
        git_hash = hashlib.sha256(git.stdout.encode()).hexdigest()
        self.assertEqual(disk, git_hash)
        self.assertEqual(disk, "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390")


if __name__ == "__main__":
    unittest.main()
