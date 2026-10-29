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
        # added after the 2026-10-29 tail-influence audit (DISP-003-TAILAUDIT-001).
        self.assertEqual(registry["next_sequence_number"], 9)
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
