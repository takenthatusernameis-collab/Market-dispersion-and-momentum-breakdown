#!/usr/bin/env python3
"""Regression guards for the DISP-003 full-grid F1 coverage sensitivity run.

DISP-003-F1GRID-001 (``scripts/run_f1_grid.py``) runs the complete 216-cell
DISPERSION-003 sensitivity grid twice on already-available development panels:
arm A on the committed panels (the fidelity anchor, which must reproduce the
committed ``grid_result_ledger.json`` within 1e-9 on every cell) and arm B on
the same panels with only the four F1COVERAGE-001-repaired kline panels
overridden in memory (funding is NOT substituted). It is EXPLORATORY_ONLY
descriptive evidence: bootstrap p-values and Holm rejections are computed per
arm for contrast only, never for promotion.

The preregistration
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/preregistrations/F1_GRID_COVERAGE_REPAIR_v1.md``
(sec 6) promised this guard file, and no such file existed on disk. This file
supplies it.

Guards (stdlib + the two committed artifacts only; no network, no new market
evidence, no writing):
  1. The preregistration names the script, the test and every promised output.
  2. Script constants isolate the new experiment and pin the declared fidelity
     tolerance, the four substituted symbols and the read-only frozen list.
  3. ``fidelity_check`` semantics: exact/within-tolerance agreement passes,
     a real drift fails with a located path, ``evaluated_utc`` is ignored and
     missing keys or length mismatches fail.
  4. ``build_arm_panels`` substitutes exactly the four F1 kline panels and
     shares the funding frames by identity (funding is not substituted).
  5. ``cell_counts`` reports the terminal status partition of an arm.
"""
import hashlib
import json
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_f1_grid.py"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001"
OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
F1_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"
PREREG = (ROOT / "artifacts" / NEW_EXP / "preregistrations"
          / "F1_GRID_COVERAGE_REPAIR_v1.md")
F1_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_module():
    spec = util.spec_from_file_location("run_f1_grid", str(SCRIPT))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cell(**over):
    cell = {
        "config_id": "H004V001",
        "status": "OK",
        "evaluated_utc": "2026-11-14T04:04:18Z",
        "high_low_diff_net_1x": 0.5,
        "spread_net_1x_mean": 0.1,
        "spread_net_1x_median": 0.01,
        "n_formations": 10,
        "n_high": 3,
        "n_low": 4,
        "n_mid": 3,
        "formations": [{"date": "2025-01-02", "state": "high", "spread_net_1x": 0.2}],
        "reason": "",
    }
    cell.update(over)
    return cell


class TestF1GridPreregContract(unittest.TestCase):
    def test_preregistration_exists_and_names_every_promised_artifact(self):
        self.assertTrue(PREREG.exists(), f"missing preregistration {PREREG}")
        text = PREREG.read_text(encoding="utf-8")
        for token in (
            NEW_EXP,
            "scripts/run_f1_grid.py",
            "tests/test_f1_grid_coverage_repair.py",
            "grid_result_ledger.json",
            "grid_summary.json",
            "grid_checkpoints/",
            "EXPLORATORY_ONLY",
        ):
            self.assertIn(token, text)

    def test_preregistration_forbids_promotion_and_declares_the_fidelity_anchor(self):
        text = PREREG.read_text(encoding="utf-8")
        self.assertIn("No statistical inference, no promotion", text)
        self.assertIn("1e-9", text)
        self.assertIn("F1COVERAGE-001", text)


