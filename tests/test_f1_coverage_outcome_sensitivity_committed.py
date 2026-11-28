"""Committed-disk verdict pin for scripts/f1_coverage_outcome_sensitivity.py
(DISP-003-F1SENS-002).

The static suite (test_f1_coverage_outcome_sensitivity.py) re-derives arm A from
the frozen evaluator and checks the committed audit field-by-field against a
fresh run, but it never pins the committed artifact to an INDEPENDENT sha256
literal and has no synthetic-drift self-tests proving those field assertions are
real constraints. If the committed artifact were regenerated against a different
panel set, truncated, or silently edited, the static suite's recomputation-based
checks could in principle be re-satisfied by a coordinated rewrite; nothing pins
the artifact bytes themselves. This is the same single-source-of-truth hazard the
committed-disk pins for the placebo red-team (DISP-003-FORWARD-BLOCK-PLACEBO-001),
rolling-window (DISP-003-REGIME-002), tail-influence (DISP-003-TAILAUDIT-001),
state-representativeness (DISP-003-STATEAUDIT-001), maturity-timeline (H35),
independent-recomputation (H37), frozen-tree (H38), expanding-universe (H33),
point-in-time-eligibility (H57), final-integrity and H10-fresh-integrity audits
already close.

This module pins the committed artifact's sha256 to an independent literal and
pins every load-bearing field (audit_id, status, verdict, experiment_id,
hypothesis, offline flag, fidelity_check, the arm-A/arm-B primary contrast and
its per-state formation counts, the read-only frozen-block hashes, the
disposition flags, the estimand/notes qualifiers and the repaired-symbol roster)
to independent literals. It then proves the pins are real constraints via
synthetic-drift self-tests: a tampered copy (flipped verdict, perturbed arm-B
estimate, flipped old-panels flag, zeroed frozen-hash match, mutated disposition,
dropped repaired symbol, stripped estimand qualifier) must NOT satisfy the pins.
The full evaluate() recomputation is intentionally NOT re-run here (it is
covered by the static suite's fidelity test); this module is a fast,
deterministic committed-bytes pin. Read-only; path constants are derived from
``__file__`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / NEW_EXP
    / "integrity_audit"
    / "f1_coverage_outcome_sensitivity_20261113T025950Z.json"
)
CANONICAL = ROOT / "artifacts" / OLD_EXP / "forward_block" / "forward_block_evaluation.json"
H10_FRESH = (
    ROOT
    / "artifacts"
    / OLD_EXP
    / "forward_block_h10_fresh"
    / "forward_block_evaluation.json"
)

# Independent copy of the committed F1 sensitivity artifact's sha256 so a
# coordinated change to the artifact still fails even if a module constant were
# edited.
EXPECTED_AUDIT_SHA256 = (
    "7f85b38698745da5bf3e618bd729d59fd21c88da44b1a9795f93d20e5f639fa3"
)
# Independent copies of the two frozen block hashes the audit reads and pins.
EXPECTED_CANONICAL_SHA256 = (
    "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
)
EXPECTED_H10_FRESH_SHA256 = (
    "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
)

REPAIRED_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]
FROZEN_RELS = (
    "forward_block/forward_block_evaluation.json",
    "forward_block_h10_fresh/forward_block_evaluation.json",
)


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _assert_pins(audit: dict) -> None:
    """Assert every load-bearing pin on an F1 sensitivity artifact dict.

    Factored out so the synthetic-drift self-tests can prove that a tampered
    copy fails these same assertions.
    """
    assert audit["audit_id"] == "DISP-003-F1SENS-002"
    assert audit["audit_type"] == "COVERAGE_OUTCOME_SENSITIVITY"
    assert audit["status"] == "EXPLORATORY_ONLY"
    assert audit["verdict"] == "PASS"
    assert audit["experiment_id"] == NEW_EXP
    assert audit["hypothesis"] == "H24"
    assert audit["offline"] is True

    fid = audit["fidelity_check"]
    assert fid["pass"] is True
    hl = fid["fields"]["high_low_diff_net_1x"]
    assert hl["match"] is True
    assert abs(hl["actual"] - 0.6165223953929935) < 1e-12
    assert abs(hl["expected"] - 0.6165223953929935) < 1e-12

    pc = audit["primary_contrast"]
    assert abs(pc["arm_a_high_low_diff_net_1x"] - 0.6165223953929935) < 1e-12
    assert abs(pc["arm_b_high_low_diff_net_1x"] - 0.5397762360511249) < 1e-12
    assert abs(pc["delta_b_minus_a"] - (-0.07674615934186857)) < 1e-12
    assert pc["n_formations_a"] == 608
    assert pc["n_formations_b"] == 608
    assert pc["n_high_a"] == 61
    assert pc["n_high_b"] == 49
    assert pc["n_low_a"] == 90
    assert pc["n_low_b"] == 126

    ro = audit["read_only_checks"]
    assert ro["old_panels_byte_unchanged"] is True
    frozen = ro["frozen_artifacts"]
    assert set(frozen) == set(FROZEN_RELS)
    for rel, expected in zip(FROZEN_RELS, (EXPECTED_CANONICAL_SHA256, EXPECTED_H10_FRESH_SHA256)):
        entry = frozen[rel]
        assert entry["match"] is True, rel
        assert entry["actual"] == expected, rel
        assert entry["expected"] == expected, rel

    disp = audit["disposition"]
    assert disp["frozen_artifacts_modified"] is False
    assert disp["old_panels_modified"] is False
    assert disp["outcomes_computed"] is True
    assert "EXPLORATORY_ONLY" in disp["note"]
    assert "not independent confirmation" in disp["note"]

    assert audit["inputs"]["repaired_symbols"] == REPAIRED_SYMBOLS
    assert audit["inputs"]["min_assets_deciles"] == 20
    assert abs(audit["inputs"]["cost_1x"] - 0.001) < 1e-15
    assert audit["inputs"]["block_start"] == "2025-01-01"
    assert audit["inputs"]["data_cutoff_utc"] == "2026-09-30T00:00:00Z"

    estimand = audit["estimand"]
    assert "descriptive sensitivity" in estimand
    assert "no p-value" in estimand
    assert "no promotion" in estimand

    notes = audit["notes"]
    assert len(notes) == 4
    assert any("fidelity_check" in n for n in notes)
    assert any("Arm B substitutes only the four F1-repaired" in n for n in notes)
    assert any("byte-verified unchanged" in n for n in notes)


class CommittedF1SensitivityVerdictPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [
            str(p) for p in (COMMITTED_AUDIT, CANONICAL, H10_FRESH) if not p.exists()
        ]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.committed = _load(COMMITTED_AUDIT)

    def test_committed_artifact_sha256_pinned(self):
        # Pin the committed artifact bytes to an independent literal so a
        # regenerated or edited artifact is caught even if every field-level
        # assertion were also updated.
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_AUDIT_SHA256)

    def test_frozen_canonical_block_sha256_pinned(self):
        # The sensitivity audit reads the sealed canonical block; pin its sha256
        # to an independent literal so a swapped block is caught.
        self.assertEqual(_sha256(CANONICAL), EXPECTED_CANONICAL_SHA256)

    def test_frozen_h10_fresh_block_sha256_pinned(self):
        # The audit also reads and byte-verifies the H10 fresh block; pin it too.
        self.assertEqual(_sha256(H10_FRESH), EXPECTED_H10_FRESH_SHA256)

    def test_committed_artifact_satisfies_all_pins(self):
        _assert_pins(self.committed)

    def test_synthetic_drift_is_detected(self):
        # Each tampered copy must violate at least one pin, proving the pins are
        # real constraints rather than rubber stamps.

        # 1. Flipped verdict.
        t = json.loads(json.dumps(self.committed))
        t["verdict"] = "FAIL"
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 2. Perturbed arm-B estimate.
        t = json.loads(json.dumps(self.committed))
        t["primary_contrast"]["arm_b_high_low_diff_net_1x"] = 0.5
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 3. Flipped old-panels-byte-unchanged flag.
        t = json.loads(json.dumps(self.committed))
        t["read_only_checks"]["old_panels_byte_unchanged"] = False
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 4. Zeroed frozen-hash match on the canonical block.
        t = json.loads(json.dumps(self.committed))
        t["read_only_checks"]["frozen_artifacts"][
            "forward_block/forward_block_evaluation.json"
        ]["match"] = False
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 5. Mutated disposition (claims frozen artifacts were modified).
        t = json.loads(json.dumps(self.committed))
        t["disposition"]["frozen_artifacts_modified"] = True
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 6. Dropped repaired symbol.
        t = json.loads(json.dumps(self.committed))
        t["inputs"]["repaired_symbols"] = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT"]
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 7. Estimand stripped of its "no promotion" qualifier.
        t = json.loads(json.dumps(self.committed))
        t["estimand"] = "descriptive sensitivity of the frozen H004V106 anchor"
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 8. Mutated per-state high count in the primary contrast.
        t = json.loads(json.dumps(self.committed))
        t["primary_contrast"]["n_high_b"] = 50
        with self.assertRaises(AssertionError):
            _assert_pins(t)


if __name__ == "__main__":
    unittest.main()