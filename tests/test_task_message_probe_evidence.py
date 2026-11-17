"""Durable-state guard: the task message's quoted probe census must match disk.

``research_state/agent_task_message.md`` carries a hand-written "Probe evidence
(disk)" line and a "Recompute probe counts from disk" rule that quote the
cutoff-probe census. Those quotes are the only place the next session reads the
census without recomputing it, so a quote that drifts from
``research_state/cutoff_probe/`` is a single-source-of-truth hazard exactly like
the stale session-verification pointer and the drifted test-claim narrative this
suite already guards.

A 2026-11-17 session rewrote the task message's probe line to claim all 397 real
probes were ``probe_month=2026-11`` / 0 published with newest
``cutoff_probe_20261108T232421Z.json``, while the directory actually held 270
``probe_month=2026-10`` (49 published) and 127 ``probe_month=2026-11`` (0
published) and the newest record was ``cutoff_probe_20261113T091257Z.json``. No
test compared the quoted census to disk, so the wrong quote shipped while the
handoff body carried the correct one -- the durable state contradicted itself.

This guard recomputes the census from ``research_state/cutoff_probe/`` and
requires the quoted total, every per-month count, and the newest filename to
agree. It is read-only and stdlib-only: it parses the markdown and the probe
records and touches no artifact and makes no network call.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
PROBE_DIR = STATE / "cutoff_probe"
TASK_MESSAGE = STATE / "agent_task_message.md"

# Canonical quote shapes. The task message writes, e.g.:
#   397 real `cutoff_probe_*.json` (270 `probe_month=2026-10` / 49 published, ...)
#   ..., newest `cutoff_probe_20261113T091257Z.json`.
TOTAL_RE = re.compile(r"(\d+) real `cutoff_probe_\*\.json`")
MONTH_RE = re.compile(r"(\d+) `probe_month=(\d{4}-\d{2})` / (\d+) published")
NEWEST_RE = re.compile(r"newest `([^`]+)`")
RECOMPUTE_PREFIX = "Recompute probe counts from disk"


def _real_records():
    """Every committed, non-MOCK cutoff probe record on disk (sorted by name)."""
    return sorted(
        p for p in PROBE_DIR.glob("cutoff_probe_*.json") if "MOCK" not in p.name
    )


def _disk_census():
    """Independently recompute (total, {month: (count, published)}, newest_name)."""
    counts = {}
    files = _real_records()
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        month = data.get("probe_month")
        entry = counts.setdefault(month, [0, 0])
        entry[0] += 1
        if data.get("target_published"):
            entry[1] += 1
    newest = files[-1].name if files else None
    return len(files), {m: tuple(v) for m, v in counts.items()}, newest


def _parse_census(text):
    """Parse (total, {month: (count, published)}, newest) from a block of text.

    Returns ``None`` when any component is missing, so a missing or malformed
    quote fails the caller with a clear assertion rather than a parse crash.
    """
    total_match = TOTAL_RE.search(text)
    newest_match = NEWEST_RE.search(text)
    if total_match is None or newest_match is None:
        return None
    months = {m: (int(c), int(p)) for c, m, p in MONTH_RE.findall(text)}
    return int(total_match.group(1)), months, newest_match.group(1)


def _line_with(prefix):
    for line in TASK_MESSAGE.read_text(encoding="utf-8").splitlines():
        if prefix in line:
            return line
    return None


class TaskMessageProbeEvidenceTests(unittest.TestCase):
    def test_task_message_quotes_a_probe_evidence_line(self):
        line = _line_with("Probe evidence (disk)")
        self.assertIsNotNone(
            line,
            "agent_task_message.md carries no 'Probe evidence (disk)' line",
        )
        self.assertIsNotNone(
            _parse_census(line),
            f"could not parse a total/months/newest census from: {line!r}",
        )

    def test_probe_evidence_line_matches_disk_census(self):
        line = _line_with("Probe evidence (disk)")
        self.assertIsNotNone(line, "agent_task_message.md carries no probe evidence line")
        parsed = _parse_census(line)
        self.assertIsNotNone(parsed, f"unparseable probe evidence line: {line!r}")
        total, months, newest = parsed
        disk_total, disk_months, disk_newest = _disk_census()

        self.assertEqual(
            total, disk_total,
            f"probe evidence line quotes {total} real probes; disk has {disk_total}",
        )
        self.assertEqual(
            months, disk_months,
            f"probe evidence line per-month counts {months} disagree with disk "
            f"{disk_months}",
        )
        self.assertEqual(
            newest, disk_newest,
            f"probe evidence line names newest {newest!r}; disk newest is "
            f"{disk_newest!r}",
        )

    def test_recompute_rule_line_matches_disk_census(self):
        line = _line_with(RECOMPUTE_PREFIX)
        self.assertIsNotNone(
            line,
            f"agent_task_message.md carries no '{RECOMPUTE_PREFIX}' rule line",
        )
        parsed = _parse_census(line)
        self.assertIsNotNone(
            parsed,
            f"could not parse a census from the recompute rule line: {line!r}",
        )
        total, months, newest = parsed
        disk_total, disk_months, disk_newest = _disk_census()

        self.assertEqual(
            total, disk_total,
            f"recompute rule quotes {total} real files; disk has {disk_total}",
        )
        self.assertEqual(
            months, disk_months,
            f"recompute rule per-month counts {months} disagree with disk {disk_months}",
        )
        self.assertEqual(
            newest, disk_newest,
            f"recompute rule names newest {newest!r}; disk newest is {disk_newest!r}",
        )


if __name__ == "__main__":
    unittest.main()