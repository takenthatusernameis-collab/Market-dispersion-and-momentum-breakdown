"""Tests for the H54 wave-B panel usability audit (PANELQA-WAVEB-001).

Hermetic synthetic fixtures cover calendar-gap profiling, OHLC plausibility,
funding-cadence classification and every verdict branch, plus skip-guarded
integration checks binding the committed audit to the committed panels and the
H53 normalization audit. Synthetic rows are software fixtures, never market
evidence. No network is used.

The study is EXPLORATORY_ONLY source-coverage QA: these tests verify
measurement and reporting behaviour -- not an economic claim.
"""
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import scripts.panel_wave_b_quality_audit as qa

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "artifacts" / qa.EXP

KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"

DAY_MS = 86_400_000
BASE_MS = int(datetime(2026, 10, 25, tzinfo=timezone.utc).timestamp()) * 1000


def _kline_row(day_index, close="1.0", volume="10.0", high=None, low=None):
    ms = BASE_MS + day_index * DAY_MS
    o = c = float(close)
    h = float(high) if high is not None else max(o, c)
    l = float(low) if low is not None else min(o, c)
    return (
        f"{ms},{o},{h},{l},{c},{volume},{ms + DAY_MS - 1},1.0,1,1.0,1.0,0"
    )


def _funding_row(ms, interval="8", rate="0.0001", symbol="ARKUSDT"):
    return f"{symbol},{ms},{interval},{rate}"


def _klines_csv(rows):
    return "\n".join([KLINES_HEADER, *rows]) + "\n"


def _funding_csv(rows):
    return "\n".join([FUNDING_HEADER, *rows]) + "\n"


def _write(tmp, name, text):
    path = Path(tmp) / name
    path.write_text(text, encoding="utf-8")
    return path


class GapProfileTests(unittest.TestCase):
    def test_contiguous_days_have_no_gaps(self):
        from datetime import date

        days = [date(2026, 1, 1).fromordinal(date(2026, 1, 1).toordinal() + i) for i in range(5)]
        missing, max_run = qa.gap_profile(days)
        self.assertEqual(missing, [])
        self.assertEqual(max_run, 0)

    def test_single_missing_day_is_reported(self):
        from datetime import date

        base = date(2026, 1, 1)
        days = [base, base.fromordinal(base.toordinal() + 1), base.fromordinal(base.toordinal() + 3)]
        missing, max_run = qa.gap_profile(days)
        self.assertEqual([d.isoformat() for d in missing], ["2026-01-03"])
        self.assertEqual(max_run, 1)

    def test_interior_run_is_measured(self):
        from datetime import date

        base = date(2026, 1, 1)
        days = [base] + [base.fromordinal(base.toordinal() + i) for i in (4, 5)]
        _, max_run = qa.gap_profile(days)
        self.assertEqual(max_run, 3)

    def test_empty_series_is_safe(self):
        self.assertEqual(qa.gap_profile([]), ([], 0))

    def test_expected_days_counts_inclusive_span(self):
        start = BASE_MS
        self.assertEqual(qa.expected_days(start, start + 4 * DAY_MS), 5)


class KlinesMetricsTests(unittest.TestCase):
    def test_clean_panel_is_complete(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "k.csv", _klines_csv([_kline_row(i) for i in range(4)]))
        )
        m = qa.klines_metrics(rows)
        self.assertEqual(m["n_rows"], 4)
        self.assertEqual(m["completeness_ratio"], 1.0)
        self.assertEqual(qa.panel_issues("klines", m), [])

    def test_nonpositive_price_flagged(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "k.csv", _klines_csv([_kline_row(0, close="0.0")]))
        )
        m = qa.klines_metrics(rows)
        self.assertEqual(m["n_nonpositive_price"], 1)
        self.assertIn("n_nonpositive_price", qa.panel_issues("klines", m))

    def test_ohlc_inconsistency_flagged(self):
        rows, _ = qa.read_csv_rows(
            _write(
                tempfile.mkdtemp(),
                "k.csv",
                _klines_csv([_kline_row(0, close="2.0", high="1.0", low="0.5")]),
            )
        )
        m = qa.klines_metrics(rows)
        self.assertEqual(m["n_ohlc_inconsistent"], 1)
        self.assertIn("n_ohlc_inconsistent", qa.panel_issues("klines", m))

    def test_duplicate_timestamp_flagged(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "k.csv", _klines_csv([_kline_row(0), _kline_row(0)]))
        )
        m = qa.klines_metrics(rows)
        self.assertEqual(m["n_duplicate_timestamps"], 1)
        self.assertIn("duplicate_timestamps", qa.panel_issues("klines", m))

    def test_calendar_gap_lowers_completeness(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "k.csv", _klines_csv([_kline_row(0), _kline_row(9)]))
        )
        m = qa.klines_metrics(rows)
        self.assertAlmostEqual(m["completeness_ratio"], 0.2)
        self.assertEqual(m["n_missing_days"], 8)
        self.assertIn("calendar_completeness_below_0_98", qa.panel_issues("klines", m))

    def test_zero_and_negative_volume_counted(self):
        rows, _ = qa.read_csv_rows(
            _write(
                tempfile.mkdtemp(),
                "k.csv",
                _klines_csv([_kline_row(0, volume="0"), _kline_row(1, volume="-1")]),
            )
        )
        m = qa.klines_metrics(rows)
        self.assertEqual(m["n_zero_volume_days"], 1)
        self.assertEqual(m["n_negative_volume"], 1)

    def test_staleness_flagged_past_three_days(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "k.csv", _klines_csv([_kline_row(0)]))
        )
        m = qa.klines_metrics(rows)
        self.assertGreater(m["days_stale"], 3)
        self.assertIn(f"stale_{m['days_stale']}_days", qa.panel_issues("klines", m))


