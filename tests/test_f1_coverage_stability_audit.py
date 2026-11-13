#!/usr/bin/env python3
"""Regression guards for the F1 coverage stability audit.

DISP-003-F1STAB-003 (``scripts/f1_coverage_stability_audit.py``) measures whether
the H8 leave-one-month-out CLUSTER_DOMINATION and the H19 median-date
TEMPORAL-INSTABILITY verdicts on the canonical H004V106 estimate survive the
four-asset F1 coverage repair (26-27 -> 29-31 eligible assets). It is an
EXPLORATORY_ONLY descriptive stability measurement, not a hypothesis test.

The preregistration
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003/preregistrations/F1_COVERAGE_STABILITY_AUDIT_v1.md``
promised a regression guard (sec 6). This file supplies it.

Guards (all stdlib/local, no network, no market evidence beyond the committed
F1SENS-002 records):
  1. The script is isolated to a NEW experiment id and never writes to the
     committed experiment, the F1SENS source, the panels or either frozen block.
  2. Arm A reproduces H8 (2025-10 delta -0.849) and H19 (+0.6456 / -0.1629 at
     split 2025-11-01) and both baselines exactly (fidelity), so the arm B
     comparison is measured on the same records the frozen block used.
  3. The committed audit reports verdict PASS, EXPLORATORY_ONLY, fidelity pass,
     label F1_STABILITY_PRESERVED, unchanged F1SENS source, unchanged panels and
     unchanged frozen artifacts.
"""
import hashlib
import json
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "f1_coverage_stability_audit.py"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003"
OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
F1SENS_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002"
AUDIT_DIR = ROOT / "artifacts" / NEW_EXP / "integrity_audit"

FROZEN = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}


def _load_module():
    spec = util.spec_from_file_location("f1_coverage_stability_audit", str(SCRIPT))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestF1StabilityConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_new_experiment_id_is_single_prefixed_and_distinct(self):
        self.assertEqual(self.mod.NEW_EXP, NEW_EXP)
        self.assertEqual(self.mod.NEW_EXP.count("HARMONY-CRYPTO-EDGE-004-"), 1)
        self.assertNotEqual(self.mod.NEW_EXP, self.mod.OLD_EXP)
        self.assertNotEqual(self.mod.NEW_EXP, self.mod.F1SENS_EXP)

    def test_output_paths_are_isolated_from_committed_experiment(self):
        for path in (self.mod.AUDIT_DIR,):
            self.assertTrue(path.is_relative_to(ROOT / "artifacts" / self.mod.NEW_EXP))
        # Component-wise, not a raw string prefix: the new id extends the old id
        # textually, so only a path-component check proves real isolation.
        self.assertFalse(self.mod.AUDIT_DIR.is_relative_to(ROOT / "artifacts" / self.mod.OLD_EXP))

    def test_script_never_writes_to_committed_panels_or_frozen_blocks(self):
        src = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("AUDIT_DIR.mkdir", src)
        # The only write target is AUDIT_DIR / an explicit --out path.
        self.assertNotIn("OLD_PANELS", "".join(
            ln for ln in src.splitlines() if "write" in ln.lower()
        ))
        self.assertNotIn("FROZEN_HASHES", "".join(
            ln for ln in src.splitlines() if "write" in ln.lower()
        ))

    def test_frozen_hash_constants_match_committed_artifacts(self):
        self.assertTrue(self.mod.FROZEN_HASHES)
        for rel, expected in self.mod.FROZEN_HASHES.items():
            p = ROOT / "artifacts" / self.mod.OLD_EXP / rel
            self.assertTrue(p.exists(), f"missing frozen artifact {rel}")
            self.assertEqual(_sha256_file(p), expected)


