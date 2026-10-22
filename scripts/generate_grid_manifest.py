import hashlib, itertools, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
cfg = json.loads((root/"configs/dispersion_momentum_grid_v1.json").read_text())
axes = cfg["axes"]; names = cfg["enumeration"]["axis_order"]
values = {a["name"]: a["values"] for a in axes}
rows = []
for i, combo in enumerate(itertools.product(*[values[n] for n in names]), start=1):
    params = dict(zip(names, combo))
    canonical = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    rows.append({"config_id": f"H004G{i:03d}", "enumeration_index": i, "parameters": params, "canonical_config_json": canonical, "config_sha256": hashlib.sha256(canonical.encode()).hexdigest()})
manifest = {"experiment_id": cfg["experiment_id"], "grid_id": cfg["grid_id"], "source_config": "configs/dispersion_momentum_grid_v1.json", "source_config_sha256": hashlib.sha256((root/"configs/dispersion_momentum_grid_v1.json").read_bytes()).hexdigest(), "expected_combinations": cfg["expected_combinations"], "combination_count": len(rows), "configurations": rows}
out = root/"artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/grid_config_manifest.json"
out.write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
print(len(rows))
