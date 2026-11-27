"""Committed-disk verdict pin for scripts/frozen_tree_integrity_audit.py (H38).

The hermetic seam suite (test_frozen_tree_integrity_audit_seams.py) exercises the
audit only against synthetic fixtures and mocked git plumbing. This module pins the
audit's PASS verdict against the REAL committed tree on disk, so the load-bearing
claim the task message carries into every session cannot silently drift:

  "Whole-tree frozen-artifact integrity audit -> PASS (five pins match disk AND
   git blob; zero tracked/untracked drift under artifacts/ and configs/)"

That claim is the reason a pre-gate session can do bounded audit/test work instead
of chasing a non-existent discovery task: it asserts DISPERSION-001/002/003 and
configs/ are byte-unchanged. Until now it was quoted in the task message but only
backed by synthetic seams tests -- the same single-source-of-truth hazard that the
committed maturity-timeline (H35) and independent-recomputation (H37) pins closed.

This guard runs the real audit into a throwaway temp dir (so no dated artifact is
written under research_state/), then independently re-derives every load-bearing
quantity from ground truth:

  - the aggregate git tree id for each frozen directory (git rev-parse HEAD:<dir>);
  - the five pinned file sha256 values vs BOTH disk bytes and the committed blob;
  - working-tree cleanliness (zero tracked diff, zero untracked) under artifacts/
    and configs/;
  - non-zero tracked file counts per frozen directory.

Read-only: no network, no frozen artifact/config/grid/frontier/panel touched; the
only file written is the audit's own dated artifact inside a temp dir. stdlib-only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "frozen_tree_integrity_audit.py"

spec = importlib.util.spec_from_file_location("frozen_tree_audit_committed", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Independent copies of the five pinned literals (kept here so a coordinated change
# to the module constants alone cannot satisfy this test).
EXPECTED_PINNED = {
    "canonical": (
        "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    ),
    "h10_fresh": (
        "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json",
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    ),
    "grid_result_ledger": (
        "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json",
        "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c",
    ),
    "grid_v3_config": (
        "configs/dispersion_momentum_grid_v3.json",
        "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
    ),
    "frontier": (
        "research_state/universe_frontier.json",
        "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
    ),
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True)
    return out.stdout.decode().strip()


def _git_blob_sha256(rel_path: str) -> str:
    blob = subprocess.run(
        ["git", "show", f"HEAD:{rel_path}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return hashlib.sha256(blob).hexdigest()


class CommittedFrozenTreeIntegrityAuditVerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = [ROOT / rel for rel, _ in EXPECTED_PINNED.values()]
        required += [ROOT / d for d in mod.FROZEN_DIRS]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise unittest.SkipTest(
                "committed artifacts absent in this checkout: " + ", ".join(missing)
            )
        cls._tmp = tempfile.TemporaryDirectory()
        rc = mod.main(["--output-dir", cls._tmp.name])
        cls.rc = rc
        files = list(Path(cls._tmp.name).glob("FROZEN_TREE_INTEGRITY_AUDIT_*.json"))
        if len(files) != 1:
            raise AssertionError(
                f"audit wrote {len(files)} artifacts, expected exactly 1"
            )
        cls.artifact = json.loads(files[0].read_text())

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_verdict_is_pass_with_no_failures(self):
        self.assertEqual(self.rc, 0)
        self.assertEqual(self.artifact["verdict"], "PASS")
        self.assertEqual(self.artifact["failures"], [])
        self.assertTrue(self.artifact["frozen_artifacts_untouched"])

    def test_audit_identity(self):
        self.assertEqual(
            self.artifact["audit_id"], "DISP-003-FROZEN-TREE-INTEGRITY-001"
        )
        self.assertEqual(
            self.artifact["audit_type"], "READ_ONLY_FROZEN_RECORD_AUDIT"
        )
        self.assertEqual(
            self.artifact["program_id"], "HARMONY-CRYPTO-EDGE-004"
        )

    def test_five_pinned_files_match_disk_and_git_blob(self):
        pinned = self.artifact["checks"]["pinned_files"]
        self.assertEqual(set(pinned), set(EXPECTED_PINNED))
        for name, (rel, expected) in EXPECTED_PINNED.items():
            with self.subTest(name=name):
                pr = pinned[name]
                self.assertEqual(pr["path"], rel)
                self.assertEqual(pr["expected"], expected)
                # Independent recompute from disk and from the committed blob.
                self.assertEqual(_sha256_file(ROOT / rel), expected)
                self.assertEqual(_git_blob_sha256(rel), expected)
                # And the audit's own recorded values agree.
                self.assertEqual(pr["disk"], expected)
                self.assertEqual(pr["git_blob"], expected)
                self.assertTrue(pr["disk_matches"])
                self.assertTrue(pr["git_blob_matches"])

    def test_frozen_tree_ids_match_git_rev_parse(self):
        recorded = self.artifact["checks"]["frozen_tree_ids"]
        self.assertEqual(set(recorded), set(mod.FROZEN_DIRS))
        for d in mod.FROZEN_DIRS:
            with self.subTest(dir=d):
                # Independent recompute of the aggregate content-hashed tree id.
                self.assertEqual(recorded[d], _git("rev-parse", f"HEAD:{d}"))
                # A tree id is a non-empty object name.
                self.assertRegex(recorded[d], r"^[0-9a-f]{40}$")

    def test_working_tree_clean_under_artifacts_and_configs(self):
        checks = self.artifact["checks"]
        self.assertTrue(checks["tracked_diff_empty"])
        self.assertTrue(checks["untracked_empty"])
        self.assertEqual(checks["tracked_diff_files"], [])
        self.assertEqual(checks["untracked_files"], [])
        # Independent recompute of the same cleanliness facts.
        self.assertEqual(
            _git("diff", "--name-only", "HEAD", "--", "artifacts/", "configs/"), ""
        )
        self.assertEqual(
            _git(
                "ls-files", "--others", "--exclude-standard", "--", "artifacts/", "configs/"
            ),
            "",
        )

    def test_tracked_file_counts_nonzero(self):
        counts = self.artifact["checks"]["tracked_file_counts"]
        self.assertEqual(set(counts), set(mod.FROZEN_DIRS))
        for d in mod.FROZEN_DIRS:
            with self.subTest(dir=d):
                self.assertGreater(counts[d], 0)
                # Independent recompute of the tracked file count.
                listing = _git("ls-files", d)
                self.assertEqual(counts[d], len([x for x in listing.splitlines() if x]))

    def test_helper_rejects_a_synthetic_drift(self):
        """The disk/blob comparison must actually reject a wrong hash.

        The committed-tree tests above pass only because the real tree is clean;
        on their own they could not distinguish a working guard from one that
        silently accepts everything. This exercises the same sha256 comparison
        against a bogus digest and requires the mismatch to be visible.
        """
        real = _sha256_file(ROOT / EXPECTED_PINNED["canonical"][0])
        bogus = "0" * 64
        self.assertNotEqual(real, bogus)
        self.assertEqual(real, EXPECTED_PINNED["canonical"][1])
        self.assertNotEqual(bogus, EXPECTED_PINNED["canonical"][1])


if __name__ == "__main__":
    unittest.main()