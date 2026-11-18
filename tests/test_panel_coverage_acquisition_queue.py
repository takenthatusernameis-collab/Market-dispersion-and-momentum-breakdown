"""Tests for the H48 panel-coverage acquisition queue (PANELCOV-QUEUE-001).

Hermetic synthetic fixtures cover every pre-declared wave/verdict branch, plus a
skip-guarded integration check against the committed H47/H41/H43/H40 artifacts.
No network, no market data, no writes to the repository.

The queue is EXPLORATORY_ONLY source-coverage bookkeeping: these tests verify the
adjudication rule, determinism and read-only behaviour -- not an economic claim.
"""
import json
import unittest
from pathlib import Path

import scripts.panel_coverage_acquisition_queue as queue_mod

ROOT = Path(__file__).resolve().parents[1]


def _plan(asset, symbol, kind, month):
    return {"asset": asset, "symbol": symbol, "kind": kind, "month": month}


def _probe(symbol, kind, month, status=200):
    return {
        "asset": symbol[:-4].lower(),
        "symbol": symbol,
        "kind": kind,
        "month": month,
        "http_status": status,
    }


def _roster(included, excluded, per_asset=None, ok=True):
    return {
        "join_check": {"ok": ok},
        "included_assets": included,
        "excluded_assets": excluded,
        "per_asset": per_asset or {},
    }


