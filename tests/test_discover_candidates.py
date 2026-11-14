"""Hermetic unit tests for scripts/discover_candidates.py.

Covers deterministic/pure seams: constants, module exports, and now_utc format.
No network access (cm_get_json / walk_catalog / main are not invoked).
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "discover_candidates.py"


def _load():
    spec = importlib.util.spec_from_file_location("discover_candidates_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestDiscoverCandidatesConstants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_coinmetrics_catalog_endpoint(self):
        self.assertEqual(
            self.mod.CM_BASE,
            "https://community-api.coinmetrics.io/v4/reference-data/assets",
        )

    def test_frontier_path(self):
        self.assertTrue(str(self.mod.FRONTIER_PATH).endswith(
            "research_state/universe_frontier.json"
        ))

    def test_rate_limit_and_retry_params_sane(self):
        self.assertEqual(self.mod.REQUEST_TIMEOUT, 30)
        self.assertGreaterEqual(self.mod.MAX_RETRIES, 1)
        self.assertGreater(self.mod.BACKOFF_BASE, 1.0)
        self.assertGreater(self.mod.POLL_SLEEP, 0)

    def test_expected_exports_exist(self):
        for name in ("now_utc", "cm_get_json", "walk_catalog", "main"):
            self.assertTrue(callable(getattr(self.mod, name)), name)


class TestNowUtc(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_now_utc_format(self):
        ts = self.mod.now_utc()
        self.assertRegex(ts, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
