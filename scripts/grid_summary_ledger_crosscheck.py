#!/usr/bin/env python3
"""Grid summary / ledger cross-check audit for H004V106.

Read-only integrity audit: verifies that the primary anchor aggregates in
grid_summary.json match a recomputation from the per-cell formation records in
grid_result_ledger.json. No frozen artifacts are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_DIR = ART / "integrity_audit"
PREREG = ART / "preregistrations" / "H004V106_GRID_SUMMARY_LEDGER_CROSSCHECK_v1.md"

LEDGER_PATH = ART / "grid_result_ledger.json"
SUMMARY_PATH = ART / "grid_summary.json"

ANCHORS = ("H004V105", "H004V106")
SUMMARY_KEYS = {
    "H004V105": "primary_anchor_legacy_H004V105",
    "H004V106": "primary_anchor_expanding_H004V106",
}

TOL = 1e-12


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def recompute_from_formations(formations: list[dict]) -> dict:
    """Recompute all aggregates from a cell's formations array."""
    if not formations:
        return {
            "n_formations": 0,
            "n_high": 0,
            "n_low": 0,
            "n_mid": 0,
            "high_gross_mean": None,
            "low_gross_mean": None,
            "high_net_1x_mean": None,
            "low_net_1x_mean": None,
            "high_low_diff_gross": None,
            "high_low_diff_net_1x": None,
            "spread_gross_mean": None,
            "spread_net_1x_mean": None,
            "spread_gross_median": None,
            "spread_net_1x_median": None,
            "date_first": None,
            "date_last": None,
            "eligible_assets_per_date": {"mean": 0.0, "min": 0, "max": 0},
        }

    df = pd.DataFrame(formations)
    n_formations = len(df)
    n_high = int((df["state"] == "high").sum())
    n_low = int((df["state"] == "low").sum())
    n_mid = int((df["state"] == "mid").sum())

    high_gross = df[df["state"] == "high"]["spread_gross"].dropna()
    low_gross = df[df["state"] == "low"]["spread_gross"].dropna()
    high_net = df[df["state"] == "high"]["spread_net_1x"].dropna()
    low_net = df[df["state"] == "low"]["spread_net_1x"].dropna()

    high_gross_mean = float(high_gross.mean()) if len(high_gross) else None
    low_gross_mean = float(low_gross.mean()) if len(low_gross) else None
    high_net_mean = float(high_net.mean()) if len(high_net) else None
    low_net_mean = float(low_net.mean()) if len(low_net) else None

    high_low_diff_gross = (
        float(high_gross_mean - low_gross_mean)
        if high_gross_mean is not None and low_gross_mean is not None
        else None
    )
    high_low_diff_net = (
        float(high_net_mean - low_net_mean)
        if high_net_mean is not None and low_net_mean is not None
        else None
    )

    all_gross = df["spread_gross"].dropna()
    all_net = df["spread_net_1x"].dropna()
    spread_gross_mean = float(all_gross.mean()) if len(all_gross) else None
    spread_net_mean = float(all_net.mean()) if len(all_net) else None
    spread_gross_median = float(all_gross.median()) if len(all_gross) else None
    spread_net_median = float(all_net.median()) if len(all_net) else None

    dates = df["formation_date"].tolist()
    date_first = min(dates) if dates else None
    date_last = max(dates) if dates else None

    elig_counts = [int(r.get("n_assets", 0)) for r in formations]
    elig_mean = float(statistics.mean(elig_counts)) if elig_counts else 0.0
    elig_min = int(min(elig_counts)) if elig_counts else 0
    elig_max = int(max(elig_counts)) if elig_counts else 0

    return {
        "n_formations": n_formations,
        "n_high": n_high,
        "n_low": n_low,
        "n_mid": n_mid,
        "high_gross_mean": high_gross_mean,
        "low_gross_mean": low_gross_mean,
        "high_net_1x_mean": high_net_mean,
        "low_net_1x_mean": low_net_mean,
        "high_low_diff_gross": high_low_diff_gross,
        "high_low_diff_net_1x": high_low_diff_net,
        "spread_gross_mean": spread_gross_mean,
        "spread_net_1x_mean": spread_net_mean,
        "spread_gross_median": spread_gross_median,
        "spread_net_1x_median": spread_net_median,
        "date_first": date_first,
        "date_last": date_last,
        "eligible_assets_per_date": {
            "mean": elig_mean,
            "min": elig_min,
            "max": elig_max,
        },
    }


