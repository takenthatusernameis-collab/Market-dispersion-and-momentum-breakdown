"""Pin the canonical H004V106 forward block against the committed blob.

The canonical sealed forward block
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json
is the single most-referenced number in the program (H1/H6/H7/H8/H9 all quote
its high_low_diff_net_1x). A stale sha256 string in the durable state (the
60a832fd... value that circulated for several sessions before being corrected
to 7234fc4e...) is a single-source-of-truth hazard: every future session that
re-quotes the wrong hash re-quotes a block that was never verified.

This test resolves the hash from the committed blob itself (git show HEAD:<path>)
rather than from any serialized JSON field, so it cannot be satisfied by a
self-consistent but wrong string. It also asserts the outcome fields that the
program quotes by hand, so a silent drift in n_formations, the anchor estimate,
the last formation date or the sealing flag fails the build.

stdlib only: hashlib + subprocess. No network, no market data, no trading.
"""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FB = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003" / "forward_block" / "forward_block_evaluation.json"

# The canonical value, verified three independent ways (direct file hash,
# git show HEAD:<path> | sha256sum, empty git diff HEAD -- <path>) and recorded
# in research_state/universe_frontier.json latest_archive_probe and in the
# hypothesis registry. This literal is the EXPECTED value; the test's real
# authority is git show HEAD below, so the literal is a secondary check.
EXPECTED_SHA256 = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FIELDS = {
    "n_formations": 608,
    "high_low_diff_net_1x": 0.6165223953929935,
    "date_last": "2026-08-31",
    "data_cutoff_utc": "2026-09-30T00:00:00Z",
    "anchor_id": "H004V106",
}


def _git_show_blob() -> bytes:
    r = subprocess.run(
        ["git", "show", f"HEAD:{FB.relative_to(ROOT).as_posix()}"],
        cwd=ROOT, capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"git show HEAD failed: {r.stderr.decode()}")
    return r.stdout


class CanonicalBlockGitPinnedTests(unittest.TestCase):
    def test_committed_blob_sha256_matches_canonical_value(self):
        actual = hashlib.sha256(_git_show_blob()).hexdigest()
        self.assertEqual(actual, EXPECTED_SHA256,
                         f"committed canonical block is {actual}; expected {EXPECTED_SHA256}")

    def test_working_tree_matches_committed_blob(self):
        """A modified working-tree block must not be silently quoted as canonical."""
        on_disk = FB.read_bytes()
        self.assertEqual(hashlib.sha256(on_disk).hexdigest(), EXPECTED_SHA256)
        self.assertEqual(on_disk, _git_show_blob(),
                         msg="working-tree canonical block differs from committed blob")

    def test_outcome_fields_unchanged(self):
        fb = json.loads(FB.read_text(encoding="utf-8"))
        for key, value in EXPECTED_FIELDS.items():
            with self.subTest(field=key):
                self.assertEqual(fb.get(key), value,
                                 f"canonical block field {key} = {fb.get(key)!r}; expected {value!r}")

    def test_block_is_sealed(self):
        fb = json.loads(FB.read_text(encoding="utf-8"))
        self.assertTrue(fb.get("block_sealed"), "canonical block must be sealed")


if __name__ == "__main__":
    unittest.main()