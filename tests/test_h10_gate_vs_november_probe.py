"""Guard against the H10 cutoff gate being conflated with the November 2026 probe.

The H10 gate_date_required is 2026-10-29, so it is satisfied by the PUBLISHED
October 2026 Binance archive. The November 2026 probe is a separate question
(whether the pipeline can refresh far enough to give the fresh block enough
formations); its 404s do NOT re-block the H10 gate.

A session once carried the durable handoff's "Remaining gate is date-gated
cutoff probe" / "Cutoff: cutoff_gate=BLOCKED for probe_month=2026-11" wording,
which reads as if the H10 gate itself is blocked by November. That is a
single-source-of-truth hazard: the November BLOCKED verdict and the H10
UNBLOCKED verdict are both real, both on disk, and both quotable -- only the
wrong one had been promoted into the gate decision. Every check compared
hashes and test counts, never the two verdicts against each other.

This gate pins the distinction so a future handoff rewrite cannot collapse it
back: the H10 gate is decided by the latest published-month record, and the
November probe is recorded separately and never promoted.
"""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
PROBE_DIR = STATE / "cutoff_probe"

H10_GATE_DATE_REQUIRED = "2026-10-29"


def _real_records():
    """Every committed, non-MOCK cutoff probe record on disk."""
    out = []
    for p in sorted(PROBE_DIR.glob("cutoff_probe_*.json")):
        if "MOCK" in p.name:
            continue
        out.append((p, json.loads(p.read_text(encoding="utf-8"))))
    return out


def _latest_published_record():
    """Latest on-disk record whose target month is actually published (HTTP 200
    on both monthly endpoints). Returns (path, record) or (None, None)."""
    best = None
    for path, rec in _real_records():
        if not rec.get("target_published"):
            continue
        if best is None or rec["probe_utc"] > best[1]["probe_utc"]:
            best = (path, rec)
    return best if best else (None, None)


class H10GateIsDecidedByPublishedMonthTests(unittest.TestCase):
    def test_october_2026_archive_is_published_and_unblocks_h10(self):
        """Ground truth: the October 2026 archive is published, so the H10 gate
        is UNBLOCKED. This is not a mock -- it reads the real records on disk."""
        oct_records = [
            (p, r) for p, r in _real_records()
            if r.get("probe_month") == "2026-10" and r.get("target_published")
        ]
        self.assertGreater(
            len(oct_records), 0,
            "expected at least one real on-disk record showing the October 2026 "
            "archive published (the H10 gate date is 2026-10-29)",
        )
        for _p, r in oct_records:
            self.assertEqual(r["cutoff_gate"], "UNBLOCKED")
            self.assertTrue(r["gate_met_by_month_end"])
            self.assertTrue(r["archive_alive"])

    def test_h10_gate_date_required_is_october_2029(self):
        self.assertEqual(H10_GATE_DATE_REQUIRED, "2026-10-29")

    def test_latest_published_record_unblocks_h10(self):
        path, rec = _latest_published_record()
        self.assertIsNotNone(path, "no published-month record found on disk")
        self.assertEqual(rec["cutoff_gate"], "UNBLOCKED")
        self.assertGreaterEqual(rec["probe_month"], "2026-10")

    def test_november_2026_probe_does_not_reblock_h10(self):
        """The November 2026 probe may be BLOCKED and still be true; the H10 gate
        is decided by the published month, so a November BLOCKED must not be
        promoted into the H10 gate verdict."""
        nov = [
            (p, r) for p, r in _real_records()
            if r.get("probe_month") == "2026-11"
        ]
        if not nov:
            self.skipTest("no November 2026 probe records on disk yet")
        _path, rec = _latest_published_record()
        self.assertEqual(rec["cutoff_gate"], "UNBLOCKED",
                         "H10 gate must remain UNBLOCKED regardless of the "
                         "November 2026 probe result")

    def test_durable_state_does_not_call_the_h10_gate_blocked(self):
        """The durable handoff and task message must not assert that the H10
        cutoff gate is BLOCKED. They may (and should) report the November 2026
        probe as BLOCKED, but only as a separate, clearly labelled probe -- never
        as the gate decision."""
        for name in ("agent_handoff.md", "agent_task_message.md"):
            with self.subTest(source=name):
                text = (STATE / name).read_text(encoding="utf-8")
                # The gate decision must not be asserted blocked anywhere.
                self.assertNotIn("cutoff_gate=BLOCKED", text)
                # And the November probe must be reported as a probe, not a gate.
                if "2026-11" in text:
                    self.assertIn("probe_month=2026-11", text)


if __name__ == "__main__":
    unittest.main()