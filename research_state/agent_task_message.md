## Initial task for next agent

Read `research_state/agent_handoff.md` (current **20261107T232118Z**), this file, `AGENTS.md`, `docs/research_protocol.md`, `prompts/continuous_research_operating_contract_v1.md`. Verify state before acting.

### Verified state (20261107T232118Z, HEAD `58bcd483`)
- **Frozen hashes:** H004V106 canonical `7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390` (unchanged); H10 fresh IMMATURE `324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f` (repaired 2026-11-07, additive only; historical `9162561e…`, `4106f421…`, `9bdee66f…` preserved in registry notes). `git diff HEAD -- forward_block/` empty; `git diff --name-only -- artifacts/ configs/` shows ONLY the H10 fresh block (8 added confirmatory-gate fields).
- `compileall -q scripts tests` EXIT=0; `python3 -m unittest discover -s tests` **325 run, 0 failures, 1 skipped (OK)**; `scripts/audit_preregistration_coverage.py` pass=True (14/0/0); `scripts/audit_prereg_and_h10_fresh_references.py` pass=True scanned=13 prereg=9 frozen_prereg=0 h10=1 forward_block=1 h10_variant=2 critical=0 errors=0 info=0; `scripts/audit_integrity_audit_references.py` pass=True scanned=14 critical=0 errors=0 info=8. Verified test claim 325/325/0 (`research_state/run_manifest.json:latest_verified_test_claim`).
- **H10 fresh block now carries its confirmatory gate** (prereg sec 4.2): `confirmatory_claim_allowed=false`, `confirmatory_holm_significant=null`, `confirmatory_note` (pending caller), `economic_significance_met=false`, `economic_significance_threshold=0.05`, `high_low_diff_net_1x_abs=null`, `min_state_formations=5`, `state_count_floor_met=false`. Outcome fields unchanged: n_formations=1, n_high=0, n_low=0, n_mid=1, high_low_diff_net_1x=null, evaluated_utc preserved 2026-11-02T15:18:56Z. A throwaway subprocess run reproduces ALL fields including these 8 (`tests/test_h10_fresh_block_current.py`).
- **No bounded no-cost delta exists before 2026-11-30.** Cutoff gate: H10 UNBLOCKED (October 2026 archive). November 2026 BLOCKED; **re-probe forbidden before 2026-11-30**. H10 fresh block IMMATURE (n_formations=1); first structurally classifiable cutoff projected 2026-11-30 (~31 formations). k not advanced. No confirmatory claim.

### Immediate next action
1. **On/after 2026-11-30:** run `python3 scripts/probe_cutoff_gate.py --probe-month 2026-11`. If usable, refresh required free public data; run fresh sealed block only into `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/`. Use H10 prereg + alpha-spending (k=1). Record all outcomes. The artifact already carries the confirmatory-gate machinery; a mature evaluation will populate `confirmatory_*` from the real outcome.
2. **Before 2026-11-30:** act only if a genuine bounded no-cost gap is found. Otherwise keep next action as (1) and record (3).
3. **If no bounded delta:** record that no unblocked task exists and keep next action as (1).

### Hard rules
- Never relax 30-day maturity, MIN_ASSETS_DECILES=20, trailing-decile rule, or 0.05 threshold.
- Never open canonical sealed holdout (`forward_block/`); fresh outputs go only to `forward_block_h10_fresh/` or a new uniquely identified path.
- Never use today's rank as historical truth. Never fabricate metrics. Preserve old artifacts/configs/results.
- Do not modify immutable closed preregistration/experiment records.
- Allocate unique IDs/preregister for new exploratory work. Keep confirmatory and exploratory tracks separate.
- A passing workflow/test proves only what it covers. No confirmatory claim from exploratory/integrity work.

(End of file)