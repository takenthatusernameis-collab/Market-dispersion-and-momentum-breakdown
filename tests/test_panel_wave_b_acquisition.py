"""Tests for the H52 wave-B panel archive acquisition (PANELACQ-WAVEB-001).

Hermetic synthetic fixtures cover per-asset admissible-window selection,
allowlist refusal, content-integrity branches, reconciliation and verdict
branches, plus a skip-guarded integration check against the committed
acquisition artifact and its pinned inputs. No network is used.

The study is EXPLORATORY_ONLY source-coverage acquisition: these tests verify
the scope guard, the archive integrity checks and read-only behaviour -- not an
economic claim.
"""
import hashlib
import io
import json
import unittest
import zipfile
from pathlib import Path

import scripts.panel_wave_b_acquisition as acq

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / acq.EXP / "integrity_audit"


def _plan(asset, symbol, kind, month, url=None):
    return {
        "asset": asset,
        "symbol": symbol,
        "kind": kind,
        "month": month,
        "archive_url": url
        or f"https://data.binance.vision/data/futures/um/monthly/{kind}/{symbol}/{month}.zip",
        "archive_path": f"data/futures/um/monthly/{kind}/{symbol}/{month}.zip",
    }


def _probe(symbol, kind, month, status=200):
    return {"symbol": symbol, "kind": kind, "month": month, "http_status": status}


def _zip_bytes(member, text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, text)
    return buf.getvalue()


KLINES_CSV = (
    "open_time,open,high,low,close,volume,close_time\n"
    "1693526400000,1,1,1,1,1,1693612799999\n"
    "1693612800000,1,1,1,1,1,1693699199999\n"
)
FUNDING_CSV = (
    "calc_time,funding_interval_hours,last_funding_rate\n"
    "1693526400000,8,0.0001\n"
    "1696089600000,8,0.0001\n"
)


