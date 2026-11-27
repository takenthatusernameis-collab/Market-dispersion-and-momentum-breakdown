"""Durable-state guard: the task message's hand-quoted hard-constraint literals
must equal the source constants that own them.

``research_state/agent_task_message.md`` is the first file the next agent reads.
Its "Initial task for next agent" and "Hard constraints" sections answer the
load-bearing resume question by hand: *which feasibility constants must I never
relax when I run Option A?* They quote, in prose:

    do NOT relax 30-day maturity, the trailing-decile state rule,
    `MIN_ASSETS_DECILES=20`, or the per-look `alpha_k = 0.05/(k*(k+1))` rule

Those four literals are not free-floating narrative: each is owned by exactly one
source constant --

  * ``MIN_ASSETS_DECILES = 20``                in scripts/eval_forward_block.py
  * ``rule: str = "alpha_k = 0.05 / (k * (k + 1))"``
                                               in scripts/alpha_spending.py
  * ``FORWARD_HORIZON_DAYS = 30``              in scripts/h10_maturity_timeline_audit.py
  * ``"dispersion_state_rule": "trailing_window_outer_deciles"``
                                               in scripts/eval_forward_block.py

If a future session changed one of those source constants (or rewrote the quoted
phrase in the task message) the two would silently disagree, and the next agent
would either relax a real constraint or hold to a stale one -- the same
single-source-of-truth hazard this suite already closes for the task message's
frozen hashes (``test_task_message_frozen_hashes``), its probe census
(``test_task_message_probe_evidence``), its registry sequence number
(``test_task_message_next_sequence_number``), its gate date
(``test_task_message_gate_date``) and the suite count it shares with the handoff
(``test_handoff_session_entries``).

This guard parses the quoted literals from the task message and the owning
constants from the real script sources (text only -- it never imports
eval_forward_block, which needs numpy/pandas, so it runs dep-light and cannot
introduce look-ahead) and requires them to agree. Whitespace is normalised
before comparison so the task message's compact ``0.05/(k*(k+1))`` matches the
source's spaced ``0.05 / (k * (k + 1))``. Read-only and stdlib-only: it parses
markdown and python source text, touches no artifact and makes no network call.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"
EVAL_SRC_PATH = ROOT / "scripts" / "eval_forward_block.py"
ALPHA_SRC_PATH = ROOT / "scripts" / "alpha_spending.py"
MATURITY_SRC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

# ``MIN_ASSETS_DECILES=20`` (the task message writes it without spaces).
MIN_ASSETS_RE = re.compile(r"MIN_ASSETS_DECILES\s*=\s*(\d+)")
# ``30-day maturity`` -- the leading integer is the forward horizon in days.
HORIZON_MATURITY_RE = re.compile(r"(\d+)-day\s+maturity", re.I)
# ``alpha_k = 0.05/(k*(k+1))`` -- capture through the closing paren; whitespace
# is stripped before comparison so the compact and spaced forms agree.
ALPHA_RULE_RE = re.compile(r"alpha_k\s*=\s*0\.05\s*/\s*\(\s*k\s*\*\s*\(\s*k\s*\+\s*1\s*\)\s*\)")
# The trailing-decile state rule is named in prose; the source owns the canonical
# value ``trailing_window_outer_deciles``.
STATE_RULE_PHRASE = "trailing-decile state rule"
STATE_RULE_SOURCE_RE = re.compile(
    r'"dispersion_state_rule"\s*:\s*"([a-z_]+)"'
)

# Source-side constant extractors.
SRC_MIN_ASSETS_RE = re.compile(r"^MIN_ASSETS_DECILES\s*=\s*(\d+)\s*$", re.M)
SRC_HORIZON_RE = re.compile(r"^FORWARD_HORIZON_DAYS\s*=\s*(\d+)\s*$", re.M)
SRC_ALPHA_RULE_RE = re.compile(r'rule:\s*str\s*=\s*"([^"]+)"')


def _strip_ws(text):
    """Remove all whitespace so compact and spaced rule forms compare equal."""
    return re.sub(r"\s+", "", text)


def parse_task_min_assets(text):
    """Return the integer after ``MIN_ASSETS_DECILES=`` in the task message."""
    match = MIN_ASSETS_RE.search(text)
    return int(match.group(1)) if match else None


def parse_task_horizon_maturity(text):
    """Return the integer before ``-day maturity`` in the task message."""
    match = HORIZON_MATURITY_RE.search(text)
    return int(match.group(1)) if match else None


def parse_task_alpha_rule(text):
    """Return the whitespace-stripped ``alpha_k = 0.05/(k*(k+1))`` literal."""
    match = ALPHA_RULE_RE.search(text)
    return _strip_ws(match.group(0)) if match else None


def task_names_state_rule(text):
    """True when the task message names the trailing-decile state rule in prose."""
    return STATE_RULE_PHRASE in text


def source_min_assets(src):
    match = SRC_MIN_ASSETS_RE.search(src)
    return int(match.group(1)) if match else None


def source_horizon(src):
    match = SRC_HORIZON_RE.search(src)
    return int(match.group(1)) if match else None


def source_alpha_rule(src):
    match = SRC_ALPHA_RULE_RE.search(src)
    return _strip_ws(match.group(1)) if match else None


def source_state_rule(src):
    match = STATE_RULE_SOURCE_RE.search(src)
    return match.group(1) if match else None


class TaskMessageHardConstraintLiteralsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.task = TASK_MESSAGE.read_text(encoding="utf-8")
        cls.eval_src = EVAL_SRC_PATH.read_text(encoding="utf-8")
        cls.alpha_src = ALPHA_SRC_PATH.read_text(encoding="utf-8")
        cls.maturity_src = MATURITY_SRC_PATH.read_text(encoding="utf-8")

    def test_task_message_quotes_all_four_literals(self):
        self.assertIsNotNone(
            parse_task_min_assets(self.task),
            "task message quotes no `MIN_ASSETS_DECILES=<n>` hard constraint",
        )
        self.assertIsNotNone(
            parse_task_horizon_maturity(self.task),
            "task message quotes no `<n>-day maturity` hard constraint",
        )
        self.assertIsNotNone(
            parse_task_alpha_rule(self.task),
            "task message quotes no `alpha_k = 0.05/(k*(k+1))` hard constraint",
        )
        self.assertTrue(
            task_names_state_rule(self.task),
            "task message does not name the trailing-decile state rule",
        )

    def test_min_assets_matches_source(self):
        quoted = parse_task_min_assets(self.task)
        actual = source_min_assets(self.eval_src)
        self.assertIsNotNone(actual, "eval_forward_block.py declares no MIN_ASSETS_DECILES")
        self.assertEqual(
            quoted, actual,
            f"task message quotes MIN_ASSETS_DECILES={quoted} but "
            f"eval_forward_block.py owns MIN_ASSETS_DECILES = {actual}",
        )

    def test_horizon_maturity_matches_source(self):
        quoted = parse_task_horizon_maturity(self.task)
        actual = source_horizon(self.maturity_src)
        self.assertIsNotNone(
            actual, "h10_maturity_timeline_audit.py declares no FORWARD_HORIZON_DAYS"
        )
        self.assertEqual(
            quoted, actual,
            f"task message quotes {quoted}-day maturity but the maturity audit owns "
            f"FORWARD_HORIZON_DAYS = {actual}",
        )

    def test_alpha_rule_matches_source(self):
        quoted = parse_task_alpha_rule(self.task)
        actual = source_alpha_rule(self.alpha_src)
        self.assertIsNotNone(
            actual, "alpha_spending.py declares no AlphaSpendResult.rule default"
        )
        self.assertEqual(
            quoted, actual,
            f"task message quotes alpha rule {quoted!r} but alpha_spending.py owns "
            f"rule default {actual!r} (whitespace-normalised)",
        )

    def test_state_rule_source_value_is_the_trailing_outer_decile_rule(self):
        actual = source_state_rule(self.eval_src)
        self.assertEqual(
            actual, "trailing_window_outer_deciles",
            "eval_forward_block.py ANCHOR_PARAMS.dispersion_state_rule must remain "
            "the trailing outer-decile rule the task message names",
        )
        self.assertTrue(
            task_names_state_rule(self.task),
            "task message must keep naming the trailing-decile state rule that "
            f"eval_forward_block.py owns as {actual!r}",
        )

    def test_helper_flags_a_synthetic_drift(self):
        """The helpers must reject a wrong literal, not silently accept anything.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that accepts everything. This exercises the same helpers against
        synthetic text carrying wrong values and requires each mismatch visible,
        mirroring the frozen-hash / gate-date self-tests.
        """
        good = (
            "do NOT relax 30-day maturity, the trailing-decile state rule, "
            "`MIN_ASSETS_DECILES=20`, or the per-look `alpha_k = 0.05/(k*(k+1))` rule"
        )
        self.assertEqual(parse_task_min_assets(good), 20)
        self.assertEqual(parse_task_horizon_maturity(good), 30)
        self.assertEqual(parse_task_alpha_rule(good), "alpha_k=0.05/(k*(k+1))")
        self.assertTrue(task_names_state_rule(good))

        # A wrong min-assets literal is parsed faithfully so the comparison fails.
        bad_assets = good.replace("MIN_ASSETS_DECILES=20", "MIN_ASSETS_DECILES=25")
        self.assertEqual(parse_task_min_assets(bad_assets), 25)
        self.assertNotEqual(parse_task_min_assets(bad_assets), source_min_assets(self.eval_src))

        # A wrong horizon literal is visible.
        bad_horizon = good.replace("30-day maturity", "14-day maturity")
        self.assertEqual(parse_task_horizon_maturity(bad_horizon), 14)
        self.assertNotEqual(
            parse_task_horizon_maturity(bad_horizon), source_horizon(self.maturity_src)
        )

        # A wrong alpha rule is visible after whitespace normalisation.
        bad_alpha = good.replace(
            "alpha_k = 0.05/(k*(k+1))", "alpha_k = 0.10/(k*(k+1))"
        )
        self.assertEqual(parse_task_alpha_rule(bad_alpha), "alpha_k=0.10/(k*(k+1))")
        self.assertNotEqual(parse_task_alpha_rule(bad_alpha), source_alpha_rule(self.alpha_src))

        # The spaced source form and the compact message form normalise equal.
        self.assertEqual(
            source_alpha_rule(self.alpha_src), parse_task_alpha_rule(good),
            "whitespace-normalised source rule and message rule must agree",
        )

        # Prose that omits a literal is not a quote.
        self.assertIsNone(parse_task_min_assets("never relax the decile rule"))
        self.assertIsNone(parse_task_horizon_maturity("never relax maturity"))
        self.assertIsNone(parse_task_alpha_rule("never relax the alpha rule"))
        self.assertFalse(task_names_state_rule("never relax the state rule"))


if __name__ == "__main__":
    unittest.main()