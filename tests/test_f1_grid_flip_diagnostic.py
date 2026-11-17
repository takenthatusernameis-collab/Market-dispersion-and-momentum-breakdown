"""Regression tests for scripts/f1_grid_flip_diagnostic.py (H45, F1GRID-FLIP-001).

Hermetic tests build synthetic F1GRID-002-style ledgers and pin the predeclared
classification rule and flip detection. One integration test reads the committed
F1GRID-002 ledger when it is present on disk (it is git-ignored and large, so the
test skips cleanly when absent) and asserts the observed sole flip is H004V130,
classified MARGINAL_POINT_ESTIMATE_CHANGE with a single state transfer, matching
the committed grid_summary.json.

Read-only, stdlib-only: no network, no secrets, no trading endpoint.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "f1_grid_flip_diagnostic.py"

spec = importlib.util.spec_from_file_location("f1_grid_flip_diagnostic", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

LEDGER = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
    / "grid_result_ledger.json"
)
SUMMARY = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
    / "grid_summary.json"
)


def _cell(net, p, holm, n_high=100, n_low=100, n_mid=100, n_formations=300):
    return {
        "high_low_diff_net_1x": net,
        "pvalue_bootstrap_two_sided": p,
        "holm_rejected": holm,
        "n_formations": n_formations,
        "n_high": n_high,
        "n_low": n_low,
        "n_mid": n_mid,
        "universe_arm": "expanding_point_in_time",
        "parameters": {"forward_horizon_days": 60},
    }


def _ledger(cells_a, cells_b):
    return {
        "expected_cells": len(cells_a),
        "arms": {
            mod.ARM_A: {"cells": cells_a},
            mod.ARM_B: {"cells": cells_b},
        },
    }


class ClassifyCellTests(unittest.TestCase):
    def test_marginal_classification(self):
        a = _cell(0.35, 0.006, False, n_low=136, n_mid=1078)
        b = _cell(0.38, 0.0, True, n_low=135, n_mid=1079)
        out = mod.classify_cell(a, b)
        self.assertEqual(out["classification"], "MARGINAL_POINT_ESTIMATE_CHANGE")
        self.assertAlmostEqual(out["delta_high_low_diff_net_1x"], 0.03, places=12)
        self.assertEqual(out["delta_n_low"], -1)
        self.assertEqual(out["delta_n_mid"], 1)
        self.assertEqual(out["n_state_transfers"], 1)

    def test_material_classification(self):
        a = _cell(0.30, 0.2, False)
        b = _cell(0.37, 0.0, True)
        out = mod.classify_cell(a, b)
        self.assertEqual(out["classification"], "MATERIAL_POINT_ESTIMATE_CHANGE")
        self.assertAlmostEqual(out["delta_high_low_diff_net_1x"], 0.07, places=12)

    def test_sign_flip_classification(self):
        a = _cell(-0.10, 0.2, False)
        b = _cell(0.10, 0.0, True)
        out = mod.classify_cell(a, b)
        self.assertEqual(out["classification"], "SIGN_FLIP")

    def test_below_threshold_is_marginal(self):
        a = _cell(0.30, 0.2, False)
        b = _cell(0.34, 0.0, True)
        out = mod.classify_cell(a, b)
        self.assertEqual(out["classification"], "MARGINAL_POINT_ESTIMATE_CHANGE")

    def test_state_transfer_count_multiple(self):
        a = _cell(0.35, 0.2, False, n_high=100, n_low=100, n_mid=100)
        b = _cell(0.36, 0.0, True, n_high=102, n_low=99, n_mid=99)
        out = mod.classify_cell(a, b)
        self.assertEqual(out["delta_n_high"], 2)
        self.assertEqual(out["delta_n_low"], -1)
        self.assertEqual(out["delta_n_mid"], -1)
        self.assertEqual(out["n_state_transfers"], 2)


class AnalyzeLedgerTests(unittest.TestCase):
    def test_no_flips_when_holm_matches(self):
        ledger = _ledger(
            {"H004V001": _cell(0.3, 0.01, True), "H004V002": _cell(0.4, 0.0, True)},
            {"H004V001": _cell(0.5, 0.0, True), "H004V002": _cell(0.2, 0.2, True)},
        )
        out = mod.analyze_ledger(ledger)
        self.assertEqual(out["n_flips"], 0)
        self.assertEqual(out["flip_cells"], [])

    def test_single_flip_detected_and_classified(self):
        ledger = _ledger(
            {"H004V001": _cell(0.3, 0.01, True), "H004V130": _cell(0.353, 0.006, False, n_low=136, n_mid=1078)},
            {"H004V001": _cell(0.5, 0.0, True), "H004V130": _cell(0.380, 0.0, True, n_low=135, n_mid=1079)},
        )
        out = mod.analyze_ledger(ledger)
        self.assertEqual(out["n_flips"], 1)
        flip = out["flip_cells"][0]
        self.assertEqual(flip["config_id"], "H004V130")
        self.assertEqual(flip["classification"], "MARGINAL_POINT_ESTIMATE_CHANGE")
        self.assertEqual(flip["n_state_transfers"], 1)

    def test_non_flip_cells_with_different_nets_are_ignored(self):
        ledger = _ledger(
            {"H004V001": _cell(0.3, 0.01, True)},
            {"H004V001": _cell(0.9, 0.0, True)},
        )
        out = mod.analyze_ledger(ledger)
        self.assertEqual(out["n_flips"], 0)

    def test_default_threshold_is_economic_threshold(self):
        self.assertEqual(mod.ECONOMIC_THRESHOLD, 0.05)


class CommittedLedgerIntegrationTests(unittest.TestCase):
    """Pins the observed sole flip in the committed F1GRID-002 ledger."""

    def setUp(self):
        if not LEDGER.is_file():
            self.skipTest(f"F1GRID-002 ledger not present on disk: {LEDGER}")
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.summary = (
            json.loads(SUMMARY.read_text(encoding="utf-8"))
            if SUMMARY.is_file()
            else None
        )

    def test_committed_ledger_has_exactly_one_holm_flip_h004v130(self):
        out = mod.analyze_ledger(self.ledger)
        self.assertEqual(out["n_flips"], 1, out["flip_cells"])
        flip = out["flip_cells"][0]
        self.assertEqual(flip["config_id"], "H004V130")
        self.assertEqual(flip["classification"], "MARGINAL_POINT_ESTIMATE_CHANGE")
        self.assertEqual(flip["n_state_transfers"], 1)
        # The point-estimate move is small and same-signed; the p-value crosses
        # the Holm threshold (0.006 -> 0.0) rather than the effect changing size.
        self.assertLess(abs(flip["delta_high_low_diff_net_1x"]), mod.ECONOMIC_THRESHOLD)
        self.assertEqual(flip["a_holm_rejected"], False)
        self.assertEqual(flip["b_holm_rejected"], True)

    def test_summary_crosscheck_agrees(self):
        artifact = mod.build_artifact(
            self.ledger, self.summary, LEDGER, "2026-11-17T07:36:30Z"
        )
        self.assertTrue(artifact["summary_crosscheck"]["agrees"])
        self.assertEqual(
            artifact["summary_crosscheck"]["ledger_flip_ids"], ["H004V130"]
        )
        self.assertTrue(artifact["exploratory_only"])
        self.assertFalse(artifact["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()