"""Durable-state guard: the task message's hand-quoted hard date gate must equal
the maturity-timeline audit's November-2026 vintage cutoff.

``research_state/agent_task_message.md`` is the first file the next agent reads,
and its "Initial task for next agent" section answers the single most important
resume question by hand: *which calendar date do I hold for before executing
Option A?* It quotes the gate as ``hard date gate 2026-11-30`` and repeats the
execution trigger as ``on/after 2026-11-30`` / ``At/after 2026-11-30``.

That date is not free-floating: it is the last complete November-2026 daily
candle, derived from the committed merged panel index as
``last_observed_date + 30 days`` (2026-10-31 -> 2026-11-30) by
``scripts/h10_maturity_timeline_audit.py`` and reported as
``milestones.november_2026_vintage.cutoff_date``. The committed-disk verdict pin
(``test_h10_maturity_timeline_audit_committed``) already holds that computed value
to ``2026-11-30``, but nothing held the task message's own hand-written quote to
it. If a future session advanced the data vintage (moving ``last_observed_date``
and therefore the November cutoff) or rewrote the gate phrase, the task message
could still say ``2026-11-30`` while the audit's ground truth moved, and the next
agent would hold for the wrong date -- the same single-source-of-truth hazard the
suite already closes for the task message's frozen hashes
(``test_task_message_frozen_hashes``), its probe census
(``test_task_message_probe_evidence``), its registry sequence number
(``test_task_message_next_sequence_number``) and the suite count it shares with the
handoff (``test_handoff_session_entries``).

This guard re-derives the November-2026 vintage cutoff from the REAL committed
artifacts via the audit module's own pure helpers, parses every ``date gate <date>``
quote and every ``on/after <date>`` / ``at/after <date>`` execution trigger from the
task message, requires the gate quotes to agree, requires any execution trigger to
equal the gate, and requires the gate to equal the audit's computed cutoff. It is
read-only and stdlib-only (the audit module imports no numpy/pandas): it parses
markdown and JSON and reads the committed klines panel, touches no artifact and
makes no network call.
"""
from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"
SPEC_PATH = ROOT / "scripts" / "h10_maturity_timeline_audit.py"

# ``date gate <YYYY-MM-DD>`` -- matches the task message's ``hard date gate
# 2026-11-30`` (the regex anchors on the ``date gate`` substring, so the leading
# ``hard`` is irrelevant) and rejects ``gate_date_required`` (underscore, not a
# space) and prose like ``the gate is reached``.
GATE_RE = re.compile(r"date gate\s+(\d{4}-\d{2}-\d{2})", re.I)

# ``on/after <date>`` / ``at/after <date>`` -- the execution-trigger phrasing the
# task message uses for when Option A becomes runnable. Kept separate from the gate
# quote so a trigger that drifts from the gate is caught even when the gate quote
# itself is correct.
TRIGGER_RE = re.compile(r"(?:on/after|at/after)\s+(\d{4}-\d{2}-\d{2})", re.I)


def parse_gate_dates(text):
    """Return every ``date gate <YYYY-MM-DD>`` date quoted in text (in order).

    Pure function so the guard can be exercised against synthetic text as well as
    the committed message.
    """
    return GATE_RE.findall(text)


