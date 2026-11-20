"""Tests for the H55 breadth/arity and 2-asset identification diagnostic.

Hermetic synthetic fixtures cover the arity rule, the algebraic dispersion
identity, month/breadth accounting, formation completeness and every verdict
branch. Skip-guarded integration checks bind the committed audit to the
committed wave-B panels and verify the local tail rule against the canonical
``scripts/eval_forward_block.py`` implementation.

Synthetic rows are software fixtures, never market evidence. No network is used
and no audit is written by the tests.

The study is EXPLORATORY_ONLY feasibility/identification measurement: these
tests verify measurement and reporting behaviour -- not an economic claim.
"""
import importlib.util
import json
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path

import scripts.panel_breadth_arity_diagnostic as diag

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "artifacts" / diag.EXP

KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
DAY_MS = 86_400_000
BASE = date(2026, 1, 1)


def _ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp()) * 1000


def _kline_csv(closes_by_date):
    rows = []
    for d in sorted(closes_by_date):
        c = closes_by_date[d]
        ms = _ms(d)
        rows.append(f"{ms},{c},{c},{c},{c},1.0,{ms + DAY_MS - 1},1.0,1,1.0,1.0,0")
    return "\n".join([KLINES_HEADER, *rows]) + "\n"


def _write(tmp, name, text):
    path = Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


def _business_days(start, n):
    out = []
    d = start
    while len(out) < n:
        out.append(d)
        d = date.fromordinal(d.toordinal() + 1)
    return out


class ArityTests(unittest.TestCase):
    def test_tail_size_is_floor_n_over_ten(self):
        self.assertEqual(diag.decile_tail_size(9), 0)
        self.assertEqual(diag.decile_tail_size(19), 1)
        self.assertEqual(diag.decile_tail_size(20), 2)
        self.assertEqual(diag.decile_tail_size(216), 21)

    def test_min_breadth_for_outer_deciles_is_20(self):
        self.assertEqual(diag.min_breadth_outer_deciles(), 20)
        self.assertFalse(diag.outer_decile_tails_ok(19))
        self.assertTrue(diag.outer_decile_tails_ok(20))

    def test_arity_table_is_monotone_in_tail_size(self):
        table = diag.arity_table(40)
        self.assertEqual(len(table), 40)
        sizes = [row["tail_size_k"] for row in table]
        self.assertEqual(sizes, sorted(sizes))
        self.assertEqual(
            [row["n_assets"] for row in table if row["both_tails_nonempty"]],
            list(range(20, 41)),
        )

    def test_local_rule_matches_canonical_portfolio_spread(self):
        spec = importlib.util.find_spec("pandas")
        if spec is None:
            self.skipTest("pandas unavailable")
        path = ROOT / "scripts" / "eval_forward_block.py"
        mod_spec = importlib.util.spec_from_file_location("eval_fb_arity", path)
        mod = importlib.util.module_from_spec(mod_spec)
        try:
            mod_spec.loader.exec_module(mod)
        except Exception as exc:  # pragma: no cover - environment guard
            self.skipTest(f"canonical module not importable: {exc}")
        import pandas as pd

        for n in range(1, 41):
            mom = pd.Series({f"a{i:03d}": float(n - i) for i in range(n)})
            long_leg, short_leg = mod.portfolio_spread(mom, "trailing_window_outer_deciles")
            self.assertEqual(
                diag.outer_decile_tails_ok(n),
                bool(long_leg) and bool(short_leg),
                f"n={n} local rule disagrees with canonical portfolio_spread",
            )
            if long_leg:
                self.assertEqual(len(long_leg), diag.decile_tail_size(n))


class IdentityTests(unittest.TestCase):
    def test_population_std_of_two_equals_half_absolute_spread(self):
        pairs = [(0.0, 0.0), (0.1, -0.3), (-0.25, 0.05), (1.0, -1.0), (-0.02, -0.02)]
        for a, b in pairs:
            row = diag.dispersion_identity(a, b)
            self.assertTrue(row["identity_holds"])
            self.assertAlmostEqual(
                row["dispersion_pop_std_ddof0"], abs(a - b) / 2.0, places=15
            )
            if a != b:
                self.assertAlmostEqual(row["ratio_dispersion_over_abs_spread"], 0.5, places=15)

    def test_identity_is_sign_invariant_but_spread_is_not(self):
        forward = diag.dispersion_identity(0.2, -0.1)
        swapped = diag.dispersion_identity(-0.1, 0.2)
        self.assertEqual(forward["dispersion_pop_std_ddof0"], swapped["dispersion_pop_std_ddof0"])
        self.assertEqual(forward["abs_momentum_spread"], swapped["abs_momentum_spread"])
        self.assertNotEqual(0.2 - (-0.1), (-0.1) - 0.2)

    def test_zero_spread_has_no_ratio(self):
        row = diag.dispersion_identity(0.05, 0.05)
        self.assertEqual(row["dispersion_pop_std_ddof0"], 0.0)
        self.assertIsNone(row["ratio_dispersion_over_abs_spread"])


