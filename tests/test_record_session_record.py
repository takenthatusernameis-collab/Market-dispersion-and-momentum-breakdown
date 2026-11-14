#!/usr/bin/env python3
"""Regression tests for scripts/record_session_record.py (no network, no market data).

Pins the durable-state contract that keeps research_state/run_manifest.json's
session-record bookkeeping consistent: every record written by the script must
carry the required outcome fields, must be stored under a
``session_record_<stem>`` key, must appear in the ``session_records`` list, and
``session_record_latest`` must name the newest record. The manifest's historical
``session_record_*`` keys are heterogeneous (prose strings, booleans, partial
records from older conventions) and are NOT asserted here -- only the records
this script writes are held to the contract, so the guard is hermetic and
cannot fail the build over pre-existing drift.

No market data, no network. The manifest is snapshotted in setUp and restored
in tearDown so the guard tests are hermetic.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "record_session_record.py"
spec = importlib.util.spec_from_file_location("record_session_record", SPEC)
rsm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rsm)

MANIFEST = ROOT / "research_state" / "run_manifest.json"
BACKUP = ROOT / "research_state" / "_tmp_manifest_backup.json"


def _read_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _write_manifest(m):
    MANIFEST.write_text(
        json.dumps(m, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class HermeticManifestTests(unittest.TestCase):
    """Snapshot/restore harness so guard tests never leave the manifest dirty."""

    def _run_main_with_file(self, payload):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(payload, fh)
            path = fh.name
        try:
            rsm.main([path])
        finally:
            Path(path).unlink(missing_ok=True)

    def setUp(self):
        if BACKUP.exists():
            BACKUP.unlink()
        shutil.copy2(MANIFEST, BACKUP)

    def tearDown(self):
        if BACKUP.exists():
            shutil.copy2(BACKUP, MANIFEST)
            BACKUP.unlink()


class RequiredFieldsTests(HermeticManifestTests):
    def test_missing_field_rejected(self):
        with self.assertRaises(SystemExit):
            self._run_main_with_file({"session_id": "session_rsm_x"})

    def test_session_id_prefix_enforced(self):
        with self.assertRaises(SystemExit):
            self._run_main_with_file({
                "session_id": "bad_id",
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "action": "a",
                "outcome": "o",
                "verification": "v",
            })


class AppendAndPointerTests(HermeticManifestTests):
    def _payload(self, sid):
        return {
            "session_id": sid,
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "action": "test_action",
            "outcome": "test_outcome",
            "verification": "test_verification",
        }

    def test_append_repoints_latest(self):
        payload = self._payload("session_rsm_001")
        self._run_main_with_file(payload)
        m = _read_manifest()
        ids = m.get("session_records", [])
        self.assertIn("session_record_rsm_001", ids)
        self.assertEqual(m["session_record_latest"], "session_record_rsm_001")
        self.assertEqual(m["last_updated_utc"], "2026-01-01T00:00:00Z")
        self.assertIsInstance(m["session_record_rsm_001"], dict)

    def test_replace_existing_id_is_idempotent(self):
        payload = self._payload("session_rsm_002")
        self._run_main_with_file(payload)
        self._run_main_with_file(payload)
        m = _read_manifest()
        ids = m.get("session_records", [])
        self.assertEqual(ids.count("session_record_rsm_002"), 1)
        self.assertEqual(m["session_record_latest"], "session_record_rsm_002")

    def test_newer_record_wins_pointer(self):
        older = self._payload("session_rsm_003")
        older["timestamp_utc"] = "2026-01-01T00:00:00Z"
        newer = self._payload("session_rsm_004")
        newer["timestamp_utc"] = "2026-01-02T00:00:00Z"
        self._run_main_with_file(older)
        self._run_main_with_file(newer)
        m = _read_manifest()
        self.assertEqual(m["session_record_latest"], "session_record_rsm_004")
        self.assertEqual(m["last_updated_utc"], "2026-01-02T00:00:00Z")


class ScriptWrittenRecordContractTests(HermeticManifestTests):
    """The contract that records WRITTEN BY THIS SCRIPT must satisfy.

    The committed manifest's historical ``session_record_*`` keys are
    heterogeneous (prose strings, booleans, partial records from older
    conventions) and are deliberately NOT asserted here -- only the records
    this script writes are held to the contract, so the guard is hermetic and
    cannot fail the build over pre-existing drift.
    """

    def _payload(self, sid):
        return {
            "session_id": sid,
            "timestamp_utc": "2026-01-01T00:00:00Z",
            "action": "test_action",
            "outcome": "test_outcome",
            "verification": "test_verification",
        }

    def test_written_record_carries_required_fields_and_key_shape(self):
        payload = self._payload("session_rsm_contract_001")
        self._run_main_with_file(payload)
        m = _read_manifest()
        key = "session_record_rsm_contract_001"
        self.assertIn(key, m)
        rec = m[key]
        for f in rsm.REQUIRED:
            self.assertIn(f, rec, f"{key} missing {f}")
        self.assertIn(key, m.get("session_records", []))
        self.assertEqual(m["session_record_latest"], key)

    def test_latest_pointer_always_names_a_script_written_record(self):
        # After any append, session_record_latest must name a record that is a
        # dict carrying the required fields -- i.e. a record this script wrote.
        payload = self._payload("session_rsm_contract_002")
        self._run_main_with_file(payload)
        m = _read_manifest()
        latest = m["session_record_latest"]
        self.assertIsInstance(m.get(latest), dict, f"{latest} is not a dict")
        for f in rsm.REQUIRED:
            self.assertIn(f, m[latest], f"{latest} missing {f}")


if __name__ == "__main__":
    unittest.main()