# Preregistration — H004V106 Planned Archive Source-Coverage Probe

**Program:** HARMONY-CRYPTO-EDGE-004
**Experiment ID:** HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001
**Hypothesis ID:** H43 (next_sequence_number 42 → 43)
**Status:** EXPLORATORY_ONLY
**Created:** 2026-11-16T14:22:05Z
**Author:** automated research agent

## 1. Why this study exists

`HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001` (H40, `EXPLORATORY_ONLY`) concluded that extending committed Binance kline/funding panel coverage to the 188 H39 union assets that lack committed panels is **feasible in principle** (`PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE`): all 188 have a committed verified Binance USD-M perpetual symbol mapping and committed Coin Metrics `CapMrktEstUSD` observations in the 2023-01-01..2026-10-31 window, and the gap is genuinely unfilled.

`HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001` (H41, `EXPLORATORY_ONLY`) then enumerated a bounded, deterministic 920-entry monthly `(symbol, kind, month)` acquisition plan for a 10-asset PIT subset, but every one of those 920 entries carries `published_verified: null`, `sha256: null` and `note: planning_target_only_not_verified`.

**Demonstrable gap:** no committed artifact verifies that the free public Binance Public Data Archive actually serves the H41-planned files. H40 asserts feasibility *in principle* from committed metadata; H41 enumerates *requested* targets and explicitly states they are "NOT proof of archive publication". H41 §8 names exactly this bounded keyless probe as the next step. Until the archive's real per-file availability is measured, any downstream acquisition step is planning against unverified URLs.

## 2. Question and estimand

**Question:** Of the 920 deterministic H41-planned monthly archive entries (10 assets × {klines, fundingRate} × the asset's required study months), how many does the Binance Public Data Archive actually serve (HTTP 200) right now, and what is the per-kind / per-asset availability?

**Estimand (descriptive only):** a per-entry record `{asset, symbol, kind, month, archive_url, http_status, content_length, error}` plus aggregate counts `{n_total, n_200, n_404, n_other_status, n_error, coverage_frac, per_kind, per_asset}`, a positive control, and a negative control. **No content is downloaded (HTTP HEAD only), no panels are constructed, and no returns, spreads, dispersion states, p-values, costs or inference are computed.**

## 3. Method (frozen before computation)

1. **Input set:** the committed H41 plan artifact `artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json` (read-only; SHA256 pinned to `39e740b65fbe65541aa42f55b0e231469c49dda7e04d9e22e04eae3ac9ce441b`).
2. **Targets:** every `plan_entries[*]` object, verbatim, giving `(symbol, kind, month, archive_url)`.
3. **Probe:** keyless HTTP **HEAD** `GET`-metadata request to each `archive_url` against `https://data.binance.vision`, bounded concurrency (max 8 workers), per-request timeout 15 s, up to 3 attempts with exponential backoff on transient errors. Record HTTP status (200/404/other) and `Content-Length`; **never read the response body**.
4. **Positive control:** `BTCUSDT` monthly klines and monthly fundingRate for `2023-01` (long-published) must both return HTTP 200. If not, the probe is inconclusive (archive unreachable / control failure) and the label is `PROBE_CONTROL_FAILED`.
5. **Negative control:** a well-formed but far-future URL (`BTCUSDT` monthly klines for `2099-01`) must return HTTP 404, demonstrating the probe distinguishes absence from presence without touching the date-gated `2026-11` cutoff month.
6. **Frozen-hash check (read-only):** verify the canonical forward block, H10 fresh block, grid result ledger, universe frontier, grid v3 config, H39 rank-breadth audit and the H41 plan SHA256 before and after.

## 4. Decision rule (predeclared, outcome-blind)

Let `n_total` = number of planned entries probed and `n_200` = number returning HTTP 200 with no error.

- **`PROBE_CONTROL_FAILED`** — the positive control did not return HTTP 200 for both endpoints (archive unreachable or control missing); result is inconclusive regardless of target statuses.
- **`ARCHIVE_PLAN_FULLY_SERVED`** — control OK, `n_error == 0`, and `n_200 == n_total` (every planned entry is served).
- **`ARCHIVE_PLAN_PARTIALLY_SERVED`** — control OK and `0 < n_200 < n_total` (some planned months/files are missing; the deficit is the informative result).
- **`ARCHIVE_PLAN_UNSERVED`** — control OK but `n_200 == 0`.

Any 404 is a genuine availability signal for that `(symbol, kind, month)` (e.g. a month before listing or a not-yet-published archive). Missing files are **never** fabricated, interpolated or backfilled.

## 5. Safeguards (hard constraints honored)

- **Free public data only; keyless.** No API keys, no paid services, no credentials, no non-public endpoints. Only `https://data.binance.vision` HEAD metadata requests.
- **No downloads / no content.** HEAD only; response bodies are never read. No panel or data file is constructed or written.
- **Historical research only.** No orders, no live/paper trading, no today's-rank-as-history.
- **Date gate respected.** This probe covers the historical study window 2023-01..2026-10 for the 10-asset subset; it does **not** probe the date-gated `probe_month=2026-11` cutoff and does not re-open the H10 cutoff question.
- **No outcomes.** No returns, spreads, dispersion states, p-values, costs or inference.
- **Frozen artifacts untouched.** Canonical/confirmatory artifacts, configs, ledgers, frontier, sealed holdout and the H39/H40/H41 audits are read-only and hash-verified. The inspected canonical forward block is not reused as fresh evidence.
- **Track separation.** `EXPLORATORY_ONLY` source-coverage evidence; cannot validate, replace or unlock H1/H6/H7/H10 or any confirmatory track.

## 6. Expected outputs

- This preregistration.
- `integrity_audit/H004V106_panel_archive_probe_<ts>.json` (per-entry statuses, controls, aggregates, decision, frozen-hash verification, explicit non-claims).
- `scripts/panel_archive_probe.py` (import-safe pure helpers + CLI).
- `tests/test_panel_archive_probe.py` (hermetic; no network).
- Registry H43 entry (`EXPLORATORY_ONLY`, `source_coverage_only`) and `tests/test_continuous_research_contract.py` bump in the same change.