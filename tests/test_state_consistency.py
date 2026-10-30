"""Durable state-consistency checks for research-state control files.

Each session previously re-verified by hand that research_state JSON files
parse cleanly and agree with one another and with the committed frozen
artifacts. This test file makes that check repeatable and fails the build
when state drifts (for example after a handoff rewrite or an artifact touch).

It only reads local files: no network, no secrets, no trading endpoints.
"""
import json
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
ART = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"

STATE_FILES = [
    STATE / "universe_frontier.json",
    STATE / "hypothesis_registry.json",
    STATE / "run_manifest.json",
]
ARTIFACT_FILES = [
        ART / "grid_summary.json",
        ART / "forward_block" / "forward_block_evaluation.json",
        ART / "integrity_audit" / "forward_block_integrity_audit.json",
        ART / "integrity_audit" / "forward_block_independent_recomputation_20261025.json",
        ART / "integrity_audit" / "forward_block_independent_recomputation_20261028.json",
        ART / "integrity_audit" / "forward_block_hac_addendum_20261024.json",
        ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json",
        ART / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json",
        ART / "integrity_audit" / "H004V106_rolling_dispersion_window_20261028.json",
        ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json",
        ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json",
        ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json",
]

# Every integrity audit committed under DISPERSION-003's integrity_audit/
# directory. The original list only asserted on the first five; the later
# audits (tail influence, temporal stability, cluster bootstrap, regime
# conditioning, the 2028-10-28 independent recomputation) were therefore
# outside the durable state-consistency gate. All ten now assert here so a
# future audit drift (missing file, unparseable JSON, missing identifier or
# audited_artifact field) fails the build.
INTEGRITY_AUDITS = [
    ART / "integrity_audit" / "forward_block_integrity_audit.json",
    ART / "integrity_audit" / "forward_block_hac_addendum_20261024.json",
    ART / "integrity_audit" / "forward_block_independent_recomputation_20261028.json",
    ART / "integrity_audit" / "forward_block_independent_recomputation_20261025.json",
    ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json",
    ART / "integrity_audit" / "H004V106_dispersion_regime_conditioning_20261028.json",
    ART / "integrity_audit" / "H004V106_rolling_dispersion_window_20261028.json",
    ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json",
    ART / "integrity_audit" / "H004V106_forward_block_tail_influence_20261029.json",
    ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json",
]


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _float_values(obj):
    """Recursively yield every JSON float in a nested dict/list/scalar structure."""
    if isinstance(obj, float):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _float_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _float_values(v)


