#!/usr/bin/env python3
"""
H10 Fresh Forward Block Maturity-Timeline Milestone Audit (DISP-003-H10-MATURITY)

Read-only decomposition of the H10 fresh sealed forward block's maturity into
distinct, quantified milestones derived from the frozen implementation constants
and the committed merged daily panel index. No outcomes, returns, spreads,
p-values or inference are computed; no market data is re-fetched. This is a
planning/diagnostic on already-inspected development evidence (EXPLORATORY_ONLY).

Milestones (frozen rule source: scripts/eval_forward_block.py + scripts/alpha_spending.py):
  M1  first mature look  : n_high>0 AND n_low>0  -> look counter k advances.
      Requires >= MIN_PRIOR_DISPERSIONS + 2 = 32 in-block formations (the first
      MIN_PRIOR_DISPERSIONS+1 = 31st formation is the first classifiable; a second
      classifiable formation is needed so one can be high and one low).
  M2  magnitude estimable: n_high>=MIN_STATE_FORMATIONS AND n_low>=MIN_STATE_FORMATIONS.
  M3  confirmatory claim : M2 AND |high_low_diff_net_1x|>=ECONOMIC_SIGNIFICANCE_THRESHOLD
      AND Holm-significant at the per-look alpha_k.

This module is stdlib-only (no pandas/numpy) so it is import-safe and hermetic.
"""

from __future__ import annotations

import csv
import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
FRESH_BLOCK_PATH = ARTIFACT_DIR / "forward_block_h10_fresh/forward_block_evaluation.json"
PANEL_DIR = ARTIFACT_DIR / "data" / "panels"
KLINES_BTC_PATH = PANEL_DIR / "binance_klines_BTCUSDT.csv"
CANONICAL_BLOCK_PATH = ARTIFACT_DIR / "forward_block/forward_block_evaluation.json"
GRID_LEDGER_PATH = ARTIFACT_DIR / "grid_result_ledger.json"
UNIVERSE_FRONTIER_PATH = Path("research_state/universe_frontier.json")
GRID_CONFIG_PATH = Path("configs/dispersion_momentum_grid_v3.json")
EVAL_SRC_PATH = Path("scripts/eval_forward_block.py")

# Frozen implementation constants (verified against scripts/eval_forward_block.py
# by the constant-drift checks below; never re-derived from outcomes).
MIN_PRIOR_DISPERSIONS = 30
MIN_STATE_FORMATIONS = 5
ECONOMIC_SIGNIFICANCE_THRESHOLD = 0.05
BASE_COST_TURN = 0.0005
COST_1X = BASE_COST_TURN * 2.0  # 0.001
FORWARD_HORIZON_DAYS = 30

# Frozen artifact hashes (unchanged since sealing; verified by this audit).
EXPECTED_CANONICAL_SHA256 = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH_BLOCK_SHA256 = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER_SHA256 = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER_SHA256 = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"
EXPECTED_GRID_CONFIG_SHA256 = "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    with path.open("r") as f:
        return f.read()


def check_equal(name: str, expected: Any, actual: Any, results: list[dict]) -> None:
    passed = expected == actual
    results.append({
        "check": name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
    })


def check_in_text(name: str, expected_substring: str, text: str, results: list[dict]) -> None:
    passed = expected_substring in text
    results.append({
        "check": name,
        "expected": expected_substring,
        "actual": "found" if passed else "not found",
        "passed": passed,
    })


def kline_dates_in_window(csv_path: Path, start: str, end: str) -> list[str]:
    """Return the sorted unique UTC date strings (YYYY-MM-DD) present in a Binance
    kline CSV's ``open_time`` column that fall within [start, end] (inclusive).

    ``open_time`` is milliseconds since the Unix epoch (UTC). Pure read of the
    committed panel; no network.
    """
    out: set[str] = set()
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ms = int(row["open_time"])
            d = _dt.datetime.fromtimestamp(ms / 1000.0, tz=_dt.timezone.utc).strftime("%Y-%m-%d")
            if start <= d <= end:
                out.add(d)
    return sorted(out)


def _in_block_formations(cutoff_index: int, horizon: int, block_start_index: int) -> int:
    """Number of merged-index dates in [block_start_index, cutoff_index - horizon].

    Mirrors scripts/eval_forward_block.py: a formation at index i is included iff
    block_start_index <= i <= cutoff_index - horizon (30-day maturity)."""
    return max(0, cutoff_index - horizon - block_start_index + 1)