class CalendarAndBreadthTests(unittest.TestCase):
    def test_month_keys_are_inclusive_and_ordered(self):
        keys = diag.month_keys(date(2023, 11, 15), date(2024, 2, 2))
        self.assertEqual(keys, ["2023-11", "2023-12", "2024-01", "2024-02"])

    def test_month_end_handles_december_and_leap_february(self):
        self.assertEqual(diag.month_end_on_or_before(date(2024, 12, 3), "2024-12"), date(2024, 12, 31))
        self.assertEqual(diag.month_end_on_or_before(date(2024, 2, 3), "2024-02"), date(2024, 2, 29))

    def test_breadth_by_month_counts_assets_with_any_observation(self):
        a = [date(2024, 1, 5), date(2024, 1, 20), date(2024, 2, 1)]
        b = [date(2024, 1, 31)]
        c = [date(2024, 3, 2)]
        counts = diag.breadth_by_month({"A": a, "B": b, "C": c}, ["2024-01", "2024-02", "2024-03"])
        self.assertEqual(counts["2024-01"], ["A", "B"])
        self.assertEqual(counts["2024-02"], ["A"])
        self.assertEqual(counts["2024-03"], ["C"])

    def test_breadth_ignores_months_outside_the_inventory_window(self):
        counts = diag.breadth_by_month({"A": [date(2022, 12, 31)]}, ["2023-01"])
        self.assertEqual(counts, {"2023-01": []})


class FormationTests(unittest.TestCase):
    def test_formation_dates_require_complete_lookback_window(self):
        days = _business_days(date(2026, 1, 30), 40)
        close = {d: 100.0 + i for i, d in enumerate(days)}
        forms = diag.formation_dates(close, close, days[0], days[-1], 3)
        self.assertNotIn(date(2026, 1, 31), forms)
        self.assertEqual(forms[0], date(2026, 2, 28))

    def test_formation_dates_are_last_common_day_of_each_month(self):
        days = _business_days(date(2026, 1, 1), 80)
        close = {d: 100.0 + i for i, d in enumerate(days)}
        forms = diag.formation_dates(close, close, days[0], days[-1], 3)
        self.assertEqual(forms, [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 21)])

    def test_formation_dates_skip_missing_common_days(self):
        days = _business_days(date(2026, 1, 1), 10)
        a = {d: 1.0 for d in days}
        b = {d: 1.0 for d in days[2:]}
        forms = diag.formation_dates(a, b, days[0], days[-1], 2)
        self.assertTrue(all(f in b for f in forms))

    def test_cumulative_momentum_matches_compounded_returns(self):
        days = _business_days(date(2026, 1, 1), 5)
        close = {d: c for d, c in zip(days, [100.0, 110.0, 99.0, 108.9, 120.0])}
        mom = diag.cumulative_momentum(close, days)
        expected = (110 / 100) * (99 / 110) * (108.9 / 99) * (120 / 108.9) - 1.0
        self.assertAlmostEqual(mom, expected, places=15)

    def test_cumulative_momentum_needs_two_dates(self):
        self.assertIsNone(diag.cumulative_momentum({date(2026, 1, 1): 1.0}, [date(2026, 1, 1)]))

    def test_read_klines_close_rejects_duplicates_and_bad_prices(self):
        days = _business_days(date(2026, 1, 1), 3)
        with tempfile.TemporaryDirectory() as tmp:
            good = _write(tmp, "good.csv", _kline_csv({d: 1.0 for d in days}))
            self.assertEqual(len(diag.read_klines_close(good)), 3)
            bad = _write(tmp, "bad.csv", "\n".join(
                [KLINES_HEADER, f"{_ms(days[0])},1,1,1,0,1,1,1,1,1,1,0"]
            ) + "\n")
            with self.assertRaises(ValueError):
                diag.read_klines_close(bad)


