#!/usr/bin/env python3
"""Regression tests for the tracked-bytecode hygiene rule.

Every prior session's working tree accumulated untracked ``__pycache__/``
directories and ``*.pyc`` blobs (plus three historically tracked ``.pyc``
files), which churned ``git status`` and, worse, polluted the executable-input
fingerprint that ``scripts/record_test_claim.py`` uses to bind the verified
test claim to the source inventory. The rule is now declared in ``.gitignore``
and enforced here.

Guards:
  1. ``.gitignore`` exists and declares the bytecode/cache patterns.
  2. No tracked file matches a bytecode pattern (``git ls-files`` is the
     single source of truth for what is committed).
  3. ``scripts/record_test_claim.py``'s inventory fingerprint excludes every
     path under ``__pycache__`` and every ``*.pyc`` file -- the claim
     fingerprint must never include bytecode, because bytecode is not
     executable source and its presence in the fingerprint would make the
     claim depend on interpreter version, not on source.
  4. The committed snapshot, when present, contains no bytecode paths.

These are source-control and fingerprint-integrity guards, not market
evidence. They do not touch any frozen experiment artifact.
"""
import json
import subprocess
import sys
import unittest
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITIGNORE = ROOT / ".gitignore"
SNAPSHOT = ROOT / "research_state" / "verified_test_claim_claim_snapshot.json"

BYTECODE_PATTERNS = ("__pycache__/", "*.py[cod]", "*$py.class")


def _spec():
    return util.spec_from_file_location(
        "record_test_claim", str(ROOT / "scripts" / "record_test_claim.py")
    )


class TestGitignoreBytecodeHygiene(unittest.TestCase):
    def test_gitignore_declares_bytecode_patterns(self):
        self.assertTrue(GITIGNORE.exists(), ".gitignore missing")
        text = GITIGNORE.read_text(encoding="utf-8")
        for pat in BYTECODE_PATTERNS:
            self.assertIn(pat, text, f".gitignore missing pattern {pat!r}")

    def test_no_tracked_bytecode_files(self):
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        tracked = out.splitlines()
        offenders = [
            p for p in tracked
            if p.endswith(".pyc") or "/__pycache__/" in p or p.startswith("__pycache__/")
        ]
        self.assertEqual(
            offenders, [],
            f"tracked bytecode files must be removed from the index: {offenders}",
        )


class TestRecordTestClaimExcludesBytecode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = _spec()
        mod = util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        cls.mod = mod
        cls.fingerprint, cls.files = mod.inventory_fingerprint()

    def test_fingerprint_paths_exclude_pycache(self):
        offenders = [
            f["path"] for f in self.files
            if "/__pycache__/" in f["path"] or f["path"].startswith("__pycache__/") or f["path"].endswith(".pyc")
        ]
        self.assertEqual(
            offenders, [],
            f"inventory fingerprint must cover source .py only, found: {offenders}",
        )

    def test_fingerprint_covers_all_source_files(self):
        # Sanity: the fingerprint is not empty and covers both input dirs.
        self.assertGreater(len(self.files), 0)
        self.assertTrue(any(f["path"].startswith("scripts/") for f in self.files))
        self.assertTrue(any(f["path"].startswith("tests/") for f in self.files))

    def test_snapshot_contains_no_bytecode_paths(self):
        if not SNAPSHOT.exists():
            self.skipTest("no committed snapshot yet")
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        snap_files = snap.get("input_files", [])
        # Handle both old format (list of strings) and new format (list of dicts)
        paths = [f["path"] if isinstance(f, dict) else f for f in snap_files]
        offenders = [
            p for p in paths
            if "/__pycache__/" in p or p.startswith("__pycache__/") or p.endswith(".pyc")
        ]
        self.assertEqual(
            offenders, [],
            f"snapshot input_files must not include bytecode: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()