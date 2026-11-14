"""Hermetic unit tests for scripts/formation_accounting.py.

Covers deterministic/pure seams of the DISPERSION-001 Phase A/B accounting:
``sha256_file``, ``formation_dates`` (fixed monthly UTC phase) and ``momentum``
(complete-observation trailing compounded return).

No network access, no dependency on committed panel artifacts, no frozen
artifact or config modification. Synthetic fixtures are software tests only,
never market evidence.
"""

from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "formation_accounting.py"

try:
    import pandas as pd
except Exception:  # dep-light: whole module is skipped without pandas
    pd = None

_HAS_PANDAS = pd is not None


def _load():
    spec = importlib.util.spec_from_file_location("formation_accounting_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(_HAS_PANDAS, "pandas not installed (dep-light env)")
class FormationAccountingConstantsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_experiment_id(self):
        self.assertEqual(self.mod.EXP, "HARMONY-CRYPTO-EDGE-004-DISPERSION-001")

    def test_anchor_parameters(self):
        self.assertEqual(self.mod.MOMENTUM_LOOKBACK, 30)
        self.assertEqual(self.mod.FORWARD_HORIZON, 30)
        self.assertEqual(self.mod.BREAKPOINTS, "deciles")

    def test_base_cost_turn_is_frozen(self):
        self.assertEqual(self.mod.BASE_COST_TURN, 0.0005)


class Sha256FileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_sha256_file_matches_hashlib(self):
        payload = b"formation-accounting-test-payload\n"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sample.bin"
            p.write_bytes(payload)
            got = self.mod.sha256_file(p)
        self.assertEqual(got, hashlib.sha256(payload).hexdigest())

    def test_sha256_file_deterministic(self):
        payload = b"deterministic"
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.txt"
            p.write_bytes(payload)
            h1 = self.mod.sha256_file(p)
            h2 = self.mod.sha256_file(p)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


@unittest.skipUnless(_HAS_PANDAS, "pandas not installed (dep-light env)")
class FormationDatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def _univ(self, dates, elig):
        return pd.DataFrame({
            "date": dates,
            "eligible": elig,
            "asset_id": ["x"] * len(dates),
        })

    def test_first_eligible_date_each_month(self):
        univ = self._univ(
            ["2023-01-01", "2023-01-15", "2023-02-01", "2023-02-20", "2023-03-05", "2023-03-10"],
            [True, False, True, True, False, True],
        )
        # prices frame is unused by formation_dates; pass an empty stub.
        got = self.mod.formation_dates(pd.DataFrame(), univ)
        self.assertEqual(got, ["2023-01-01", "2023-02-01", "2023-03-10"])

    def test_ignores_ineligible_dates(self):
        univ = self._univ(
            ["2023-01-05", "2023-01-06", "2023-02-06"],
            [False, False, True],
        )
        got = self.mod.formation_dates(pd.DataFrame(), univ)
        self.assertEqual(got, ["2023-02-06"])

    def test_output_is_sorted_and_non_overlapping(self):
        univ = self._univ(
            ["2023-03-10", "2023-01-01", "2023-02-01", "2023-03-01"],
            [True, True, True, True],
        )
        got = self.mod.formation_dates(pd.DataFrame(), univ)
        self.assertEqual(got, ["2023-01-01", "2023-02-01", "2023-03-01"])
        months = [d[:7] for d in got]
        self.assertEqual(len(months), len(set(months)))

    def test_no_eligible_dates_returns_empty(self):
        univ = self._univ(["2023-01-01", "2023-02-01"], [False, False])
        got = self.mod.formation_dates(pd.DataFrame(), univ)
        self.assertEqual(got, [])


@unittest.skipUnless(_HAS_PANDAS, "pandas not installed (dep-light env)")
class MomentumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def _returns(self):
        idx = ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
        return pd.DataFrame(
            {
                "a": [0.01, 0.02, 0.03, 0.04, 0.05],
                "b": [0.05, 0.04, 0.03, 0.02, 0.01],
            },
            index=idx,
        )

    def test_compounds_trailing_window(self):
        got = self.mod.momentum(self._returns(), "2023-01-05", 3, ["a", "b"])
        self.assertAlmostEqual(got["a"], 1.03 * 1.04 * 1.05 - 1.0, places=12)
        self.assertAlmostEqual(got["b"], 1.03 * 1.02 * 1.01 - 1.0, places=12)

    def test_end_date_absent_returns_empty(self):
        got = self.mod.momentum(self._returns(), "2023-02-01", 3, ["a"])
        self.assertEqual(len(got), 0)

    def test_window_longer_than_history_returns_empty(self):
        got = self.mod.momentum(self._returns(), "2023-01-05", 10, ["a"])
        self.assertEqual(len(got), 0)

    def test_incomplete_asset_is_excluded(self):
        r = self._returns()
        r.loc["2023-01-04", "b"] = float("nan")
        got = self.mod.momentum(r, "2023-01-05", 3, ["a", "b"])
        self.assertEqual(list(got.index), ["a"])
        self.assertAlmostEqual(got["a"], 1.03 * 1.04 * 1.05 - 1.0, places=12)

    def test_all_assets_incomplete_returns_empty(self):
        r = self._returns()
        r.loc["2023-01-04", "b"] = float("nan")
        got = self.mod.momentum(r, "2023-01-05", 3, ["b"])
        self.assertEqual(len(got), 0)


if __name__ == "__main__":
    unittest.main()