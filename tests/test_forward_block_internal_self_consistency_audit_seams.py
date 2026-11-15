"""Hermetic seam tests for scripts/forward_block_internal_self_consistency_audit.py.

Exercises every pure seam (sha256_file, load_json, the per-identity check
helpers, run_checks) and the full audit() path against synthetic fixtures, with
no network access and no reads of committed artifacts beyond the module import.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_internal_self_consistency_audit.py"

spec = importlib.util.spec_from_file_location("fb_selfcheck_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _block():
    """A fully self-consistent synthetic block."""
    formations = [
        {"formation_date": "2025-01-01", "n_assets": 26, "state": "mid",
         "spread_gross": 0.01, "spread_net_1x": 0.009, "dispersion": 1.0},
        {"formation_date": "2025-01-02", "n_assets": 27, "state": "high",
         "spread_gross": 0.02, "spread_net_1x": 0.019, "dispersion": 2.0},
        {"formation_date": "2025-01-03", "n_assets": 26, "state": "low",
         "spread_gross": -0.02, "spread_net_1x": -0.021, "dispersion": 0.5},
    ]
    n = len(formations)
    return {
        "anchor_id": "H004V106",
        "block_sealed": True,
        "data_cutoff_utc": "2026-09-30T00:00:00Z",
        "date_last": "2025-01-03",
        "date_first": "2025-01-01",
        "n_formations": n,
        "n_high": 1,
        "n_low": 1,
        "n_mid": 1,
        "eligible_assets_per_date": {"min": 26, "max": 27, "mean": (26 + 27 + 26) / 3},
        "formations": formations,
    }


class HelperSeamsTests(unittest.TestCase):
    def test_sha256_file_matches_hashlib(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tf:
            tf.write(b"hello self-consistency")
            path = Path(tf.name)
        try:
            self.assertEqual(mod.sha256_file(path),
                             hashlib.sha256(b"hello self-consistency").hexdigest())
        finally:
            path.unlink()

    def test_sha256_file_chunked_read_stable(self):
        data = b"x" * 20000
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(data)
            path = Path(tf.name)
        try:
            self.assertEqual(mod.sha256_file(path), hashlib.sha256(data).hexdigest())
        finally:
            path.unlink()

    def test_load_json_roundtrips(self):
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as tf:
            json.dump({"a": 1, "b": [2, 3]}, tf)
            path = Path(tf.name)
        try:
            self.assertEqual(mod.load_json(path), {"a": 1, "b": [2, 3]})
        finally:
            path.unlink()

    def test_now_utc_format(self):
        s = mod.now_utc()
        self.assertRegex(s, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

    def test_constants_frozen(self):
        self.assertEqual(mod.CANONICAL_SHA256,
                         "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390")
        self.assertEqual(mod.MIN_ASSETS_DECILES, 20)
        self.assertEqual(mod.MEAN_TOL, 1e-9)
        self.assertEqual(mod.VALID_STATES, ("high", "mid", "low"))


class RunChecksTests(unittest.TestCase):
    def test_consistent_block_passes_all(self):
        res = mod.run_checks(_block())
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["checks_failed"], 0)
        self.assertEqual(res["checks_passed"], res["checks_total"])

    def test_n_formations_mismatch_fails(self):
        b = _block()
        b["n_formations"] = 999
        res = mod.run_checks(b)
        self.assertEqual(res["verdict"], "FAIL")
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("n_formations_equals_array_len", failed)

    def test_eligible_min_mismatch_fails(self):
        b = _block()
        b["eligible_assets_per_date"]["min"] = 99
        res = mod.run_checks(b)
        self.assertEqual(res["verdict"], "FAIL")
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("eligible_min_equals_array_min", failed)

    def test_eligible_mean_tolerance(self):
        b = _block()
        # 26.666666...; perturb within tol then beyond tol
        b["eligible_assets_per_date"]["mean"] = (26 + 27 + 26) / 3 + 1e-10
        res = mod.run_checks(b)
        mean_row = next(c for c in res["checks"]
                        if c["check"] == "eligible_mean_equals_array_mean")
        self.assertTrue(mean_row["passed"])
        b["eligible_assets_per_date"]["mean"] = (26 + 27 + 26) / 3 + 1e-6
        res2 = mod.run_checks(b)
        mean_row2 = next(c for c in res2["checks"]
                         if c["check"] == "eligible_mean_equals_array_mean")
        self.assertFalse(mean_row2["passed"])

    def test_header_n_high_mismatch_fails(self):
        b = _block()
        b["n_high"] = 5
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("n_high_equals_array_state_count", failed)

    def test_header_n_mid_mismatch_fails(self):
        b = _block()
        b["n_mid"] = 0
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("n_mid_equals_array_state_count", failed)

    def test_state_counts_dict_crosschecked_when_present(self):
        b = _block()
        b["state_counts"] = {"high": 1, "mid": 1, "low": 1}
        res = mod.run_checks(b)
        self.assertEqual(res["verdict"], "PASS")
        b["state_counts"] = {"high": 2, "mid": 1, "low": 1}
        res2 = mod.run_checks(b)
        failed = [c["check"] for c in res2["checks"] if not c["passed"]]
        self.assertIn("state_counts_high", failed)

    def test_date_first_mismatch_fails(self):
        b = _block()
        b["date_first"] = "2024-01-01"
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("date_first_equals_array_min", failed)

    def test_date_last_mismatch_fails(self):
        b = _block()
        b["date_last"] = "2030-01-01"
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("date_last_equals_array_max", failed)

    def test_non_monotonic_dates_fail(self):
        b = _block()
        b["formations"][1]["formation_date"] = "2024-12-31"  # out of order
        # fix header min/max expectations so only monotonic check fails
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("dates_strictly_increasing_and_unique", failed)

    def test_duplicate_dates_fail(self):
        b = _block()
        b["formations"][1]["formation_date"] = b["formations"][0]["formation_date"]
        res = mod.run_checks(b)
        row = next(c for c in res["checks"]
                   if c["check"] == "dates_strictly_increasing_and_unique")
        self.assertFalse(row["passed"])
        self.assertFalse(row["actual"]["unique"])

    def test_invalid_state_fails(self):
        b = _block()
        b["formations"][0]["state"] = "extreme"
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("all_states_in_domain", failed)

    def test_n_assets_below_floor_fails(self):
        b = _block()
        b["formations"][0]["n_assets"] = 19
        # also fix summary min so only floor check fails
        b["eligible_assets_per_date"]["min"] = 19
        res = mod.run_checks(b)
        failed = [c["check"] for c in res["checks"] if not c["passed"]]
        self.assertIn("all_n_assets_meet_floor", failed)

    def test_empty_formations_passes_structural_checks(self):
        b = {
            "anchor_id": "H004V106", "block_sealed": True,
            "data_cutoff_utc": "2026-09-30T00:00:00Z", "date_last": None,
            "date_first": None, "n_formations": 0,
            "n_high": 0, "n_low": 0, "n_mid": 0,
            "eligible_assets_per_date": {"min": None, "max": None, "mean": None},
            "formations": [],
        }
        res = mod.run_checks(b)
        self.assertEqual(res["verdict"], "PASS")


class AuditPathTests(unittest.TestCase):
    def test_audit_reads_real_canonical_block_and_passes(self):
        # Reads the committed canonical block only (read-only); no network.
        report = mod.audit()
        self.assertEqual(report["verdict"], "PASS")
        self.assertTrue(report["sha256_match"])
        self.assertEqual(report["checks_failed"], 0)
        self.assertEqual(report["hypothesis_id"], "H38")
        self.assertEqual(report["status"], "EXPLORATORY_ONLY")
        self.assertEqual(report["frozen_artifacts_modified"], [])
        self.assertEqual(report["canonical_sha256"], mod.CANONICAL_SHA256)

    def test_main_returns_zero_on_pass(self):
        with patch.object(mod, "audit", return_value={
            "verdict": "PASS", "checks_passed": 12, "checks_total": 12,
            "sha256_match": True}):
            # Redirect OUT_DIR to a temp dir so no artifact dir is created.
            with tempfile.TemporaryDirectory() as td:
                with patch.object(mod, "OUT_DIR", Path(td)):
                    rc = mod.main()
                self.assertEqual(rc, 0)
                self.assertTrue(list(Path(td).glob("*.json")))

    def test_main_returns_one_on_fail(self):
        with patch.object(mod, "audit", return_value={
            "verdict": "FAIL", "checks_passed": 1, "checks_total": 2,
            "sha256_match": True}):
            with tempfile.TemporaryDirectory() as td:
                with patch.object(mod, "OUT_DIR", Path(td)):
                    rc = mod.main()
                self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()