def parse_trigger_dates(text):
    """Return every ``on/after`` / ``at/after`` execution-trigger date in text."""
    return TRIGGER_RE.findall(text)


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("h10_maturity_gate_date_guard", SPEC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _reanchor_paths(mod):
    """Point the audit module's path constants at ROOT-anchored absolute paths."""
    art = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    mod.ARTIFACT_DIR = art
    mod.FRESH_BLOCK_PATH = art / "forward_block_h10_fresh" / "forward_block_evaluation.json"
    mod.PANEL_DIR = art / "data" / "panels"
    mod.KLINES_BTC_PATH = mod.PANEL_DIR / "binance_klines_BTCUSDT.csv"
    mod.CANONICAL_BLOCK_PATH = art / "forward_block" / "forward_block_evaluation.json"
    mod.GRID_LEDGER_PATH = art / "grid_result_ledger.json"
    mod.UNIVERSE_FRONTIER_PATH = ROOT / "research_state" / "universe_frontier.json"
    mod.GRID_CONFIG_PATH = ROOT / "configs" / "dispersion_momentum_grid_v3.json"
    mod.EVAL_SRC_PATH = ROOT / "scripts" / "eval_forward_block.py"


class TaskMessageGateDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load_audit_module()
        _reanchor_paths(cls.mod)
        required = [cls.mod.FRESH_BLOCK_PATH, cls.mod.KLINES_BTC_PATH]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls.fresh = cls.mod.load_json(cls.mod.FRESH_BLOCK_PATH)
        cls.all_dates = cls.mod.kline_dates_in_window(
            cls.mod.KLINES_BTC_PATH, "0000-00-00", "9999-99-99"
        )
        cls.block_start = str(cls.fresh["forward_block_start"])
        cls.block_start_index = cls.all_dates.index(cls.block_start)
        cls.last_observed_index = len(cls.all_dates) - 1
        cls.last_date = cls.all_dates[-1]
        cls.ms = cls.mod.compute_maturity_milestones(
            block_start=cls.block_start,
            last_observed_date=cls.last_date,
            block_start_index=cls.block_start_index,
            last_observed_index=cls.last_observed_index,
        )
        cls.nov_cutoff = cls.ms["november_2026_vintage"]["cutoff_date"]

    def test_task_message_quotes_a_gate_date(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        self.assertTrue(
            parse_gate_dates(text),
            "task message quotes no 'date gate <YYYY-MM-DD>'; the next agent "
            "cannot tell from the first file it reads which calendar date to hold "
            "for before executing Option A",
        )

    def test_every_gate_quote_agrees(self):
        """Every ``date gate`` occurrence must carry the same date.

        The message may quote the gate in more than one place; if those copies
        drift apart the next agent cannot tell which is authoritative, the same
        single-source-of-truth hazard the frozen-hash label guard pins.
        """
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_gate_dates(text)
        self.assertTrue(quoted, "task message quotes no gate date")
        self.assertEqual(
            len(set(quoted)), 1,
            f"task message quotes conflicting gate dates: {sorted(set(quoted))}",
        )

    def test_gate_date_matches_audit_november_vintage_cutoff(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_gate_dates(text)
        self.assertTrue(quoted, "task message quotes no gate date")
        self.assertEqual(
            set(quoted), {self.nov_cutoff},
            f"task message quotes hard date gate {sorted(set(quoted))}; the "
            f"maturity-timeline audit derives the November-2026 vintage cutoff "
            f"{self.nov_cutoff} from the committed panel "
            f"(last_observed_date {self.last_date} + 30 days)",
        )

    def test_execution_triggers_match_the_gate_date(self):
        """Any ``on/after`` / ``at/after`` trigger must equal the gate date.

        The execution trigger is when Option A becomes runnable; if it drifts from
        the gate the next agent either runs Option A before the gate or holds past
        it. A message with no trigger phrasing is allowed (the gate quote is the
        essential claim), but any trigger that is present must agree.
        """
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        gate = set(parse_gate_dates(text))
        self.assertTrue(gate, "task message quotes no gate date")
        triggers = parse_trigger_dates(text)
        if triggers:
            self.assertEqual(
                set(triggers), gate,
                f"task message execution triggers {sorted(set(triggers))} disagree "
                f"with the quoted gate date {sorted(gate)}",
            )

    def test_helper_flags_a_synthetic_drift(self):
        """The parser/comparison must actually reject a wrong date.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that silently accepts everything. This exercises the same helpers against
        synthetic text carrying a bogus date and requires the mismatch to be
        visible, mirroring the frozen-hash / sequence-number self-tests.
        """
        good = "Hold for the hard date gate 2026-11-30; run on/after 2026-11-30."
        bad = "Hold for the hard date gate 2026-12-31; run on/after 2026-12-31."

        self.assertEqual(parse_gate_dates(good), ["2026-11-30"])
        self.assertEqual(parse_trigger_dates(good), ["2026-11-30"])
        self.assertEqual(parse_gate_dates(bad), ["2026-12-31"])
        self.assertEqual(parse_trigger_dates(bad), ["2026-12-31"])

        # A trigger that disagrees with the gate is visible to the comparison.
        mixed = "hard date gate 2026-11-30; run At/after 2026-12-01."
        self.assertEqual(parse_gate_dates(mixed), ["2026-11-30"])
        self.assertEqual(parse_trigger_dates(mixed), ["2026-12-01"])
        self.assertNotEqual(
            set(parse_trigger_dates(mixed)), set(parse_gate_dates(mixed))
        )

        # Prose that names the gate without a date is not a quote.
        self.assertEqual(parse_gate_dates("the gate is reached soon"), [])
        # ``gate_date_required`` (underscore) is not a ``date gate`` quote.
        self.assertEqual(parse_gate_dates("gate_date_required: 2026-10-29"), [])


if __name__ == "__main__":
    unittest.main()