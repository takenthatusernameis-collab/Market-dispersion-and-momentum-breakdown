#!/usr/bin/env python3
"""H004V106 state representativeness audit (DISP-003-STATEAUDIT-001).

Reads the canonical sealed forward block (read-only) and measures how
sensitive the high-minus-low estimate is to the removal of individual
calendar months, and what share of the high-state mean is contributed by
the largest single-month cluster. Writes a new audit artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/.
No frozen artifact is modified.

Decision rule (predeclared in the preregistration):
- Removing any single calendar month moves high_low_diff_net_1x by more
  than 50% of its full-block magnitude  -> CLUSTER_DOMINATED
- Largest single-month cluster contributes >50% of high-state mean ->
  CLUSTER_DOMINATED
- otherwise MONTH_ROBUST
Result is EXPLORATORY_ONLY in every branch.
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_PATH = ART / "integrity_audit" / "H004V106_state_representativeness_audit_20261025.json"

THRESHOLD_FRAC = 0.50


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    block = json.loads(BLOCK_PATH.read_text(encoding="utf-8"))
    formations = block["formations"]
    baseline = block["high_low_diff_net_1x"]

    months = sorted({r["formation_date"][:7] for r in formations})
    month_drop = {}
    for m in months:
        keep = [r for r in formations if not r["formation_date"].startswith(m)]
        hi = [r["spread_net_1x"] for r in keep if r["state"] == "high"]
        lo = [r["spread_net_1x"] for r in keep if r["state"] == "low"]
        nh = len(hi)
        nl = len(lo)
        diff = (statistics.mean(hi) - statistics.mean(lo)) if hi and lo else None
        month_drop[m] = {
            "formations_kept": len(keep),
            "n_high": nh,
            "n_low": nl,
            "high_low_diff_net_1x": diff,
            "delta_vs_baseline": (diff - baseline) if diff is not None else None,
            "delta_frac_vs_baseline": ((diff - baseline) / baseline) if (diff is not None and baseline) else None,
        }

    hi_all = [r["spread_net_1x"] for r in formations if r["state"] == "high"]
    hi_mean = statistics.mean(hi_all) if hi_all else None

    hi_by_month: dict[str, list[float]] = {}
    for r in formations:
        if r["state"] == "high":
            hi_by_month.setdefault(r["formation_date"][:7], []).append(r["spread_net_1x"])
    if hi_by_month:
        largest_month, largest_vals = max(hi_by_month.items(), key=lambda kv: len(kv[1]))
        largest_mean = statistics.mean(largest_vals)
        largest_median = statistics.median(largest_vals)
        largest_share = (largest_mean / hi_mean) if (hi_mean and hi_mean != 0) else None
    else:
        largest_month, largest_vals, largest_mean, largest_median, largest_share = None, [], None, None, None

    high_per_month = {m: len(v) for m, v in sorted(hi_by_month.items())}
    last_high = max((r["formation_date"] for r in formations if r["state"] == "high"), default=None)

    dominated_by_drop = any(
        v["delta_frac_vs_baseline"] is not None and abs(v["delta_frac_vs_baseline"]) > THRESHOLD_FRAC
        for v in month_drop.values()
    )
    dominated_by_cluster = (
        largest_share is not None and largest_share > THRESHOLD_FRAC
    )
    label = "CLUSTER_DOMINATED" if (dominated_by_drop or dominated_by_cluster) else "MONTH_ROBUST"

    out = {
        "audit_id": "H004V106_STATE_REPRESENTATIVENESS_AUDIT_20261025",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-STATEAUDIT-001",
        "status": "EXPLORATORY_ONLY",
        "label": label,
        "preregistration": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/H004V106_STATE_REPRESENTATIVENESS_AUDIT_v1.md",
        "audited_artifact": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
        "computed_utc": now_utc(),
        "baseline": {
            "n_formations": block["n_formations"],
            "n_high": block["n_high"],
            "n_low": block["n_low"],
            "n_mid": block["n_mid"],
            "high_low_diff_net_1x": baseline,
            "high_net_1x_mean": block["high_net_1x_mean"],
            "low_net_1x_mean": block["low_net_1x_mean"],
            "data_cutoff_utc": block["data_cutoff_utc"],
            "date_first": block["date_first"],
            "date_last": block["date_last"],
        },
        "calendar_month_leave_one_out": {
            "threshold_frac": THRESHOLD_FRAC,
            "dominated_by_drop": dominated_by_drop,
            "months": month_drop,
        },
        "largest_high_state_month_cluster": {
            "month": largest_month,
            "n": len(largest_vals),
            "mean": largest_mean,
            "median": largest_median,
            "share_of_high_state_mean": largest_share,
            "threshold_frac": THRESHOLD_FRAC,
            "dominated_by_cluster": dominated_by_cluster,
        },
        "high_state_calendar_counts": high_per_month,
        "last_high_state_formation_date": last_high,
        "conclusion": (
            f"The canonical H004V106 high-minus-low estimate ({baseline}) is labeled {label}. "
            "This is a measurement-feasibility diagnostic on already-inspected development "
            "evidence. It is NOT a fresh holdout, NOT independent confirmation, and does NOT "
            "unlock the frozen confirmatory track. Promotion requires a genuinely fresh "
            "sealed forward block with formations after 2026-09-29."
        ),
    }
    OUT_PATH.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[state-audit] label={label} baseline={baseline} out={OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())