#!/usr/bin/env python3
"""Regression guards for the F1 panel-coverage repair arm.

The F1COVERAGE-001 arm (``scripts/f1_panel_coverage_repair.py``) fetches the 168
missing Binance monthly zips for four symbols, rebuilds ONLY that arm's panels
into a new experiment directory, and reports descriptive eligible-asset coverage
deltas. It is an EXPLORATORY_ONLY source-coverage repair, not a hypothesis test.

The preregistration
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001/preregistrations/F1_PANEL_COVERAGE_REPAIR_v1.md``
promised a regression guard (§6, item 4) that was never committed. This file
supplies it.

Guards (all stdlib, no network, no market evidence):
  1. The new experiment id has exactly one ``HARMONY-CRYPTO-EDGE-004-`` prefix.
     The first emitted audit recorded a doubled prefix
     (``HARMONY-CRYPTO-EDGE-004-HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001``);
     the script now emits the bare id and this must stay fixed.
  2. The script source no longer contains the doubling expression, and emits
     ``"experiment_id": NEW_EXP`` directly.
  3. New paths are isolated from the committed DISPERSION-003 panels/raw.
  4. The repair writes panels only under the new experiment directory.
  5. The frozen canonical and H10-fresh block hashes the script pins match the
     committed artifacts on disk.
  6. The latest committed audit reports unchanged inputs, unchanged frozen
     artifacts, a single-prefixed experiment id, and an allowed verdict.
"""
import hashlib
import json
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "f1_panel_coverage_repair.py"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"
PROGRAM_PREFIX = "HARMONY-CRYPTO-EDGE-004-"


def _load_module():
    spec = util.spec_from_file_location("f1_panel_coverage_repair", str(SCRIPT))
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class TestF1RepairConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_new_experiment_id_has_single_program_prefix(self):
        self.assertEqual(self.mod.NEW_EXP, NEW_EXP)
        self.assertEqual(self.mod.NEW_EXP.count(PROGRAM_PREFIX), 1)
        self.assertFalse(
            self.mod.NEW_EXP.startswith(PROGRAM_PREFIX + PROGRAM_PREFIX),
            "experiment id must not carry a doubled program prefix",
        )
        self.assertNotEqual(self.mod.OLD_EXP, self.mod.NEW_EXP)

    def test_script_source_has_no_double_prefix_expression(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn(
            f'f"{PROGRAM_PREFIX}{{NEW_EXP}}"',
            source,
            "experiment_id must not be built by prefixing NEW_EXP again",
        )
        self.assertIn('"experiment_id": NEW_EXP', source)

    def test_new_paths_are_isolated_from_committed_experiment(self):
        old_root = ROOT / "artifacts" / self.mod.OLD_EXP
        new_root = ROOT / "artifacts" / self.mod.NEW_EXP
        for path in (self.mod.NEW_PANELS, self.mod.NEW_RAW, self.mod.NEW_AUDIT):
            self.assertTrue(path.is_relative_to(new_root), f"{path} escapes {new_root}")
        self.assertFalse(self.mod.NEW_PANELS.is_relative_to(old_root))
        self.assertFalse(self.mod.NEW_RAW.is_relative_to(old_root))
        self.assertFalse(self.mod.NEW_AUDIT.is_relative_to(old_root))

    def test_rebuild_panels_writes_only_under_new_panels(self):
        import inspect

        src = inspect.getsource(self.mod.rebuild_panels)
        self.assertIn("NEW_PANELS", src)
        self.assertNotIn("OLD_PANELS", src)


class TestF1RepairFrozenHashes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()

    def test_frozen_hash_constants_match_committed_artifacts(self):
        self.assertTrue(self.mod.FROZEN_HASHES)
        for rel, expected in self.mod.FROZEN_HASHES.items():
            path = ROOT / "artifacts" / self.mod.OLD_EXP / rel
            self.assertTrue(path.exists(), f"missing frozen artifact {rel}")
            self.assertEqual(
                _sha256_file(path),
                expected,
                f"committed artifact drifted from the hash pinned by the repair: {rel}",
            )


class TestF1RepairCommittedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_module()
        cls.audit_dir = ROOT / "artifacts" / cls.mod.NEW_EXP / "integrity_audit"
        cls.audits = sorted(cls.audit_dir.glob("f1_panel_coverage_repair_*.json"))

    def test_committed_audit_exists(self):
        self.assertTrue(self.audits, "no committed F1 repair audit found")

    def test_latest_audit_is_well_formed(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        self.assertEqual(latest["experiment_id"], self.mod.NEW_EXP)
        self.assertIn(latest["verdict"], ("PASS", "PARTIAL"))
        checks = latest["read_only_checks"]
        self.assertTrue(checks["old_panels_byte_unchanged"])
        self.assertTrue(all(v["match"] for v in checks["old_kline_panel_hashes"].values()))
        self.assertTrue(all(v["match"] for v in checks["frozen_artifacts"].values()))
        disposition = latest["disposition"]
        self.assertFalse(disposition["frozen_artifacts_modified"])
        self.assertFalse(disposition["old_panels_modified"])
        self.assertFalse(disposition["outcomes_computed"])

    def test_latest_audit_pins_both_frozen_blocks(self):
        latest = json.loads(self.audits[-1].read_text(encoding="utf-8"))
        frozen = latest["read_only_checks"]["frozen_artifacts"]
        self.assertEqual(set(frozen), set(self.mod.FROZEN_HASHES))
        for rel, entry in frozen.items():
            self.assertTrue(entry["match"], f"{rel} mismatch in committed audit")


if __name__ == "__main__":
    unittest.main()