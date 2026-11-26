"""Durable-state guard: the manifest's ``next_experiment_status`` narrative must
agree with the actual H10 fresh-block maturity and the registry H10 status.

``run_manifest.json`` carries a hand-written ``next_experiment_status`` string
that tells the next agent what the current pending experiment is and whether it
is mature. It is the same single-source-of-truth hazard class the repo has
systematically closed for the canonical-block sha256, the registry
``next_sequence_number``, the ``latest_verified_test_claim`` and the
``session_record_latest`` pointer: a narrative that can drift away from the
artifact it summarises while every structural check still passes.

Concretely, while the frozen H10 fresh block is IMMATURE (n_high == 0 or
n_low == 0 or ``high_low_diff_net_1x`` is null) the manifest must:

  * name H10 as the pending experiment;
  * label the state IMMATURE (it may not claim the block is confirmed/supported);
  * and the registry H10 status must not be promoted to
    ``SUPPORTED_FOR_FURTHER_RESEARCH``.

If a future session matures the block (n_high > 0 and n_low > 0 and a non-null
spread) the IMMATURE label is no longer required, so this guard does not block a
legitimate post-maturity update -- it only forbids the two contradictory states
(narrative claims maturity while the block is immature, or the registry promotes
an immature block).

Read-only, stdlib-only: parses local state JSON. No network, no artifact writes.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
H10_BLOCK = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"

# Tokens that would assert a decided/confirmed outcome. None may appear in the
# next_experiment_status narrative while the H10 block is immature.
CONFIRMED_TOKENS = ("CONFIRMED", "SUPPORTED", "REJECTED")


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _h10_is_immature(block):
    """True when the H10 fresh block cannot yet produce a high-minus-low spread.

    Mirrors the evaluator's own maturity rule: an overlap-aware interval (and any
    confirmatory claim) needs both states populated and a non-null spread.
    """
    return (
        block.get("n_high", 0) == 0
        or block.get("n_low", 0) == 0
        or block.get("high_low_diff_net_1x") is None
    )


class NextExperimentStatusConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = _load(STATE / "run_manifest.json")
        cls.registry = _load(STATE / "hypothesis_registry.json")
        cls.block = _load(H10_BLOCK)
        cls.status = cls.manifest.get("next_experiment_status")
        cls.h10 = next(
            (h for h in cls.registry["hypotheses"] if h["id"] == "H10"), None
        )

    def test_manifest_has_next_experiment_status(self):
        self.assertIsInstance(
            self.status, str, "run_manifest.json next_experiment_status missing"
        )
        self.assertTrue(self.status.strip(), "next_experiment_status is empty")

    def test_next_experiment_status_names_h10(self):
        """The pending experiment is H10 until it matures; the narrative must say so."""
        self.assertIn(
            "H10", self.status,
            f"next_experiment_status {self.status!r} does not name H10",
        )

    def test_registry_has_h10(self):
        self.assertIsNotNone(self.h10, "registry carries no H10 hypothesis")

    def test_next_experiment_status_matches_immature_block(self):
        """While the frozen H10 block is immature, the narrative must say IMMATURE
        and must not assert a confirmed/supported/rejected outcome."""
        if not _h10_is_immature(self.block):
            self.skipTest("H10 fresh block is mature; IMMATURE label not required")
        upper = self.status.upper()
        self.assertIn(
            "IMMATURE", upper,
            f"H10 block is immature (n_high={self.block.get('n_high')}, "
            f"n_low={self.block.get('n_low')}, "
            f"high_low_diff_net_1x={self.block.get('high_low_diff_net_1x')}) but "
            f"next_experiment_status {self.status!r} does not say IMMATURE",
        )
        for token in CONFIRMED_TOKENS:
            self.assertNotIn(
                token, upper,
                f"next_experiment_status {self.status!r} claims {token} while the "
                "H10 block is immature",
            )

    def test_registry_h10_not_promoted_while_block_immature(self):
        """An immature H10 block may never be promoted to a supported conclusion."""
        if not _h10_is_immature(self.block):
            self.skipTest("H10 fresh block is mature; promotion guard not required")
        self.assertNotEqual(
            self.h10["status"], "SUPPORTED_FOR_FURTHER_RESEARCH",
            "registry promotes H10 to SUPPORTED_FOR_FURTHER_RESEARCH while the "
            "frozen H10 fresh block is immature",
        )
        self.assertFalse(
            self.block.get("confirmatory_claim_allowed"),
            "H10 block carries confirmatory_claim_allowed=True while immature",
        )

    def test_status_and_block_maturity_do_not_contradict(self):
        """The narrative's IMMATURE label and the block's maturity must agree in
        both directions: an immature block forces the label, and a mature block
        (both states populated, non-null spread) must not be labelled IMMATURE."""
        immature = _h10_is_immature(self.block)
        labelled_immature = "IMMATURE" in self.status.upper()
        if immature:
            self.assertTrue(
                labelled_immature,
                f"immature H10 block but next_experiment_status {self.status!r} "
                "omits the IMMATURE label",
            )
        else:
            self.assertFalse(
                labelled_immature,
                f"mature H10 block but next_experiment_status {self.status!r} "
                "still says IMMATURE",
            )


if __name__ == "__main__":
    unittest.main()