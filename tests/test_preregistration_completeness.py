"""Registry-completeness gate for every DISP-003 diagnostic audit.

Every committed integrity audit under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/ must have a
corresponding hypothesis entry in research_state/hypothesis_registry.json.

This is the durable-state gate that was missing when the following audits were
committed with a preregistration, a script and a regression test, but no
registry entry -- i.e. committed evidence with no registered hypothesis, the
same single-source-of-truth hazard class repaired for H11 (the consolidated
final integrity audit) and H12 (the H10 structural feasibility analysis):

  * H004V106_FORWARD_BLOCK_PLACEBO_RED_TEAM_001
    (H004V106_forward_block_placebo_red_team_20261028.json,
     preregistrations/H004V106 Forward Block Placebo Red Team v1.md,
     scripts/forward_block_placebo_red_team.py,
     tests/test_forward_block_placebo_red_team.py)

  * H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102 (H11)
  * DISP-003-H10-FEASIBILITY-001 (H12)
  * DISP-003-SOURCECOV-001 (H28) -- the source-coverage gap audit naming the 24
    Binance-perpetual assets that lack Coin Metrics market-cap data and are
    therefore structurally unrankable. Its artifact
    source_coverage_gap_binance_no_capmkt_20261114.json was committed before
    its preregistration existed; the retroactive prereg
    (preregistrations/SOURCE_COVERAGE_GAP_AUDIT_v1.md) carries an explicit
    correction note and is dated after the artifact's generated_utc, and
    scripts/repair_source_coverage_audit_prereg.py re-verifies the recorded
    findings against the source data before adding the missing fields.

The mapping is audit_id -> expected hypothesis id. A future audit committed
without a registry entry fails the build instead of silently drifting.

Only local files are read: no network, no secrets, no trading endpoints.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"

# audit_id (as carried in the artifact) -> hypothesis id that must exist in
# the registry. Audits without a separate preregistered experiment id (the
# HAC addendum and the two independent recomputations are addenda to the
# 2026-10-24 integrity audit) are deliberately excluded.
AUDIT_TO_HYPOTHESIS = {
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001": "H13",
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FINAL-INTEGRITY-AUDIT": "H11",
    "DISP-003-H10-FEASIBILITY-001": "H12",
    "DISP-003-SOURCECOV-001": "H28",
    "H004V106_DISPERSION_REGIME_CONDITIONING_20261028": "H14",
    "H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_20261029": "H15",
    "H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102": "H16",
    "H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102": "H17",
    "H004V106_FORWARD_BLOCK_TAIL_INFLUENCE_AUDIT_20261029": "H18",
    "H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_20261029": "H19",
    "H004V106_ROLLING_DISPERSION_WINDOW_20261028": "H20",
    "H004V106_STATE_REPRESENTATIVENESS_AUDIT_20261025": "H21",
}


class PreregistrationCompletenessTests(unittest.TestCase):
    def test_every_registered_audit_has_a_hypothesis_entry(self):
        registry = json.loads((STATE / "hypothesis_registry.json").read_text())
        ids = {h["id"] for h in registry["hypotheses"]}
        for audit_id, hyp_id in AUDIT_TO_HYPOTHESIS.items():
            with self.subTest(audit=audit_id):
                self.assertIn(
                    hyp_id, ids,
                    f"audit {audit_id} has no hypothesis entry in the registry "
                    f"(expected {hyp_id}); the durable state is internally "
                    f"inconsistent -- register the hypothesis before shipping "
                    f"the audit, the same way H11 and H12 were repaired.",
                )

    def test_every_committed_audit_is_registered_or_excluded(self):
        """The converse: every audit file under integrity_audit/ must either be
        covered by AUDIT_TO_HYPOTHESIS or be an addendum to the 2026-10-24
        integrity audit (which has no separate experiment id). A new audit
        silently falling outside both buckets is the defect this guard exists
        to catch, so the set is pinned explicitly rather than derived."""
        registry = json.loads((STATE / "hypothesis_registry.json").read_text())
        ids = {h["id"] for h in registry["hypotheses"]}
        audit_dir = ART / "integrity_audit"
        addenda = {
            "forward_block_hac_addendum_20261024.json",
            "forward_block_independent_recomputation_20261025.json",
            "forward_block_independent_recomputation_20261028.json",
            "forward_block_integrity_audit.json",
        }
        for path in sorted(audit_dir.glob("*.json")):
            with self.subTest(audit=path.name):
                audit = json.loads(path.read_text())
                audit_id = audit.get("audit_id") or audit.get("addendum_id") \
                    or audit.get("artifact_id")
                if path.name in addenda:
                    # addenda to the 2026-10-24 integrity audit; no separate
                    # experiment id, so they are not hypotheses in their own
                    # right and must not be expected in the registry.
                    self.assertIsNone(
                        audit_id,
                        f"{path.name} is an addendum but carries an id "
                        f"{audit_id}; if it is a standalone audit it needs a "
                        f"registry entry",
                    )
                    continue
                self.assertIsNotNone(
                    audit_id,
                    f"{path.name} carries no audit_id/addendum_id/artifact_id",
                )
                self.assertIn(
                    audit_id, AUDIT_TO_HYPOTHESIS,
                    f"{path.name} ({audit_id}) is neither a registered audit "
                    f"nor a declared addendum; add it to AUDIT_TO_HYPOTHESIS "
                    f"or addenda and register the hypothesis",
                )
                self.assertIn(AUDIT_TO_HYPOTHESIS[audit_id], ids)

    def test_registered_hypothesis_names_its_experiment_id(self):
        """Each hypothesis allocated for a diagnostic audit must quote the
        audit's own experiment id, so the registry entry and the artifact
        cannot drift apart."""
        registry = json.loads((STATE / "hypothesis_registry.json").read_text())
        for h in registry["hypotheses"]:
            with self.subTest(hyp=h["id"]):
                eid = h.get("experiment_id")
                if eid is None:
                    continue
                for audit_id, hyp_id in AUDIT_TO_HYPOTHESIS.items():
                    if h["id"] == hyp_id:
                        self.assertEqual(
                            eid, audit_id,
                            f"{hyp_id} experiment_id {eid} does not match the "
                            f"audit's audit_id {audit_id}",
                        )


if __name__ == "__main__":
    unittest.main()