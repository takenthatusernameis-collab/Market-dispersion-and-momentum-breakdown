"""Regression tests for scripts/panel_archive_probe.py (H43).

DISP-003-PANELACQ-PROBE-001, EXPLORATORY_ONLY. Pins:
  * module import-safe (pure helpers, no network at import);
  * deterministic target projection from the committed H41 plan;
  * summarize() and decide_label() behavior on synthetic results;
  * the committed artifact's identity, status, controls, frozen hashes,
    summary/per-entry internal consistency, and that its targets equal the
    committed H41 plan (offline-deterministic projection).

The committed artifact's per-entry HTTP statuses are a point-in-time live
measurement and are NOT rebuilt here (that would require network); the test
validates structure and the offline-deterministic parts instead. No network,
no secrets, no trading endpoints.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "panel_archive_probe.py"
AUDIT_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
    / "integrity_audit"
)
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)

spec = importlib.util.spec_from_file_location("panel_archive_probe", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _committed_artifact():
    files = sorted(AUDIT_DIR.glob("H004V106_panel_archive_probe_*.json"))
    assert files, "no committed panel-archive probe artifact found"
    return files[-1], json.loads(files[-1].read_text(encoding="utf-8"))


class PureHelperTests(unittest.TestCase):
    def test_build_targets_matches_committed_plan(self):
        plan = json.loads(H41_PLAN.read_text(encoding="utf-8"))
        targets = mod.build_targets(plan)
        self.assertEqual(len(targets), len(plan["plan_entries"]))
        keys = mod.target_keys(targets)
        self.assertEqual(len(keys), len(set(keys)), "targets are not unique")
        # The projection must preserve (symbol, kind, month) exactly.
        expected = [
            (e["symbol"], e["kind"], e["month"]) for e in plan["plan_entries"]
        ]
        self.assertEqual(keys, expected)

    def test_build_targets_deterministic(self):
        plan = json.loads(H41_PLAN.read_text(encoding="utf-8"))
        self.assertEqual(mod.build_targets(plan), mod.build_targets(plan))

    def test_summarize_counts(self):
        results = [
            {"kind": "klines", "asset": "a", "http_status": 200},
            {"kind": "klines", "asset": "a", "http_status": 404},
            {"kind": "funding", "asset": "b", "http_status": 200},
            {"kind": "funding", "asset": "b", "http_status": None, "error": "timeout"},
        ]
        s = mod.summarize(results)
        self.assertEqual(s["n_total"], 4)
        self.assertEqual(s["n_200"], 2)
        self.assertEqual(s["n_404"], 1)
        self.assertEqual(s["n_error"], 1)
        self.assertAlmostEqual(s["coverage_frac"], 0.5)
        self.assertEqual(s["per_kind"]["klines"]["n_200"], 1)
        self.assertEqual(s["per_asset"]["b"]["n_error"], 1)

    def test_summarize_empty(self):
        s = mod.summarize([])
        self.assertEqual(s["n_total"], 0)
        self.assertEqual(s["coverage_frac"], 0.0)


class DecisionRuleTests(unittest.TestCase):
    def _summary(self, n_total, n_200, n_error=0):
        return {"n_total": n_total, "n_200": n_200, "n_error": n_error}

    def test_control_failed(self):
        label, checks = mod.decide_label(False, self._summary(10, 10))
        self.assertEqual(label, "PROBE_CONTROL_FAILED")
        self.assertFalse(checks["control_ok"])

    def test_fully_served(self):
        label, _ = mod.decide_label(True, self._summary(10, 10))
        self.assertEqual(label, "ARCHIVE_PLAN_FULLY_SERVED")

    def test_partially_served(self):
        label, _ = mod.decide_label(True, self._summary(10, 7))
        self.assertEqual(label, "ARCHIVE_PLAN_PARTIALLY_SERVED")

    def test_unserved(self):
        label, _ = mod.decide_label(True, self._summary(10, 0))
        self.assertEqual(label, "ARCHIVE_PLAN_UNSERVED")

    def test_errors_block_fully_served(self):
        # A single transient error must not be reported as fully served.
        label, _ = mod.decide_label(True, self._summary(10, 9, n_error=1))
        self.assertEqual(label, "ARCHIVE_PLAN_PARTIALLY_SERVED")


class FrozenHashTests(unittest.TestCase):
    def test_all_frozen_hashes_match(self):
        frozen = mod.verify_frozen_hashes()
        for name, row in frozen.items():
            with self.subTest(frozen=name):
                self.assertTrue(row["match"], row)
        self.assertIn("h41_plan", frozen)


class CommittedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path, cls.artifact = _committed_artifact()

    def test_identity_and_status(self):
        a = self.artifact
        self.assertEqual(a["audit_id"], mod.AUDIT_ID)
        self.assertEqual(a["experiment_id"], mod.EXPERIMENT_ID)
        self.assertEqual(a["hypothesis"], "H43")
        self.assertEqual(a["status"], "EXPLORATORY_ONLY")
        self.assertIn(
            a["label"],
            {
                "PROBE_CONTROL_FAILED",
                "ARCHIVE_PLAN_FULLY_SERVED",
                "ARCHIVE_PLAN_PARTIALLY_SERVED",
                "ARCHIVE_PLAN_UNSERVED",
            },
        )

    def test_all_frozen_hashes_match(self):
        self.assertTrue(self.artifact["all_frozen_hashes_match"])
        for section in ("frozen_hashes_verified_before", "frozen_hashes_verified_after"):
            for name, row in self.artifact[section].items():
                with self.subTest(section=section, frozen=name):
                    self.assertTrue(row["match"], row)

    def test_controls_ok(self):
        controls = self.artifact["controls"]
        self.assertTrue(controls["control_ok"])
        self.assertTrue(controls["positive_control"]["ok"])
        self.assertEqual(controls["positive_control"]["klines_status"], 200)
        self.assertEqual(controls["positive_control"]["funding_status"], 200)
        self.assertTrue(controls["negative_control"]["ok"])
        self.assertEqual(controls["negative_control"]["status"], 404)

    def test_summary_internal_consistency(self):
        s = self.artifact["summary"]
        self.assertEqual(s["n_total"], len(self.artifact["per_entry"]))
        self.assertEqual(
            s["n_200"] + s["n_404"] + s["n_other_status"] + s["n_error"],
            s["n_total"],
        )
        self.assertEqual(s["n_total"], 920)

    def test_per_entry_statuses_are_valid(self):
        for r in self.artifact["per_entry"]:
            with self.subTest(entry=(r["symbol"], r["kind"], r["month"])):
                self.assertIn(r["http_status"], (200, 404, None))
                if r["http_status"] is None:
                    self.assertIsNotNone(r["error"])

    def test_targets_equal_committed_h41_plan(self):
        plan = json.loads(H41_PLAN.read_text(encoding="utf-8"))
        expected = [(e["symbol"], e["kind"], e["month"]) for e in plan["plan_entries"]]
        got = [(r["symbol"], r["kind"], r["month"]) for r in self.artifact["per_entry"]]
        self.assertEqual(got, expected)

    def test_no_download_or_outcome_claims(self):
        non_claims = self.artifact["non_claims"]
        self.assertIn("no_content_downloaded", non_claims)
        self.assertIn("no_outcome_or_inference", non_claims)
        self.assertIn("no_cutoff_month_reprobe", non_claims)
        self.assertIn("no_fabricated_missing_files", non_claims)
        self.assertEqual(self.artifact["inputs"]["probe_method"],
                         "keyless HTTP HEAD (no body read, no download)")


if __name__ == "__main__":
    unittest.main()