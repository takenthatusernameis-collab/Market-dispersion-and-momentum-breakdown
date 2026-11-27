"""Durable-state guard: the task message's frontier-exhaustion claim must match
the committed ``-003`` re-audit AND the live universe frontier.

``research_state/agent_task_message.md`` is the first file the next agent reads.
Its "State carried in" summary answers the resume question "is there any
unblocked discovery/expansion task left?" by hand:

    ... frontier catalog exhausted per the 2026-11-25 -003 re-audit
    (220 verified + 6127 blocked = 6347 walked, 0 newly discovered), so no
    unblocked discovery/expansion task exists before a new data vintage.

That sentence is load-bearing: it is the sole justification for why a pre-gate
session must NOT go looking for a new candidate to validate and should instead
do bounded audit/test work. If the quoted counts drift from the committed
re-audit artifact (``research_state/FRONTIER_INTEGRITY_REAUDIT_20261125T014120Z.json``,
audit_id ``DISP-003-FRONTIER-INTEGRITY-003``) or from the live
``research_state/universe_frontier.json``, the next agent would either chase a
discovery task that does not exist or skip one that does -- the same
single-source-of-truth hazard this suite already closes for the task message's
frozen hashes (``test_task_message_frozen_hashes``), its probe census
(``test_task_message_probe_evidence``), its registry ``next_sequence_number``
(``test_task_message_next_sequence_number``), its hard date gate
(``test_task_message_gate_date``) and the guard total it shares with the handoff
(``test_task_message_guard_count``).

This guard parses the quoted ``verified``/``blocked``/``walked``/``newly
discovered`` counts and the ``<date> -<seq> re-audit`` reference from the task
message, requires the internal arithmetic (``verified + blocked == walked``) to
hold, requires the quoted numbers and re-audit date to equal the committed
re-audit artifact's ``checks`` block and ``verdict == PASS``, and requires the
same numbers to equal the live frontier's ``candidates_verified`` /
``candidates_blocked`` / ``catalog_discovery`` counts. It is read-only and
stdlib-only: it parses markdown and JSON, touches no artifact and makes no
network call.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"
FRONTIER = STATE / "universe_frontier.json"

# The claim lives on the line that contains this anchor phrase.
CLAIM_ANCHOR = "frontier catalog exhausted"

# ``<N> verified`` / ``<N> blocked`` / ``<N> walked`` / ``<N> newly discovered``.
VERIFIED_RE = re.compile(r"(\d+) verified")
BLOCKED_RE = re.compile(r"(\d+) blocked")
WALKED_RE = re.compile(r"(\d+) walked")
NEWLY_RE = re.compile(r"(\d+) newly discovered")
# ``2026-11-25 -003 re-audit`` -- the date and zero-padded sequence of the audit.
REAUDIT_REF_RE = re.compile(r"(\d{4}-\d{2}-\d{2})\s+-(\d{3})\s+re-audit")


def _claim_line(text):
    """Return the single task-message line carrying the exhaustion claim, or None."""
    for line in text.splitlines():
        if CLAIM_ANCHOR in line:
            return line
    return None


def parse_exhaustion(text):
    """Parse the exhaustion claim from text.

    Returns ``(verified, blocked, walked, newly, reaudit_date, reaudit_seq)`` or
    ``None`` when any component is missing, so a missing/malformed quote fails
    the caller with a clear assertion rather than a parse crash. Pure function so
    the guard can be exercised against synthetic text as well as the committed
    message.
    """
    line = _claim_line(text)
    if line is None:
        return None
    verified = VERIFIED_RE.search(line)
    blocked = BLOCKED_RE.search(line)
    walked = WALKED_RE.search(line)
    newly = NEWLY_RE.search(line)
    reaudit = REAUDIT_REF_RE.search(line)
    if not (verified and blocked and walked and newly and reaudit):
        return None
    return (
        int(verified.group(1)),
        int(blocked.group(1)),
        int(walked.group(1)),
        int(newly.group(1)),
        reaudit.group(1),
        reaudit.group(2),
    )


def _load_reeaudit(seq):
    """Load the committed re-audit artifact whose audit_id ends ``-<seq>``.

    Locates the artifact by audit_id (``DISP-003-FRONTIER-INTEGRITY-<seq>``)
    rather than a hard-coded filename, so renaming the timestamp stem does not
    silently break the guard. Returns ``(path, data)`` or ``(None, None)``.
    """
    target = f"DISP-003-FRONTIER-INTEGRITY-{seq}"
    for path in sorted(STATE.glob("FRONTIER_INTEGRITY_REAUDIT_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("audit_id") == target:
            return path, data
    return None, None


class TaskMessageFrontierExhaustionTests(unittest.TestCase):
    def test_task_message_quotes_an_exhaustion_claim(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        self.assertIsNotNone(
            _claim_line(text),
            f"agent_task_message.md carries no '{CLAIM_ANCHOR}' line; the next "
            "agent cannot tell from the first file it reads whether any "
            "unblocked discovery task remains",
        )
        self.assertIsNotNone(
            parse_exhaustion(text),
            "could not parse verified/blocked/walked/newly counts and the re-audit "
            "reference from the exhaustion claim",
        )

    def test_internal_arithmetic_is_consistent(self):
        parsed = parse_exhaustion(TASK_MESSAGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(parsed, "task message has no parseable exhaustion claim")
        verified, blocked, walked, _newly, _date, _seq = parsed
        self.assertEqual(
            verified + blocked, walked,
            f"quoted verified ({verified}) + blocked ({blocked}) != walked ({walked})",
        )

    def test_claim_matches_committed_reeaudit_artifact(self):
        parsed = parse_exhaustion(TASK_MESSAGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(parsed, "task message has no parseable exhaustion claim")
        verified, blocked, walked, newly, date, seq = parsed
        path, data = _load_reeaudit(seq)
        self.assertIsNotNone(
            path,
            f"no committed FRONTIER_INTEGRITY_REAUDIT artifact with audit_id "
            f"DISP-003-FRONTIER-INTEGRITY-{seq}",
        )
        checks = data["checks"]
        self.assertEqual(checks["verified_count"], verified)
        self.assertEqual(checks["blocked_count"], blocked)
        self.assertEqual(checks["catalog_entries_walked"], walked)
        self.assertEqual(checks["newly_discovered"], newly)
        self.assertEqual(data.get("verdict"), "PASS")
        # The quoted re-audit date must be the artifact's own UTC date. The
        # artifact timestamp is the compact ``YYYYMMDDTHHMMSSZ`` form, so the
        # date is its first eight characters.
        self.assertEqual(data["timestamp_utc"][:8], date.replace("-", ""))

    def test_claim_matches_live_universe_frontier(self):
        parsed = parse_exhaustion(TASK_MESSAGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(parsed, "task message has no parseable exhaustion claim")
        verified, blocked, walked, newly, _date, _seq = parsed
        frontier = json.loads(FRONTIER.read_text(encoding="utf-8"))
        self.assertEqual(len(frontier["candidates_verified"]), verified)
        self.assertEqual(len(frontier["candidates_blocked"]), blocked)
        catalog = frontier["catalog_discovery"]
        self.assertEqual(catalog["catalog_entries_walked"], walked)
        self.assertEqual(catalog["newly_discovered"], newly)

    def test_helper_flags_a_synthetic_drift(self):
        """The parser/comparison must actually reject a wrong count.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that silently accepts everything. This exercises the same helper against
        synthetic text carrying a bogus count and requires the mismatch to be
        visible, mirroring the frozen-hash / gate-date self-tests.
        """
        good = (
            "frontier catalog exhausted per the 2026-11-25 -003 re-audit "
            "(220 verified + 6127 blocked = 6347 walked, 0 newly discovered)"
        )
        bad = (
            "frontier catalog exhausted per the 2026-11-25 -003 re-audit "
            "(221 verified + 6127 blocked = 6347 walked, 0 newly discovered)"
        )
        parsed_good = parse_exhaustion(good)
        parsed_bad = parse_exhaustion(bad)
        self.assertEqual(parsed_good[:4], (220, 6127, 6347, 0))
        self.assertEqual(parsed_good[4:], ("2026-11-25", "003"))
        # A wrong verified count is parsed faithfully so the comparison would fail.
        self.assertEqual(parsed_bad[0], 221)
        self.assertNotEqual(parsed_good[0], parsed_bad[0])
        # Prose that names no counts is not a claim.
        self.assertIsNone(parse_exhaustion("frontier catalog exhausted soon"))
        # A claim with no re-audit reference is not parseable.
        self.assertIsNone(
            parse_exhaustion("frontier catalog exhausted (220 verified + 6127 blocked)")
        )


if __name__ == "__main__":
    unittest.main()