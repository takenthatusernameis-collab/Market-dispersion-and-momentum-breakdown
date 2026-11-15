"""Hermetic unit tests for scripts/grid_ledger_internal_consistency.py.

Gap: the ledger internal-consistency audit exposes deterministic pure seams
(implied_costs, recompute_aggregates, _num_eq, check_cell, check_ledger) that no
other test imports or exercises directly; the audit itself only ran as a
one-shot CLI against the committed 73 MB ledger. These tests exercise every
seam with synthetic dicts (no frozen artifacts, no network, no market data).
"""
from __future__ import annotations

import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "grid_ledger_internal_consistency.py"


def _load():
    spec = importlib.util.spec_from_file_location(
        "grid_ledger_internal_consistency_seams_test", SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


MOD = _load()

_FORMS = [
    {"formation_date": "2023-01-31", "state": "high", "spread_gross": 0.2,
     "spread_net_1x": 0.199, "n_assets": 26, "dispersion": 0.2},
    {"formation_date": "2023-02-28", "state": "low", "spread_gross": -0.1,
     "spread_net_1x": -0.101, "n_assets": 27, "dispersion": 0.15},
    {"formation_date": "2023-03-31", "state": "mid", "spread_gross": 0.05,
     "spread_net_1x": 0.049, "n_assets": 26, "dispersion": 0.1},
]


def _valid_cell(config_id="H004V001"):
    rec = MOD.recompute_aggregates(_FORMS)
    cell = {
        "config_id": config_id,
        "status": "OK",
        "reason": "",
        "holm_rejected": False,
        "pvalue_bootstrap_two_sided": 0.5,
        "formations": [dict(f) for f in _FORMS],
        "eligible_assets_per_date": dict(rec["eligible_assets_per_date"]),
    }
    for k in (
        "n_formations", "n_high", "n_low", "n_mid",
        "high_gross_mean", "low_gross_mean", "high_net_1x_mean", "low_net_1x_mean",
        "high_low_diff_gross", "high_low_diff_net_1x",
        "spread_gross_mean", "spread_net_1x_mean",
        "spread_gross_median", "spread_net_1x_median",
        "date_first", "date_last",
    ):
        cell[k] = rec[k]
    return cell


def _valid_ledger():
    return {
        "expected_cells": 1,
        "cells_ok": 1,
        "cells_evaluated": 1,
        "cells_failed": 0,
        "cells_blocked": 0,
        "holm_rejected_count": 0,
        "cells": {"H004V001": _valid_cell()},
    }


class ImpliedCostsTests(unittest.TestCase):
    def test_basic_constant_cost(self):
        costs = MOD.implied_costs(_FORMS)
        self.assertEqual(len(costs), 3)
        for c in costs:
            self.assertAlmostEqual(c, 0.001, places=12)

    def test_missing_value_is_nan(self):
        forms = [{"spread_gross": 0.1, "spread_net_1x": None}]
        self.assertTrue(math.isnan(MOD.implied_costs(forms)[0]))


class RecomputeAggregatesTests(unittest.TestCase):
    def test_empty(self):
        r = MOD.recompute_aggregates([])
        self.assertEqual(r["n_formations"], 0)
        self.assertIsNone(r["high_gross_mean"])
        self.assertIsNone(r["spread_gross_median"])
        self.assertIsNone(r["date_first"])

    def test_single_mid(self):
        forms = [{"formation_date": "2023-01-31", "state": "mid",
                  "spread_gross": 0.1, "spread_net_1x": 0.099, "n_assets": 26}]
        r = MOD.recompute_aggregates(forms)
        self.assertEqual(r["n_mid"], 1)
        self.assertIsNone(r["high_gross_mean"])
        self.assertAlmostEqual(r["spread_gross_mean"], 0.1)
        self.assertEqual(r["date_first"], "2023-01-31")
        self.assertEqual(r["eligible_assets_per_date"], {"mean": 26.0, "min": 26, "max": 26})

    def test_mixed_states(self):
        r = MOD.recompute_aggregates(_FORMS)
        self.assertEqual((r["n_high"], r["n_low"], r["n_mid"]), (1, 1, 1))
        self.assertAlmostEqual(r["high_low_diff_gross"], 0.3)
        self.assertAlmostEqual(r["high_low_diff_net_1x"], 0.3)
        self.assertEqual(r["date_first"], "2023-01-31")
        self.assertEqual(r["date_last"], "2023-03-31")
        self.assertAlmostEqual(r["eligible_assets_per_date"]["mean"], (26 + 27 + 26) / 3)

    def test_median(self):
        r = MOD.recompute_aggregates(_FORMS)
        self.assertAlmostEqual(r["spread_gross_median"], 0.05)
        self.assertAlmostEqual(r["spread_net_1x_median"], 0.049)

    def test_nan_values_dropped_from_mean(self):
        forms = [
            {"formation_date": "2023-01-31", "state": "high", "spread_gross": 0.2,
             "spread_net_1x": 0.199, "n_assets": 26},
            {"formation_date": "2023-02-28", "state": "high", "spread_gross": float("nan"),
             "spread_net_1x": 0.15, "n_assets": 26},
        ]
        r = MOD.recompute_aggregates(forms)
        self.assertAlmostEqual(r["high_gross_mean"], 0.2)
        self.assertAlmostEqual(r["high_net_1x_mean"], (0.199 + 0.15) / 2)


class NumEqTests(unittest.TestCase):
    def test_both_none(self):
        self.assertTrue(MOD._num_eq(None, None))

    def test_one_none(self):
        self.assertFalse(MOD._num_eq(1.0, None))
        self.assertFalse(MOD._num_eq(None, 1.0))

    def test_within_and_beyond_tolerance(self):
        self.assertTrue(MOD._num_eq(1.0, 1.0 + 1e-13))
        self.assertFalse(MOD._num_eq(1.0, 1.1))

    def test_non_numeric(self):
        self.assertFalse(MOD._num_eq("abc", 1.0))


class CheckCellTests(unittest.TestCase):
    def test_valid_cell_passes(self):
        r = MOD.check_cell(_valid_cell())
        self.assertTrue(r["matched"], r["violations"])
        self.assertEqual(r["violations"], [])

    def test_n_formations_mismatch(self):
        c = _valid_cell()
        c["n_formations"] = 99
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("n_formations" in v for v in r["violations"]))

    def test_empty_formations(self):
        c = _valid_cell()
        c["formations"] = []
        c["n_formations"] = 0
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("no formations" in v for v in r["violations"]))

    def test_non_increasing_dates(self):
        c = _valid_cell()
        c["formations"][1]["formation_date"] = "2023-01-15"
        c["formations"][2]["formation_date"] = "2023-03-31"
        # recompute aggregates so only the ordering violation remains
        rec = MOD.recompute_aggregates(c["formations"])
        c["date_first"] = rec["date_first"]
        c["date_last"] = rec["date_last"]
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("strictly increasing" in v for v in r["violations"]))

    def test_duplicate_dates(self):
        c = _valid_cell()
        c["formations"][2]["formation_date"] = c["formations"][1]["formation_date"]
        rec = MOD.recompute_aggregates(c["formations"])
        c["date_first"] = rec["date_first"]
        c["date_last"] = rec["date_last"]
        c["n_formations"] = rec["n_formations"]
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("duplicate" in v for v in r["violations"]))

    def test_invalid_state(self):
        c = _valid_cell()
        c["formations"][0]["state"] = "extreme"
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("invalid state" in v for v in r["violations"]))

    def test_invalid_dispersion_negative(self):
        c = _valid_cell()
        c["formations"][0]["dispersion"] = -0.1
        r = MOD.check_cell(c)
        self.assertTrue(any("invalid dispersion" in v for v in r["violations"]))

    def test_invalid_dispersion_non_finite(self):
        c = _valid_cell()
        c["formations"][0]["dispersion"] = float("nan")
        r = MOD.check_cell(c)
        self.assertTrue(any("invalid dispersion" in v for v in r["violations"]))

    def test_invalid_n_assets(self):
        c = _valid_cell()
        c["formations"][0]["n_assets"] = 0
        r = MOD.check_cell(c)
        self.assertTrue(any("invalid n_assets" in v for v in r["violations"]))

    def test_non_constant_implied_cost(self):
        c = _valid_cell()
        c["formations"][0]["spread_net_1x"] = 0.1  # implied cost 0.1
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("not constant" in v for v in r["violations"]))

    def test_wrong_baseline_cost(self):
        c = _valid_cell()
        for f in c["formations"]:
            f["spread_net_1x"] = f["spread_gross"] - 0.002
        rec = MOD.recompute_aggregates(c["formations"])
        c["spread_net_1x_mean"] = rec["spread_net_1x_mean"]
        c["spread_net_1x_median"] = rec["spread_net_1x_median"]
        c["high_net_1x_mean"] = rec["high_net_1x_mean"]
        c["low_net_1x_mean"] = rec["low_net_1x_mean"]
        c["high_low_diff_net_1x"] = rec["high_low_diff_net_1x"]
        r = MOD.check_cell(c)
        self.assertFalse(r["matched"])
        self.assertTrue(any("baseline" in v for v in r["violations"]))

    def test_state_count_mismatch(self):
        c = _valid_cell()
        c["n_high"] = 5
        r = MOD.check_cell(c)
        self.assertTrue(any("n_high" in v for v in r["violations"]))

    def test_aggregate_mismatch(self):
        c = _valid_cell()
        c["high_gross_mean"] = 0.999
        r = MOD.check_cell(c)
        self.assertTrue(any("high_gross_mean" in v for v in r["violations"]))

    def test_date_mismatch(self):
        c = _valid_cell()
        c["date_first"] = "1999-01-01"
        r = MOD.check_cell(c)
        self.assertTrue(any("date_first" in v for v in r["violations"]))

    def test_eligible_mismatch(self):
        c = _valid_cell()
        c["eligible_assets_per_date"]["max"] = 99
        r = MOD.check_cell(c)
        self.assertTrue(any("eligible_assets_per_date.max" in v for v in r["violations"]))

    def test_pvalue_out_of_range(self):
        c = _valid_cell()
        c["pvalue_bootstrap_two_sided"] = 1.5
        r = MOD.check_cell(c)
        self.assertTrue(any("pvalue" in v for v in r["violations"]))

    def test_holm_not_boolean(self):
        c = _valid_cell()
        c["holm_rejected"] = "yes"
        r = MOD.check_cell(c)
        self.assertTrue(any("holm_rejected" in v for v in r["violations"]))


