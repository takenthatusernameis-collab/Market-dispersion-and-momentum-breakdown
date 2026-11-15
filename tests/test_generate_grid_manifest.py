"""Hermetic unit tests for scripts/generate_grid_manifest.py.

Covers the pure, deterministic seams ``canonical_json(value)`` and
``build_manifest(config_path)`` for the frozen DISPERSION-001 grid:

* ``canonical_json`` — sorted keys, compact separators, non-ASCII preserved.
* ``build_manifest`` — Cartesian enumeration in the configured axis order,
  ``H004G###`` id assignment, per-cell canonical JSON + SHA-256, uniqueness
  guards, and ``ValueError`` failure paths (axis_order mismatch, empty axis,
  combination count mismatch).
* Frozen-config reproduction — ``build_manifest`` on the committed DISPERSION-001
  config reproduces the committed 72-cell manifest byte-for-byte (deep equal),
  including the preregistered primary-compatible anchor H004G033 and the frozen
  config SHA-256.

The synthetic-config tests write only to a temporary directory. The
frozen-config test reads the committed config and manifest but never writes
them. No network. Synthetic fixtures are software tests only, never market
evidence.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_grid_manifest.py"


def _load():
    spec = importlib.util.spec_from_file_location("generate_grid_manifest_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _base_config() -> dict:
    """Minimal 2-cell config satisfying every build_manifest guard."""
    return {
        "experiment_id": "SYNTH-001",
        "grid_id": "SYNTH-GRID-001",
        "axes": [
            {"name": "lookback", "values": [30]},
            {"name": "arm", "values": ["a", "b"]},
        ],
        "expected_combinations": 2,
        "enumeration": {"axis_order": ["lookback", "arm"]},
    }


def _write_config(directory: Path, config: dict) -> Path:
    path = directory / "grid_config.json"
    path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class CanonicalJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_sorted_keys(self):
        self.assertEqual(self.mod.canonical_json({"b": 1, "a": 2}), '{"a":2,"b":1}')

    def test_compact_separators(self):
        out = self.mod.canonical_json({"a": [1, 2], "b": {"c": 3}})
        self.assertEqual(out, '{"a":[1,2],"b":{"c":3}}')
        self.assertNotIn(", ", out)
        self.assertNotIn(": ", out)

    def test_non_ascii_preserved(self):
        self.assertEqual(self.mod.canonical_json({"name": "café"}), '{"name":"café"}')

    def test_nested_key_order_is_deterministic(self):
        a = self.mod.canonical_json({"z": {"y": 1, "x": 2}, "a": 0})
        b = self.mod.canonical_json({"a": 0, "z": {"x": 2, "y": 1}})
        self.assertEqual(a, b)


class BuildManifestSyntheticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_enumerates_cartesian_product_in_axis_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), _base_config())
            manifest = self.mod.build_manifest(path)

        self.assertEqual(manifest["experiment_id"], "SYNTH-001")
        self.assertEqual(manifest["grid_id"], "SYNTH-GRID-001")
        self.assertEqual(manifest["combination_count"], 2)
        self.assertEqual(manifest["expected_combinations"], 2)
        self.assertEqual(
            [row["config_id"] for row in manifest["configurations"]],
            ["H004G001", "H004G002"],
        )
        # arm varies fastest in the declared order [lookback, arm]
        self.assertEqual(
            [row["parameters"] for row in manifest["configurations"]],
            [{"lookback": 30, "arm": "a"}, {"lookback": 30, "arm": "b"}],
        )

    def test_ids_hashes_and_canonical_json_are_self_consistent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), _base_config())
            manifest = self.mod.build_manifest(path)

        ids = [row["config_id"] for row in manifest["configurations"]]
        hashes = [row["config_sha256"] for row in manifest["configurations"]]
        self.assertEqual(len(set(ids)), 2)
        self.assertEqual(len(set(hashes)), 2)
        for row in manifest["configurations"]:
            self.assertEqual(
                row["canonical_config_json"],
                self.mod.canonical_json(row["parameters"]),
            )
            self.assertEqual(
                row["config_sha256"],
                hashlib.sha256(row["canonical_config_json"].encode("utf-8")).hexdigest(),
            )
            self.assertEqual(row["enumeration_index"], int(row["config_id"][5:]))

    def test_source_config_sha256_and_path_recorded(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), _base_config())
            manifest = self.mod.build_manifest(path)
            self.assertEqual(
                manifest["source_config_sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            # temp config is outside ROOT so source_config falls back to basename
            self.assertEqual(manifest["source_config"], path.name)

    def test_schema_version_absent_to_preserve_frozen_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), _base_config())
            manifest = self.mod.build_manifest(path)
        self.assertNotIn("schema_version", manifest)

    def test_axis_order_naming_extra_axis_raises(self):
        cfg = _base_config()
        cfg["enumeration"]["axis_order"].append("nonexistent_axis")
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "axis_order must name every"):
                self.mod.build_manifest(path)

    def test_axis_order_missing_axis_raises(self):
        cfg = _base_config()
        cfg["enumeration"]["axis_order"] = cfg["enumeration"]["axis_order"][:-1]
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "axis_order must name every"):
                self.mod.build_manifest(path)

    def test_empty_axis_raises(self):
        cfg = _base_config()
        cfg["axes"][0]["values"] = []
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                self.mod.build_manifest(path)

    def test_combination_count_mismatch_raises(self):
        cfg = _base_config()
        cfg["expected_combinations"] = 99
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "expected 99 combinations"):
                self.mod.build_manifest(path)

    def test_base_config_is_not_mutated_by_build(self):
        cfg = _base_config()
        snapshot = copy.deepcopy(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            self.mod.build_manifest(path)
        self.assertEqual(cfg, snapshot)


class FrozenGridReproductionTests(unittest.TestCase):
    """Read-only reproduction of the committed DISPERSION-001 grid manifest."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_build_manifest_reproduces_committed_manifest(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        committed = json.loads(self.mod.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(manifest, committed)

    def test_source_config_sha256_matches_file_bytes(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        self.assertEqual(
            manifest["source_config_sha256"],
            hashlib.sha256(self.mod.DEFAULT_CONFIG.read_bytes()).hexdigest(),
        )

    def test_counts_ids_and_hashes(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        self.assertEqual(manifest["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-001")
        self.assertEqual(manifest["combination_count"], 72)
        self.assertEqual(manifest["expected_combinations"], 72)
        ids = [row["config_id"] for row in manifest["configurations"]]
        self.assertEqual(ids[0], "H004G001")
        self.assertEqual(ids[-1], "H004G072")
        self.assertEqual(ids, [f"H004G{i:03d}" for i in range(1, 73)])
        self.assertEqual(len({row["config_sha256"] for row in manifest["configurations"]}), 72)

    def test_primary_compatible_anchor_id(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        anchor = {
            "momentum_lookback_days": 30,
            "forward_horizon_days": 30,
            "dispersion_estimator": "cross_sectional_population_stddev",
            "dispersion_state_rule": "trailing_365d_outer_deciles",
            "momentum_spread_breakpoints": "top_bottom_deciles",
        }
        matches = [
            row["config_id"]
            for row in manifest["configurations"]
            if row["parameters"] == anchor
        ]
        self.assertEqual(matches, ["H004G033"])


if __name__ == "__main__":
    unittest.main()