class TestF1GridConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_experiment_ids_are_single_prefixed_and_distinct(self):
        self.assertEqual(self.mod.NEW_EXP, NEW_EXP)
        self.assertEqual(self.mod.NEW_EXP.count("HARMONY-CRYPTO-EDGE-004-"), 1)
        self.assertEqual(self.mod.OLD_EXP, OLD_EXP)
        self.assertEqual(self.mod.F1_EXP, F1_EXP)
        self.assertNotEqual(self.mod.NEW_EXP, self.mod.OLD_EXP)
        self.assertNotEqual(self.mod.NEW_EXP, self.mod.F1_EXP)

    def test_outputs_are_isolated_to_the_new_experiment_component(self):
        for path in (self.mod.OUT_LEDGER, self.mod.OUT_SUMMARY, self.mod.OUT_CHECKPOINTS):
            self.assertTrue(path.is_relative_to(ROOT / "artifacts" / NEW_EXP), path)
            # Component-wise: the new id extends the old id textually, so a raw
            # string prefix check would not prove real isolation.
            self.assertFalse(path.is_relative_to(ROOT / "artifacts" / OLD_EXP), path)

    def test_fidelity_tolerance_and_substituted_symbols_are_declared(self):
        self.assertEqual(self.mod.FIDELITY_TOL, 1e-9)
        self.assertEqual(self.mod.F1_SYMBOLS, F1_SYMBOLS)

    def test_frozen_read_only_list_covers_both_blocks_and_both_ledgers(self):
        rels = set(self.mod.FROZEN_ARTIFACT_RELS)
        self.assertEqual(rels, {
            "forward_block/forward_block_evaluation.json",
            "forward_block_h10_fresh/forward_block_evaluation.json",
            "grid_result_ledger.json",
            "grid_summary.json",
        })
        for rel in rels:
            self.assertTrue((ROOT / "artifacts" / OLD_EXP / rel).exists(), rel)


