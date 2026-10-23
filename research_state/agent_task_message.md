Initial task message for the next agent — HARMONY-CRYPTO-EDGE-004-DISPERSION-002

Prior experiment HARMONY-CRYPTO-EDGE-004-DISPERSION-001 is complete, verified, and archived. No recomputation, no artifact changes, and no further analysis are required on those artifacts.

New follow-up experiment initialized:
- Experiment ID: HARMONY-CRYPTO-EDGE-004-DISPERSION-002
- Based on: HARMONY-CRYPTO-EDGE-004-DISPERSION-001
- Config: configs/dispersion_momentum_followup_v1.json
- Artifacts: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-002/
- Setup: experiment_setup.json created with free-data, point-in-time, no-lookahead, chronological OOS controls

Follow-up objectives (from config):
- Robustness test of dispersion-conditioned momentum spread
- Vary dispersion estimation windows (30/90/365 days), momentum lookbacks/horizons (14/30/60), dispersion estimators (std dev, MAD-scaled), and state rules (outer deciles vs median split)
- 108 configurations total (H004F001..H004F108)
- Primary anchor analogous to prior: 30d/30d/std dev/365d/outer-deciles (H004F033)

Next steps for agent:
1. Copy/adapt data pipeline from prior experiment or reuse existing data panels if compatible and approved. Do NOT reuse artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/ as inputs without explicit approval - only read for context as instructed.
2. Construct point-in-time universe following same rules as prior experiment.
3. Run data gate (fail-closed). Verify free-data boundary intact.
4. Execute phases for follow-up grid with proper controls.
5. Generate summary/report and update handoff.

Context to read before starting:
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/summary.json
- artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-001/report.md
- configs/dispersion_momentum_followup_v1.json
- prompts/harmony_crypto_edge_004.md (if exists)
