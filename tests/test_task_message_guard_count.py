"""Durable-state guard: the task message's hand-quoted durable-state guard
count must equal the actual number of tests in the modules it names.

``research_state/agent_task_message.md`` is the first file the next agent reads.
Its "State carried in" summary answers the resume question "are the durable-state
guards green?" by hand:

    durable-state guards `tests.test_handoff_session_entries` + ... +
    `tests.test_task_message_gate_date` -> 55/55 OK

That ``N/N`` is a hand-summed count over an explicit, hand-typed module list. It
is the same single-source-of-truth hazard class this suite already closes for the
task message's five frozen-artifact hashes (``test_task_message_frozen_hashes``),
its probe census (``test_task_message_probe_evidence``), the registry
``next_sequence_number`` (``test_task_message_next_sequence_number``) and the
suite count it shares with the handoff (``test_handoff_session_entries``): a
hand-written narrative that drifts from ground truth while every structural guard
still passes.

This hazard is not hypothetical. The 2026-11-26T20:19:24Z session added
``tests/test_task_message_gate_date.py`` (5 tests) to a 45-test base and wrote
``55/55`` -- but the six modules it listed actually held 50 tests; the ``55``
was the *seven*-module total that also includes
``tests/test_task_message_frozen_hashes``, which the list omitted. The count and
the list silently disagreed, and no test compared either to reality.

This guard parses the module list and the ``N/N`` from the task message, imports
exactly those modules, counts the tests ``unittest`` would run in them, and
requires the quoted numerator and denominator to equal that actual count. It also
requires the handoff's newest session entry to quote the same ``N/N`` (mirroring
the suite-count cross-check), so the two durable narratives cannot disagree on
the guard total. It is read-only and stdlib-only: it parses markdown, imports
local test modules and counts their test methods; it touches no artifact and
makes no network call.
"""
import importlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"
HANDOFF = STATE / "agent_handoff.md"

# ``durable-state guards `...` + ... + `tests.x` -> N/N OK`` -- the module list is
# captured non-greedily up to the ``-> N/N OK`` verdict so trailing prose after
# the verdict is not swallowed.
GUARD_CLAUSE_RE = re.compile(
    r"durable-state guards\s+(?P<mods>.+?)\s*->\s*(?P<num>\d+)\s*/\s*(?P<den>\d+)\s*OK"
)
# `` `tests.<module>` `` -- the backtick-wrapped module names the clause lists.
MODULE_RE = re.compile(r"`(tests\.[A-Za-z0-9_]+)`")
# Handoff newest entry: ``durable-state guards N/N`` (the handoff drops the
# ``->`` and ``OK`` and writes ``durable-state guards 55/55 (seven-module set...)``).
HANDOFF_GUARD_RE = re.compile(r"durable-state guards?\s+(\d+)\s*/\s*(\d+)")
# A level-2 session heading (``## Session summary -- ...`` / ``## Previous
# session -- ...``); the newest entry body runs from the first such heading to
# the next one (or EOF).
ENTRY_HEADING_RE = re.compile(r"^## (?:Session summary|Previous session) — ")


def parse_guard_clause(text):
    """Return ``(modules, num, den)`` from the task message, or ``None``.

    ``modules`` is the ordered list of ``tests.<module>`` names the clause lists;
    ``num``/``den`` are the quoted numerator/denominator. Pure function so the
    guard can be exercised against synthetic text as well as the committed
    message.
    """
    match = GUARD_CLAUSE_RE.search(text)
    if not match:
        return None
    modules = MODULE_RE.findall(match.group("mods"))
    return modules, int(match.group("num")), int(match.group("den"))


def count_tests_in_modules(module_names):
    """Number of test methods ``unittest`` would run across ``module_names``.

    Mirrors ``unittest.TestLoader.getTestCaseNames`` (the same count
    ``python3 -m unittest`` reports as ``Ran N tests``) without running any test.
    Raises ``AssertionError`` with a clear message if a module cannot be imported
    or contributes no tests, so a typo in the task message's module list fails
    loudly rather than silently under-counting.
    """
    loader = unittest.TestLoader()
    total = 0
    for name in module_names:
        try:
            module = importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - surface any import failure
            raise AssertionError(
                f"task message names durable-state guard module {name!r}, which "
                f"cannot be imported: {exc}"
            )
        module_total = 0
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, unittest.TestCase)
                and obj is not unittest.TestCase
            ):
                module_total += len(loader.getTestCaseNames(obj))
        if module_total == 0:
            raise AssertionError(
                f"task message names durable-state guard module {name!r}, which "
                "contributes no unittest test cases"
            )
        total += module_total
    return total


