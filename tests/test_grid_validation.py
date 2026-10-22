import hashlib, itertools, json, unittest
from pathlib import Path
root = Path(__file__).resolve().parents[1]
cfg = json.loads((root/"configs/dispersion_momentum_grid_v1.json").read_text())
manifest = json.loads((root/"artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/grid_config_manifest.json").read_text())
names = cfg["enumeration"]["axis_order"]
values = {a["name"]: a["values"] for a in cfg["axes"]}

class GridValidation(unittest.TestCase):
    def test_count(self):
        self.assertEqual(len(manifest["configurations"]), 72)
        self.assertEqual(manifest["combination_count"], 72)
    def test_unique_ids_hashes(self):
        ids = [r["config_id"] for r in manifest["configurations"]]
        hashes = [r["config_sha256"] for r in manifest["configurations"]]
        self.assertEqual(len(set(ids)), 72)
        self.assertEqual(len(set(hashes)), 72)
        self.assertEqual(ids, [f"H004G{i:03d}" for i in range(1,73)])
    def test_axis_coverage(self):
        for name in names:
            seen = {r["parameters"][name] for r in manifest["configurations"]}
            self.assertEqual(seen, set(values[name]))
    def test_deterministic_regeneration(self):
        rows = []
        for i, combo in enumerate(itertools.product(*[values[n] for n in names]), start=1):
            params = dict(zip(names, combo))
            canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            rows.append((f"H004G{i:03d}", hashlib.sha256(canonical.encode()).hexdigest()))
        self.assertEqual(rows, [(r["config_id"], r["config_sha256"]) for r in manifest["configurations"]])
    def test_anchor(self):
        anchor = next(r for r in manifest["configurations"] if r["config_id"] == "H004G033")
        self.assertEqual(anchor["parameters"], cfg["enumeration"]["primary_compatible_anchor"])

if __name__ == "__main__":
    unittest.main()
