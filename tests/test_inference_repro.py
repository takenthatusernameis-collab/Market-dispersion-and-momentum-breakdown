"""Regression tests for scripts/fix_inference.py.

The committed inference script was a reproducibility hazard: it hardcoded
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001" while the artifacts it wrote
lived under DISPERSION-002, and it indexed phase_f["split"][split] (a list of
dates) which does not exist in the 002 schema. So the script as committed
could not have produced the artifacts it claimed to produce.

These tests pin the script to the 002 experiment and require that re-running
it reproduces the committed artifacts byte-for-byte.
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
ART = root / "artifacts" / EXP
SCRIPT = root / "scripts" / "fix_inference.py"
TARGET_FILES = ["phase_c_summary.json", "phase_f_summary.json"]


def _snapshot():
    tmp = Path(tempfile.mkdtemp())
    for name in TARGET_FILES:
        shutil.copy2(ART / name, tmp / name)
    return tmp


class InferenceRepro(unittest.TestCase):
    def setUp(self):
        self.snapshot = _snapshot()

    def tearDown(self):
        for name in TARGET_FILES:
            shutil.copy2(self.snapshot / name, ART / name)
        shutil.rmtree(self.snapshot, ignore_errors=True)

    def test_script_targets_correct_experiment(self):
        src = SCRIPT.read_text()
        self.assertIn('EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"', src)
        self.assertNotIn('EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-001"', src)

    def test_script_runs_clean(self):
        r = subprocess.run(
            ["python", str(SCRIPT)], cwd=root, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_artifacts_reproduced_byte_identical(self):
        """Re-running the script must not change the committed artifacts."""
        before = {n: (ART / n).read_bytes() for n in TARGET_FILES}
        r = subprocess.run(
            ["python", str(SCRIPT)], cwd=root, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        for n in TARGET_FILES:
            self.assertEqual((ART / n).read_bytes(), before[n])

    def test_diff_ci_is_not_degenerate(self):
        """The whole point of the fix: CIs must not collapse to a point."""
        pc = json.loads((ART / "phase_c_summary.json").read_text())
        pf = json.loads((ART / "phase_f_summary.json").read_text())
        hi, lo = pc["high_gross_ci_95_blockboot"], pc["low_gross_ci_95_blockboot"]
        self.assertNotEqual(hi[0], hi[1])
        self.assertNotEqual(lo[0], lo[1])
        # Difference CI is null because high/low states share no formation
        # date; that is the correct paired-bootstrap answer, not a bug.
        self.assertIsNone(pc["high_low_diff_ci_95_blockboot"][0])
        self.assertEqual(pc["inference_method"]["n_diff_observations"], 0)
        for split in ("discovery", "validation", "final"):
            self.assertIsNone(pf[split]["diff_gross_ci_95"][0])
            self.assertEqual(pf[split]["n_diff_observations"], 0)

    def test_phase_f_split_counts_match_formation_panel(self):
        """Split sizes must reconcile with the conditioned formation panel."""
        import pandas as pd
        cond = pd.read_csv(ART / "formation_returns_conditioned.csv")
        n = cond["formation_date"].nunique()
        pf = json.loads((ART / "phase_f_summary.json").read_text())
        s = pf["split"]
        self.assertEqual(s["discovery_n"] + s["validation_n"] + s["final_n"], n)
        self.assertEqual(
            pf["discovery"]["n"] + pf["validation"]["n"] + pf["final"]["n"], n
        )


if __name__ == "__main__":
    unittest.main()