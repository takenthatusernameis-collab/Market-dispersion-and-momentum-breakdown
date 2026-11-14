"""Hermetic unit tests for scripts/rewrite_state_json.py.

Covers the pure, deterministic ``detect_format(raw: bytes)`` seam:
round-trip reproduction for indent None/1/2/4, ensure_ascii True/False,
trailing newline present/absent, and the SystemExit failure path.

No network, no committed-panel dependency, no frozen artifact reads/writes.
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "rewrite_state_json.py"


def _load():
    spec = importlib.util.spec_from_file_location("rewrite_state_json_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class DetectFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_compact_ascii_no_trailing_newline(self):
        raw = b'{"a": 1, "b": [1, 2, 3]}'
        self.assertEqual(self.mod.detect_format(raw), (None, True, False))

    def test_compact_non_ascii_no_trailing_newline(self):
        raw = json.dumps({"name": "我爱马来了"}, ensure_ascii=False).encode()
        self.assertEqual(self.mod.detect_format(raw), (None, False, False))

    def test_compact_with_trailing_newline_raises_system_exit(self):
        with self.assertRaises(SystemExit):
            self.mod.detect_format(b'{"a": 1, "b": [1, 2, 3]}\n')

    def test_indent_2_ascii_with_trailing_newline(self):
        obj = {"a": 1, "b": [1, 2, 3]}
        raw = json.dumps(obj, indent=2, ensure_ascii=True).encode() + b"\n"
        self.assertEqual(self.mod.detect_format(raw), (2, True, True))

    def test_indent_2_ascii_no_trailing_newline_raises_system_exit(self):
        obj = {"a": 1, "b": [1, 2, 3]}
        raw = json.dumps(obj, indent=2, ensure_ascii=True).encode()
        with self.assertRaises(SystemExit):
            self.mod.detect_format(raw)

    def test_indent_4_non_ascii_with_trailing_newline(self):
        obj = {"name": "我爱马来了", "value": 7}
        raw = json.dumps(obj, indent=4, ensure_ascii=False).encode() + b"\n"
        self.assertEqual(self.mod.detect_format(raw), (4, False, True))

    def test_indent_1_non_ascii_no_trailing_newline_raises_system_exit(self):
        obj = {"name": "我爱马来了"}
        raw = json.dumps(obj, indent=1, ensure_ascii=False).encode()
        with self.assertRaises(SystemExit):
            self.mod.detect_format(raw)

    def test_unreproducible_format_raises_system_exit(self):
        with self.assertRaises(SystemExit):
            self.mod.detect_format(b'{"a":1}')


if __name__ == "__main__":
    unittest.main()
