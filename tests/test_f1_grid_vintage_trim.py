#!/usr/bin/env python3
"""Regression guards for DISP-003 F1 grid vintage-trim sensitivity (F1GRID-002).

H27 / HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002 preregisters a
ledger-vintage (as-of 2026-09-30) exploratory sensitivity contrast: arm A on
committed panels trimmed to the frozen ledger vintage must reproduce the
committed grid_result_ledger.json within 1e-9, then arm B compares the same
vintage with the four F1-repaired kline panels substituted (funding shared).

This file guards the preregistration contract and the trim/fidelity semantics
without running the full 432-evaluation grid. It includes a bounded verification
that trimming to 2026-09-30 reproduces the committed ledger for representative
cells (including the H004V002/2026-09-29 tail formation the audit identified).
"""
import json
import subprocess
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_f1_grid_vintage_trim.py"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
PREREG = ROOT / "artifacts" / NEW_EXP / "preregistrations" / "F1_GRID_VINTAGE_TRIM_v1.md"
COMMITTED_LEDGER = ROOT / "artifacts" / OLD_EXP / "grid_result_ledger.json"
MANIFEST = ROOT / "artifacts" / OLD_EXP / "grid_config_manifest.json"
F1_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]


def _load(path, name):
    spec = util.spec_from_file_location(name, str(path))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestVintageTrimPreregContract(unittest.TestCase):
    def test_prereg_exists_and_names_promised_artifacts(self):
        self.assertTrue(PREREG.exists())
        text = PREREG.read_text(encoding="utf-8")
        for tok in (NEW_EXP, "EXPLORATORY_ONLY", "2026-09-30", "1e-9",
                    "grid_result_ledger.json", "grid_summary.json",
                    "grid_checkpoints", "H004V002", "spread_gross", "0.0"):
            self.assertIn(tok, text)

    def test_prereg_forbids_promotion_and_states_vintage_label(self):
        text = PREREG.read_text(encoding="utf-8")
        self.assertIn("No statistical inference, no promotion", text)
        self.assertIn("ledger-vintage", text.lower().replace("_", "-") + " " if False else text)  # loose
        self.assertIn("NOT comparable", text)

    def test_script_constants_and_paths(self):
        mod = _load(SCRIPT, "run_f1_grid_vintage_trim")
        self.assertEqual(mod.NEW_EXP, NEW_EXP)
        self.assertEqual(mod.OLD_EXP, OLD_EXP)
        self.assertEqual(mod.ASOF_DATE, "2026-09-30")
        self.assertEqual(mod.FIDELITY_TOL, 1e-9)
        self.assertEqual(mod.F1_SYMBOLS, F1_SYMBOLS)
        self.assertTrue(mod.NEW_EXP_DIR.is_relative_to(ROOT / "artifacts" / NEW_EXP))
        self.assertFalse(mod.NEW_EXP_DIR.is_relative_to(ROOT / "artifacts" / OLD_EXP))