class TestF1GridFidelitySemantics(unittest.TestCase):
    """The fidelity anchor is the only guard against a silently wrong arm A."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_identical_cells_pass(self):
        a = {"H004V001": _cell()}
        b = {"H004V001": _cell()}
        res = self.mod.fidelity_check(a, b)
        self.assertTrue(res["passed"], res["drifted"])
        self.assertEqual(res["drift_count"], 0)
        self.assertEqual(res["compared_cells"], 1)

    def test_within_tolerance_float_differences_pass(self):
        a = {"H004V001": _cell(high_low_diff_net_1x=0.5)}
        b = {"H004V001": _cell(high_low_diff_net_1x=0.5 + 1e-12)}
        res = self.mod.fidelity_check(a, b)
        self.assertTrue(res["passed"], res["drifted"])

    def test_real_drift_fails_and_locates_the_path(self):
        a = {"H004V001": _cell(high_low_diff_net_1x=0.5)}
        b = {"H004V001": _cell(high_low_diff_net_1x=0.6)}
        res = self.mod.fidelity_check(a, b)
        self.assertFalse(res["passed"])
        self.assertEqual(res["drift_count"], 1)
        self.assertTrue(any("high_low_diff_net_1x" in d for d in res["drifted"]))

    def test_formation_level_drift_is_located(self):
        a = {"H004V001": _cell()}
        b = {"H004V001": _cell(formations=[
            {"date": "2025-01-02", "state": "high", "spread_net_1x": 0.9}])}
        res = self.mod.fidelity_check(a, b)
        self.assertFalse(res["passed"])
        self.assertTrue(any("formations" in d for d in res["drifted"]))

    def test_evaluated_utc_is_not_compared(self):
        a = {"H004V001": _cell(evaluated_utc="2026-11-14T04:04:18Z")}
        b = {"H004V001": _cell(evaluated_utc="2026-11-15T09:00:00Z")}
        res = self.mod.fidelity_check(a, b)
        self.assertTrue(res["passed"], res["drifted"])

    def test_missing_key_fails(self):
        a = {"H004V001": _cell()}
        b = {"H004V001": {k: v for k, v in _cell().items() if k != "n_high"}}
        res = self.mod.fidelity_check(a, b)
        self.assertFalse(res["passed"])

    def test_cell_id_mismatch_fails(self):
        res = self.mod.fidelity_check({"H004V001": _cell()}, {"H004V002": _cell()})
        self.assertFalse(res["passed"])
        self.assertEqual(res["compared_cells"], 0)

    def test_values_close_handles_nan_and_length_mismatch(self):
        drifted = []
        self.mod.values_close(float("nan"), float("nan"), "x", drifted)
        self.assertEqual(drifted, [])
        self.mod.values_close([1.0, 2.0], [1.0], "y", drifted)
        self.assertTrue(drifted)


class TestF1GridCellCounts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_status_partition_and_holm_count(self):
        cells = {
            "H004V001": _cell(),
            "H004V002": _cell(status="BLOCKED", reason="gate"),
            "H004V003": _cell(status="FAILED", reason="boom"),
            "H004V004": _cell(holm_rejected=True),
        }
        counts = self.mod.cell_counts({"cells": cells})
        self.assertEqual(counts["cells_evaluated"], 4)
        self.assertEqual(counts["cells_ok"], 2)
        self.assertEqual(counts["cells_blocked"], 1)
        self.assertEqual(counts["cells_failed"], 1)
        self.assertEqual(counts["holm_rejected_count"], 1)


class TestF1GridPanelSubstitution(unittest.TestCase):
    """Arm B must differ from arm A only in the four repaired kline panels."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        import pandas as pd

        def frame(tag):
            return pd.DataFrame({"date": ["2025-01-01", "2025-01-02"],
                                 "close": [1.0, 2.0]}).assign(tag=tag)

        px = {f"SYM{i}USDT": frame(f"a{i}") for i in range(3)}
        px.update({s: frame(f"committed_{s}") for s in F1_SYMBOLS})
        fd = {s: frame(f"funding_{s}") for s in list(px)}
        cls.committed_px, cls.committed_fd = px, fd
        cls.arm_a, cls.arm_b = cls.mod.build_arm_panels(px, fd)

    def test_arm_a_is_the_committed_panel_set_unchanged(self):
        px_a, fd_a, _ = self.arm_a
        self.assertEqual(set(px_a), set(self.committed_px))
        for symbol, frame in self.committed_px.items():
            self.assertTrue(px_a[symbol].equals(frame), symbol)
        self.assertEqual(set(fd_a), set(self.committed_fd))

    def test_arm_b_keeps_every_non_repaired_panel(self):
        px_a, _, _ = self.arm_a
        px_b, _, _ = self.arm_b
        self.assertEqual(set(px_a), set(px_b))
        for symbol in set(px_a) - set(F1_SYMBOLS):
            self.assertTrue(px_a[symbol].equals(px_b[symbol]), symbol)

    def test_arm_b_kline_frames_match_the_committed_f1_panels(self):
        px_b, _, _ = self.arm_b
        f1_px = self.mod.load_binance_panel(self.mod.F1_PANELS, "klines")
        for symbol in F1_SYMBOLS:
            self.assertIn(symbol, f1_px)
            self.assertEqual(len(px_b[symbol]), len(f1_px[symbol]))
            self.assertTrue(px_b[symbol]["close"].equals(f1_px[symbol]["close"]),
                            symbol)

    def test_arm_b_replaces_the_committed_klines_for_repaired_symbols(self):
        px_a, _, _ = self.arm_a
        px_b, _, _ = self.arm_b
        f1_px = self.mod.load_binance_panel(self.mod.F1_PANELS, "klines")
        replaced = [s for s in F1_SYMBOLS
                    if not px_a[s]["close"].equals(px_b[s]["close"])]
        self.assertTrue(replaced, "arm B did not replace any committed kline panel")
        for symbol in replaced:
            self.assertTrue(px_b[symbol]["close"].equals(f1_px[symbol]["close"]),
                            symbol)

    def test_funding_is_not_substituted_between_arms(self):
        _, fd_a, _ = self.arm_a
        _, fd_b, _ = self.arm_b
        self.assertIs(fd_a, fd_b)

    def test_missing_f1_panel_is_a_hard_error(self):
        """A missing repaired kline panel must abort, never silently skip."""
        import tempfile
        import pandas as pd
        from unittest import mock

        frame = pd.DataFrame({"date": ["2025-01-01"], "close": [1.0]})
        px = {s: frame.copy() for s in F1_SYMBOLS}
        fd = {s: frame.copy() for s in F1_SYMBOLS}
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(self.mod, "F1_PANELS", Path(tmp)):
                with self.assertRaises(FileNotFoundError):
                    self.mod.build_arm_panels(px, fd)