def newest_handoff_entry_body(text):
    """Return the body text of the newest (first) session entry in the handoff.

    The body is the text after the first ``## Session summary/Previous session``
    heading up to (not including) the next session heading or EOF. Older entries
    legitimately quote older guard totals (``45/45``, ``41/41`` ...), so the
    cross-check must read only the newest entry.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if ENTRY_HEADING_RE.match(line):
            start = i + 1
            break
    if start is None:
        return ""
    body = []
    for line in lines[start:]:
        if ENTRY_HEADING_RE.match(line):
            break
        body.append(line)
    return "\n".join(body)


def parse_handoff_guard_count(text):
    """Return ``(num, den)`` quoted in the newest handoff entry, or ``None``."""
    match = HANDOFF_GUARD_RE.search(newest_handoff_entry_body(text))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


class TaskMessageGuardCountTests(unittest.TestCase):
    def test_task_message_quotes_a_guard_count(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        parsed = parse_guard_clause(text)
        self.assertIsNotNone(
            parsed,
            "task message carries no 'durable-state guards ... -> N/N OK' clause",
        )
        modules, num, den = parsed
        self.assertTrue(
            modules,
            "task message's durable-state guard clause names no `tests.<module>`",
        )
        self.assertEqual(num, den, "guard clause numerator != denominator")

    def test_quoted_count_matches_actual_tests(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        parsed = parse_guard_clause(text)
        self.assertIsNotNone(parsed, "task message has no guard-count clause")
        modules, num, den = parsed
        actual = count_tests_in_modules(modules)
        self.assertEqual(
            num, actual,
            f"task message quotes {num} durable-state guard tests but the listed "
            f"modules {modules} actually hold {actual}",
        )
        self.assertEqual(
            den, actual,
            f"task message quotes denominator {den} but the listed modules "
            f"{modules} actually hold {actual}",
        )

    def test_handoff_newest_entry_quotes_same_guard_count(self):
        task = parse_guard_clause(TASK_MESSAGE.read_text(encoding="utf-8"))
        self.assertIsNotNone(task, "task message has no guard-count clause")
        handoff = parse_handoff_guard_count(HANDOFF.read_text(encoding="utf-8"))
        self.assertIsNotNone(
            handoff,
            "handoff newest session entry quotes no 'durable-state guards N/N'",
        )
        self.assertEqual(
            handoff, (task[1], task[2]),
            f"handoff newest entry quotes guard count {handoff} but task message "
            f"quotes {(task[1], task[2])}; both durable narratives must agree",
        )

    def test_helper_flags_a_synthetic_drift(self):
        """The helpers must reject a wrong count and a bogus module.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that silently accepts everything. This exercises the same helpers against
        synthetic text carrying a wrong count and a non-existent module and
        requires both to be visible, mirroring the frozen-hash self-test.
        """
        modules, num, den = parse_guard_clause(
            "durable-state guards `tests.test_task_message_gate_date` -> 5/5 OK"
        )
        self.assertEqual(modules, ["tests.test_task_message_gate_date"])
        actual = count_tests_in_modules(modules)
        self.assertEqual(num, actual)
        self.assertEqual(den, actual)

        # A wrong numerator is parsed faithfully so the comparison would fail.
        wrong = parse_guard_clause(
            "durable-state guards `tests.test_task_message_gate_date` -> 6/6 OK"
        )
        self.assertEqual(wrong[1], 6)
        self.assertNotEqual(wrong[1], actual)

        # A non-existent module fails loudly rather than under-counting.
        with self.assertRaises(AssertionError):
            count_tests_in_modules(["tests.does_not_exist_xyz"])

        # Prose that names no module is not a clause.
        self.assertIsNone(parse_guard_clause("durable-state guards are green"))


if __name__ == "__main__":
    unittest.main()