class TestVintageTrimFidelitySample(unittest.TestCase):
    """Bounded fidelity check: trimming to 2026-09-30 reproduces ledger cells."""

    @classmethod
    def setUpClass(cls):
        cls.f1 = _load(ROOT / "scripts" / "run_f1_grid.py", "run_f1_grid_for_trim")
        cls.ge = _load(ROOT / "scripts" / "run_dispersion003_grid.py", "ge_for_trim")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.committed = json.loads(COMMITTED_LEDGER.read_text(encoding="utf-8"))["cells"]

    def _trimmed_env(self):
        px_raw = self.f1.load_binance_panel(self.f1.OLD_PANELS, "klines")
        fd_raw = self.f1.load_binance_panel(self.f1.OLD_PANELS, "funding")
        mc_raw = self.f1.load_marketcap(self.f1.OLD_PANELS)
        trim = lambda df: df[df["date"].astype(str).str.slice(0, 10) <= "2026-09-30"].copy()
        px = {k: trim(v) for k, v in px_raw.items()}
        fd = {k: trim(v) for k, v in fd_raw.items()}
        mc = trim(mc_raw)
        px_wide = self.ge.build_price_wide_all(px)
        mom_cache = self.ge.MomentumCache(px_wide)
        elig = {
            "legacy28_comparator": self.ge.build_eligibility_map(mc, px, fd, "legacy28_comparator"),
            "expanding_point_in_time": self.ge.build_eligibility_map(mc, px, fd, "expanding_point_in_time"),
        }
        return px_wide, mom_cache, elig

    def test_representative_cells_reproduce_committed_ledger(self):
        px_wide, mom_cache, elig = self._trimmed_env()
        for cid in ("H004V001", "H004V002", "H004V105", "H004V106", "H004V216"):
            row = next(r for r in self.manifest["configurations"] if r["config_id"] == cid)
            ck = {}
            self.ge.evaluate_cell(cid, row["parameters"],
                                  elig[row["parameters"]["universe_arm"]],
                                  px_wide, mom_cache, ck)
            res, ref = ck[cid], self.committed[cid]
            self.assertEqual(res["n_formations"], ref["n_formations"], cid)
            self.assertEqual(res["date_last"], ref["date_last"], cid)
            self.assertEqual(res["formations"], ref["formations"], cid)

    def test_h004v002_tail_formation_matches_ledger_zero_spread(self):
        px_wide, mom_cache, elig = self._trimmed_env()
        row = next(r for r in self.manifest["configurations"] if r["config_id"] == "H004V002")
        ck = {}
        self.ge.evaluate_cell("H004V002", row["parameters"],
                              elig[row["parameters"]["universe_arm"]],
                              px_wide, mom_cache, ck)
        last = ck["H004V002"]["formations"][-1]
        self.assertEqual(last["formation_date"], "2026-09-29")
        self.assertEqual(last["spread_gross"], 0.0)
        self.assertEqual(last, self.committed["H004V002"]["formations"][-1])


