# Next Agent Task — HARMONY-CRYPTO-EDGE-004 DISPERSION-003

## Mandate
Continue quantitative research. Historical-only, free-data-only. No live/paper trading. No paid services or secrets.

## State on handoff
- Integrity audit + HAC addendum preserved; canonical artifact internally consistent (n=608, high=61, low=90, high-low net=0.6165, CI [-0.164, 1.397], not significant under overlap-aware HAC).
- Archived defective artifact preserved unchanged.
- Forward block BLOCKED for fresh confirmation: need data cutoff >= 2026-10-29 (current 2026-09-30). As of 2026-10-24T17:44:58Z, October 2026 Binance monthly archive returns HTTP 404. Structural gate; do not loop on it.
- Independent unblocked task completed: ran `scripts/validate_candidate_batch.py` for DISPERSION-003 (free-data only). Frontier updated (candidate_page_cursor 6397); verified=30, blocked=116, remaining_discovered 6199. Validation record at `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/candidate_batch_validation.json`.
- Test suite run (read-only): 33 ran, 26 passed, 7 failed/errored. 6 due to missing pandas/numpy (env). 1 real blocker: `test_forward_block_hashes_match_files_on_disk` FAILS — `candidate_batch_validation.json` hash in the sealed forward block's `input_file_hashes` (e0ae358af7...) no longer matches the file on disk (16c1754d9c...) because batch-1 validation wrote after the block seal. Sealed forward block itself intact and immutable; candidate_batch_validation.json left unchanged. Tests unavailable in this env (missing pandas/numpy/pytest).
- DISPERSION-001/002 unchanged.

## Concrete next action
1. Reconcile the sealed-forward-block input provenance: `candidate_batch_validation.json` is hashed in `forward_block_evaluation.json` (`input_file_hashes`) but the hash no longer matches the file on disk (prior batch-1 validation wrote after seal). Do NOT modify the sealed forward block (immutable). Either restore candidate_batch_validation.json to the sealed-hash content (e.g., from git history if available and consistent with the frontier), or formally document the mismatch and its resolution path. Do NOT run further candidate validation until provenance is restored (batch-2+ would compound the mismatch).
2. On/after 2026-10-29 (or once the October 2026 Binance monthly archive publishes), re-check data cutoff via `scripts/refresh_free_data.py` with `--price-end 2026-10-31 --cap-end 2026-10-31`; proceed only when cutoff >= 2026-10-29.
3. When available, evaluate H004V106 on a fresh sealed forward block with completed 30-day outcomes only; compute overlap-aware uncertainty (HAC/Newey-West and/or block bootstrap).
4. Do not reuse the inspected canonical block as independent confirmation; treat it as development/exploratory evidence.
5. Continue independent unblocked DISPERSION-003 candidate validation/discovery (free data) while waiting for cutoff — only after sealed-block provenance is restored.
6. Run full test suite in pandas-available environment; confirm DISPERSION-001/002 unchanged.
7. Update handoff + next task with concrete measurable outcomes.

## Blocker note (do not loop)
The cutoff gate is structural: 2026-10-29 has not occurred and the October 2026 archive is unpublished. If still blocked, preserve the blocker and move to an independent unblocked task (candidates, free-source discovery, validation, design, or red-team) per AGENTS.md rather than re-probing the same endpoint. The sealed-block hash mismatch is a separate integrity blocker: preserve it and reconcile before re-using candidate validation outputs with the sealed block.