class QueueRuleTests(unittest.TestCase):
    def test_fully_served_asset_is_wave_a(self):
        plans = [
            _plan("aaa", "AAAUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        probes = [
            _probe("AAAUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        roster = _roster(["aaa"], [], {"aaa": {"symbol": "AAAUSDT"}})
        q = queue_mod.build_queue(plans, probes, roster, ["2023-01", "2023-02"])
        self.assertEqual(q["verdict"], queue_mod.QUEUE_READY)
        self.assertEqual(q["waves"]["aaa"]["wave"], queue_mod.WAVE_A)
        self.assertEqual(q["waves"]["aaa"]["n_planned_files"], 4)
        self.assertEqual(q["waves"]["aaa"]["n_served_planned_files"], 4)
        self.assertEqual(q["wave_file_counts"]["wave_a"]["planned_files"], 4)

    def test_missing_kind_month_is_wave_b_with_listed_month(self):
        plans = [
            _plan("ark", "ARKUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        # klines 2023-01 absent, everything else served.
        probes = [
            _probe("ARKUSDT", "klines", "2023-01", 404),
            _probe("ARKUSDT", "klines", "2023-02"),
            _probe("ARKUSDT", "funding", "2023-01"),
            _probe("ARKUSDT", "funding", "2023-02"),
        ]
        roster = _roster(["ark"], [], {"ark": {"symbol": "ARKUSDT"}})
        q = queue_mod.build_queue(plans, probes, roster, ["2023-01", "2023-02"])
        rec = q["waves"]["ark"]
        self.assertEqual(rec["wave"], queue_mod.WAVE_B)
        self.assertEqual(rec["absent_required_months"], ["2023-01"])
        self.assertEqual(rec["n_absent_planned_files"], 1)
        self.assertEqual(q["wave_file_counts"]["wave_b"]["planned_files"], 4)
        self.assertEqual(q["wave_file_counts"]["wave_a"]["n_assets"], 0)
        self.assertEqual(q["verdict"], queue_mod.QUEUE_NO_UNCONDITIONAL_WAVE)

    def test_months_outside_study_window_are_ignored(self):
        plans = [
            _plan("aaa", "AAAUSDT", kind, "2022-12")
            for kind in ("klines", "funding")
        ] + [
            _plan("aaa", "AAAUSDT", kind, "2023-01")
            for kind in ("klines", "funding")
        ]
        probes = [
            _probe("AAAUSDT", "klines", "2022-12", 404),
            _probe("AAAUSDT", "funding", "2022-12", 404),
            _probe("AAAUSDT", "klines", "2023-01"),
            _probe("AAAUSDT", "funding", "2023-01"),
        ]
        roster = _roster(["aaa"], [], {"aaa": {"symbol": "AAAUSDT"}})
        q = queue_mod.build_queue(plans, probes, roster, ["2023-01"])
        self.assertEqual(q["waves"]["aaa"]["wave"], queue_mod.WAVE_A)
        self.assertEqual(q["waves"]["aaa"]["n_required_months"], 1)
        self.assertEqual(q["waves"]["aaa"]["n_planned_files"], 2)

    def test_excluded_asset_files_are_reconciled_not_downloadable(self):
        plans = [
            _plan("alpha", "ALPHAUSDT", kind, "2023-01")
            for kind in ("klines", "funding")
        ] + [
            _plan("aaa", "AAAUSDT", kind, "2023-01")
            for kind in ("klines", "funding")
        ]
        probes = [
            _probe("ALPHAUSDT", "klines", "2023-01", 404),
            _probe("ALPHAUSDT", "funding", "2023-01", 404),
            _probe("AAAUSDT", "klines", "2023-01"),
            _probe("AAAUSDT", "funding", "2023-01"),
        ]
        roster = _roster(
            ["aaa"], ["alpha"], {"aaa": {"symbol": "AAAUSDT"}, "alpha": {"symbol": "ALPHAUSDT"}}
        )
        q = queue_mod.build_queue(plans, probes, roster, ["2023-01"])
        self.assertEqual(q["wave_file_counts"]["excluded"]["planned_files"], 2)
        self.assertEqual(q["total_planned_files_reconciled"], 4)
        self.assertEqual(
            q["wave_file_counts"]["wave_a"]["planned_files"]
            + q["wave_file_counts"]["wave_b"]["planned_files"]
            + q["wave_file_counts"]["excluded"]["planned_files"],
            q["total_planned_files_reconciled"],
        )

    def test_monthly_utility_splits_wave_a_and_wave_b_increment(self):
        plans = [
            _plan(a, s, kind, month)
            for a, s in (("aaa", "AAAUSDT"), ("ark", "ARKUSDT"))
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        probes = [
            _probe("AAAUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ] + [
            _probe("ARKUSDT", kind, month, 404 if month == "2023-01" else 200)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        roster = _roster(
            ["aaa", "ark"],
            [],
            {"aaa": {"symbol": "AAAUSDT"}, "ark": {"symbol": "ARKUSDT"}},
        )
        q = queue_mod.build_queue(plans, probes, roster, ["2023-01", "2023-02"])
        self.assertEqual(q["monthly_utility"][0]["n_wave_a"], 1)
        self.assertEqual(q["monthly_utility"][0]["n_all_included"], 1)
        self.assertEqual(q["monthly_utility"][1]["n_wave_a"], 1)
        self.assertEqual(q["monthly_utility"][1]["n_all_included"], 2)
        self.assertEqual(q["monthly_utility"][1]["wave_b_assets"], ["ark"])
        self.assertEqual(q["served_asset_months"], 3)
        self.assertEqual(q["total_possible_asset_months"], 4)

    def test_unregistered_included_asset_is_join_mismatch(self):
        roster = _roster(["ghost"], [], {"ghost": {"symbol": "GHOSTUSDT"}})
        q = queue_mod.build_queue([], [], roster, ["2023-01"])
        self.assertFalse(q["join_ok"])
        self.assertEqual(q["verdict"], queue_mod.QUEUE_JOIN_MISMATCH)

    def test_queue_is_order_invariant(self):
        plans = [
            _plan("aaa", "AAAUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        probes = [
            _probe("AAAUSDT", kind, month)
            for kind in ("klines", "funding")
            for month in ("2023-01", "2023-02")
        ]
        roster = _roster(["aaa"], [], {"aaa": {"symbol": "AAAUSDT"}})
        forward = queue_mod.build_queue(plans, probes, roster, ["2023-01", "2023-02"])
        backward = queue_mod.build_queue(
            list(reversed(plans)), list(reversed(probes)), roster, ["2023-02", "2023-01"]
        )
        self.assertEqual(
            forward["queue_canonical_sha256"], backward["queue_canonical_sha256"]
        )
        self.assertEqual(forward["waves"], backward["waves"])

    def test_build_queue_does_not_touch_filesystem(self):
        plans = [_plan("aaa", "AAAUSDT", "klines", "2023-01")]
        probes = [_probe("AAAUSDT", "klines", "2023-01")]
        roster = _roster(["aaa"], [], {"aaa": {"symbol": "AAAUSDT"}})
        before = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        queue_mod.build_queue(plans, probes, roster, ["2023-01"])
        after = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        self.assertEqual(before, after)


class QueueIntegrationTests(unittest.TestCase):
    def setUp(self):
        for path in (
            queue_mod.H47_ROSTER,
            queue_mod.H41_PLAN,
            queue_mod.H43_PROBE,
            queue_mod.H40_FEAS,
        ):
            if not path.exists():
                self.skipTest(f"committed input missing: {path.name}")

    def test_committed_inputs_produce_expected_queue(self):
        audit = queue_mod.build_audit(None)
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertFalse(audit["confirmatory_claim_allowed"])
        self.assertTrue(audit["h47_roster_binding_ok"])
        self.assertTrue(audit["all_frozen_hashes_match"])
        self.assertEqual(audit["verdict"], queue_mod.QUEUE_READY)
        self.assertEqual(audit["n_study_months"], 46)
        self.assertEqual(audit["n_included_assets"], 9)
        self.assertEqual(audit["n_excluded_assets"], 1)
        self.assertEqual(
            audit["wave_file_counts"]["wave_a"]["assets"],
            ["alice", "ankr", "ape", "api3", "apt", "ar", "arpa"],
        )
        self.assertEqual(audit["wave_file_counts"]["wave_a"]["planned_files"], 644)
        self.assertEqual(audit["wave_file_counts"]["wave_b"]["assets"], ["ark", "astr"])
        self.assertEqual(audit["wave_file_counts"]["wave_b"]["planned_files"], 184)
        self.assertEqual(audit["wave_file_counts"]["wave_b"]["absent_files"], 18)
        self.assertEqual(audit["wave_file_counts"]["excluded"]["planned_files"], 92)
        self.assertEqual(audit["total_planned_files_reconciled"], 920)
        self.assertEqual(audit["total_possible_asset_months"], 414)
        self.assertEqual(audit["served_asset_months"], 405)
        self.assertEqual(len(audit["monthly_utility"]), 46)
        self.assertEqual(audit["monthly_utility"][0]["month"], "2023-01")
        self.assertEqual(audit["monthly_utility"][0]["n_wave_a"], 7)
        self.assertEqual(audit["monthly_utility"][-1]["month"], "2026-10")
        self.assertRegex(audit["queue_canonical_sha256"], r"^[0-9a-f]{64}$")

    def test_audit_is_byte_stable_across_builds(self):
        first = queue_mod.build_audit(None)
        second = queue_mod.build_audit(None)
        self.assertEqual(
            first["queue_canonical_sha256"], second["queue_canonical_sha256"]
        )
        self.assertEqual(
            json.dumps(first["monthly_utility"], sort_keys=True),
            json.dumps(second["monthly_utility"], sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
