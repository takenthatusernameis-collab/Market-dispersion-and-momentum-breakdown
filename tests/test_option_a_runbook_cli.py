"""Durable-state guard: the Option A runbook command must match the real CLI.

On the hard date gate (2026-11-30) the next agent executes Option A by pasting
the commands recorded in ``research_state/agent_task_message.md`` verbatim:

    python3 scripts/probe_cutoff_gate.py --probe-month 2026-11
    python3 scripts/eval_forward_block.py --forward-block-start 2026-09-30 \
        --data-cutoff <new cutoff> \
        --output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/

Those two commands are the single gate-day shot: if ``eval_forward_block.py``
renames or drops a flag (``--forward-block-start``, ``--data-cutoff``,
``--output-dir``) or ``probe_cutoff_gate.py`` renames ``--probe-month``, the
pasted command aborts with an argparse error and the one unblocked session is
spent on a usage message instead of the fresh sealed block. That is a
single-source-of-truth hazard exactly like the stale session-verification
pointer and the drifted probe census this suite already guards: the runbook
quotes flags by hand while the scripts own the truth.

This guard re-parses the argparse flags from the real script sources and
requires every ``--flag`` quoted in a ``python3 scripts/...`` runbook span to be
a registered argument. It also pins the two safety invariants of the Option A
command: the fresh block is written to ``forward_block_h10_fresh/`` and never to
the canonical ``forward_block/`` directory, and the fresh-block start is
``2026-09-30`` (after the 2026-09-30 canonical cutoff).

Read-only, stdlib-only: it parses markdown and python source text, touches no
artifact, makes no network call and modifies nothing.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"

# Inline-code spans that invoke a repo script, e.g.
#   `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
SPAN_RE = re.compile(r"`(python3 scripts/[^`]+)`")
SCRIPT_RE = re.compile(r"(scripts/[A-Za-z0-9_]+\.py)")
FLAG_RE = re.compile(r"--[a-z0-9][a-z0-9-]*")
ARGPARSE_RE = re.compile(r"add_argument\(\s*['\"](--[a-z0-9-]+)['\"]")

CANONICAL_DIR = "forward_block/"
FRESH_DIR = "forward_block_h10_fresh/"


def _runbook_spans():
    """Return [(script_relpath, span_text)] for every `python3 scripts/...` span."""
    out = []
    for span in SPAN_RE.findall(TASK_MESSAGE.read_text(encoding="utf-8")):
        match = SCRIPT_RE.search(span)
        if match:
            out.append((match.group(1), span))
    return out


def _registered_flags(script_relpath):
    """Every long option registered via ``add_argument('--flag', ...)`` in a script."""
    src = (ROOT / script_relpath).read_text(encoding="utf-8")
    return set(ARGPARSE_RE.findall(src))


def _flag_tokens(span_text):
    """Every ``--flag`` token quoted in a runbook span (values are not flags)."""
    return set(FLAG_RE.findall(span_text))


class OptionARunbookCliGuardTests(unittest.TestCase):
    def test_task_message_carries_the_two_option_a_scripts(self):
        scripts = {rel for rel, _span in _runbook_spans()}
        self.assertIn(
            "scripts/probe_cutoff_gate.py", scripts,
            "agent_task_message.md Option A no longer quotes the probe_cutoff_gate.py command",
        )
        self.assertIn(
            "scripts/eval_forward_block.py", scripts,
            "agent_task_message.md Option A no longer quotes the eval_forward_block.py command",
        )

    def test_every_runbook_flag_is_a_registered_cli_argument(self):
        spans = _runbook_spans()
        self.assertGreater(len(spans), 0, "no `python3 scripts/...` runbook span found")
        for rel, span in spans:
            registered = _registered_flags(rel)
            self.assertGreater(
                len(registered), 0,
                f"could not parse any add_argument flags from {rel}",
            )
            for flag in _flag_tokens(span):
                with self.subTest(script=rel, flag=flag):
                    self.assertIn(
                        flag, registered,
                        f"runbook quotes {flag} for {rel}, which is not a registered "
                        f"CLI argument (registered: {sorted(registered)}); the gate-day "
                        f"command would abort with an argparse error",
                    )

    def test_eval_runbook_seals_fresh_block_not_canonical(self):
        """The fresh H10 block must go to forward_block_h10_fresh/, never the
        canonical forward_block/ that every audit treats as read-only evidence."""
        eval_spans = [s for rel, s in _runbook_spans() if rel == "scripts/eval_forward_block.py"]
        self.assertGreater(len(eval_spans), 0, "no eval_forward_block.py runbook span")
        for span in eval_spans:
            with self.subTest(span=span):
                self.assertIn("--output-dir", span)
                self.assertIn(FRESH_DIR, span)
                # The canonical directory must not be the --output-dir target. The
                # prose "(never `forward_block/`)" legitimately names it, so strip
                # that annotation before asserting the canonical dir is absent.
                guard = span.replace("never `forward_block/`", "")
                self.assertNotIn(
                    "--output-dir artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/" + CANONICAL_DIR,
                    guard,
                    "runbook points the fresh-block --output-dir at the canonical "
                    "forward_block/ directory",
                )
                self.assertIn("--forward-block-start 2026-09-30", span)
                self.assertIn("--data-cutoff", span)

    def test_probe_runbook_targets_november_2026(self):
        probe_spans = [s for rel, s in _runbook_spans() if rel == "scripts/probe_cutoff_gate.py"]
        self.assertGreater(len(probe_spans), 0, "no probe_cutoff_gate.py runbook span")
        for span in probe_spans:
            with self.subTest(span=span):
                self.assertIn("--probe-month 2026-11", span)

    def test_guard_helper_flags_a_synthetic_drift(self):
        """The flag-coverage helper must actually reject an unregistered flag.

        The committed-runbook test above passes only because the real runbook is
        clean; on its own it could not distinguish a working guard from one that
        silently accepts everything. This exercises the same logic against a
        synthetic span carrying a bogus ``--no-such-flag`` and requires it to be
        reported as unregistered, mirroring the dangling-index helper self-test.
        """
        registered = _registered_flags("scripts/probe_cutoff_gate.py")
        synthetic_span = "python3 scripts/probe_cutoff_gate.py --probe-month 2026-11 --no-such-flag"
        tokens = _flag_tokens(synthetic_span)
        self.assertIn("--no-such-flag", tokens)
        self.assertNotIn("--no-such-flag", registered,
                         "synthetic drift guard is self-blind: bogus flag is registered")
        self.assertIn("--probe-month", tokens)
        self.assertIn("--probe-month", registered)


if __name__ == "__main__":
    unittest.main()