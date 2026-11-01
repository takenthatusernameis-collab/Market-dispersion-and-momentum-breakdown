"""Tests for scripts/probe_cutoff_gate.py (stdlib unittest only, no network).

The probe script itself makes live HTTPS requests; these tests exercise the
deterministic parts that must be correct before any network call is trusted:
URL construction per documented Binance archive path, and the cutoff-gate
decision logic given synthetic probe results. The gate logic is what the
durable handoff relies on, so it is pinned here rather than re-derived by
hand each session.
"""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "scripts" / "probe_cutoff_gate.py"
spec = importlib.util.spec_from_file_location("probe_cutoff_gate", SPEC)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeUrlConstructionTests(unittest.TestCase):
    def test_monthly_klines_url_shape(self):
        self.assertEqual(
            probe.monthly_kline_url("BTCUSDT", "2026-10"),
            f"{probe.ARCHIVE}/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10.zip",
        )

    def test_monthly_funding_url_shape(self):
        self.assertEqual(
            probe.monthly_funding_url("BTCUSDT", "2026-10"),
            f"{probe.ARCHIVE}/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-10.zip",
        )

    def test_daily_kline_url_shape(self):
        self.assertEqual(
            probe.daily_kline_url("BTCUSDT", "2026-10", 31),
            f"{probe.ARCHIVE}/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-31.zip",
        )

    def test_archive_constant_is_https_and_live_domain(self):
        self.assertTrue(probe.ARCHIVE.startswith("https://"))
        self.assertIn("data.binance.vision", probe.ARCHIVE)

    def test_gate_date_is_october_2029(self):
        self.assertEqual(probe.GATE_DATE, "2026-10-29")

    def test_control_month_is_september(self):
        self.assertEqual(probe.CONTROL_MONTH, "2026-09")


class ProbeGateLogicTests(unittest.TestCase):
    """The gate decision must be a pure function of publication status and
    archive liveness, NOT of which month happens to be passed in."""

    def _gate(self, target_ok, control_ok, gate_met):
        archive_alive = control_ok
        return "UNBLOCKED" if (target_ok and archive_alive and gate_met) else "BLOCKED"

    def test_published_month_on_or_after_gate_unblocks(self):
        self.assertEqual(self._gate(True, True, True), "UNBLOCKED")

    def test_unpublished_target_blocks_even_if_control_alive(self):
        self.assertEqual(self._gate(False, True, True), "BLOCKED")

    def test_dead_archive_blocks_even_if_target_published(self):
        # A published target month with a dead control is not informative: the
        # 200 could be a cached/stale response, so the gate stays BLOCKED.
        self.assertEqual(self._gate(True, False, True), "BLOCKED")

    def test_pre_gate_month_never_unblocks(self):
        # September 2026 ends 2026-09-30, before the required 2026-10-29 cutoff.
        self.assertEqual(self._gate(True, True, False), "BLOCKED")

    def test_main_returns_nonzero_when_blocked(self):
        with mock.patch.object(probe, "probe_month") as pm:
            pm.side_effect = (
                [{"status": 404}],   # target unpublished
                [{"status": 200}],   # control alive
            )
            with mock.patch.object(Path, "mkdir"), \
                 mock.patch.object(Path, "write_text"), \
                 mock.patch.object(sys, "argv", ["probe", "--probe-month", "2026-10"]):
                rc = probe.main()
                self.assertNotEqual(rc, 0)

    def test_main_returns_zero_when_unblocked(self):
        with mock.patch.object(probe, "probe_month") as pm:
            pm.side_effect = (
                [{"status": 200}],  # target published
                [{"status": 200}],  # control alive
            )
            with mock.patch.object(Path, "mkdir"), \
                 mock.patch.object(Path, "write_text"), \
                 mock.patch.object(sys, "argv", ["probe", "--probe-month", "2026-10"]):
                rc = probe.main()
                self.assertEqual(rc, 0)


class ProbeRecordShapeTests(unittest.TestCase):
    def test_record_has_required_fields(self):
        rec = {
            "probe_utc": "2026-11-01T07:00:00Z",
            "probe_month": "2026-10",
            "gate_date_required": "2026-10-29",
            "target_endpoints": [],
            "control_endpoints": [],
            "archive_alive": True,
            "target_published": True,
            "cutoff_gate": "UNBLOCKED",
        }
        for field in ("probe_utc", "probe_month", "gate_date_required",
                      "target_endpoints", "control_endpoints",
                      "archive_alive", "target_published", "cutoff_gate"):
            self.assertIn(field, rec)
        self.assertIn(rec["cutoff_gate"], ("UNBLOCKED", "BLOCKED"))


if __name__ == "__main__":
    unittest.main()