"""Hermetic seam tests for scripts/h10_fresh_block_prereg_compliance_audit.py.

Exercises every pure seam (check_equal, check_in_text, sha256_file, load_json,
load_text) and the full audit function against synthetic fixtures, with no
network access and no reads of committed artifacts beyond the module import.
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
SPEC_PATH = ROOT / "scripts" / "h10_fresh_block_prereg_compliance_audit.py"

spec = importlib.util.spec_from_file_location("h10_precomp_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _compliant_block():
    return {
        "economic_significance_threshold": 0.05,
        "economic_significance_met": False,
        "high_low_diff_net_1x_abs": None,
        "formations": [{"spread_gross": -0.047729065266337745,
                        "spread_net_1x": -0.048729065266337745}],
        "min_state_formations": 5,
        "state_count_floor_met": False,
        "n_high": 0,
        "n_low": 0,
        "confirmatory_claim_allowed": False,
        "confirmatory_holm_significant": None,
        "confirmatory_note": (
            "gate: |high_low_diff_net_1x|=None >= 0.05 -> False; "
            "n_high=0>= 5 and n_low=0>=5 -> False; Holm-significance across "
            "the complete 216-cell family at alpha_k = 0.025 -> None. A "
            "confirmatory claim requires all three True and is never promoted "
            "from raw p-values or return alone."
        ),
        "sequential_alpha_rule": "alpha_k = 0.05 / (k * (k + 1))",
        "sequential_family_alpha": 0.05,
        "sequential_look_number": 1,
        "sequential_alpha_k": 0.025,
        "sequential_cumulative_spend": 0.025,
        "sequential_remaining_budget": 0.025,
        "sequential_look_consumes_budget": False,
        "sequential_look_mature": False,
        "sequential_look_note": (
            "look k=1 at alpha_k=0.025 (family alpha 0.05); IMMATURE "
            "(n_high=0 or n_low=0): consumes no budget, do NOT advance k"
        ),
        "block_sealed": True,
        "block_sealing_rule": (
            "formations with formation_date > 2026-09-30 excluded because "
            "their 30-day forward horizon is not completed by the data cutoff "
            "2026-10-31; no truncated outcomes are computed"
        ),
        "n_formations": 1,
        "n_mid": 1,
        "high_low_diff_net_1x": None,
        "overlap_aware_uncertainty": {
            "status": "IMMATURE",
            "reason": "need n_high>0 and n_low>0 for overlap-aware interval",
            "n_boot": 0,
            "n_clusters_with_both_states": 0,
            "n_months": 0,
        },
    }


class HelperSeamTests(unittest.TestCase):
    def test_check_equal_pass_and_fail(self):
        results = []
        mod.check_equal("a", 1, 1, results)
        mod.check_equal("b", 1, 2, results)
        self.assertTrue(results[0]["passed"])
        self.assertFalse(results[1]["passed"])
        self.assertEqual(results[0]["expected"], 1)
        self.assertEqual(results[1]["actual"], 2)

    def test_check_in_text_pass_and_fail(self):
        results = []
        mod.check_in_text("x", "needle", "a needle here", results)
        mod.check_in_text("y", "absent", "a needle here", results)
        self.assertTrue(results[0]["passed"])
        self.assertEqual(results[0]["actual"], "found")
        self.assertFalse(results[1]["passed"])
        self.assertEqual(results[1]["actual"], "not found")

    def test_sha256_file_matches_hashlib(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "f.bin"
            payload = b"compliance-audit"
            p.write_bytes(payload)
            self.assertEqual(mod.sha256_file(p),
                             hashlib.sha256(payload).hexdigest())

    def test_load_json_and_text(self):
        with tempfile.TemporaryDirectory() as td:
            jp = Path(td) / "d.json"
            jp.write_text(json.dumps({"k": [1, 2]}))
            tp = Path(td) / "t.md"
            tp.write_text("hello")
            self.assertEqual(mod.load_json(jp), {"k": [1, 2]})
            self.assertEqual(mod.load_text(tp), "hello")


class AuditFunctionSeamTests(unittest.TestCase):
    def _write_fixture(self, td, block=None):
        block = block if block is not None else _compliant_block()
        fresh = Path(td) / "fresh.json"
        prereg = Path(td) / "prereg.md"
        canonical = Path(td) / "canonical.json"
        ledger = Path(td) / "ledger.json"
        frontier = Path(td) / "frontier.json"
        fresh.write_text(json.dumps(block))
        prereg.write_text("prereg text")
        for p in (canonical, ledger, frontier):
            p.write_text("{}")
        return {
            "FRESH_BLOCK_PATH": fresh,
            "PREREG_PATH": prereg,
            "CANONICAL_BLOCK_PATH": canonical,
            "GRID_LEDGER_PATH": ledger,
            "UNIVERSE_FRONTIER_PATH": frontier,
            "EXPECTED_FRESH_BLOCK_SHA256": mod.sha256_file(fresh),
            "EXPECTED_CANONICAL_SHA256": mod.sha256_file(canonical),
            "EXPECTED_GRID_LEDGER_SHA256": mod.sha256_file(ledger),
            "EXPECTED_FRONTIER_SHA256": mod.sha256_file(frontier),
        }

    def test_audit_passes_on_compliant_fixture(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td)):
                res = mod.audit_fresh_block_prereg_compliance()
            self.assertEqual(res["verdict"], "PASS")
            self.assertEqual(res["checks_failed"], 0)
            self.assertEqual(res["checks_passed"], res["checks_total"])
            self.assertEqual(res["hypothesis_id"], "H34")

    def test_audit_fails_on_deviating_fixture(self):
        bad = _compliant_block()
        bad["sequential_alpha_k"] = 0.05  # violates alpha_1 = 0.025
        bad["n_high"] = 1
        with tempfile.TemporaryDirectory() as td:
            with patch.multiple(mod, **self._write_fixture(td, bad)):
                res = mod.audit_fresh_block_prereg_compliance()
            self.assertEqual(res["verdict"], "FAIL")
            self.assertGreater(res["checks_failed"], 0)
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("sequential_alpha_k", failed)
            self.assertIn("n_high_is_zero", failed)

    def test_main_writes_artifact_and_returns_pass_exit(self):
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch.multiple(mod, **self._write_fixture(td)), \
                    patch.object(mod, "ARTIFACT_DIR", td_path):
                rc = mod.main()
            self.assertEqual(rc, 0)
            written = list((td_path / "integrity_audit").glob("*.json"))
            self.assertEqual(len(written), 1)
            data = json.loads(written[0].read_text())
            self.assertEqual(data["verdict"], "PASS")

    def test_main_returns_nonzero_on_fail(self):
        bad = _compliant_block()
        bad["block_sealed"] = False
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            with patch.multiple(mod, **self._write_fixture(td, bad)), \
                    patch.object(mod, "ARTIFACT_DIR", td_path):
                rc = mod.main()
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()