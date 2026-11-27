"""Committed-disk verdict pin for scripts/h10_fresh_block_prereg_compliance_audit.py (H34).

The hermetic seam suite (test_h10_fresh_block_prereg_compliance_audit_seams.py)
exercises the audit only against synthetic fixtures. This module pins the audit's
PASS verdict against the REAL committed artifacts on disk, so the confirmatory
decision rules that the 2026-11-30 Option A execution depends on cannot silently
drift:

  - the committed H10 fresh block still encodes the preregistered confirmatory
    gate CLOSED (economic_significance_threshold 0.05 but
    economic_significance_met False, min_state_formations 5 but
    state_count_floor_met False, n_high=0 / n_low=0, high_low_diff_net_1x null,
    confirmatory_claim_allowed False);
  - the sequential alpha-spending fields are still k=1 / alpha_k=0.025 /
    consumes_budget False / mature False;
  - the four frozen artifact hashes still match the values the audit quotes;
  - the committed H34 audit artifact on disk still agrees with a fresh
    recomputation (same verdict, same 40-check name set, same fresh-block sha).

Read-only: no network, no writes. stdlib-only (the audit module imports no
numpy/pandas), so it runs in the dep-light environment too. Path constants are
re-anchored to the repository root in setUpClass so the test is CWD-independent.
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
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
INTEGRITY_AUDIT_DIR = ART / "integrity_audit"

spec = importlib.util.spec_from_file_location("h10_precomp_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Frozen hash literals the audit is expected to quote (kept here as an independent
# copy so a change to the module constants alone cannot satisfy this test).
EXPECTED_CANONICAL = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"


def _reanchor_paths() -> None:
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    mod.ARTIFACT_DIR = ART
    mod.FRESH_BLOCK_PATH = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
    mod.PREREG_PATH = ART / "preregistrations" / "H10_FRESH_FORWARD_BLOCK_v1.md"
    mod.CANONICAL_BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
    mod.GRID_LEDGER_PATH = ART / "grid_result_ledger.json"
    mod.UNIVERSE_FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"


def _committed_audit_artifact() -> Path:
    matches = sorted(INTEGRITY_AUDIT_DIR.glob(
        "H004V106_H10_fresh_forward_block_prereg_compliance_audit_*.json"
    ))
    return matches[-1] if matches else Path("/nonexistent")


class CommittedPreregComplianceVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _reanchor_paths()
        required = [
            mod.FRESH_BLOCK_PATH,
            mod.PREREG_PATH,
            mod.CANONICAL_BLOCK_PATH,
            mod.GRID_LEDGER_PATH,
            mod.UNIVERSE_FRONTIER_PATH,
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.result = mod.audit_fresh_block_prereg_compliance()
        cls.fresh_block = mod.load_json(mod.FRESH_BLOCK_PATH)

    def test_verdict_is_pass_with_all_checks(self):
        res = self.result
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["checks_failed"], 0)
        self.assertEqual(res["checks_passed"], res["checks_total"])
        self.assertGreaterEqual(res["checks_total"], 40)

    def test_hypothesis_and_status_labels(self):
        res = self.result
        self.assertEqual(res["hypothesis_id"], "H34")
        self.assertEqual(res["status"], "EXPLORATORY_ONLY")
        self.assertEqual(
            res["audit_id"],
            "H004V106_H10_FRESH_FORWARD_BLOCK_PREREG_COMPLIANCE_AUDIT",
        )

    def test_fresh_block_is_immature(self):
        # The confirmatory gate must be CLOSED: a single mid formation, no
        # high/low states, no estimable high-minus-low spread.
        fb = self.fresh_block
        self.assertEqual(fb["n_formations"], 1)
        self.assertEqual(fb["n_high"], 0)
        self.assertEqual(fb["n_low"], 0)
        self.assertEqual(fb["n_mid"], 1)
        self.assertIsNone(fb["high_low_diff_net_1x"])

    def test_confirmatory_gate_fields_closed(self):
        fb = self.fresh_block
        self.assertEqual(fb["economic_significance_threshold"], 0.05)
        self.assertFalse(fb["economic_significance_met"])
        self.assertFalse(fb["state_count_floor_met"])
        self.assertEqual(fb["min_state_formations"], 5)
        self.assertFalse(fb["confirmatory_claim_allowed"])
        self.assertIsNone(fb["confirmatory_holm_significant"])
        # Sequential alpha-spending: k=1 look, alpha_1=0.025, immature -> no budget.
        self.assertEqual(fb["sequential_look_number"], 1)
        self.assertEqual(fb["sequential_alpha_k"], 0.025)
        self.assertFalse(fb["sequential_look_consumes_budget"])
        self.assertFalse(fb["sequential_look_mature"])
        self.assertEqual(
            fb["overlap_aware_uncertainty"]["status"], "IMMATURE"
        )

    def test_frozen_hashes_match_committed_artifacts(self):
        # Independent literals vs disk bytes.
        self.assertEqual(mod.sha256_file(mod.CANONICAL_BLOCK_PATH), EXPECTED_CANONICAL)
        self.assertEqual(mod.sha256_file(mod.FRESH_BLOCK_PATH), EXPECTED_FRESH)
        self.assertEqual(mod.sha256_file(mod.GRID_LEDGER_PATH), EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.sha256_file(mod.UNIVERSE_FRONTIER_PATH), EXPECTED_FRONTIER)

        # And confirm the audit's own quoted constants agree with those literals.
        self.assertEqual(mod.EXPECTED_CANONICAL_SHA256, EXPECTED_CANONICAL)
        self.assertEqual(mod.EXPECTED_FRESH_BLOCK_SHA256, EXPECTED_FRESH)
        self.assertEqual(mod.EXPECTED_GRID_LEDGER_SHA256, EXPECTED_GRID_LEDGER)
        self.assertEqual(mod.EXPECTED_FRONTIER_SHA256, EXPECTED_FRONTIER)

    def test_committed_artifact_matches_recomputation(self):
        # The committed H34 audit artifact on disk must not silently drift from a
        # fresh recomputation against the same committed inputs.
        art_path = _committed_audit_artifact()
        self.assertTrue(
            art_path.exists(),
            "no committed H34 prereg-compliance audit artifact on disk",
        )
        committed = json.loads(art_path.read_text())
        self.assertEqual(committed["verdict"], "PASS")
        self.assertEqual(committed["checks_failed"], 0)
        self.assertEqual(committed["checks_passed"], committed["checks_total"])
        self.assertEqual(committed["hypothesis_id"], "H34")

        # Same check-name set as the fresh recomputation (no check added/removed).
        committed_names = [c["check"] for c in committed["checks"]]
        recomputed_names = [c["check"] for c in self.result["checks"]]
        self.assertEqual(committed_names, recomputed_names)

        # The committed artifact's recorded fresh-block sha and prereg sha must
        # equal what the current code computes from the committed bytes.
        self.assertEqual(committed["artifact_sha256"], EXPECTED_FRESH)
        self.assertEqual(
            committed["preregistration_sha256"],
            self.result["preregistration_sha256"],
        )

    def test_drift_self_test_detects_real_artifact_mutation(self):
        # Mutate the REAL committed fresh block bytes (a copy) and require the
        # audit to FAIL on the economic-significance gate, proving this pin
        # actually detects drift in the committed artifact rather than only in a
        # synthetic fixture.
        bad = dict(self.fresh_block)
        bad["economic_significance_threshold"] = 0.06
        with tempfile.TemporaryDirectory() as td:
            bad_path = Path(td) / "fresh.json"
            bad_path.write_text(json.dumps(bad))
            with patch.multiple(
                mod,
                FRESH_BLOCK_PATH=bad_path,
                EXPECTED_FRESH_BLOCK_SHA256=mod.sha256_file(bad_path),
            ):
                res = mod.audit_fresh_block_prereg_compliance()
            self.assertEqual(res["verdict"], "FAIL")
            failed = {c["check"] for c in res["checks"] if not c["passed"]}
            self.assertIn("economic_significance_threshold", failed)


if __name__ == "__main__":
    unittest.main()