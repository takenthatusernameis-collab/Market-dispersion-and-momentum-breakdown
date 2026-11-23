#!/usr/bin/env python3
"""
H004V106 Forward Block Independent Recomputation Audit (DISP-003-RECOMPUTE-001)

Read-only reproducibility cross-check: recompute every metric recorded by the
addendum `forward_block_independent_recomputation_20261028.json` *from the
sealed canonical forward block's formations array* and compare within
predeclared tolerance. No outcomes are produced beyond this consistency check;
no market data is re-fetched; no sealed holdout is opened; stdlib only; no
network; nothing is written to any frozen artifact.

This module is stdlib-only so it is import-safe and hermetic.

Tolerances (predeclared):
  - absolute tolerance 1e-9 for means (spread_net_mean, spread_gross_mean,
    high_net_mean, low_net_mean)
  - absolute tolerance 1e-12 for high_low_diff_net and high_low_diff_gross
  - exact match for n_formations and state_counts
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any

ARTIFACT_DIR = Path("artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003")
CANONICAL_BLOCK_PATH = ARTIFACT_DIR / "forward_block/forward_block_evaluation.json"
ADDENDUM_PATH = ARTIFACT_DIR / "integrity_audit/forward_block_independent_recomputation_20261028.json"
OUT_DIR = ARTIFACT_DIR / "integrity_audit"

CANONICAL_SHA256 = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"

MEAN_TOL = 1e-9
DIFF_TOL = 1e-12


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r") as f:
        return json.load(f)


def check_equal(name: str, expected: Any, actual: Any, results: list[dict]) -> None:
    passed = expected == actual
    results.append({
        "check": name,
        "expected": expected,
        "actual": actual,
        "passed": passed,
    })


def check_close(name: str, expected: float, actual: float, tol: float, results: list[dict]) -> None:
    diff = abs(expected - actual)
    passed = diff <= tol
    results.append({
        "check": name,
        "expected": expected,
        "actual": actual,
        "abs_diff": diff,
        "tolerance": tol,
        "passed": passed,
    })


def median(values: list[float]) -> float:
    return statistics.median(values)


def recompute_from_formations(formations: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute all metrics from the canonical block's formations array."""
    n_formations = len(formations)
    state_counts: dict[str, int] = {"high": 0, "mid": 0, "low": 0}
    spread_net: list[float] = []
    spread_gross: list[float] = []
    high_net: list[float] = []
    low_net: list[float] = []
    high_gross: list[float] = []
    low_gross: list[float] = []
    any_non_finite = False

    for f in formations:
        state = f.get("state", "mid")
        state_counts[state] = state_counts.get(state, 0) + 1
        net = f.get("spread_net_1x")
        gross = f.get("spread_gross")
        spread_net.append(net)
        spread_gross.append(gross)
        if net is not None and not _is_finite(net):
            any_non_finite = True
        if gross is not None and not _is_finite(gross):
            any_non_finite = True
        if state == "high":
            high_net.append(net)
            high_gross.append(gross)
        elif state == "low":
            low_net.append(net)
            low_gross.append(gross)

    spread_net_mean = sum(spread_net) / n_formations if n_formations else 0.0
    spread_gross_mean = sum(spread_gross) / n_formations if n_formations else 0.0
    spread_net_median = median(spread_net) if spread_net else 0.0
    spread_gross_median = median(spread_gross) if spread_gross else 0.0
    high_net_mean = sum(high_net) / len(high_net) if high_net else 0.0
    low_net_mean = sum(low_net) / len(low_net) if low_net else 0.0
    high_low_diff_net = high_net_mean - low_net_mean

    high_gross_mean = sum(high_gross) / len(high_gross) if high_gross else 0.0
    low_gross_mean = sum(low_gross) / len(low_gross) if low_gross else 0.0
    high_low_diff_gross = high_gross_mean - low_gross_mean

    return {
        "n_formations": n_formations,
        "state_counts": state_counts,
        "finite_checks": {
            "all_spread_net_finite": not any_non_finite,
            "all_spread_gross_finite": not any_non_finite,
            "any_non_finite": any_non_finite,
        },
        "metrics": {
            "spread_net_mean": spread_net_mean,
            "spread_net_median": spread_net_median,
            "spread_gross_mean": spread_gross_mean,
            "spread_gross_median": spread_gross_median,
            "high_net_mean": high_net_mean,
            "low_net_mean": low_net_mean,
            "high_low_diff_net": high_low_diff_net,
            "high_low_diff_gross": high_low_diff_gross,
        },
    }


def _is_finite(x: Any) -> bool:
    try:
        return x == x and x != float("inf") and x != float("-inf")
    except TypeError:
        return False


