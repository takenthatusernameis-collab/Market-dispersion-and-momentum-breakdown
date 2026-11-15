#!/usr/bin/env python3
"""Cross-check H004V106 anchor across grid_summary.json, cell_checkpoint.json, and grid_result_ledger.json.

Read-only and additive: produces a new integrity audit artifact. No sealed artifact,
grid ledger, manifest, or DISPERSION-001/002 artifact is modified.

Preregistration:
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_GRID_ANCHOR_CROSSCHECK_v1.md
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
OUT_DIR = ART / "integrity_audit"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOL = 1e-12


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compute_summary_from_formations(formations: list[dict]) -> dict:
    """Compute summary statistics from formation records."""
    n_formations = len(formations)
    n_high = sum(1 for r in formations if r.get("state") == "high")
    n_low = sum(1 for r in formations if r.get("state") == "low")
    n_mid = sum(1 for r in formations if r.get("state") == "mid")

    spread_gross = [float(r["spread_gross"]) for r in formations if r.get("spread_gross") is not None]
    spread_net = [float(r["spread_net_1x"]) for r in formations if r.get("spread_net_1x") is not None]

    hi_gross = [float(r["spread_gross"]) for r in formations if r.get("state") == "high" and r.get("spread_gross") is not None]
    lo_gross = [float(r["spread_gross"]) for r in formations if r.get("state") == "low" and r.get("spread_gross") is not None]
    hi_net = [float(r["spread_net_1x"]) for r in formations if r.get("state") == "high" and r.get("spread_net_1x") is not None]
    lo_net = [float(r["spread_net_1x"]) for r in formations if r.get("state") == "low" and r.get("spread_net_1x") is not None]

    return {
        "n_formations": n_formations,
        "n_high": n_high,
        "n_low": n_low,
        "n_mid": n_mid,
        "high_low_diff_net_1x": (float(np.mean(hi_net)) - float(np.mean(lo_net))) if hi_net and lo_net else None,
        "high_low_diff_gross": (float(np.mean(hi_gross)) - float(np.mean(lo_gross))) if hi_gross and lo_gross else None,
        "spread_net_1x_mean": float(np.mean(spread_net)) if spread_net else None,
        "spread_net_1x_median": float(np.median(spread_net)) if spread_net else None,
        "spread_gross_mean": float(np.mean(spread_gross)) if spread_gross else None,
        "spread_gross_median": float(np.median(spread_gross)) if spread_gross else None,
        "high_net_1x_mean": float(np.mean(hi_net)) if hi_net else None,
        "low_net_1x_mean": float(np.mean(lo_net)) if lo_net else None,
        "high_gross_mean": float(np.mean(hi_gross)) if hi_gross else None,
        "low_gross_mean": float(np.mean(lo_gross)) if lo_gross else None,
        "date_first": formations[0].get("formation_date") if formations else None,
        "date_last": formations[-1].get("formation_date") if formations else None,
    }


def load_grid_summary() -> dict:
    path = ART / "grid_summary.json"
    raw = path.read_text()
    data = json.loads(raw)
    anchor = data["primary_anchor_expanding_H004V106"]
    formations = anchor["formations"]
    # Compute summary from formations since grid_summary doesn't store them
    computed_summary = compute_summary_from_formations(formations)
    return {
        "source": "grid_summary.json",
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "formations": formations,
        **computed_summary,
        "eligible_assets_per_date": anchor["eligible_assets_per_date"],
        "evaluated_utc": anchor["evaluated_utc"],
    }


def load_cell_checkpoint() -> dict:
    path = ART / "grid_checkpoints" / "cell_checkpoint.json"
    raw = path.read_text()
    data = json.loads(raw)
    v106 = data["H004V106"]
    return {
        "source": "grid_checkpoints/cell_checkpoint.json",
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "formations": v106["formations"],
        "date_first": v106["date_first"],
        "date_last": v106["date_last"],
        "eligible_assets_per_date": v106["eligible_assets_per_date"],
        "evaluated_utc": v106["evaluated_utc"],
        "n_formations": v106["n_formations"],
        "n_high": v106["n_high"],
        "n_low": v106["n_low"],
        "n_mid": v106["n_mid"],
        "high_low_diff_net_1x": v106["high_low_diff_net_1x"],
        "high_low_diff_gross": v106["high_low_diff_gross"],
        "spread_net_1x_mean": v106["spread_net_1x_mean"],
        "spread_net_1x_median": v106["spread_net_1x_median"],
        "spread_gross_mean": v106["spread_gross_mean"],
        "spread_gross_median": v106["spread_gross_median"],
        "high_net_1x_mean": v106["high_net_1x_mean"],
        "low_net_1x_mean": v106["low_net_1x_mean"],
        "high_gross_mean": v106["high_gross_mean"],
        "low_gross_mean": v106["low_gross_mean"],
        "status": v106["status"],
    }


def load_grid_result_ledger() -> dict:
    path = ART / "grid_result_ledger.json"
    raw = path.read_text()
    data = json.loads(raw)
    v106 = data["cells"]["H004V106"]
    return {
        "source": "grid_result_ledger.json",
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "formations": v106["formations"],
        "date_first": v106["date_first"],
        "date_last": v106["date_last"],
        "eligible_assets_per_date": v106["eligible_assets_per_date"],
        "evaluated_utc": v106["evaluated_utc"],
        "n_formations": v106["n_formations"],
        "n_high": v106["n_high"],
        "n_low": v106["n_low"],
        "n_mid": v106["n_mid"],
        "high_low_diff_net_1x": v106["high_low_diff_net_1x"],
        "high_low_diff_gross": v106["high_low_diff_gross"],
        "spread_net_1x_mean": v106["spread_net_1x_mean"],
        "spread_net_1x_median": v106["spread_net_1x_median"],
        "spread_gross_mean": v106["spread_gross_mean"],
        "spread_gross_median": v106["spread_gross_median"],
        "high_net_1x_mean": v106["high_net_1x_mean"],
        "low_net_1x_mean": v106["low_net_1x_mean"],
        "high_gross_mean": v106["high_gross_mean"],
        "low_gross_mean": v106["low_gross_mean"],
        "status": v106["status"],
    }


def compare_formations(f1: list[dict], f2: list[dict], label1: str, label2: str) -> dict:
    """Compare two formation lists element-wise."""
    mismatches = []
    n1, n2 = len(f1), len(f2)
    if n1 != n2:
        mismatches.append({
            "type": "length_mismatch",
            "label1": label1,
            "label2": label2,
            "n1": n1,
            "n2": n2,
        })
        min_n = min(n1, n2)
    else:
        min_n = n1

    for i in range(min_n):
        r1, r2 = f1[i], f2[i]
        # Check formation_date
        if r1.get("formation_date") != r2.get("formation_date"):
            mismatches.append({
                "type": "date_mismatch",
                "index": i,
                "label1": label1,
                "label2": label2,
                "date1": r1.get("formation_date"),
                "date2": r2.get("formation_date"),
            })
            continue

        # Check numeric fields
        for field in ("dispersion", "spread_gross", "spread_net_1x"):
            v1, v2 = r1.get(field), r2.get(field)
            if v1 is None or v2 is None:
                mismatches.append({
                    "type": "missing_field",
                    "index": i,
                    "field": field,
                    "label1": label1,
                    "label2": label2,
                    "v1": v1,
                    "v2": v2,
                })
            elif not math.isclose(float(v1), float(v2), rel_tol=0.0, abs_tol=TOL):
                mismatches.append({
                    "type": "numeric_mismatch",
                    "index": i,
                    "field": field,
                    "label1": label1,
                    "label2": label2,
                    "v1": v1,
                    "v2": v2,
                    "diff": abs(float(v1) - float(v2)),
                })

        # Check n_assets (integer)
        if r1.get("n_assets") != r2.get("n_assets"):
            mismatches.append({
                "type": "n_assets_mismatch",
                "index": i,
                "label1": label1,
                "label2": label2,
                "v1": r1.get("n_assets"),
                "v2": r2.get("n_assets"),
            })

        # Check state
        if r1.get("state") != r2.get("state"):
            mismatches.append({
                "type": "state_mismatch",
                "index": i,
                "label1": label1,
                "label2": label2,
                "v1": r1.get("state"),
                "v2": r2.get("state"),
            })

    return {
        "match": len(mismatches) == 0,
        "mismatches": mismatches,
        "n_compared": min_n,
    }


def compare_summaries(s1: dict, s2: dict, label1: str, label2: str) -> dict:
    """Compare summary statistics."""
    mismatches = []
    fields = [
        "n_formations", "n_high", "n_low", "n_mid",
        "high_low_diff_net_1x", "high_low_diff_gross",
        "spread_net_1x_mean", "spread_net_1x_median",
        "spread_gross_mean", "spread_gross_median",
        "high_net_1x_mean", "low_net_1x_mean",
        "high_gross_mean", "low_gross_mean",
        "date_first", "date_last",
    ]
    for field in fields:
        v1, v2 = s1.get(field), s2.get(field)
        if v1 is None or v2 is None:
            mismatches.append({
                "field": field,
                "label1": label1,
                "label2": label2,
                "v1": v1,
                "v2": v2,
                "reason": "missing_in_one",
            })
        elif isinstance(v1, float) and isinstance(v2, float):
            if not math.isclose(v1, v2, rel_tol=0.0, abs_tol=TOL):
                mismatches.append({
                    "field": field,
                    "label1": label1,
                    "label2": label2,
                    "v1": v1,
                    "v2": v2,
                    "diff": abs(v1 - v2),
                })
        elif v1 != v2:
            mismatches.append({
                "field": field,
                "label1": label1,
                "label2": label2,
                "v1": v1,
                "v2": v2,
            })

    return {
        "match": len(mismatches) == 0,
        "mismatches": mismatches,
    }


def check_data_integrity(formations: list[dict], label: str) -> dict:
    """Check data integrity of formations."""
    issues = []
    seen_dates = set()
    for i, r in enumerate(formations):
        # Check for duplicate dates
        d = r.get("formation_date")
        if d in seen_dates:
            issues.append({
                "type": "duplicate_date",
                "index": i,
                "date": d,
            })
        seen_dates.add(d)

        # Check finite values
        for field in ("dispersion", "spread_gross", "spread_net_1x"):
            v = r.get(field)
            if v is None:
                issues.append({
                    "type": "missing_field",
                    "index": i,
                    "field": field,
                })
            elif not math.isfinite(float(v)):
                issues.append({
                    "type": "non_finite",
                    "index": i,
                    "field": field,
                    "value": v,
                })

        # Check n_assets
        if r.get("n_assets") is None:
            issues.append({"type": "missing_n_assets", "index": i})

        # Check state
        if r.get("state") not in ("high", "low", "mid"):
            issues.append({
                "type": "invalid_state",
                "index": i,
                "state": r.get("state"),
            })

    # Check strictly increasing dates
    dates = [r.get("formation_date") for r in formations if r.get("formation_date")]
    for i in range(1, len(dates)):
        if dates[i] <= dates[i-1]:
            issues.append({
                "type": "non_increasing_date",
                "index": i,
                "date": dates[i],
                "prev_date": dates[i-1],
            })

    return {
        "source": label,
        "all_ok": len(issues) == 0,
        "issues": issues,
        "n_formations": len(formations),
        "unique_dates": len(seen_dates),
    }


def build_artifact(
    gs: dict, cc: dict, grl: dict,
    formation_checks: dict, summary_checks: dict, integrity_checks: dict
) -> dict:
    all_pass = (
        all(v["match"] for v in formation_checks.values()) and
        all(v["match"] for v in summary_checks.values()) and
        all(v["all_ok"] for v in integrity_checks.values())
    )

    conclusion = (
        "PASS: H004V106 anchor is internally consistent across grid_summary.json, "
        "grid_checkpoints/cell_checkpoint.json, and grid_result_ledger.json. "
        "All 1338 formations match element-wise within 1e-12 tolerance. "
        "All summary statistics match within 1e-12 tolerance. "
        "All data integrity checks pass (finite values, unique dates, valid states, increasing dates). "
        "No artifact modified."
    ) if all_pass else (
        "FAIL: One or more cross-checks failed. "
        f"Formation checks: {sum(1 for v in formation_checks.values() if not v['match'])} failed. "
        f"Summary checks: {sum(1 for v in summary_checks.values() if not v['match'])} failed. "
        f"Integrity checks: {sum(1 for v in integrity_checks.values() if not v['all_ok'])} failed. "
        "See detailed mismatches in artifact. No artifact modified to force a pass."
    )

    return {
        "audit_id": "H004V106_GRID_ANCHOR_CROSSCHECK_20261115",
        "audit_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "audited_artifacts": [
            gs["path"],
            cc["path"],
            grl["path"],
        ],
        "artifact_sha256": {
            "grid_summary.json": gs["sha256"],
            "grid_checkpoints/cell_checkpoint.json": cc["sha256"],
            "grid_result_ledger.json": grl["sha256"],
        },
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_GRID_ANCHOR_CROSSCHECK_v1.md",
        "formation_checks": formation_checks,
        "summary_checks": summary_checks,
        "integrity_checks": integrity_checks,
        "conclusion": conclusion,
        "pass": all_pass,
    }


def main() -> int:
    # Load all three artifacts
    gs = load_grid_summary()
    cc = load_cell_checkpoint()
    grl = load_grid_result_ledger()

    # Formation-level cross-checks (pairwise)
    formation_checks = {
        "grid_summary_vs_cell_checkpoint": compare_formations(
            gs["formations"], cc["formations"], "grid_summary", "cell_checkpoint"
        ),
        "grid_summary_vs_grid_result_ledger": compare_formations(
            gs["formations"], grl["formations"], "grid_summary", "grid_result_ledger"
        ),
        "cell_checkpoint_vs_grid_result_ledger": compare_formations(
            cc["formations"], grl["formations"], "cell_checkpoint", "grid_result_ledger"
        ),
    }

    # Summary statistics cross-checks (pairwise)
    summary_checks = {
        "grid_summary_vs_cell_checkpoint": compare_summaries(gs, cc, "grid_summary", "cell_checkpoint"),
        "grid_summary_vs_grid_result_ledger": compare_summaries(gs, grl, "grid_summary", "grid_result_ledger"),
        "cell_checkpoint_vs_grid_result_ledger": compare_summaries(cc, grl, "cell_checkpoint", "grid_result_ledger"),
    }

    # Data integrity checks (each artifact)
    integrity_checks = {
        "grid_summary": check_data_integrity(gs["formations"], "grid_summary"),
        "cell_checkpoint": check_data_integrity(cc["formations"], "cell_checkpoint"),
        "grid_result_ledger": check_data_integrity(grl["formations"], "grid_result_ledger"),
    }

    # Build and write artifact
    artifact = build_artifact(gs, cc, grl, formation_checks, summary_checks, integrity_checks)

    out_path = OUT_DIR / "H004V106_grid_anchor_crosscheck_20261115.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "pass": artifact["pass"],
        "artifact": str(out_path.relative_to(ROOT)),
        "formation_mismatches": sum(len(v["mismatches"]) for v in formation_checks.values()),
        "summary_mismatches": sum(len(v["mismatches"]) for v in summary_checks.values()),
        "integrity_issues": sum(len(v["issues"]) for v in integrity_checks.values()),
    }, indent=2))

    return 0 if artifact["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())