"""Hermetic unit tests for scripts/finalize_data_gate.py.

Covers the pure, deterministic ``load_json(p: Path)`` seam:
well-formed JSON object/array/scalar, missing file, invalid JSON and empty
file. The module's ``main()`` is never invoked -- only the importable seam is
exercised, against temp-dir files only.

No network, no committed-panel dependency, no frozen artifact reads/writes.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "finalize_data_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("finalize_data_gate_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class LoadJsonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_loads_well_formed_json_object(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.json"
            p.write_text('{"a": 1, "b": [1, 2, 3]}', encoding="utf-8")
            self.assertEqual(self.mod.load_json(p), {"a": 1, "b": [1, 2, 3]})

    def test_loads_json_array_and_scalar(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "data.json"
            p.write_text('[1, "x", null]', encoding="utf-8")
            self.assertEqual(self.mod.load_json(p), [1, "x", None])

    def test_missing_file_raises_file_not_found_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "absent.json"
            with self.assertRaises(FileNotFoundError):
                self.mod.load_json(p)

    def test_invalid_json_raises_json_decode_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text('{"a": 1,', encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                self.mod.load_json(p)

    def test_empty_file_raises_json_decode_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "empty.json"
            p.write_text("", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                self.mod.load_json(p)


if __name__ == "__main__":
    unittest.main()
