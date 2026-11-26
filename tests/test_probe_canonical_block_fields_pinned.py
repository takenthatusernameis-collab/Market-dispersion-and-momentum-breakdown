"""Durable-state guard: the structured canonical_forward_block copies carried in
the frontier and manifest probe summaries must match the frozen canonical block.

Both research_state/universe_frontier.json and research_state/run_manifest.json
carry TWO hand-written probe summaries (``latest_archive_probe`` and
``latest_november_2026_probe``), and each summary embeds a structured
``canonical_forward_block`` object (sha256, n_formations, high_low_diff_net_1x,
data_cutoff_utc, last_allowed_formation_date, block_sealed). Those six fields are
the block's identity in the durable state: a reader who trusts the summary rather
than re-deriving the block is reading these numbers.

The existing guards pin only part of this surface:
  * tests/test_canonical_block_git_pinned.py pins the frozen block FILE against
    its committed blob;
  * tests/test_state_consistency.py::test_durable_state_quotes_canonical_block_sha256
    pins the FRONTIER archive sha256 and requires the canonical sha256 string to
    appear somewhere in the manifest/registry prose.
Nothing pins the manifest's archive sha256 as a structured field, and nothing
pins ANY of the numeric structured fields (n_formations, high_low_diff_net_1x,
the cutoff/formation dates, the sealing flag) in ANY of the four summaries
against the frozen block. A re-serialization or one-sided hand edit that drifted,
say, latest_november_2026_probe.canonical_forward_block.n_formations from 608 to
607 would pass every existing guard while leaving the durable state quoting a
block that was never produced -- the same single-source-of-truth hazard class the
pinned-record and dangling-pointer guards exist for.

This guard resolves the frozen block from its committed git blob (not from any
serialized field, so it cannot be satisfied by a self-consistent but wrong
string), asserts the working tree matches that blob, and requires every one of
the four structured copies to agree with it field by field. A pure comparison
helper is exercised against synthetic drift so the guard cannot silently accept
everything.

Read-only, stdlib-only: hashlib + json + subprocess. No network, no market data,
no trading.
"""
import hashlib
import json
import math
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "research_state"
FB = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block"
    / "forward_block_evaluation.json"
)

# The structured fields every canonical_forward_block copy must carry. sha256 is
# checked against the committed-blob hash; the rest against the parsed frozen
# block.
PINNED_FIELDS = (
    "sha256",
    "n_formations",
    "high_low_diff_net_1x",
    "data_cutoff_utc",
    "last_allowed_formation_date",
    "block_sealed",
)
_FLOAT_FIELDS = {"high_low_diff_net_1x"}


def _git_show_blob():
    r = subprocess.run(
        ["git", "show", f"HEAD:{FB.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
        capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"git show HEAD failed: {r.stderr.decode()}")
    return r.stdout


def _field_mismatches(summary_block, frozen):
    """Return ``[(field, summary_value, frozen_value)]`` for every pinned field
    that disagrees.

    ``frozen`` is the authoritative block dict carrying a ``sha256`` key set to
    the committed-blob hash. Pure function so a synthetic drifted copy can be
    checked without touching the committed state.
    """
    mismatches = []
    for field in PINNED_FIELDS:
        got = summary_block.get(field)
        want = frozen[field]
        if field in _FLOAT_FIELDS:
            same = (
                isinstance(got, (int, float))
                and isinstance(want, (int, float))
                and math.isclose(got, want, rel_tol=0.0, abs_tol=1e-12)
            )
        else:
            same = got == want
        if not same:
            mismatches.append((field, got, want))
    return mismatches


class ProbeCanonicalBlockFieldsPinnedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        blob = _git_show_blob()
        cls.blob_sha = hashlib.sha256(blob).hexdigest()
        frozen = json.loads(blob.decode("utf-8"))
        frozen["sha256"] = cls.blob_sha
        cls.frozen = frozen
        frontier = json.loads((STATE / "universe_frontier.json").read_text(encoding="utf-8"))
        manifest = json.loads((STATE / "run_manifest.json").read_text(encoding="utf-8"))
        cls.summaries = [
            ("universe_frontier.json:latest_archive_probe", frontier["latest_archive_probe"]),
            (
                "universe_frontier.json:latest_november_2026_probe",
                frontier["latest_november_2026_probe"],
            ),
            ("run_manifest.json:latest_archive_probe", manifest["latest_archive_probe"]),
            (
                "run_manifest.json:latest_november_2026_probe",
                manifest["latest_november_2026_probe"],
            ),
        ]

    def test_working_tree_matches_committed_blob(self):
        """A modified working-tree canonical block must not be quoted as the
        frozen truth this guard pins the summaries against."""
        self.assertEqual(
            FB.read_bytes(),
            _git_show_blob(),
            msg="working-tree canonical block differs from its committed blob",
        )

    def test_every_summary_matches_frozen_block(self):
        for label, summary in self.summaries:
            with self.subTest(summary=label):
                cb = summary.get("canonical_forward_block")
                self.assertIsInstance(
                    cb, dict, f"{label} carries no canonical_forward_block object"
                )
                mismatches = _field_mismatches(cb, self.frozen)
                self.assertEqual(
                    mismatches,
                    [],
                    f"{label} canonical_forward_block drifts from the frozen "
                    f"block: {mismatches}",
                )

    def test_helper_detects_synthetic_drift(self):
        """The comparison helper must actually flag a drifted field.

        The committed-state test above passes only because the durable state is
        clean; on its own it could not distinguish a working guard from one that
        silently accepts everything. This exercises the same helper against a
        synthetic copy with each pinned field drifted in turn and requires the
        helper to report exactly that field.
        """
        frozen = self.frozen
        clean = {field: frozen[field] for field in PINNED_FIELDS}
        self.assertEqual(
            _field_mismatches(clean, frozen), [], "clean copy should not mismatch"
        )
        for field in PINNED_FIELDS:
            bad = dict(clean)
            if field in _FLOAT_FIELDS:
                bad[field] = frozen[field] + 1.0
            elif field == "block_sealed":
                bad[field] = not frozen[field]
            elif field == "sha256":
                bad[field] = "0" * 64
            elif field == "n_formations":
                bad[field] = frozen[field] + 1
            else:
                bad[field] = "drifted"
            with self.subTest(field=field):
                mismatches = _field_mismatches(bad, frozen)
                self.assertEqual(
                    [m[0] for m in mismatches],
                    [field],
                    f"helper failed to flag synthetic drift in {field}",
                )


if __name__ == "__main__":
    unittest.main()