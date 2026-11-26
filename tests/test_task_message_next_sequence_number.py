"""Durable-state guard: the task message's hand-quoted registry
``next_sequence_number`` must equal the hypothesis registry.

``research_state/agent_task_message.md`` is the first file the next agent reads,
and its "State carried in" summary answers the single most important resume
question by hand: has a new hypothesis been allocated since the last session?
It quotes ``Registry `next_sequence_number` = 57 (no new hypothesis allocated)``.
If that quote drifts from ``research_state/hypothesis_registry.json`` the next
agent either re-allocates an id that already exists (a duplicate H58) or skips
allocating one it should, while every structural guard still passes.

This is the same single-source-of-truth hazard class the suite already closes for
the task message's five frozen-artifact hashes
(``test_task_message_frozen_hashes``), its probe census
(``test_task_message_probe_evidence``) and the suite count it shares with the
handoff (``test_handoff_session_entries``). The registry value itself is pinned
to ground truth by ``test_continuous_research_contract`` and the manifest's
narrative by ``test_state_consistency``; the task message's own quote was the one
hand-written ``next_sequence_number`` narrative left unpinned.

This guard parses every `` `next_sequence_number` = <int> `` quote from the task
message, requires at least one, requires all occurrences to agree, and requires
the quoted value to equal the registry's ``next_sequence_number``. It is
read-only and stdlib-only: it parses markdown and JSON, touches no artifact and
makes no network call.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"
REGISTRY = STATE / "hypothesis_registry.json"

# `` `next_sequence_number` = <int> `` -- the backtick-wrapped field name
# immediately followed by an equals sign and an integer, the exact shape the task
# message uses. Prose that merely names the field (e.g. "the registry
# next_sequence_number is unchanged") is not a quote and must not be parsed as
# one, mirroring the prose-safety of the frozen-hash label parser.
SEQ_RE = re.compile(r"`next_sequence_number`\s*=\s*(\d+)")


def parse_quoted_sequence_numbers(text):
    """Return every integer quoted as `` `next_sequence_number` = N `` in text.

    Pure function so the guard can be exercised against synthetic text as well as
    the committed message.
    """
    return [int(n) for n in SEQ_RE.findall(text)]


def registry_next_sequence_number():
    """The registry's ground-truth ``next_sequence_number``."""
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["next_sequence_number"]


class TaskMessageNextSequenceNumberTests(unittest.TestCase):
    def test_task_message_quotes_a_next_sequence_number(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        self.assertTrue(
            parse_quoted_sequence_numbers(text),
            "task message quotes no `next_sequence_number` = N; the next agent "
            "cannot tell from the first file it reads whether a new hypothesis "
            "was allocated",
        )

    def test_every_quoted_value_agrees(self):
        """Every occurrence of the quote must carry the same integer.

        The message may quote the value in more than one place; if those copies
        drift apart the next agent cannot tell which is authoritative, the same
        single-source-of-truth hazard the frozen-hash label guard pins.
        """
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_quoted_sequence_numbers(text)
        self.assertTrue(quoted, "task message quotes no next_sequence_number")
        self.assertEqual(
            len(set(quoted)), 1,
            f"task message quotes conflicting next_sequence_number values: "
            f"{sorted(set(quoted))}",
        )

    def test_quoted_value_matches_registry(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_quoted_sequence_numbers(text)
        self.assertTrue(quoted, "task message quotes no next_sequence_number")
        actual = registry_next_sequence_number()
        self.assertEqual(
            set(quoted), {actual},
            f"task message quotes next_sequence_number {sorted(set(quoted))}; "
            f"registry holds {actual}",
        )

    def test_helper_flags_a_synthetic_drift(self):
        """The parser/comparison must actually reject a wrong value.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that silently accepts everything. This exercises the same helpers against
        synthetic text carrying a bogus value and requires the mismatch to be
        visible, mirroring the frozen-hash self-test.
        """
        actual = registry_next_sequence_number()
        bogus = actual + 1

        good_text = (
            f"Registry `next_sequence_number` = {actual} "
            "(no new hypothesis allocated)."
        )
        bad_text = (
            f"Registry `next_sequence_number` = {bogus} "
            "(no new hypothesis allocated)."
        )

        self.assertEqual(parse_quoted_sequence_numbers(good_text), [actual])
        self.assertEqual(parse_quoted_sequence_numbers(bad_text), [bogus])
        self.assertEqual(set(parse_quoted_sequence_numbers(good_text)), {actual})
        self.assertNotEqual(set(parse_quoted_sequence_numbers(bad_text)), {actual})

        # Prose that names the field without the `= N` shape is not a quote.
        self.assertEqual(
            parse_quoted_sequence_numbers(
                "the registry next_sequence_number is unchanged"
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()