class WindowSelectionTests(unittest.TestCase):
    """Wave-B selection honours each asset's own H50 admissible window."""

    def _fixture(self):
        plans = [
            _plan("ark", "ARKUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-08", "2023-09", "2023-10")
        ] + [
            _plan("astr", "ASTRUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ] + [_plan("alice", "ALICEUSDT", "klines", "2023-09")]
        probes = [
            _probe("ARKUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-08", "2023-09", "2023-10")
        ] + [
            _probe("ASTRUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-02",)
        ] + [
            _probe("ASTRUSDT", "klines", "2023-01", 404),
            _probe("ASTRUSDT", "funding", "2023-01", 404),
            _probe("ALICEUSDT", "klines", "2023-09", 200),
        ]
        return plans, probes

    def test_selects_only_each_assets_admissible_months(self):
        plans, probes = self._fixture()
        admissible = {"ark": ["2023-09", "2023-10"], "astr": ["2023-02"]}
        out = acq.select_wave_b_entries(plans, probes, admissible)
        keys = {(e["asset"], e["kind"], e["month"]) for e in out}
        self.assertEqual(
            keys,
            {
                ("ark", "klines", "2023-09"),
                ("ark", "funding", "2023-09"),
                ("ark", "klines", "2023-10"),
                ("ark", "funding", "2023-10"),
                ("astr", "klines", "2023-02"),
                ("astr", "funding", "2023-02"),
            },
        )

    def test_dropped_prelisting_month_never_selected(self):
        plans, probes = self._fixture()
        admissible = {"ark": ["2023-09", "2023-10"], "astr": ["2023-02"]}
        out = acq.select_wave_b_entries(plans, probes, admissible)
        self.assertFalse(any(e["month"] == "2023-08" for e in out))
        self.assertFalse(any(e["month"] == "2023-01" for e in out))

    def test_absent_status_excluded_even_inside_window(self):
        plans, probes = self._fixture()
        admissible = {"astr": ["2023-01", "2023-02"]}
        out = acq.select_wave_b_entries(plans, probes, admissible)
        self.assertEqual({e["month"] for e in out}, {"2023-02"})

    def test_wave_a_and_alpha_never_selected(self):
        plans, probes = self._fixture()
        admissible = {"ark": ["2023-09"], "astr": ["2023-02"], "alice": ["2023-09"]}
        out = acq.select_wave_b_entries(plans, probes, admissible)
        self.assertFalse({e["asset"] for e in out} & set(acq.FORBIDDEN_ASSETS))

    def test_select_is_deterministic_and_sorted(self):
        plans, probes = self._fixture()
        admissible = {"ark": ["2023-09", "2023-10"], "astr": ["2023-02"]}
        a = acq.select_wave_b_entries(plans, probes, admissible)
        b = acq.select_wave_b_entries(list(reversed(plans)), probes, admissible)
        self.assertEqual(a, b)
        self.assertEqual(a, sorted(a, key=lambda r: (r["asset"], r["kind"], r["month"])))


class TrimDecisionParsingTests(unittest.TestCase):
    def test_admissible_months_are_deduplicated_and_ordered(self):
        per_asset = {"ark": {"admissible_study_months": ["2023-09", "2023-09", "2023-10"]}}
        self.assertEqual(
            acq.admissible_months_by_asset(per_asset), {"ark": ["2023-09", "2023-10"]}
        )

    def test_dropped_months_read_from_trim(self):
        per_asset = {"ark": {"dropped_required_months": ["2023-01", "2023-02"]}}
        self.assertEqual(
            acq.dropped_months_by_asset(per_asset), {"ark": ["2023-01", "2023-02"]}
        )


class AllowlistTests(unittest.TestCase):
    def test_allowlisted_url_accepted(self):
        url = "https://data.binance.vision/data/futures/um/monthly/klines/ARKUSDT/2023-09.zip"
        self.assertTrue(acq.is_allowlisted_url(url, {url}))

    def test_url_absent_from_plan_rejected(self):
        url = "https://data.binance.vision/data/futures/um/monthly/klines/ARKUSDT/2023-09.zip"
        self.assertFalse(acq.is_allowlisted_url(url, set()))

    def test_off_base_url_rejected(self):
        url = "https://example.com/data/futures/um/monthly/klines/ARKUSDT/2023-09.zip"
        self.assertFalse(acq.is_allowlisted_url(url, {url}))


class ContentIntegrityTests(unittest.TestCase):
    def test_valid_klines_archive(self):
        payload = _zip_bytes("ARKUSDT-1d-2023-09.csv", KLINES_CSV)
        out = acq.verify_archive_bytes(payload, "klines")
        self.assertTrue(out["is_zip"])
        self.assertTrue(out["content_ok"], out["content_error"])
        self.assertEqual(out["n_csv_rows"], 2)
        self.assertEqual(out["csv_header"][0], "open_time")

    def test_valid_funding_archive_uses_calc_time(self):
        payload = _zip_bytes("ARKUSDT-fundingRate-2023-09.csv", FUNDING_CSV)
        out = acq.verify_archive_bytes(payload, "funding")
        self.assertTrue(out["content_ok"], out["content_error"])
        self.assertEqual(out["csv_header"][0], "calc_time")

    def test_non_zip_payload_flagged(self):
        out = acq.verify_archive_bytes(b"not a zip at all", "klines")
        self.assertFalse(out["is_zip"])
        self.assertFalse(out["content_ok"])

    def test_wrong_header_flagged(self):
        payload = _zip_bytes("x.csv", FUNDING_CSV)
        out = acq.verify_archive_bytes(payload, "klines")
        self.assertFalse(out["content_ok"])
        self.assertIn("unexpected header", out["content_error"])

    def test_header_only_csv_flagged(self):
        payload = _zip_bytes("x.csv", "open_time,open\n")
        out = acq.verify_archive_bytes(payload, "klines")
        self.assertFalse(out["content_ok"])
        self.assertEqual(out["n_csv_rows"], 0)

    def test_non_monotone_timestamps_flagged(self):
        text = "open_time,open\n1693612800000,1\n1693526400000,1\n"
        out = acq.verify_archive_bytes(_zip_bytes("x.csv", text), "klines")
        self.assertFalse(out["content_ok"])
        self.assertIn("monotonically", out["content_error"])


class ReconciliationTests(unittest.TestCase):
    def _entries(self):
        return [
            {"asset": "ark", "symbol": "ARKUSDT", "kind": k, "month": m}
            for k in ("klines", "funding")
            for m in ("2023-09", "2023-10")
        ]

    def _record(self, entry, ok=True):
        rec = dict(entry)
        rec.update(
            {
                "http_status": 200 if ok else 404,
                "sha256": "a" * 64 if ok else None,
                "content_ok": ok,
                "bytes_downloaded": 10 if ok else 0,
            }
        )
        return rec

    def test_complete_reconciliation(self):
        entries = self._entries()
        recon = acq.reconcile(entries, [self._record(e) for e in entries])
        self.assertEqual(recon["n_expected"], 4)
        self.assertEqual(recon["n_content_ok"], 4)
        self.assertEqual(recon["n_missing"], 0)
        self.assertEqual(recon["n_extra"], 0)
        self.assertEqual(recon["bytes_content_ok"], 40)
        self.assertEqual(acq.decide_verdict(True, recon), acq.ACQ_COMPLETE)

    def test_missing_file_blocks_complete_verdict(self):
        entries = self._entries()
        recon = acq.reconcile(entries, [self._record(e) for e in entries[:-1]])
        self.assertEqual(recon["n_missing"], 1)
        self.assertEqual(acq.decide_verdict(True, recon), acq.ACQ_INCOMPLETE)

    def test_bad_content_blocks_complete_verdict(self):
        entries = self._entries()
        records = [self._record(e) for e in entries]
        records[0]["content_ok"] = False
        recon = acq.reconcile(entries, records)
        self.assertEqual(acq.decide_verdict(True, recon), acq.ACQ_INCOMPLETE)

    def test_extra_wave_a_record_detected(self):
        entries = self._entries()
        extra = {"asset": "alice", "symbol": "ALICEUSDT", "kind": "klines", "month": "2023-09"}
        records = [self._record(e) for e in entries] + [self._record(extra)]
        recon = acq.reconcile(entries, records)
        self.assertEqual(recon["n_extra"], 1)
        self.assertEqual(acq.decide_verdict(True, recon), acq.ACQ_INCOMPLETE)

    def test_scope_mismatch_overrides(self):
        recon = acq.reconcile(self._entries(), [])
        self.assertEqual(acq.decide_verdict(False, recon), acq.SCOPE_MISMATCH)


class CommittedInputScopeTests(unittest.TestCase):
    def test_build_plan_scope_is_the_pinned_166_file_wave_b(self):
        plan = acq.build_plan()
        self.assertTrue(plan["scope_ok"], plan["scope_checks"])
        self.assertEqual(len(plan["entries"]), acq.EXPECTED_WAVE_B_FILES)
        self.assertEqual(plan["per_asset_counts"], acq.EXPECTED_FILES_PER_ASSET)
        self.assertEqual(len(plan["study_months"]), 46)
        self.assertEqual(
            tuple(sorted({e["asset"] for e in plan["entries"]})),
            acq.EXPECTED_WAVE_B_ASSETS,
        )
        self.assertFalse({e["asset"] for e in plan["entries"]} & set(acq.FORBIDDEN_ASSETS))
        self.assertEqual(plan["dropped_leak"], [])


@unittest.skipUnless(
    any(ARTIFACT_DIR.glob("panel_wave_b_acquisition_*.json")),
    "committed wave-B acquisition artifact not present",
)
class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = sorted(ARTIFACT_DIR.glob("panel_wave_b_acquisition_*.json"))[-1]
        cls.path = path
        cls.audit = json.loads(path.read_text(encoding="utf-8"))

    def test_artifact_is_complete_and_scoped(self):
        a = self.audit
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertEqual(a["hypothesis"], "H52")
        self.assertTrue(a["scope_ok"], a["scope_checks"])
        self.assertEqual(a["verdict"], acq.ACQ_COMPLETE)
        self.assertEqual(a["reconciliation"]["n_expected"], acq.EXPECTED_WAVE_B_FILES)
        self.assertEqual(a["reconciliation"]["n_content_ok"], acq.EXPECTED_WAVE_B_FILES)
        self.assertEqual(a["reconciliation"]["n_missing"], 0)
        self.assertEqual(a["reconciliation"]["n_extra"], 0)
        self.assertEqual(len(a["records"]), acq.EXPECTED_WAVE_B_FILES)
        self.assertEqual(
            {k: v["ok"] for k, v in a["reconciliation"]["per_asset"].items()},
            acq.EXPECTED_FILES_PER_ASSET,
        )

    def test_every_record_is_hashed_and_content_verified(self):
        for rec in self.audit["records"]:
            self.assertEqual(rec["http_status"], 200)
            self.assertRegex(rec["sha256"], r"^[0-9a-f]{64}$")
            self.assertTrue(rec["content_ok"], rec.get("content_error"))
            self.assertGreater(rec["n_csv_rows"], 0)

    def test_only_trimmed_wave_b_assets_and_months_acquired(self):
        assets = {r["asset"] for r in self.audit["records"]}
        self.assertFalse(assets & set(acq.FORBIDDEN_ASSETS))
        self.assertEqual(assets, set(acq.EXPECTED_WAVE_B_ASSETS))
        admissible = self.audit["scope_declaration"]["admissible_months_by_asset"]
        for rec in self.audit["records"]:
            self.assertIn(rec["month"], admissible[rec["asset"]])

    def test_frozen_hashes_unchanged_and_no_confirmatory_claim(self):
        a = self.audit
        self.assertTrue(a["all_frozen_hashes_match"])
        self.assertFalse(a["confirmatory_claim_allowed"])
        self.assertFalse(a["promotion_allowed"])
        for name, expected in acq.EXPECTED_FROZEN_SHA256.items():
            self.assertEqual(a["frozen_hashes_verified"][name]["actual"], expected)

    def test_records_hash_is_canonical(self):
        blob = json.dumps(
            self.audit["records"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        self.assertEqual(
            hashlib.sha256(blob.encode("utf-8")).hexdigest(),
            self.audit["records_canonical_sha256"],
        )

    def test_pinned_inputs_still_match(self):
        self.assertEqual(acq._file_sha256(acq.H41_PLAN), acq.H41_PLAN_SHA256)
        self.assertEqual(acq._file_sha256(acq.H43_PROBE), acq.H43_PROBE_SHA256)
        self.assertEqual(acq._file_sha256(acq.H50_TRIM), acq.H50_TRIM_FILE_SHA256)


if __name__ == "__main__":
    unittest.main()
