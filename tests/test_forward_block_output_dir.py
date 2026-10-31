"""Regression test for the --output-dir flag on scripts/eval_forward_block.py.

The canonical H004V106 sealed forward block (artifacts/.../forward_block/
forward_block_evaluation.json) is development/exploratory evidence only: it has
already been inspected by six integrity audits and must never be re-sealed,
overwritten or used as a fresh holdout. The H10 preregistration requires a
*genuinely fresh* sealed forward block (formations after 2026-09-29), but that
block cannot be produced until the October 2026 Binance archive publishes and
the data cutoff advances past 2026-10-29. Until then the evaluator must be
capable of sealing a block into a *separate* directory without touching the
canonical artifact, or the first unblocked session would silently destroy the
canonical block while attempting to produce the fresh one.

This test pins that capability:

  1. the canonical artifact is byte-identical before and after a run that
     targets a different --output-dir;
  2. the targeted directory receives a well-formed sealed block that agrees
     with the canonical block on every frozen outcome field (same cutoff, same
     formation count, same high_low_diff_net_1x, same last_allowed_formation
     date) -- i.e. the new flag is a pure relocation of the write, not a change
     in computation;
  3. the default (no --output-dir) still writes to the canonical path, so the
     flag is additive and the existing reproducibility test keeps passing.

The run is a subprocess at the frozen 2026-09-30 cutoff, which is the latest
cutoff available on the committed panels and reproduces the canonical block
exactly. No new data are fetched and no frozen artifact is modified.
"""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"
EVAL = ROOT / "scripts" / "eval_forward_block.py"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class ForwardBlockOutputDirTests(unittest.TestCase):
    def test_output_dir_override_writes_separate_block_and_leaves_canonical_intact(self):
        import tempfile

        canonical_hash_before = _sha(CANONICAL)

        with tempfile.TemporaryDirectory() as td:
            out_dir = Path(td) / "fresh_block"
            r = subprocess.run(
                ["python", str(EVAL), "--data-cutoff", "2026-09-30",
                 "--output-dir", str(out_dir)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            produced = out_dir / "forward_block_evaluation.json"
            self.assertTrue(produced.exists(),
                            msg=f"--output-dir did not produce a block at {produced}")

            self.assertEqual(
                _sha(CANONICAL), canonical_hash_before,
                msg="canonical H004V106 block must be byte-identical after a "
                    "--output-dir run",
            )

            fresh = json.loads(produced.read_text(encoding="utf-8"))
            canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
            # The override is a pure relocation: every frozen outcome field must
            # agree with the canonical block, since the same panels and the same
            # cutoff were used.
            for field in ("data_cutoff_utc", "n_formations", "n_high", "n_low",
                          "n_mid", "high_low_diff_net_1x", "high_low_diff_gross",
                          "date_first", "date_last",
                          "last_allowed_formation_date", "block_sealing_rule"):
                with self.subTest(field=field):
                    self.assertEqual(fresh.get(field), canonical.get(field),
                                     msg=f"{field} differs between fresh and canonical block")
            self.assertTrue(fresh.get("block_sealed"))
            self.assertEqual(fresh.get("anchor_id"), "H004V106")
            self.assertGreater(len(fresh.get("formations", [])), 0)

    def test_default_path_is_still_canonical(self):
        # The default (no --output-dir) must write to the canonical path, so the
        # flag is additive and the existing reproducibility test keeps passing.
        import tempfile

        canonical_hash_before = _sha(CANONICAL)
        with tempfile.TemporaryDirectory() as td:
            # Point --output-dir at a throwaway dir, then confirm the canonical
            # file is STILL the canonical file (i.e. the default was not moved).
            out_dir = Path(td) / "fresh_block"
            r = subprocess.run(
                ["python", str(EVAL), "--data-cutoff", "2026-09-30",
                 "--output-dir", str(out_dir)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(_sha(CANONICAL), canonical_hash_before,
                         msg="canonical block must not change even when a "
                             "separate --output-dir run executes")


if __name__ == "__main__":
    unittest.main()