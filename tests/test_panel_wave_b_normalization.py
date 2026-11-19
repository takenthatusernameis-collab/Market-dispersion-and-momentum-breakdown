"""Tests for the H53 wave-B extension panel normalization (PANELNORM-WAVEB-001).

Hermetic synthetic fixtures cover month-window accounting, archive content
re-validation, duplicate detection, funding symbol prefixing, row accounting and
every verdict branch, plus skip-guarded integration checks binding the committed
panels to the committed audit artifact. No network is used.

The study is EXPLORATORY_ONLY source-coverage normalization: these tests verify
reconciliation, schema and read-only behaviour -- not an economic claim.
"""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import scripts.panel_wave_b_normalization as norm

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "artifacts" / norm.EXP


def _zip_csv(tmp, name, text):
    path = Path(tmp) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name.replace(".zip", ".csv"), text)
    return path


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _plan(months_by_asset, kinds=norm.KINDS):
    series = []
    for asset, months in months_by_asset.items():
        for kind in kinds:
            series.append(
                {
                    "asset": asset,
                    "symbol": f"{asset.upper()}USDT",
                    "kind": kind,
                    "admissible_months": list(months),
                }
            )
    return {
        "hypothesis": "H51",
        "series": series,
        "symbol_map": {a: f"{a.upper()}USDT" for a in months_by_asset},
    }


def _record(asset, kind, month, path, relative):
    return {
        "asset": asset,
        "kind": kind,
        "month": month,
        "archive_path": str(relative),
        "sha256": _sha(path),
        "http_status": 200,
        "content_ok": True,
        "n_csv_rows": 1,
    }


