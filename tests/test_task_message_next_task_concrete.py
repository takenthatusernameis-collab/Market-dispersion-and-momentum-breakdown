"""Durable-state guard: the task message's next task must be concrete, never a
bare "wait for a new experiment ID".

The continuous-research operating contract
(``prompts/continuous_research_operating_contract_v1.md``, "Continuous execution
and recovery") and ``AGENTS.md`` both forbid writing "await a new experiment ID"
/ "wait for a new experiment ID" as the next task: the program must always carry
a concrete, executable next action (recover a checkpoint, expand the frontier,
repair a source gate, run grid cells, red-team, preregister a candidate, or
update durable state). ``research_state/agent_task_message.md`` is the first file
the next agent reads; if its "Initial task for next agent" section degenerates
into a bare wait-for-an-experiment-ID, the program stalls silently while every
structural guard still passes.

This guard parses the "Initial task for next agent" section and requires it to
carry a concrete next action -- an explicit ISO calendar date (``YYYY-MM-DD``)
or a backticked ``python3 scripts/...`` command -- and forbids an un-negated
"wait/await ... experiment id" directive. It is read-only and stdlib-only: it
parses markdown, touches no artifact and makes no network call.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_MESSAGE = ROOT / "research_state" / "agent_task_message.md"

SECTION_HEADING_RE = re.compile(r"^##\s+Initial task for next agent\s*$", re.M)
NEXT_HEADING_RE = re.compile(r"^##\s+", re.M)
DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
SCRIPT_CMD_RE = re.compile(r"`python3\s+scripts/[A-Za-z0-9_./-]+\.py")
BARE_WAIT_RE = re.compile(
    r"\b(?:wait|waiting|await|awaiting)\b[^.\n]{0,60}?\bexperiment[ _-]?id\b",
    re.I,
)
NEGATION_RE = re.compile(r"\b(?:do not|don't|never|not|no|cannot|can't)\b", re.I)


def initial_task_section(text):
    """Return the body of the '## Initial task for next agent' section, or None."""
    match = SECTION_HEADING_RE.search(text)
    if not match:
        return None
    rest = text[match.end():]
    nxt = NEXT_HEADING_RE.search(rest)
    return rest[: nxt.start()] if nxt else rest


def has_concrete_action(section):
    """True when the section names a hard date or a `python3 scripts/...` command."""
    return bool(DATE_RE.search(section) or SCRIPT_CMD_RE.search(section))


def unnegated_bare_waits(section):
    """Return each 'wait/await ... experiment id' match not negated in its sentence.

    A directive such as "Do not wait for a new experiment ID" is a negation, not
    a bare wait, so it is allowed; only an un-negated wait is reported.
    """
    out = []
    for match in BARE_WAIT_RE.finditer(section):
        start = max(
            section.rfind(".", 0, match.start()),
            section.rfind("\n", 0, match.start()),
        )
        prefix = section[start + 1 : match.start()]
        if not NEGATION_RE.search(prefix):
            out.append(match.group(0))
    return out


class TaskMessageNextTaskConcreteTests(unittest.TestCase):
    def test_initial_task_section_exists(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        self.assertIsNotNone(
            initial_task_section(text),
            "task message has no '## Initial task for next agent' section",
        )

    def test_initial_task_is_concrete(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        section = initial_task_section(text)
        self.assertTrue(
            has_concrete_action(section),
            "Initial task carries no concrete next action (no ISO date and no "
            "`python3 scripts/...` command); the contract forbids a bare "
            "'wait for a new experiment ID' next task",
        )

    def test_initial_task_is_not_a_bare_experiment_id_wait(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        section = initial_task_section(text)
        self.assertEqual(
            unnegated_bare_waits(section), [],
            "Initial task contains an un-negated 'wait/await ... experiment id' "
            "directive, which the operating contract forbids as the next task",
        )

    def test_helper_flags_a_synthetic_bare_wait(self):
        """The helpers must reject a bare wait and accept a concrete/negated one."""
        bare = "Next: wait for a new experiment ID before doing anything."
        self.assertFalse(has_concrete_action(bare))
        self.assertTrue(unnegated_bare_waits(bare))

        concrete = (
            "Hold for the hard date gate 2026-11-30; then run "
            "`python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`."
        )
        self.assertTrue(has_concrete_action(concrete))
        self.assertEqual(unnegated_bare_waits(concrete), [])

        negated = "Do not wait for a new experiment ID; run the frontier audit instead."
        self.assertEqual(unnegated_bare_waits(negated), [])


if __name__ == "__main__":
    unittest.main()