class CheckLedgerTests(unittest.TestCase):
    def test_valid_ledger_passes(self):
        r = MOD.check_ledger(_valid_ledger(), expected_cells=1)
        self.assertTrue(r["passed"], r["cell_violations"] + r["global_violations"])
        self.assertEqual(r["n_cells"], 1)
        self.assertEqual(r["holm_rejected_true"], 0)

    def test_expected_cells_mismatch(self):
        led = _valid_ledger()
        led["expected_cells"] = 216
        r = MOD.check_ledger(led, expected_cells=1)
        self.assertFalse(r["passed"])
        self.assertTrue(any("expected_cells" in v for v in r["global_violations"]))

    def test_cells_ok_mismatch(self):
        led = _valid_ledger()
        led["cells_ok"] = 0
        r = MOD.check_ledger(led, expected_cells=1)
        self.assertTrue(any("cells_ok" in v for v in r["global_violations"]))

    def test_holm_count_mismatch(self):
        led = _valid_ledger()
        led["holm_rejected_count"] = 3
        r = MOD.check_ledger(led, expected_cells=1)
        self.assertTrue(any("holm_rejected_count" in v for v in r["global_violations"]))

    def test_duplicate_config_ids(self):
        led = _valid_ledger()
        c = _valid_cell()
        c["config_id"] = "H004V001"
        led["cells"]["H004V002"] = c
        r = MOD.check_ledger(led, expected_cells=2)
        self.assertFalse(r["passed"])
        self.assertTrue(any("duplicate config_id" in v for v in r["global_violations"]))

    def test_cell_violation_surfaced(self):
        led = _valid_ledger()
        led["cells"]["H004V001"]["high_gross_mean"] = 0.5
        r = MOD.check_ledger(led, expected_cells=1)
        self.assertFalse(r["passed"])
        self.assertEqual(len(r["cell_violations"]), 1)


