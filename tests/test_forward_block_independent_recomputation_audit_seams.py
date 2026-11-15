"""Hermetic seam tests for scripts/forward_block_independent_recomputation_audit.py.

Exercises every pure seam (sha256_file, load_json, check_equal, check_close,
median, _is_finite, recompute_from_formations) and the full audit function
against synthetic fixtures, with no network access and no reads of committed
artifacts beyond the module import.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "forward_block_independent_recomputation_audit.py"

spec = importlib.util.spec_from_file_location("forward_block_recompute_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _formation(state="mid", net=0.0, gross=0.01, dispersion=0.1, n_assets=27,
               formation_date="2025-01-01"):
    return {
        "dispersion": dispersion,
        "formation_date": formation_date,
        "n_assets": n_assets,
        "spread_gross": gross,
        "spread_net_1x": net,
        "state": state,
    }


def _compliant_block(formations):
    return {
        "anchor_id": "H004V106",
        "block_sealed": True,
        "data_cutoff_utc": "2026-09-30T00:00:00Z",
        "date_last": "2026-08-31",
        "formations": formations,
    }


def _compliant_addendum(recomputed, n_formations=608):
    return {
        "audited_artifact": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        "n_formations": n_formations,
        "state_counts": recomputed["state_counts"],
        "finite_checks": recomputed["finite_checks"],
        "metrics": recomputed["metrics"],
        "reference_values": {
            "high_low_diff_net_1x": recomputed["metrics"]["high_low_diff_net"],
            "spread_net_mean": recomputed["metrics"]["spread_net_mean"],
            "spread_net_median": recomputed["metrics"]["spread_net_median"],
        },
    }


def _write_fixture(td, block=None, addendum=None):
    block = block if block is not None else _compliant_block([])
    addendum = addendum if addendum is not None else _compliant_addendum(
        mod.recompute_from_formations(block["formations"]))
    canonical = Path(td) / "canonical.json"
    addendum_path = Path(td) / "addendum.json"
    canonical.write_text(json.dumps(block))
    addendum_path.write_text(json.dumps(addendum))
    return {
        "CANONICAL_BLOCK_PATH": canonical,
        "ADDENDUM_PATH": addendum_path,
        "CANONICAL_SHA256": mod.sha256_file(canonical),
    }


class HelperSeamTests(unittest.TestCase):
    def test_check_equal_pass_and_fail(self):
        results = []
        mod.check_equal("a", 1, 1, results)
        mod.check_equal("b", 1, 2, results)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])

    def test_check_close_pass_and_fail(self):
        results = []
        mod.check_close("x", 1.0, 1.0 + 1e-10, 1e-9, results)
        mod.check_close("y", 1.0, 1.0 + 1e-8, 1e-9, results)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])
        self.assertLessEqual(results[0]["abs_diff"], results[0]["tolerance"])
        self.assertGreater(results[1]["abs_diff"], results[1]["tolerance"])

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.bin"
            payload = b"recompute-audit"
            p.write_bytes(payload)
            self.assertEqual(mod.sha256_file(p), hashlib.sha256(payload).hexdigest())

    def test_load_json(self):
        with tempfile.TemporaryDirectory() as td:
            jp = Path(td) / "d.json"
            jp.write_text(json.dumps({"k": [1, 2]}))
            self.assertEqual(mod.load_json(jp), {"k": [1, 2]})

    def test_is_finite(self):
        self.assertTrue(mod._is_finite(1.0))
        self.assertTrue(mod._is_finite(0.0))
        self.assertFalse(mod._is_finite(float("inf")))
        self.assertFalse(mod._is_finite(float("-inf")))
        self.assertFalse(mod._is_finite(float("nan")))

    def test_median(self):
        self.assertEqual(mod.median([1, 2, 3]), 2)
        self.assertEqual(mod.median([1, 2, 3, 4]), 2.5)


class RecomputeFromFormationsTests(unittest.TestCase):
    def test_empty_formations(self):
        out = mod.recompute_from_formations([])
        self.assertEqual(out["n_formations"], 0)
        self.assertEqual(out["state_counts"], {"high": 0, "mid": 0, "low": 0})
        self.assertEqual(out["metrics"]["spread_net_mean"], 0.0)
        self.assertFalse(out["finite_checks"]["any_non_finite"])

    def test_state_counts_and_means(self):
        formations = [
            _formation(state="high", net=0.5, gross=0.51),
            _formation(state="low", net=-0.1, gross=-0.09),
            _formation(state="mid", net=0.0, gross=0.01),
        ]
        out = mod.recompute_from_formations(formations)
        self.assertEqual(out["n_formations"], 3)
        self.assertEqual(out["state_counts"], {"high": 1, "mid": 1, "low": 1})
        self.assertAlmostEqual(out["metrics"]["high_net_mean"], 0.5)
        self.assertAlmostEqual(out["metrics"]["low_net_mean"], -0.1)
        self.assertAlmostEqual(out["metrics"]["high_low_diff_net"], 0.6)
        self.assertAlmostEqual(out["metrics"]["high_low_diff_gross"], 0.6)

    def test_spread_net_mean_median(self):
        formations = [_formation(net=float(i)) for i in range(5)]
        out = mod.recompute_from_formations(formations)
        self.assertAlmostEqual(out["metrics"]["spread_net_mean"], 2.0)
        self.assertAlmostEqual(out["metrics"]["spread_net_median"], 2.0)

    def test_non_finite_flag(self):
        formations = [_formation(net=float("inf"))]
        out = mod.recompute_from_formations(formations)
        self.assertTrue(out["finite_checks"]["any_non_finite"])
        self.assertFalse(out["finite_checks"]["all_spread_net_finite"])


class AuditFunctionSeamTests(unittest.TestCase):
    def test_audit_passes_on_compliant_fixture(self):
        block = _compliant_block([
            _formation(state="high", net=0.5, gross=0.51),
            _formation(state="low", net=-0.1, gross=-0.09),
            _formation(state="mid", net=0.0, gross=0.01),
        ])
        recomputed = mod.recompute_from_formations(block["formations"])
        addendum = _compliant_addendum(recomputed, n_formations=3)
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, block, addendum)):
                res = mod.audit_forward_block_independent_recomputation()
            self.assertEqual(res["verdict"], "PASS")
            self.assertEqual(res["checks_failed"], 0)
            self.assertEqual(res["hypothesis_id"], "H37")
            self.assertEqual(res["status"], "EXPLORATORY_ONLY")

    def test_audit_fails_on_state_counts_mismatch(self):
        block = _compliant_block([
            _formation(state="high", net=0.5, gross=0.51),
            _formation(state="low", net=-0.1, gross=-0.09),
        ])
        recomputed = mod.recompute_from_formations(block["formations"])
        addendum = _compliant_addendum(recomputed, n_formations=2)
        addendum["state_counts"] = {"high": 2, "mid": 0, "low": 0}
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, block, addendum)):
                res = mod.audit_forward_block_independent_recomputation()
            self.assertEqual(res["verdict"], "FAIL")
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("state_counts_exact", failed)

    def test_audit_fails_on_metric_beyond_tolerance(self):
        block = _compliant_block([
            _formation(state="high", net=0.5, gross=0.51),
            _formation(state="low", net=-0.1, gross=-0.09),
        ])
        recomputed = mod.recompute_from_formations(block["formations"])
        addendum = _compliant_addendum(recomputed, n_formations=2)
        addendum["metrics"]["high_net_mean"] = 999.0
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, block, addendum)):
                res = mod.audit_forward_block_independent_recomputation()
            self.assertEqual(res["verdict"], "FAIL")
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("high_net_mean", failed)

    def test_main_writes_artifact_and_returns_pass_exit(self):
        block = _compliant_block([
            _formation(state="high", net=0.5, gross=0.51),
            _formation(state="low", net=-0.1, gross=-0.09),
        ])
        recomputed = mod.recompute_from_formations(block["formations"])
        addendum = _compliant_addendum(recomputed, n_formations=2)
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch.multiple(mod, **self._write_fixture(td, block, addendum)), \
                    patch.object(mod, "OUT_DIR", td_path / "integrity_audit"), \
                    patch.object(mod, "CANONICAL_BLOCK_PATH",
                                 td_path / "canonical.json"), \
                    patch.object(mod, "ADDENDUM_PATH", td_path / "addendum.json"), \
                    patch.object(mod, "CANONICAL_SHA256",
                                 mod.sha256_file(td_path / "canonical.json")):
                rc = mod.main()
            self.assertEqual(rc, 0)
            written = list((td_path / "integrity_audit").glob("*.json"))
            self.assertEqual(len(written), 1)
            data = json.loads(written[0].read_text())
            self.assertEqual(data["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main()
