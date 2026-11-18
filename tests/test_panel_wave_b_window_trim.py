"""Tests for the H50 wave-B (ARK/ASTR) window-trim decision (PANELCOV-WAVEB-TRIM-001).

Hermetic synthetic fixtures cover the pre-declared trim rule, the no-backfill
guarantee and both verdict branches, plus a skip-guarded integration check
against the committed artifact and its pinned H47/H48 inputs. No network is used
and nothing is written to the repository.

The study is EXPLORATORY_ONLY source-coverage planning: these tests verify the
trim adjudication, determinism and read-only behaviour -- not an economic claim.
"""
import json
import unittest
from pathlib import Path

import scripts.panel_wave_b_window_trim as trim_mod

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts" / trim_mod.EXP / "integrity_audit"


def _plan(asset, symbol, kind, month):
    return {"asset": asset, "symbol": symbol, "kind": kind, "month": month}


def _probe(symbol, kind, month, status=200):
    return {"symbol": symbol, "kind": kind, "month": month, "http_status": status}


def _roster(per_asset, included, ok=True):
    return {"join_check": {"ok": ok}, "included_assets": included, "per_asset": per_asset}


def _asset_record(symbol, first, last, absent=()):
    return {
        "symbol": symbol,
        "served_window": {
            kind: {"first": first, "last": last} for kind in ("klines", "funding")
        },
        "absent": [
            {"month": month, "kind": kind, "http_status": 404,
             "classification": "BEFORE_FIRST_SERVED"}
            for month in absent
            for kind in ("klines", "funding")
        ],
    }


def _fixture(ark_first="2023-03", astr_first="2023-02", months=("2023-01", "2023-02", "2023-03")):
    """Two wave-B assets; every month before ``first`` is a verified 404."""
    per_asset = {
        "ark": _asset_record("ARKUSDT", ark_first, months[-1], absent=[m for m in months if m < ark_first]),
        "astr": _asset_record("ASTRUSDT", astr_first, months[-1], absent=[m for m in months if m < astr_first]),
    }
    plans = [
        _plan(asset, symbol, kind, month)
        for asset, symbol in (("ark", "ARKUSDT"), ("astr", "ASTRUSDT"))
        for kind in ("klines", "funding")
        for month in months
    ]
    probes = []
    for asset, symbol in (("ark", "ARKUSDT"), ("astr", "ASTRUSDT")):
        first = per_asset[asset]["served_window"]["klines"]["first"]
        for kind in ("klines", "funding"):
            for month in months:
                probes.append(_probe(symbol, kind, month, 200 if month >= first else 404))
    queue = {
        "waves": {
            asset: {
                "symbol": symbol,
                "n_served_planned_files": 2 * sum(1 for m in months if m >= first),
            }
            for asset, symbol, first in (
                ("ark", "ARKUSDT", ark_first),
                ("astr", "ASTRUSDT", astr_first),
            )
        }
    }
    return per_asset, queue, plans, probes


