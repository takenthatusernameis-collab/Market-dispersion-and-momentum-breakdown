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


if __name__ == "__main__":
    unittest.main()