class FundingMetricsTests(unittest.TestCase):
    def test_cadence_histogram_is_recorded(self):
        day = DAY_MS
        rows, _ = qa.read_csv_rows(
            _write(
                tempfile.mkdtemp(),
                "f.csv",
                _funding_csv(
                    [
                        _funding_row(BASE_MS + 6 * day + day // 8, interval="8"),
                        _funding_row(BASE_MS + 6 * day + day // 8 + day // 4, interval="4"),
                    ]
                ),
            )
        )
        m = qa.funding_metrics(rows)
        self.assertEqual(m["funding_interval_hours_histogram"], {"4.0": 1, "8.0": 1})
        self.assertTrue(m["interval_values_allowed"])
        self.assertEqual(qa.panel_issues("funding", m), [])

    def test_unexpected_interval_flagged(self):
        rows, _ = qa.read_csv_rows(
            _write(tempfile.mkdtemp(), "f.csv", _funding_csv([_funding_row(BASE_MS, interval="3")]))
        )
        m = qa.funding_metrics(rows)
        self.assertFalse(m["interval_values_allowed"])
        self.assertIn("unexpected_funding_interval", qa.panel_issues("funding", m))

    def test_nonfinite_and_extreme_rates_counted(self):
        rows, _ = qa.read_csv_rows(
            _write(
                tempfile.mkdtemp(),
                "f.csv",
                _funding_csv(
                    [
                        _funding_row(BASE_MS, rate="nan"),
                        _funding_row(BASE_MS + 1, rate="0.5"),
                        _funding_row(BASE_MS + 2, rate="0.0"),
                    ]
                ),
            )
        )
        m = qa.funding_metrics(rows)
        self.assertEqual(m["n_nonfinite_rate"], 1)
        self.assertEqual(m["n_abs_rate_gt_0_1"], 1)
        self.assertEqual(m["n_zero_rate"], 1)
        self.assertIn("nonfinite_funding_rate", qa.panel_issues("funding", m))

    def test_duplicate_calc_time_flagged(self):
        rows, _ = qa.read_csv_rows(
            _write(
                tempfile.mkdtemp(),
                "f.csv",
                _funding_csv([_funding_row(BASE_MS), _funding_row(BASE_MS)]),
            )
        )
        m = qa.funding_metrics(rows)
        self.assertEqual(m["n_duplicate_calc_time"], 1)
        self.assertIn("duplicate_calc_time", qa.panel_issues("funding", m))


class VerdictTests(unittest.TestCase):
    def _h53(self, panels):
        return {
            "panels": [
                {
                    "asset": asset,
                    "symbol": symbol,
                    "kind": kind,
                    "path": name,
                    "sha256": sha,
                    "n_rows": n,
                }
                for asset, symbol, kind, name, sha, n in panels
            ]
        }

    def _build(self, tmp, klines_rows=None, sha_override=None):
        klines_rows = klines_rows or [_kline_row(i) for i in range(6)]
        panels = []
        specs = [
            ("ark", "ARKUSDT", "klines", "binance_klines_ARKUSDT.csv", _klines_csv(klines_rows)),
            ("ark", "ARKUSDT", "funding", "binance_funding_ARKUSDT.csv", _funding_csv([_funding_row(BASE_MS + 6 * DAY_MS + 3600_000)])),
            ("astr", "ASTRUSDT", "klines", "binance_klines_ASTRUSDT.csv", _klines_csv(klines_rows)),
            ("astr", "ASTRUSDT", "funding", "binance_funding_ASTRUSDT.csv", _funding_csv([_funding_row(BASE_MS + 6 * DAY_MS + 3600_000)])),
        ]
        for asset, symbol, kind, name, text in specs:
            path = _write(tmp, name, text)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            if sha_override and name in sha_override:
                sha = sha_override[name]
            panels.append((asset, symbol, kind, name, sha, len(text.strip().splitlines()) - 1))
        return self._h53(panels)

    def test_clean_panels_complete(self):
        tmp = tempfile.mkdtemp()
        audit = qa.run_audit(
            panel_dir=Path(tmp),
            h53_audit_path=_write(tmp, "h53.json", json.dumps(self._build(tmp))),
        )
        self.assertEqual(audit["verdict"], qa.COMPLETE)
        self.assertEqual(len(audit["panels"]), 4)
        self.assertEqual(audit["cross_panel"]["n_days_both_assets"], 6)

    def test_sha_mismatch_is_scope_mismatch(self):
        tmp = tempfile.mkdtemp()
        h53 = self._build(
            tmp,
            sha_override={"binance_klines_ARKUSDT.csv": "0" * 64},
        )
        audit = qa.run_audit(
            panel_dir=Path(tmp),
            h53_audit_path=_write(tmp, "h53.json", json.dumps(h53)),
        )
        self.assertEqual(audit["verdict"], qa.SCOPE_MISMATCH)
        self.assertTrue(audit["scope_problems"])

    def test_missing_panel_is_scope_mismatch(self):
        tmp = tempfile.mkdtemp()
        h53 = self._build(tmp)
        h53["panels"][0]["path"] = "binance_klines_ABSENT.csv"
        audit = qa.run_audit(
            panel_dir=Path(tmp),
            h53_audit_path=_write(tmp, "h53.json", json.dumps(h53)),
        )
        self.assertEqual(audit["verdict"], qa.SCOPE_MISMATCH)

    def test_gap_lowers_verdict_to_issues(self):
        tmp = tempfile.mkdtemp()
        h53 = self._build(tmp, klines_rows=[_kline_row(0), _kline_row(9)])
        audit = qa.run_audit(
            panel_dir=Path(tmp),
            h53_audit_path=_write(tmp, "h53.json", json.dumps(h53)),
        )
        self.assertEqual(audit["verdict"], qa.ISSUES_FOUND)


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audits = sorted((EXP_DIR / "qa").glob("panel_wave_b_quality_audit_*.json"))
        if not cls.audits:
            raise unittest.SkipTest("no committed wave-B quality audit")
        cls.audit = json.loads(cls.audits[-1].read_text())

    def test_preregistration_exists_and_names_hypothesis(self):
        prereg = EXP_DIR / "preregistrations" / "PANELQA_WAVEB_001_v1.md"
        self.assertTrue(prereg.exists())
        text = prereg.read_text()
        self.assertIn(qa.EXPERIMENT_ID, text)
        self.assertIn("H54", text)

    def test_labels_and_verdict(self):
        self.assertEqual(self.audit["hypothesis"], "H54")
        self.assertEqual(self.audit["status"], "EXPLORATORY_ONLY")
        self.assertFalse(self.audit["confirmatory_claim_allowed"])
        self.assertFalse(self.audit["promotion_allowed"])
        self.assertIn(self.audit["verdict"], (qa.COMPLETE, qa.ISSUES_FOUND))
        self.assertTrue(self.audit["non_claims"])

    def test_frozen_hashes_match(self):
        self.assertTrue(self.audit["frozen_hashes_verified"]["all_match"])

    def test_panels_reconcile_to_h53_hashes(self):
        self.assertEqual(len(self.audit["panels"]), 4)
        for panel in self.audit["panels"]:
            with self.subTest(panel=panel["path"]):
                self.assertTrue(panel["sha256_matches_h53"])
                self.assertTrue(panel["row_count_matches_h53"])
                self.assertTrue((ROOT / panel["path"]).exists())

    def test_klines_continuity_is_measured_not_assumed(self):
        klines = [p for p in self.audit["panels"] if p["kind"] == "klines"]
        self.assertEqual(len(klines), 2)
        for panel in klines:
            m = panel["metrics"]
            self.assertEqual(
                m["n_observed_days"] + m["n_missing_days"], m["expected_days"]
            )
            self.assertAlmostEqual(
                m["completeness_ratio"],
                m["n_observed_days"] / m["expected_days"],
                places=12,
            )

    def test_funding_cadence_histogram_sums_to_rows(self):
        funding = [p for p in self.audit["panels"] if p["kind"] == "funding"]
        self.assertEqual(len(funding), 2)
        for panel in funding:
            m = panel["metrics"]
            self.assertEqual(
                sum(m["funding_interval_hours_histogram"].values()), m["n_rows"]
            )


if __name__ == "__main__":
    unittest.main()
