"""Hermetic tests for scripts/fix_frontier_last_updated_utc.py.

Pure seam: ``main()`` bumps ``research_state/universe_frontier.json``'s
``last_updated_utc`` to ``max(now, probe_utc)`` where ``probe_utc`` is the
timestamp quoted by ``latest_archive_probe``. The non-backdating floor means the
field is never moved earlier than the probe it names. Everything here runs
against a synthetic frontier file in a temp dir (module-level ``FRONTIER``
monkeypatched) with ``datetime.now`` frozen to a fixed instant; no network, no
real frontier read/write, no frozen-artifact mutation.
"""
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts import fix_frontier_last_updated_utc as module

ROOT = Path(__file__).resolve().parents[1]

NOW = datetime(2026, 11, 14, 12, 0, 0, tzinfo=timezone.utc)
NOW_STR = "2026-11-14T12:00:00Z"


def _fixed_datetime_cls(value):
    class _FixedDatetime:
        @classmethod
        def now(cls, tz=None):
            return value

    return _FixedDatetime


class FixFrontierLastUpdatedUtcTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="fix_frontier_last_updated_", dir=ROOT))
        self.frontier = self.tmp / "universe_frontier.json"
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_frontier(self, obj):
        self.frontier.write_text(
            json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )

    def _run(self, obj):
        self._write_frontier(obj)
        with mock.patch.object(module, "FRONTIER", self.frontier), mock.patch.object(
            module, "datetime", _fixed_datetime_cls(NOW)
        ):
            return module.main()

    def _loaded(self):
        return json.loads(self.frontier.read_text(encoding="utf-8"))

    def test_probe_later_than_now_floors_to_probe(self):
        # now=2026-11-14T12:00:00Z, probe=2026-11-14T13:00:00Z -> max is probe.
        obj = {
            "last_updated_utc": "2026-11-04T22:45:00Z",
            "latest_archive_probe": {"probe_utc": "2026-11-14T13:00:00Z"},
        }
        rc = self._run(obj)
        self.assertEqual(rc, 0)
        self.assertEqual(self._loaded()["last_updated_utc"], "2026-11-14T13:00:00Z")

    def test_now_later_than_probe_uses_now(self):
        obj = {
            "last_updated_utc": "2026-11-10T00:00:00Z",
            "latest_archive_probe": {"probe_utc": "2026-11-10T00:00:00Z"},
        }
        rc = self._run(obj)
        self.assertEqual(rc, 0)
        self.assertEqual(self._loaded()["last_updated_utc"], NOW_STR)

    def test_already_current_is_noop_and_file_unchanged(self):
        obj = {
            "last_updated_utc": NOW_STR,
            "latest_archive_probe": {"probe_utc": "2026-11-10T00:00:00Z"},
        }
        before = self.frontier.write_text(
            json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        before_bytes = self.frontier.read_bytes()
        with mock.patch.object(module, "FRONTIER", self.frontier), mock.patch.object(
            module, "datetime", _fixed_datetime_cls(NOW)
        ):
            rc = module.main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.frontier.read_bytes(), before_bytes)
        self.assertEqual(self._loaded()["last_updated_utc"], NOW_STR)

    def test_missing_probe_utc_returns_one_and_no_write(self):
        obj = {"last_updated_utc": "2026-11-04T22:45:00Z"}
        self.frontier.write_text(
            json.dumps(obj, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        before_bytes = self.frontier.read_bytes()
        with mock.patch.object(module, "FRONTIER", self.frontier), mock.patch.object(
            module, "datetime", _fixed_datetime_cls(NOW)
        ):
            rc = module.main()
        self.assertEqual(rc, 1)
        self.assertEqual(self.frontier.read_bytes(), before_bytes)
        self.assertEqual(self._loaded()["last_updated_utc"], "2026-11-04T22:45:00Z")

    def test_other_content_preserved_on_write(self):
        obj = {
            "last_updated_utc": "2026-11-04T22:45:00Z",
            "latest_archive_probe": {"probe_utc": "2026-11-14T13:00:00Z"},
            "notes": ["first", "second"],
            "count": 7,
        }
        rc = self._run(obj)
        self.assertEqual(rc, 0)
        got = self._loaded()
        self.assertEqual(got["last_updated_utc"], "2026-11-14T13:00:00Z")
        self.assertEqual(got["notes"], ["first", "second"])
        self.assertEqual(got["count"], 7)

    def test_written_file_is_canonical_indent2_escaped_newline(self):
        obj = {
            "last_updated_utc": "2026-11-04T22:45:00Z",
            "latest_archive_probe": {"probe_utc": "2026-11-14T13:00:00Z"},
            "catalog": "caf\u00e9 CoinMetrics",
        }
        rc = self._run(obj)
        self.assertEqual(rc, 0)
        text = self.frontier.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"))
        self.assertIn('\n  "last_updated_utc"', text)
        # non-ASCII escaped under ensure_ascii=True
        self.assertIn("caf\\u00e9", text)
        self.assertEqual(json.loads(text)["catalog"], "caf\u00e9 CoinMetrics")

    def test_floor_never_backdates_earlier_probe(self):
        # probe earlier than current last_updated_utc must not move it back.
        obj = {
            "last_updated_utc": "2026-11-13T00:00:00Z",
            "latest_archive_probe": {"probe_utc": "2026-11-10T00:00:00Z"},
        }
        rc = self._run(obj)
        self.assertEqual(rc, 0)
        self.assertEqual(self._loaded()["last_updated_utc"], NOW_STR)


if __name__ == "__main__":
    unittest.main()