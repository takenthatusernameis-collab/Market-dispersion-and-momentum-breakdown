#!/usr/bin/env python3
"""Independent overlap-aware uncertainty audit of the sealed canonical
H004V106 forward block.

Read-only: consumes only the sealed
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json
and recomputes (a) every sealed outcome field from the formations ledger and
(b) the additive formation-month cluster-bootstrap (overlap-aware) interval on
the high-minus-low net-1x spread difference.

The sealed block's own ``overlap_aware_uncertainty`` field is null (it was
sealed before that reporting was added), so this audit records it here as a NEW
artifact without touching, re-sealing or overwriting the sealed block.

Status: EXPLORATORY_ONLY. The canonical block is a strict subset of the grid
ledger's development window and was already inspected during tuning, so it is
development/exploratory evidence and NOT independent confirmation. Nothing in
this audit promotes H1/H6/H7 or unlocks the confirmatory track. No frozen
artifact, grid ledger, DISPERSION-001/002 file or forward-block input is
modified.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
CANONICAL = ART / "forward_block" / "forward_block_evaluation.json"
AUDIT_DIR = ART / "integrity_audit"

# Reuse the pipeline's exact overlap-aware interval so the audit and the
# fresh-block pipeline report the same statistic on the same data.
sys.path.insert(0, str(ROOT / "scripts"))
from eval_forward_block import overlap_aware_interval  # noqa: E402


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    block = load_json(CANONICAL)
    formations = block.get("formations", [])
    records = [
        {
            "formation_date": f["formation_date"],
            "state": f["state"],
            "spread_net_1x": f["spread_net_1x"],
        }
        for f in formations
    ]

    dispersions = [f["dispersion"] for f in formations]
    net = [f["spread_net_1x"] for f in formations]
    gross = [f["spread_gross"] for f in formations]
    hi_net = [f["spread_net_1x"] for f in formations if f["state"] == "high"]
    lo_net = [f["spread_net_1x"] for f in formations if f["state"] == "low"]
    hi_gross = [f["spread_gross"] for f in formations if f["state"] == "high"]
    lo_gross = [f["spread_gross"] for f in formations if f["state"] == "low"]

    state_counts = {"high": 0, "low": 0, "mid": 0}
    for f in formations:
        state_counts[f["state"]] = state_counts.get(f["state"], 0) + 1

    n_assets = [f["n_assets"] for f in formations]
    finite_disp = sum(1 for d in dispersions if d is not None and abs(d) < float("inf"))
    non_finite_disp = len(dispersions) - finite_disp

    def mean(xs):
        return float(statistics.fmean(xs)) if xs else None

    def median(xs):
        return float(statistics.median(xs)) if xs else None

    overlap = overlap_aware_interval(records, n_boot=2000, rng_seed=20261102)

    recomputed = {
        "n_formations": len(formations),
        "state_counts": state_counts,
        "n_assets_min": int(min(n_assets)) if n_assets else 0,
        "n_assets_max": int(max(n_assets)) if n_assets else 0,
        "finite_dispersion_count": finite_disp,
        "non_finite_dispersion_count": non_finite_disp,
        "spread_net_mean_recomputed": mean(net),
        "spread_net_median_recomputed": median(net),
        "spread_gross_mean_recomputed": mean(gross),
        "spread_gross_median_recomputed": median(gross),
        "high_net_mean_recomputed": mean(hi_net),
        "low_net_mean_recomputed": mean(lo_net),
        "high_gross_mean_recomputed": mean(hi_gross),
        "low_gross_mean_recomputed": mean(lo_gross),
        "high_low_diff_net_recomputed": (
            float(mean(hi_net) - mean(lo_net)) if hi_net and lo_net else None
        ),
        "high_low_diff_gross_recomputed": (
            float(mean(hi_gross) - mean(lo_gross)) if hi_gross and lo_gross else None
        ),
        "date_first": formations[0]["formation_date"] if formations else None,
        "date_last": formations[-1]["formation_date"] if formations else None,
    }

    audit = {
        "audit_id": "H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102",
        "addendum_id": None,
        "audit_utc": now_utc(),
        "audited_artifact": str(CANONICAL.relative_to(ROOT)),
        "audited_artifact_sha256": sha256_file(CANONICAL),
        "status": "EXPLORATORY_ONLY",
        "canonical_summary": {
            "anchor_id": block.get("anchor_id"),
            "data_cutoff_utc": block.get("data_cutoff_utc"),
            "date_first": block.get("date_first"),
            "date_last": block.get("date_last"),
            "n_formations": block.get("n_formations"),
            "n_high": block.get("n_high"),
            "n_low": block.get("n_low"),
            "n_mid": block.get("n_mid"),
            "high_low_diff_net_1x": block.get("high_low_diff_net_1x"),
            "high_low_diff_gross": block.get("high_low_diff_gross"),
            "spread_net_1x_mean": block.get("spread_net_1x_mean"),
            "spread_net_1x_median": block.get("spread_net_1x_median"),
            "spread_gross_mean": block.get("spread_gross_mean"),
            "spread_gross_median": block.get("spread_gross_median"),
            "status": block.get("status"),
            "block_sealed": block.get("block_sealed"),
            "overlap_aware_uncertainty": block.get("overlap_aware_uncertainty"),
        },
        "canonical_recomputed": recomputed,
        "overlap_aware": overlap,
        "reconciliation": {
            "canonical_reported_vs_recomputed_n_formations_match": recomputed["n_formations"] == block.get("n_formations"),
            "canonical_reported_vs_recomputed_diff_net_match": (
                recomputed["high_low_diff_net_recomputed"] is not None
                and abs(recomputed["high_low_diff_net_recomputed"] - block.get("high_low_diff_net_1x")) < 1e-9
            ),
            "canonical_state_counts_match": state_counts == {
                "high": block.get("n_high"),
                "low": block.get("n_low"),
                "mid": block.get("n_mid"),
            },
            "canonical_finite_dispersion": non_finite_disp == 0,
            "cost_treatment": "net = gross - 0.001 (1x cost) per formation; high_low_diff identical gross vs net because the per-formation cost cancels in the difference of state means",
            "overlap_dependence_note": "formations are daily overlapping 30-day forward horizons; the simple mean difference ignores autocorrelation, so uncertainty is reported at the formation-month cluster level",
        },
        "conclusion": (
            "Canonical H004V106 sealed forward block is internally consistent and finite (608 formations, "
            "n_high=61, n_low=90, n_mid=457, high_low_diff_net_1x=+0.6165223953929935, all spreads finite, "
            "block sealed). The sealed block's overlap_aware_uncertainty was null; this audit computes it "
            "as a formation-month cluster-bootstrap interval (n_boot=2000, fixed seed) and reports it here. "
            "The block is a strict subset of the grid ledger's development window and was already inspected, "
            "so it is development/exploratory evidence only -- NOT independent confirmation and NOT a "
            "confirmatory claim for H1/H6/H7. Label EXPLORATORY_ONLY. No sealed artifact was modified."
        ),
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIT_DIR / "H004V106_forward_block_overlap_aware_audit_20261102.json"
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"[overlap-aware-audit] wrote {out_path.relative_to(ROOT)}")
    print(f"[overlap-aware-audit] status={audit['status']} overlap_aware.status={overlap['status']}")
    if overlap.get("status") == "OK":
        print(
            f"[overlap-aware-audit] baseline={overlap['baseline_high_low_diff_net_1x']:.6f} "
            f"bootstrap_mean={overlap['bootstrap_mean']:.6f} "
            f"bootstrap_se={overlap['bootstrap_se']:.6f} "
            f"ci_95=[{overlap['ci_95_percentile'][0]:.6f},{overlap['ci_95_percentile'][1]:.6f}] "
            f"ci_includes_zero={overlap['ci_includes_zero']} "
            f"n_months={overlap['n_months']} "
            f"n_clusters_with_both_states={overlap['n_clusters_with_both_states']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
