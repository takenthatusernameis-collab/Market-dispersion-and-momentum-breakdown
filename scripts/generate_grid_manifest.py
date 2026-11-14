#!/usr/bin/env python3
"""Generate the deterministic, pre-registered DISPERSION-001 grid manifest.

The pure seam ``build_manifest(config_path)`` enumerates the Cartesian product
of the configured axes in the declared order, assigns ``H004G###`` IDs, computes
the canonical JSON and SHA-256 of every configuration, and returns the manifest
dict. ``main()`` is the only place that reads or writes files, and it is guarded
by ``__main__`` so importing this module never touches the filesystem.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "dispersion_momentum_grid_v1.json"
DEFAULT_OUTPUT = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-001" / "grid_config_manifest.json"


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
            "config_id": f"H004G{index:03d}",
            "enumeration_index": index,
            "parameters": parameters,
            "canonical_config_json": canonical,
            "config_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        })

    ids = [row["config_id"] for row in rows]
    hashes = [row["config_sha256"] for row in rows]
    if len(set(ids)) != expected or len(set(hashes)) != expected:
        raise ValueError("configuration IDs and hashes must be unique")

    try:
        source_path = str(config_path.resolve().relative_to(ROOT))
    except ValueError:
        source_path = config_path.name
    # NOTE: the committed DISP-001 manifest predates the schema_version field and
    # is a frozen artifact; build_manifest omits it so regeneration is
    # byte-identical. Do not add schema_version here without re-freezing the
    # artifact under a new ID.
    return {
        "experiment_id": config["experiment_id"],
        "grid_id": config["grid_id"],
        "source_config": source_path,
        "source_config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "expected_combinations": expected,
        "combination_count": len(rows),
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