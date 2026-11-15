#!/usr/bin/env python3
"""Grid ledger internal-consistency audit for the 216-cell DISPERSION-003 grid.

Read-only integrity audit. For every committed cell in
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/grid_result_ledger.json`` it
recomputes the cell's own accounting, state counts, aggregate statistics, date
range, eligible-asset coverage and inference fields from that cell's
``formations`` array, and compares them against the cell's recorded fields.

Complements H29 (anchor-only cross-check), H30 (grid_summary vs ledger for the
two primary anchors) and H31 (H10 fresh forward block): this audit covers all
216 cells, including the 214 non-anchor cells that no other audit re-derives.

No frozen artifact, config, input, frontier, registry entry (other than the H32
allocation) or sealed holdout is modified. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
AUDIT_DIR = ART / "integrity_audit"
PREREG = ART / "preregistrations" / "H004V106_GRID_LEDGER_INTERNAL_CONSISTENCY_v1.md"

LEDGER_PATH = ART / "grid_result_ledger.json"

EXPECTED_CELLS = 216
EXPECTED_COST_1X = 0.001  # BASE_COST_TURN (0.0005) * 2.0, declared in eval_forward_block.py
TOL = 1e-12
ELIG_MEAN_TOL = 1e-9
VALID_STATES = ("high", "low", "mid")


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _mean(values: list[float]) -> float | None:
    vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return statistics.fmean(vals) if vals else None


def _median(values: list[float]) -> float | None:
    vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    return statistics.median(vals) if vals else None


def implied_costs(formations: list[dict]) -> list[float]:
    """Return ``spread_gross - spread_net_1x`` for each formation."""
    out = []
    for f in formations:
        g = f.get("spread_gross")
        n = f.get("spread_net_1x")
        if g is None or n is None:
            out.append(float("nan"))
        else:
            out.append(float(g) - float(n))
    return out


def recompute_aggregates(formations: list[dict]) -> dict:
    """Recompute every cell-level aggregate from a cell's formations array."""
    n = len(formations)
    if n == 0:
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
            "eligible_assets_per_date": {"mean": None, "min": None, "max": None},
        }

    states = [f.get("state") for f in formations]
    high_gross = [f["spread_gross"] for f in formations if f.get("state") == "high"]
    low_gross = [f["spread_gross"] for f in formations if f.get("state") == "low"]
    high_net = [f["spread_net_1x"] for f in formations if f.get("state") == "high"]
    low_net = [f["spread_net_1x"] for f in formations if f.get("state") == "low"]
    all_gross = [f["spread_gross"] for f in formations]
    all_net = [f["spread_net_1x"] for f in formations]

    high_gross_mean = _mean(high_gross)
    low_gross_mean = _mean(low_gross)
    high_net_mean = _mean(high_net)
    low_net_mean = _mean(low_net)

    dates = [f["formation_date"] for f in formations]
    elig = [int(f["n_assets"]) for f in formations]

    return {
        "n_formations": n,
        "n_high": states.count("high"),
        "n_low": states.count("low"),
        "n_mid": states.count("mid"),
        "high_gross_mean": high_gross_mean,
        "low_gross_mean": low_gross_mean,
        "high_net_1x_mean": high_net_mean,
        "low_net_1x_mean": low_net_mean,
        "high_low_diff_gross": (high_gross_mean - low_gross_mean)
        if high_gross_mean is not None and low_gross_mean is not None else None,
        "high_low_diff_net_1x": (high_net_mean - low_net_mean)
        if high_net_mean is not None and low_net_mean is not None else None,
        "spread_gross_mean": _mean(all_gross),
        "spread_net_1x_mean": _mean(all_net),
        "spread_gross_median": _median(all_gross),
        "spread_net_1x_median": _median(all_net),
        "date_first": min(dates) if dates else None,
        "date_last": max(dates) if dates else None,
        "eligible_assets_per_date": {
            "mean": _mean(elig),
            "min": min(elig) if elig else None,
            "max": max(elig) if elig else None,
        },
    }


def _num_eq(a, b, tol: float = TOL) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return False