class TestF1GridExecutionStateAudit(unittest.TestCase):
    """The execution-state audit must stay a faithful record of the run.

    The preregistered fidelity anchor cannot be met on the current committed
    panel vintage, so the run aborts and writes no comparison. That leaves a
    durable record whose whole value is that it matches disk; these guards pin
    the record to the artifacts it describes (hash-only, no large parse) and
    forbid the record from ever claiming a completed, promotable run.
    """

    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        audit_dir = ROOT / "artifacts" / NEW_EXP / "integrity_audit"
        cls.audits = sorted(audit_dir.glob("f1_grid_execution_state_audit_*.json"))
        cls.audit = json.loads(cls.audits[-1].read_text(encoding="utf-8"))

    def test_committed_audit_exists(self):
        self.assertTrue(self.audits, "no committed F1GRID execution-state audit")

    def test_audit_is_well_formed_and_hypothesis_scoped(self):
        self.assertEqual(self.audit["audit_id"], "F1GRID-001-EXECUTION-STATE")
        self.assertEqual(self.audit["experiment_id"], NEW_EXP)
        self.assertEqual(self.audit["hypothesis"], "H26")
        self.assertIn(self.audit["status"], {
            "NOT_RUN", "BLOCKED_SPECIFICATION_GATE", "BLOCKED_DATA_GATE",
            "IMPLEMENTATION_FAILED", "EXPLORATORY_ONLY", "INCONCLUSIVE",
        })
        self.assertIn(self.audit["verdict"], {
            "PASS_EXECUTION_COMPLETE",
            "BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE",
            "INCOMPLETE_UNEXPECTED_STATE",
            "NOT_RUN",
        })

    def test_blocked_verdict_is_never_labelled_a_completed_run(self):
        if self.audit["verdict"].startswith("BLOCKED"):
            self.assertTrue(self.audit["status"].startswith("BLOCKED"))
            self.assertFalse(self.audit["evidence"]["outputs"]["ledger_present"])
            self.assertFalse(self.audit["disposition"]["comparison_written"])
        if self.audit["verdict"] == "PASS_EXECUTION_COMPLETE":
            self.assertTrue(self.audit["evidence"]["outputs"]["ledger_present"])
            self.assertTrue(self.audit["fidelity"]["fidelity_passed"])

    def test_audit_pins_the_artifacts_it_describes(self):
        ev = self.audit["evidence"]
        for key, rel in (
            ("prereg_sha256", PREREG),
            ("script_sha256", SCRIPT),
            ("arm_a_checkpoint_sha256",
             ROOT / "artifacts" / NEW_EXP / "grid_checkpoints"
             / "cell_checkpoint_armA_committed.json"),
            ("committed_ledger_sha256",
             ROOT / "artifacts" / OLD_EXP / "grid_result_ledger.json"),
        ):
            self.assertTrue(rel.exists(), rel)
            self.assertEqual(ev[key], _sha256_file(rel), key)

    def test_frozen_artifacts_match_their_declared_constants(self):
        frozen = self.audit["frozen_artifacts"]
        self.assertEqual(set(frozen), {
            "forward_block/forward_block_evaluation.json",
            "forward_block_h10_fresh/forward_block_evaluation.json",
        })
        for rel, entry in frozen.items():
            self.assertTrue(entry["matches_declared_constant"], rel)
            self.assertEqual(
                entry["sha256"],
                _sha256_file(ROOT / "artifacts" / OLD_EXP / rel), rel)

    def test_recorded_vintage_mismatch_is_real(self):
        vm = self.audit["vintage_mismatch"]
        self.assertGreater(vm["panel_max_kline_date"], vm["ledger_max_formation_date"])
        self.assertLess(vm["arm_a_max_formation_date"],
                        vm["panel_max_kline_date"])
        self.assertGreater(vm["arm_a_max_formation_date"],
                           vm["ledger_max_formation_date"])
        contrast = vm["tail_formation_contrast"]
        self.assertEqual(contrast["formation_date"], vm["ledger_max_formation_date"])
        self.assertEqual(contrast["ledger_n_assets"], contrast["arm_a_n_assets"])
        self.assertNotEqual(contrast["ledger_spread_gross"],
                            contrast["arm_a_spread_gross"])

    def test_fidelity_failure_is_reported_with_its_scale(self):
        fid = self.audit["fidelity"]
        self.assertFalse(fid["fidelity_passed"])
        self.assertEqual(fid["compared_cells"], 216)
        self.assertGreater(fid["drift_count"], 0)
        self.assertEqual(fid["cells_with_different_date_last"], 216)
        self.assertTrue(fid["sample_drifts"])

    def test_audit_never_claims_promotion(self):
        self.assertFalse(self.audit["disposition"]["frozen_artifacts_modified"])
        self.assertFalse(self.audit["disposition"]["committed_panels_modified"])
        self.assertIn("no", self.audit["disposition"]["promotion"].lower())


if __name__ == "__main__":
    unittest.main()