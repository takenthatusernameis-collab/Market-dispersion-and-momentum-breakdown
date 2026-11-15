"""Hermetic unit tests for the pure seams in scripts/repair_h10_fresh_block_registry_hash.py.

Gap: ``scripts/repair_h10_fresh_block_registry_hash.py`` exposes two deterministic
seams -- ``committed_blob_sha256`` and ``main``'s registry note rewrite -- but no
test imports the module or exercises them directly (grep across ``tests/`` returns
zero references). The module is import-safe (top-level code is imports and
constants only; ``main()`` is ``__main__``-guarded).

``committed_blob_sha256`` shells out to ``git show HEAD:<path>`` and hashes the
blob; it is tested by monkeypatching the module's ``subprocess`` name, so no git
repository, working tree or network is needed.

``main()`` reads and rewrites ``research_state/hypothesis_registry.json`` H10's
``evidence_note_correction_20261103T0120Z``. It is exercised against a synthetic
temp-dir registry so the real registry is never the write target and is never
mutated; the real registry bytes are snapshot before and after each run to prove
they are unchanged.

No frozen artifact/config/input is read or written. No network.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "repair_h10_fresh_block_registry_hash.py"
REAL_REGISTRY = ROOT / "research_state" / "hypothesis_registry.json"

# A synthetic committed blob whose sha256 is the "current" value quoted by the
# rewritten note. Arbitrary bytes; only the hash matters.
FAKE_BLOB = b"synthetic forward_block_evaluation.json committed blob\n"
CURRENT_SHA = hashlib.sha256(FAKE_BLOB).hexdigest()

# Two superseded historical blobs preserved verbatim by the repair (the module's
# HISTORICAL constant).
OLD_SHA = "9162561ed61d6ce27edcd87c2faeba3b36aad9fa1b82361bb9a1ccddeb9f88bb"
ANOTHER_OLD = "4106f42105d224ab0880710e8e1847c012025e5d50fdd47a3e66feb20e03435a"


def _proc(stdout=b"", returncode=0, stderr=b""):
    p = mock.MagicMock()
    p.returncode = returncode
    p.stdout = stdout
    p.stderr = stderr
    return p


def _load():
    spec = importlib.util.spec_from_file_location(
        "repair_h10_fresh_block_registry_hash_seam_test", SCRIPT
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _make_temp_registry(tmp_path: Path, note: str) -> Path:
    registry = {
        "schema_version": "1.0",
        "program_id": "HARMONY-CRYPTO-EDGE-004",
        "next_sequence_number": 28,
        "hypotheses": [
            {
                "id": "H10",
                "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-H10",
                "statement": "synthetic H10 statement",
                "predicted_high_minus_low_sign": "unspecified",
                "status": "CANDIDATE_UNVALIDATED",
                "evidence_note": "synthetic evidence note",
                "evidence_note_correction_20261103T0120Z": note,
            },
            {
                "id": "H1",
                "statement": "other hypothesis that must be left untouched",
                "status": "NOT_SUPPORTED_AS_ROBUST_EDGE",
            },
        ],
    }
    p = tmp_path / "hypothesis_registry.json"
    p.write_text(
        json.dumps(registry, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return p


class CommittedBlobSha256Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()

    def test_returns_sha256_of_git_show_stdout(self):
        payload = b'{"schema_version": "1.0"}\n'
        expected = hashlib.sha256(payload).hexdigest()
        fake_subprocess = mock.MagicMock()
        fake_subprocess.run.return_value = _proc(stdout=payload)
        with mock.patch.object(self.mod, "subprocess", fake_subprocess):
            self.assertEqual(self.mod.committed_blob_sha256(), expected)

    def test_raises_runtime_error_when_git_show_fails(self):
        fake_subprocess = mock.MagicMock()
        fake_subprocess.run.return_value = _proc(returncode=1, stderr=b"fatal: bad object")
        with mock.patch.object(self.mod, "subprocess", fake_subprocess):
            with self.assertRaises(RuntimeError) as ctx:
                self.mod.committed_blob_sha256()
            self.assertIn("git show HEAD failed", str(ctx.exception))


class MainRewriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _load()
        cls.real_before = REAL_REGISTRY.read_bytes()

    def _run_main(self, reg_path: Path):
        fake_subprocess = mock.MagicMock()
        fake_subprocess.run.return_value = _proc(stdout=FAKE_BLOB)
        with mock.patch.object(self.mod, "subprocess", fake_subprocess), mock.patch.object(
            self.mod, "REGISTRY", reg_path
        ):
            return self.mod.main()

    def test_replaces_new_sha256_clause_and_appends_historical_chain(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg = _make_temp_registry(
                tmp,
                (
                    "STALE-ARTIFACT CORRECTION. ... the artifact's NEW sha256 is "
                    f"{OLD_SHA}. This correction does not change any hypothesis"
                ),
            )
            rc = self._run_main(reg)
            self.assertEqual(rc, 0)
            updated = json.loads(reg.read_text(encoding="utf-8"))
            h10 = next(h for h in updated["hypotheses"] if h["id"] == "H10")
            note = h10["evidence_note_correction_20261103T0120Z"]
            self.assertIn(f"the artifact's NEW sha256 is {CURRENT_SHA}", note)
            self.assertNotIn(f"the artifact's NEW sha256 is {OLD_SHA}", note)
            self.assertIn("HISTORICAL BLOB CHAIN", note)
            self.assertIn(OLD_SHA, note)
            self.assertIn(ANOTHER_OLD, note)
            self.assertIn(CURRENT_SHA, note)
            self.assertIn("This correction does not change any hypothesis", note)
            # The historical chain ends with ANOTHER_OLD, then the current sha256.
            self.assertIn(f"{ANOTHER_OLD}, {CURRENT_SHA}", note)
            # H1 is untouched.
            h1 = next(h for h in updated["hypotheses"] if h["id"] == "H1")
            self.assertEqual(h1["statement"], "other hypothesis that must be left untouched")

    def test_no_change_when_current_already_in_note(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            note = (
                f"STALE-ARTIFACT CORRECTION. OPERATIVE sha256 is {CURRENT_SHA}. "
                "This correction does not change any hypothesis"
            )
            reg = _make_temp_registry(tmp, note)
            before = reg.read_text(encoding="utf-8")
            rc = self._run_main(reg)
            self.assertEqual(rc, 0)
            self.assertEqual(reg.read_text(encoding="utf-8"), before)

    def test_raises_when_new_sha256_clause_missing(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg = _make_temp_registry(
                tmp, "STALE-ARTIFACT CORRECTION. No operative sha256 clause here."
            )
            with self.assertRaises(RuntimeError) as ctx:
                self._run_main(reg)
            self.assertIn("NEW sha256 is", str(ctx.exception))

    def test_real_registry_is_never_mutated(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg = _make_temp_registry(
                tmp,
                (
                    f"STALE-ARTIFACT CORRECTION. the artifact's NEW sha256 is {OLD_SHA}. "
                    "This correction does not change any hypothesis"
                ),
            )
            self._run_main(reg)
        self.assertEqual(REAL_REGISTRY.read_bytes(), self.real_before)


if __name__ == "__main__":
    unittest.main()
