"""Tests for the H57 point-in-time cap eligibility audit.

Hermetic synthetic fixtures cover every pure helper: symbol/asset mapping, month
conventions, the snapshot-signature rule, the percentile distribution, date
shifting, and the predeclared decision rule across every verdict branch. A
skip-guarded integration block binds the committed audit artifact to the
committed inputs and verifies the four frozen hashes are byte-identical.

Synthetic rows are software fixtures, never market evidence. No network is used
and no audit is written by the tests.

The study is EXPLORATORY_ONLY source-coverage measurement: these tests verify
measurement and reporting behaviour -- not an economic claim. The audit computes
no return, spread, dispersion state, cost, p-value or inference.
"""
import hashlib
import json
import unittest
from pathlib import Path

import scripts.pointintime_eligibility_audit as audit

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "artifacts" / audit.EXP_DIR if hasattr(audit, "EXP_DIR") else ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"


class SymbolToAssetTests(unittest.TestCase):
    def test_usdt_quote_is_stripped_and_lowercased(self):
        self.assertEqual(audit.symbol_to_asset("BTCUSDT"), "btc")
        self.assertEqual(audit.symbol_to_asset("1INCHUSDT"), "1inch")
        self.assertEqual(audit.symbol_to_asset("ETHUSDT"), "eth")

    def test_non_usdt_symbol_is_lowercased_only(self):
        self.assertEqual(audit.symbol_to_asset("BTC"), "btc")
        self.assertEqual(audit.symbol_to_asset("btc"), "btc")

    def test_whitespace_is_stripped(self):
        self.assertEqual(audit.symbol_to_asset("  BTCUSDT  "), "btc")


class MonthConventionTests(unittest.TestCase):
    def test_month_key_is_zero_padded(self):
        self.assertEqual(audit.month_key(2025, 1), "2025-01")
        self.assertEqual(audit.month_key(2026, 10), "2026-10")

    def test_month_end_date_is_last_calendar_day(self):
        self.assertEqual(audit.month_end_date(2025, 1), "2025-01-31")
        self.assertEqual(audit.month_end_date(2024, 2), "2024-02-29")
        self.assertEqual(audit.month_end_date(2025, 2), "2025-02-28")
        self.assertEqual(audit.month_end_date(2026, 10), "2026-10-31")

    def test_fresh_window_is_22_months_inclusive(self):
        months = audit.fresh_window_months()
        self.assertEqual(len(months), 22)
        self.assertEqual(months[0], (2025, 1))
        self.assertEqual(months[-1], (2026, 10))

    def test_fresh_window_crosses_year_boundary(self):
        months = audit.fresh_window_months()
        self.assertIn((2025, 12), months)
        self.assertIn((2026, 1), months)

    def test_shift_date_crosses_month_boundary(self):
        self.assertEqual(audit._shift_date("2025-01-01", -1), "2024-12-31")
        self.assertEqual(audit._shift_date("2025-03-01", -1), "2025-02-28")
        self.assertEqual(audit._shift_date("2025-01-01", 7), "2025-01-08")


class SnapshotSignatureTests(unittest.TestCase):
    def test_single_date_is_snapshot_like(self):
        snap, reason = audit.snapshot_signature({"2025-01-01": 1.0})
        self.assertTrue(snap)
        self.assertIn("fewer_than_2_distinct_dates", reason)

    def test_single_value_is_snapshot_like(self):
        snap, reason = audit.snapshot_signature(
            {"2025-01-01": 1.0, "2025-01-02": 1.0}
        )
        self.assertTrue(snap)
        self.assertIn("fewer_than_2_distinct_values", reason)

    def test_genuine_series_is_not_snapshot_like(self):
        snap, reason = audit.snapshot_signature(
            {"2025-01-01": 1.0, "2025-01-02": 2.0}
        )
        self.assertFalse(snap)
        self.assertEqual(reason, "ok")

    def test_empty_series_is_snapshot_like(self):
        snap, _reason = audit.snapshot_signature({})
        self.assertTrue(snap)


