"""Hermetic regression tests for the pure/deterministic seams of
``scripts/audit_f1_grid_execution_state.py`` (DISP-003-F1GRID-001 execution-state
audit).

The module had no direct test reference before this file. These tests exercise
only pure functions and constants: ``cell_partition``, ``max_date``,
``tail_formation_contrast``, ``drift_summary``, ``sha256_file`` and the
``FROZEN_HASHES`` map. They import the module (which imports the read-only run
script for its ``fidelity_check``) but never call ``audit()``, never read a
committed artifact, never touch the network and never write into the repository.
Synthetic dicts/Series are software fixtures, never market evidence.
"""

import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import audit_f1_grid_execution_state as audit  # noqa: E402


class CellPartitionTests(unittest.TestCase):
    def test_counts_each_status(self):
        cells = {
            "a": {"status": "OK"},
            "b": {"status": "OK"},
            "c": {"status": "BLOCKED"},
            "d": {"status": "FAILED"},
        }
        self.assertEqual(
            audit.cell_partition(cells),
            {"cells": 4, "ok": 2, "blocked": 1, "failed": 1},
        )

    def test_empty_partition_is_all_zero(self):
        self.assertEqual(
            audit.cell_partition({}),
            {"cells": 0, "ok": 0, "blocked": 0, "failed": 0},
        )

    def test_unknown_and_missing_status_do_not_count(self):
        cells = {"a": {"status": "INVALID"}, "b": {}, "c": {"status": "OK"}}
        part = audit.cell_partition(cells)
        self.assertEqual(part["cells"], 3)
        self.assertEqual(part["ok"], 1)
        self.assertEqual(part["blocked"], 0)
        self.assertEqual(part["failed"], 0)


class MaxDateTests(unittest.TestCase):
    def test_returns_lexical_max_iso_prefix(self):
        series = pd.Series(
            ["2026-09-30T00:00:00Z", "2026-10-31T00:00:00Z", "2026-01-01T00:00:00Z"]
        )
        self.assertEqual(audit.max_date(series), "2026-10-31")

    def test_drops_na_and_empty(self):
        self.assertIsNone(audit.max_date(pd.Series([], dtype="object")))
        self.assertIsNone(
            audit.max_date(pd.Series([None, float("nan")], dtype="object"))
        )

    def test_slices_to_ten_chars(self):
        series = pd.Series(["2026-10-31 23:59:59+00:00"])
        self.assertEqual(audit.max_date(series), "2026-10-31")


class TailFormationContrastTests(unittest.TestCase):
    def test_empty_when_either_side_missing(self):
        ledger = {"H004V002": {"formations": [{"formation_date": "2026-08-31"}]}}
        self.assertEqual(audit.tail_formation_contrast({}, ledger), {})
        self.assertEqual(
            audit.tail_formation_contrast({"H004V002": {"formations": []}}, ledger),
            {},
        )

    def test_contrasts_last_ledger_formation(self):
        arm_a = {
            "H004V002": {
                "formations": [
                    {"formation_date": "2026-07-31", "spread_gross": 0.20, "n_assets": 29},
                    {"formation_date": "2026-08-31", "spread_gross": 0.10, "n_assets": 30},
                ]
            }
        }
        ledger = {
            "H004V002": {
                "formations": [
                    {"formation_date": "2026-08-31", "spread_gross": 0.15, "n_assets": 31},
                ]
            }
        }
        out = audit.tail_formation_contrast(arm_a, ledger)
        self.assertEqual(out["config_id"], "H004V002")
        self.assertEqual(out["formation_date"], "2026-08-31")
        self.assertEqual(out["ledger_spread_gross"], 0.15)
        self.assertEqual(out["arm_a_spread_gross"], 0.10)
        self.assertEqual(out["ledger_n_assets"], 31)
        self.assertEqual(out["arm_a_n_assets"], 30)
        self.assertIn("different forward window", out["note"])

    def test_arm_a_row_absent_yields_none_values(self):
        ledger = {
            "H004V002": {
                "formations": [
                    {"formation_date": "2026-08-31", "spread_gross": 0.15, "n_assets": 31},
                ]
            }
        }
        arm_a = {
            "H004V002": {
                "formations": [
                    {"formation_date": "2026-07-31", "spread_gross": 0.20, "n_assets": 29},
                ]
            }
        }
        out = audit.tail_formation_contrast(arm_a, ledger)
        self.assertIsNone(out["arm_a_spread_gross"])
        self.assertIsNone(out["arm_a_n_assets"])


