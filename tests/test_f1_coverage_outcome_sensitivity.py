#!/usr/bin/env python3
"""Regression guards for the F1 coverage-outcome sensitivity arm.

DISP-003-F1SENS-002 (``scripts/f1_coverage_outcome_sensitivity.py``) measures
whether the frozen H004V106 anchor formation outcome changes when the four
F1-repaired assets are added, over the identical sealed canonical window. It is
an EXPLORATORY_ONLY descriptive sensitivity, not a hypothesis test.

The preregistration
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002/preregistrations/F1_COVERAGE_OUTCOME_SENSITIVITY_v1.md``
promised a regression guard (sec 6, item 3). This file supplies it.

Guards (all stdlib/local, no network, no market evidence beyond the committed
panels):
  1. The script imports the unmodified evaluator functions and reproduces the
     committed canonical block exactly (fidelity), so the sensitivity is measured
     on the same arithmetic as the frozen block.
  2. The script never writes to the committed panels or either frozen block
     (source pins NEW paths and only reads OLD panels).
  3. The committed audit reports verdict PASS, EXPLORATORY_ONLY, fidelity pass,
     unchanged committed panels and unchanged frozen artifacts.
  4. The committed audit's arm A reproduces the frozen block's canonical fields.
"""
import hashlib
import json
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "f1_coverage_outcome_sensitivity.py"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002"
OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
CANONICAL_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block" / "forward_block_evaluation.json"
AUDIT_DIR = ROOT / "artifacts" / NEW_EXP / "integrity_audit"

FROZEN = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}


def _load_module():
    spec = util.spec_from_file_location("f1_coverage_outcome_sensitivity", str(SCRIPT))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestF1SensitivityConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_new_experiment_id_is_single_prefixed_and_distinct(self):
        self.assertEqual(self.mod.NEW_EXP, NEW_EXP)
        self.assertEqual(self.mod.NEW_EXP.count("HARMONY-CRYPTO-EDGE-004-"), 1)
        self.assertNotEqual(self.mod.NEW_EXP, self.mod.OLD_EXP)

    def test_output_paths_are_isolated_from_committed_experiment(self):
        old_root = ROOT / "artifacts" / self.mod.OLD_EXP
        for path in (self.mod.AUDIT_DIR,):
            self.assertTrue(path.is_relative_to(ROOT / "artifacts" / self.mod.NEW_EXP))

    def test_script_never_writes_to_committed_panels(self):
        src = SCRIPT.read_text(encoding="utf-8")
        # The only writes are to AUDIT_DIR / an explicit --out path.
        self.assertIn("AUDIT_DIR.mkdir", src)
        self.assertNotIn("OLD_PANELS", "".join(
            ln for ln in src.splitlines() if "write" in ln.lower()
        ))

    def test_frozen_hash_constants_match_committed_artifacts(self):
        self.assertTrue(self.mod.FROZEN_HASHES)
        for rel, expected in self.mod.FROZEN_HASHES.items():
            p = ROOT / "artifacts" / self.mod.OLD_EXP / rel
            self.assertTrue(p.exists(), f"missing frozen artifact {rel}")
            self.assertEqual(_sha256_file(p), expected)


class TestF1SensitivityFidelity(unittest.TestCase):
    """Recompute arm A and require it to reproduce the committed block."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.block = json.loads(CANONICAL_BLOCK.read_text(encoding="utf-8"))
        mc = cls.mod.ef.load_marketcap()
        px = cls.mod.ef.load_binance_panel("klines")
        cls.arm_a = cls.mod.evaluate(px, mc)
        cls.fid = cls.mod.fidelity_check(cls.arm_a, cls.block)

    def test_arm_a_reproduces_frozen_block(self):
        self.assertTrue(self.fid["pass"], self.fid)
        self.assertEqual(self.arm_a["n_formations"], self.block["n_formations"])
        self.assertEqual(self.arm_a["n_high"], self.block["n_high"])
        self.assertEqual(self.arm_a["n_low"], self.block["n_low"])
        self.assertAlmostEqual(
            self.arm_a["high_low_diff_net_1x"],
            self.block["high_low_diff_net_1x"], places=12,
        )


class TestF1SensitivityCommittedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.audits = sorted(AUDIT_DIR.glob("f1_coverage_outcome_sensitivity_*.json"))

    def test_committed_audit_exists(self):
        self.assertTrue(self.audits, "no committed F1 sensitivity audit found")

    def test_latest_audit_is_well_formed(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        self.assertEqual(latest["experiment_id"], self.mod.NEW_EXP)
        self.assertEqual(latest["verdict"], "PASS")
        self.assertEqual(latest["status"], "EXPLORATORY_ONLY")
        self.assertTrue(latest["fidelity_check"]["pass"])
        checks = latest["read_only_checks"]
        self.assertTrue(checks["old_panels_byte_unchanged"])
        self.assertTrue(all(v["match"] for v in checks["frozen_artifacts"].values()))
        self.assertFalse(latest["disposition"]["frozen_artifacts_modified"])
        self.assertFalse(latest["disposition"]["old_panels_modified"])

    def test_latest_audit_arm_a_matches_frozen_block(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        block = json.loads(CANONICAL_BLOCK.read_text(encoding="utf-8"))
        arm_a = latest["arm_a_committed"]
        self.assertEqual(arm_a["n_formations"], block["n_formations"])
        self.assertEqual(arm_a["n_high"], block["n_high"])
        self.assertEqual(arm_a["n_low"], block["n_low"])
        self.assertAlmostEqual(arm_a["high_low_diff_net_1x"],
                               block["high_low_diff_net_1x"], places=12)

    def test_latest_audit_pins_both_frozen_blocks(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        frozen = latest["read_only_checks"]["frozen_artifacts"]
        self.assertEqual(set(frozen), set(self.mod.FROZEN_HASHES))
        for rel, entry in frozen.items():
            self.assertTrue(entry["match"], f"{rel} mismatch in committed audit")


if __name__ == "__main__":
    unittest.main()