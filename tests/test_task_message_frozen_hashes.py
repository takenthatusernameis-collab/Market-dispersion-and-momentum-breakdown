"""Durable-state guard: the task message's hand-quoted frozen hashes must match disk.

``research_state/agent_task_message.md`` is the first file the next agent reads.
Its "State carried in" and "Frozen hashes" bullets quote five frozen-artifact
sha256 values by hand and then instruct the gate-day agent to "verify the five
frozen hashes byte-unchanged vs disk AND git blob". Those five quotes are the
cheat-sheet the agent verifies *against*; if one is a typo, the agent either
chases a phantom drift on a byte-identical file or, worse, accepts a real drift
because it compared against the wrong expected value.

Every other hand-quoted narrative in the durable state is already pinned to
ground truth by this suite -- the canonical sha256 in the frontier / manifest /
registry (``test_durable_state_quotes_canonical_block_sha256``), the probe
census (``test_task_message_probe_evidence``), the suite count
(``test_handoff_session_entries``), the newest session-verify pointer
(``test_state_consistency``) and the Option A runbook flags
(``test_option_a_runbook_cli``). The task message's own five-hash summary was
the one hand-written quote left unpinned: a single-source-of-truth hazard of
exactly the same class, on the one line the next agent trusts first.

This guard parses the five labelled ``<label> `<64-hex>` `` quotes from the task
message and requires each to equal the sha256 recomputed from disk (and from the
committed git blob). It is read-only and stdlib-only: it parses markdown and
re-hashes local files, touches no artifact and makes no network call.
"""
import hashlib
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
TASK_MESSAGE = STATE / "agent_task_message.md"

# Label (as written in the task message) -> repository-relative file whose
# sha256 the label quotes. The labels are the exact backtick-preceded words the
# message uses: ``canonical `...```; ``h10_fresh `...```; ``grid_result_ledger
# `...```; ``grid v3 config `...```; ``frontier `...```.
LABELED_FILES = {
    "canonical": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
    "h10_fresh": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json",
    "grid_result_ledger": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json",
    "grid v3 config": "configs/dispersion_momentum_grid_v3.json",
    "frontier": "research_state/universe_frontier.json",
}

# ``<label> `<64 lowercase hex>``` -- the label must be immediately followed by a
# backtick-wrapped 64-hex digest, so prose like "frontier catalog exhausted" or
# "never `forward_block/`" cannot masquerade as a hash quote.
LABEL_RE = re.compile(
    r"(canonical|h10_fresh|grid_result_ledger|grid v3 config|frontier) `([0-9a-f]{64})`"
)


def parse_labeled_hashes(text):
    """Return ``{label: [hash, ...]}`` for every labelled 64-hex quote in text.

    A label may be quoted more than once (the task message quotes the set in
    both its "State carried in" summary and its "Frozen hashes" reference
    bullet); every occurrence is collected in file order so the caller can
    require the occurrences to agree. Pure function so the guard can be
    exercised against synthetic text as well as the committed message.
    """
    out = {}
    for label, digest in LABEL_RE.findall(text):
        out.setdefault(label, []).append(digest)
    return out


def sha256_file(path):
    """sha256 of the file's bytes at ``path`` (disk ground truth)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_git_blob(rel_path):
    """sha256 of the committed blob ``HEAD:<rel_path>`` (git ground truth)."""
    proc = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"],
        cwd=ROOT, capture_output=True,
    )
    if proc.returncode != 0:
        raise AssertionError(
            f"git show HEAD:{rel_path} failed: {proc.stderr.decode()}"
        )
    return hashlib.sha256(proc.stdout).hexdigest()


class TaskMessageFrozenHashGuardTests(unittest.TestCase):
    def test_task_message_quotes_all_five_frozen_hashes(self):
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_labeled_hashes(text)
        missing = [label for label in LABELED_FILES if label not in quoted]
        self.assertEqual(
            missing, [],
            f"task message quotes no hash for these frozen artifacts: {missing}; "
            "the gate-day 'verify the five frozen hashes' step has nothing to "
            "verify against",
        )

    def test_each_label_quotes_a_single_consistent_hash(self):
        """Every occurrence of a label must quote the same digest.

        The message quotes the set twice (summary + reference bullet). If those
        two copies drift apart, the agent cannot tell which is authoritative --
        the same single-source-of-truth hazard the suite guards elsewhere.
        """
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_labeled_hashes(text)
        for label in LABELED_FILES:
            if label not in quoted:
                continue  # reported by the completeness test above
            with self.subTest(label=label):
                self.assertEqual(
                    len(set(quoted[label])), 1,
                    f"task message quotes conflicting {label} hashes: "
                    f"{sorted(set(quoted[label]))}",
                )

    def test_quoted_hashes_match_disk(self):
        """Each quoted hash must equal the sha256 recomputed from disk."""
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_labeled_hashes(text)
        for label, rel in LABELED_FILES.items():
            if label not in quoted:
                continue
            disk = sha256_file(ROOT / rel)
            with self.subTest(label=label):
                self.assertEqual(
                    set(quoted[label]), {disk},
                    f"task message quotes {label} {sorted(set(quoted[label]))}; "
                    f"disk {rel} is {disk}",
                )

    def test_quoted_hashes_match_committed_git_blob(self):
        """Each quoted hash must also equal the committed ``HEAD:`` blob.

        The task message tells the agent to verify the hashes "byte-unchanged vs
        disk AND git blob"; this pins the git half so a quote that matches a
        locally-modified file but not the committed frozen artifact still fails.
        """
        text = TASK_MESSAGE.read_text(encoding="utf-8")
        quoted = parse_labeled_hashes(text)
        for label, rel in LABELED_FILES.items():
            if label not in quoted:
                continue
            blob = sha256_git_blob(rel)
            with self.subTest(label=label):
                self.assertEqual(
                    set(quoted[label]), {blob},
                    f"task message quotes {label} {sorted(set(quoted[label]))}; "
                    f"committed HEAD:{rel} is {blob}",
                )

    def test_helper_flags_a_synthetic_drift(self):
        """The parser/comparison must actually reject a wrong hash.

        The committed-message tests above pass only because the real message is
        clean; on their own they could not distinguish a working guard from one
        that silently accepts everything. This exercises the same helpers
        against synthetic text carrying a bogus digest and requires the mismatch
        to be visible, mirroring the dangling-index and runbook-flag self-tests.
        """
        real = sha256_file(ROOT / LABELED_FILES["canonical"])
        bogus = "0" * 64
        self.assertNotEqual(real, bogus)

        good_text = f"canonical `{real}`"
        bad_text = f"canonical `{bogus}`"

        good = parse_labeled_hashes(good_text)
        bad = parse_labeled_hashes(bad_text)
        # Parser extracts the labelled digest in both cases.
        self.assertEqual(good["canonical"], [real])
        self.assertEqual(bad["canonical"], [bogus])
        # The good quote matches disk; the bogus one does not.
        self.assertEqual(set(good["canonical"]), {real})
        self.assertNotEqual(set(bad["canonical"]), {real})

        # A label with no backtick-hash is not parsed as a quote (prose safety).
        self.assertEqual(parse_labeled_hashes("frontier catalog exhausted"), {})


if __name__ == "__main__":
    unittest.main()