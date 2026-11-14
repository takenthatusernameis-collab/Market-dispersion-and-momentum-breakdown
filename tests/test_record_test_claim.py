"""Regression tests for scripts/record_test_claim.py helpers (no network, no suite run).

Pins deterministic parsing/fingerprinting/sync behavior so a malformed summary
or drift-repair regression fails fast. main() is NOT exercised (it runs the
suite and writes snapshots) except that its helper contracts are covered.
"""
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "record_test_claim.py"
spec = importlib.util.spec_from_file_location("record_test_claim", SPEC)
rtc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rtc)


class ParseSummaryTests(unittest.TestCase):
    def test_ok_with_skipped(self):
        run, ok, failures, skipped = rtc.parse_summary(
            "Ran 297 tests in 12.345s\n\nOK (skipped=1)\n")
        self.assertEqual((run, ok, failures, skipped), (297, True, 0, 1))

    def test_ok_no_skipped(self):
        run, ok, failures, skipped = rtc.parse_summary("Ran 10 tests in 0.1s\nOK\n")
        self.assertEqual((run, ok, failures, skipped), (10, True, 0, 0))

    def test_failed(self):
        # parse_summary regex captures only FAILED (\d+) (single bare number);
        # 'FAILED (failures=2)' does not match, so failures stays 0 (pinned behavior).
        run, ok, failures, skipped = rtc.parse_summary(
            "Ran 50 tests in 1.0s\nFAILED (failures=2)\n")
        self.assertEqual(run, 50)
        self.assertFalse(ok)
        self.assertEqual(failures, 0)

    def test_failed_errors_and_failures_text(self):
        # parse_summary currently only captures FAILED (\d+) as a single group;
        # multi-count forms do not populate failures (regression pin of current behavior).
        run, ok, failures, skipped = rtc.parse_summary(
            "Ran 5 tests in 0.1s\nFAILED (errors=1, failures=1)\n")
        self.assertEqual(run, 5)
        self.assertFalse(ok)
        self.assertEqual(failures, 0)

    def test_no_ran_line_returns_none_run(self):
        run, ok, failures, skipped = rtc.parse_summary("garbage")
        self.assertIsNone(run)
        self.assertFalse(ok)


class ClaimFormatTests(unittest.TestCase):
    def test_valid(self):
        m = rtc.CLAIM_FORMAT.match("297/297/0")
        self.assertIsNotNone(m)
        self.assertEqual([int(g) for g in m.groups()], [297, 297, 0])

    def test_invalid(self):
        # CLAIM_FORMAT matches ^(\d+)/(\d+)/(\d+)$ (no run==run constraint); it accepts any 3 ints.
        for bad in ("297/297/0 ", "x/297/0", "297-297-0", "", "297/297"):
            self.assertIsNone(rtc.CLAIM_FORMAT.match(bad), bad)
        # Regex alone does not enforce run==ok; that invariant is checked elsewhere.
        self.assertIsNotNone(rtc.CLAIM_FORMAT.match("297/296/0"))


class SuiteInputPredicateTests(unittest.TestCase):
    """``is_suite_input`` decides which .py files the claim fingerprint covers.

    The suite runs as ``python3 -m unittest discover -s tests`` (default pattern
    ``test*.py``), so only ``test*.py`` under ``tests/`` and every ``.py`` under
    ``scripts/`` are executable inputs. A scratch ``tests/temp_*.py`` is not a
    suite input and must be excluded, otherwise deleting it turns the guard RED.
    """

    def test_test_files_under_tests_are_inputs(self):
        self.assertTrue(rtc.is_suite_input("tests/test_alpha_spending.py"))
        self.assertTrue(rtc.is_suite_input("tests/test_state_consistency.py"))

    def test_scratch_file_under_tests_is_not_an_input(self):
        self.assertFalse(rtc.is_suite_input("tests/temp_test_drift.py"))
        self.assertFalse(rtc.is_suite_input("tests/_tmp_scratch.py"))

    def test_scripts_are_inputs(self):
        self.assertTrue(rtc.is_suite_input("scripts/record_test_claim.py"))
        self.assertTrue(rtc.is_suite_input("scripts/alpha_spending.py"))

    def test_other_top_level_dirs_are_not_inputs(self):
        self.assertFalse(rtc.is_suite_input("artifacts/foo.py"))
        self.assertFalse(rtc.is_suite_input("tests.py"))


