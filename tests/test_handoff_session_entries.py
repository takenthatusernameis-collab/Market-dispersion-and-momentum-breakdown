"""Durable-state guard: the handoff's session log must stay a well-formed,
append-only narrative.

The durable handoff is a stack of session entries: one `## Session summary --
<ts> (this session)` at the top followed by `## Previous session -- <ts>`
blocks, newest first. The 2026-11-13T17:46:23Z handoff update broke that shape:
it inserted its own summary at the top but left a second copy of the *same*
timestamp labelled `## Previous session -- 2026-11-13T17:46:23Z`, and the
retained 16:55:25Z block was headed `## Session summary -- ... (previous
session)` instead of `## Previous session -- ...`. The duplicated block carried
the same session-verification filename as the real one, so every existence-based
pointer guard still passed; only a structural check on the entry headings can
catch it. A handoff that lists one session twice makes the "latest session"
ambiguous for the next agent, which is exactly the single-source-of-truth
hazard these guards exist to prevent.

Read-only, stdlib-only: parses the handoff text and asserts entry structure.
Makes no network call and touches no artifact.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
HANDOFF = STATE / "agent_handoff.md"

TITLE_RE = re.compile(r"^# Agent Handoff — (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \(current session\)$")
ENTRY_RE = re.compile(
    r"^## (Session summary|Previous session) — "
    r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)"
    r"( \(this session\))?$"
)
VERIFY_RE = re.compile(r"session_verify_2026\d{8}T\d{6}Z\.json")


def _entries():
    """Return [(kind, timestamp, is_this_session, line_number)] for every session
    heading in the handoff, in file order."""
    out = []
    for lineno, line in enumerate(
        HANDOFF.read_text(encoding="utf-8").splitlines(), start=1
    ):
        match = ENTRY_RE.match(line)
        if match:
            out.append(
                (match.group(1), match.group(2), match.group(3) is not None, lineno)
            )
    return out


class HandoffSessionEntryStructureTests(unittest.TestCase):
    def test_handoff_has_session_entries(self):
        self.assertGreater(len(_entries()), 1, "handoff carries no session entries")

    def test_exactly_one_this_session_entry(self):
        marked = [e for e in _entries() if e[2]]
        self.assertEqual(
            len(marked), 1,
            f"expected exactly one '(this session)' entry, found {len(marked)}: {marked}",
        )

    def test_this_session_entry_is_the_newest_and_matches_title(self):
        entries = _entries()
        self.assertTrue(entries[0][2], "the first session entry must be '(this session)'")
        self.assertEqual(entries[0][0], "Session summary")
        text = HANDOFF.read_text(encoding="utf-8")
        title = TITLE_RE.match(text.splitlines()[0])
        self.assertIsNotNone(title, "handoff title is not '# Agent Handoff — <ts> (current session)'")
        self.assertEqual(
            title.group(1), entries[0][1],
            "title timestamp disagrees with the newest session entry",
        )

    def test_session_timestamps_are_unique(self):
        """A session may not appear twice, even under different heading labels.

        The 2026-11-13T17:46:23Z handoff update listed that timestamp as both
        'Session summary' and 'Previous session', giving the next agent two
        different 'latest' narratives for one session."""
        timestamps = [e[1] for e in _entries()]
        duplicates = sorted({ts for ts in timestamps if timestamps.count(ts) > 1})
        self.assertEqual(
            duplicates, [],
            f"handoff lists these session timestamps more than once: {duplicates}",
        )

    def test_only_the_newest_entry_is_marked_this_session(self):
        for kind, ts, is_this, lineno in _entries()[1:]:
            with self.subTest(timestamp=ts, line=lineno):
                self.assertFalse(is_this, f"line {lineno}: older entry marked '(this session)'")
                self.assertEqual(kind, "Previous session",
                                 f"line {lineno}: older entry is not a 'Previous session' block")

    def test_entries_are_in_strictly_descending_time_order(self):
        timestamps = [e[1] for e in _entries()]
        self.assertEqual(
            timestamps, sorted(timestamps, reverse=True),
            "handoff session entries are not ordered newest-first",
        )

    def test_handoff_quotes_the_newest_session_verification_record(self):
        """The handoff must name the newest session verification record on disk.

        A handoff that points at an older record while a newer verification
        exists sends the next agent to stale evidence; the dangling-pointer
        guard only checks that quoted names exist, not that the newest one is
        quoted."""
        records = sorted(STATE.glob("session_verifications/session_verify_*.json"))
        self.assertGreater(len(records), 0, "no session verification records found")
        newest = records[-1].name
        self.assertIn(
            newest, HANDOFF.read_text(encoding="utf-8"),
            f"handoff does not quote the newest session verification record {newest}",
        )


if __name__ == "__main__":
    unittest.main()