class PercentileTests(unittest.TestCase):
    def test_empty_is_nan(self):
        import math

        self.assertTrue(math.isnan(audit._percentile([], 50)))

    def test_single_value_returns_itself(self):
        self.assertEqual(audit._percentile([5.0], 50), 5.0)

    def test_median_of_odd_count(self):
        self.assertEqual(audit._percentile([1.0, 2.0, 3.0], 50), 2.0)

    def test_median_of_even_count_interpolates(self):
        self.assertEqual(audit._percentile([1.0, 2.0, 3.0, 4.0], 50), 2.5)

    def test_distribution_reports_min_p50_mean_max(self):
        dist = audit._distribution([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(dist["min"], 1.0)
        self.assertEqual(dist["max"], 4.0)
        self.assertEqual(dist["p50"], 2.5)
        self.assertEqual(dist["mean"], 2.5)
        self.assertEqual(dist["n"], 4)

    def test_distribution_empty_is_none(self):
        dist = audit._distribution([])
        self.assertIsNone(dist["min"])
        self.assertEqual(dist["n"], 0)


class DecideLabelTests(unittest.TestCase):
    def _asset(self, symbol, cap_source="legacy_marketcap_panel", snap=False):
        return {
            "symbol": symbol,
            "asset": audit.symbol_to_asset(symbol),
            "cap_source": cap_source,
            "snapshot_signature": snap,
            "n_fresh_months_covered": 22,
        }

    def _month(self, mk, strict, asof):
        return {"month": mk, "n_strict": strict, "n_asof": asof}

    def test_eligible_when_all_conditions_pass(self):
        per_asset = [self._asset("BTCUSDT"), self._asset("ETHUSDT")]
        monthly = [self._month("2025-01", 20, 20), self._month("2025-02", 22, 22)]
        label, decision = audit.decide_label(per_asset, monthly)
        self.assertEqual(label, audit.LABEL_ELIGIBLE)
        self.assertTrue(decision["condition_all_assets_resolve_to_cap"]["pass"])
        self.assertTrue(decision["condition_no_snapshot_signature"]["pass"])
        self.assertTrue(decision["condition_min_strict_breadth_ge_min"]["pass"])
        self.assertTrue(decision["condition_min_asof_breadth_ge_min"]["pass"])

    def test_limited_when_an_asset_has_no_cap_source(self):
        per_asset = [
            self._asset("BTCUSDT"),
            self._asset("XYZUSDT", cap_source=None),
        ]
        monthly = [self._month("2025-01", 20, 20)]
        label, decision = audit.decide_label(per_asset, monthly)
        self.assertEqual(label, audit.LABEL_LIMITED)
        self.assertFalse(decision["condition_all_assets_resolve_to_cap"]["pass"])
        self.assertIn("XYZUSDT", decision["condition_all_assets_resolve_to_cap"]["unresolved"])

    def test_limited_when_snapshot_signature_present(self):
        per_asset = [self._asset("BTCUSDT"), self._asset("ETHUSDT", snap=True)]
        monthly = [self._month("2025-01", 20, 20)]
        label, decision = audit.decide_label(per_asset, monthly)
        self.assertEqual(label, audit.LABEL_LIMITED)
        self.assertFalse(decision["condition_no_snapshot_signature"]["pass"])
        self.assertIn("ETHUSDT", decision["condition_no_snapshot_signature"]["snapshot_like"])

    def test_limited_when_strict_breadth_below_min(self):
        per_asset = [self._asset("BTCUSDT")]
        monthly = [self._month("2025-01", 19, 20)]
        label, decision = audit.decide_label(per_asset, monthly)
        self.assertEqual(label, audit.LABEL_LIMITED)
        self.assertFalse(decision["condition_min_strict_breadth_ge_min"]["pass"])
        self.assertTrue(decision["condition_min_asof_breadth_ge_min"]["pass"])

    def test_limited_when_asof_breadth_below_min(self):
        per_asset = [self._asset("BTCUSDT")]
        monthly = [self._month("2025-01", 20, 19)]
        label, decision = audit.decide_label(per_asset, monthly)
        self.assertEqual(label, audit.LABEL_LIMITED)
        self.assertFalse(decision["condition_min_asof_breadth_ge_min"]["pass"])

    def test_min_breadth_constant_is_20(self):
        self.assertEqual(audit.MIN_BREADTH, 20)
        self.assertEqual(audit.ASOF_STALENESS_DAYS, 7)


class FrozenHashTests(unittest.TestCase):
    def test_frozen_expected_pins_canonical_block_sha256(self):
        path, expected = audit.FROZEN_EXPECTED["canonical_forward_block"]
        self.assertEqual(
            expected,
            "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
        )

    def test_frozen_expected_pins_h10_fresh_block_sha256(self):
        path, expected = audit.FROZEN_EXPECTED["h10_fresh_block"]
        self.assertEqual(
            expected,
            "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
        )


class CommittedAuditIntegrationTests(unittest.TestCase):
    """Skip-guarded: bind the committed H57 audit to the committed inputs.

    These run only when the audit artifact is present on disk. They verify the
    audit is EXPLORATORY_ONLY, does not allow confirmatory claims, resolves all
    symbols, carries no snapshot-like series, and that every frozen hash still
    matches. Synthetic fixtures are never used here.
    """

    def setUp(self):
        artifacts = sorted(AUDIT_DIR.glob("H004V106_pointintime_eligibility_*.json"))
        if not artifacts:
            self.skipTest("no committed H57 audit artifact on disk")
        self.audit = json.loads(artifacts[-1].read_text(encoding="utf-8"))

    def test_status_is_exploratory_only(self):
        self.assertEqual(self.audit["status"], "EXPLORATORY_ONLY")
        self.assertTrue(self.audit["exploratory_only"])
        self.assertFalse(self.audit["confirmatory_claim_allowed"])
        self.assertFalse(self.audit["promotion_allowed"])

    def test_all_symbols_resolve_and_no_snapshot_signature(self):
        self.assertEqual(self.audit["inventory"]["assets_without_cap"], [])
        self.assertEqual(self.audit["inventory"]["snapshot_like_assets"], [])

    def test_frozen_hashes_all_match(self):
        self.assertTrue(self.audit["all_frozen_hashes_match"])
        for name, info in self.audit["frozen_hashes_verified"].items():
            self.assertTrue(info["match"], f"{name} hash mismatch")
            actual = hashlib.sha256(
                (ROOT / info["path"]).read_bytes()
            ).hexdigest()
            self.assertEqual(actual, info["expected"])

    def test_rank_provenance_is_not_proven_complete(self):
        self.assertEqual(self.audit["rank_provenance"]["label"], "NOT_PROVEN_COMPLETE")
        self.assertIsNone(self.audit["rank_provenance"]["last_verified_historical_rank"])

    def test_min_breadth_meets_requirement_in_every_month(self):
        self.assertGreaterEqual(
            self.audit["summary"]["strict_breadth_stats"]["min"], audit.MIN_BREADTH
        )
        self.assertGreaterEqual(
            self.audit["summary"]["asof_breadth_stats"]["min"], audit.MIN_BREADTH
        )
        self.assertEqual(
            self.audit["summary"]["n_months_strict_ge_min"],
            self.audit["summary"]["n_months"],
        )


if __name__ == "__main__":
    unittest.main()