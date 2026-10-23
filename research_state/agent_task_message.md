Initial task message for the next agent — HARMONY-CRYPTO-EDGE-004-DISPERSION-002

Status: Complete and verified. Robustness & inference tightening done; paired block-bootstrap CIs applied to phase_c_summary.json and phase_f_summary.json (replaced degenerate point-estimate CIs); report updated; robustness_inference_summary.json updated with inference_fix_applied block. Committed at 9f08240; working tree clean.

Reproducibility fix applied this session: scripts/fix_inference.py was committed pointing at DISPRESSION-001 and indexing a split schema absent from 002, so it could not have produced the artifacts it claimed. It now targets DISPERSION-002 and derives Phase F splits from the formation panel; re-running it reproduces the committed artifacts byte-for-byte. New regression test tests/test_inference_repro.py (5 tests) pins this. `python -m unittest discover -s tests -v` passes 15/15.

No further authorized work on DISPERSION-002 unless a new experiment ID is issued. Preserve controls: free-data-only, point-in-time universe, no-lookahead, chronological OOS. Do not modify grid manifest/config/data pipeline or DISPERSION-002 artifacts.

Await a new experiment ID before making any changes. Verification command: `python -m unittest discover -s tests -v` (must stay green; pytest is not installed in this environment, so use unittest).