class ResearchStateConsistencyTests(unittest.TestCase):
    def test_state_and_artifact_files_parse_cleanly(self):
        for path in STATE_FILES + ARTIFACT_FILES:
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), f"missing state/artifact file: {path}")
                _load(path)

    def test_program_id_agrees_across_state_files(self):
        frontier = _load(STATE / "universe_frontier.json")
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        for label, obj in (("frontier", frontier), ("registry", registry), ("manifest", manifest)):
            with self.subTest(file=label):
                self.assertEqual(obj["program_id"], "HARMONY-CRYPTO-EDGE-004")

    def test_program_statuses_are_active(self):
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        frontier = _load(STATE / "universe_frontier.json")
        self.assertEqual(registry["program_status"], "ACTIVE")
        self.assertEqual(manifest["program_status"], "ACTIVE_CONTINUOUS_RESEARCH")
        self.assertEqual(frontier["status"], "ACTIVE_INCOMPLETE")

    def test_registry_sequence_matches_registered_hypotheses(self):
        registry = _load(STATE / "hypothesis_registry.json")
        # next_sequence_number tracks the highest registered hypothesis id
        # (registry comment: H1..H8 present with next_sequence_number 8).
        ids = [h["id"] for h in registry["hypotheses"]]
        self.assertEqual(ids, [f"H{i}" for i in range(1, registry["next_sequence_number"] + 1)])

    def test_h1_immutable_and_grid_complete_unrejected(self):
        registry = _load(STATE / "hypothesis_registry.json")
        grid = _load(ART / "grid_summary.json")
        h1 = next(h for h in registry["hypotheses"] if h["id"] == "H1")
        self.assertTrue(h1["immutable"])
        self.assertEqual(h1["status"], "NOT_SUPPORTED_AS_ROBUST_EDGE")
        self.assertEqual(grid["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
        self.assertEqual(grid["cells_ok"], grid["expected_cells"])
        self.assertEqual(grid["cells_ok"], 216)
        self.assertEqual(grid["cells_evaluated"], 216)
        self.assertEqual(grid["cells_blocked"], 0)
        self.assertEqual(grid["cells_failed"], 0)
        self.assertEqual(grid["holm_rejected_count"], 0)

    def test_grid_anchor_and_forward_block_cutoff_are_consistent(self):
        grid = _load(ART / "grid_summary.json")
        block = _load(ART / "forward_block" / "forward_block_evaluation.json")
        anchor = grid["primary_anchor_expanding_H004V106"]
        self.assertEqual(anchor["config_id"], "H004V106")
        self.assertEqual(anchor["date_first"], "2023-01-31")
        self.assertEqual(anchor["date_last"], "2026-09-29")
        self.assertEqual(block["anchor_id"], "H004V106")
        self.assertEqual(block["n_formations"], 608)
        self.assertEqual(block["data_cutoff_utc"][:10], "2026-09-30")
        self.assertEqual(block["date_last"][:10], "2026-08-31")
        self.assertAlmostEqual(block["high_low_diff_net_1x"], 0.6165223953929935, places=12)
        self.assertTrue(block.get("block_sealed"))

    def test_all_integrity_audits_present_and_parse(self):
        # Every committed integrity audit must be present, parse, carry an
        # audit identifier, name the artifact it audited and declare a
        # conclusion. The full set of ten is asserted here (the earlier
        # version only covered five, leaving tail-influence, temporal
        # stability, cluster bootstrap, regime conditioning and the 2028
        # recomputation outside the gate).
        audits = INTEGRITY_AUDITS
        self.assertEqual(len(audits), 10)
        for path in audits:
            with self.subTest(path=str(path)):
                self.assertTrue(path.exists(), f"missing integrity audit: {path}")
                audit = _load(path)
                identifier = audit.get("audit_id") or audit.get("addendum_id")
                self.assertIsNotNone(identifier, f"{path} has no audit identifier")
                self.assertIn("audited_artifact", audit)
                self.assertIn("conclusion", audit)

    def test_frontier_records_no_new_discovery_and_incomplete_rank_coverage(self):
        frontier = _load(STATE / "universe_frontier.json")
        self.assertEqual(frontier["candidates_discovered"], [])
        self.assertEqual(frontier["historical_rank_coverage_state"], "NOT_PROVEN_COMPLETE")
        self.assertEqual(frontier["expanding_universe_target_met"], True)
        self.assertEqual(frontier["rank_frontier_exhausted"], False)
        self.assertIsNone(frontier["last_verified_historical_rank"])
        self.assertIn("no fixed top-N cutoff", frontier["rank_policy"])
        self.assertGreater(frontier["next_candidate_batch_size"], 0)

    def test_defective_archive_remains_quarantined(self):
        archive = ART / "archive_defective_momentum_20261024" / "forward_block_evaluation.json"
        self.assertTrue(archive.exists())
        block = _load(archive)
        self.assertIsNone(block.get("block_sealing_rule"))
        self.assertIsNone(block.get("last_allowed_formation_date"))

    def test_audit_conclusions_match_registry_evidence_notes(self):
        """Each integrity audit's declared operative label must agree with
        the label recorded in the H8/H9 evidence notes of the hypothesis
        registry, so the two cannot drift apart (for example an audit
        relabelled after the fact while the registry keeps the old label).

        Labels are substring assertions, not equality: audit conclusions are
        free-form prose and the operative label sometimes lives in a JSON
        key rather than the conclusion string, so the serialized audit is
        searched rather than the conclusion alone.
        """
        registry = _load(STATE / "hypothesis_registry.json")
        manifest = _load(STATE / "run_manifest.json")
        grid = _load(ART / "grid_summary.json")
        # Collect every evidence note and every dated addendum across the
        # registry, manifest and grid summary: the operative labels for
        # REGIME-001/002 live in addenda dated 20261028, not in the base
        # evidence_note or the 20261029 addendum, and the manifest records
        # them under next_required_actions rather than the registry notes.
        notes = " ".join(
            str(h.get(field, ""))
            for h in registry["hypotheses"]
            for field in ("evidence_note",) + tuple(
                k for k in h.keys() if k.startswith("evidence_note_addendum_")
            )
        ) + " " + json.dumps(manifest) + " " + json.dumps(grid)

        expected = {
            "H004V106_state_representativeness_audit_20261025.json": "CLUSTER_DOMINATED",
            "H004V106_forward_block_tail_influence_20261029.json": "TAIL_ROBUST",
            "H004V106_forward_block_temporal_stability_20261029.json": "not temporally stable",
            "H004V106_rolling_dispersion_window_20261028.json": "ROLLING_FRAGILE",
            "H004V106_dispersion_regime_conditioning_20261028.json": "WEAK_CONTINUOUS_ASSOCIATION",
        }
        for filename, needle in expected.items():
            audit = _load(ART / "integrity_audit" / filename)
            with self.subTest(audit=filename):
                self.assertIn(needle, json.dumps(audit))
                self.assertIn(needle, notes)

        # Cluster bootstrap: the operative finding is the CI spanning zero,
        # recorded in the audit both as ci_includes_zero=true and in prose, and
        # in the registry as "cluster bootstrap CI includes zero".
        bootstrap = _load(ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json")
        with self.subTest(audit="cluster_bootstrap"):
            self.assertTrue(bootstrap["ci_includes_zero"])
            self.assertIn("EXPLORATORY_ONLY", bootstrap["conclusion"])
            self.assertIn("includes zero", notes)
            self.assertIn("EXPLORATORY_ONLY", notes)

    def test_all_audits_target_the_canonical_forward_block(self):
        """Every integrity audit must audit the canonical sealed block and
        carry the canonical anchor estimate, so no audit silently drifted
        onto a different artifact or a different block vintage.

        The baseline is recorded under different key names across audits
        (baseline_high_low_diff_net_1x, high_low_diff_net_recomputed,
        diff_high_low_net, high_low_diff_net, the 'baseline' sub-object),
        so the canonical value is matched as a float anywhere in the
        serialized audit rather than under one fixed key.
        """
        block = _load(ART / "forward_block" / "forward_block_evaluation.json")
        canonical = block["high_low_diff_net_1x"]
        for path in INTEGRITY_AUDITS:
            audit = _load(path)
            with self.subTest(path=str(path)):
                self.assertEqual(
                    audit["audited_artifact"],
                    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
                )
                # The canonical anchor value must appear in the audit. Key names
                # differ across audits (baseline_high_low_diff_net_1x,
                # high_low_diff_net_recomputed, diff_high_low_net,
                # high_low_diff_net, the 'baseline' sub-object), so the check
                # scans all serialized floats rather than one fixed key. A tight
                # absolute tolerance accepts 1-ULP float-repr differences between
                # computation paths while still flagging any real drift onto a
                # different anchor value or block vintage.
                audit_floats = list(_float_values(audit))
                self.assertTrue(
                    any(math.isclose(v, canonical, rel_tol=0.0, abs_tol=1e-9)
                        for v in audit_floats),
                    f"canonical anchor {canonical:.16f} not found among audit floats "
                    f"in {path}",
                )


if __name__ == "__main__":
    unittest.main()
