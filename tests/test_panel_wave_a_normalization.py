"""Tests for the H56 wave-A extension panel normalization (PANELNORM-WAVEA-001).

Hermetic synthetic fixtures cover the H49 scope guard, month-window accounting,
archive content re-validation, duplicate detection, funding symbol prefixing,
row accounting, every verdict branch and the digest-pinned fetch path, plus
skip-guarded integration checks binding the committed panels to the committed
audit artifact. No network is used.

The study is EXPLORATORY_ONLY source-coverage normalization: these tests verify
reconciliation, schema, coverage accounting and read-only behaviour -- not an
economic claim.
"""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import scripts.panel_wave_a_normalization as norm

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "artifacts" / norm.EXP


def _zip_bytes(csv_text, member="XUSDT-klines-2023-01.csv"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, csv_text)
    return buf.getvalue()


def _write_zip(tmp, rel, csv_text, member="XUSDT-klines-2023-01.csv"):
    path = Path(tmp) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_zip_bytes(csv_text, member=member))
    return path


def _klines_text(stamps):
    lines = [norm.KLINES_HEADER]
    for ts in stamps:
        lines.append(f"{ts},1.0,1.1,0.9,1.05,10.0,{ts + 1},10.0,2,5.0,5.0,0")
    return "\n".join(lines) + "\n"


def _funding_text(stamps):
    lines = [",".join(norm.FUNDING_FIELDS)]
    for ts in stamps:
        lines.append(f"{ts},8,0.0001")
    return "\n".join(lines) + "\n"


def _synthetic_audit(months, assets=("alice", "ankr")):
    records = []
    for asset in assets:
        symbol = f"{asset.upper()}USDT"
        for kind in norm.KINDS:
            for month in months:
                stem = (
                    f"{symbol}-1d-{month}"
                    if kind == "klines"
                    else f"{symbol}-fundingRate-{month}"
                )
                folder = "klines" if kind == "klines" else "fundingRate"
                rel = f"data/futures/um/monthly/{folder}/{symbol}/{stem}.zip"
                records.append(
                    {
                        "archive_path": rel,
                        "archive_url": f"{norm.SOURCE_BASE}/{rel}",
                        "asset": asset,
                        "symbol": symbol,
                        "kind": kind,
                        "month": month,
                        "sha256": "0" * 64,
                        "http_status": 200,
                        "content_ok": True,
                        "n_csv_rows": 1,
                    }
                )
    return {
        "hypothesis": "H49",
        "verdict": "WAVEA_ACQUISITION_COMPLETE",
        "scope_declaration": {"study_months": list(months)},
        "records": records,
    }


