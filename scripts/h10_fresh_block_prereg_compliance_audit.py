#!/usr/bin/env python3
"""
H10 Fresh Forward Block Preregistration Compliance Audit (DISP-003-H10-PRECOMP)

Read-only verification that the committed H10 fresh forward block artifact
correctly encodes the preregistered confirmatory decision rules from
H10_FRESH_FORWARD_BLOCK_v1.md (sections 4, 4.1, 4.2).

This is EXPLORATORY_ONLY: diagnostic on already-inspected development evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ARTIFACT_DIR = Path(
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
)
FRESH_BLOCK_PATH = ARTIFACT_DIR / "forward_block_h10_fresh/forward_block_evaluation.json"
PREREG_PATH = ARTIFACT_DIR / "preregistrations/H10_FRESH_FORWARD_BLOCK_v1.md"
CANONICAL_BLOCK_PATH = ARTIFACT_DIR / "forward_block/forward_block_evaluation.json"
GRID_LEDGER_PATH = ARTIFACT_DIR / "grid_result_ledger.json"
UNIVERSE_FRONTIER_PATH = ARTIFACT_DIR / "universe_frontier.json"

EXPECTED_CANONICAL_SHA256 = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
EXPECTED_FRESH_BLOCK_SHA256 = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
EXPECTED_GRID_LEDGER_SHA256 = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
EXPECTED_FRONTIER_SHA256 = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"


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
        "passed": passed
    })


def check_in_text(name: str, expected_substring: str, text: str, results: list[dict]) -> None:
    passed = expected_substring in text
    results.append({
        "check": name,
        "expected": expected_substring,
        "actual": "found" if passed else "not found",
        "passed": passed
    })


def audit_fresh_block_prereg_compliance() -> dict[str, Any]:
    """Main audit function."""
    results = []

    # Load artifacts
    fresh_block = load_json(FRESH_BLOCK_PATH)
    prereg_text = load_text(PREREG_PATH)

    # --- 3.1 Economic significance threshold (section 4.2) ---
    check_equal(
        "economic_significance_threshold",
        0.05,
        fresh_block.get("economic_significance_threshold"),
        results
    )
    check_equal(
        "economic_significance_met",
        False,
        fresh_block.get("economic_significance_met"),
        results
    )
    check_equal(
        "high_low_diff_net_1x_abs",
        None,
        fresh_block.get("high_low_diff_net_1x_abs"),
        results
    )
    # Verify net = gross - 0.001 for the single formation
    formation = fresh_block["formations"][0]
    expected_net = formation["spread_gross"] - 0.001
    check_equal(
        "formation_spread_net_1x_cost_consistent",
        round(expected_net, 12),
        round(formation["spread_net_1x"], 12),
        results
    )

    # --- 3.2 State count floor (section 4.2) ---
    check_equal(
        "min_state_formations",
        5,
        fresh_block.get("min_state_formations"),
        results
    )
    check_equal(
        "state_count_floor_met",
        False,
        fresh_block.get("state_count_floor_met"),
        results
    )
    # Verify n_high and n_low are both 0
    check_equal(
        "n_high_is_zero",
        0,
        fresh_block.get("n_high"),
        results
    )
    check_equal(
        "n_low_is_zero",
        0,
        fresh_block.get("n_low"),
        results
    )

    # --- 3.3 Confirmatory claim logic (section 4) ---
    check_equal(
        "confirmatory_claim_allowed",
        False,
        fresh_block.get("confirmatory_claim_allowed"),
        results
    )
    check_equal(
        "confirmatory_holm_significant",
        None,
        fresh_block.get("confirmatory_holm_significant"),
        results
    )
    confirmatory_note = fresh_block.get("confirmatory_note", "")
    check_in_text(
        "confirmatory_note_contains_economic_gate",
        "|high_low_diff_net_1x|",
        confirmatory_note,
        results
    )
    check_in_text(
        "confirmatory_note_contains_state_floor",
        "n_high=0>= 5 and n_low=0>=5 -> False",
        confirmatory_note,
        results
    )
    check_in_text(
        "confirmatory_note_contains_holm_at_alpha_k",
        "Holm-significance across the complete 216-cell family at alpha_k = 0.025",
        confirmatory_note,
        results
    )
    check_in_text(
        "confirmatory_note_contains_never_promoted",
        "never promoted from raw p-values or return alone",
        confirmatory_note,
        results
    )

    # --- 3.4 Sequential alpha-spending rule (section 4.1) ---
    check_equal(
        "sequential_alpha_rule",
        "alpha_k = 0.05 / (k * (k + 1))",
        fresh_block.get("sequential_alpha_rule"),
        results
    )
    check_equal(
        "sequential_family_alpha",
        0.05,
        fresh_block.get("sequential_family_alpha"),
        results
    )
    check_equal(
        "sequential_look_number",
        1,
        fresh_block.get("sequential_look_number"),
        results
    )
    check_equal(
        "sequential_alpha_k",
        0.025,
        fresh_block.get("sequential_alpha_k"),
        results
    )
    check_equal(
        "sequential_cumulative_spend",
        0.025,
        fresh_block.get("sequential_cumulative_spend"),
        results
    )
    check_equal(
        "sequential_remaining_budget",
        0.025,
        fresh_block.get("sequential_remaining_budget"),
        results
    )
    check_equal(
        "sequential_look_consumes_budget",
        False,
        fresh_block.get("sequential_look_consumes_budget"),
        results
    )
    check_equal(
        "sequential_look_mature",
        False,
        fresh_block.get("sequential_look_mature"),
        results
    )
    seq_note = fresh_block.get("sequential_look_note", "")
    check_in_text(
        "sequential_look_note_explains_k1_alpha",
        "k=1 at alpha_k=0.025",
        seq_note,
        results
    )
    check_in_text(
        "sequential_look_note_explains_immature_no_budget",
        "consumes no budget",
        seq_note,
        results
    )
    check_in_text(
        "sequential_look_note_explains_do_not_advance_k",
        "do NOT advance k",
        seq_note,
        results
    )

    # --- 3.5 Block maturity and sealing ---
    check_equal(
        "block_sealed",
        True,
        fresh_block.get("block_sealed"),
        results
    )
    sealing_rule = fresh_block.get("block_sealing_rule", "")
    check_in_text(
        "block_sealing_rule_mentions_30_day_maturity",
        "30-day forward horizon is not completed",
        sealing_rule,
        results
    )
    check_in_text(
        "block_sealing_rule_mentions_no_truncated",
        "no truncated outcomes",
        sealing_rule,
        results
    )
    check_equal(
        "n_formations",
        1,
        fresh_block.get("n_formations"),
        results
    )
    check_equal(
        "n_mid",
        1,
        fresh_block.get("n_mid"),
        results
    )
    check_equal(
        "high_low_diff_net_1x_is_null",
        None,
        fresh_block.get("high_low_diff_net_1x"),
        results
    )
    overlap = fresh_block.get("overlap_aware_uncertainty", {})
    check_equal(
        "overlap_aware_status_immature",
        "IMMATURE",
        overlap.get("status"),
        results
    )
    check_equal(
        "overlap_aware_reason_correct",
        "need n_high>0 and n_low>0 for overlap-aware interval",
        overlap.get("reason"),
        results
    )
    check_equal(
        "overlap_aware_n_boot_zero",
        0,
        overlap.get("n_boot"),
        results
    )
    check_equal(
        "overlap_aware_n_clusters_zero",
        0,
        overlap.get("n_clusters_with_both_states"),
        results
    )
    check_equal(
        "overlap_aware_n_months_zero",
        0,
        overlap.get("n_months"),
        results
    )

    # --- 3.6 Frozen hash verification ---
    check_equal(
        "canonical_block_sha256",
        EXPECTED_CANONICAL_SHA256,
        sha256_file(CANONICAL_BLOCK_PATH),
        results
    )
    check_equal(
        "fresh_block_sha256",
        EXPECTED_FRESH_BLOCK_SHA256,
        sha256_file(FRESH_BLOCK_PATH),
        results
    )
    check_equal(
        "grid_ledger_sha256",
        EXPECTED_GRID_LEDGER_SHA256,
        sha256_file(GRID_LEDGER_PATH),
        results
    )
    check_equal(
        "universe_frontier_sha256",
        EXPECTED_FRONTIER_SHA256,
        sha256_file(UNIVERSE_FRONTIER_PATH),
        results
    )

    # --- Overall verdict ---
    all_passed = all(r["passed"] for r in results)
    verdict = "PASS" if all_passed else "FAIL"

    return {
        "audit_id": "H004V106_H10_FRESH_FORWARD_BLOCK_PREREG_COMPLIANCE_AUDIT",
        "hypothesis_id": "H34",
        "status": "EXPLORATORY_ONLY",
        "verdict": verdict,
        "timestamp_utc": "2026-11-15T10:47:00Z",
        "artifact_sha256": sha256_file(FRESH_BLOCK_PATH),
        "preregistration_sha256": hashlib.sha256(prereg_text.encode()).hexdigest(),
        "checks_total": len(results),
        "checks_passed": sum(1 for r in results if r["passed"]),
        "checks_failed": sum(1 for r in results if not r["passed"]),
        "checks": results,
        "frozen_artifacts_modified": [],
        "note": "EXPLORATORY_ONLY: compliance diagnostic on already-inspected development evidence. Does not validate, replace or unlock any confirmatory track."
    }


def main() -> int:
    audit_result = audit_fresh_block_prereg_compliance()

    # Write artifact
    out_dir = ARTIFACT_DIR / "integrity_audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"H004V106_H10_fresh_forward_block_prereg_compliance_audit_2026-11-15T10-47-00Z.json"
    with out_path.open("w") as f:
        json.dump(audit_result, f, indent=2)

    # Print summary
    print(f"Verdict: {audit_result['verdict']}")
    print(f"Checks: {audit_result['checks_passed']}/{audit_result['checks_total']} passed")
    for check in audit_result["checks"]:
        if not check["passed"]:
            print(f"  FAIL: {check['check']} (expected={check['expected']}, actual={check['actual']})")

    return 0 if audit_result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())