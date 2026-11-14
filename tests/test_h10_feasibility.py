"""Regression guard for the H10 structural feasibility analysis.

DISP-003-H10-FEASIBILITY-001 (artifacts/.../integrity_audit/
H10_feasibility_analysis_20261103.json) established, from on-disk panels only,
that the current 2026-10-31 cutoff yields exactly 1 fresh-block formation and
that the trailing-decile state rule therefore cannot classify high/low. This
test pins those hard structural facts so that a silent drift in the panels or
in the evaluator's horizon math fails the build.

Pure stdlib + pandas (no network, no frozen artifact modified).
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _has_module(name: str) -> bool:
    """dep-light probe: True when the named module imports."""
    try:
        __import__(name)
        return True
    except Exception:
        return False


_HAS_PANDAS = _has_module("pandas")

try:
    import importlib
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    _eval_fb = importlib.import_module("eval_forward_block")
    assign_trailing_decile_states = _eval_fb.assign_trailing_decile_states
    MIN_PRIOR_DISPERSIONS = _eval_fb.MIN_PRIOR_DISPERSIONS
    _EVAL_FB_AVAILABLE = True
except Exception:
    _eval_fb = None
    assign_trailing_decile_states = None
    MIN_PRIOR_DISPERSIONS = None
    _EVAL_FB_AVAILABLE = False

try:
    import pandas as pd
except Exception:
    pd = None  # dep-light: whole class is skipped dep-light

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
PANEL_DIR = ART / "data" / "panels"
FRESH = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
FEAS = ART / "integrity_audit" / "H10_feasibility_analysis_20261103.json"
HORIZON = 30
START = "2026-09-30"


def build_index():
    frames = []
    for p in sorted(PANEL_DIR.glob("binance_klines_*.csv")):
        df = pd.read_csv(p)
        col = [c for c in df.columns if "time" in c.lower()][0]
        d = pd.to_datetime(df[col], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        sym = p.stem.replace("binance_klines_", "")
        asset = sym[:-4].lower() if sym.endswith("USDT") else sym.lower()
        frames.append(pd.DataFrame({"date": d, asset: df["close"]}))
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="date", how="outer")
    idx = pd.DatetimeIndex(sorted(pd.to_datetime(merged["date"], utc=True).unique()))
    return idx


def fresh_block_formations(idx, cutoff: str) -> int:
    """Replicates eval_forward_block.py's last_allowed math exactly."""
    cutoff_ts = pd.Timestamp(cutoff, tz="UTC")
    loc = idx.get_loc(cutoff_ts)
    lad = idx[loc - HORIZON]
    return int(sum(1 for d in idx if d >= pd.Timestamp(START, tz="UTC") and d <= lad))


@unittest.skipUnless(_HAS_PANDAS and _EVAL_FB_AVAILABLE,
                     "pandas/eval_forward_block not importable (dep-light env)")
@unittest.skipUnless(_HAS_PANDAS and _EVAL_FB_AVAILABLE,
                     "pandas/eval_forward_block not importable (dep-light env)")
class TestH10Feasibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = build_index()
        cls.fresh = json.loads(FRESH.read_text())
        cls.feas = json.loads(FEAS.read_text())

    def test_artifact_exists(self):
        self.assertTrue(FEAS.is_file(), "feasibility artifact missing")

    def test_current_cutoff_yields_one_formation(self):
        n = fresh_block_formations(self.idx, "2026-10-31")
        self.assertEqual(n, 1,
                         f"expected 1 fresh-block formation at cutoff 2026-10-31, got {n}")

    def test_artifact_matches_recomputed_state(self):
        self.assertEqual(self.fresh["n_formations"], 1)
        self.assertEqual(self.fresh["last_allowed_formation_date"], "2026-09-30")
        self.assertEqual(self.fresh["n_high"], 0)
        self.assertEqual(self.fresh["n_low"], 0)
        self.assertIsNone(self.fresh["high_low_diff_net_1x"])
        self.assertEqual(self.fresh["data_cutoff_utc"], "2026-10-31T00:00:00Z")
        self.assertEqual(self.feas["observed_on_disk"]["october_2026_missing_dates"],
                         ["2026-10-28"])

    def test_october_28_gap_present_in_all_active_symbols(self):
        """2026-10-28 is absent from every kline panel still trading in October.

        Mirrors the feasibility artifact's observed_on_disk scope: 30 active
        symbols (EOSUSDT and MATICUSDT are delisted and end before October).
        """
        missing = []
        active = []
        for p in sorted(PANEL_DIR.glob("binance_klines_*.csv")):
            df = pd.read_csv(p)
            col = [c for c in df.columns if "time" in c.lower()][0]
            dates = set(pd.to_datetime(df[col], unit="ms", utc=True).dt.strftime("%Y-%m-%d"))
            sym = p.stem.replace("binance_klines_", "")
            if max(dates) >= "2026-10-01":
                active.append(sym)
                if "2026-10-28" not in dates:
                    missing.append(sym)
        # Every active symbol must show the gap (not a subset).
        self.assertEqual(sorted(missing), sorted(active))
        self.assertEqual(len(missing), 30)

    def test_state_rule_needs_thirty_prior_dispersions(self):
        """eval_forward_block.assign_trailing_decile_states: high/low state is
        only assigned when at least MIN_PRIOR_DISPERSIONS (30) strictly prior
        in-block dispersions exist, so a block with <31 formations can never
        classify. Semantics unchanged from the prior inline `if len(past) >= 30:`
        rule, now extracted into a testable function (scripts/eval_forward_block.py)."""
        self.assertEqual(MIN_PRIOR_DISPERSIONS, 30)
        src = (ROOT / "scripts" / "eval_forward_block.py").read_text()
        self.assertIn("def assign_trailing_decile_states", src)
        self.assertIn("if len(past) < min_prior:", src)
        # Behavioral pin mirroring the old inline rule.
        days = ["2026-01-%02d" % d for d in range(1, 31)]
        base = {d: 1.0 for d in days}
        extreme = dict(base)
        extreme["2026-01-31"] = 2.0  # exactly 30 strictly prior dispersions
        states = assign_trailing_decile_states(extreme, window_days=365)
        self.assertEqual(states["2026-01-31"], "high")
        self.assertEqual(
            [s for d, s in states.items() if d != "2026-01-31"],
            ["mid"] * 30,
        )

    def test_projection_first_classifiable_cutoff_is_november(self):
        self.assertEqual(self.feas["projection"]["cutoff_2026_11_30"]["state_classifiable"], True)
        self.assertEqual(self.feas["projection"]["cutoff_2026_10_31"]["state_classifiable"], False)


if __name__ == "__main__":
    unittest.main()