def check_cell(cell: dict) -> dict:
    """Run every predeclared per-cell check and return a structured result."""
    cid = cell.get("config_id")
    formations = cell.get("formations", [])
    violations: list[str] = []

    # 1. n_formations matches and non-empty
    if cell.get("n_formations") != len(formations):
        violations.append(
            f"n_formations {cell.get('n_formations')!r} != len(formations) {len(formations)}"
        )
    if not formations:
        violations.append("cell has no formations")

    # 2. strictly increasing, unique formation dates
    dates = [f.get("formation_date") for f in formations]
    if any(d is None for d in dates):
        violations.append("formation with missing formation_date")
    else:
        if dates != sorted(dates):
            violations.append("formation dates are not strictly increasing")
        if len(set(dates)) != len(dates):
            violations.append("duplicate formation_date values")

    # 3-5. per-formation field validity
    for i, f in enumerate(formations):
        if f.get("state") not in VALID_STATES:
            violations.append(f"formation[{i}] invalid state {f.get('state')!r}")
        d = f.get("dispersion")
        if not isinstance(d, (int, float)) or not math.isfinite(d) or d < 0:
            violations.append(f"formation[{i}] invalid dispersion {d!r}")
        na = f.get("n_assets")
        if not isinstance(na, int) or isinstance(na, bool) or na <= 0:
            violations.append(f"formation[{i}] invalid n_assets {na!r}")

    # 6. accounting invariant: constant implied cost == EXPECTED_COST_1X
    costs = implied_costs(formations)
    finite_costs = [c for c in costs if math.isfinite(c)]
    if len(finite_costs) != len(costs):
        violations.append("formation with non-finite implied cost (gross/net missing)")
    elif finite_costs:
        spread = max(finite_costs) - min(finite_costs)
        if spread > TOL:
            violations.append(f"implied cost not constant (spread {spread:.3e})")
        if abs(statistics.fmean(finite_costs) - EXPECTED_COST_1X) > TOL:
            violations.append(
                f"implied cost {statistics.fmean(finite_costs)!r} != baseline {EXPECTED_COST_1X!r}"
            )

    # 7-11. aggregates
    recomputed = recompute_aggregates(formations)
    for field in (
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
    ):
        if not _num_eq(cell.get(field), recomputed.get(field)):
            violations.append(
                f"{field} {cell.get(field)!r} != recomputed {recomputed.get(field)!r}"
            )

    # Date fields are ISO strings, compared exactly.
    for field in ("date_first", "date_last"):
        if cell.get(field) != recomputed.get(field):
            violations.append(
                f"{field} {cell.get(field)!r} != recomputed {recomputed.get(field)!r}"
            )

    cell_elig = cell.get("eligible_assets_per_date", {})
    rec_elig = recomputed["eligible_assets_per_date"]
    for sub in ("mean", "min", "max"):
        tol = ELIG_MEAN_TOL if sub == "mean" else TOL
        if not _num_eq(cell_elig.get(sub), rec_elig.get(sub), tol=tol):
            violations.append(
                f"eligible_assets_per_date.{sub} {cell_elig.get(sub)!r} != "
                f"recomputed {rec_elig.get(sub)!r}"
            )

    # 11. inference fields
    p = cell.get("pvalue_bootstrap_two_sided")
    if p is not None and not (isinstance(p, (int, float)) and 0.0 <= float(p) <= 1.0):
        violations.append(f"pvalue_bootstrap_two_sided out of range {p!r}")
    if not isinstance(cell.get("holm_rejected"), bool):
        violations.append(f"holm_rejected not a boolean {cell.get('holm_rejected')!r}")

    return {
        "config_id": cid,
        "n_formations": len(formations),
        "matched": len(violations) == 0,
        "violations": violations,
    }


