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


if __name__ == "__main__":
    unittest.main()
