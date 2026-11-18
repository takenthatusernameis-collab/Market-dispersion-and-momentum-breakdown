"""Tests for the H47 panel-coverage eligibility roster (PANELCOV-NARROW-001).

Hermetic synthetic fixtures cover every pre-declared decision branch, plus a
skip-guarded integration check against the committed H41/H43/H40 artifacts.
No network, no market data, no writes to the repository.

The roster is EXPLORATORY_ONLY source-coverage bookkeeping: these tests verify
the adjudication rule, determinism and read-only behaviour -- not an economic
claim.
"""
import json
import unittest
from pathlib import Path

import scripts.panel_coverage_eligibility_roster as roster_mod

ROOT = Path(__file__).resolve().parents[1]


def _entry(asset, symbol, kind, month, status=200, error=None):
    plan = {"asset": asset, "symbol": symbol, "kind": kind, "month": month}
    probe = {
        "asset": asset,
        "symbol": symbol,
        "kind": kind,
        "month": month,
        "http_status": status,
        "error": error,
    }
    return plan, probe


def _fixture(spec):
    """spec: list of (symbol, kind, month, status, error); asset = symbol lower."""
    plans, probes = [], []
    for symbol, kind, month, status, error in spec:
        plan, probe = _entry(symbol.lower(), symbol, kind, month, status, error)
        plans.append(plan)
        probes.append(probe)
    return plans, probes


class RosterRuleTests(unittest.TestCase):
    def test_fully_served_asset_is_included(self):
        plans, probes = _fixture(
            [
                ("AAAUSDT", "klines", "2023-01", 200, None),
                ("AAAUSDT", "klines", "2023-02", 200, None),
                ("AAAUSDT", "funding", "2023-01", 200, None),
                ("AAAUSDT", "funding", "2023-02", 200, None),
            ]
        )
        r = roster_mod.build_roster(plans, probes)
        self.assertEqual(r["verdict"], roster_mod.VERDICT_ALL_SERVED)
        self.assertEqual(r["included_assets"], ["aaausdt"])
        self.assertEqual(r["excluded_assets"], [])
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.INCLUDED_FULLY_SERVED)
        self.assertEqual(rec["served_window"]["klines"], {"first": "2023-01", "last": "2023-02"})
        self.assertEqual(rec["n_absent"], 0)

    def test_preslisting_gaps_only_include_with_verified_window(self):
        spec = [("ARKUSDT", "klines", m, 200, None) for m in ("2023-09", "2023-10")]
        spec += [("ARKUSDT", "funding", m, 200, None) for m in ("2023-09", "2023-10")]
        # Planned months 2023-01..2023-10 (8 pre-listing absences, 2 served).
        spec += [("ARKUSDT", kind, f"2023-0{i}", 404, None) for kind in ("klines", "funding") for i in range(1, 9)]
        plans, probes = _fixture(spec)
        feas = {"arkusdt": {"required_study_months": [f"2023-0{i}" for i in range(1, 10)]}}
        r = roster_mod.build_roster(plans, probes, feas)
        rec = r["per_asset"]["arkusdt"]
        self.assertEqual(rec["decision"], roster_mod.INCLUDED_PRELISTING_GAPS_ONLY)
        self.assertTrue(rec["included"])
        self.assertEqual(rec["absent_class_counts"], {"BEFORE_FIRST_SERVED": 16})
        self.assertEqual(rec["served_window"]["klines"], {"first": "2023-09", "last": "2023-10"})
        # 2023-01..2023-08 fall outside the verified window.
        self.assertEqual(rec["n_required_months_outside_verified_window"], 8)
        self.assertEqual(r["verdict"], roster_mod.VERDICT_ALL_SERVED)

    def test_trailing_gap_excludes_asset(self):
        spec = [("AAAUSDT", "klines", m, 200, None) for m in ("2023-01", "2023-02", "2023-03")]
        spec += [("AAAUSDT", "funding", m, 200, None) for m in ("2023-01", "2023-02")]
        spec += [("AAAUSDT", "funding", "2023-03", 404, None)]
        plans, probes = _fixture(spec)
        r = roster_mod.build_roster(plans, probes)
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.EXCLUDED_UNSERVED_TIMELINE)
        self.assertEqual(rec["absent_class_counts"], {"AFTER_LAST_SERVED": 1})
        self.assertEqual(r["excluded_assets"], ["aaausdt"])
        self.assertEqual(r["verdict"], roster_mod.VERDICT_HAS_UNSERVED)

    def test_interior_gap_excludes_asset(self):
        spec = [("AAAUSDT", "klines", m, 200, None) for m in ("2023-01", "2023-03")]
        spec += [("AAAUSDT", "klines", "2023-02", 404, None)]
        plans, probes = _fixture(spec)
        r = roster_mod.build_roster(plans, probes)
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.EXCLUDED_UNSERVED_TIMELINE)
        self.assertEqual(rec["absent_class_counts"], {"INTERIOR": 1})

    def test_entirely_absent_group_excludes_asset(self):
        spec = [("AAAUSDT", "klines", "2023-01", 404, None)]
        plans, probes = _fixture(spec)
        r = roster_mod.build_roster(plans, probes)
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.EXCLUDED_UNSERVED_TIMELINE)
        self.assertEqual(rec["absent_class_counts"], {"ENTIRELY_ABSENT": 1})
        self.assertEqual(rec["served_window"]["klines"], {"first": None, "last": None})

    def test_probe_error_excludes_asset(self):
        spec = [("AAAUSDT", "klines", "2023-01", 200, None)]
        spec += [("AAAUSDT", "klines", "2023-02", None, "timeout")]
        plans, probes = _fixture(spec)
        r = roster_mod.build_roster(plans, probes)
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.EXCLUDED_PROBE_ERROR)
        self.assertEqual(rec["absent_class_counts"], {"ERROR": 1})

    def test_unprobed_plan_entry_is_join_mismatch(self):
        plans, probes = _fixture(
            [
                ("AAAUSDT", "klines", "2023-01", 200, None),
                ("AAAUSDT", "klines", "2023-02", 200, None),
            ]
        )
        probes = probes[:1]  # plan key 2023-02 never probed
        r = roster_mod.build_roster(plans, probes)
        rec = r["per_asset"]["aaausdt"]
        self.assertEqual(rec["decision"], roster_mod.EXCLUDED_UNPROBED)
        self.assertEqual(rec["absent_class_counts"], {"UNPROBED": 1})
        self.assertEqual(r["verdict"], roster_mod.VERDICT_JOIN_MISMATCH)
        self.assertFalse(r["join_check"]["ok"])
        self.assertEqual(r["join_check"]["n_plan_only"], 1)

    def test_roster_is_order_invariant(self):
        spec = [
            ("AAAUSDT", "klines", "2023-01", 200, None),
            ("AAAUSDT", "klines", "2023-02", 404, None),
            ("BBBUSDT", "funding", "2023-01", 200, None),
            ("BBBUSDT", "funding", "2023-02", 200, None),
        ]
        plans, probes = _fixture(spec)
        forward = roster_mod.build_roster(plans, probes)
        backward = roster_mod.build_roster(list(reversed(plans)), list(reversed(probes)))
        self.assertEqual(
            forward["roster_canonical_sha256"], backward["roster_canonical_sha256"]
        )
        self.assertEqual(forward["verdict"], backward["verdict"])
        self.assertEqual(forward["per_asset"], backward["per_asset"])

    def test_build_roster_does_not_touch_filesystem(self):
        plans, probes = _fixture([("AAAUSDT", "klines", "2023-01", 200, None)])
        before = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        roster_mod.build_roster(plans, probes)
        after = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        self.assertEqual(before, after)


