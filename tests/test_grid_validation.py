import hashlib, itertools, json, unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
cfg = json.loads((root/"configs/dispersion_momentum_followup_v1.json").read_text())
manifest = json.loads((root/"artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/grid_config_manifest.json").read_text())
names = cfg["enumeration"]["axis_order"]
values = {a["name"]: a["values"] for a in cfg["axes"]}


class GridValidation(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(manifest["configurations"]), 108)
        self.assertEqual(manifest["combination_count"], 108)

    def test_unique_ids_hashes(self):
        ids = [r["config_id"] for r in manifest["configurations"]]
        hashes = [r["config_sha256"] for r in manifest["configurations"]]
        self.assertEqual(len(set(ids)), 108)
        self.assertEqual(len(set(hashes)), 108)
        self.assertEqual(ids, [f"H004F{i:03d}" for i in range(1, 109)])

    def test_axis_coverage(self):
        for name in names:
            seen = {r["parameters"][name] for r in manifest["configurations"]}
            self.assertEqual(seen, set(values[name]))

    def test_deterministic_regeneration(self):
        rows = []
        for i, combo in enumerate(itertools.product(*[values[n] for n in names]), start=1):
            params = dict(zip(names, combo))
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            rows.append((f"H004F{i:03d}", hashlib.sha256(canonical.encode()).hexdigest()))
        self.assertEqual(rows, [(r["config_id"], r["config_sha256"]) for r in manifest["configurations"]])

    def test_anchor(self):
        anchor = next(r for r in manifest["configurations"] if r["config_id"] == "H004F033")
        expected = {
            "momentum_lookback_days": 14,
            "forward_horizon_days": 60,
            "dispersion_estimator": "scaled_median_absolute_deviation_1_4826",
            "dispersion_window_days": 90,
            "dispersion_state_rule": "trailing_window_outer_deciles"
        }
        self.assertEqual(anchor["parameters"], expected)


class GridV3ManifestValidation(unittest.TestCase):
    """Deterministic regeneration checks for the DISPERSION-003 v3 grid manifest
    (216 cells, IDs H004V001-H004V216). Read-only: regenerates from the frozen
    config and compares against the stored artifact without writing it.
    """

    def setUp(self):
        self.cfg_path = root / "configs" / "dispersion_momentum_grid_v3.json"
        self.stored = json.loads((root / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003" / "grid_config_manifest.json").read_text())
        self.cfg = json.loads(self.cfg_path.read_text())
        self.names = self.cfg["enumeration"]["axis_order"]
        self.values = {a["name"]: a["values"] for a in self.cfg["axes"]}

    def test_stored_count_and_ids(self):
        self.assertEqual(self.cfg["expected_combinations"], 216)
        self.assertEqual(self.stored["combination_count"], 216)
        self.assertEqual(len(self.stored["configurations"]), 216)
        ids = [r["config_id"] for r in self.stored["configurations"]]
        self.assertEqual(ids, [f"H004V{i:03d}" for i in range(1, 217)])
        self.assertEqual(len(set(ids)), 216)
        self.assertEqual(len(set(r["config_sha256"] for r in self.stored["configurations"])), 216)

    def test_anchor_ids_by_arm(self):
        by_arm = {r["parameters"]["universe_arm"]: r["config_id"] for r in self.stored["configurations"] if all(
            r["parameters"].get(k) == v for k, v in self.cfg["enumeration"].items() if k in r["parameters"]
        )}
        anchor_params = {
            "momentum_lookback_days": 30,
            "forward_horizon_days": 30,
            "dispersion_estimator": "cross_sectional_population_stddev",
            "dispersion_window_days": 365,
            "dispersion_state_rule": "trailing_window_outer_deciles",
        }
        anchor_rows = [r for r in self.stored["configurations"] if all(r["parameters"].get(k) == v for k, v in anchor_params.items())]
        by_arm = {r["parameters"]["universe_arm"]: r["config_id"] for r in anchor_rows}
        self.assertEqual(by_arm.get("legacy28_comparator"), "H004V105")
        self.assertEqual(by_arm.get("expanding_point_in_time"), "H004V106")

    def test_deterministic_regeneration_matches_stored(self):
        rows = []
        for index, combination in enumerate(
            itertools.product(*(self.values[name] for name in self.names)), start=1
        ):
            parameters = dict(zip(self.names, combination))
            canonical = json.dumps(parameters, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            rows.append({
                "config_id": f"H004V{index:03d}",
                "enumeration_index": index,
                "parameters": parameters,
                "canonical_config_json": canonical,
                "config_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            })
        self.assertEqual(
            [(r["config_id"], r["config_sha256"]) for r in rows],
            [(r["config_id"], r["config_sha256"]) for r in self.stored["configurations"]],
        )


if __name__ == "__main__":
    unittest.main()
