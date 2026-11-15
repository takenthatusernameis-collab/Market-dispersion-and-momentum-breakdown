"""Hermetic tests for scripts/h10_fresh_block_integrity_audit.py pure seams.

Tests the audit logic on synthetic data without reading any committed artifacts.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import h10_fresh_block_integrity_audit as h10_audit


class H10FreshBlockIntegrityAuditSeamTests(unittest.TestCase):
    def setUp(self):
        # Synthetic canonical block matching the H10 fresh structure
        self.canonical_block = {
            "audit_id": "H004V106_H10_FRESH_FORWARD_BLOCK_INTEGRITY_AUDIT",
            "n_formations": 1,
            "n_high": 0,
            "n_low": 0,
            "n_mid": 1,
            "high_low_diff_net_1x": None,
            "high_low_diff_gross": None,
            "spread_net_1x_mean": -0.048729065266337745,
            "spread_net_1x_median": -0.048729065266337745,
            "spread_gross_mean": -0.047729065266337745,
            "spread_gross_median": -0.047729065266337745,
            "high_net_1x_mean": None,
            "low_net_1x_mean": None,
            "high_gross_mean": None,
            "low_gross_mean": None,
            "date_first": "2026-09-30",
            "date_last": "2026-09-30",
            "block_sealed": True,
            "data_cutoff_utc": "2026-10-31T00:00:00Z",
            "last_allowed_formation_date": "2026-09-30",
            "eligible_assets_per_date": {"mean": 26.0, "min": 26, "max": 26},
            "min_completed_forward_horizon_days": 30,
            "min_state_formations": 5,
            "state_count_floor_met": False,
            "economic_significance_threshold": 0.05,
            "economic_significance_met": False,
            "confirmatory_claim_allowed": False,
            "sequential_look_number": 1,
            "sequential_alpha_k": 0.025,
            "sequential_cumulative_spend": 0.025,
            "sequential_remaining_budget": 0.025,
            "block_sealing_rule": "first_formation_ge_min_date_and_forward_horizon_complete",
            "forward_block_start": "2026-09-30",
            "forward_block_end": "2026-09-30",
            "input_file_hashes": {
                "binance_klines_BTCUSDT.csv": "abc123",
                "grid_result_ledger.json": "def456",
            },
            "overlap_aware_uncertainty": {
                "status": "IMMATURE",
                "reason": "need n_high>0 and n_low>0 for overlap-aware interval",
                "n_boot": 0,
                "n_clusters_with_both_states": 0,
                "n_months": 0,
                "rng_seed": 20261102,
            },
        }

        # Synthetic recomputed block
        self.recomputed = {
            "n_formations": 1,
            "state_counts": {"high": 0, "low": 0, "mid": 1},
            "n_assets_min": 26,
            "n_assets_max": 26,
            "finite_dispersion_count": 1,
            "non_finite_dispersion_count": 0,
            "spread_net_mean_recomputed": -0.048729065266337745,
            "spread_net_median_recomputed": -0.048729065266337745,
            "spread_gross_mean_recomputed": -0.047729065266337745,
            "spread_gross_median_recomputed": -0.047729065266337745,
            "high_net_mean_recomputed": None,
            "low_net_mean_recomputed": None,
            "high_low_diff_net_recomputed": None,
            "high_gross_mean_recomputed": None,
            "low_gross_mean_recomputed": None,
            "high_low_diff_gross_recomputed": None,
            "date_first": "2026-09-30",
            "date_last": "2026-09-30",
            "formation_records": [{
                "formation_date": "2026-09-30",
                "dispersion": 0.19716600141456223,
                "n_assets": 26,
                "top_ret": 0.0,
                "bot_ret": 0.047729065266337745,
                "spread_gross": -0.047729065266337745,
                "spread_net_1x": -0.048729065266337745,
                "state": "mid",
            }],
        }

    def test_finite_value_checks_all_finite(self):
        """All finite values pass the check."""
        result = h10_audit.finite_value_checks(self.recomputed["formation_records"])
        self.assertTrue(result["all_finite"])
        self.assertEqual(result["offending_count"], 0)
        self.assertEqual(result["offending"], [])

    def test_finite_value_checks_nan_dispersion(self):
        """NaN dispersion is detected."""
        formations = [dict(self.recomputed["formation_records"][0])]
        formations[0]["dispersion"] = float("nan")
        result = h10_audit.finite_value_checks(formations)
        self.assertFalse(result["all_finite"])
        self.assertEqual(result["offending_count"], 1)
        self.assertEqual(result["offending"][0]["field"], "dispersion")

    def test_finite_value_checks_inf_spread_net(self):
        """Infinite spread_net_1x is detected."""
        formations = [dict(self.recomputed["formation_records"][0])]
        formations[0]["spread_net_1x"] = float("inf")
        result = h10_audit.finite_value_checks(formations)
        self.assertFalse(result["all_finite"])
        self.assertEqual(result["offending_count"], 1)
        self.assertEqual(result["offending"][0]["field"], "spread_net_1x")

    def test_finite_value_checks_none_spread_gross(self):
        """None spread_gross is detected."""
        formations = [dict(self.recomputed["formation_records"][0])]
        formations[0]["spread_gross"] = None
        result = h10_audit.finite_value_checks(formations)
        self.assertFalse(result["all_finite"])
        self.assertEqual(result["offending_count"], 1)
        self.assertEqual(result["offending"][0]["field"], "spread_gross")

    def test_cost_treatment_check_consistent(self):
        """Cost treatment net = gross - 0.001 is consistent."""
        result = h10_audit.cost_treatment_check(self.recomputed["formation_records"])
        self.assertTrue(result["net_equals_gross_minus_cost"])
        self.assertEqual(result["cost_1x"], 0.001)
        self.assertEqual(result["violations"], [])

    def test_cost_treatment_check_violation(self):
        """Cost treatment violation is detected."""
        formations = [dict(self.recomputed["formation_records"][0])]
        formations[0]["spread_net_1x"] = -0.05  # wrong: should be -0.048729...
        result = h10_audit.cost_treatment_check(formations)
        self.assertFalse(result["net_equals_gross_minus_cost"])
        self.assertEqual(len(result["violations"]), 1)
        self.assertEqual(result["violations"][0]["formation_date"], "2026-09-30")

    def test_state_consistency_check_clean(self):
        """Clean canonical and recomputed blocks pass state consistency."""
        result = h10_audit.state_consistency_check(self.canonical_block, self.recomputed)
        self.assertTrue(result["all_consistent"])
        self.assertEqual(result["issues"], [])

    def test_state_consistency_check_n_high_mismatch(self):
        """n_high mismatch is detected."""
        canonical = dict(self.canonical_block)
        canonical["n_high"] = 1
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("n_high mismatch" in i for i in result["issues"]))

    def test_state_consistency_check_n_low_mismatch(self):
        """n_low mismatch is detected."""
        canonical = dict(self.canonical_block)
        canonical["n_low"] = 1
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("n_low mismatch" in i for i in result["issues"]))

    def test_state_consistency_check_high_low_diff_should_be_null(self):
        """high_low_diff should be null when n_high=0 or n_low=0."""
        canonical = dict(self.canonical_block)
        canonical["high_low_diff_net_1x"] = 0.01  # should be null
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("high_low_diff_net_1x should be null" in i for i in result["issues"]))

    def test_state_consistency_check_high_gross_mean_should_be_null(self):
        """high_gross_mean should be null when n_high=0."""
        canonical = dict(self.canonical_block)
        canonical["high_gross_mean"] = 0.01
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("high_gross_mean should be null" in i for i in result["issues"]))

    def test_state_consistency_check_block_sealed_false(self):
        """block_sealed false is detected."""
        canonical = dict(self.canonical_block)
        canonical["block_sealed"] = False
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("block_sealed should be true" in i for i in result["issues"]))

    def test_state_consistency_check_sequential_look_number_wrong(self):
        """Wrong sequential_look_number is detected."""
        canonical = dict(self.canonical_block)
        canonical["sequential_look_number"] = 2
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("sequential_look_number should be 1" in i for i in result["issues"]))

    def test_state_consistency_check_confirmatory_claim_allowed_true(self):
        """confirmatory_claim_allowed true is detected (should be false for IMMATURE)."""
        canonical = dict(self.canonical_block)
        canonical["confirmatory_claim_allowed"] = True
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("confirmatory_claim_allowed should be false" in i for i in result["issues"]))

    def test_state_consistency_check_overlap_aware_status_wrong(self):
        """Wrong overlap_aware_uncertainty status is detected."""
        canonical = dict(self.canonical_block)
        canonical["overlap_aware_uncertainty"] = dict(canonical["overlap_aware_uncertainty"])
        canonical["overlap_aware_uncertainty"]["status"] = "OK"
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("overlap_aware_uncertainty.status should be IMMATURE" in i for i in result["issues"]))

    def test_state_consistency_check_overlap_aware_reason_missing(self):
        """Missing reason in overlap_aware_uncertainty is detected."""
        canonical = dict(self.canonical_block)
        canonical["overlap_aware_uncertainty"] = dict(canonical["overlap_aware_uncertainty"])
        canonical["overlap_aware_uncertainty"]["reason"] = "some other reason"
        result = h10_audit.state_consistency_check(canonical, self.recomputed)
        self.assertFalse(result["all_consistent"])
        self.assertTrue(any("overlap_aware_uncertainty.reason should mention n_high>0 and n_low>0" in i for i in result["issues"]))

    def test_reconcile_inputs_mock(self):
        """Input hash reconciliation works with mocked file system."""
        with patch("h10_fresh_block_integrity_audit.efb") as mock_efb:
            # Setup mock panel directory
            mock_panel_dir = MagicMock()
            mock_efb.PANEL_DIR = mock_panel_dir

            # Setup mock ART directory
            mock_art_dir = MagicMock()
            mock_efb.ART = mock_art_dir

            # Create mock file objects that can be sorted (by name)
            class MockFile:
                def __init__(self, name):
                    self.name = name
                def is_file(self):
                    return True
                def __lt__(self, other):
                    return self.name < other.name

            # Mock file iteration - return list of MockFile objects for panel dir
            mock_panel_files = [
                MockFile("binance_klines_BTCUSDT.csv"),
                MockFile("other_panel_file.txt"),  # some other panel file
            ]
            mock_panel_dir.iterdir.return_value = mock_panel_files

            # Mock the two specific files from ART directory
            mock_grid_config = MockFile("grid_config_manifest.json")
            mock_grid_result = MockFile("grid_result_ledger.json")
            mock_art_dir.__truediv__ = lambda self, name: {
                "grid_config_manifest.json": mock_grid_config,
                "grid_result_ledger.json": mock_grid_result,
            }.get(name)

            # Mock sha256_file
            with patch("h10_fresh_block_integrity_audit.sha256_file") as mock_sha256:
                mock_sha256.side_effect = lambda p: {
                    "binance_klines_BTCUSDT.csv": "abc123",
                    "other_panel_file.txt": "other_hash",
                    "grid_config_manifest.json": "ghi789",
                    "grid_result_ledger.json": "def456",
                }.get(p.name, "unknown")

                canonical = {
                    "input_file_hashes": {
                        "binance_klines_BTCUSDT.csv": "abc123",
                        "other_panel_file.txt": "other_hash",
                        "grid_config_manifest.json": "ghi789",
                        "grid_result_ledger.json": "def456",
                    }
                }
                result = h10_audit.reconcile_inputs(canonical)
                self.assertEqual(result["recorded_hash_count"], 4)
                self.assertEqual(result["on_disk_hash_count"], 4)
                self.assertTrue(result["all_match"])
                self.assertTrue(result["per_file"]["binance_klines_BTCUSDT.csv"]["match"])

    def test_reconcile_inputs_mismatch(self):
        """Input hash mismatch is detected."""
        with patch("h10_fresh_block_integrity_audit.efb") as mock_efb:
            mock_panel_dir = MagicMock()
            mock_efb.PANEL_DIR = mock_panel_dir
            mock_efb.ART = MagicMock()

            mock_file1 = MagicMock()
            mock_file1.name = "binance_klines_BTCUSDT.csv"
            mock_file1.is_file.return_value = True

            mock_panel_dir.iterdir.return_value = [mock_file1]

            with patch("h10_fresh_block_integrity_audit.sha256_file") as mock_sha256:
                mock_sha256.side_effect = lambda p: {
                    "binance_klines_BTCUSDT.csv": "different_hash",
                    "grid_result_ledger.json": "def456",
                    "grid_config_manifest.json": "ghi789",
                }.get(p.name, "unknown")

                canonical = {
                    "input_file_hashes": {
                        "binance_klines_BTCUSDT.csv": "abc123",
                        "grid_result_ledger.json": "def456",
                        "grid_config_manifest.json": "ghi789",
                    }
                }
                result = h10_audit.reconcile_inputs(canonical)
                self.assertFalse(result["all_match"])
                self.assertFalse(result["per_file"]["binance_klines_BTCUSDT.csv"]["match"])


if __name__ == "__main__":
    unittest.main()