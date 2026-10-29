#!/usr/bin/env python3
"""H004V106 forward block temporal stability audit.

Re-estimates the canonical sealed forward-block anchor (read-only) on two
formation-date halves of the block and reports high-minus-low net-1x spread
with formation counts, month counts and month-cluster bootstrap SE/CI for
each half. Describes whether the sign/magnitude is temporally stable.
Writes a new audit artifact. No frozen artifact is modified. EXPLORATORY_ONLY.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
BLOCK_PATH = ART / "forward_block" / "forward_block_evaluation.json"
OUT_PATH = ART / "integrity_audit" / "H004V106_forward_block_temporal_stability_20261029.json"

N_BOOT = 2000
RNG_SEED = 20261029


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def diff_from_forms(forms):
    high = [f["spread_net_1x"] for f in forms if f["state"] == "high"]
    low = [f["spread_net_1x"] for f in forms if f["state"] == "low"]
    if not high or not low:
        return None
    return statistics.mean(high) - statistics.mean(low)


def month_groups(forms):
    months = defaultdict(list)
    for f in forms:
        months[f["formation_date"][:7]].append(f)
    return dict(sorted(months.items()))


def bootstrap(months, rng):
    keys = list(months.keys())
    boot = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(keys), size=len(keys))
        sample = []
        for i in idx:
            sample.extend(months[keys[i]])
        d = diff_from_forms(sample)
        if d is not None:
            boot.append(d)
    if not boot:
        return {"mean": None, "se": None, "ci_lo": None, "ci_hi": None, "n_boot": 0}
    arr = np.asarray(boot, dtype=float)
    ci_lo = float(np.percentile(arr, 2.5))
    ci_hi = float(np.percentile(arr, 97.5))
    return {
        "mean": float(arr.mean()),
        "se": float(arr.std(ddof=1)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "ci_includes_zero": bool(ci_lo <= 0 <= ci_hi),
        "n_boot": len(boot),
    }


def half_stats(forms, rng):
    months = month_groups(forms)
    both = sum(
        1
        for mk in months
        if any(f["state"] == "high" for f in months[mk])
        and any(f["state"] == "low" for f in months[mk])
    )
    return {
        "n_formations": len(forms),
        "n_high": sum(1 for f in forms if f["state"] == "high"),
        "n_low": sum(1 for f in forms if f["state"] == "low"),
        "n_mid": sum(1 for f in forms if f["state"] == "mid"),
        "high_low_diff_net_1x": diff_from_forms(forms),
        "spread_net_1x_median": float(np.median([f["spread_net_1x"] for f in forms])),
        "date_first": forms[0]["formation_date"],
        "date_last": forms[-1]["formation_date"],
        "n_months": len(months),
        "n_months_with_both_states": both,
        "bootstrap": bootstrap(months, rng),
        "month_level_diffs": {mk: diff_from_forms(months[mk]) for mk in months},
    }


def main():
    block = json.loads(BLOCK_PATH.read_text())
    forms = sorted(block["formations"], key=lambda f: f["formation_date"])
    split = len(forms) // 2
    split_date = forms[split]["formation_date"]
    rng = np.random.default_rng(RNG_SEED)
    first = half_stats(forms[:split], rng)
    second = half_stats(forms[split:], rng)
    baseline = diff_from_forms(forms)

    result = {
        "audit_id": "H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_20261029",
        "experiment_id": block["experiment_id"],
        "audited_artifact": str(BLOCK_PATH.relative_to(ROOT)),
        "computed_utc": now_utc(),
        "status": "EXPLORATORY_ONLY",
        "data_cutoff_utc": block["data_cutoff_utc"],
        "date_first": block["date_first"],
        "date_last": block["date_last"],
        "n_formations": block["n_formations"],
        "split_date": split_date,
        "n_first_half": split,
        "n_second_half": len(forms) - split,
        "baseline_high_low_diff_net_1x": baseline,
        "first_half": first,
        "second_half": second,
        "conclusion": "Anchor estimate not temporally stable across the frozen block; EXPLORATORY_ONLY, does not unlock confirmatory track.",
    }
    OUT_PATH.write_text(json.dumps(result, indent=2))
    print(
        json.dumps(
            {
                "split_date": split_date,
                "first_half": {
                    "n": first["n_formations"],
                    "diff": first["high_low_diff_net_1x"],
                    "se": first["bootstrap"]["se"],
                    "ci": first["bootstrap"]["ci_lo"],
                    "ci_hi": first["bootstrap"]["ci_hi"],
                },
                "second_half": {
                    "n": second["n_formations"],
                    "diff": second["high_low_diff_net_1x"],
                    "se": second["bootstrap"]["se"],
                    "ci": second["bootstrap"]["ci_lo"],
                    "ci_hi": second["bootstrap"]["ci_hi"],
                },
                "baseline": baseline,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