class TrimRuleTests(unittest.TestCase):
    def _build(self, months=("2023-01", "2023-02", "2023-03"), **kwargs):
        per_asset, queue, plans, probes = _fixture(months=months, **kwargs)
        roster = _roster(per_asset, sorted(per_asset))
        return trim_mod.build_trim_decision(roster, queue, plans, probes, list(months))

    def test_drops_only_pre_listing_months_and_keeps_served_months(self):
        out = self._build()
        ark = out["per_asset"]["ark"]
        self.assertEqual(ark["admissible_study_months"], ["2023-03"])
        self.assertEqual(ark["dropped_required_months"], ["2023-01", "2023-02"])
        self.assertEqual(ark["n_trimmed_planned_files"], 2)
        self.assertEqual(ark["n_dropped_planned_files"], 4)
        self.assertEqual(ark["n_served_within_trimmed_window"], 2)
        self.assertEqual(ark["n_absent_within_trimmed_window"], 0)
        self.assertTrue(ark["all_dropped_before_first_served"])
        self.assertEqual(ark["dropped_class_counts"], {"BEFORE_FIRST_SERVED": 2})

    def test_admissible_window_is_intersection_of_both_kinds(self):
        per_asset, queue, plans, probes = _fixture(months=("2023-01", "2023-02", "2023-03"))
        # funding starts one month later than klines for ark.
        per_asset["ark"]["served_window"]["klines"]["first"] = "2023-02"
        per_asset["ark"]["served_window"]["funding"]["first"] = "2023-03"
        out = trim_mod.build_trim_decision(
            _roster(per_asset, sorted(per_asset)), queue, plans, probes,
            ["2023-01", "2023-02", "2023-03"],
        )
        self.assertEqual(out["per_asset"]["ark"]["admissible_study_months"], ["2023-03"])

    def test_trim_never_plans_files_outside_served_window(self):
        out = self._build()
        for asset, rec in out["per_asset"].items():
            self.assertEqual(
                rec["n_trimmed_planned_files"], 2 * len(rec["admissible_study_months"])
            )
            for month in rec["dropped_required_months"]:
                self.assertNotIn(month, rec["admissible_study_months"])
        trimmed = out["wave_b_trimmed"]
        self.assertEqual(trimmed["assets"], ["ark", "astr"])
        self.assertEqual(trimmed["planned_files"], 2 + 4)
        self.assertEqual(trimmed["absent_files"], 0)
        self.assertEqual(trimmed["dropped_files"], 4 + 2)
        self.assertTrue(trimmed["all_dropped_before_first_served"])

    def test_study_months_outside_plan_are_not_required(self):
        out = self._build(months=("2023-01", "2023-02", "2023-03"))
        self.assertEqual(out["per_asset"]["ark"]["n_required_months"], 3)
        self.assertEqual(out["n_study_months"], 3)

    def test_verdict_recorded_for_expected_scope(self):
        out = self._build()
        self.assertTrue(out["join_ok"])
        self.assertEqual(out["verdict"], trim_mod.TRIM_DECISION_RECORDED)

    def test_verdict_scope_mismatch_when_join_fails(self):
        per_asset, queue, plans, probes = _fixture()
        roster = _roster(per_asset, ["ark", "astr"], ok=False)
        out = trim_mod.build_trim_decision(
            roster, queue, plans, probes, ["2023-01", "2023-02", "2023-03"]
        )
        self.assertFalse(out["join_ok"])
        self.assertEqual(out["verdict"], trim_mod.TRIM_SCOPE_MISMATCH)

    def test_verdict_scope_mismatch_when_wave_b_asset_has_no_plan(self):
        per_asset, queue, plans, probes = _fixture()
        plans = [e for e in plans if e["asset"] != "astr"]
        out = trim_mod.build_trim_decision(
            _roster(per_asset, ["ark", "astr"]), queue, plans, probes,
            ["2023-01", "2023-02", "2023-03"],
        )
        self.assertFalse(out["join_ok"])
        self.assertEqual(out["verdict"], trim_mod.TRIM_SCOPE_MISMATCH)

    def test_unserved_asset_has_empty_window_and_nothing_planned(self):
        per_asset, queue, plans, probes = _fixture()
        per_asset["ark"]["served_window"] = {k: {} for k in ("klines", "funding")}
        out = trim_mod.build_trim_decision(
            _roster(per_asset, sorted(per_asset)), queue, plans, probes,
            ["2023-01", "2023-02", "2023-03"],
        )
        ark = out["per_asset"]["ark"]
        self.assertEqual(ark["admissible_study_months"], [])
        self.assertEqual(ark["n_trimmed_planned_files"], 0)
        self.assertEqual(ark["n_dropped_planned_files"], 6)
        self.assertEqual(out["verdict"], trim_mod.TRIM_DECISION_RECORDED)

    def test_trim_is_order_invariant(self):
        per_asset, queue, plans, probes = _fixture()
        roster = _roster(per_asset, sorted(per_asset))
        months = ["2023-01", "2023-02", "2023-03"]
        forward = trim_mod.build_trim_decision(roster, queue, plans, probes, months)
        backward = trim_mod.build_trim_decision(
            roster, queue, list(reversed(plans)), list(reversed(probes)),
            list(reversed(months)),
        )
        self.assertEqual(forward["per_asset"], backward["per_asset"])
        self.assertEqual(forward["trim_canonical_sha256"], backward["trim_canonical_sha256"])

    def test_build_trim_decision_does_not_touch_filesystem(self):
        per_asset, queue, plans, probes = _fixture()
        roster = _roster(per_asset, sorted(per_asset))
        before = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        trim_mod.build_trim_decision(
            roster, queue, plans, probes, ["2023-01", "2023-02", "2023-03"]
        )
        after = sorted(p.name for p in (ROOT / "artifacts").iterdir())
        self.assertEqual(before, after)


