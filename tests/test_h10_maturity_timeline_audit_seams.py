"""Hermetic seam tests for scripts/h10_maturity_timeline_audit.py.

Exercises every pure seam (sha256_file, load_json, load_text, check_equal,
check_in_text, kline_dates_in_window, _in_block_formations,
compute_maturity_milestones) and the full audit function against synthetic
fixtures, with no network access and no reads of committed artifacts beyond the
module import.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

spec = importlib.util.spec_from_file_location("h10_maturity_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _ms(date_str: str) -> int:
    d = _dt.datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=_dt.timezone.utc)
    return int(d.timestamp() * 1000)


def _compliant_block():
    return {
        "n_high": 0,
        "n_low": 0,
        "n_formations": 1,
        "block_sealed": True,
        "high_low_diff_net_1x": None,
        "last_allowed_formation_date": "2026-09-30",
        "sequential_look_mature": False,
        "sequential_look_consumes_budget": False,
        "sequential_look_number": 1,
        "sequential_alpha_k": 0.025,
        "sequential_cumulative_spend": 0.025,
        "sequential_remaining_budget": 0.025,
        "economic_significance_met": False,
        "state_count_floor_met": False,
        "confirmatory_claim_allowed": False,
        "economic_significance_threshold": 0.05,
        "min_state_formations": 5,
        "forward_block_start": "2026-09-30",
        "formations": [{"spread_gross": -0.047729065266337745,
                        "spread_net_1x": -0.048729065266337745}],
    }


def _eval_source():
    return (
        "BASE_COST_TURN = 0.0005\n"
        "ECONOMIC_SIGNIFICANCE_THRESHOLD = 0.05\n"
        "MIN_STATE_FORMATIONS = 5\n"
        "MIN_PRIOR_DISPERSIONS = 30\n"
        'ANCHOR_PARAMS = {"forward_horizon_days": 30}\n'
    )


def _window_dates():
    """31 dates: 2026-09-30 plus October 2026 minus the 2026-10-28 archive gap."""
    dates = ["2026-09-30"]
    for day in range(1, 32):
        d = f"2026-10-{day:02d}"
        if d == "2026-10-28":
            continue
        dates.append(d)
    return dates  # 1 + 30 = 31


class HelperSeamTests(unittest.TestCase):
    def test_check_equal_pass_and_fail(self):
        results = []
        mod.check_equal("a", 1, 1, results)
        mod.check_equal("b", 1, 2, results)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])
        self.assertEqual(results[0]["expected"], 1)
        self.assertEqual(results[1]["actual"], 2)

    def test_check_in_text_pass_and_fail(self):
        results = []
        mod.check_in_text("x", "needle", "a needle here", results)
        mod.check_in_text("y", "absent", "a needle here", results)
        self.assertTrue(results[0]["passed"])
        self.assertEqual(results[0]["actual"], "found")
        self.assertFalse(results[1]["passed"])
        self.assertEqual(results[1]["actual"], "not found")

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.bin"
            payload = b"maturity-audit"
            p.write_bytes(payload)
            self.assertEqual(mod.sha256_file(p), hashlib.sha256(payload).hexdigest())

    def test_load_json_and_text(self):
        with tempfile.TemporaryDirectory() as td:
            jp = Path(td) / "d.json"
            jp.write_text(json.dumps({"k": [1, 2]}))
            tp = Path(td) / "t.md"
            tp.write_text("hello")
            self.assertEqual(mod.load_json(jp), {"k": [1, 2]})
            self.assertEqual(mod.load_text(tp), "hello")

    def test_in_block_formations_mathematically(self):
        # in_block = cutoff_index - horizon - block_start_index + 1, floored at 0
        self.assertEqual(mod._in_block_formations(30, 30, 0), 1)
        self.assertEqual(mod._in_block_formations(60, 30, 0), 31)
        self.assertEqual(mod._in_block_formations(61, 30, 0), 32)
        self.assertEqual(mod._in_block_formations(10, 30, 0), 0)  # before horizon


class KlineDatesSeamTests(unittest.TestCase):
    def test_kline_dates_in_window_filters_and_sorts(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "k.csv"
            dates = _window_dates()
            lines = ["open_time,close"]
            for d in dates:
                lines.append(f"{_ms(d)},1.0")
            p.write_text("\n".join(lines) + "\n")
            got = mod.kline_dates_in_window(p, "2026-09-30", "2026-10-31")
            self.assertEqual(got, sorted(dates))
            self.assertEqual(len(got), 31)
            self.assertNotIn("2026-10-28", got)

    def test_kline_dates_in_window_excludes_out_of_range(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "k.csv"
            lines = ["open_time,close"]
            for d in ["2026-09-29", "2026-09-30", "2026-10-31", "2026-11-01"]:
                lines.append(f"{_ms(d)},1.0")
            p.write_text("\n".join(lines) + "\n")
            got = mod.kline_dates_in_window(p, "2026-09-30", "2026-10-31")
            self.assertEqual(got, ["2026-09-30", "2026-10-31"])


class ComputeMilestonesSeamTests(unittest.TestCase):
    def test_current_immature_geometry(self):
        ms = mod.compute_maturity_milestones(
            block_start="2026-09-30",
            last_observed_date="2026-10-31",
            block_start_index=0,
            last_observed_index=30,
        )
        self.assertEqual(ms["current_in_block_formations"], 1)
        self.assertEqual(ms["current_classifiable_formations"], 0)
        self.assertEqual(ms["M1_first_mature_look"]["min_in_block_formations"], 32)
        self.assertEqual(
            ms["M1_first_mature_look"]["cutoff_index_offset_from_block_start"], 61)
        self.assertEqual(
            ms["M1_first_mature_look"]["additional_in_block_formations_needed"], 31)
        self.assertEqual(
            ms["M1_first_mature_look"]["earliest_cutoff_calendar_estimate"], "2026-12-01")
        self.assertEqual(ms["november_2026_vintage"]["in_block_formations"], 31)
        self.assertEqual(ms["november_2026_vintage"]["classifiable_formations"], 1)
        self.assertFalse(ms["november_2026_vintage"]["m1_possible"])
        self.assertEqual(
            ms["M2_magnitude_estimable"]["decile_based_estimate_in_block_formations"], 80)
        self.assertEqual(
            ms["M2_magnitude_estimable"]["hard_lower_bound_in_block_formations"], 40)

    def test_already_mature_block_needs_no_additional_formations(self):
        ms = mod.compute_maturity_milestones(
            block_start="2026-09-30",
            last_observed_date="2027-03-31",
            block_start_index=0,
            last_observed_index=180,
        )
        self.assertEqual(ms["current_in_block_formations"], 151)
        self.assertGreater(ms["current_classifiable_formations"], 0)
        self.assertEqual(
            ms["M1_first_mature_look"]["additional_in_block_formations_needed"], 0)

    def test_november_possible_when_enough_classifiable(self):
        # Far-future observed index so the November-vintage geometry is moot, but
        # verify m1_possible flips True once classifiable >= 2.
        ms = mod.compute_maturity_milestones(
            block_start="2026-09-30",
            last_observed_date="2027-06-30",
            block_start_index=0,
            last_observed_index=270,
        )
        self.assertGreaterEqual(ms["november_2026_vintage"]["classifiable_formations"], 2)
        self.assertTrue(ms["november_2026_vintage"]["m1_possible"])


class AuditFunctionSeamTests(unittest.TestCase):
    def _write_fixture(self, td, block=None, eval_src=None):
        block = block if block is not None else _compliant_block()
        eval_src = eval_src if eval_src is not None else _eval_source()
        fresh = Path(td) / "fresh.json"
        klines = Path(td) / "klines.csv"
        canonical = Path(td) / "canonical.json"
        ledger = Path(td) / "ledger.json"
        frontier = Path(td) / "frontier.json"
        grid_config = Path(td) / "grid_config.json"
        eval_path = Path(td) / "eval_forward_block.py"
        fresh.write_text(json.dumps(block))
        canonical.write_text("{}")
        ledger.write_text("{}")
        frontier.write_text("{}")
        grid_config.write_text("{}")
        eval_path.write_text(eval_src)
        lines = ["open_time,close"]
        for d in _window_dates():
            lines.append(f"{_ms(d)},1.0")
        klines.write_text("\n".join(lines) + "\n")
        return {
            "FRESH_BLOCK_PATH": fresh,
            "KLINES_BTC_PATH": klines,
            "CANONICAL_BLOCK_PATH": canonical,
            "GRID_LEDGER_PATH": ledger,
            "UNIVERSE_FRONTIER_PATH": frontier,
            "GRID_CONFIG_PATH": grid_config,
            "EVAL_SRC_PATH": eval_path,
            "EXPECTED_FRESH_BLOCK_SHA256": mod.sha256_file(fresh),
            "EXPECTED_CANONICAL_SHA256": mod.sha256_file(canonical),
            "EXPECTED_GRID_LEDGER_SHA256": mod.sha256_file(ledger),
            "EXPECTED_FRONTIER_SHA256": mod.sha256_file(frontier),
            "EXPECTED_GRID_CONFIG_SHA256": mod.sha256_file(grid_config),
        }

    def test_audit_passes_on_compliant_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td)):
                res = mod.audit_h10_maturity_timeline()
            self.assertEqual(res["verdict"], "PASS")
            self.assertEqual(res["checks_failed"], 0)
            self.assertEqual(res["hypothesis_id"], "H35")

    def test_audit_fails_on_deviating_fixture(self):
        bad = _compliant_block()
        bad["n_high"] = 1  # violates IMMATURE
        bad["sequential_alpha_k"] = 0.05  # violates alpha_1 = 0.025
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, bad)):
                res = mod.audit_h10_maturity_timeline()
            self.assertEqual(res["verdict"], "FAIL")
            self.assertGreater(res["checks_failed"], 0)
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("block_is_immature_n_high", failed)
            self.assertIn("alpha_k_is_alpha_1", failed)

    def test_audit_fails_on_constant_drift(self):
        drift = _eval_source().replace("MIN_PRIOR_DISPERSIONS = 30",
                                       "MIN_PRIOR_DISPERSIONS = 25")
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, eval_src=drift)):
                res = mod.audit_h10_maturity_timeline()
            self.assertEqual(res["verdict"], "FAIL")
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("constant_min_prior", failed)

    def test_main_writes_artifact_and_returns_pass_exit(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch.multiple(mod, **self._write_fixture(td)), \
                    patch.object(mod, "ARTIFACT_DIR", td_path):
                rc = mod.main()
            self.assertEqual(rc, 0)
            written = list((td_path / "integrity_audit").glob("*.json"))
            self.assertEqual(len(written), 1)
            data = json.loads(written[0].read_text())
            self.assertEqual(data["verdict"], "PASS")

    def test_main_returns_nonzero_on_fail(self):
        bad = _compliant_block()
        bad["block_sealed"] = False
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch.multiple(mod, **self._write_fixture(td, bad)), \
                    patch.object(mod, "ARTIFACT_DIR", td_path):
                rc = mod.main()
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()