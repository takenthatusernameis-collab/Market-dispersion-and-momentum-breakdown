#!/usr/bin/env python3
"""Repair the H10 fresh-block sha256 quoted in the hypothesis registry.

The H10 fresh sealed forward block
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/
forward_block_evaluation.json has been re-run in place several times as the
evaluator gained additive sections (overlap_aware_uncertainty 2026-11-02,
sequential_alpha_* 2026-11-04). Every re-run preserved all 27 outcome fields
byte-identically, so the artifact's sha256 changed while its economic content
did not. The registry's H10 evidence_note_correction_20261103T0120Z still
quoted the superseded 4106f421... as the artifact's "NEW sha256", which is the
same single-source-of-truth hazard class already repaired once for the
canonical block (60a832fd... -> 7234fc4e...): a durable-state string that drifts
from the artifact it claims to describe, with nothing to catch the next drift.

This repair does NOT touch the artifact. It only rewrites the registry's prose
correction note to quote the CURRENT committed blob sha256 (resolved from
`git show HEAD:<path>`, never from a serialized field), while preserving every
historical hash as a record of what was claimed at each stage. No hypothesis,
conclusion, grid, decision rule, cost model or frozen artifact is changed.

Usage:
    python3 scripts/repair_h10_fresh_block_registry_hash.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_state" / "hypothesis_registry.json"
FRESH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json"

# Historical blob hashes, in the order each was quoted as the artifact's
# operative sha256. All are preserved verbatim in the repaired note as a record
# of what was claimed; only the LAST one is the current committed blob.
HISTORICAL = [
    "9162561ed61d6ce27edcd87c2faeba3b36aad9fa1b82361bb9a1ccddeb9f88bb",
    "4106f42105d224ab0880710e8e1847c012025e5d50fdd47a3e66feb20e03435a",
]


def committed_blob_sha256() -> str:
    r = subprocess.run(
        ["git", "show", f"HEAD:{FRESH}"], cwd=ROOT, capture_output=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"git show HEAD failed: {r.stderr.decode()}")
    return hashlib.sha256(r.stdout).hexdigest()


def main() -> int:
    current = committed_blob_sha256()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    h10 = next(h for h in registry["hypotheses"] if h["id"] == "H10")
    key = "evidence_note_correction_20261103T0120Z"
    note = h10[key]

    if current in note:
        print(f"registry already quotes current blob sha256 {current}; no change")
        return 0

    # Replace the superseded "NEW sha256 is <old>" clause with the current
    # value, and append the full historical chain as a record. The original
    # historical hashes are already quoted in the note; we keep them and add
    # the current one explicitly.
    import re
    new_note = re.sub(
        r"the artifact's NEW sha256 is [0-9a-f]{64}",
        f"the artifact's NEW sha256 is {current}",
        note,
        count=1,
    )
    if new_note == note:
        raise RuntimeError("could not locate the 'NEW sha256 is' clause in the note")

    # Record the full historical chain so the next drift is auditable.
    chain = ", ".join(HISTORICAL + [current])
    new_note = new_note.replace(
        "This correction does not change any hypothesis",
        "HISTORICAL BLOB CHAIN (each quoted in turn as the artifact's operative "
        f"sha256, all preserving the same 27 outcome fields byte-identically): "
        f"{chain}. This correction does not change any hypothesis",
        1,
    )

    h10[key] = new_note
    REGISTRY.write_text(
        json.dumps(registry, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"repaired H10 {key} to quote current blob sha256 {current}")
    print(f"historical chain preserved: {chain}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())