import hashlib
import importlib.util
import itertools
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_grid_v3.json"
FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
REGISTRY_PATH = ROOT / "research_state" / "hypothesis_registry.json"
PROMPT_PATH = ROOT / "prompts" / "continuous_research_operating_contract_v1.md"
SCRIPT_PATH = ROOT / "scripts" / "generate_grid_v3_manifest.py"

spec = importlib.util.spec_from_file_location("grid_v3", SCRIPT_PATH)
grid_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grid_v3)


class ContinuousResearchContractTests(unittest.TestCase):
    def test_grid_has_exactly_216_cells(self):
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        axes = {item["name"]: item["values"] for item in config["axes"]}
        combinations = list(itertools.product(*(axes[name] for name in config["enumeration"]["axis_order"])))
        self.assertEqual(config["expected_combinations"], 216)
        self.assertEqual(len(combinations), 216)

    def test_manifest_is_deterministic_and_anchor_ids_match(self):
        first = grid_v3.build_manifest(CONFIG_PATH)
        second = grid_v3.build_manifest(CONFIG_PATH)
        self.assertEqual(first, second)
        rows = first["configurations"]
        self.assertEqual(len(rows), 216)
        self.assertEqual([row["config_id"] for row in rows], [f"H004V{i:03d}" for i in range(1, 217)])
        self.assertEqual(len({row["config_sha256"] for row in rows}), 216)
        self.assertEqual(rows[104]["parameters"]["universe_arm"], "legacy28_comparator")
        self.assertEqual(rows[105]["parameters"]["universe_arm"], "expanding_point_in_time")

    def test_every_cell_hash_matches_canonical_json(self):
        manifest = grid_v3.build_manifest(CONFIG_PATH)
        for row in manifest["configurations"]:
            canonical = json.dumps(row["parameters"], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            self.assertEqual(row["canonical_config_json"], canonical)
            self.assertEqual(row["config_sha256"], hashlib.sha256(canonical.encode("utf-8")).hexdigest())

    def test_frontier_has_no_fixed_research_cutoff_and_is_not_exhausted(self):
        frontier = json.loads(FRONTIER_PATH.read_text(encoding="utf-8"))
        self.assertFalse(frontier["rank_frontier_exhausted"])
        self.assertIsNone(frontier["last_verified_historical_rank"])
        self.assertIn("no fixed top-N cutoff", frontier["rank_policy"])
        self.assertGreater(frontier["next_candidate_batch_size"], 0)

    def test_registry_keeps_old_hypothesis_and_active_sequence(self):
        registry = json.loads(REGISTRY_PATH.read_text())
        self.assertEqual(registry["program_status"], "ACTIVE")
        # next_sequence_number tracks the highest registered hypothesis id;
        # H1..H7 are present after the 2026-10-25 reconciliation that added
        # H7 (canonical-block positive-direction candidate); H8 was added
        # after the 2026-10-25T19Z state-representativeness audit; H9 was
        # added after the 2026-10-29 tail-influence audit (DISP-003-TAILAUDIT-001);
        # H10 was allocated after the 2026-11-02 cutoff unblock and refresh
        # (DISP-003-H10 fresh sealed forward block, currently BLOCKED by data
        # availability); H11 was added as final integrity audit; H12 added for
        # H10 feasibility; H13 added for the forward-block placebo red team;
        # H14..H22 added for DISP-003 diagnostic-audit AUDIT_TO_HYPOTHESIS
        # coverage (regime conditioning, cluster bootstrap, final integrity,
        # overlap aware, tail influence, temporal stability, rolling dispersion
        # window, state representativeness) and for the H10 sequential
        # alpha-spending declaration (H22); H23 was added for the F1COVERAGE-001
        # panel-coverage repair (DISP-003-F1COVERAGE-001, EXPLORATORY_ONLY,
        # coverage_only) so the committed F1 repair audit no longer references an
        # unallocated registry hypothesis; H24 was added for the F1SENS-002
        # coverage-outcome sensitivity (DISP-003-F1SENS-002, EXPLORATORY_ONLY)
        # so the committed F1 sensitivity audit references an allocated
        # registry hypothesis; H25 was added for the F1STAB-003 coverage
        # stability audit (DISP-003-F1STAB-003, EXPLORATORY_ONLY,
        # stability_robustness) so the committed F1 stability audit references
        # an allocated registry hypothesis. H26 was added for the F1GRID-001
        # full 216-cell grid sensitivity arm (DISP-003-F1GRID-001,
        # EXPLORATORY_ONLY) so the committed F1 grid preregistration references
        # an allocated registry hypothesis. H27 was added for the F1GRID-002
        # ledger-vintage (as-of 2026-09-30) grid sensitivity arm
        # (DISP-003-F1GRID-002, EXPLORATORY_ONLY), preregistering the
        # F1GRID-001 unblock path (a): trim panels to the frozen ledger
        # vintage so arm A can reproduce the committed ledger before the
        # arm B contrast. H28 was added for the DISP-003-SOURCECOV-001
        # source-coverage gap audit (EXPLORATORY_ONLY, coverage_only) so the
        # committed audit artifact references an allocated registry hypothesis;
        # the artifact predated its preregistration, which is repaired by
        # scripts/repair_source_coverage_audit_prereg.py. H29 was added for the
        # H004V106 grid anchor cross-check integrity audit
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-GRID-ANCHOR-CROSSCHECK,
        # EXPLORATORY_ONLY, consistency_only) so the committed grid anchor
        # cross-check audit references an allocated registry hypothesis.
        # H32 was added for the H004V106 grid ledger internal-consistency
        # audit (HARMONY-CRYPTO-EDGE-004-DISPERSION-003, EXPLORATORY_ONLY,
        # consistency_only) so the committed whole-ledger 216-cell
        # internal-consistency audit references an allocated registry hypothesis.
        # H33 was added for the H004V106 expanding universe eligibility
        # coverage audit (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-EXP-ELIG-001,
        # EXPLORATORY_ONLY, coverage_only) so the committed eligibility
        # coverage audit references an allocated registry hypothesis.
        # H34 was added for the H004V106 H10 fresh forward block
        # preregistration-compliance audit
        # (H004V106_H10_FRESH_FORWARD_BLOCK_PREREG_COMPLIANCE_AUDIT,
        # EXPLORATORY_ONLY, consistency_only) so the committed prereg-compliance
        # audit references an allocated registry hypothesis.
        # H35 was added for the H004V106 H10 fresh forward block maturity-timeline
        # milestone audit (H004V106_H10_MATURITY_TIMELINE_AUDIT, EXPLORATORY_ONLY,
        # planning_only) so the committed maturity-timeline audit references an
        # allocated registry hypothesis.
        # H36 was added for the H004V106 H10 post-2026-11-30 evaluation sequence
        # design (H004V106_H10_POST_2026_11_30_EVALUATION_SEQUENCE, EXPLORATORY_ONLY,
        # planning_only) so the committed evaluation-sequence design artifact
        # references an allocated registry hypothesis.
        # H37 was added for the H004V106 forward block independent recomputation
        # audit (H004V106_FORWARD_BLOCK_INDEPENDENT_RECOMPUTATION_AUDIT,
        # EXPLORATORY_ONLY, consistency_only) so the committed recomputation
        # audit references an allocated registry hypothesis.
        # H38 was added for the H004V106 forward block internal self-consistency
        # audit (H004V106_FORWARD_BLOCK_SELF_CONSISTENCY_AUDIT, EXPLORATORY_ONLY,
        # consistency_only) so the committed self-consistency audit references an
        # allocated registry hypothesis.
        # H39 was added for the H004V106 rank-breadth measurement feasibility
        # study (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001,
        # EXPLORATORY_ONLY, feasibility_only) so the committed feasibility
        # artifact references an allocated registry hypothesis.
        # H40 was added for the committed-panel coverage extension feasibility
        # study (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001,
        # EXPLORATORY_ONLY, feasibility_only) confirming deterministic verified
        # Binance mapping + PIT cap observations for the 188 H39 union assets
        # lacking committed panels (gap unfilled, planning only).
        # H41 was added for the bounded committed-metadata panel acquisition/
        # probe plan (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001,
        # EXPLORATORY_ONLY, planning_only) enumerating deterministic subset
        # and monthly archive targets (no network, no outcomes).
        # H42 was added for the independent rank-breadth reproducibility +
        # raw cap-series integrity audit
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001,
        # EXPLORATORY_ONLY, reproducibility_integrity_only) re-deriving the H39
        # verdict from committed inputs via a separate stdlib-only code path.
        # H43 was added for the planned-archive source-coverage probe
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001,
        # EXPLORATORY_ONLY, source_coverage_only) keylessly HEAD-probing all 920
        # H41-planned monthly archive entries against the free public Binance
        # Public Data Archive to measure actual per-file availability.
        # H44 was added for the F1GRID-002 full 216-cell ledger-vintage
        # execution (DISP-003-F1GRID-002 completed 2026-11-16T23:12:49Z,
        # EXPLORATORY_ONLY, coverage_sensitivity) so the committed
        # grid_result_ledger.json / grid_summary.json under the F1GRID-002
        # experiment root reference an allocated registry hypothesis.
        # H45 was added for the F1GRID-002 sole Holm-status flip diagnostic
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-FLIP-001,
        # EXPLORATORY_ONLY, coverage_sensitivity_diagnostic) characterising the
        # single cell (H004V130) whose Holm status differs between the F1GRID-002
        # arms, so the committed diagnostic artifact references an allocated
        # registry hypothesis.
        # H46 was added for the panel-acquisition coverage reconciliation
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-RECON-001,
        # EXPLORATORY_ONLY, source_coverage_reconciliation) classifying the 31
        # H41-planned archive files absent from the H43 probe as benign
        # pre-listing vs genuine trailing gaps, so the committed reconciliation
        # artifact references an allocated registry hypothesis.
        # H47 was added for the panel-coverage eligibility roster
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001,
        # EXPLORATORY_ONLY, source_coverage_roster) executing H46 next-test
        # option (b): per-asset inclusion decisions from the H43 served windows
        # (9 included / ALPHA excluded), so the committed roster artifact
        # references an allocated registry hypothesis.
        # H48 was added for the panel-coverage acquisition queue
        # (HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001,
        # EXPLORATORY_ONLY, source_coverage_acquisition_queue) turning the H47
        # roster into a bounded wave A / wave B acquisition queue with a
        # per-study-month utility map (7 wave-A assets / 644 files, ARK+ASTR
        # wave B with 18 absent files, ALPHA excluded, 920 files reconciled), so
        # the committed queue artifact references an allocated registry
        # hypothesis.
        self.assertEqual(registry["next_sequence_number"], 48)

        h1 = next(h for h in registry["hypotheses"] if h["id"] == "H1")
        self.assertTrue(h1["immutable"])
        self.assertEqual(h1["status"], "NOT_SUPPORTED_AS_ROBUST_EDGE")
        h7 = next(h for h in registry["hypotheses"] if h["id"] == "H7")
        self.assertEqual(h7["predicted_high_minus_low_sign"], "positive")
        h8 = next(h for h in registry["hypotheses"] if h["id"] == "H8")
        self.assertEqual(h8["status"], "EXPLORATORY_ONLY")

    def test_loop_policy_forbids_manual_id_pause_and_trading(self):
        prompt = PROMPT_PATH.read_text(encoding="utf-8").lower()
        self.assertIn("do not wait for a user-provided experiment id", prompt)
        self.assertIn("no paid services", prompt)
        self.assertIn("live or paper trading", prompt)

if __name__ == "__main__":
    unittest.main()
