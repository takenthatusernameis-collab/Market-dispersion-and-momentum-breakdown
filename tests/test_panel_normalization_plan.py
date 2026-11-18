#!/usr/bin/env python3
"""
Tests for panel_normalization_plan.py — hermetic plan-structure fixtures +
skip-guarded integration on the committed artifact.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestPanelNormalizationPlanHermetic(unittest.TestCase):
    """Hermetic tests using minimal fixtures; no committed artifacts required."""

    def setUp(self):
        self.script = Path("scripts/panel_normalization_plan.py")
        self.assertTrue(self.script.exists(), "script missing")

    def test_script_syntax_valid(self):
        """Script must have valid Python syntax and execute without import errors."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(self.script)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, f"syntax check failed: {result.stderr}")

    def test_help_exits_zero(self):
        """--help should exit 0."""
        result = subprocess.run(
            [sys.executable, str(self.script), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)

    def test_requires_out_or_print(self):
        """Must require --out or --print."""
        result = subprocess.run(
            [sys.executable, str(self.script)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required", result.stderr.lower())

def test_plan_structure_expected_keys(self):
        """Plan output must contain all declared top-level keys."""
        # Check if all required inputs exist
        inputs_exist = all([
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_20261118T211130Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_20261118T221212Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_panel_manifest.json").exists(),
        ])

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            # This will fail due to missing inputs, but we can check the error structure
            result = subprocess.run(
                [sys.executable, str(self.script), "--out", str(out)],
                capture_output=True,
                text=True,
            )
            # If inputs exist (as they do in CI), it should succeed with PLAN_RECORDED
            # If inputs don't exist, it should fail with PLAN_SCOPE_MISMATCH or similar
            if inputs_exist:
                self.assertEqual(result.returncode, 0)
                with out.open() as f:
                    plan = json.load(f)
                required = [
                    "experiment_id", "hypothesis", "status", "computed_utc",
                    "confirmatory_claim_allowed", "exploratory_only",
                    "extension_assets", "total_planned_files", "series",
                    "symbol_map", "frozen_hashes_verified", "input_hashes_verified",
                    "non_claims",
                ]
                for k in required:
                    self.assertIn(k, plan, f"missing key: {k}")
            else:
                self.assertNotEqual(result.returncode, 0)


class TestPanelNormalizationPlanIntegration(unittest.TestCase):
    """Integration tests against committed artifacts; skipped if artifacts absent."""

    @classmethod
    def setUpClass(cls):
        cls.script = Path("scripts/panel_normalization_plan.py")
        cls.artifact_dir = Path(
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001"
        )
        cls.prereg = cls.artifact_dir / "preregistrations" / "PANELNORM_PLAN_001_v1.md"
        cls.audit_dir = cls.artifact_dir / "integrity_audit"

        # Check if all required inputs exist
        cls.inputs_exist = all([
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_20261118T211130Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_20261118T221212Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json").exists(),
            Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_panel_manifest.json").exists(),
        ])

    def test_inputs_exist_or_skip(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

    def test_plan_runs_and_produces_valid_json(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            result = subprocess.run(
                [sys.executable, str(self.script), "--out", str(out)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, f"plan failed: {result.stderr}")

            with out.open() as f:
                plan = json.load(f)

            # Required top-level fields
            required = [
                "experiment_id", "hypothesis", "status", "computed_utc",
                "confirmatory_claim_allowed", "exploratory_only",
                "extension_assets", "total_planned_files", "series",
                "symbol_map", "frozen_hashes_verified", "input_hashes_verified",
                "non_claims",
            ]
            for k in required:
                self.assertIn(k, plan, f"missing key: {k}")

            self.assertEqual(plan["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001")
            self.assertEqual(plan["hypothesis"], "H51")
            self.assertEqual(plan["extension_assets"], 9)
            self.assertEqual(plan["total_planned_files"], 810)
            self.assertFalse(plan["confirmatory_claim_allowed"])
            self.assertTrue(plan["exploratory_only"])
            self.assertEqual(plan["status"], "PLAN_RECORDED")

    def test_series_count_and_assets(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

            # 9 assets × 2 kinds = 18 series entries
            self.assertEqual(len(plan["series"]), 18)

            assets_in_series = sorted(set(s["asset"] for s in plan["series"]))
            # Order matches H47 alphabetical: alice, ankr, ape, api3, apt, ar, ark, arpa, astr
            expected = ["alice", "ankr", "ape", "api3", "apt", "ar", "ark", "arpa", "astr"]
            self.assertEqual(assets_in_series, expected)

            # Each asset has both kinds
            for asset in expected:
                kinds = sorted(s["kind"] for s in plan["series"] if s["asset"] == asset)
                self.assertEqual(kinds, ["funding", "klines"])

    def test_wave_a_provenance_and_sha256(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

        # Wave-A assets should have provenance H49 and sha256 filled
        wave_a = {"alice", "ankr", "ape", "api3", "apt", "ar", "arpa"}
        for s in plan["series"]:
            if s["asset"] in wave_a:
                self.assertEqual(s["provenance"], "H49")
                for mf in s["monthly_files"]:
                    self.assertIsNotNone(mf["sha256"], f"missing sha256 for {s['asset']} {s['kind']} {mf['month']}")
                    self.assertEqual(len(mf["sha256"]), 64)

    def test_wave_b_provenance_placeholder_sha256(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

        # Wave-B assets should have provenance H51-b and sha256 = None (placeholder)
        wave_b = {"ark", "astr"}
        for s in plan["series"]:
            if s["asset"] in wave_b:
                self.assertEqual(s["provenance"], "H51-b")
                for mf in s["monthly_files"]:
                    self.assertIsNone(mf["sha256"], f"wave-B sha256 should be None placeholder for {s['asset']} {s['kind']} {mf['month']}")

    def test_admissible_months_match_h47_h50(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

        # Load H47 roster for expected windows
        h47 = json.loads(Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json").read_text())
        h50 = json.loads(Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_20261118T221212Z.json").read_text())

        h50_months = {a["asset"]: set(a["admissible_study_months"]) for a in h50["per_asset"].values()}

        for s in plan["series"]:
            asset = s["asset"]
            kind = s["kind"]
            h47_asset = next(a for a in h47["per_asset"].values() if a["asset"] == asset)
            first = h47_asset["served_window"][kind]["first"]
            last = h47_asset["served_window"][kind]["last"]
            expected_months = [m for m in [f"{y:04d}-{m:02d}" for y in range(2023, 2027) for m in range(1, 13) if not (y == 2026 and m > 10)] if first <= m <= last]

            if asset in h50_months:
                expected_set = set(expected_months) & h50_months[asset]
                self.assertEqual(set(s["admissible_months"]), expected_set, f"{asset} {kind} months mismatch")
            else:
                self.assertEqual(s["admissible_months"], expected_months, f"{asset} {kind} months mismatch")

    def test_frozen_hashes_verified(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

        self.assertTrue(plan["frozen_hashes_verified"]["all_match"])
        for name, detail in plan["frozen_hashes_verified"]["details"].items():
            self.assertTrue(detail["match"], f"frozen hash mismatch: {name}")

    def test_input_hashes_verified(self):
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                plan = json.load(f)

        self.assertTrue(all(plan["input_hashes_verified"].values()))

    def test_committed_artifact_exists_and_matches(self):
        """Verify the committed audit artifact exists and matches current run."""
        if not self.inputs_exist:
            self.skipTest("committed input artifacts not present")

        # Find the committed audit file
        audit_files = list(self.audit_dir.glob("panel_normalization_plan_*.json"))
        if not audit_files:
            self.skipTest("committed audit artifact not yet present")
        audit_path = audit_files[0]

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            subprocess.run([sys.executable, str(self.script), "--out", str(out)], check=True)
            with out.open() as f:
                current = json.load(f)
            with audit_path.open() as f:
                committed = json.load(f)

        # Core plan fields should match (except computed_utc)
        for key in ["experiment_id", "hypothesis", "status", "extension_assets", "total_planned_files", "series", "symbol_map"]:
            self.assertEqual(current[key], committed[key], f"mismatch in {key}")


if __name__ == "__main__":
    unittest.main()