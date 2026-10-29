#!/usr/bin/env python3
"""H004V106 forward block formation-month cluster bootstrap uncertainty audit.

Reads the canonical sealed forward block (read-only) and measures inference
under formation-month clustering: resample months with replacement, recompute
the high-minus-low net-1x spread difference, report bootstrap distribution,
percentile CI and effective independent-cluster count. Writes a new audit
artifact. No frozen artifact is modified. EXPLORATORY_ONLY.
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_PATH = ART / "integrity_audit" / "H004V106_forward_block_cluster_bootstrap_20261029.json"

N_BOOT = 2000
RNG_SEED = 20261029


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def diff_from_formations(forms):
    high = [f["spread_net_1x"] for f in forms if f["state"] == "high"]
    low = [f["spread_net_1x"] for f in forms if f["state"] == "low"]
    if not high or not low:
        return None
    return statistics.mean(high) - statistics.mean(low)


def main():
    block = json.loads(BLOCK_PATH.read_text())
    forms = block["formations"]

    # group formation indices by YYYY-MM
    months = defaultdict(list)
    for f in forms:
        months[f["formation_date"][:7]].append(f)

    month_keys = sorted(months.keys())
    month_diffs = []
    for mk in month_keys:
        d = diff_from_formations(months[mk])
        month_diffs.append(d if d is not None else 0.0)

    baseline = diff_from_formations(forms)

    rng = np.random.default_rng(RNG_SEED)
    boot = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(month_keys), size=len(month_keys))
        sampled_forms = []
        for i in idx:
            sampled_forms.extend(months[month_keys[i]])
        d = diff_from_formations(sampled_forms)
        if d is not None:
            boot.append(d)

    boot_arr = np.asarray(boot, dtype=float)
    ci_lo = float(np.percentile(boot_arr, 2.5))
    ci_hi = float(np.percentile(boot_arr, 97.5))
    se = float(np.std(boot_arr, ddof=1))

    # effective independent clusters: number of months with both states
    n_clusters_both = sum(1 for mk in month_keys if any(f["state"] == "high" for f in months[mk]) and any(f["state"] == "low" for f in months[mk]))

    result = {
        "audit_id": "H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_20261029",
        "experiment_id": block["experiment_id"],
        "audited_artifact": str(BLOCK_PATH.relative_to(ROOT)),
        "computed_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "data_cutoff_utc": block["data_cutoff_utc"],
        "date_first": block["date_first"],
        "date_last": block["date_last"],
        "n_formations": block["n_formations"],
        "n_months": len(month_keys),
        "n_clusters_with_both_states": n_clusters_both,
        "baseline_high_low_diff_net_1x": baseline,
        "n_boot": len(boot),
        "rng_seed": RNG_SEED,
        "bootstrap_mean": float(np.mean(boot_arr)),
        "bootstrap_median": float(np.median(boot_arr)),
        "bootstrap_se": se,
        "ci_95_percentile": [ci_lo, ci_hi],
        "ci_includes_zero": bool(ci_lo <= 0 <= ci_hi),
        "month_level_diffs": {mk: (diff_from_formations(months[mk])) for mk in month_keys},
        "conclusion": "Cluster bootstrap by formation month; EXPLORATORY_ONLY, does not unlock confirmatory track.",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ["n_months", "baseline_high_low_diff_net_1x", "bootstrap_mean", "bootstrap_se", "ci_95_percentile", "ci_includes_zero"]}, indent=2))


if __name__ == "__main__":
    main()