class VerdictTests(unittest.TestCase):
    def test_structural_limit_branch(self):
        verdict, reasons = diag.evaluate_verdict(20, 0.0, 37, True, 12, 24, "2024-12")
        self.assertEqual(verdict, diag.STRUCTURAL_LIMIT)
        self.assertTrue(any("breadth>=20" in r for r in reasons))

    def test_unexpected_when_arity_differs(self):
        verdict, reasons = diag.evaluate_verdict(19, 0.0, 37, True, 12, 24, "2024-12")
        self.assertEqual(verdict, diag.UNEXPECTED)
        self.assertTrue(reasons)

    def test_unexpected_when_identity_fails_or_sample_short(self):
        self.assertEqual(
            diag.evaluate_verdict(20, 1e-6, 37, True, 12, 24, "2024-12")[0], diag.UNEXPECTED
        )
        self.assertEqual(
            diag.evaluate_verdict(20, 0.0, 5, True, 12, 24, "2024-12")[0], diag.UNEXPECTED
        )

    def test_confirmed_branch_when_no_legacy_breadth_month(self):
        verdict, _ = diag.evaluate_verdict(20, 0.0, 37, True, 5, 0, None)
        self.assertEqual(verdict, diag.CONFIRMED)

    def test_verdict_checks_flag_only_the_maturity_expectation_when_it_fails(self):
        checks = diag.verdict_checks(20, 0.0, 37, True, 36, 24, "2024-12")
        failed = [c["condition"] for c in checks if not c["held"]]
        self.assertEqual(len(failed), 1)
        self.assertIn("n_forward_matured", failed[0])

    def test_verdict_checks_all_hold_for_structural_case(self):
        checks = diag.verdict_checks(20, 0.0, 37, True, 12, 24, "2024-12")
        self.assertTrue(all(c["held"] for c in checks))


class CommittedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted((EXP_DIR / "integrity_audit").glob("panel_breadth_arity_diagnostic_*.json"))
        if not cls.paths:
            raise unittest.SkipTest("no committed breadth/arity audit in this checkout")
        cls.audit = json.loads(cls.paths[-1].read_text(encoding="utf-8"))

    def test_preregistration_exists_and_precedes_the_audit(self):
        prereg = EXP_DIR / "preregistrations" / "BREADTH_ARITY_001_v1.md"
        self.assertTrue(prereg.exists())
        text = prereg.read_text(encoding="utf-8")
        self.assertIn("Created:** 2026-11-20T02:33:35Z", text)
        self.assertLessEqual("2026-11-20T02:33:35Z", self.audit["computed_utc"])

    def test_registered_identity_and_non_claims(self):
        self.assertEqual(self.audit["experiment_id"], diag.EXPERIMENT_ID)
        self.assertEqual(self.audit["audit_id"], diag.AUDIT_ID)
        self.assertEqual(self.audit["hypothesis"], diag.HYPOTHESIS)
        self.assertEqual(self.audit["status"], "EXPLORATORY_ONLY")
        self.assertFalse(self.audit["confirmatory_claim_allowed"])
        self.assertEqual(self.audit["network_io"], "none")
        self.assertTrue(self.audit["frozen_hashes_verified"]["all_match"])
        self.assertTrue(self.audit["non_claims"])

    def test_arity_and_identity_figures_are_structural(self):
        self.assertEqual(self.audit["m1_arity"]["min_breadth_outer_deciles"], 20)
        m2 = self.audit["m2_identity"]
        self.assertLessEqual(m2["max_abs_deviation"], diag.IDENTITY_TOL)
        self.assertTrue(m2["identity_holds_all_formations"])
        self.assertEqual(m2["ratio_min"], 0.5)
        self.assertEqual(m2["ratio_max"], 0.5)

    def test_breadth_and_maturity_counts_are_internally_consistent(self):
        m3 = self.audit["m3_breadth_inventory"]
        self.assertEqual(m3["n_months"], len(m3["rows"]))
        self.assertEqual(len(m3["months_with_breadth_ge_20"]), m3["n_months_with_breadth_ge_20"])
        self.assertEqual(m3["max_breadth"], max(r["n_assets"] for r in m3["rows"]))
        m4 = self.audit["m4_narrow_sample"]
        self.assertEqual(m4["n_candidate_formations"], len(m4["rows"]))
        self.assertEqual(
            m4["n_forward_matured"], sum(1 for r in m4["rows"] if r["forward_matured"])
        )

    def test_no_outcome_fields_are_present(self):
        blob = json.dumps(self.audit)
        for forbidden in ('"spread_net', '"gross_return', '"p_value', '"funding_pnl'):
            self.assertNotIn(forbidden, blob)


if __name__ == "__main__":
    unittest.main()
