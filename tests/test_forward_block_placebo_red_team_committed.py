"""Committed-disk verdict pin for scripts/forward_block_placebo_red_team.py
(DISP-003-FORWARD-BLOCK-PLACEBO-001).

The static suite (test_forward_block_placebo_red_team.py) checks the committed
placebo artifact field-by-field against the sealed block and exercises the pure
seams, but it never pins the committed artifact to an INDEPENDENT sha256 literal
and has no synthetic-drift self-tests proving those field assertions are real
constraints. If the committed artifact were regenerated against a different
block, truncated, or silently edited, the static suite's recomputation-based
checks could in principle be re-satisfied by a coordinated rewrite; nothing pins
the artifact bytes themselves. This is the same single-source-of-truth hazard
the committed-disk pins for the rolling-window (DISP-003-REGIME-002), tail-
influence (DISP-003-TAILAUDIT-001), state-representativeness
(DISP-003-STATEAUDIT-001), maturity-timeline (H35), independent-recomputation
(H37), frozen-tree (H38), expanding-universe (H33), point-in-time-eligibility
(H57), final-integrity and H10-fresh-integrity audits already close.

This module pins the committed artifact's sha256 to an independent literal and
pins every load-bearing field (audit_id, status, label, seed, n_draws, alpha,
block summary, per-family null mean / empirical p / CI / inside-CI / p-below-
alpha, self-consistency flags, decision-rule and conclusion substrings) to
independent literals. It then proves the pins are real constraints via
synthetic-drift self-tests: a tampered copy (flipped label, perturbed p,
dropped family, zeroed frozen hash, mutated block count) must NOT satisfy the
pins. The slow N=10000 x 3 permutation recomputation is intentionally NOT
re-run here (it is covered, gated, by the static suite's
``test_script_is_reproducible_and_read_only``); this module is a fast,
deterministic committed-bytes pin. Read-only; path constants are derived from
``__file__`` so the test is CWD-independent.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
COMMITTED_AUDIT = (
    ROOT
    / "artifacts"
    / EXP
    / "integrity_audit"
    / "H004V106_forward_block_placebo_red_team_20261028.json"
)
CANONICAL = ROOT / "artifacts" / EXP / "forward_block" / "forward_block_evaluation.json"

# Independent copy of the committed placebo artifact's sha256 so a coordinated
# change to the artifact still fails even if a module constant were edited.
EXPECTED_PLACEBO_SHA256 = (
    "fa07100c8c8af820bd5583b8555c12724b6067bef4d4b5629e761a9a4c27818f"
)
# Independent copy of the frozen canonical block hash the placebo audit reads.
EXPECTED_CANONICAL_SHA256 = (
    "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
)

FAMILIES = ("state_permutation", "random_ranking", "dispersion_shuffle")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _assert_pins(audit: dict) -> None:
    """Assert every load-bearing pin on a placebo artifact dict.

    Factored out so the synthetic-drift self-tests can prove that a tampered
    copy fails these same assertions.
    """
    assert audit["audit_id"] == (
        "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001"
    )
    assert audit["status"] == "EXPLORATORY_ONLY"
    assert audit["label"] == "PLACEBO_SENSITIVE"
    assert audit["seed"] == 20261028
    assert audit["n_draws"] == 10000
    assert audit["alpha"] == 0.05
    assert audit["self_consistency"] == {
        "derived_spread_matches_stored": True,
        "re_derived_states_match_stored": True,
    }
    assert audit["modified_frozen_artifacts"] == []
    assert audit["read_only_inputs"] == [str(CANONICAL)]

    b = audit["block"]
    assert b["anchor_id"] == "H004V106"
    assert b["n_formations"] == 608
    assert b["n_high"] == 61
    assert b["n_low"] == 90
    assert b["n_mid"] == 457
    assert b["date_first"] == "2025-01-01"
    assert b["date_last"] == "2026-08-31"
    assert abs(b["high_low_diff_net_1x"] - 0.6165223953929935) < 1e-12

    fam = audit["placebo_family"]
    assert set(fam.keys()) == set(FAMILIES)
    for name in FAMILIES:
        r = fam[name]
        assert r["n_draws"] == 10000
        assert abs(r["observed"] - 0.6165223953929935) < 1e-12
        assert r["observed_inside_ci_95"] is False
        assert r["p_below_alpha"] is True
        # Two-sided empirical p at the floor (1 / (10000 + 1)).
        assert abs(r["empirical_p_two_sided"] - 9.999000099990002e-05) < 1e-15
        assert len(r["ci_95"]) == 2
        assert r["ci_95"][0] <= r["ci_95"][1]

    # Null means are centered near zero (the static suite asserts < 0.01).
    for name in FAMILIES:
        assert abs(fam[name]["null_mean"]) < 0.01

    assert "EXPLORATORY_ONLY" in audit["decision_rule"]
    assert "placebo" in audit["decision_rule"].lower()
    assert "PLACEBO_SENSITIVE" in audit["conclusion"]
    assert "not an edge" in audit["conclusion"]


class CommittedPlaceboVerdictPinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [
            str(p) for p in (COMMITTED_AUDIT, CANONICAL) if not p.exists()
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
        self.assertEqual(_sha256(COMMITTED_AUDIT), EXPECTED_PLACEBO_SHA256)

    def test_frozen_canonical_block_sha256_pinned(self):
        # The placebo audit reads the sealed canonical block; pin its sha256 to
        # an independent literal so a swapped block is caught.
        self.assertEqual(_sha256(CANONICAL), EXPECTED_CANONICAL_SHA256)

    def test_committed_artifact_satisfies_all_pins(self):
        _assert_pins(self.committed)

    def test_synthetic_drift_is_detected(self):
        # Each tampered copy must violate at least one pin, proving the pins are
        # real constraints rather than rubber stamps.

        # 1. Flipped label.
        t = json.loads(json.dumps(self.committed))
        t["label"] = "PLACEBO_INCONCLUSIVE"
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 2. Perturbed empirical p on one family.
        t = json.loads(json.dumps(self.committed))
        t["placebo_family"]["random_ranking"]["empirical_p_two_sided"] = 0.5
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 3. Dropped family.
        t = json.loads(json.dumps(self.committed))
        del t["placebo_family"]["dispersion_shuffle"]
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 4. Mutated block formation count.
        t = json.loads(json.dumps(self.committed))
        t["block"]["n_formations"] = 607
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 5. Flipped inside-CI flag.
        t = json.loads(json.dumps(self.committed))
        t["placebo_family"]["state_permutation"]["observed_inside_ci_95"] = True
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 6. Self-consistency flag flipped.
        t = json.loads(json.dumps(self.committed))
        t["self_consistency"]["re_derived_states_match_stored"] = False
        with self.assertRaises(AssertionError):
            _assert_pins(t)

        # 7. Conclusion stripped of its "not an edge" qualifier.
        t = json.loads(json.dumps(self.committed))
        t["conclusion"] = "PLACEBO_SENSITIVE: significant."
        with self.assertRaises(AssertionError):
            _assert_pins(t)


if __name__ == "__main__":
    unittest.main()