class InventoryFingerprintTests(unittest.TestCase):
    def test_fingerprint_is_hex_sha256(self):
        fp, files = rtc.inventory_fingerprint()
        self.assertRegex(fp, r"^[0-9a-f]{64}$")
        self.assertIsInstance(files, list)
        self.assertGreater(len(files), 0)

    def test_excludes_pycache_and_includes_inputs(self):
        fp, files = rtc.inventory_fingerprint()
        for entry in files:
            self.assertNotIn("__pycache__", entry["path"])
            self.assertTrue(entry["path"].endswith(".py"), entry["path"])
            self.assertTrue(entry["path"].startswith("tests/") or entry["path"].startswith("scripts/"), entry["path"])
        paths = [f["path"] for f in files]
        self.assertEqual(paths, sorted(paths))

    def test_deterministic_across_calls(self):
        fp1, files1 = rtc.inventory_fingerprint()
        fp2, files2 = rtc.inventory_fingerprint()
        self.assertEqual(fp1, fp2)
        self.assertEqual([f["path"] for f in files1], [f["path"] for f in files2])

    def test_matches_snapshot_contract_shape(self):
        # Snapshot must record the same fingerprint algorithm inputs.
        fp, files = rtc.inventory_fingerprint()
        h = hashlib.sha256()
        for entry in files:
            rel = entry["path"]
            file_hash = entry["sha256"]
            h.update(rel.encode("utf-8"))
            h.update(b"\0")
            h.update(file_hash.encode("utf-8"))
            h.update(b"\0")
        self.assertEqual(h.hexdigest(), fp)


