"""Regression tests for the H004V106 forward block placebo red team audit
(scripts/forward_block_placebo_red_team.py).

The preregistration
(artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106
Forward Block Placebo Red Team v1.md, sec 6) commits to a regression test in this
file. The audit is read-only: it consumes only the sealed canonical forward block
and writes a single new artifact under integrity_audit/. The sealed block itself
must never be modified.

All audits here are EXPLORATORY_ONLY development evidence on the frozen
canonical block (a strict subset of the grid ledger's development window that
was already inspected); none promotes H1/H6/H7 or unlocks the confirmatory
track.
"""

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT = ART / "integrity_audit" / "H004V106_forward_block_placebo_red_team_20261028.json"
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"
PLACEBO = ROOT / "scripts" / "forward_block_placebo_red_team.py"

FAMILIES = ("state_permutation", "random_ranking", "dispersion_shuffle")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ForwardBlockPlaceboRedTeamTests(unittest.TestCase):
    def test_audit_artifact_exists_and_parses(self):
        self.assertTrue(AUDIT.exists(), f"missing audit artifact: {AUDIT}")
        audit = _load(AUDIT)
        self.assertEqual(
            audit["audit_id"],
            "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001",
        )
        self.assertEqual(audit["status"], "EXPLORATORY_ONLY")
        self.assertIn("EXPLORATORY_ONLY", audit["decision_rule"])
        self.assertIn("placebo", audit["decision_rule"].lower())

    def test_audit_targets_the_canonical_sealed_block(self):
        audit = _load(AUDIT)
        self.assertEqual(
            audit["audited_artifact"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        )
        # The audit must not have modified the audited block: the on-disk
        # canonical blob must still match the committed blob.
        canonical = hashlib.sha256(
            subprocess.run(
                ["git", "show", "HEAD:artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json"],
                cwd=ROOT, capture_output=True,
            ).stdout
        ).hexdigest()
        self.assertEqual(hashlib.sha256(CANONICAL.read_bytes()).hexdigest(), canonical)

    def test_placebo_family_is_complete_and_predeclared(self):
        audit = _load(AUDIT)
        self.assertEqual(set(audit["placebo_family"].keys()), set(FAMILIES))
        for name in FAMILIES:
            r = audit["placebo_family"][name]
            self.assertEqual(r["n_draws"], 10000)
            self.assertGreater(r["n_draws"], 0)
            self.assertLessEqual(r["n_draws"], 10000)
            self.assertAlmostEqual(r["observed"], 0.6165223953929935, places=12)
            self.assertTrue(all(
                key in r for key in (
                    "null_mean", "null_std", "empirical_p_two_sided",
                    "ci_95", "observed_inside_ci_95", "p_below_alpha",
                )
            ))
            self.assertEqual(len(r["ci_95"]), 2)
            self.assertLessEqual(r["ci_95"][0], r["ci_95"][1])
            self.assertIsInstance(r["observed_inside_ci_95"], bool)
            self.assertIsInstance(r["p_below_alpha"], bool)

    def test_all_three_families_reject_the_null(self):
        audit = _load(AUDIT)
        for name in FAMILIES:
            r = audit["placebo_family"][name]
            self.assertTrue(r["p_below_alpha"], msg=f"{name} p not below alpha")
            self.assertFalse(r["observed_inside_ci_95"], msg=f"{name} observed inside CI")
        self.assertEqual(audit["label"], "PLACEBO_SENSITIVE")

    def test_null_means_are_centered_near_zero(self):
        audit = _load(AUDIT)
        for name in FAMILIES:
            r = audit["placebo_family"][name]
            self.assertLess(abs(r["null_mean"]), 0.01,
                            msg=f"{name} null mean not centered near zero")

    def test_self_consistency_checks_passed(self):
        audit = _load(AUDIT)
        sc = audit["self_consistency"]
        self.assertTrue(sc["derived_spread_matches_stored"])
        self.assertTrue(sc["re_derived_states_match_stored"])

    def test_block_summary_matches_sealed_block(self):
        block = _load(CANONICAL)
        audit = _load(AUDIT)
        b = audit["block"]
        self.assertEqual(b["anchor_id"], block["anchor_id"])
        self.assertEqual(b["n_formations"], block["n_formations"])
        self.assertEqual(b["n_formations"], 608)
        self.assertEqual(b["n_high"], 61)
        self.assertEqual(b["n_low"], 90)
        self.assertEqual(b["n_mid"], 457)
        self.assertEqual(b["date_first"], "2025-01-01")
        self.assertEqual(b["date_last"], "2026-08-31")
        self.assertAlmostEqual(b["high_low_diff_net_1x"], 0.6165223953929935, places=12)

    def test_no_frozen_artifact_was_modified(self):
        audit = _load(AUDIT)
        self.assertEqual(audit["modified_frozen_artifacts"], [])
        # The audit records its single read-only input by absolute path; the
        # canonical sealed block it points to must be the on-disk artifact.
        self.assertEqual(
            audit["read_only_inputs"], [str(CANONICAL)],
        )

    def test_script_is_reproducible_and_read_only(self):
        # Re-running the audit script must reproduce the same artifact and must
        # not modify the sealed canonical block. The permutation loop is
        # N=10000 x 3 families (~2 min), so this check is gated behind the
        # RUN_SLOW_PLACEBO=1 environment variable and is excluded from the
        # default discovery run.
        import os
        if os.environ.get("RUN_SLOW_PLACEBO") != "1":
            raise unittest.SkipTest(
                "slow reproducibility check (N=10000 x 3 permutation families); "
                "set RUN_SLOW_PLACEBO=1 to run it"
            )
        audit = _load(AUDIT)
        before = CANONICAL.read_bytes()
        r = subprocess.run(
            ["python", str(PLACEBO)], cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(CANONICAL.read_bytes(), before)
        reloaded = _load(AUDIT)
        self.assertEqual(reloaded["label"], "PLACEBO_SENSITIVE")
        for name in FAMILIES:
            self.assertAlmostEqual(
                reloaded["placebo_family"][name]["observed"],
                audit["placebo_family"][name]["observed"], places=12,
            )


if __name__ == "__main__":
    unittest.main()