"""Regression tests for the price-level vs return-based momentum defect.

DISPERSION-003 was computed with a cumulative product of (1 + price) across
the cross-section, which multiplies dollar magnitudes (~1e9-1e12 per asset).
The resulting "momentum" was dominated by price level, dispersion was ~1e128,
the decile split ranked by price level rather than return dispersion, and the
dispersion-state thresholds were meaningless. The grid and sealed forward block
were both recomputed using daily returns.

These tests pin the corrected behaviour so the defect cannot regress silently.
"""
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class MomentumAccountingTests(unittest.TestCase):
    def _make_price_frame(self) -> pd.DataFrame:
        idx = pd.date_range("2023-01-01", periods=40, freq="D", tz="UTC")
        rng = __import__("random").Random(7)
        # Two assets: one high-price-level, one low-price-level, both with
        # bounded returns. Price level alone must not determine the ranking.
        high = [100_000.0]
        low = [10.0]
        for _ in range(39):
            high.append(high[-1] * (1 + rng.uniform(-0.05, 0.05)))
            low.append(low[-1] * (1 + rng.uniform(-0.05, 0.05)))
        return pd.DataFrame({"high_level": high, "low_level": low}, index=idx)

    def test_return_based_momentum_is_order_one_in_price(self):
        px = self._make_price_frame()
        ret = px.pct_change().iloc[-30:]
        comp = (1.0 + ret).prod() - 1.0
        # A 30-day cumulative return is order 1, never ~1e128.
        for v in comp:
            self.assertLess(abs(v), 100.0, msg=f"momentum magnitude {v} not order-1")

    def test_price_level_momentum_is_unbounded(self):
        px = self._make_price_frame()
        comp = (1.0 + px).prod() - 1.0
        # The defective computation multiplies price levels and explodes.
        self.assertGreater(max(abs(comp)), 1e6)

    def test_dispersion_of_returns_is_bounded(self):
        px = self._make_price_frame()
        ret = px.pct_change().iloc[-30:]
        comp = (1.0 + ret).prod() - 1.0
        self.assertLess(comp.std(ddof=0), 10.0)

    def test_dispersion_of_price_levels_is_unbounded(self):
        px = self._make_price_frame()
        comp = (1.0 + px).prod() - 1.0
        self.assertGreater(comp.std(ddof=0), 1e6)

    def test_forward_block_uses_return_momentum(self):
        """The committed forward-block script must compute momentum from daily
        returns (returns_wide), not from a cumulative product of raw prices."""
        src = (ROOT / "scripts" / "eval_forward_block.py").read_text()
        self.assertIn("pct_change()", src)
        self.assertIn("returns_wide", src)
        self.assertIn("MomentumCache", src)
        # The MomentumCache constructor must build a returns frame, and the
        # cumulative product must operate on that returns frame.
        self.assertIn("self.returns_wide = px_wide.pct_change()", src)
        self.assertIn("window = self.returns_wide.iloc", src)

    def test_grid_ledger_dispersion_magnitudes_are_order_one(self):
        """Committed ledger cells must not carry ~1e128 dispersion values."""
        import json
        ledger = json.loads(
            (ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
             / "grid_result_ledger.json").read_text()
        )
        for cid, cell in ledger["cells"].items():
            for f in cell.get("formations", []):
                d = f.get("dispersion")
                if d is None:
                    continue
                self.assertLess(abs(d), 100.0,
                                msg=f"{cid} dispersion {d} not order-1")


if __name__ == "__main__":
    unittest.main()