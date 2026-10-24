#!/usr/bin/env python3
"""Generate the deterministic, pre-registered DISPERSION-003 grid manifest."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "dispersion_momentum_grid_v3.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003" / "grid_config_manifest.json"


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_manifest(config_path: Path = DEFAULT_CONFIG) -> dict:
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    axes = {axis["name"]: axis["values"] for axis in config["axes"]}
    names = config["enumeration"]["axis_order"]
    if set(names) != set(axes) or len(names) != len(axes):
        raise ValueError("axis_order must name every configured axis exactly once")
    if any(not axes[name] for name in names):
        raise ValueError("grid axes must not be empty")

    combinations = list(itertools.product(*(axes[name] for name in names)))
    expected = int(config["expected_combinations"])
    if len(combinations) != expected:
        raise ValueError(f"expected {expected} combinations but generated {len(combinations)}")

    rows = []
    for index, combination in enumerate(combinations, start=1):
        parameters = dict(zip(names, combination))
        canonical = canonical_json(parameters)
        rows.append({
            "config_id": f"H004V{index:03d}",
            "enumeration_index": index,
            "parameters": parameters,
            "canonical_config_json": canonical,
            "config_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        })

    ids = [row["config_id"] for row in rows]
    hashes = [row["config_sha256"] for row in rows]
    if len(set(ids)) != expected or len(set(hashes)) != expected:
        raise ValueError("configuration IDs and hashes must be unique")

    anchor_values = {
        "momentum_lookback_days": 30,
        "forward_horizon_days": 30,
        "dispersion_estimator": "cross_sectional_population_stddev",
        "dispersion_window_days": 365,
        "dispersion_state_rule": "trailing_window_outer_deciles",
    }
    anchor_rows = [row for row in rows if all(row["parameters"].get(k) == v for k, v in anchor_values.items())]
    by_arm = {row["parameters"]["universe_arm"]: row["config_id"] for row in anchor_rows}
    if by_arm.get("legacy28_comparator") != config["enumeration"]["comparator_anchor_legacy_config_id"]:
        raise ValueError("legacy anchor ID disagrees with preregistration")
    if by_arm.get("expanding_point_in_time") != config["enumeration"]["primary_anchor_expanding_config_id"]:
        raise ValueError("expanding-universe anchor ID disagrees with preregistration")

    try:
        source_path = str(config_path.resolve().relative_to(ROOT))
    except ValueError:
        source_path = config_path.name
    return {
        "schema_version": config["schema_version"],
        "experiment_id": config["experiment_id"],
        "grid_id": config["grid_id"],
        "source_config": source_path,
        "source_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "expected_combinations": expected,
        "combination_count": len(rows),
        "parameter_configuration_count_before_universe_arms": expected // len(axes["universe_arm"]),
        "universe_arms": axes["universe_arm"],
        "family_size_for_holm": expected,
        "configurations": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest(args.config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment_id": manifest["experiment_id"],
        "combination_count": manifest["combination_count"],
        "unique_ids": len({row["config_id"] for row in manifest["configurations"]}),
        "unique_hashes": len({row["config_sha256"] for row in manifest["configurations"]}),
        "output": str(args.output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