class MainTests(unittest.TestCase):
    def _run(self, ledger):
        with tempfile.TemporaryDirectory() as td:
            ledger_path = Path(td) / "ledger.json"
            ledger_path.write_text(json.dumps(ledger))
            out = Path(td) / "audit.json"
            old = MOD.LEDGER_PATH
            MOD.LEDGER_PATH = ledger_path
            try:
                rc = MOD.main(["--out", str(out)])
            finally:
                MOD.LEDGER_PATH = old
            self.assertTrue(out.is_file())
            return rc, json.loads(out.read_text())

    def test_main_pass(self):
        rc, report = self._run(_valid_ledger())
        self.assertEqual(rc, 0)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["overall_passed"])
        self.assertEqual(report["n_cells_checked"], 1)

    def test_main_fail(self):
        led = _valid_ledger()
        led["cells"]["H004V001"]["n_high"] = 7
        rc, report = self._run(led)
        self.assertEqual(rc, 1)
        self.assertEqual(report["status"], "FAIL")


class ConstantsTests(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(MOD.EXPECTED_CELLS, 216)
        self.assertEqual(MOD.EXPECTED_COST_1X, 0.001)
        self.assertEqual(MOD.VALID_STATES, ("high", "low", "mid"))
        self.assertEqual(MOD.TOL, 1e-12)


if __name__ == "__main__":
    unittest.main()