def compare_values(key: str, ledger_val, summary_val, diffs: list[str]) -> None:
    """Compare a recomputed value against the summary, record any mismatch."""
    if ledger_val is None and summary_val is None:
        return
    if ledger_val is None or summary_val is None:
        diffs.append(f"  {key}: ledger={ledger_val!r} vs summary={summary_val!r} (one None)")
        return
    if isinstance(ledger_val, float) or isinstance(summary_val, float):
        try:
            lv, sv = float(ledger_val), float(summary_val)
        except (TypeError, ValueError):
            diffs.append(f"  {key}: type mismatch {ledger_val!r} vs {summary_val!r}")
            return
        if np.isnan(lv) and np.isnan(sv):
            return
        if abs(lv - sv) > TOL:
            diffs.append(f"  {key}: {lv!r} vs {sv!r} (diff {abs(lv - sv):.3e})")
        return
    if ledger_val != summary_val:
        diffs.append(f"  {key}: {ledger_val!r} vs {summary_val!r}")


def audit() -> dict:
    # Load inputs
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))

    ledger_cells = ledger.get("cells", {})
    results = {}
    all_diffs = []

    for anchor in ANCHORS:
        summary_key = SUMMARY_KEYS[anchor]
        ledger_cell = ledger_cells.get(anchor, {})
        summary_anchor = summary.get(summary_key, {})

        formations = ledger_cell.get("formations", [])
        recomputed = recompute_from_formations(formations)
        summary_formations = summary_anchor.get("formations", [])
        recomputed_summary = recompute_from_formations(summary_formations) if summary_formations else {}

        # Also compare against the summary's top-level fields (which may be pre-aggregated)
        diffs = []
        fields_to_check = [
            "n_formations",
            "n_high",
            "n_low",
            "n_mid",
            "high_gross_mean",
            "low_gross_mean",
            "high_net_1x_mean",
            "low_net_1x_mean",
            "high_low_diff_gross",
            "high_low_diff_net_1x",
            "spread_gross_mean",
            "spread_net_1x_mean",
            "spread_gross_median",
            "spread_net_1x_median",
            "date_first",
            "date_last",
        ]
        for field in fields_to_check:
            ledger_v = recomputed.get(field)
            summary_v = summary_anchor.get(field)
            compare_values(field, ledger_v, summary_v, diffs)

        # Also check eligible_assets_per_date
        ledger_e = recomputed.get("eligible_assets_per_date", {})
        summary_e = summary_anchor.get("eligible_assets_per_date", {})
        for subfield in ("mean", "min", "max"):
            compare_values(f"eligible_assets_per_date.{subfield}", ledger_e.get(subfield), summary_e.get(subfield), diffs)

        # Cross-check: summary's formations array vs ledger's formations array
        if summary_formations:
            diffs2 = []
            for field in fields_to_check:
                ledger_v = recomputed.get(field)
                summary_v = recomputed_summary.get(field)
                compare_values(field, ledger_v, summary_v, diffs2)
            if diffs2:
                diffs.append("  [summary-formations-recompute mismatch]")
                diffs.extend(diffs2)

        results[anchor] = {
            "recomputed_from_ledger": recomputed,
            "summary_fields": {k: summary_anchor.get(k) for k in fields_to_check},
            "summary_eligible_assets": summary_anchor.get("eligible_assets_per_date"),
            "matched": len(diffs) == 0,
            "diffs": diffs,
        }
        if diffs:
            all_diffs.append({"anchor": anchor, "diffs": diffs})

    passed = len(all_diffs) == 0

    return {
        "audit_id": "H004V106_GRID_SUMMARY_LEDGER_CROSSCHECK",
        "experiment_id": EXP,
        "hypothesis": "H30",
        "status": "PASS" if passed else "FAIL",
        "audited_utc": now_utc(),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "script": "scripts/grid_summary_ledger_crosscheck.py",
        "inputs": {
            "ledger": str(LEDGER_PATH.relative_to(ROOT)),
            "summary": str(SUMMARY_PATH.relative_to(ROOT)),
        },
        "anchors_checked": list(ANCHORS),
        "results": results,
        "overall_passed": passed,
        "total_diffs": sum(len(d["diffs"]) for d in all_diffs),
        "frozen_artifacts_modified": False,
        "interpretation": (
            "This audit verifies internal consistency between the committed grid "
            "ledger and the grid summary for the primary anchors H004V105 and "
            "H004V106. It is an integrity check on already-inspected development "
            "evidence (DISPERSION-003), NOT a fresh holdout, NOT independent "
            "confirmation, and does NOT validate/refute/unlock H1/H6/H7/H8/H9/H10/H11."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="output path (default: integrity_audit/H004V106_grid_summary_ledger_crosscheck_<ts>.json)")
    args = parser.parse_args(argv)

    report = audit()

    if args.out:
        out = Path(args.out)
    else:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out = AUDIT_DIR / f"H004V106_grid_summary_ledger_crosscheck_{stamp}.json"

    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"[crosscheck] verdict={report['status']} diffs={report['total_diffs']}")
    print(f"[crosscheck] -> {out.relative_to(ROOT)}")

    if not report["overall_passed"]:
        for a in report["results"].values():
            if a["diffs"]:
                print(f"  [{a.get('anchor','?')}] mismatches:")
                for d in a["diffs"]:
                    print(f"    {d}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())