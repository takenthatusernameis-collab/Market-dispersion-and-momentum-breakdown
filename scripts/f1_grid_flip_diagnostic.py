#!/usr/bin/env python3
"""F1 grid Holm-status flip diagnostic (DISP-003-F1GRID-FLIP-001, H45).

Read-only, stdlib-only characterisation of the single grid cell whose Holm
rejection status differs between the two arms of the committed F1GRID-002
ledger-vintage (as-of 2026-09-30) sensitivity contrast:

  * arm A -- committed panels trimmed to the frozen ledger vintage
  * arm B -- the same panels with the four F1COVERAGE-001-repaired kline panels

The diagnostic is EXPLORATORY_ONLY: it reports descriptive deltas (net-1x point
estimate, bootstrap p-value, state counts) and classifies each flip cell by a
predeclared rule relative to the 0.05 economic-significance scale. It performs no
promotion, no multiple-testing family claim and no economic inference, and it
never opens the sealed forward block.

Usage:
    python3 scripts/f1_grid_flip_diagnostic.py
    python3 scripts/f1_grid_flip_diagnostic.py --ledger <path> --out <path>

Pure stdlib; no market data; no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-FLIP-001"
DEFAULT_LEDGER = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
    / "grid_result_ledger.json"
)
DEFAULT_SUMMARY = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
    / "grid_summary.json"
)
DEFAULT_OUT_DIR = ROOT / "artifacts" / EXP / "integrity_audit"

# Predeclared economic-significance scale (H10 net-1x threshold). Used here only
# as a descriptive ruler for the size of the point-estimate move, NOT as a
# promotion gate.
ECONOMIC_THRESHOLD = 0.05

ARM_A = "A_ledger_vintage_committed"
ARM_B = "B_ledger_vintage_f1_repaired"

_FIELDS = (
    "high_low_diff_net_1x",
    "pvalue_bootstrap_two_sided",
    "holm_rejected",
    "n_formations",
    "n_high",
    "n_low",
    "n_mid",
)


def _sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def classify_cell(a, b, threshold=ECONOMIC_THRESHOLD):
    """Classify one cell's arm-A -> arm-B move by the predeclared rule.

    Returns a dict of descriptive diagnostics plus a ``classification`` label:
      * SIGN_FLIP -- the net-1x point estimate changes sign (both non-zero)
      * MATERIAL_POINT_ESTIMATE_CHANGE -- |delta_net| >= threshold
      * MARGINAL_POINT_ESTIMATE_CHANGE -- otherwise
    """
    a_net = a["high_low_diff_net_1x"]
    b_net = b["high_low_diff_net_1x"]
    delta_net = b_net - a_net
    delta_p = b["pvalue_bootstrap_two_sided"] - a["pvalue_bootstrap_two_sided"]
    d_high = b["n_high"] - a["n_high"]
    d_low = b["n_low"] - a["n_low"]
    d_mid = b["n_mid"] - a["n_mid"]
    # A single formation moving from one bucket to another gives one +1 and one
    # -1; the number of formations that moved is the sum of the positive deltas.
    n_state_transfers = sum(d for d in (d_high, d_low, d_mid) if d > 0)
    denom = max(abs(a_net), 1e-12)
    relative_net_change = abs(delta_net) / denom

    if _sign(a_net) != 0 and _sign(b_net) != 0 and _sign(a_net) != _sign(b_net):
        classification = "SIGN_FLIP"
    elif abs(delta_net) >= threshold:
        classification = "MATERIAL_POINT_ESTIMATE_CHANGE"
    else:
        classification = "MARGINAL_POINT_ESTIMATE_CHANGE"

    return {
        "a_high_low_diff_net_1x": a_net,
        "b_high_low_diff_net_1x": b_net,
        "delta_high_low_diff_net_1x": delta_net,
        "relative_net_change": relative_net_change,
        "a_pvalue_bootstrap_two_sided": a["pvalue_bootstrap_two_sided"],
        "b_pvalue_bootstrap_two_sided": b["pvalue_bootstrap_two_sided"],
        "delta_pvalue": delta_p,
        "a_holm_rejected": a["holm_rejected"],
        "b_holm_rejected": b["holm_rejected"],
        "a_n_formations": a["n_formations"],
        "b_n_formations": b["n_formations"],
        "a_n_high": a["n_high"],
        "b_n_high": b["n_high"],
        "a_n_low": a["n_low"],
        "b_n_low": b["n_low"],
        "a_n_mid": a["n_mid"],
        "b_n_mid": b["n_mid"],
        "delta_n_high": d_high,
        "delta_n_low": d_low,
        "delta_n_mid": d_mid,
        "n_state_transfers": n_state_transfers,
        "parameters": dict(b.get("parameters") or a.get("parameters") or {}),
        "classification": classification,
    }


def analyze_ledger(ledger, threshold=ECONOMIC_THRESHOLD):
    """Pure analysis of a F1GRID-002-style ledger dict.

    Returns a deterministic dict with the flip set and per-cell diagnostics.
    """
    arms = ledger["arms"]
    cells_a = arms[ARM_A]["cells"]
    cells_b = arms[ARM_B]["cells"]
    common = sorted(set(cells_a) & set(cells_b))

    flip_cells = []
    for cid in common:
        a = cells_a[cid]
        b = cells_b[cid]
        if bool(a.get("holm_rejected")) != bool(b.get("holm_rejected")):
            diag = classify_cell(a, b, threshold)
            diag["config_id"] = cid
            diag["universe_arm"] = a.get("universe_arm") or b.get("universe_arm")
            flip_cells.append(diag)

    return {
        "expected_cells": ledger.get("expected_cells"),
        "n_cells_arm_a": len(cells_a),
        "n_cells_arm_b": len(cells_b),
        "n_cells_common": len(common),
        "n_flips": len(flip_cells),
        "flip_cells": flip_cells,
        "economic_threshold": threshold,
    }


def build_artifact(ledger, summary, ledger_path, computed_utc, threshold=ECONOMIC_THRESHOLD):
    """Assemble the audit artifact from the ledger (and optional summary cross-check)."""
    analysis = analyze_ledger(ledger, threshold)

    summary_flip_ids = None
    summary_holm_change = None
    if summary is not None:
        deltas = summary.get("cell_deltas") or []
        summary_flip_ids = sorted(
            c["config_id"] for c in deltas
            if bool(c.get("holm_rejected_a")) != bool(c.get("holm_rejected_b"))
        )
        summary_holm_change = (summary.get("aggregate_labels") or {}).get(
            "HOLM_STATUS_CHANGE"
        )

    analysis_ids = sorted(c["config_id"] for c in analysis["flip_cells"])
    summary_agrees = (
        summary_flip_ids is None or summary_flip_ids == analysis_ids
    )

    return {
        "experiment_id": EXP,
        "audit_id": "H004V106_F1GRID_FLIP_DIAGNOSTIC_20261117",
        "audited_artifact": str(
            Path(ledger_path).resolve().relative_to(ROOT).as_posix()
        )
        if Path(ledger_path).is_absolute()
        else str(ledger_path),
        "computed_utc": computed_utc,
        "preregistration": (
            f"artifacts/{EXP}/preregistrations/F1_GRID_FLIP_DIAGNOSTIC_v1.md"
        ),
        "method": (
            "For every config_id present in both F1GRID-002 arms, compare "
            "high_low_diff_net_1x, pvalue_bootstrap_two_sided, holm_rejected and "
            "n_high/n_low/n_mid; a flip cell is one whose holm_rejected differs. "
            "Each flip cell is classified SIGN_FLIP / MATERIAL_POINT_ESTIMATE_CHANGE "
            "(|delta_net| >= threshold) / MARGINAL_POINT_ESTIMATE_CHANGE by a rule "
            "predeclared before computation."
        ),
        "economic_threshold": analysis["economic_threshold"],
        "n_flips": analysis["n_flips"],
        "flip_cells": analysis["flip_cells"],
        "summary_crosscheck": {
            "summary_flip_ids": summary_flip_ids,
            "summary_holm_status_change": summary_holm_change,
            "ledger_flip_ids": analysis_ids,
            "agrees": summary_agrees,
        },
        "verdict": (
            f"{analysis['n_flips']} Holm-status flip cell(s) between F1GRID-002 arms "
            f"A and B; classifications: "
            + ", ".join(
                f"{c['config_id']}={c['classification']}"
                for c in analysis["flip_cells"]
            )
            + (
                "; the coverage repair changes Holm status for "
                f"{analysis['n_flips']} cell(s) without a material point-estimate "
                "move (all |delta_net| < economic threshold and same sign)."
                if analysis["flip_cells"]
                and all(
                    c["classification"] == "MARGINAL_POINT_ESTIMATE_CHANGE"
                    for c in analysis["flip_cells"]
                )
                else "; see per-cell classifications."
            )
        ),
        "exploratory_only": True,
        "promotion_allowed": False,
        "conclusion": (
            "EXPLORATORY_ONLY: descriptive coverage-sensitivity diagnostic on "
            "already-inspected F1GRID-002 development data; no p-value promotion, "
            "no multiple-testing family claim, no economic inference, no sealed "
            "holdout opened, no frozen artifact modified."
        ),
    }


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--out", default=None)
    parser.add_argument("--computed-utc", default=None)
    args = parser.parse_args(argv)

    ledger_path = Path(args.ledger)
    if not ledger_path.is_file():
        sys.exit(f"ledger not found: {ledger_path}")
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))

    summary = None
    if Path(args.summary).is_file():
        summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))

    import time

    computed_utc = args.computed_utc or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    artifact = build_artifact(ledger, summary, ledger_path, computed_utc)

    out_dir = Path(args.out) if args.out else DEFAULT_OUT_DIR
    out_path = out_dir / f"f1_grid_flip_diagnostic_{computed_utc.replace(':', '').replace('-', '')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[f1_grid_flip_diagnostic] n_flips={artifact['n_flips']}")
    for c in artifact["flip_cells"]:
        print(
            f"  {c['config_id']}: {c['classification']} "
            f"A.net={c['a_high_low_diff_net_1x']:.6f} "
            f"B.net={c['b_high_low_diff_net_1x']:.6f} "
            f"delta={c['delta_high_low_diff_net_1x']:+.6f} "
            f"p {c['a_pvalue_bootstrap_two_sided']}->{c['b_pvalue_bootstrap_two_sided']} "
            f"state_transfers={c['n_state_transfers']}"
        )
    print(f"[f1_grid_flip_diagnostic] wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))