class TrimIntegrationTests(unittest.TestCase):
    def setUp(self):
        for path in (
            trim_mod.H47_ROSTER,
            trim_mod.H48_QUEUE,
            trim_mod.H43_PROBE,
            trim_mod.H41_PLAN,
            trim_mod.H40_FEAS,
        ):
            if not path.exists():
                self.skipTest(f"committed input missing: {path.name}")

    def test_committed_inputs_produce_trim_decision(self):
        audit = trim_mod.build_audit(None)
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertFalse(audit["confirmatory_claim_allowed"])
        self.assertFalse(audit["promotion_allowed"])
        self.assertTrue(audit["h47_roster_binding_ok"])
        self.assertTrue(audit["h48_queue_binding_ok"])
        self.assertTrue(audit["all_frozen_hashes_match"])
        self.assertEqual(audit["trim_verdict"], trim_mod.TRIM_DECISION_RECORDED)
        self.assertEqual(audit["n_study_months"], 46)
        self.assertEqual(audit["wave_b_trimmed"]["assets"], ["ark", "astr"])
        self.assertEqual(audit["wave_b_trimmed"]["planned_files"], 166)
        self.assertEqual(audit["wave_b_trimmed"]["servable_files"], 166)
        self.assertEqual(audit["wave_b_trimmed"]["absent_files"], 0)
        self.assertEqual(audit["wave_b_trimmed"]["dropped_files"], 18)
        self.assertTrue(audit["wave_b_trimmed"]["all_dropped_before_first_served"])
        ark, astr = audit["per_asset"]["ark"], audit["per_asset"]["astr"]
        self.assertEqual(ark["admissible_study_months"][0], "2023-09")
        self.assertEqual(ark["n_trimmed_planned_files"], 76)
        self.assertEqual(ark["n_dropped_planned_files"], 16)
        self.assertEqual(astr["admissible_study_months"][0], "2023-02")
        self.assertEqual(astr["n_trimmed_planned_files"], 90)
        self.assertEqual(astr["n_dropped_planned_files"], 2)
        self.assertEqual(len(audit["monthly_utility_trimmed"]), 46)
        self.assertEqual(audit["monthly_utility_trimmed"][0]["month"], "2023-01")
        self.assertEqual(audit["monthly_utility_trimmed"][0]["wave_b_admissible_assets"], [])
        self.assertEqual(audit["monthly_utility_trimmed"][1]["wave_b_admissible_assets"], ["astr"])
        self.assertEqual(
            audit["monthly_utility_trimmed"][8]["wave_b_admissible_assets"], ["ark", "astr"]
        )
        self.assertEqual(audit["monthly_utility_trimmed"][-1]["n_wave_b_admissible"], 2)
        self.assertRegex(audit["trim_canonical_sha256"], r"^[0-9a-f]{64}$")

    def test_audit_is_stable_across_builds(self):
        first = trim_mod.build_audit(None)
        second = trim_mod.build_audit(None)
        self.assertEqual(first["trim_canonical_sha256"], second["trim_canonical_sha256"])
        self.assertEqual(
            json.dumps(first["per_asset"], sort_keys=True),
            json.dumps(second["per_asset"], sort_keys=True),
        )

    def test_committed_artifact_matches_recomputation(self):
        if not ARTIFACT_DIR.exists():
            self.skipTest("committed wave-B trim artifact missing")
        candidates = sorted(ARTIFACT_DIR.glob("panel_wave_b_window_trim_*.json"))
        if not candidates:
            self.skipTest("committed wave-B trim artifact missing")
        committed = json.loads(candidates[-1].read_text())
        rebuilt = trim_mod.build_audit(None)
        self.assertEqual(committed["trim_verdict"], rebuilt["trim_verdict"])
        self.assertEqual(
            committed["trim_canonical_sha256"], rebuilt["trim_canonical_sha256"]
        )
        self.assertEqual(
            json.dumps(committed["per_asset"], sort_keys=True),
            json.dumps(rebuilt["per_asset"], sort_keys=True),
        )


if __name__ == "__main__":
    unittest.main()