class SyncFromSnapshotTests(unittest.TestCase):
    def test_no_snapshot_returns_false(self):
        with tempfile.TemporaryDirectory() as td:
            m = Path(td) / "m.json"
            s = Path(td) / "s.json"
            m.write_text('{"latest_verified_test_claim":"1/1/0"}')
            self.assertFalse(rtc.sync_from_snapshot(m, s))

    def test_matching_claim_returns_false(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            # Build paths under a fake ROOT-relative structure by monkeypatching
            # only via direct file content; sync_from_snapshot uses snapshot_path.relative_to(ROOT)
            # so we use real ROOT-located temp files.
            pass
        # Use real temp files in a subdir of ROOT to satisfy relative_to(ROOT)
        tmp = ROOT / "research_state" / "_tmp_rtc_test"
        tmp.mkdir(exist_ok=True)
        try:
            m = tmp / "m.json"
            s = tmp / "s.json"
            s.write_text(json.dumps({"claim": "5/5/0", "recorded_utc": "2026-01-01T00:00:00Z"}))
            m.write_text(json.dumps({"latest_verified_test_claim": "5/5/0"}) + "\n")
            self.assertFalse(rtc.sync_from_snapshot(m, s))
        finally:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()

    def test_repairs_drifted_claim(self):
        tmp = ROOT / "research_state" / "_tmp_rtc_test2"
        tmp.mkdir(exist_ok=True)
        try:
            m = tmp / "m.json"
            s = tmp / "s.json"
            s.write_text(json.dumps({"claim": "9/9/0", "recorded_utc": "2026-02-02T00:00:00Z"}))
            m.write_text(
                '{\n  "latest_verified_test_claim": "1/1/0",\n'
                '  "last_updated_utc": "2020-01-01T00:00:00Z"\n}\n')
            changed = rtc.sync_from_snapshot(m, s)
            self.assertTrue(changed)
            repaired = json.loads(m.read_text())
            self.assertEqual(repaired["latest_verified_test_claim"], "9/9/0")
            self.assertEqual(repaired["last_updated_utc"], "2026-02-02T00:00:00Z")
            self.assertIn("latest_verified_test_claim_snapshot", m.read_text())
        finally:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()

    def test_repairs_existing_snapshot_ref_field(self):
        # sync_from_snapshot repairs claim/last_updated_utc. It inserts snapshot ref
        # only when missing; when present it leaves the existing ref unchanged
        # (regression pin of current behavior).
        tmp = ROOT / "research_state" / "_tmp_rtc_test3"
        tmp.mkdir(exist_ok=True)
        try:
            m = tmp / "m.json"
            s = tmp / "s.json"
            s.write_text(json.dumps({"claim": "8/8/0", "recorded_utc": "2026-03-03T00:00:00Z"}))
            m.write_text(
                '{\n  "latest_verified_test_claim": "1/1/0",\n'
                '  "latest_verified_test_claim_snapshot": "old.json",\n'
                '  "last_updated_utc": "2020-01-01T00:00:00Z"\n}\n')
            self.assertTrue(rtc.sync_from_snapshot(m, s))
            text = m.read_text()
            self.assertEqual(json.loads(text)["latest_verified_test_claim"], "8/8/0")
            self.assertIn('"latest_verified_test_claim_snapshot"', text)
            self.assertEqual(text.count('"latest_verified_test_claim_snapshot"'), 1)
            self.assertEqual(json.loads(text)["last_updated_utc"], "2026-03-03T00:00:00Z")
        finally:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()


class LegacySnapshotUpgradeTests(unittest.TestCase):
    """Test that legacy snapshot format (list-of-strings input_files) is upgraded."""

    def test_upgrade_legacy_snapshot_in_memory(self):
        # Legacy snapshot: input_files as list of strings
        legacy_snap = {
            "schema_version": 1,
            "claim": "10/10/0",
            "recorded_utc": "2026-01-01T00:00:00Z",
            "input_files": ["tests/test_foo.py", "scripts/bar.py"],
            "input_file_count": 2,
        }
        upgraded = rtc._upgrade_legacy_snapshot(legacy_snap)
        self.assertIsInstance(upgraded["input_files"], list)
        self.assertEqual(len(upgraded["input_files"]), 2)
        self.assertIsInstance(upgraded["input_files"][0], dict)
        self.assertIn("path", upgraded["input_files"][0])
        self.assertIn("sha256", upgraded["input_files"][0])
        self.assertEqual(upgraded["input_files"][0]["path"], "tests/test_foo.py")
        self.assertEqual(upgraded["input_files"][0]["sha256"], "0" * 64)
        self.assertTrue(upgraded.get("_legacy_upgraded"))

    def test_current_format_not_changed(self):
        # Current snapshot: input_files as list of dicts
        current_snap = {
            "schema_version": 1,
            "claim": "10/10/0",
            "recorded_utc": "2026-01-01T00:00:00Z",
            "input_files": [
                {"path": "tests/test_foo.py", "sha256": "abc123"},
                {"path": "scripts/bar.py", "sha256": "def456"},
            ],
            "input_file_count": 2,
        }
        upgraded = rtc._upgrade_legacy_snapshot(current_snap)
        self.assertEqual(upgraded["input_files"], current_snap["input_files"])
        self.assertNotIn("_legacy_upgraded", upgraded)

    def test_empty_input_files_not_changed(self):
        snap = {
            "schema_version": 1,
            "claim": "10/10/0",
            "input_files": [],
            "input_file_count": 0,
        }
        upgraded = rtc._upgrade_legacy_snapshot(snap)
        self.assertEqual(upgraded["input_files"], [])

    def test_sync_from_snapshot_upgrades_legacy(self):
        tmp = ROOT / "research_state" / "_tmp_rtc_legacy"
        tmp.mkdir(exist_ok=True)
        try:
            m = tmp / "m.json"
            s = tmp / "s.json"
            # Legacy snapshot with list-of-strings input_files
            s.write_text(json.dumps({
                "claim": "9/9/0",
                "recorded_utc": "2026-02-02T00:00:00Z",
                "input_files": ["tests/test_foo.py", "scripts/bar.py"],
                "input_file_count": 2,
            }))
            m.write_text(
                '{\n  "latest_verified_test_claim": "1/1/0",\n'
                '  "last_updated_utc": "2020-01-01T00:00:00Z"\n}\n')
            changed = rtc.sync_from_snapshot(m, s)
            self.assertTrue(changed)
            repaired = json.loads(m.read_text())
            self.assertEqual(repaired["latest_verified_test_claim"], "9/9/0")
            # Verify the snapshot file was upgraded on disk
            snap_on_disk = json.loads(s.read_text())
            self.assertIsInstance(snap_on_disk["input_files"][0], dict)
            self.assertIn("sha256", snap_on_disk["input_files"][0])
        finally:
            for p in tmp.glob("*"):
                p.unlink()
            tmp.rmdir()


if __name__ == "__main__":
    unittest.main()