def compute_maturity_milestones(
    *,
    block_start: str,
    last_observed_date: str,
    block_start_index: int,
    last_observed_index: int,
    min_prior: int = MIN_PRIOR_DISPERSIONS,
    min_state_formations: int = MIN_STATE_FORMATIONS,
    horizon: int = FORWARD_HORIZON_DAYS,
    economic_threshold: float = ECONOMIC_SIGNIFICANCE_THRESHOLD,
) -> dict[str, Any]:
    """Pure milestone decomposition from the merged-index geometry and constants.

    ``block_start_index`` / ``last_observed_index`` are 0-based positions of the
    block start and the last observed panel date in the merged daily index.
    """
    current_cutoff_index = last_observed_index
    current_in_block = _in_block_formations(current_cutoff_index, horizon, block_start_index)
    current_classifiable = max(0, current_in_block - min_prior)

    # M1: first mature look needs >=2 classifiable formations (one high, one low).
    m1_min_in_block = min_prior + 2
    # cutoff_index >= block_start_index + min_prior + horizon + 1
    m1_cutoff_offset = min_prior + horizon + 1
    m1_cutoff_index = block_start_index + m1_cutoff_offset
    m1_additional_in_block_needed = max(0, m1_min_in_block - current_in_block)
    m1_additional_index_positions = max(0, m1_cutoff_index - current_cutoff_index)
    m1_earliest_cutoff_date = (
        _dt.date.fromisoformat(last_observed_date)
        + _dt.timedelta(days=m1_additional_index_positions)
    ).isoformat()

    # November 2026 vintage cutoff: last complete November candle = last observed
    # + 30 calendar days (daily cadence). Index offset = 30 positions (no gaps assumed).
    nov_cutoff_date = (
        _dt.date.fromisoformat(last_observed_date) + _dt.timedelta(days=30)
    ).isoformat()
    nov_cutoff_index = last_observed_index + 30
    nov_in_block = _in_block_formations(nov_cutoff_index, horizon, block_start_index)
    nov_classifiable = max(0, nov_in_block - min_prior)
    nov_m1_possible = nov_classifiable >= 2

    # M2: magnitude estimable needs n_high>=min_state AND n_low>=min_state.
    # Outer-decile classification puts ~10% of classifiable formations in each tail,
    # so ~min_state/0.1 classifiable formations yield ~min_state in EACH tail at the
    # same time (the tails are disjoint ~10%/~10% slices of the classifiable set).
    # Expected-value order-of-magnitude estimate only.
    tail_fraction = 0.10
    classifiable_needed = math.ceil(min_state_formations / tail_fraction)
    m2_estimate_in_block = min_prior + classifiable_needed
    m2_hard_lower_bound = min_prior + 2 * min_state_formations

    return {
        "current_cutoff_index": current_cutoff_index,
        "current_in_block_formations": current_in_block,
        "current_classifiable_formations": current_classifiable,
        "M1_first_mature_look": {
            "condition": "n_high>0 AND n_low>0",
            "min_in_block_formations": m1_min_in_block,
            "cutoff_index_offset_from_block_start": m1_cutoff_offset,
            "additional_in_block_formations_needed": m1_additional_in_block_needed,
            "additional_index_positions_needed": m1_additional_index_positions,
            "earliest_cutoff_calendar_estimate": m1_earliest_cutoff_date,
            "earliest_cutoff_note": (
                "necessary-condition estimate assuming daily merged-index cadence and "
                "no further archive gaps; the exact date shifts later with any gap"
            ),
        },
        "M2_magnitude_estimable": {
            "condition": f"n_high>={min_state_formations} AND n_low>={min_state_formations}",
            "hard_lower_bound_in_block_formations": m2_hard_lower_bound,
            "decile_based_estimate_in_block_formations": m2_estimate_in_block,
            "note": (
                "approximate expected-value estimate (outer deciles ~10% per tail); the "
                "exact count is data-dependent on the realized dispersion sequence and "
                "cannot be fixed before the dispersions are observed"
            ),
        },
        "M3_confirmatory_claim": {
            "condition": (
                f"M2 AND |high_low_diff_net_1x|>={economic_threshold} AND "
                "Holm-significant across the complete 216-cell family at alpha_k"
            ),
            "note": "not reachable until M2",
        },
        "november_2026_vintage": {
            "cutoff_date": nov_cutoff_date,
            "cutoff_index": nov_cutoff_index,
            "in_block_formations": nov_in_block,
            "classifiable_formations": nov_classifiable,
            "m1_possible": nov_m1_possible,
            "note": (
                "the November 2026 vintage cutoff yields fewer than two classifiable "
                "formations, so the first mature look (M1) is impossible at this cutoff"
            ),
        },
    }


