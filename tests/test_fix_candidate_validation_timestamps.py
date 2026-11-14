"""Hermetic tests for scripts/fix_candidate_validation_timestamps.py.

Pure seam: ``time_first``/``time_last`` are recomputed as the min/max of each
raw payload's row times (the CoinMetrics timeseries endpoint paginates
descending, so the raw file's first/last rows are not the earliest/latest).
Everything here uses synthetic records in a temp dir and monkeypatches the
module-level ``VAL_PATH``; no network, no committed-panel reads/writes, no
frozen-artifact mutation.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import fix_candidate_validation_timestamps as module

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"


def _write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _entry(raw_path, time_first, time_last, status="ok", metric="CapMrktEstUSD"):
    return {
        "asset": "AA",
        "metrics": {
            metric: {
                "status": status,
                "raw_path": str(raw_path),
                "time_first": time_first,
                "time_last": time_last,
            }
        },
    }


class FixCandidateValidationTimestampsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fix_candidate_validation_timestamps_", dir=ROOT))
        self.val = self.tmp / "candidate_batch_validation.json"
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _run(self, entries):
        _write_json(self.val, {"candidates_processed": entries, "experiment_id": EXP})
        with mock.patch.object(module, "VAL_PATH", self.val):
            return module.main()

    def _loaded(self):
        return json.loads(self.val.read_text(encoding="utf-8"))

    def test_recomputes_inverted_boundaries_and_sets_note(self):
        raw = self.tmp / "raw.json"
        raw.write_text(
            json.dumps([
                {"time": "2026-10-05T00:00:00Z"},
                {"time": "2026-10-01T00:00:00Z"},
                {"time": "2026-10-03T00:00:00Z"},
            ]),
            encoding="utf-8",
        )
        entries = [_entry(raw, "2026-10-05T00:00:00Z", "2026-10-01T00:00:00Z")]
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-01T00:00:00Z")
        self.assertEqual(m["time_last"], "2026-10-05T00:00:00Z")
        self.assertIn("sorting rows by time ascending", m["time_order_note"])
        self.assertEqual(m["status"], "ok")

    def test_already_correct_boundaries_leave_values_untouched(self):
        raw = self.tmp / "raw.json"
        raw.write_text(json.dumps([{"time": "2026-10-01T00:00:00Z"}]), encoding="utf-8")
        entries = [_entry(raw, "2026-10-01T00:00:00Z", "2026-10-01T00:00:00Z")]
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-01T00:00:00Z")
        self.assertEqual(m["time_last"], "2026-10-01T00:00:00Z")

    def test_missing_raw_file_increments_missing_and_returns_one(self):
        missing = self.tmp / "does_not_exist.json"
        entries = [_entry(missing, "2026-10-01T00:00:00Z", "2026-10-05T00:00:00Z")]
        rc = self._run(entries)
        self.assertEqual(rc, 1)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-01T00:00:00Z")
        self.assertEqual(m["time_last"], "2026-10-05T00:00:00Z")

    def test_skips_non_ok_status(self):
        raw = self.tmp / "raw.json"
        raw.write_text(json.dumps([{"time": "2026-10-01T00:00:00Z"}]), encoding="utf-8")
        entries = [_entry(raw, "2026-10-05T00:00:00Z", "2026-10-01T00:00:00Z", status="asset_not_served")]
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-05T00:00:00Z")
        self.assertEqual(m["time_last"], "2026-10-01T00:00:00Z")

    def test_skips_missing_raw_path(self):
        entries = [_entry(None, "2026-10-05T00:00:00Z", "2026-10-01T00:00:00Z")]
        entries[0]["metrics"]["CapMrktEstUSD"].pop("raw_path")
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-05T00:00:00Z")

    def test_skips_raw_without_times(self):
        raw = self.tmp / "raw.json"
        raw.write_text(json.dumps([{}, {"time": None}]), encoding="utf-8")
        entries = [_entry(raw, "2026-10-05T00:00:00Z", "2026-10-01T00:00:00Z")]
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        m = self._loaded()["candidates_processed"][0]["metrics"]["CapMrktEstUSD"]
        self.assertEqual(m["time_first"], "2026-10-05T00:00:00Z")

    def test_both_metrics_processed_independently(self):
        raw_est = self.tmp / "raw_est.json"
        raw_cur = self.tmp / "raw_cur.json"
        raw_est.write_text(json.dumps([{"time": "2026-10-02T00:00:00Z"}, {"time": "2026-10-01T00:00:00Z"}]), encoding="utf-8")
        raw_cur.write_text(json.dumps([{"time": "2026-10-04T00:00:00Z"}, {"time": "2026-10-03T00:00:00Z"}]), encoding="utf-8")
        entries = [{
            "asset": "AA",
            "metrics": {
                "CapMrktEstUSD": {"status": "ok", "raw_path": str(raw_est), "time_first": "2026-10-02T00:00:00Z", "time_last": "2026-10-01T00:00:00Z"},
                "CapMrktCurUSD": {"status": "ok", "raw_path": str(raw_cur), "time_first": "2026-10-04T00:00:00Z", "time_last": "2026-10-03T00:00:00Z"},
            },
        }]
        rc = self._run(entries)
        self.assertEqual(rc, 0)
        got = self._loaded()["candidates_processed"][0]["metrics"]
        self.assertEqual(got["CapMrktEstUSD"]["time_first"], "2026-10-01T00:00:00Z")
        self.assertEqual(got["CapMrktEstUSD"]["time_last"], "2026-10-02T00:00:00Z")
        self.assertEqual(got["CapMrktCurUSD"]["time_first"], "2026-10-03T00:00:00Z")
        self.assertEqual(got["CapMrktCurUSD"]["time_last"], "2026-10-04T00:00:00Z")

    def test_empty_candidates_processed(self):
        rc = self._run([])
        self.assertEqual(rc, 0)
        self.assertEqual(self._loaded()["candidates_processed"], [])


if __name__ == "__main__":
    unittest.main()
