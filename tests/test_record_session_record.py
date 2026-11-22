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

No market data, no network. The record_session_record module's MANIFEST path is
redirected at a per-test temporary COPY of the real manifest in setUp, so the
committed research_state/run_manifest.json is opened read-only (once, to seed
the copy) and is never written. This removes the shared-mutable-file class of
bug entirely; see HermeticManifestTests for why a snapshot/restore of the real
file was not sufficient.
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


def _read_manifest():
    # Reads the module's ACTIVE manifest path (a per-test temp copy under the
    # hermetic harness), never a hard-coded real path.
    return json.loads(rsm.MANIFEST.read_text(encoding="utf-8"))


def _write_manifest(m):
    rsm.MANIFEST.write_text(
        json.dumps(m, indent=2, sort_keys=False, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


class HermeticManifestTests(unittest.TestCase):
    """Fully hermetic harness: the record_session_record module's MANIFEST path
    is redirected at a per-test temporary COPY of the real manifest, so the
    committed research_state/run_manifest.json is never written.

    The earlier implementation snapshotted the real manifest to a sibling
    ``_tmp_manifest_backup.json`` in setUp and copied it back in tearDown. That
    left the real durable-state file writable by the test and, under the full
    suite, the restore was not reliable: checkpoint commits ee98b1d1, bddb0c7,
    56490d93 and e27c4080 captured committed ``session_record_rsm_*`` fixtures
    (timestamp 2026-01-01) inside run_manifest.json, and a polluted manifest
    makes tests/test_state_timestamp_not_stale.py and
    tests/test_state_consistency.py::test_session_record_latest_points_at_the_most_recent_record
    fail on the next run. Redirecting the module constant (the same pattern
    tests/test_append_manifest_entry.py uses) removes the shared-mutable-file
    class of bug: the real file is opened read-only, once, to seed the copy.
    """

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
        import tempfile
        self._tmpdir = tempfile.mkdtemp(prefix="rsm_test_")
        self._tmp_manifest = Path(self._tmpdir) / "run_manifest.json"
        # Seed the temp copy from the real manifest (read-only access).
        self._tmp_manifest.write_text(
            MANIFEST.read_text(encoding="utf-8"), encoding="utf-8"
        )
        self._orig_manifest = rsm.MANIFEST
        rsm.MANIFEST = self._tmp_manifest

    def tearDown(self):
        rsm.MANIFEST = self._orig_manifest
        shutil.rmtree(self._tmpdir, ignore_errors=True)


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

    def test_real_manifest_is_never_written(self):
        # Tripwire: running any record append must leave the committed
        # research_state/run_manifest.json byte-identical. If the hermetic
        # redirection above is ever removed, this fails loudly instead of
        # silently re-polluting durable state (the recurring class of bug this
        # test file's history records).
        before = MANIFEST.read_bytes()
        self._run_main_with_file(self._payload("session_rsm_contract_003"))
        after = MANIFEST.read_bytes()
        self.assertEqual(
            before, after,
            "record_session_record wrote the real research_state/run_manifest.json",
        )


if __name__ == "__main__":
    unittest.main()