def audit_h10_maturity_timeline() -> dict[str, Any]:
    """Main audit: read-only milestone decomposition + consistency checks."""
    results: list[dict] = []

    fresh_block = load_json(FRESH_BLOCK_PATH)
    eval_src = load_text(EVAL_SRC_PATH)

    # Merged daily index geometry from the committed BTC kline panel (full coverage).
    block_start = str(fresh_block.get("forward_block_start"))
    all_btc_dates = kline_dates_in_window(KLINES_BTC_PATH, "0000-00-00", "9999-99-99")
    last_observed_date = all_btc_dates[-1]
    block_start_index = all_btc_dates.index(block_start)
    last_observed_index = len(all_btc_dates) - 1
    observed_window_dates = kline_dates_in_window(KLINES_BTC_PATH, block_start, "2026-10-31")

    ms = compute_maturity_milestones(
        block_start=block_start,
        last_observed_date=last_observed_date,
        block_start_index=block_start_index,
        last_observed_index=last_observed_index,
    )
    m1 = ms["M1_first_mature_look"]
    m2 = ms["M2_magnitude_estimable"]
    m3 = ms["M3_confirmatory_claim"]
    nov = ms["november_2026_vintage"]

    # --- Current block state matches the artifact and is IMMATURE ---
    check_equal("block_is_immature_n_high", 0, fresh_block.get("n_high"), results)
    check_equal("block_is_immature_n_low", 0, fresh_block.get("n_low"), results)
    check_equal("n_formations_matches_artifact", 1, fresh_block.get("n_formations"), results)
    check_equal("n_formations_matches_geometry",
                fresh_block.get("n_formations"), ms["current_in_block_formations"], results)
    check_equal("current_classifiable_zero", 0, ms["current_classifiable_formations"], results)
    check_equal("block_sealed", True, fresh_block.get("block_sealed"), results)
    check_equal("high_low_diff_net_1x_null", None, fresh_block.get("high_low_diff_net_1x"), results)
    check_equal("last_allowed_formation_date",
                "2026-09-30", fresh_block.get("last_allowed_formation_date"), results)

    # --- Sequential look not consumed (alpha budget intact) ---
    check_equal("look_not_mature", False, fresh_block.get("sequential_look_mature"), results)
    check_equal("look_consumes_no_budget",
                False, fresh_block.get("sequential_look_consumes_budget"), results)
    check_equal("look_number_is_one", 1, fresh_block.get("sequential_look_number"), results)
    check_equal("alpha_k_is_alpha_1", 0.025, fresh_block.get("sequential_alpha_k"), results)
    check_equal("cumulative_spend_is_alpha_1",
                0.025, fresh_block.get("sequential_cumulative_spend"), results)
    check_equal("remaining_budget_is_half",
                0.025, fresh_block.get("sequential_remaining_budget"), results)

    # --- Decision gates all unmet ---
    check_equal("economic_significance_not_met",
                False, fresh_block.get("economic_significance_met"), results)
    check_equal("state_count_floor_not_met",
                False, fresh_block.get("state_count_floor_met"), results)
    check_equal("confirmatory_not_allowed",
                False, fresh_block.get("confirmatory_claim_allowed"), results)
    check_equal("economic_threshold_constant",
                ECONOMIC_SIGNIFICANCE_THRESHOLD, fresh_block.get("economic_significance_threshold"), results)
    check_equal("min_state_formations_constant",
                MIN_STATE_FORMATIONS, fresh_block.get("min_state_formations"), results)

    # --- Endpoint is net of cost ---
    formation = fresh_block["formations"][0]
    expected_net = formation["spread_gross"] - COST_1X
    check_equal("formation_net_cost_consistent",
                round(expected_net, 12), round(formation["spread_net_1x"], 12), results)

    # --- M1 milestone derivation ---
    check_equal("m1_min_in_block_formations", 32, m1["min_in_block_formations"], results)
    check_equal("m1_cutoff_index_offset", 61, m1["cutoff_index_offset_from_block_start"], results)
    check_equal("m1_additional_in_block_needed", 31, m1["additional_in_block_formations_needed"], results)
    check_equal("m1_earliest_cutoff_calendar_estimate",
                "2026-12-01", m1["earliest_cutoff_calendar_estimate"], results)

    # --- November vintage is insufficient for M1 ---
    check_equal("november_cutoff_date", "2026-11-30", nov["cutoff_date"], results)
    check_equal("november_in_block_formations", 31, nov["in_block_formations"], results)
    check_equal("november_classifiable_formations", 1, nov["classifiable_formations"], results)
    check_equal("november_m1_impossible", False, nov["m1_possible"], results)

    # --- M2/M3 present and labelled approximate / gated ---
    check_equal("m2_condition", "n_high>=5 AND n_low>=5", m2["condition"], results)
    check_equal("m3_gated_on_m2", "not reachable until M2", m3["note"], results)

    # --- Merged-index cadence evidence (grounds the geometry) ---
    check_equal("observed_window_dates", 31, len(observed_window_dates), results)
    check_equal("archive_gap_2026_10_28_absent", True, "2026-10-28" not in all_btc_dates, results)

    # --- Constant drift guard: frozen implementation unchanged ---
    check_in_text("constant_min_prior", "MIN_PRIOR_DISPERSIONS = 30", eval_src, results)
    check_in_text("constant_min_state", "MIN_STATE_FORMATIONS = 5", eval_src, results)
    check_in_text("constant_econ_threshold", "ECONOMIC_SIGNIFICANCE_THRESHOLD = 0.05", eval_src, results)
    check_in_text("constant_base_cost", "BASE_COST_TURN = 0.0005", eval_src, results)
    check_in_text("constant_horizon", '"forward_horizon_days": 30', eval_src, results)

    # --- Frozen hash verification ---
    check_equal("canonical_block_sha256",
                EXPECTED_CANONICAL_SHA256, sha256_file(CANONICAL_BLOCK_PATH), results)
    check_equal("fresh_block_sha256",
                EXPECTED_FRESH_BLOCK_SHA256, sha256_file(FRESH_BLOCK_PATH), results)
    check_equal("grid_ledger_sha256",
                EXPECTED_GRID_LEDGER_SHA256, sha256_file(GRID_LEDGER_PATH), results)
    check_equal("universe_frontier_sha256",
                EXPECTED_FRONTIER_SHA256, sha256_file(UNIVERSE_FRONTIER_PATH), results)
    check_equal("grid_config_sha256",
                EXPECTED_GRID_CONFIG_SHA256, sha256_file(GRID_CONFIG_PATH), results)

    all_passed = all(r["passed"] for r in results)
    verdict = "PASS" if all_passed else "FAIL"

    return {
        "audit_id": "H004V106_H10_MATURITY_TIMELINE_AUDIT",
        "hypothesis_id": "H35",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003",
        "status": "EXPLORATORY_ONLY",
        "verdict": verdict,
        "generated_utc": "2026-11-15T12:30:00Z",
        "artifact_sha256": sha256_file(FRESH_BLOCK_PATH),
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/"
            "H004V106_H10_MATURITY_TIMELINE_AUDIT_v1.md"
        ),
        "script": "scripts/h10_maturity_timeline_audit.py",
        "frozen_artifacts_modified": [],
        "checks_total": len(results),
        "checks_passed": sum(1 for r in results if r["passed"]),
        "checks_failed": sum(1 for r in results if not r["passed"]),
        "checks": results,
        "milestones": ms,
        "interpretation": (
            "The H10 fresh block is IMMATURE (1 in-block formation, 0 classifiable). "
            "The first mature look (M1: n_high>0 AND n_low>0) requires >=32 in-block "
            "daily formations, i.e. a merged-index cutoff ~2026-12-01; the November "
            "2026 vintage cutoff (2026-11-30) yields only 31 in-block / 1 classifiable "
            "formation, so M1 is impossible at that cutoff. M2 (n_high>=5 AND n_low>=5) "
            "and M3 (confirmatory) are strictly later and data-dependent. The sequential "
            "alpha-spending budget (k=1, alpha_k=0.025) is unconsumed. No outcomes are "
            "computed; this is a planning/diagnostic on already-inspected evidence."
        ),
        "note": (
            "EXPLORATORY_ONLY: maturity-timeline diagnostic on already-inspected "
            "development evidence. Does not validate, replace or unlock any confirmatory "
            "track and does not change the frozen H10 preregistration or date gate."
        ),
    }


def main() -> int:
    audit_result = audit_h10_maturity_timeline()

    out_dir = ARTIFACT_DIR / "integrity_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "H004V106_H10_maturity_timeline_2026-11-15T12-30-00Z.json"
    with out_path.open("w") as f:
        json.dump(audit_result, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"Verdict: {audit_result['verdict']}")
    print(f"Checks: {audit_result['checks_passed']}/{audit_result['checks_total']} passed")
    for check in audit_result["checks"]:
        if not check["passed"]:
            print(f"  FAIL: {check['check']} (expected={check['expected']}, actual={check['actual']})")

    return 0 if audit_result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())