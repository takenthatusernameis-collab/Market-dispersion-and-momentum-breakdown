#!/usr/bin/env python3
"""Panel-acquisition coverage reconciliation (DISP-003-PANELACQ-RECON-001, H46).

Read-only, stdlib-only reconciliation of two committed exploratory artifacts that
stand in unresolved tension:

  * H40 (PANELCOV-FEAS-001) concluded ``PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE``
    assuming the full per-asset ``expected_zip_files_upper_bound`` is acquirable.
  * H43 (PANELACQ-PROBE-001) keyless-HEAD-probed all 920 H41-planned monthly
    ``(symbol, kind, month)`` archive entries and found 889 served (HTTP 200) and
    31 absent (HTTP 404), concentrated in ARK, ALPHA, ASTR.

This script classifies each absent file against its ``(asset, kind)`` served
window so a reader can see which 404s are benign *pre-listing* gaps (the archive
serves nothing earlier, so H40's "in principle" verdict is unaffected) and which
are genuine *trailing* / *interior* / *entirely-absent* gaps that would make a
future acquisition incomplete.

Hard properties:
  * EXPLORATORY_ONLY -- no network, no downloads, no panels, no returns, no
    spreads/states/p-values/costs/inference, no promotion.
  * Does not re-probe the date-gated ``2026-11`` cutoff month.
  * Frozen artifacts are read-only (only read).
  * Import-safe: pure helpers importable without side effects or network.

Usage:
    python3 scripts/panel_archive_reconciliation.py
    python3 scripts/panel_archive_reconciliation.py --out <path>

Pure stdlib; no market data; no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-RECON-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = (
    EXP_DIR / "preregistrations" / "PANELACQ_RECON_001_v1.md"
)

# Committed read-only inputs (H41 plan + H43 probe + H40 feasibility context).
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)
H43_PROBE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
    / "integrity_audit"
    / "H004V106_panel_archive_probe_20261116T142247Z.json"
)
H40_FEAS = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
    / "integrity_audit"
    / "H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json"
)

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-RECON-001"
AUDIT_ID = "H004V106_PANELACQ_RECON_001"
HYPOTHESIS = "H46"

# Predeclared verdict labels (see preregistration section 5).
VERDICT_FULLY_BENIGN = "RECONCILIATION_FULLY_BENIGN"
VERDICT_HAS_GAPS = "RECONCILIATION_HAS_COVERAGE_GAPS"
VERDICT_JOIN_MISMATCH = "JOIN_MISMATCH"

# Classification labels for an absent month within its (asset, kind) window.
BEFORE_FIRST_SERVED = "BEFORE_FIRST_SERVED"
AFTER_LAST_SERVED = "AFTER_LAST_SERVED"
INTERIOR = "INTERIOR"
ENTIRELY_ABSENT = "ENTIRELY_ABSENT"


def entry_key(entry):
    """Join key for a plan/probe entry: (symbol, kind, month)."""
    return (entry.get("symbol"), entry.get("kind"), entry.get("month"))


def classify_absent_month(month, first_served, last_served):
    """Classify one absent ``YYYY-MM`` against its group's served window.

    ``first_served`` / ``last_served`` are ``None`` when the group has no served
    file at all (entirely absent).
    """
    if first_served is None or last_served is None:
        return ENTIRELY_ABSENT
    if month < first_served:
        return BEFORE_FIRST_SERVED
    if month > last_served:
        return AFTER_LAST_SERVED
    return INTERIOR


def _sorted_months(months):
    return sorted(m for m in months if m)


def build_groups(plan_entries, probe_entries):
    """Group plan+probe entries by (asset, kind) and classify each 404.

    Returns ``(groups, join_check)`` where ``groups`` is a dict keyed by
    ``(asset, kind)`` and ``join_check`` records the plan/probe key-set match.
    """
    plan_keys = {entry_key(e) for e in plan_entries}
    probe_keys = {entry_key(e) for e in probe_entries}
    plan_only = plan_keys - probe_keys
    probe_only = probe_keys - plan_keys
    join_ok = not plan_only and not probe_only and len(plan_keys) == len(probe_keys)

    # Map asset by symbol from the plan (probe also carries asset, but the plan is
    # the authoritative asset<->symbol mapping for the acquisition plan).
    symbol_to_asset = {}
    for e in plan_entries:
        sym = e.get("symbol")
        if sym is not None:
            symbol_to_asset.setdefault(sym, e.get("asset"))

    # Bucket probe entries by (asset, kind).
    buckets = {}
    for e in probe_entries:
        asset = symbol_to_asset.get(e.get("symbol"), e.get("asset"))
        key = (asset, e.get("kind"))
        buckets.setdefault(key, []).append(e)

    groups = {}
    for (asset, kind), entries in sorted(buckets.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        served_months = _sorted_months(
            e.get("month") for e in entries if e.get("http_status") == 200
        )
        first_served = served_months[0] if served_months else None
        last_served = served_months[-1] if served_months else None
        absent = []
        for e in entries:
            status = e.get("http_status")
            if status == 200:
                continue
            month = e.get("month")
            if status is None and e.get("error"):
                # Errored probe (not a clean 404): record but do not treat as a
                # coverage gap without a reason.
                absent.append(
                    {
                        "month": month,
                        "http_status": status,
                        "error": e.get("error"),
                        "classification": "ERROR",
                    }
                )
                continue
            absent.append(
                {
                    "month": month,
                    "http_status": status,
                    "classification": classify_absent_month(
                        month, first_served, last_served
                    ),
                }
            )
        groups[(asset, kind)] = {
            "asset": asset,
            "kind": kind,
            "n_total": len(entries),
            "n_served": len(served_months),
            "n_absent": len(absent),
            "first_served": first_served,
            "last_served": last_served,
            "absent": absent,
        }

    join_check = {
        "ok": join_ok,
        "n_plan_entries": len(plan_entries),
        "n_probe_entries": len(probe_entries),
        "n_plan_keys": len(plan_keys),
        "n_probe_keys": len(probe_keys),
        "n_plan_only": len(plan_only),
        "n_probe_only": len(probe_only),
    }
    return groups, join_check


def _class_counts(absent):
    counts = {}
    for a in absent:
        c = a.get("classification")
        counts[c] = counts.get(c, 0) + 1
    return counts


def reconcile(plan_entries, probe_entries, feasibility_per_asset=None):
    """Pure reconciliation over committed artifacts.

    ``feasibility_per_asset`` is an optional ``{asset: per_asset_record}`` map used
    only to annotate each asset group with the H40 required-study-months count and
    cap window. It never affects the verdict.
    """
    groups, join_check = build_groups(plan_entries, probe_entries)

    per_group = {}
    per_asset = {}
    absent_total = 0
    has_genuine_gap = False
    for (asset, kind), g in groups.items():
        cc = _class_counts(g["absent"])
        per_group[f"{asset}:{kind}"] = {
            "asset": asset,
            "kind": kind,
            "n_total": g["n_total"],
            "n_served": g["n_served"],
            "n_absent": g["n_absent"],
            "first_served": g["first_served"],
            "last_served": g["last_served"],
            "absent_class_counts": cc,
            "absent": g["absent"],
        }
        absent_total += g["n_absent"]
        # A genuine gap is anything not BEFORE_FIRST_SERVED and not ERROR-only.
        for label, n in cc.items():
            if label in (AFTER_LAST_SERVED, INTERIOR, ENTIRELY_ABSENT) and n > 0:
                has_genuine_gap = True
        # Per-asset roll-up.
        pa = per_asset.setdefault(
            asset,
            {
                "asset": asset,
                "n_total": 0,
                "n_served": 0,
                "n_absent": 0,
                "absent_class_counts": {},
                "kinds": {},
            },
        )
        pa["n_total"] += g["n_total"]
        pa["n_served"] += g["n_served"]
        pa["n_absent"] += g["n_absent"]
        pa["kinds"][kind] = {
            "n_served": g["n_served"],
            "n_absent": g["n_absent"],
            "first_served": g["first_served"],
            "last_served": g["last_served"],
        }
        for label, n in cc.items():
            pa["absent_class_counts"][label] = (
                pa["absent_class_counts"].get(label, 0) + n
            )

    # Annotate per-asset with H40 context if supplied.
    if feasibility_per_asset:
        for asset, pa in per_asset.items():
            ctx = feasibility_per_asset.get(asset)
            if not ctx:
                continue
            pa["h40_required_study_months"] = len(
                ctx.get("required_study_months") or []
            )
            pa["h40_cap_first_in_window"] = ctx.get("cap_first_in_window")
            pa["h40_cap_last_in_window"] = ctx.get("cap_last_in_window")
            pa["h40_expected_zip_files_upper_bound"] = ctx.get(
                "expected_zip_files_upper_bound"
            )

    if not join_check["ok"]:
        verdict = VERDICT_JOIN_MISMATCH
    elif has_genuine_gap:
        verdict = VERDICT_HAS_GAPS
    else:
        verdict = VERDICT_FULLY_BENIGN

    # Overall absent-set classification counts (regardless of group).
    absent_summary = {}
    for g in groups.values():
        for label, n in _class_counts(g["absent"]).items():
            absent_summary[label] = absent_summary.get(label, 0) + n

    return {
        "join_check": join_check,
        "n_absent_total": absent_total,
        "absent_summary": absent_summary,
        "per_group": per_group,
        "per_asset": per_asset,
        "verdict": verdict,
    }


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _feasibility_map(feas):
    per = feas.get("per_asset") or []
    if isinstance(per, dict):
        return per
    return {e.get("asset"): e for e in per if isinstance(e, dict)}


def build_audit(out_path=None):
    """Assemble the audit artifact. Writes only when ``out_path`` is given.

    Returns the audit dict so tests can call it hermetically without touching the
    filesystem.
    """
    plan = _load_json(H41_PLAN)
    probe = _load_json(H43_PROBE)
    feas = _load_json(H40_FEAS)

    plan_entries = plan["plan_entries"]
    probe_entries = probe["per_entry"]
    result = reconcile(plan_entries, probe_entries, _feasibility_map(feas))

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "computed_utc": _utc_now(),
        "preregistration": PREREG.relative_to(ROOT).as_posix(),
        "method": (
            "Read-only reconciliation of H41 plan (920 entries) and H43 probe "
            "(920 per_entry). Join on (symbol, kind, month); classify each 404 "
            "against its (asset, kind) served window as BEFORE_FIRST_SERVED / "
            "AFTER_LAST_SERVED / INTERIOR / ENTIRELY_ABSENT. H40 feasibility "
            "context annotates per-asset only. No network, no downloads, no "
            "panels, no outcomes."
        ),
        "audited_artifacts": {
            "h41_plan": H41_PLAN.relative_to(ROOT).as_posix(),
            "h43_probe": H43_PROBE.relative_to(ROOT).as_posix(),
            "h40_feasibility_context": H40_FEAS.relative_to(ROOT).as_posix(),
        },
        "join_check": result["join_check"],
        "n_absent_total": result["n_absent_total"],
        "absent_summary": result["absent_summary"],
        "per_group": result["per_group"],
        "per_asset": result["per_asset"],
        "verdict": result["verdict"],
        "verdict_rule": (
            "JOIN_MISMATCH if plan/probe key sets differ; else "
            "RECONCILIATION_HAS_COVERAGE_GAPS if any absent file is "
            "AFTER_LAST_SERVED / INTERIOR / ENTIRELY_ABSENT; else "
            "RECONCILIATION_FULLY_BENIGN (all 404s are BEFORE_FIRST_SERVED)."
        ),
        "exploratory_only": True,
        "promotion_allowed": False,
        "non_claims": [
            "No network access, no HEAD probe, no content downloaded.",
            "No panel constructed; no returns/spreads/states/p-values/costs/"
            "inference computed.",
            "Does not re-probe the date-gated 2026-11 cutoff month.",
            "Does not overturn or confirm H40's PANEL_EXTENSION_FEASIBLE_IN_"
            "PRINCIPLE verdict; only locates which absent files are benign "
            "(pre-listing) vs which a future acquisition must resolve.",
            "Cannot validate, replace, or unlock H1/H6/H7/H10 or any "
            "confirmatory track.",
            "Never fabricates a missing file; absent files stay absent.",
        ],
    }

    if out_path is not None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    return audit


def _utc_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Panel-acquisition coverage reconciliation (H46, read-only)."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path (default: <experiment>/integrity_audit/"
        "panel_archive_reconciliation_<computed_utc>.json).",
    )
    args = parser.parse_args(argv)

    if args.out:
        out_path = Path(args.out)
    else:
        # Compute the timestamped default path without writing twice.
        audit = build_audit(None)
        stamp = audit["computed_utc"].replace("-", "").replace(":", "").replace("Z", "Z")
        out_path = AUDIT_DIR / f"panel_archive_reconciliation_{stamp}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"verdict": audit["verdict"], "out": str(out_path)}))
        return 0

    audit = build_audit(out_path)
    print(
        json.dumps(
            {"verdict": audit["verdict"], "n_absent_total": audit["n_absent_total"],
             "out": str(out_path)}
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())