class RosterIntegrationTests(unittest.TestCase):
    def setUp(self):
        for path in (
            roster_mod.H41_PLAN,
            roster_mod.H43_PROBE,
            roster_mod.H40_FEAS,
        ):
            if not path.exists():
                self.skipTest(f"committed input missing: {path.name}")

    def test_committed_inputs_produce_expected_roster(self):
        audit = roster_mod.build_audit(None)
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertFalse(audit["confirmatory_claim_allowed"])
        self.assertTrue(audit["join_check"]["ok"])
        self.assertEqual(audit["n_assets_planned"], 10)
        self.assertEqual(audit["verdict"], roster_mod.VERDICT_HAS_UNSERVED)
        self.assertEqual(audit["excluded_assets"], ["alpha"])
        self.assertEqual(audit["n_excluded"], 1)
        self.assertEqual(audit["n_included"], 9)

        per = audit["per_asset"]
        self.assertEqual(per["alpha"]["decision"], roster_mod.EXCLUDED_UNSERVED_TIMELINE)
        self.assertEqual(per["alpha"]["absent_class_counts"], {"AFTER_LAST_SERVED": 13})
        for asset in ("ark", "astr"):
            self.assertEqual(
                per[asset]["decision"], roster_mod.INCLUDED_PRELISTING_GAPS_ONLY
            )
            self.assertTrue(per[asset]["included"])
            self.assertEqual(
                set(per[asset]["absent_class_counts"]), {"BEFORE_FIRST_SERVED"}
            )
        for asset in ("alice", "ankr", "ape", "api3", "apt", "ar", "arpa"):
            self.assertEqual(per[asset]["decision"], roster_mod.INCLUDED_FULLY_SERVED)

        # Verified windows are recorded for every included asset-kind.
        for asset in audit["included_assets"]:
            for kind in per[asset]["kinds"]:
                window = per[asset]["served_window"][kind]
                self.assertIsNotNone(window["first"])
                self.assertIsNotNone(window["last"])

        self.assertRegex(audit["roster_canonical_sha256"], r"^[0-9a-f]{64}$")

    def test_audit_is_byte_stable_across_builds(self):
        first = roster_mod.build_audit(None)
        second = roster_mod.build_audit(None)
        self.assertEqual(
            first["roster_canonical_sha256"], second["roster_canonical_sha256"]
        )
        self.assertEqual(
            json.dumps(first["per_asset"], sort_keys=True),
            json.dumps(second["per_asset"], sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