class TestF1StabilityFidelity(unittest.TestCase):
    """Recompute both arms and require arm A to reproduce H8/H19 exactly."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        src = json.loads(cls.mod._latest_f1sens_artifact().read_text(encoding="utf-8"))
        cls.arm_a = cls.mod.analyze_arm(src["arm_a_committed"]["formations"])
        cls.arm_b = cls.mod.analyze_arm(src["arm_b_repaired"]["formations"])
        cls.fid = cls.mod.fidelity_check(cls.arm_a, cls.arm_b)

    def test_fidelity_check_passes(self):
        self.assertTrue(self.fid["pass"], self.fid)

    def test_arm_a_reproduces_canonical_baseline(self):
        self.assertAlmostEqual(
            self.arm_a["baseline_high_low_diff_net_1x"],
            self.mod.CANONICAL_BASELINE, places=12,
        )

    def test_arm_a_reproduces_h8_cluster_domination(self):
        loo = self.arm_a["leave_one_month_out"]
        self.assertTrue(loo["cluster_dominated"])
        self.assertEqual(loo["max_abs_month"], "2025-10")
        self.assertAlmostEqual(
            loo["months"]["2025-10"]["delta_frac_vs_baseline"],
            self.mod.H8_2025_10_DELTA_FRAC, places=6,
        )

    def test_arm_a_reproduces_h19_temporal_instability(self):
        split = self.arm_a["temporal_split"]
        self.assertEqual(split["split_date"], self.mod.H19_SPLIT_DATE)
        self.assertTrue(split["temporal_instability"])
        self.assertAlmostEqual(
            split["first_half"]["high_low_diff_net_1x"], self.mod.H19_FIRST_DIFF, places=12,
        )
        self.assertAlmostEqual(
            split["second_half"]["high_low_diff_net_1x"], self.mod.H19_SECOND_DIFF, places=12,
        )
        self.assertEqual(
            (split["first_half"]["n_high"], split["first_half"]["n_low"]),
            self.mod.H19_FIRST_COUNTS,
        )
        self.assertEqual(
            (split["second_half"]["n_high"], split["second_half"]["n_low"]),
            self.mod.H19_SECOND_COUNTS,
        )

    def test_arm_b_baseline_matches_f1sens(self):
        self.assertAlmostEqual(
            self.arm_b["baseline_high_low_diff_net_1x"],
            self.mod.F1SENS_ARM_B_BASELINE, places=12,
        )

    def test_arm_b_still_cluster_dominated_and_temporally_unstable(self):
        loo = self.arm_b["leave_one_month_out"]
        self.assertTrue(loo["cluster_dominated"])
        self.assertEqual(loo["max_abs_month"], "2025-10")
        self.assertGreater(loo["max_abs_delta_frac"], self.mod.THRESHOLD_FRAC)
        self.assertTrue(self.arm_b["temporal_split"]["temporal_instability"])


class TestF1StabilityCommittedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.audits = sorted(AUDIT_DIR.glob("f1_coverage_stability_audit_*.json"))

    def test_committed_audit_exists(self):
        self.assertTrue(self.audits, "no committed F1 stability audit found")

    def test_latest_audit_is_well_formed(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        self.assertEqual(latest["experiment_id"], self.mod.NEW_EXP)
        self.assertEqual(latest["hypothesis"], "H25")
        self.assertEqual(latest["verdict"], "PASS")
        self.assertEqual(latest["status"], "EXPLORATORY_ONLY")
        self.assertTrue(latest["fidelity_check"]["pass"])
        self.assertEqual(latest["comparison"]["label"], "F1_STABILITY_PRESERVED")

    def test_latest_audit_read_only_checks_are_clean(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        checks = latest["read_only_checks"]
        self.assertTrue(checks["old_panels_byte_unchanged"])
        self.assertTrue(checks["old_panels_match_f1sens_recorded_hashes"])
        self.assertTrue(checks["f1sens_source_byte_unchanged"])
        self.assertTrue(all(v["match"] for v in checks["frozen_artifacts"].values()))
        self.assertFalse(latest["disposition"]["frozen_artifacts_modified"])
        self.assertFalse(latest["disposition"]["old_panels_modified"])
        self.assertFalse(latest["disposition"]["f1sens_source_modified"])

    def test_latest_audit_pins_both_frozen_blocks(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        frozen = latest["read_only_checks"]["frozen_artifacts"]
        self.assertEqual(set(frozen), set(self.mod.FROZEN_HASHES))
        for rel, entry in frozen.items():
            self.assertTrue(entry["match"], f"{rel} mismatch in committed audit")


if __name__ == "__main__":
    unittest.main()