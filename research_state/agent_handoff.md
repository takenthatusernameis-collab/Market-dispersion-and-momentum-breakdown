# Agent Handoff — 2026-11-12T16:20:52Z (current session)

## Session summary
- **28th pass — input-coverage lineage audit (2026-11-12T16:16Z–16:20Z):** read the prior agent task, re-verified state from disk at HEAD `cec33df6f5f73d0e8a8a29fbae5fe4cb35de5c9d` (`main...origin/main` 0/0, clean tracked tree at verify start). All five frozen sha256 recomputed match disk. Checks: `python3 -m compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` **Ran 348 tests, OK (skipped=1), EXIT=0** (59.464s); the three reference/coverage audits pass (14/13/14 scanned, critical=0, errors=0).
- **Bounded gap found and acted on (read-only):** `research_state/DISP_003_PANEL_COVERAGE_LINEAGE_AUDIT_20261112T162052Z.json` (`DISP-003-PANEL-COVERAGE-LINEAGE-001`, verdict `PASS_WITH_NEW_INPUT_COVERAGE_FINDING`).
  - **F1:** 4 of 32 panel symbols — `1inch`, `aave`, `ach`, `agld` — have **no klines and no funding** for **2025-01-01..2026-09-30** (639-day kline hole; 21 missing months per symbol; **168 missing monthly zips** = 84 klines + 84 funding). Their series resume at the 2026-10 zip and the cap panel covers every day of the gap, so this is a raw-archive acquisition gap, not a delisting. No artifact recorded this before.
  - **F2:** the sealed canonical H004V106 block (`2025-01-01..2026-08-31`) therefore ran on **26–27 assets**, not 32. Recomputing the documented eligibility rule from the on-disk panels reproduces **608/608** recorded `n_assets` exactly (27 on 141 formations through 2025-05-21; 26 on 467 formations from 2025-05-22). Excluded throughout: the four F1 symbols + `matic` (delisted 2024-09-11); `eos` only until 2025-05-21.
  - **F3:** H10 fresh formation (2026-09-30) uses 26 assets — consistent with `EVALUATED_NULL_DIFF_IMMATURE`; no change to the H10 gate, `k` or the maturity rule.
  - **F4:** minor single-day holes only (all 26 full-coverage symbols lack 2026-10-28; `eos` cap panel lacks 2025-06-05; cap panel ends 2026-11-03 vs klines 2026-10-31).
  - **F5 (documentation drift, no value change):** frontier `expanding_universe_assets_with_cap_and_binance = 220` is pinned by `tests/test_candidate_validation.py` to `len(candidates_verified)`, but its definition sentence says "in the committed panels" — only **32** assets have a committed price series and the grid's expanding arm can never exceed 32 eligible assets per date (grid anchor max 32, mean 29.02, min 26). Value and frontier file were **not** changed; recorded for the frontier owner.
- **Evidence produced:** `research_state/session_verifications/session_verify_20261112T162052Z.json`; `research_state/DISP_003_PANEL_COVERAGE_LINEAGE_AUDIT_20261112T162052Z.json`; regenerated additive audit outputs `research_state/INTEGRITY_AUDIT_REFERENCE_CONSISTENCY_20261112T162007Z.json`, `research_state/PREREG_AND_H10_FRESH_REFERENCE_CONSISTENCY_20261112T162007Z.json`, `research_state/preregistration_coverage_audit.json` (byte-identical to committed version).
- **No frozen result artifact, panel, raw zip, config, script, test, doc, prompt, `research_state/hypothesis_registry.json`, or `research_state/universe_frontier.json` modified. No zip downloaded. No network access used.**