class DriftSummaryTests(unittest.TestCase):
    def test_counts_differences_over_intersection(self):
        fidelity = {
            "passed": True,
            "drift_count": 1,
            "compared_cells": 2,
            "drifted": ["A"],
        }
        arm_a = {
            "A": {"date_last": "d1", "n_formations": 1, "high_low_diff_net_1x": 0.1},
            "B": {"date_last": "d2", "n_formations": 2, "high_low_diff_net_1x": 0.5},
        }
        ledger = {
            "A": {"date_last": "dX", "n_formations": 1, "high_low_diff_net_1x": 0.2},
            "B": {"date_last": "d2", "n_formations": 3, "high_low_diff_net_1x": 0.4},
        }
        out = audit.drift_summary(fidelity, arm_a, ledger)
        self.assertEqual(out["cells_with_different_date_last"], 1)
        self.assertEqual(out["cells_with_different_n_formations"], 1)
        self.assertAlmostEqual(out["max_abs_delta_high_low_diff_net_1x"], 0.1)
        self.assertTrue(out["fidelity_passed"])
        self.assertEqual(out["drift_count"], 1)
        self.assertEqual(out["compared_cells"], 2)
        self.assertEqual(out["sample_drifts"], ["A"])

    def test_no_float_pairs_yields_none_delta(self):
        fidelity = {
            "passed": False,
            "drift_count": 0,
            "compared_cells": 0,
            "drifted": [],
        }
        arm_a = {"A": {"date_last": "d1"}}
        ledger = {"A": {"date_last": "d2"}}
        out = audit.drift_summary(fidelity, arm_a, ledger)
        self.assertIsNone(out["max_abs_delta_high_low_diff_net_1x"])
        self.assertEqual(out["cells_with_different_date_last"], 1)

    def test_sample_drifts_truncated_to_ten(self):
        fidelity = {
            "passed": False,
            "drift_count": 12,
            "compared_cells": 12,
            "drifted": [f"c{i}" for i in range(12)],
        }
        out = audit.drift_summary(fidelity, {}, {})
        self.assertEqual(len(out["sample_drifts"]), 10)
        self.assertEqual(out["sample_drifts"][0], "c0")
        self.assertEqual(out["sample_drifts"][-1], "c9")


class Sha256FileTests(unittest.TestCase):
    def test_missing_returns_none(self):
        self.assertIsNone(audit.sha256_file(Path("/nonexistent/does-not-exist")))

    def test_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.bin"
            payload = b"audit-fixture-bytes"
            path.write_bytes(payload)
            self.assertEqual(
                audit.sha256_file(path), hashlib.sha256(payload).hexdigest()
            )


class ConstantTests(unittest.TestCase):
    def test_frozen_hashes_pin_canonical_and_h10_fresh(self):
        self.assertEqual(
            audit.FROZEN_HASHES["forward_block/forward_block_evaluation.json"],
            "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
        )
        self.assertEqual(
            audit.FROZEN_HASHES["forward_block_h10_fresh/forward_block_evaluation.json"],
            "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
        )


class NowUtcTests(unittest.TestCase):
    def test_iso_z_format(self):
        self.assertRegex(
            audit.now_utc(), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        )


if __name__ == "__main__":
    unittest.main()