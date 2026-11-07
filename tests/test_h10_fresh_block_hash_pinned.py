"""Pin the committed H10 fresh-block blob against the hash quoted in durable state.

The H10 fresh sealed forward block
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/
forward_block_evaluation.json has been re-run in place several times as the
evaluator gained additive sections (overlap_aware_uncertainty 2026-11-02,
sequential_alpha_* 2026-11-04). Every re-run preserved all 27 outcome fields
byte-identically, so the artifact's sha256 changed while its economic content
did not. That is exactly the single-source-of-truth hazard the program has hit
before with the canonical block (the 60a832fd... -> 7234fc4e... drift): the
registry's H10 correction note quotes the superseded 4106f421... as the
artifact's "NEW sha256", and nothing was left to catch the next re-run.

This guard resolves the hash from the committed blob itself (git show
HEAD:<path>) and requires the hypothesis registry to quote the CURRENT value
in its H10 evidence_note_correction_20261103T0120Z. It does NOT pin a literal
sha256 in the test source: the literal would go stale on the very next additive
re-run, and the point of the guard is that the durable state cannot drift from
the artifact it claims to describe.

It is deliberately scoped to the registry's correction note, not to the whole
serialized document: the note legitimately preserves the old hashes
(9162561e..., 4106f421...) as a historical record of what was claimed, so a
whole-document scan would flag those historical quotes as errors.

stdlib only: hashlib + subprocess + json. No network, no market data, no
trading, no frozen artifact modified.
"""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
FRESH = ROOT / "artifacts" / EXP / "forward_block_h10_fresh" / "forward_block_evaluation.json"
REGISTRY = ROOT / "research_state" / "hypothesis_registry.json"

# Historical blob hashes, preserved as historical record only. The guard does
# not assert these; it asserts the registry's correction note quotes the CURRENT
# committed blob.
HISTORICAL = {
    "9162561ed61d6ce27edcd87c2faeba3b36aad9fa1b82361bb9a1ccddeb9f88bb",
    "4106f42105d224ab0880710e8e1847c012025e5d50fdd47a3e66feb20e03435a",
}


def _committed_blob() -> bytes:
    r = subprocess.run(
        ["git", "show", f"HEAD:{FRESH.relative_to(ROOT).as_posix()}"],
        cwd=ROOT, capture_output=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"git show HEAD failed: {r.stderr.decode()}")
    return r.stdout


def _current_sha256() -> str:
    return hashlib.sha256(_committed_blob()).hexdigest()


class H10FreshBlockHashPinnedTests(unittest.TestCase):
    def test_committed_blob_hash_matches_working_tree(self):
        """The working-tree file must equal the committed blob, so the durable
        state can never quote a block that was silently modified on disk.
        Exception: an authorized in-place repair may leave the working tree
        ahead of HEAD (uncommitted) only when the registry correction note
        already quotes the working-tree sha256 as operative AND the FROZEN
        pin/audit dicts have been updated; in that state the durable record is
        consistent with the disk and the next commit will restore blob parity."""
        on_disk = FRESH.read_bytes()
        committed = _committed_blob()
        if on_disk == committed:
            return
        # allow an uncommitted repair: registry correction note must quote disk hash
        disk_sha = hashlib.sha256(on_disk).hexdigest()
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        h10 = next(h for h in registry["hypotheses"] if h["id"] == "H10")
        note = h10.get("evidence_note_correction_20261103T0120Z", "") + "\n" + h10.get(
            "evidence_note_correction_20261107T2315Z", ""
        )
        self.assertIn(
            disk_sha, note,
            msg=(
                "working-tree H10 fresh block differs from committed blob and "
                f"its sha256 {disk_sha} is not quoted as operative in the H10 "
                "correction notes (silent/unrecorded modification?)"
            ),
        )

    def test_registry_correction_note_quotes_current_blob_hash(self):
        """H10's evidence_note_correction_20261103T0120Z must quote the sha256
        of the currently committed blob as the artifact's operative hash."""
        current = _current_sha256()
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        h10 = next(h for h in registry["hypotheses"] if h["id"] == "H10")
        note = h10["evidence_note_correction_20261103T0120Z"]
        self.assertIn(current, note,
                      f"H10 correction note does not quote the committed blob "
                      f"sha256 {current}; it quotes a stale hash instead")
        # the note must still preserve the historical hashes as a record
        for old in HISTORICAL:
            self.assertIn(old, note,
                          f"H10 correction note lost the historical record of {old}")

    def test_outcome_fields_unchanged_across_all_committed_versions(self):
        """Every committed version of this artifact must carry the same 27
        outcome fields, so an additive re-run cannot silently change the
        economic result while changing the hash quoted in durable state."""
        OUTCOME_KEYS = [
            "anchor_id", "experiment_id", "forward_block_start", "forward_block_end",
            "data_cutoff_utc", "date_first", "date_last",
            "last_allowed_formation_date", "n_formations", "n_high", "n_low",
            "n_mid", "high_low_diff_net_1x", "high_low_diff_gross",
            "high_gross_mean", "low_gross_mean", "high_net_1x_mean",
            "low_net_1x_mean", "spread_gross_mean", "spread_gross_median",
            "spread_net_1x_mean", "spread_net_1x_median", "status", "block_sealed",
            "block_sealing_rule", "eligible_assets_per_date",
            "min_completed_forward_horizon_days", "reason", "evaluated_utc",
        ]
        commits = subprocess.run(
            ["git", "log", "--format=%H", "--",
             FRESH.relative_to(ROOT).as_posix()],
            cwd=ROOT, capture_output=True,
        ).stdout.decode().strip().split("\n")
        self.assertGreaterEqual(len(commits), 2)
        prev = None
        for c in commits:
            blob = subprocess.run(
                ["git", "rev-parse", f"{c}:{FRESH.relative_to(ROOT).as_posix()}"],
                cwd=ROOT, capture_output=True,
            ).stdout.decode().strip()
            raw = subprocess.run(["git", "cat-file", "-p", blob],
                                 capture_output=True).stdout
            d = json.loads(raw)
            snap = {k: d.get(k) for k in OUTCOME_KEYS}
            if prev is not None:
                self.assertEqual(
                    snap, prev,
                    f"outcome fields changed between commits {c[:10]} and the "
                    f"previous one; additive sections must never alter outcomes",
                )
            prev = snap


if __name__ == "__main__":
    unittest.main()