## Frozen integrity (sha256, re-verified 2026-11-12T16:20:52Z)
- canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` — `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json`
- h10_fresh `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` — `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json`
- registry `7faacdb3f7add98a9e6bddf3c4ab3403fd812711dd0ca601b5ddda031a664df4` — `research_state/hypothesis_registry.json`
- frontier `9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e` — `research_state/universe_frontier.json`
- latest probe `25c11cbae9e62c9f5feb41d9f2de09a996dd4a0a1ddcfa4828ecc05daa73f7e6` — `research_state/cutoff_probe/cutoff_probe_20261111T013459Z.json`

## Frontier (unchanged)
`status=ACTIVE_INCOMPLETE`, `last_updated_utc=2026-11-06T12:27:02Z`, `historical_rank_coverage_state=NOT_PROVEN_COMPLETE`, `rank_frontier_exhausted=false`, `candidate_page_cursor=6347`, `candidates_verified=220`, `candidates_blocked=6127`, `expanding_universe_target_met=true`, panel `2023-01-01..2026-10-31`. Catalog exhausted.

## Gates
- **November 2026 probe:** verdict blocked (`probe_month=2026-11`, `target_published=false`, latest probe 2026-11-11). Probe result only — NOT the H10 cutoff-gate decision. **Do not re-probe before 2026-11-30.**
- **H10 cutoff gate:** UNBLOCKED by the published October 2026 archive (real probe 2026-11-05T10:38:51Z, `cutoff_probe_20261105T103851Z.json`, `probe_month=2026-10`, `target_published=true`; `run_manifest.json` -> `latest_archive_probe`). Gate date required 2026-10-29; November 404s do not block H10.
- **H10 candidate:** CANDIDATE_UNVALIDATED / EXPLORATORY_ONLY / EVALUATED_NULL_DIFF_IMMATURE; k not advanced. Inspected 003 holdout is exploratory evidence only, never fresh confirmation.

## Current unblocked work
**Completed this session:** the input-coverage lineage audit above — the first session in this program to quantify and attribute the reduced eligible-asset count behind the sealed canonical block. It is descriptive evidence: it does not change, weaken or strengthen the canonical result, and it does not evaluate any outcome.

## Next action (explicit)
**On/after 2026-11-30 (date-gated sequence):**
1. `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`
2. If `target_published=true`: refresh free public data only (Coin Metrics Community API + Binance Public Data Archive); run `python3 -m compileall -q scripts tests && python3 -m unittest discover -s tests`; verify canonical hash `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` unchanged; run fresh sealed H10 block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/` with `--look-number 1` (30-day maturity, `MIN_ASSETS_DECIMAL=20`, trailing-decile, 0.05 economic threshold, sequential `alpha_k = 0.05/(k*(k+1))`).
3. Require `n_high > 0 AND n_low > 0` before any confirmatory claim. If still immature, record outcome and **do not advance k**. Preserve all frozen artifacts/configs unchanged.
4. **Note for that pass:** the fresh block will again run on 26 assets unless the F1 gap is repaired. Do not repair the current panels (they are sealed inputs); if a full-panel estimate is wanted, follow the separate new-ID route below.

**Before 2026-11-30 (only on a genuine bounded no-cost gap):** acceptable work is a reproducible tracked code/audit/test defect (excluding env-only dependency absence), a missing guard against frozen-artifact mutation, or reference-consistency drift — only if it does not alter frozen result artifacts, configs, scripts, tests, docs, prompts, `research_state/hypothesis_registry.json` or `research_state/universe_frontier.json`. If nothing genuine appears, record "no unblocked task exists" with verification evidence and stop; avoid repeated idle verification churn.

**Separate new-ID route for F1 (NOT authorized this session):** repairing the input coverage requires a NEW hypothesis/experiment ID, a new preregistration, and a new artifact path, because it changes the inputs of a sealed artifact. Do not overwrite `data/panels/` or `data/raw/`. Minimal change: fetch only the 168 missing keyless zips (`4 symbols x 21 months x 2 series`, months `2025-01..2026-09`) from `https://data.binance.vision/data/futures/um`, rebuild into a NEW panel directory, and keep the current 003 block, panels, hashes and findings byte-unchanged. State explicitly that the new arm is EXPLORATORY_ONLY unless the full confirmatory gates are re-run on admissible data.

## Constraints (hard)
Free public data only; historical research only (no orders/live/paper trading); preserve DISPERSION-001/002 and frozen 003 artifacts/configs/inputs; no look-ahead/fabrication/forward-fill; today's rank ≠ historical truth; complete multiple-testing correction for any claim; do not reuse inspected holdout as fresh confirmation.

## Resume notes
Leave clean state; update this handoff and `research_state/agent_task_message.md` with verified evidence; never write "wait for a new experiment ID."

(End of file - total 76 lines)