def check_ledger(ledger: dict, expected_cells: int = EXPECTED_CELLS) -> dict:
    """Run the per-cell checks plus the ledger-level checks.

    ``expected_cells`` is a parameter (defaulting to the declared 216-cell
    family) so the pure seam can be exercised on a small synthetic ledger.
    """
    cells = ledger.get("cells", {})
    per_cell = {}
    all_violations: list[dict] = []
    for cid in sorted(cells):
        result = check_cell(cells[cid])
        per_cell[cid] = result
        if not result["matched"]:
            all_violations.append({"config_id": cid, "violations": result["violations"]})

    global_violations: list[str] = []

    # 12. expected cell count and unique ids
    if len(cells) != expected_cells:
        global_violations.append(f"cell count {len(cells)} != {expected_cells}")
    if ledger.get("expected_cells") != expected_cells:
        global_violations.append(
            f"ledger expected_cells {ledger.get('expected_cells')!r} != {expected_cells}"
        )
    ids = [c.get("config_id") for c in cells.values()]
    if len(set(ids)) != len(ids):
        global_violations.append("duplicate config_id values in ledger")

    # 13. terminal-status counts
    status_counts = {"OK": 0, "BLOCKED": 0, "INVALID": 0, "FAILED": 0, "NOT_RUN": 0}
    for c in cells.values():
        st = c.get("status")
        if st in status_counts:
            status_counts[st] += 1
        else:
            global_violations.append(f"cell {c.get('config_id')} has unknown status {st!r}")
    if ledger.get("cells_ok") != status_counts["OK"]:
        global_violations.append(
            f"cells_ok {ledger.get('cells_ok')!r} != observed {status_counts['OK']}"
        )
    if ledger.get("cells_evaluated") != len(cells):
        global_violations.append(
            f"cells_evaluated {ledger.get('cells_evaluated')!r} != observed {len(cells)}"
        )
    if ledger.get("cells_failed") != status_counts["FAILED"]:
        global_violations.append(
            f"cells_failed {ledger.get('cells_failed')!r} != observed {status_counts['FAILED']}"
        )
    if ledger.get("cells_blocked") != status_counts["BLOCKED"]:
        global_violations.append(
            f"cells_blocked {ledger.get('cells_blocked')!r} != observed {status_counts['BLOCKED']}"
        )

    # 14. Holm rejection count
    holm_true = sum(1 for c in cells.values() if c.get("holm_rejected") is True)
    if ledger.get("holm_rejected_count") != holm_true:
        global_violations.append(
            f"holm_rejected_count {ledger.get('holm_rejected_count')!r} != observed {holm_true}"
        )

    passed = not all_violations and not global_violations
    return {
        "n_cells": len(cells),
        "per_cell": per_cell,
        "cell_violations": all_violations,
        "global_violations": global_violations,
        "status_counts": status_counts,
        "holm_rejected_true": holm_true,
        "passed": passed,
    }


def audit() -> dict:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    result = check_ledger(ledger)
    n_cell_violations = len(result["cell_violations"])
    n_checks_failed = sum(len(v["violations"]) for v in result["cell_violations"])
    passed = result["passed"]
    return {
        "audit_id": "H004V106_GRID_LEDGER_INTERNAL_CONSISTENCY",
        "experiment_id": EXP,
        "hypothesis": "H32",
        "status": "PASS" if passed else "FAIL",
        "generated_utc": now_utc(),
        "preregistration": _rel(PREREG),
        "script": "scripts/grid_ledger_internal_consistency.py",
        "inputs": {"ledger": _rel(LEDGER_PATH)},
        "n_cells_checked": result["n_cells"],
        "cells_with_violations": n_cell_violations,
        "total_violations": n_checks_failed + len(result["global_violations"]),
        "global_violations": result["global_violations"],
        "cell_violations": result["cell_violations"],
        "status_counts": result["status_counts"],
        "holm_rejected_true": result["holm_rejected_true"],
        "overall_passed": passed,
        "frozen_artifacts_modified": False,
        "interpretation": (
            "This audit verifies that every committed DISPERSION-003 grid cell is "
            "internally self-consistent with its own formation records (accounting, "
            "state counts, aggregates, date range, eligible coverage, inference "
            "fields). It is an integrity check on already-inspected development "
            "evidence, NOT a fresh holdout, NOT independent confirmation, and does "
            "NOT validate/refute/unlock H1/H6/H7/H8/H9/H10/H11."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="output path (default: integrity_audit/"
        "H004V106_grid_ledger_internal_consistency_<ts>.json)",
    )
    args = parser.parse_args(argv)

    report = audit()
    if args.out:
        out = Path(args.out)
    else:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out = AUDIT_DIR / f"H004V106_grid_ledger_internal_consistency_{stamp}.json"

    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    try:
        shown = out.relative_to(ROOT)
    except ValueError:
        shown = out
    print(
        f"[ledger-consistency] verdict={report['status']} "
        f"cells={report['n_cells_checked']} "
        f"cells_with_violations={report['cells_with_violations']} "
        f"total_violations={report['total_violations']}"
    )
    print(f"[ledger-consistency] -> {shown}")
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())