class MonthWindowTests(unittest.TestCase):
    def test_month_window_is_utc_half_open(self):
        start, end = norm.month_window("2023-09")
        self.assertEqual(start % 1000, 0)
        self.assertEqual((end - start) // 86400000, 30)

    def test_december_window_rolls_year(self):
        start, end = norm.month_window("2026-12")
        self.assertEqual((end - start) // 86400000, 31)
        self.assertEqual(norm.month_window("2027-01")[0], end)


class ScopeTests(unittest.TestCase):
    def _h52(self, n=norm.EXPECTED_RECORDS, verdict="WAVEB_ACQUISITION_COMPLETE"):
        return {
            "verdict": verdict,
            "hypothesis": "H52",
            "records": [{"i": i} for i in range(n)],
        }

    def _plan_two(self):
        return _plan(
            {"ark": ["2023-09"] * 38, "astr": ["2023-02"] * 45},
        )

    def test_wrong_h52_verdict_is_a_scope_problem(self):
        problems = norm.scope_problems(
            self._h52(verdict="WAVEB_ACQUISITION_INCOMPLETE"),
            self._plan_two(),
            {},
        )
        self.assertTrue(any("h52_verdict" in p for p in problems))

    def test_forbidden_asset_never_enters_planned_scope(self):
        plan = _plan({"ark": ["2023-09"], "alpha": ["2023-09"]})
        scope = norm.planned_scope(plan)
        self.assertEqual(sorted(scope), ["ark"])
        self.assertNotIn("alpha", json.dumps(scope))

    def test_planned_panels_are_four_canonical_names(self):
        plan = _plan({"ark": ["2023-09"], "astr": ["2023-02"]})
        names = sorted(p[4] for p in norm.expected_panels(plan))
        self.assertEqual(
            names,
            [
                "binance_funding_ARKUSDT.csv",
                "binance_funding_ASTRUSDT.csv",
                "binance_klines_ARKUSDT.csv",
                "binance_klines_ASTRUSDT.csv",
            ],
        )


class ContentValidationTests(unittest.TestCase):
    def test_bad_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _zip_csv(tmp, "a-klines-2023-09.zip", "foo,bar\n1,2\n")
            with self.assertRaises(ValueError):
                norm.parse_archive(path, "klines")

    def test_empty_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _zip_csv(tmp, "a-klines-2023-09.zip", "")
            with self.assertRaises(ValueError):
                norm.parse_archive(path, "klines")

    def test_non_monotone_timestamps_rejected(self):
        rows = ",".join(["0"] * 11)
        text = norm.KLINES_HEADER + "\n" + f"2000000000000,{rows}\n" + f"1000000000000,{rows}\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = _zip_csv(tmp, "a-klines-2023-09.zip", text)
            with self.assertRaises(ValueError):
                norm.parse_archive(path, "klines")

    def test_header_only_funding_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _zip_csv(tmp, "a-funding-2023-09.zip", ",".join(norm.FUNDING_FIELDS) + "\n")
            with self.assertRaises(ValueError):
                norm.parse_archive(path, "funding")

    def test_funding_symbol_column_prepended(self):
        text = norm.render_panel("ARKUSDT", "funding", [["1", "8", "0.01"]])
        self.assertTrue(text.startswith(norm.FUNDING_HEADER + "\n"))
        self.assertEqual(text.strip().splitlines()[1], "ARKUSDT,1,8,0.01")

    def test_klines_render_has_no_symbol_column(self):
        row = ["1"] + ["0"] * 11
        text = norm.render_panel("ARKUSDT", "klines", [row])
        self.assertEqual(text.strip().splitlines()[1], ",".join(row))


class NormalizeSeriesTests(unittest.TestCase):
    def _klines_text(self, month, n=2):
        start, _ = norm.month_window(month)
        lines = [norm.KLINES_HEADER]
        for i in range(n):
            lines.append(f"{start + i * 86400000}," + ",".join(["1.5"] * 11))
        return "\n".join(lines) + "\n"

    def test_out_of_window_rows_are_excluded_and_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            month = "2023-09"
            start, end = norm.month_window(month)
            text = (
                norm.KLINES_HEADER
                + f"\n{start}," + ",".join(["1.0"] * 11)
                + f"\n{end}," + ",".join(["1.0"] * 11)
                + "\n"
            )
            path = _zip_csv(tmp, "ark-klines-2023-09.zip", text)
            rec = _record("ark", "klines", month, path, Path("ark-klines-2023-09.zip"))
            result = norm.normalize_series([rec], tmp, "ark", "ARKUSDT", "klines")
            self.assertEqual(result["n_rows_in"], 2)
            self.assertEqual(result["n_rows_out"], 1)
            self.assertEqual(result["n_rows_out_of_window"], 1)

    def test_duplicate_timestamps_are_counted_not_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            month = "2023-09"
            start, _ = norm.month_window(month)
            row = ",".join(["1.0"] * 11)
            text = norm.KLINES_HEADER + f"\n{start},{row}\n{start},{row}\n"
            path = _zip_csv(tmp, "ark-klines-2023-09.zip", text)
            rec = _record("ark", "klines", month, path, Path("ark-klines-2023-09.zip"))
            result = norm.normalize_series([rec], tmp, "ark", "ARKUSDT", "klines")
            self.assertEqual(result["n_duplicate_timestamps"], 1)
            self.assertEqual(result["n_rows_out"], 2)

    def test_sha256_mismatch_marks_file_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            month = "2023-09"
            path = _zip_csv(tmp, "ark-klines-2023-09.zip", self._klines_text(month))
            rec = _record("ark", "klines", month, path, Path("ark-klines-2023-09.zip"))
            rec["sha256"] = "0" * 64
            result = norm.normalize_series([rec], tmp, "ark", "ARKUSDT", "klines")
            self.assertEqual(result["n_files_bad"], 1)
            self.assertEqual(result["n_files_ok"], 0)
            self.assertEqual(result["n_rows_out"], 0)

    def test_missing_cache_file_is_reported_not_fabricated(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = {
                "asset": "ark",
                "kind": "klines",
                "month": "2023-09",
                "archive_path": "nope.zip",
                "sha256": "0" * 64,
                "http_status": 200,
                "content_ok": True,
                "n_csv_rows": 1,
            }
            result = norm.normalize_series([rec], tmp, "ark", "ARKUSDT", "klines")
            self.assertEqual(result["n_files_bad"], 1)
            self.assertEqual(result["n_rows_out"], 0)
            self.assertEqual(result["bad_files"][0]["status"], "MISSING")


class VerdictTests(unittest.TestCase):
    def _series(self, months, ok=True, oow=0, dup=0, rows=2):
        return {
            "months_seen": list(months),
            "n_files_ok": len(months),
            "n_files_bad": 0 if ok else 1,
            "n_rows_out": rows,
            "n_rows_in": rows,
            "n_rows_out_of_window": oow,
            "n_duplicate_timestamps": dup,
        }

    def _plan(self):
        return _plan({"ark": ["2023-09"], "astr": ["2023-02"]})

    def _series_all(self, **kw):
        return [self._series(["2023-09"], **kw), self._series(["2023-09"], **kw),
                self._series(["2023-02"], **kw), self._series(["2023-02"], **kw)]

    def test_scope_problem_wins(self):
        verdict = norm.evaluate_verdict(["boom"], self._series_all(), self._plan())
        self.assertEqual(verdict, norm.SCOPE_MISMATCH)

    def test_bad_file_is_incomplete(self):
        verdict = norm.evaluate_verdict([], self._series_all(ok=False), self._plan())
        self.assertEqual(verdict, norm.INCOMPLETE)

    def test_uncovered_month_is_incomplete(self):
        series = self._series_all()
        series[0]["months_seen"] = []
        verdict = norm.evaluate_verdict([], series, self._plan())
        self.assertEqual(verdict, norm.INCOMPLETE)

    def test_out_of_window_row_is_incomplete(self):
        verdict = norm.evaluate_verdict([], self._series_all(oow=1), self._plan())
        self.assertEqual(verdict, norm.INCOMPLETE)

    def test_duplicate_timestamp_is_incomplete(self):
        verdict = norm.evaluate_verdict([], self._series_all(dup=1), self._plan())
        self.assertEqual(verdict, norm.INCOMPLETE)

    def test_clean_series_complete(self):
        verdict = norm.evaluate_verdict([], self._series_all(), self._plan())
        self.assertEqual(verdict, norm.COMPLETE)


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audits = sorted((EXP_DIR / "integrity_audit").glob("panel_wave_b_normalization_*.json"))
        if not cls.audits:
            raise unittest.SkipTest("no committed wave-B normalization audit")
        cls.audit = json.loads(cls.audits[-1].read_text())
        cls.panels = EXP_DIR / "panels"

    def test_preregistration_precedes_artifact(self):
        prereg = EXP_DIR / "preregistrations" / "PANELNORM_WAVEB_001_v1.md"
        self.assertTrue(prereg.exists())
        text = prereg.read_text()
        self.assertIn(norm.EXPERIMENT_ID, text)
        self.assertIn("H53", text)

    def test_verdict_and_labels(self):
        self.assertEqual(self.audit["verdict"], norm.COMPLETE)
        self.assertTrue(self.audit["exploratory_only"])
        self.assertFalse(self.audit["confirmatory_claim_allowed"])
        self.assertFalse(self.audit["promotion_allowed"])
        self.assertEqual(self.audit["hypothesis"], "H53")

    def test_all_pinned_inputs_and_frozen_hashes_match(self):
        self.assertTrue(all(self.audit["pinned_input_checks"].values()))
        self.assertTrue(self.audit["frozen_hashes_verified"]["all_match"])

    def test_four_panels_exist_and_match_recorded_hashes(self):
        self.assertEqual(len(self.audit["panels"]), 4)
        for panel in self.audit["panels"]:
            path = ROOT / panel["path"]
            with self.subTest(panel=panel["path"]):
                self.assertTrue(path.exists())
                blob = path.read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), panel["sha256"])
                self.assertEqual(len(blob), panel["n_bytes"])

    def test_row_accounting_identity_and_months(self):
        rec = self.audit["reconciliation"]
        self.assertEqual(rec["n_files_reconciled"], 166)
        self.assertEqual(rec["n_files_bad"], 0)
        self.assertTrue(rec["row_accounting_identity_holds"])
        self.assertEqual(rec["n_rows_out_of_window"], 0)
        self.assertEqual(rec["n_duplicate_timestamps"], 0)
        self.assertEqual(rec["per_asset"]["ark"]["months_klines"], 38)
        self.assertEqual(rec["per_asset"]["astr"]["months_klines"], 45)
        self.assertEqual(rec["per_asset"]["ark"]["files_ok"], 76)
        self.assertEqual(rec["per_asset"]["astr"]["files_ok"], 90)

    def test_panels_cover_exactly_admissible_months(self):
        for panel in self.audit["panels"]:
            text = (ROOT / panel["path"]).read_text().strip().splitlines()
            self.assertEqual(text[0], norm.KLINES_HEADER if panel["kind"] == "klines"
                             else norm.FUNDING_HEADER)
            self.assertEqual(len(text) - 1, panel["n_rows"])
            self.assertEqual(panel["n_months"], len(panel["months"]))


if __name__ == "__main__":
    unittest.main()
