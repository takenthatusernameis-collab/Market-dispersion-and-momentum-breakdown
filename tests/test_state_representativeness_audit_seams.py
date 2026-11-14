"""Hermetic tests for the pure computation in scripts/state_representativeness_audit.py.

The existing ``tests/test_state_representativeness_audit.py`` only pins the
committed audit artifact JSON and never imports the module, so the inline
month-leave-one-out and largest-cluster share computations in ``main()`` have
no seam coverage. These tests monkeypatch ``BLOCK_PATH``/``OUT_PATH`` to temp
paths, run ``main()`` on small synthetic block fixtures, and assert the
computed label, deltas and cluster shares (including the CLUSTER_DOMINATED
branches) without writing to frozen artifacts.

No network, no committed-panel dependency, no frozen artifact mutation.
Synthetic fixtures are software tests only, never market evidence.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import scripts.state_representativeness_audit as sra


def _write_block(tmp: str, formations, high_mean=0.0, low_mean=0.0):
    hi = [f["spread_net_1x"] for f in formations if f["state"] == "high"]
    lo = [f["spread_net_1x"] for f in formations if f["state"] == "low"]
    baseline = (sum(hi) / len(hi) - sum(lo) / len(lo)) if hi and lo else 0.0
    block = {
        "anchor_id": "H004V106",
        "n_formations": len(formations),
        "n_high": sum(1 for f in formations if f["state"] == "high"),
        "n_low": sum(1 for f in formations if f["state"] == "low"),
        "n_mid": sum(1 for f in formations if f["state"] == "mid"),
        "high_low_diff_net_1x": baseline,
        "high_net_1x_mean": (sum(hi) / len(hi)) if hi else None,
        "low_net_1x_mean": (sum(lo) / len(lo)) if lo else None,
        "data_cutoff_utc": "2099-01-01T00:00:00Z",
        "date_first": min(f["formation_date"] for f in formations),
        "date_last": max(f["formation_date"] for f in formations),
        "block_sealed": True,
        "formations": formations,
    }
    p = Path(tmp) / "block.json"
    p.write_text(json.dumps(block), encoding="utf-8")
    return p, block


class StateRepresentativenessSeamTests(unittest.TestCase):
    def _run(self, formations):
        with tempfile.TemporaryDirectory() as tmp:
            block_path, block = _write_block(tmp, formations)
            out_path = Path(tmp) / "audit.json"
            old_block, old_out = sra.BLOCK_PATH, sra.OUT_PATH
            try:
                sra.BLOCK_PATH = block_path
                sra.OUT_PATH = out_path
                rc = sra.main()
            finally:
                sra.BLOCK_PATH, sra.OUT_PATH = old_block, old_out
            self.assertEqual(rc, 0)
            audit = json.loads(out_path.read_text(encoding="utf-8"))
        return audit, block

    def test_month_robust_when_no_month_or_cluster_dominates(self):
        # Largest high-state month by count is 2026-01 (n=2, mean 0.2). High
        # mean is 0.56 so cluster share ~0.357 <= 0.5. Other high/low months
        # have similar per-observation contributions, keeping every leave-one-out
        # delta well below the 50% threshold.
        formations = [
            {"formation_date": "2026-01-05", "state": "high", "spread_net_1x": 0.2},
            {"formation_date": "2026-01-15", "state": "high", "spread_net_1x": 0.2},
            {"formation_date": "2026-02-05", "state": "high", "spread_net_1x": 0.8},
            {"formation_date": "2026-03-05", "state": "high", "spread_net_1x": 0.8},
            {"formation_date": "2026-04-05", "state": "high", "spread_net_1x": 0.8},
            {"formation_date": "2026-05-05", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-06-05", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-07-05", "state": "low", "spread_net_1x": 0.0},
        ]
        audit, block = self._run(formations)
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertEqual(audit["label"], "MONTH_ROBUST")
        self.assertFalse(audit["calendar_month_leave_one_out"]["dominated_by_drop"])
        self.assertFalse(audit["largest_high_state_month_cluster"]["dominated_by_cluster"])
        self.assertEqual(audit["largest_high_state_month_cluster"]["month"], "2026-01")
        self.assertEqual(audit["largest_high_state_month_cluster"]["n"], 2)
        self.assertAlmostEqual(audit["largest_high_state_month_cluster"]["share_of_high_state_mean"], 0.2 / 0.56, places=12)
        self.assertAlmostEqual(audit["baseline"]["high_low_diff_net_1x"], block["high_low_diff_net_1x"], places=12)

    def test_cluster_dominated_by_month_drop(self):
        # baseline = mean(high)-mean(low) = 1.0 - (-0.5) = 1.5.
        # Dropping 2026-04 removes the only negative low: lows mean becomes 0,
        # diff becomes 1.0, delta -0.5, frac -1/3 (not > 50%).
        # Dropping 2026-02 removes a zero low: lows mean becomes -1.0,
        # diff becomes 2.0, delta +0.5, frac +1/3.
        # To exceed 50%: make a single-month low swing large enough.
        formations = [
            {"formation_date": "2026-01-10", "state": "high", "spread_net_1x": 1.0},
            {"formation_date": "2026-02-10", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-03-10", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-04-10", "state": "low", "spread_net_1x": -4.0},
        ]
        # high mean 1, low mean -4/3=-1.333..., baseline 2.333...
        # drop 2026-04: lows mean 0, diff 1.0, delta -1.333, frac -4/7 ~ -0.571 > 0.5
        audit, block = self._run(formations)
        self.assertAlmostEqual(audit["baseline"]["high_low_diff_net_1x"], 7.0 / 3.0, places=12)
        apr = audit["calendar_month_leave_one_out"]["months"]["2026-04"]
        self.assertAlmostEqual(apr["delta_frac_vs_baseline"], -4.0 / 7.0, places=12)
        self.assertTrue(audit["calendar_month_leave_one_out"]["dominated_by_drop"])
        self.assertEqual(audit["label"], "CLUSTER_DOMINATED")

    def test_month_drop_delta_none_when_side_removed(self):
        # Dropping the only high month leaves diff undefined.
        formations = [
            {"formation_date": "2026-01-10", "state": "high", "spread_net_1x": 1.0},
            {"formation_date": "2026-02-10", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-03-10", "state": "low", "spread_net_1x": 0.0},
        ]
        audit, _ = self._run(formations)
        jan = audit["calendar_month_leave_one_out"]["months"]["2026-01"]
        self.assertIsNone(jan["high_low_diff_net_1x"])
        self.assertIsNone(jan["delta_vs_baseline"])
        self.assertIsNone(jan["delta_frac_vs_baseline"])

    def test_cluster_dominated_by_largest_high_month_share(self):
        # One month contributes all high-state observations -> share 1.0 > 0.5
        formations = [
            {"formation_date": "2026-01-10", "state": "high", "spread_net_1x": 2.0},
            {"formation_date": "2026-01-20", "state": "high", "spread_net_1x": 2.0},
            {"formation_date": "2026-02-10", "state": "low", "spread_net_1x": 0.0},
            {"formation_date": "2026-03-10", "state": "low", "spread_net_1x": 0.0},
        ]
        audit, block = self._run(formations)
        self.assertEqual(audit["label"], "CLUSTER_DOMINATED")
        self.assertTrue(audit["largest_high_state_month_cluster"]["dominated_by_cluster"])
        self.assertEqual(audit["largest_high_state_month_cluster"]["month"], "2026-01")
        self.assertAlmostEqual(audit["largest_high_state_month_cluster"]["share_of_high_state_mean"], 1.0, places=12)
        self.assertEqual(audit["high_state_calendar_counts"], {"2026-01": 2})

    def test_month_counts_and_baseline_fields_recorded(self):
        formations = [
            {"formation_date": "2026-01-10", "state": "high", "spread_net_1x": 0.5},
            {"formation_date": "2026-02-10", "state": "low", "spread_net_1x": -0.1},
            {"formation_date": "2026-02-20", "state": "mid", "spread_net_1x": 9.0},
        ]
        audit, block = self._run(formations)
        b = audit["baseline"]
        self.assertEqual(b["n_formations"], 3)
        self.assertEqual(b["n_high"], 1)
        self.assertEqual(b["n_low"], 1)
        self.assertEqual(b["n_mid"], 1)
        self.assertEqual(b["date_first"], "2026-01-10")
        self.assertEqual(b["date_last"], "2026-02-20")
        self.assertEqual(audit["last_high_state_formation_date"], "2026-01-10")
        # leave-one-out months include all calendar months present
        self.assertEqual(set(audit["calendar_month_leave_one_out"]["months"].keys()), {"2026-01", "2026-02"})


if __name__ == "__main__":
    unittest.main()
