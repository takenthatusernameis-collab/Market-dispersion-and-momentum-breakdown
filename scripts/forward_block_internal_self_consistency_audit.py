#!/usr/bin/env python3
"""
H004V106 Forward Block Internal Self-Consistency Audit (DISP-003-SELFCHECK-001)

Read-only, stdlib-only, no network: verifies that the sealed canonical forward
block's own header/summary scalar fields agree with its own `formations` array.
No outcomes beyond this consistency check are produced; no market data is
re-fetched; no sealed holdout is opened; nothing is written to any frozen
artifact.

This module is import-safe and hermetic so it can be unit-tested with synthetic
blocks.

Predeclared identities (exact for integers/dates/states, 1e-9 for the mean):
  1. eligible_assets_per_date.min == min(n_assets)
  2. eligible_assets_per_date.max == max(n_assets)
  3. eligible_assets_per_date.mean == mean(n_assets)  [tol 1e-9]
  4. n_formations == len(formations)
  5. header scalars n_high/n_low/n_mid == per-state counts of formations[].state
     (and, if a state_counts dict is present in a future schema, it too matches)
  6. date_first == min(formation_date) and date_last == max(formation_date)
  7. formation_date strictly increasing and unique
  8. every state in {high,mid,low} and every n_assets >= MIN_ASSETS_DECILES
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
OUT_DIR = ARTIFACT_DIR / "integrity_audit"

CANONICAL_SHA256 = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
MIN_ASSETS_DECILES = 20
MEAN_TOL = 1e-9
VALID_STATES = ("high", "mid", "low")


def now_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r") as f:
        return json.load(f)


def _record(results: list[dict], name: str, passed: bool, expected: Any, actual: Any,
            note: str = "", **extra: Any) -> None:
    row = {"check": name, "expected": expected, "actual": actual,
           "passed": bool(passed)}
    if note:
        row["note"] = note
    row.update(extra)
    results.append(row)


def check_eligible_min(records: list[dict], summary: dict, results: list[dict]) -> None:
    n_assets = [r["n_assets"] for r in records]
    actual = min(n_assets) if n_assets else None
    expected = summary.get("min")
    _record(results, "eligible_min_equals_array_min", expected == actual,
            expected, actual)


def check_eligible_max(records: list[dict], summary: dict, results: list[dict]) -> None:
    n_assets = [r["n_assets"] for r in records]
    actual = max(n_assets) if n_assets else None
    expected = summary.get("max")
    _record(results, "eligible_max_equals_array_max", expected == actual,
            expected, actual)


def check_eligible_mean(records: list[dict], summary: dict, results: list[dict]) -> None:
    n_assets = [r["n_assets"] for r in records]
    actual = statistics.fmean(n_assets) if n_assets else None
    expected = summary.get("mean")
    if expected is None or actual is None:
        ok = expected == actual
        diff = None
    else:
        diff = abs(float(expected) - float(actual))
        ok = diff <= MEAN_TOL
    _record(results, "eligible_mean_equals_array_mean", ok, expected, actual,
            abs_diff=diff, tolerance=MEAN_TOL)


def check_n_formations(block: dict, records: list[dict], results: list[dict]) -> None:
    expected = block.get("n_formations")
    actual = len(records)
    _record(results, "n_formations_equals_array_len", expected == actual,
            expected, actual)


def check_header_state_counts(block: dict, records: list[dict],
                              results: list[dict]) -> None:
    """Verify the block's top-level n_high/n_low/n_mid header scalars equal the
    per-state counts derived from formations[].state.

    The canonical block has no `state_counts` dict; it carries the counts as
    the scalars n_high/n_low/n_mid. A present-but-inconsistent state_counts dict
    (in a hypothetical future schema) is also cross-checked against the array.
    """
    counts = {s: 0 for s in VALID_STATES}
    for r in records:
        counts[r.get("state")] = counts.get(r.get("state"), 0) + 1
    pairs = (("n_high", "high"), ("n_low", "low"), ("n_mid", "mid"))
    for header_key, state_key in pairs:
        _record(results, f"{header_key}_equals_array_state_count",
                block.get(header_key) == counts[state_key],
                counts[state_key], block.get(header_key))
    declared = block.get("state_counts")
    if isinstance(declared, dict):
        for s in VALID_STATES:
            _record(results, f"state_counts_{s}", declared.get(s) == counts[s],
                    declared.get(s), counts[s])


def check_date_first_last(block: dict, records: list[dict], results: list[dict]) -> None:
    dates = [r["formation_date"] for r in records]
    if dates:
        _record(results, "date_first_equals_array_min",
                block.get("date_first") == min(dates), min(dates),
                block.get("date_first"))
        _record(results, "date_last_equals_array_max",
                block.get("date_last") == max(dates), max(dates),
                block.get("date_last"))
    else:
        _record(results, "date_first_equals_array_min", block.get("date_first") is None,
                None, block.get("date_first"))
        _record(results, "date_last_equals_array_max", block.get("date_last") is None,
                None, block.get("date_last"))


def check_dates_strictly_increasing(records: list[dict], results: list[dict]) -> None:
    dates = [r["formation_date"] for r in records]
    if not dates:
        _record(results, "dates_strictly_increasing_and_unique", True, True, True,
                note="empty formations array")
        return
    strictly_increasing = all(dates[i] < dates[i + 1] for i in range(len(dates) - 1))
    unique = len(set(dates)) == len(dates)
    _record(results, "dates_strictly_increasing_and_unique",
            strictly_increasing and unique, True,
            {"strictly_increasing": strictly_increasing, "unique": unique})


def check_state_domain(records: list[dict], results: list[dict]) -> None:
    offending = sorted({r.get("state") for r in records
                        if r.get("state") not in VALID_STATES})
    _record(results, "all_states_in_domain", len(offending) == 0,
            list(VALID_STATES), offending)


def check_min_assets_floor(records: list[dict], results: list[dict]) -> None:
    offending = [r["formation_date"] for r in records
                 if r.get("n_assets") is None or r["n_assets"] < MIN_ASSETS_DECILES]
    _record(results, "all_n_assets_meet_floor", len(offending) == 0,
            f">= {MIN_ASSETS_DECILES}", offending[:20],
            offending_count=len(offending))


def run_checks(block: dict) -> dict[str, Any]:
    """Run every internal self-consistency check against a loaded block."""
    records = block.get("formations", []) or []
    summary = block.get("eligible_assets_per_date", {}) or {}
    results: list[dict] = []
    check_eligible_min(records, summary, results)
    check_eligible_max(records, summary, results)
    check_eligible_mean(records, summary, results)
    check_n_formations(block, records, results)
    check_header_state_counts(block, records, results)
    check_date_first_last(block, records, results)
    check_dates_strictly_increasing(records, results)
    check_state_domain(records, results)
    check_min_assets_floor(records, results)

    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    return {
        "checks": results,
        "checks_total": len(results),
        "checks_passed": passed,
        "checks_failed": failed,
        "verdict": "PASS" if failed == 0 else "FAIL",
    }


def audit() -> dict[str, Any]:
    """Execute the full read-only audit against the on-disk canonical block."""
    actual_sha = sha256_file(CANONICAL_BLOCK_PATH)
    block = load_json(CANONICAL_BLOCK_PATH)
    run = run_checks(block)

    sha_ok = actual_sha == CANONICAL_SHA256
    header_ok = (block.get("block_sealed") is True
                 and block.get("anchor_id") == "H004V106"
                 and str(block.get("data_cutoff_utc", "")).startswith("2026-09-30")
                 and str(block.get("date_last", "")).startswith("2026-08-31"))
    overall = "PASS" if (run["verdict"] == "PASS" and sha_ok and header_ok) else "FAIL"

    return {
        "audit_id": "H004V106_FORWARD_BLOCK_SELF_CONSISTENCY_AUDIT",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003",
        "hypothesis_id": "H38",
        "status": "EXPLORATORY_ONLY",
        "scope": "consistency_only",
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/"
            "H004V106_FORWARD_BLOCK_SELF_CONSISTENCY_AUDIT_v1.md"
        ),
        "script": "scripts/forward_block_internal_self_consistency_audit.py",
        "audited_artifact": str(CANONICAL_BLOCK_PATH),
        "canonical_sha256": CANONICAL_SHA256,
        "actual_sha256": actual_sha,
        "sha256_match": sha_ok,
        "header_ok": header_ok,
        "generated_utc": now_utc(),
        "verdict": overall,
        "note": (
            "EXPLORATORY_ONLY/consistency_only: verifies the sealed canonical "
            "forward block's own header/summary fields against its own "
            "formations array. Does not validate, replace or unlock any "
            "confirmatory track; does not re-fetch market data; opens no sealed "
            "holdout; modifies no frozen artifact."
        ),
        "frozen_artifacts_modified": [],
        **run,
    }


def main() -> int:
    report = audit()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_path = OUT_DIR / f"H004V106_forward_block_self_consistency_{ts}.json"
    with out_path.open("w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"verdict={report['verdict']} checks={report['checks_passed']}/"
          f"{report['checks_total']} sha_match={report['sha256_match']}")
    print(f"wrote {out_path}")
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())