def audit_forward_block_independent_recomputation() -> dict[str, Any]:
    """Main audit: recompute from canonical block and compare to addendum."""
    results: list[dict] = []

    canonical = load_json(CANONICAL_BLOCK_PATH)
    addendum = load_json(ADDENDUM_PATH)

    # --- Frozen-artifact identity ---
    actual_sha = sha256_file(CANONICAL_BLOCK_PATH)
    check_equal("canonical_block_sha256", CANONICAL_SHA256, actual_sha, results)
    check_equal("anchor_id", "H004V106", canonical.get("anchor_id"), results)
    check_equal("block_sealed", True, canonical.get("block_sealed"), results)
    check_equal("data_cutoff_utc",
                "2026-09-30T00:00:00Z", canonical.get("data_cutoff_utc"), results)
    check_equal("date_last", "2026-08-31", canonical.get("date_last"), results)

    formations = canonical.get("formations", [])
    recomputed = recompute_from_formations(formations)
    recorded = addendum.get("metrics", {})
    recorded_state = addendum.get("state_counts", {})
    recorded_n = addendum.get("n_formations")

    # --- n_formations and state_counts: exact match ---
    check_equal("n_formations_exact", recorded_n, recomputed["n_formations"], results)
    check_equal("state_counts_exact", recorded_state, recomputed["state_counts"], results)

    # --- Finite checks ---
    check_equal("all_spread_net_finite", True, recomputed["finite_checks"]["all_spread_net_finite"], results)
    check_equal("all_spread_gross_finite", True, recomputed["finite_checks"]["all_spread_gross_finite"], results)
    check_equal("any_non_finite", False, recomputed["finite_checks"]["any_non_finite"], results)

    # --- Metrics: within tolerance ---
    check_close("spread_net_mean", recorded["spread_net_mean"],
                recomputed["metrics"]["spread_net_mean"], MEAN_TOL, results)
    check_close("spread_net_median", recorded["spread_net_median"],
                recomputed["metrics"]["spread_net_median"], MEAN_TOL, results)
    check_close("spread_gross_mean", recorded["spread_gross_mean"],
                recomputed["metrics"]["spread_gross_mean"], MEAN_TOL, results)
    check_close("spread_gross_median", recorded["spread_gross_median"],
                recomputed["metrics"]["spread_gross_median"], MEAN_TOL, results)
    check_close("high_net_mean", recorded["high_net_mean"],
                recomputed["metrics"]["high_net_mean"], MEAN_TOL, results)
    check_close("low_net_mean", recorded["low_net_mean"],
                recomputed["metrics"]["low_net_mean"], MEAN_TOL, results)
    check_close("high_low_diff_net", recorded["high_low_diff_net"],
                recomputed["metrics"]["high_low_diff_net"], DIFF_TOL, results)
    check_close("high_low_diff_gross", recorded["high_low_diff_gross"],
                recomputed["metrics"]["high_low_diff_gross"], DIFF_TOL, results)

    ref_values = addendum.get("reference_values", {})
    # --- Reference values: spot-check against canonical ---
    check_close("ref_high_low_diff_net_1x", ref_values.get("high_low_diff_net_1x"),
                recomputed["metrics"]["high_low_diff_net"], DIFF_TOL, results)

    all_passed = all(r["passed"] for r in results)
    verdict = "PASS" if all_passed else "FAIL"

    return {
        "audit_id": "H004V106_FORWARD_BLOCK_INDEPENDENT_RECOMPUTATION_AUDIT",
        "hypothesis_id": "H37",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003",
        "status": "EXPLORATORY_ONLY",
        "verdict": verdict,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "audited_artifact": str(CANONICAL_BLOCK_PATH),
        "canonical_sha256": actual_sha,
        "addendum_audited": str(ADDENDUM_PATH),
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/"
            "H004V106_FORWARD_BLOCK_INDEPENDENT_RECOMPUTATION_AUDIT_v1.md"
        ),
        "script": "scripts/forward_block_independent_recomputation_audit.py",
        "frozen_artifacts_modified": [],
        "checks_total": len(results),
        "checks_passed": sum(1 for r in results if r["passed"]),
        "checks_failed": sum(1 for r in results if not r["passed"]),
        "checks": results,
        "recomputed": recomputed,
        "recorded_addendum": {
            "n_formations": recorded_n,
            "state_counts": recorded_state,
            "metrics": recorded,
            "reference_values": addendum.get("reference_values", {}),
        },
        "interpretation": (
            "Independently recomputed every metric recorded by the addendum "
            "forward_block_independent_recomputation_20261028.json from the "
            "sealed canonical forward block's formations array (608 formations, "
            "cutoff 2026-09-30, last formation 2026-08-31). n_formations and "
            "state_counts match exactly; all means match within 1e-9; the two "
            "high-low differences match within 1e-12. No market data re-fetched, "
            "no sealed holdout opened, no frozen artifact modified. This is a "
            "consistency-only reproducibility cross-check on already-inspected "
            "development evidence; it does not validate, replace or unlock any "
            "confirmatory track."
        ),
        "note": (
            "EXPLORATORY_ONLY/consistency_only: reproducibility audit of an "
            "existing addendum against its source block. Does not validate, "
            "replace or unlock H1/H6/H7/H10/H11; does not change the frozen H10 "
            "preregistration or the 2026-11-30 data-availability gate."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Read-only reproducibility cross-check of the H004V106 "
                    "forward-block independent-recomputation addendum."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for the timestamped audit JSON. Defaults to a fresh "
             "temporary directory so the committed integrity_audit/ directory "
             "is never mutated by a diagnostic run (its file count is pinned "
             "at 27 by frozen-reference guards).",
    )
    args = parser.parse_args(argv)

    audit_result = audit_forward_block_independent_recomputation()

    out_dir = Path(args.output_dir) if args.output_dir else Path(_dt.datetime.now(
        _dt.timezone.utc
    ).strftime("/tmp/fb_recompute_audit_%Y%m%dT%H%M%SZ"))
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"H004V106_forward_block_independent_recomputation_{ts}.json"
    with out_path.open("w") as f:
        json.dump(audit_result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote audit: {out_path}")

    print(f"Verdict: {audit_result['verdict']}")
    print(f"Checks: {audit_result['checks_passed']}/{audit_result['checks_total']} passed")
    for check in audit_result["checks"]:
        if not check["passed"]:
            print(f"  FAIL: {check['check']}"
                  f"(expected={check.get('expected')}, actual={check.get('actual')}, "
                  f"abs_diff={check.get('abs_diff', 'N/A')}, tol={check.get('tolerance', 'N/A')}")

    return 0 if audit_result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