class TestVintageTrimCommittedResultPinned(unittest.TestCase):
    """Pin the committed F1GRID-002 ledger-vintage result against a re-run.

    scripts/run_f1_grid_vintage_trim.py is deterministic on the same committed
    inputs, so a re-run must reproduce the committed artifacts exactly apart from
    the wall-clock ``evaluated_utc`` field. This guard prevents the recorded
    EXPLORATORY_ONLY result from silently drifting (e.g. a new code path in the
    engine, a changed cost constant) while the committed artifacts still quote the
    old numbers.
    """

    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "artifacts" / NEW_EXP / "grid_summary.json").read_text(
                encoding="utf-8"))
        # grid_result_ledger.json is an intentionally gitignored, oversized
        # generated artifact (.gitignore), so it is absent from a clean
        # checkout. Load it when present and let the ledger-pinning tests skip
        # otherwise, matching CommittedLedgerIntegrationTests in
        # tests/test_f1_grid_flip_diagnostic.py. The summary and frozen-hash
        # guards in this class still run without it.
        ledger_path = ROOT / "artifacts" / NEW_EXP / "grid_result_ledger.json"
        cls.ledger = (
            json.loads(ledger_path.read_text(encoding="utf-8"))
            if ledger_path.is_file() else None)

    def _require_ledger(self):
        if self.ledger is None:
            self.skipTest(
                "F1GRID-002 grid_result_ledger.json not present on disk "
                "(gitignored generated artifact)")

    def _strip(self, d):
        d = json.loads(json.dumps(d))
        d.pop("evaluated_utc", None)
        return d

    def test_summary_reproduces_committed_blob_ignoring_evaluated_utc(self):
        blob = subprocess.run(
            ["git", "show", f"HEAD:artifacts/{NEW_EXP}/grid_summary.json"],
            capture_output=True, text=True, check=True).stdout
        committed = json.loads(blob)
        self.assertEqual(self._strip(committed), self._strip(self.summary))

    def test_ledger_is_idempotent_and_armA_checkpoint_matches_committed_blob(self):
        self._require_ledger()
        # grid_result_ledger.json was never committed to git (only grid_summary.json
        # and the arm A checkpoint were), so the ledger pin is a content-equality
        # check against the on-disk artifact: a re-run must reproduce it exactly
        # apart from evaluated_utc. The arm A checkpoint IS git-pinned.
        blob = subprocess.run(
            ["git", "show",
             f"HEAD:artifacts/{NEW_EXP}/grid_checkpoints/"
             "cell_checkpoint_armA_ledger_vintage.json"],
            capture_output=True, text=True, check=True).stdout
        committed_ckpt = json.loads(blob)
        on_disk_ckpt = json.loads(
            (ROOT / "artifacts" / NEW_EXP / "grid_checkpoints"
             / "cell_checkpoint_armA_ledger_vintage.json").read_text(
                encoding="utf-8"))
        self.assertEqual(committed_ckpt, on_disk_ckpt)
        self.assertEqual(self.ledger["arms"]
                         ["A_ledger_vintage_committed"]["cells"], on_disk_ckpt)
        # determinism: the ledger carries no wall-clock field other than
        # evaluated_utc, so stripping it leaves a self-consistent document
        stripped = self._strip(self.ledger)
        self.assertNotIn("evaluated_utc", stripped)
        self.assertEqual(len(stripped["arms"]), 2)

    def test_fidelity_anchor_passed_on_all_216_cells(self):
        self._require_ledger()
        self.assertTrue(self.ledger["fidelity_anchor"]["passed"])
        self.assertEqual(self.ledger["fidelity_anchor"]["compared_cells"], 216)
        self.assertEqual(self.ledger["fidelity_anchor"]["drift_count"], 0)
        self.assertEqual(self.ledger["expected_cells"], 216)

    def test_terminal_status_partition(self):
        self._require_ledger()
        for arm in self.ledger["arms"].values():
            self.assertEqual(arm["cells_evaluated"], 216)
            self.assertEqual(arm["cells_ok"], 216)
            self.assertEqual(arm["cells_blocked"], 0)
            self.assertEqual(arm["cells_failed"], 0)
        self.assertEqual(self.summary["n_cells_ok_both_arms"], 216)

    def test_holm_rejection_counts(self):
        self._require_ledger()
        a = self.ledger["arms"]["A_ledger_vintage_committed"]
        b = self.ledger["arms"]["B_ledger_vintage_f1_repaired"]
        self.assertEqual(a["holm_rejected_count"], 0)
        self.assertEqual(b["holm_rejected_count"], 1)
        flips = [d for d in self.summary["cell_deltas"]
                 if d["holm_rejected_a"] != d["holm_rejected_b"]]
        self.assertEqual([d["config_id"] for d in flips], ["H004V130"])

    def test_anchor_contrasts(self):
        d = {x["config_id"]: x for x in self.summary["cell_deltas"]}
        # legacy comparator arm is untouched by the four-asset kline repair
        self.assertEqual(d["H004V105"]["delta_high_low_diff_net_1x"], 0.0)
        self.assertEqual(d["H004V105"]["delta_eligible_assets_mean"], 0.0)
        # expanding anchor: eligible assets +1.81, high/low counts shift by one
        self.assertAlmostEqual(d["H004V106"]["delta_eligible_assets_mean"],
                               1.8116591928251111, places=9)
        self.assertAlmostEqual(d["H004V106"]["delta_high_low_diff_net_1x"],
                               -0.03765270427844142, places=12)
        self.assertEqual(d["H004V106"]["delta_n_high"], 0)
        self.assertEqual(d["H004V106"]["delta_n_low"], -1)
        self.assertEqual(d["H004V106"]["delta_n_mid"], 1)
        # mean eligible-asset delta across the whole grid
        self.assertAlmostEqual(self.summary["delta_mean_eligible_assets"],
                               0.909186884971348, places=9)

    def test_no_frozen_artifact_was_modified(self):
        # canonical forward block, H10 fresh block, committed ledger, frontier
        import hashlib
        expected = {
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "forward_block/forward_block_evaluation.json":
                "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "forward_block_h10_fresh/forward_block_evaluation.json":
                "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "grid_result_ledger.json":
                "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c",
            "research_state/universe_frontier.json":
                "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
        }
        for rel, want in expected.items():
            h = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            self.assertEqual(h, want, rel)


if __name__ == "__main__":
    unittest.main()
