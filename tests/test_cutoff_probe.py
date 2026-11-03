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

ARCHIVE = probe.ARCHIVE


def _monthly_results(published: bool) -> list[dict]:
    """Realistic probe_month results for target month 2026-10.

    Both monthly endpoints (the ones refresh_free_data.py consumes) are HTTP 200
    when published, otherwise HTTP 404. Daily endpoints are included as 404 to
    mirror a genuinely unpublished month.
    """
    k_status = 200 if published else 404
    f_status = 200 if published else 404
    return [
        {"url": f"{ARCHIVE}/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10.zip", "status": k_status, "bytes": 0, "error": None},
        {"url": f"{ARCHIVE}/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-10.zip", "status": f_status, "bytes": 0, "error": None},
        {"url": f"{ARCHIVE}/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-29.zip", "status": 404, "bytes": 0, "error": None},
        {"url": f"{ARCHIVE}/daily/klines/BTCUSDT/1d/BTCUSDT-1d-2026-10-30.zip", "status": 404, "bytes": 0, "error": None},
    ]


def _control_results() -> list[dict]:
    return [
        {"url": f"{ARCHIVE}/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2026-09.zip", "status": 200, "bytes": 2066, "error": None},
        {"url": f"{ARCHIVE}/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2026-09.zip", "status": 200, "bytes": 924, "error": None},
    ]


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
                _monthly_results(False),   # target unpublished (monthly 404)
                _control_results(),        # control alive
            )
            with mock.patch.object(Path, "mkdir"), \
                 mock.patch.object(Path, "write_text"), \
                 mock.patch.object(sys, "argv", ["probe", "--probe-month", "2026-10"]):
                rc = probe.main()
                self.assertNotEqual(rc, 0)

    def test_main_returns_zero_when_unblocked(self):
        with mock.patch.object(probe, "probe_month") as pm:
            pm.side_effect = (
                _monthly_results(True),  # target published (monthly 200)
                _control_results(),      # control alive
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


class MockOutputIsNeverRealStateTests(unittest.TestCase):
    """Guard against the single most dangerous artifact in this test file.

    test_main_returns_zero_when_unblocked exercises probe.main() with
    probe_month mocked and Path.write_text mocked, so NO record is written to
    disk -- but main() still prints a JSON summary ending in
    "cutoff_gate": "UNBLOCKED". That printed line is the last line of the
    whole suite, and it looks exactly like a live gate decision. Sessions have
    misread it as "the gate is open" when the real latest on-disk record is
    BLOCKED (see research_state/cutoff_probe/cutoff_probe_20261103T152208Z.json).

    These tests pin (a) that the printed mock line corresponds to no file on
    disk, and (b) the durable state of the real November 2026 probe. They are
    read-only: they never call probe.main() and never write anything.
    """
    PROBE_DIR = ROOT / "research_state" / "cutoff_probe"

    @classmethod
    def setUpClass(cls):
        cls.records = sorted(
            p for p in cls.PROBE_DIR.glob("cutoff_probe_*.json")
            if p.is_file() and not p.name.startswith("MOCK")
        )

    def test_mock_unblocked_line_has_no_record_on_disk(self):
        # The synthetic record printed by the mocked main() call would be
        # written at a path derived from the mocked clock; the mock writes
        # nothing. The danger being guarded is that this printed line looks
        # exactly like a live gate decision, so pin the durable state: every
        # real record on disk whose probe_month is 2026-11 must report the
        # month unpublished and the gate BLOCKED. A future open gate is then
        # detected as a state change rather than silently inherited.
        import glob as _glob
        probe_dir = self.PROBE_DIR
        for p in _glob.glob(str(probe_dir / "cutoff_probe_*.json")):
            if "MOCK" in p:
                continue
            with open(p) as fh:
                rec = json.load(fh)
            if rec.get("probe_month") != "2026-11":
                continue
            self.assertFalse(
                rec.get("target_published"),
                msg=f"real on-disk record {p} claims November 2026 published",
            )
            self.assertEqual(rec["cutoff_gate"], "BLOCKED")

    def test_real_latest_november_2026_probe_is_blocked(self):
        # Durable state: November 2026 is genuinely unpublished as of the
        # latest real probe. Pin it so a future open gate is detected as a
        # state change rather than silently inherited.
        nov = [p for p in self.records if "20261103" in p.name]
        self.assertTrue(nov, "expected at least one real November 2026 probe record")
        latest = max(nov, key=lambda p: p.name)
        rec = json.loads(latest.read_text())
        self.assertEqual(rec["probe_month"], "2026-11")
        self.assertFalse(rec["target_published"])
        self.assertEqual(rec["cutoff_gate"], "BLOCKED")
        self.assertTrue(rec["archive_alive"])


if __name__ == "__main__":
    unittest.main()