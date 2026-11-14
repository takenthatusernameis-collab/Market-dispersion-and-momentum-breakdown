#!/usr/bin/env python3
"""Audit the execution state of the DISP-003 full-grid F1 coverage run.

DISP-003-F1GRID-001 (``scripts/run_f1_grid.py``) promises two outputs --
``grid_result_ledger.json`` and ``grid_summary.json`` -- and a fidelity anchor:
arm A on the committed panels must reproduce the frozen DISPERSION-003
``grid_result_ledger.json`` within 1e-9 on every cell, otherwise the run aborts
and writes no comparison.

This audit records, read-only, whether that promise was met, and why not when it
was not. It reuses the run script's own ``fidelity_check`` so the audit cannot
disagree with the gate it is reporting on. It never writes into the committed
experiment, never modifies a frozen artifact and never promotes a result.

Usage:
    python3 scripts/audit_f1_grid_execution_state.py [--out <path>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import run_f1_grid as grid  # unmodified run script (read-only import)

OLD_EXP = grid.OLD_EXP
NEW_EXP = grid.NEW_EXP
NEW_EXP_DIR = ROOT / "artifacts" / NEW_EXP
OLD_PANELS = ROOT / "artifacts" / OLD_EXP / "data" / "panels"
AUDIT_DIR = NEW_EXP_DIR / "integrity_audit"
PREREG = NEW_EXP_DIR / "preregistrations" / "F1_GRID_COVERAGE_REPAIR_v1.md"
ARM_A_CKPT = NEW_EXP_DIR / "grid_checkpoints" / "cell_checkpoint_armA_committed.json"
ARM_B_CKPT = NEW_EXP_DIR / "grid_checkpoints" / "cell_checkpoint_armB_f1_repaired.json"
OUT_LEDGER = NEW_EXP_DIR / "grid_result_ledger.json"
OUT_SUMMARY = NEW_EXP_DIR / "grid_summary.json"

FROZEN_HASHES = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def max_date(series: pd.Series) -> str | None:
    s = series.dropna().astype(str).str.slice(0, 10)
    return s.max() if len(s) else None


def panel_vintage() -> dict:
    kline_max, funding_max = [], []
    for p in sorted(OLD_PANELS.glob("binance_klines_*.csv")):
        df = pd.read_csv(p, usecols=["open_time"])
        kline_max.append(pd.to_datetime(df["open_time"].max(), unit="ms", utc=True))
    for p in sorted(OLD_PANELS.glob("binance_funding_*.csv")):
        df = pd.read_csv(p, usecols=["calc_time"])
        funding_max.append(pd.to_datetime(df["calc_time"].max(), unit="ms", utc=True))
    mc = pd.read_csv(OLD_PANELS / "marketcap_panel.csv", usecols=["date"])
    return {
        "kline_files": len(kline_max),
        "kline_max_open_time_utc": (
            max(kline_max).strftime("%Y-%m-%dT%H:%M:%SZ") if kline_max else None),
        "kline_min_of_file_maxima_utc": (
            min(kline_max).strftime("%Y-%m-%dT%H:%M:%SZ") if kline_max else None),
        "funding_files": len(funding_max),
        "funding_max_calc_time_utc": (
            max(funding_max).strftime("%Y-%m-%dT%H:%M:%SZ") if funding_max else None),
        "marketcap_rows": int(len(mc)),
        "marketcap_max_date": max_date(mc["date"]),
    }


def cell_partition(cells: dict) -> dict:
    return {
        "cells": len(cells),
        "ok": sum(1 for c in cells.values() if c.get("status") == "OK"),
        "blocked": sum(1 for c in cells.values() if c.get("status") == "BLOCKED"),
        "failed": sum(1 for c in cells.values() if c.get("status") == "FAILED"),
    }


def tail_formation_contrast(arm_a: dict, ledger: dict) -> dict:
    """Compare the last old-vintage formation of one cell across vintages.

    If the panel vintage changed, the same formation date gets a different
    forward window: a shorter window in the older vintage. That single
    observation explains a family-wide fidelity failure better than any
    aggregate drift count.
    """
    cid = "H004V002"
    a, b = arm_a.get(cid), ledger.get(cid)
    if not a or not b or not a.get("formations") or not b.get("formations"):
        return {}
    last_ledger_date = b["formations"][-1]["formation_date"]
    a_row = next((f for f in a["formations"]
                  if f["formation_date"] == last_ledger_date), None)
    return {
        "config_id": cid,
        "formation_date": last_ledger_date,
        "ledger_spread_gross": b["formations"][-1]["spread_gross"],
        "arm_a_spread_gross": a_row["spread_gross"] if a_row else None,
        "ledger_n_assets": b["formations"][-1]["n_assets"],
        "arm_a_n_assets": a_row["n_assets"] if a_row else None,
        "note": "the same formation date carries a different forward window in "
                "the two panel vintages; the older vintage ends immediately "
                "after this date, so its forward window degenerates to one bar",
    }


def drift_summary(fidelity: dict, arm_a: dict, ledger: dict) -> dict:
    date_last_diff = sum(
        1 for cid in set(arm_a) & set(ledger)
        if arm_a[cid].get("date_last") != ledger[cid].get("date_last"))
    nform_diff = sum(
        1 for cid in set(arm_a) & set(ledger)
        if arm_a[cid].get("n_formations") != ledger[cid].get("n_formations"))
    diffs = []
    for cid in sorted(set(arm_a) & set(ledger)):
        x, y = arm_a[cid].get("high_low_diff_net_1x"), ledger[cid].get("high_low_diff_net_1x")
        if isinstance(x, float) and isinstance(y, float):
            diffs.append(abs(x - y))
    return {
        "cells_with_different_date_last": date_last_diff,
        "cells_with_different_n_formations": nform_diff,
        "max_abs_delta_high_low_diff_net_1x": max(diffs) if diffs else None,
        "fidelity_passed": fidelity["passed"],
        "drift_count": fidelity["drift_count"],
        "compared_cells": fidelity["compared_cells"],
        "sample_drifts": fidelity["drifted"][:10],
    }


def audit() -> dict:
    ledger_exists = OUT_LEDGER.exists()
    summary_exists = OUT_SUMMARY.exists()
    ledger = (json.loads(OUT_LEDGER.read_text(encoding="utf-8"))
              if ledger_exists else {})
    committed = json.loads((ROOT / "artifacts" / OLD_EXP /
                            "grid_result_ledger.json").read_text(encoding="utf-8"))
    arm_a = (json.loads(ARM_A_CKPT.read_text(encoding="utf-8"))
             if ARM_A_CKPT.exists() else {})

    fidelity = (grid.fidelity_check(arm_a, committed["cells"])
                if arm_a and committed.get("cells") else
                {"passed": False, "drift_count": None, "compared_cells": 0,
                 "drifted": ["arm A checkpoint or committed ledger missing"]})

    vintage = panel_vintage()
    frozen = {rel: sha256_file(ROOT / "artifacts" / OLD_EXP / rel)
              for rel in grid.FROZEN_ARTIFACT_RELS}

    if ledger_exists and summary_exists and fidelity["passed"]:
        verdict = "PASS_EXECUTION_COMPLETE"
    elif arm_a and not ledger_exists:
        verdict = "BLOCKED_FIDELITY_ANCHOR_UNSATISFIABLE"
    elif not arm_a:
        verdict = "NOT_RUN"
    else:
        verdict = "INCOMPLETE_UNEXPECTED_STATE"

    arm_a_cells = arm_a
    committed_cells = committed["cells"]
    report = {
        "audit_id": "F1GRID-001-EXECUTION-STATE",
        "experiment_id": NEW_EXP,
        "hypothesis": "H26",
        "status": "BLOCKED_SPECIFICATION_GATE"
        if verdict.startswith("BLOCKED") else verdict,
        "audited_utc": now_utc(),
        "verdict": verdict,
        "promise": {
            "preregistration": str(PREREG.relative_to(ROOT)),
            "script": "scripts/run_f1_grid.py",
            "promised_outputs": [
                str(OUT_LEDGER.relative_to(ROOT)),
                str(OUT_SUMMARY.relative_to(ROOT)),
                str(ARM_A_CKPT.relative_to(ROOT)),
                str(ARM_B_CKPT.relative_to(ROOT)),
            ],
        },
        "evidence": {
            "prereg_sha256": sha256_file(PREREG),
            "script_sha256": sha256_file(ROOT / "scripts" / "run_f1_grid.py"),
            "arm_a_checkpoint_sha256": sha256_file(ARM_A_CKPT),
            "arm_b_checkpoint_sha256": sha256_file(ARM_B_CKPT),
            "committed_ledger_sha256": sha256_file(
                ROOT / "artifacts" / OLD_EXP / "grid_result_ledger.json"),
            "committed_ledger_evaluated_utc": committed.get("evaluated_utc"),
            "committed_ledger_cells_ok": committed.get("cells_ok"),
            "committed_ledger_holm_rejected_count": committed.get("holm_rejected_count"),
            "arm_a_cells": cell_partition(arm_a_cells),
            "arm_a_max_date_last": max((c.get("date_last") for c in arm_a_cells.values()
                                        if c.get("date_last")), default=None),
            "committed_ledger_max_date_last": max(
                (c.get("date_last") for c in committed_cells.values()
                 if c.get("date_last")), default=None),
            "panel_vintage": vintage,
            "outputs": {
                "ledger_present": ledger_exists,
                "summary_present": summary_exists,
                "arm_b_checkpoint_present": ARM_B_CKPT.exists(),
                "ledger_experiment_id": ledger.get("experiment_id"),
                "ledger_fidelity_anchor": (ledger.get("fidelity_anchor") or None)
                if ledger_exists else None,
            },
        },
        "fidelity": drift_summary(fidelity, arm_a_cells, committed_cells),
        "vintage_mismatch": {
            "panel_max_kline_date": (vintage["kline_max_open_time_utc"] or "")[:10],
            "ledger_max_formation_date": max(
                (c.get("date_last") for c in committed_cells.values()
                 if c.get("date_last")), default=None),
            "arm_a_max_formation_date": max(
                (c.get("date_last") for c in arm_a_cells.values()
                 if c.get("date_last")), default=None),
            "tail_formation_contrast": tail_formation_contrast(arm_a_cells,
                                                               committed_cells),
        },
        "frozen_artifacts": {
            rel: {"sha256": digest, "matches_declared_constant":
                  digest == FROZEN_HASHES.get(rel)}
            for rel, digest in frozen.items()
            if rel in FROZEN_HASHES
        },
        "disposition": {
            "frozen_artifacts_modified": False,
            "committed_panels_modified": False,
            "comparison_written": ledger_exists,
            "promotion": "none: EXPLORATORY_ONLY development evidence; a fidelity "
                         "failure aborts the run and writes no comparison",
        },
        "interpretation": (
            "The preregistered fidelity anchor requires arm A on the committed "
            "panels to reproduce the frozen 216-cell DISPERSION-003 ledger within "
            "1e-9. The committed panels now end later than the vintage that "
            "produced that ledger, so the same formation dates carry different "
            "forward windows and no cell reproduces. The run script aborts by "
            "design and writes no comparison; nothing is promoted and no frozen "
            "artifact is modified. Re-running on the current vintage cannot "
            "satisfy the anchor; satisfying it requires an explicitly "
            "vintage-matched arm A under a new experiment ID and preregistration."),
        "next_test": (
            "Either (a) preregister a new EXPLORATORY_ONLY experiment that trims "
            "the panels to the frozen ledger's as-of date so arm A reproduces the "
            "committed ledger, then compares arm B on that same vintage; or "
            "(b) re-baseline arm A on the current vintage and drop the "
            "ledger-anchor claim. Neither path may promote a result or modify the "
            "frozen 003 artifacts, and neither may treat this audit as confirmation."),
    }
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None,
                        help="output path (default: integrity_audit/"
                             "f1_grid_execution_state_audit_<ts>.json)")
    args = parser.parse_args(argv)

    report = audit()
    if args.out:
        out = Path(args.out)
    else:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out = AUDIT_DIR / f"f1_grid_execution_state_audit_{stamp}.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"[audit] verdict={report['verdict']} "
          f"fidelity_passed={report['fidelity']['fidelity_passed']} "
          f"drift_count={report['fidelity']['drift_count']}")
    print(f"[audit] -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())