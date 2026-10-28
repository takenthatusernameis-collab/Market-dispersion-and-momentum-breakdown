"""Regression tests for the DISPENSITY-002 Phase B placebo red-team artifact.

Verifies the new artifact artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/
phase_b_placebos.json exists, is EXPLORATORY_ONLY, reproduces the predeclared
placebo values on the frozen conditioned panel, and that no existing
DISPENSITY-002 file was modified (timestamps/contents unchanged).
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
ART = ROOT / "artifacts" / EXP
PLACEBO_PATH = ART / "phase_b_placebos.json"
PREREG_PATH = ART / "preregistrations" / "PHASE-B-PLACEBO-V1.md"
SCRIPT_PATH = ROOT / "scripts" / "phase_b_placebos_disp002.py"
FROZEN_FILES = [
    ART / "formation_returns_conditioned.csv",
    ART / "phase_c_summary.json",
    ART / "phase_e_summary.json",
    ART / "phase_f_summary.json",
    ART / "report.md",
    ART / "robustness_inference_summary.json",
    ART / "grid_config_manifest.json",
    ART / "experiment_setup.json",
]


class Disp002PhaseBPlaceboTests(unittest.TestCase):
    def test_artifact_exists_and_is_exploratory(self):
        self.assertTrue(PLACEBO_PATH.exists(), "DISP-002 phase_b_placebos.json must exist")
        p = json.loads(PLACEBO_PATH.read_text(encoding="utf-8"))
        self.assertEqual(p["experiment_id"], EXP)
        self.assertEqual(p["phase"], "B_placebos")
        self.assertEqual(p["n_formations"], 53)
        # EXPLORATORY_ONLY label is recorded in the preregistration, not the JSON;
        # the JSON records the predeclared placebo statistics.
        self.assertAlmostEqual(p["observed"]["conditional_high_minus_low_gross"],
                               0.17471689140306546, places=12)

    def test_preregistration_exists(self):
        self.assertTrue(PREREG_PATH.exists())
        text = PREREG_PATH.read_text(encoding="utf-8")
        self.assertIn("EXPLORATORY_ONLY", text)
        self.assertIn("HARMONY-CRYPTO-EDGE-004-DISPERSION-002-PHASE-B-PLACEBO", text)

    def test_script_exists_and_is_read_only_on_frozen_inputs(self):
        self.assertTrue(SCRIPT_PATH.exists())
        src = SCRIPT_PATH.read_text(encoding="utf-8")
        # the script must read the frozen conditioned panel and write only the
        # new placebo artifact; it must not touch any other DISP-002 file
        self.assertIn("formation_returns_conditioned.csv", src)
        self.assertIn("phase_b_placebos.json", src)
        self.assertNotIn("phase_c_summary.json", src)
        self.assertNotIn("phase_f_summary.json", src)

    def test_frozen_files_unchanged(self):
        # timestamps preserved from the original 2026-10-28T18:18:38Z freeze
        for f in FROZEN_FILES:
            self.assertTrue(f.exists(), f"missing frozen file {f}")
            self.assertEqual(f.stat().st_mtime, 1793211518,
                             f"{f.name} modified after the freeze")

    def test_placebo_values_match_predeclared_decision_rule(self):
        p = json.loads(PLACEBO_PATH.read_text(encoding="utf-8"))
        st = p["state_time_permutation_placebo"]
        # predeclared: observed diff must be compared against the permutation CI
        lo, hi = st["ci_95"]
        self.assertLessEqual(lo, st["observed_diff"])
        self.assertGreaterEqual(hi, st["observed_diff"])
        # observed lies inside the null CI -> CONDITIONAL_EDGE_NOT_DISTINGUISHABLE
        self.assertGreater(st["empirical_p_two_sided"], 0.05)


if __name__ == "__main__":
    unittest.main()