class MonthWindowTests(unittest.TestCase):
    def test_month_window_is_utc_half_open(self):
        start, end = norm.month_window("2023-01")
        self.assertEqual(start % 1000, 0)
        self.assertEqual((end - start) // 86400000, 31)

    def test_december_window_rolls_year(self):
        start, end = norm.month_window("2026-12")
        self.assertEqual((end - start) // 86400000, 31)
        self.assertEqual(norm.month_window("2027-01")[0], end)


class ScopeTests(unittest.TestCase):
    def test_wrong_h49_verdict_is_a_scope_problem(self):
        audit = _synthetic_audit(["2023-01"])
        audit["verdict"] = "WAVEA_ACQUISITION_INCOMPLETE"
        problems = norm.scope_problems(audit, records_pin=norm._canonical_sha256(audit["records"]))
        self.assertTrue(any("verdict" in p for p in problems))

    def test_wrong_hypothesis_is_a_scope_problem(self):
        audit = _synthetic_audit(["2023-01"])
        audit["hypothesis"] = "H52"
        problems = norm.scope_problems(audit, records_pin=norm._canonical_sha256(audit["records"]))
        self.assertTrue(any("h49_hypothesis" in p for p in problems))

    def test_record_count_mismatch_is_a_scope_problem(self):
        audit = _synthetic_audit(["2023-01"])
        problems = norm.scope_problems(audit, records_pin=norm._canonical_sha256(audit["records"]))
        self.assertTrue(any("record_count" in p for p in problems))

    def test_canonical_pin_mismatch_is_a_scope_problem(self):
        audit = _synthetic_audit(["2023-01"])
        problems = norm.scope_problems(audit, records_pin="f" * 64)
        self.assertIn("h49_records_canonical_sha256 mismatch", problems)

    def test_forbidden_asset_and_off_base_url_are_scope_problems(self):
        audit = _synthetic_audit(["2023-01"])
        audit["records"][0]["asset"] = "ark"
        problems = norm.scope_problems(audit, records_pin=norm._canonical_sha256(audit["records"]))
        self.assertTrue(any("forbidden_asset" in p for p in problems))

        audit2 = _synthetic_audit(["2023-01"])
        audit2["records"][0]["archive_url"] = "https://example.com/x.zip"
        problems2 = norm.scope_problems(
            audit2, records_pin=norm._canonical_sha256(audit2["records"])
        )
        self.assertTrue(any("off_documented_base" in p for p in problems2))

    def test_planned_scope_uses_declared_months_only(self):
        audit = _synthetic_audit(["2023-01", "2023-02"])
        audit["scope_declaration"]["study_months"] = ["2023-01"]
        scope = norm.planned_scope(audit)
        self.assertEqual(scope["alice"]["klines"], ["2023-01"])
        self.assertEqual(scope["alice"]["funding"], ["2023-01"])

    def test_expected_panels_are_canonical_names(self):
        audit = _synthetic_audit(["2023-01"])
        panels = norm.expected_panels(audit)
        self.assertEqual(len(panels), norm.EXPECTED_PANELS)
        names = {p[4] for p in panels}
        self.assertIn("binance_klines_ALICEUSDT.csv", names)
        self.assertIn("binance_funding_ANKRUSDT.csv", names)
        self.assertEqual(len(names), norm.EXPECTED_PANELS)

    def test_symbol_map_falls_back_to_upper_symbol(self):
        audit = {"records": [{"asset": "alice", "symbol": "ALICEUSDT"}]}
        self.assertEqual(norm.symbol_map(audit), {"alice": "ALICEUSDT"})


class ParseTests(unittest.TestCase):
    def test_bad_header_is_rejected(self):
        blob = _zip_bytes("alpha,beta\n1,2\n")
        with self.assertRaises(ValueError):
            norm.parse_archive_bytes(blob, "klines")

    def test_empty_csv_is_rejected(self):
        blob = _zip_bytes("")
        with self.assertRaises(ValueError):
            norm.parse_archive_bytes(blob, "klines")

    def test_non_monotone_timestamps_rejected(self):
        blob = _zip_bytes(_klines_text([2000, 1000]))
        with self.assertRaises(ValueError):
            norm.parse_archive_bytes(blob, "klines")

    def test_header_only_funding_is_rejected(self):
        blob = _zip_bytes(norm.FUNDING_HEADER + "\n", member="f.csv")
        with self.assertRaises(ValueError):
            norm.parse_archive_bytes(blob, "funding")

    def test_two_csv_members_rejected(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("a.csv", _klines_text([1000]))
            zf.writestr("b.csv", _klines_text([1000]))
        with self.assertRaises(ValueError):
            norm.parse_archive_bytes(buf.getvalue(), "klines")

    def test_funding_header_only_once_and_rows_parsed(self):
        header, rows = norm.parse_archive_bytes(
            _zip_bytes(_funding_text([1000, 2000]), member="f.csv"), "funding"
        )
        self.assertEqual(header, norm.FUNDING_FIELDS)
        self.assertEqual([r[0] for r in rows], [1000, 2000])


class RenderTests(unittest.TestCase):
    def test_funding_symbol_column_prepended(self):
        text = norm.render_panel("ALICEUSDT", "funding", [["1000", "8", "0.0001"]])
        self.assertEqual(text.splitlines()[0], norm.FUNDING_HEADER)
        self.assertEqual(text.splitlines()[1], "ALICEUSDT,1000,8,0.0001")

    def test_klines_render_has_no_symbol_column(self):
        text = norm.render_panel(
            "ALICEUSDT", "klines", [["1000", "1", "1", "1", "1", "1", "2", "1", "1", "1", "1", "0"]]
        )
        self.assertEqual(text.splitlines()[0], norm.KLINES_HEADER)
        self.assertFalse(text.splitlines()[1].startswith("ALICEUSDT"))


class NormalizeSeriesTests(unittest.TestCase):
    def _record(self, month, rel, path):
        return {
            "asset": "alice",
            "kind": "klines",
            "month": month,
            "archive_path": rel,
            "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            "http_status": 200,
            "content_ok": True,
            "n_csv_rows": 1,
        }

    def test_out_of_window_rows_are_excluded_and_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            start, end = norm.month_window("2023-01")
            rel = "data/futures/um/monthly/klines/XUSDT/XUSDT-1d-2023-01.zip"
            path = _write_zip(tmp, rel, _klines_text([start, end]))
            rec = self._record("2023-01", rel, path)
            result = norm.normalize_series([rec], tmp, "alice", "ALICEUSDT", "klines")
            self.assertEqual(result["n_rows_in"], 2)
            self.assertEqual(result["n_rows_out"], 1)
            self.assertEqual(result["n_rows_out_of_window"], 1)
            self.assertEqual(result["n_duplicate_timestamps"], 0)

    def test_duplicate_timestamps_are_counted_not_collapsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            start, _ = norm.month_window("2023-01")
            rel = "data/futures/um/monthly/klines/XUSDT/XUSDT-1d-2023-01.zip"
            path = _write_zip(tmp, rel, _klines_text([start, start]))
            rec = self._record("2023-01", rel, path)
            result = norm.normalize_series([rec], tmp, "alice", "ALICEUSDT", "klines")
            self.assertEqual(result["n_duplicate_timestamps"], 1)
            self.assertEqual(result["n_rows_out"], 2)

    def test_sha256_mismatch_marks_file_bad(self):
        with tempfile.TemporaryDirectory() as tmp:
            rel = "data/futures/um/monthly/klines/XUSDT/XUSDT-1d-2023-01.zip"
            path = _write_zip(tmp, rel, _klines_text([norm.month_window("2023-01")[0]]))
            rec = self._record("2023-01", rel, path)
            rec["sha256"] = "f" * 64
            result = norm.normalize_series([rec], tmp, "alice", "ALICEUSDT", "klines")
            self.assertEqual(result["n_files_bad"], 1)
            self.assertEqual(result["bad_files"][0]["status"], "SHA256_MISMATCH")

    def test_missing_cache_file_is_reported_not_fabricated(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = {
                "asset": "alice",
                "kind": "klines",
                "month": "2023-01",
                "archive_path": "nope/x.zip",
                "sha256": "0" * 64,
                "http_status": 200,
                "content_ok": True,
                "n_csv_rows": 1,
            }
            result = norm.normalize_series([rec], tmp, "alice", "ALICEUSDT", "klines")
            self.assertEqual(result["n_files_bad"], 1)
            self.assertEqual(result["bad_files"][0]["status"], "MISSING")
            self.assertEqual(result["n_rows_out"], 0)


class FetchTests(unittest.TestCase):
    class _Response:
        def __init__(self, blob, status=200):
            self._blob = blob
            self.status = status

        def read(self):
            return self._blob

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def test_matching_digest_writes_cache_and_flags_pinned_url(self):
        blob = _zip_bytes(_klines_text([1000]))
        audit = _synthetic_audit(["2023-01"], assets=("alice",))
        for rec in audit["records"]:
            rec["sha256"] = hashlib.sha256(blob).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            results = norm.fetch_archives(
                audit, tmp, opener=lambda url: self._Response(blob)
            )
            self.assertEqual([r["status"] for r in results], ["OK", "OK"])
            self.assertTrue(all(r["url_is_pinned"] for r in results))
            self.assertTrue(all(r["sha256_match"] for r in results))
            for rec in audit["records"]:
                self.assertTrue((Path(tmp) / rec["archive_path"]).exists())

    def test_digest_mismatch_is_reported_and_not_written(self):
        blob = _zip_bytes(_klines_text([1000]))
        audit = _synthetic_audit(["2023-01"], assets=("alice",))
        with tempfile.TemporaryDirectory() as tmp:
            results = norm.fetch_archives(
                audit, tmp, opener=lambda url: self._Response(blob)
            )
            self.assertEqual([r["status"] for r in results], ["SHA256_MISMATCH"] * 2)
            self.assertFalse((Path(tmp) / audit["records"][0]["archive_path"]).exists())

    def test_fetch_failure_after_retry_is_recorded(self):
        def boom(url):
            raise OSError("connection refused")

        audit = _synthetic_audit(["2023-01"], assets=("alice",))
        with tempfile.TemporaryDirectory() as tmp:
            results = norm.fetch_archives(audit, tmp, opener=boom, max_attempts=2)
            self.assertEqual(results[0]["status"], "FETCH_FAILED")
            self.assertIn("OSError", results[0]["error"])


class VerdictTests(unittest.TestCase):
    def _series(self, months, **overrides):
        base = {
            "asset": "alice",
            "symbol": "ALICEUSDT",
            "kind": "klines",
            "rows": [],
            "months_seen": list(months),
            "n_files_ok": len(months),
            "n_files_bad": 0,
            "bad_files": [],
            "n_rows_in": 1,
            "n_rows_out": 1,
            "n_rows_out_of_window": 0,
            "n_duplicate_timestamps": 0,
            "files": [],
        }
        base.update(overrides)
        return base

    def _audit(self, months):
        return _synthetic_audit(months, assets=("alice",))

    def test_scope_problem_wins(self):
        audit = self._audit(["2023-01"])
        verdict = norm.evaluate_verdict(["bad"], [self._series(["2023-01"])] * 2, audit)
        self.assertEqual(verdict, norm.SCOPE_MISMATCH)

    def test_bad_file_is_incomplete(self):
        audit = self._audit(["2023-01"])
        series = [self._series(["2023-01"], n_files_bad=1), self._series(["2023-01"])]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.INCOMPLETE)

    def test_uncovered_month_is_incomplete(self):
        audit = self._audit(["2023-01"])
        series = [self._series([]), self._series(["2023-01"])]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.INCOMPLETE)

    def test_out_of_window_row_is_incomplete(self):
        audit = self._audit(["2023-01"])
        series = [
            self._series(["2023-01"], n_rows_out_of_window=1),
            self._series(["2023-01"]),
        ]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.INCOMPLETE)

    def test_duplicate_timestamp_is_incomplete(self):
        audit = self._audit(["2023-01"])
        series = [
            self._series(["2023-01"], n_duplicate_timestamps=1),
            self._series(["2023-01"]),
        ]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.INCOMPLETE)

    def test_row_identity_failure_is_incomplete(self):
        audit = self._audit(["2023-01"])
        series = [
            self._series(["2023-01"], n_rows_in=2, n_rows_out=1),
            self._series(["2023-01"]),
        ]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.INCOMPLETE)

    def test_clean_series_complete(self):
        audit = self._audit(["2023-01"])
        series = [self._series(["2023-01"]), self._series(["2023-01"])]
        self.assertEqual(norm.evaluate_verdict([], series, audit), norm.COMPLETE)


