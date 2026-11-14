"""Hermetic unit tests for scripts/generate_grid_v3_manifest.py.

Covers the pure, deterministic seams ``canonical_json(value)`` and
``build_manifest(config_path)``:

* ``canonical_json`` — sorted keys, compact separators, non-ASCII preserved.
* ``build_manifest`` — Cartesian enumeration in the configured axis order,
  ``H004V###`` id assignment, per-cell canonical JSON + SHA-256, uniqueness
  guards, anchor-id agreement with the preregistration, and the
  ``ValueError`` failure paths (axis_order mismatch, empty axis, combination
  count mismatch, anchor-id disagreement).
* Frozen-config reproduction — ``build_manifest`` on the committed DISPERSION-003
  config reproduces the committed 216-cell manifest byte-for-byte (deep equal),
  including the preregistered anchor ids H004V105 (legacy) / H004V106
  (expanding) and the frozen config SHA-256.

The synthetic-config tests write only to a temporary directory. The
frozen-config test reads the committed config and manifest but never writes
them. No network. Synthetic fixtures are software tests only, never market
evidence.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_grid_v3_manifest.py"
FROZEN_CONFIG_SHA256 = (
    "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176"
)


def _load():
    spec = importlib.util.spec_from_file_location("generate_grid_v3_manifest_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _base_config() -> dict:
    """Minimal two-cell config that satisfies every build_manifest guard.

    The five anchor axes each carry exactly the preregistered anchor value, and
    ``universe_arm`` carries both arms, so the Cartesian product is exactly the
    two anchor cells: index 1 = legacy (H004V001), index 2 = expanding
    (H004V002).
    """
    return {
        "schema_version": "1.0",
        "experiment_id": "SYNTH-GRID",
        "grid_id": "SYNTH-GRID-001",
        "axes": [
            {"name": "momentum_lookback_days", "values": [30]},
            {"name": "forward_horizon_days", "values": [30]},
            {"name": "dispersion_estimator", "values": ["cross_sectional_population_stddev"]},
            {"name": "dispersion_window_days", "values": [365]},
            {"name": "dispersion_state_rule", "values": ["trailing_window_outer_deciles"]},
            {"name": "universe_arm", "values": ["legacy28_comparator", "expanding_point_in_time"]},
        ],
        "expected_combinations": 2,
        "enumeration": {
            "axis_order": [
                "momentum_lookback_days",
                "forward_horizon_days",
                "dispersion_estimator",
                "dispersion_window_days",
                "dispersion_state_rule",
                "universe_arm",
            ],
            "comparator_anchor_legacy_config_id": "H004V001",
            "primary_anchor_expanding_config_id": "H004V002",
        },
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

        self.assertEqual(manifest["combination_count"], 2)
        self.assertEqual(manifest["expected_combinations"], 2)
        self.assertEqual(manifest["family_size_for_holm"], 2)
        self.assertEqual(manifest["parameter_configuration_count_before_universe_arms"], 1)
        self.assertEqual(
            [row["config_id"] for row in manifest["configurations"]],
            ["H004V001", "H004V002"],
        )
        # universe_arm varies fastest, so index 1 is legacy and 2 is expanding.
        self.assertEqual(
            manifest["configurations"][0]["parameters"]["universe_arm"],
            "legacy28_comparator",
        )
        self.assertEqual(
            manifest["configurations"][1]["parameters"]["universe_arm"],
            "expanding_point_in_time",
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
            import hashlib

            self.assertEqual(
                row["config_sha256"],
                hashlib.sha256(row["canonical_config_json"].encode("utf-8")).hexdigest(),
            )
            self.assertEqual(row["enumeration_index"], int(row["config_id"][5:]))

    def test_source_config_sha256_matches_file_bytes(self):
        import hashlib

        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), _base_config())
            manifest = self.mod.build_manifest(path)
            self.assertEqual(
                manifest["source_config_sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

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

    def test_wrong_legacy_anchor_id_raises(self):
        cfg = _base_config()
        cfg["enumeration"]["comparator_anchor_legacy_config_id"] = "H004V999"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "legacy anchor ID disagrees"):
                self.mod.build_manifest(path)

    def test_wrong_expanding_anchor_id_raises(self):
        cfg = _base_config()
        cfg["enumeration"]["primary_anchor_expanding_config_id"] = "H004V999"
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            with self.assertRaisesRegex(ValueError, "expanding-universe anchor ID disagrees"):
                self.mod.build_manifest(path)

    def test_base_config_is_not_mutated_by_build(self):
        cfg = _base_config()
        snapshot = copy.deepcopy(cfg)
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_config(Path(tmp), cfg)
            self.mod.build_manifest(path)
        self.assertEqual(cfg, snapshot)


class FrozenGridReproductionTests(unittest.TestCase):
    """Read-only reproduction of the committed DISPERSION-003 grid manifest."""

    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_build_manifest_reproduces_committed_manifest(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        committed = json.loads(self.mod.DEFAULT_OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(manifest, committed)

    def test_source_config_sha256_matches_frozen_hash(self):
        import hashlib

        self.assertEqual(
            hashlib.sha256(self.mod.DEFAULT_CONFIG.read_bytes()).hexdigest(),
            FROZEN_CONFIG_SHA256,
        )

    def test_counts_and_family_size(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        self.assertEqual(manifest["combination_count"], 216)
        self.assertEqual(manifest["expected_combinations"], 216)
        self.assertEqual(manifest["family_size_for_holm"], 216)
        self.assertEqual(manifest["parameter_configuration_count_before_universe_arms"], 108)

    def test_ids_are_contiguous_and_hashes_unique(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        ids = [row["config_id"] for row in manifest["configurations"]]
        self.assertEqual(ids[0], "H004V001")
        self.assertEqual(ids[-1], "H004V216")
        self.assertEqual(ids, [f"H004V{i:03d}" for i in range(1, 217)])
        self.assertEqual(len({row["config_sha256"] for row in manifest["configurations"]}), 216)

    def test_preregistered_anchor_ids(self):
        manifest = self.mod.build_manifest(self.mod.DEFAULT_CONFIG)
        by_arm = {
            row["parameters"]["universe_arm"]: row["config_id"]
            for row in manifest["configurations"]
            if all(
                row["parameters"].get(k) == v
                for k, v in {
                    "momentum_lookback_days": 30,
                    "forward_horizon_days": 30,
                    "dispersion_estimator": "cross_sectional_population_stddev",
                    "dispersion_window_days": 365,
                    "dispersion_state_rule": "trailing_window_outer_deciles",
                }.items()
            )
        }
        self.assertEqual(by_arm["legacy28_comparator"], "H004V105")
        self.assertEqual(by_arm["expanding_point_in_time"], "H004V106")


if __name__ == "__main__":
    unittest.main()