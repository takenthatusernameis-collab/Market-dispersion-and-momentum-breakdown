"""Hermetic seam tests for scripts/frozen_tree_integrity_audit.py.

Exercises the pure seams (sha256 helper, git-tree resolution, pinned-hash
verification, cleanliness check) and the full audit function against mocked
git plumbing and temp output dirs, with no network and no dependency on the
real committed tree state.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "frozen_tree_integrity_audit.py"

spec = importlib.util.spec_from_file_location("frozen_tree_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class _FakeProc:
    def __init__(self, stdout: bytes):
        self.stdout = stdout


def _build_patches(disk_drift_path: str | None = None):
    """Return (context managers, sentinel->expected map) for a fake frozen tree.

    Each pinned path gets a unique sentinel byte string used for BOTH its disk
    bytes and its git blob bytes; the patched ``_sha256_bytes`` maps each
    sentinel back to that path's pinned literal, so disk_matches and
    git_blob_matches are both True. Cleanliness is faked clean unless
    ``disk_drift_path`` is given, in which case git diff reports that path.
    """
    pinned = mod.PINNED_FILES
    sentinel_to_expected: dict[bytes, str] = {}
    path_to_sentinel: dict[str, bytes] = {}
    for i, (name, (rel, expected)) in enumerate(pinned.items()):
        sentinel = f"SENTINEL_{i}".encode()
        sentinel_to_expected[sentinel] = expected
        path_to_sentinel[rel] = sentinel

    real_run = subprocess.run
    real_read_bytes = Path.read_bytes

    def fake_run(args, **kw):
        if args[:2] == ["git", "show"]:
            rel = args[2].split(":", 1)[1]
            return _FakeProc(path_to_sentinel[rel])
        return real_run(args, **kw)

    def fake_git(*a):
        if a[0] == "rev-parse":
            return "treeid"
        if a[0] == "diff":
            return disk_drift_path or ""
        if a[0] == "ls-files" and "--others" in a:
            return ""
        if a[0] == "ls-files":
            return "f1\nf2\n"
        return ""

    def fake_read_bytes(self):
        rel = str(self.relative_to(ROOT))
        if rel in path_to_sentinel:
            return path_to_sentinel[rel]
        return real_read_bytes(self)

    def fake_sha(data: bytes) -> str:
        return sentinel_to_expected[data]

    return (
        patch.object(mod, "_git", side_effect=fake_git),
        patch.object(mod.subprocess, "run", side_effect=fake_run),
        patch.object(Path, "read_bytes", fake_read_bytes),
        patch.object(mod, "_sha256_bytes", side_effect=fake_sha),
    )


class FrozenTreeIntegritySeams(unittest.TestCase):
    def test_sha256_bytes_matches_hashlib(self):
        self.assertEqual(mod._sha256_bytes(b"abc"), hashlib.sha256(b"abc").hexdigest())

    def test_git_helper_returns_stripped_stdout(self):
        with patch.object(mod.subprocess, "run", return_value=_FakeProc(b"  deadbeef \n")):
            self.assertEqual(mod._git("rev-parse", "HEAD:x"), "deadbeef")

    def test_full_audit_pass_writes_artifact(self):
        patches = _build_patches()
        with patches[0], patches[1], patches[2], patches[3]:
            with tempfile.TemporaryDirectory() as td:
                rc = mod.main(["--output-dir", td])
                self.assertEqual(rc, 0)
                files = list(Path(td).glob("FROZEN_TREE_INTEGRITY_AUDIT_*.json"))
                self.assertEqual(len(files), 1)
                art = json.loads(files[0].read_text())
                self.assertEqual(art["verdict"], "PASS")
                self.assertEqual(art["failures"], [])
                self.assertTrue(art["checks"]["tracked_diff_empty"])
                self.assertTrue(art["checks"]["untracked_empty"])
                self.assertEqual(set(art["checks"]["frozen_tree_ids"]), set(mod.FROZEN_DIRS))
                for name in mod.PINNED_FILES:
                    pr = art["checks"]["pinned_files"][name]
                    self.assertTrue(pr["disk_matches"])
                    self.assertTrue(pr["git_blob_matches"])

    def test_full_audit_fail_on_tracked_drift(self):
        patches = _build_patches(disk_drift_path="artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/x.json")
        with patches[0], patches[1], patches[2], patches[3]:
            with tempfile.TemporaryDirectory() as td:
                rc = mod.main(["--output-dir", td])
                self.assertEqual(rc, 1)
                files = list(Path(td).glob("FROZEN_TREE_INTEGRITY_AUDIT_*.json"))
                art = json.loads(files[0].read_text())
                self.assertEqual(art["verdict"], "FAIL")
                self.assertFalse(art["checks"]["tracked_diff_empty"])
                self.assertTrue(any("tracked modifications" in f for f in art["failures"]))

    def test_full_audit_fail_on_pinned_hash_mismatch(self):
        # Disk bytes differ from the pinned literal -> disk_matches False.
        pinned = mod.PINNED_FILES
        path_to_sentinel: dict[str, bytes] = {}
        for i, (name, (rel, expected)) in enumerate(pinned.items()):
            path_to_sentinel[rel] = f"SENTINEL_{i}".encode()
        real_run = subprocess.run
        real_read_bytes = Path.read_bytes

        def fake_run(args, **kw):
            if args[:2] == ["git", "show"]:
                rel = args[2].split(":", 1)[1]
                return _FakeProc(path_to_sentinel[rel])
            return real_run(args, **kw)

        def fake_git(*a):
            if a[0] == "rev-parse":
                return "treeid"
            if a[0] == "diff":
                return ""
            if a[0] == "ls-files" and "--others" in a:
                return ""
            if a[0] == "ls-files":
                return "f1\n"
            return ""

        def fake_read_bytes(self):
            rel = str(self.relative_to(ROOT))
            if rel in path_to_sentinel:
                return path_to_sentinel[rel] + b"_DRIFT"
            return real_read_bytes(self)

        # Disk bytes hash to a wrong value; blob bytes hash to the expected literal.
        def fake_sha(data: bytes) -> str:
            for rel, sentinel in path_to_sentinel.items():
                if data == sentinel:
                    return pinned[[n for n, (r, _) in pinned.items() if r == rel][0]][1]
                if data == sentinel + b"_DRIFT":
                    return "0" * 64
            raise AssertionError("unexpected bytes")

        with patch.object(mod, "_git", side_effect=fake_git), \
             patch.object(mod.subprocess, "run", side_effect=fake_run), \
             patch.object(Path, "read_bytes", fake_read_bytes), \
             patch.object(mod, "_sha256_bytes", side_effect=fake_sha):
            with tempfile.TemporaryDirectory() as td:
                rc = mod.main(["--output-dir", td])
                self.assertEqual(rc, 1)
                files = list(Path(td).glob("FROZEN_TREE_INTEGRITY_AUDIT_*.json"))
                art = json.loads(files[0].read_text())
                self.assertEqual(art["verdict"], "FAIL")
                self.assertTrue(any("disk hash" in f for f in art["failures"]))


if __name__ == "__main__":
    unittest.main()