class FrozenHashTests(unittest.TestCase):
    def test_frozen_hashes_match(self):
        details = norm.frozen_hashes()
        if not all(Path(ROOT / v["path"]).exists() for v in details.values()):
            self.skipTest("frozen artifacts absent in this checkout")
        for name, info in details.items():
            with self.subTest(frozen=name):
                self.assertTrue(info["match"], f"{name} drifted")


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        audits = sorted((EXP_DIR / "integrity_audit").glob("panel_wave_a_normalization_*.json"))
        cls.audit_path = audits[-1] if audits else None
        cls.audit = json.loads(cls.audit_path.read_text()) if cls.audit_path else None

    def setUp(self):
        if self.audit is None:
            self.skipTest("no committed wave-A normalization audit in this checkout")

    def test_preregistration_precedes_artifact(self):
        prereg = (ROOT / self.audit["preregistration"]).read_text()
        created = [ln for ln in prereg.splitlines() if ln.startswith("- Created:")][0]
        created_ts = created.split("Created:", 1)[1].split()[0]
        self.assertLess(created_ts, self.audit["computed_utc"])

    def test_verdict_and_labels(self):
        self.assertEqual(self.audit["verdict"], norm.COMPLETE)
        self.assertTrue(self.audit["exploratory_only"])
        self.assertFalse(self.audit["confirmatory_claim_allowed"])
        self.assertFalse(self.audit["promotion_allowed"])
        self.assertEqual(self.audit["hypothesis"], "H56")

    def test_pinned_inputs_and_frozen_hashes_match(self):
        self.assertTrue(all(self.audit["pinned_input_checks"].values()))
        self.assertTrue(self.audit["frozen_hashes_verified"]["all_match"])

    def test_fourteen_panels_exist_and_match_recorded_hashes(self):
        panels = self.audit["panels"]
        self.assertEqual(len(panels), norm.EXPECTED_PANELS)
        for panel in panels:
            path = ROOT / panel["path"]
            with self.subTest(panel=panel["path"]):
                self.assertTrue(path.exists())
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), panel["sha256"]
                )

    def test_row_accounting_identity_and_months(self):
        rec = self.audit["reconciliation"]
        self.assertTrue(rec["row_accounting_identity_holds"])
        self.assertEqual(rec["n_files_reconciled"], norm.EXPECTED_RECORDS)
        self.assertEqual(rec["n_files_bad"], 0)
        self.assertEqual(rec["n_rows_out_of_window"], 0)
        self.assertEqual(rec["n_duplicate_timestamps"], 0)
        self.assertEqual(self.audit["fetch"]["n_ok"], norm.EXPECTED_RECORDS)
        self.assertTrue(self.audit["fetch"]["all_digests_match_h49"])

    def test_scope_is_wave_a_seven_assets(self):
        scope = self.audit["scope_declaration"]
        self.assertEqual(scope["assets"], list(norm.EXPECTED_ASSETS))
        self.assertEqual(scope["n_study_months"], 46)
        self.assertTrue(all(self.audit["scope_checks"].values()))
        self.assertEqual(self.audit["scope_problems"], [])

    def test_panels_cover_exactly_declared_months(self):
        for series in self.audit["series"]:
            with self.subTest(asset=series["asset"], kind=series["kind"]):
                self.assertEqual(series["months_seen"], sorted(series["months_seen"]))
                self.assertEqual(len(series["months_seen"]), 46)

    def test_coverage_breadth_block_is_consistent(self):
        breadth = self.audit["coverage_breadth"]
        self.assertEqual(len(breadth["per_month"]), 46)
        self.assertEqual(
            breadth["max_month_breadth"],
            max(breadth["per_month"].values()),
        )
        self.assertEqual(
            breadth["n_months_breadth_ge_20"],
            sum(1 for v in breadth["per_month"].values() if v >= 20),
        )
        self.assertEqual(len(breadth["fresh_window_months"]), 22)
        for month, count in breadth["fresh_window_breadth"].items():
            self.assertEqual(count, breadth["per_month"][month])
        self.assertEqual(
            breadth["arity_requirement_met_in_fresh_window"],
            min(breadth["fresh_window_breadth"].values()) >= 20,
        )


if __name__ == "__main__":
    unittest.main()
