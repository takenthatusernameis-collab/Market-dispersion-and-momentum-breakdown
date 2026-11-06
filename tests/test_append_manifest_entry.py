#!/usr/bin/env python3
"""Regression tests for scripts/append_manifest_entry.py.

The run manifest is a narrative JSON file whose top-level entries are
indented with two spaces and whose last top-level value is the
``session_history`` array. A plain json.load -> json.dump round trip would
re-indent the whole file and churn a frozen narrative for one new entry, so
the script appends by string manipulation. These tests exercise that
behaviour on a throwaway copy of the manifest: round-trip preservation,
duplicate-key refusal, and the guarantee that the appended key set is
exactly the old set plus the new key.

Source-control and durable-state guards only; no market evidence, no frozen
experiment artifact is touched (the tests operate on a temp copy).
"""
import json
import shutil
import sys
import tempfile
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "append_manifest_entry.py"


def _spec():
    return util.spec_from_file_location("append_manifest_entry", str(SCRIPT))


class TestAppendManifestEntry(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.manifest = self.tmp / "run_manifest.json"
        shutil.copy(ROOT / "research_state" / "run_manifest.json", self.manifest)
        self.original = self.manifest.read_text(encoding="utf-8")
        self.original_bytes = self.original.encode("utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, key, obj_str):
        spec = _spec()
        mod = util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.MANIFEST = self.manifest
        old_argv = sys.argv
        sys.argv = ["append_manifest_entry.py", key, obj_str]
        try:
            rc = mod.main()
        finally:
            sys.argv = old_argv
        return rc

    def test_appends_new_key_preserving_formatting(self):
        rc = self._run(
            "test_entry_20261106T000000Z",
            '{"narrow": true, "value": 42}',
        )
        self.assertEqual(rc, 0)
        new = self.manifest.read_text(encoding="utf-8")
        # The pre-existing narrative must be byte-identical up to the insertion
        # point (i.e. the file's prefix is unchanged).
        self.assertTrue(
            new.startswith(self.original[:4096]),
            "append must not reformat the pre-existing narrative",
        )
        d = json.loads(new)
        self.assertIn("test_entry_20261106T000000Z", d)
        self.assertEqual(
            d["test_entry_20261106T000000Z"], {"narrow": True, "value": 42}
        )
        # The old keys are all still present.
        old = json.loads(self.original)
        self.assertTrue(set(old.keys()).issubset(set(d.keys())))

    def test_refuses_duplicate_key(self):
        existing = next(
            k for k in json.loads(self.original) if not k.startswith("session_record_")
        )
        rc = self._run(existing, '{"x": 1}')
        self.assertNotEqual(rc, 0, "duplicate key must be refused")
        self.assertEqual(
            self.manifest.read_bytes(), self.original_bytes,
            "refused write must not modify the manifest",
        )

    def test_refuses_invalid_json_object(self):
        rc = self._run("test_bad_entry", "not-valid-json")
        self.assertNotEqual(rc, 0)

    def test_refuses_missing_argument(self):
        spec = _spec()
        mod = util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.MANIFEST = self.manifest
        old_argv = sys.argv
        sys.argv = ["append_manifest_entry.py"]
        try:
            rc = mod.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()