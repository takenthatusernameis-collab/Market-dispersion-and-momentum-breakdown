#!/usr/bin/env python3
"""Panel-coverage eligibility roster (DISP-003-PANELCOV-NARROW-001, H47).

Read-only, stdlib-only adjudication that converts H46's per-file reconciliation
into an **asset-level eligibility roster** for the ten H41 panel-extension
assets: for each asset, the archive window actually served, every absent planned
file classified against that window, and an inclusion/exclusion decision.

This implements H46's own next-test option (b): "explicitly narrow the eligible
expanding universe to exclude assets whose required study months are not fully
served."

Hard properties:
  * EXPLORATORY_ONLY -- no network, no downloads, no panels, no returns, no
    spreads/states/p-values/costs/inference, no promotion.
  * Missing files are never fabricated; they stay absent and are listed.
  * Frozen artifacts are read-only (only read).
  * Does not re-probe the date-gated ``2026-11`` cutoff month.
  * Import-safe: pure helpers importable without side effects or network.

Usage:
    python3 scripts/panel_coverage_eligibility_roster.py
    python3 scripts/panel_coverage_eligibility_roster.py --out <path>

Pure stdlib; no market data; no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELCOV_NARROW_001_v1.md"

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

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001"
AUDIT_ID = "H004V106_PANELCOV_NARROW_001"
HYPOTHESIS = "H47"

# Pre-declared roster verdict labels (preregistration section 4).
VERDICT_ALL_SERVED = "ROSTER_ALL_ASSETS_FULLY_SERVED"
VERDICT_HAS_UNSERVED = "ROSTER_HAS_UNSERVED_ASSETS"
VERDICT_JOIN_MISMATCH = "ROSTER_JOIN_MISMATCH"

# Pre-declared per-asset inclusion decisions (preregistration section 4).
INCLUDED_FULLY_SERVED = "INCLUDED_FULLY_SERVED"
INCLUDED_PRELISTING_GAPS_ONLY = "INCLUDED_PRELISTING_GAPS_ONLY"
EXCLUDED_UNPROBED = "EXCLUDED_UNPROBED"
EXCLUDED_PROBE_ERROR = "EXCLUDED_PROBE_ERROR"
EXCLUDED_UNSERVED_TIMELINE = "EXCLUDED_UNSERVED_TIMELINE"

# Classification labels for an absent planned file within its (asset, kind) window.
BEFORE_FIRST_SERVED = "BEFORE_FIRST_SERVED"
AFTER_LAST_SERVED = "AFTER_LAST_SERVED"
INTERIOR = "INTERIOR"
ENTIRELY_ABSENT = "ENTIRELY_ABSENT"
ERROR = "ERROR"
UNPROBED = "UNPROBED"

EXCLUSIONARY_GAP_CLASSES = (AFTER_LAST_SERVED, INTERIOR, ENTIRELY_ABSENT)


def entry_key(entry):
    """Join key for a plan/probe entry: (symbol, kind, month)."""
    return (entry.get("symbol"), entry.get("kind"), entry.get("month"))


def classify_absent_month(month, first_served, last_served):
    """Classify one absent ``YYYY-MM`` against its group's served window.

    ``first_served`` / ``last_served`` are ``None`` when the group serves no file
    at all (entirely absent).
    """
    if first_served is None or last_served is None:
        return ENTIRELY_ABSENT
    if month < first_served:
        return BEFORE_FIRST_SERVED
    if month > last_served:
        return AFTER_LAST_SERVED
    return INTERIOR


def build_roster(plan_entries, probe_entries, feasibility_per_asset=None):
    """Pure eligibility roster over the H41 plan and H43 probe entries.

    ``feasibility_per_asset`` is an optional ``{asset: record}`` map (H40). It is
    used only to annotate ``n_required_months_outside_verified_window`` for
    included assets; it never affects a decision.
    """
    probe_by_key = {}
    for e in probe_entries:
        probe_by_key.setdefault(entry_key(e), e)

    plan_keys = [entry_key(e) for e in plan_entries]
    plan_key_set = set(plan_keys)
    probe_key_set = set(probe_by_key)
    plan_only = plan_key_set - probe_key_set
    probe_only = probe_key_set - plan_key_set

    # Arm: per (asset, kind) served window from HTTP 200 responses.
    served_months = {}
    for key in sorted(probe_key_set):
        probe = probe_by_key[key]
        if probe.get("http_status") == 200:
            served_months.setdefault((key[0], key[1]), []).append(key[2])
    windows = {}
    for (symbol, kind), months in served_months.items():
        ordered = sorted(m for m in months if m)
        windows[(symbol, kind)] = (ordered[0], ordered[-1])

    # Asset roll-up, sorted for byte-stable output.
    per_asset = {}
    for plan in sorted(plan_entries, key=lambda e: (str(e.get("symbol")), str(e.get("kind")), str(e.get("month")))):
        asset = plan.get("asset")
        symbol = plan.get("symbol")
        kind = plan.get("kind")
        month = plan.get("month")
        record = per_asset.setdefault(
            asset,
            {
                "asset": asset,
                "symbol": symbol,
                "n_planned": 0,
                "n_served": 0,
                "n_absent": 0,
                "absent": [],
                "served_window": {},
                "kinds": sorted({
                    p.get("kind") for p in plan_entries if p.get("asset") == asset
                }),
            },
        )
        record["n_planned"] += 1
        probe = probe_by_key.get(entry_key(plan))
        if probe is None:
            record["n_absent"] += 1
            record["absent"].append(
                {"kind": kind, "month": month, "classification": UNPROBED}
            )
            continue
        status = probe.get("http_status")
        if status == 200:
            record["n_served"] += 1
            continue
        record["n_absent"] += 1
        if status is None and probe.get("error"):
            record["absent"].append(
                {
                    "kind": kind,
                    "month": month,
                    "http_status": status,
                    "error": probe.get("error"),
                    "classification": ERROR,
                }
            )
            continue
        first, last = windows.get((symbol, kind), (None, None))
        record["absent"].append(
            {
                "kind": kind,
                "month": month,
                "http_status": status,
                "classification": classify_absent_month(month, first, last),
            }
        )

    # Decision per asset (pre-declared priority order).
    for asset in sorted(per_asset):
        record = per_asset[asset]
        record["absent"] = sorted(
            record["absent"],
            key=lambda a: (str(a.get("kind")), str(a.get("month"))),
        )
        for kind in record["kinds"]:
            first, last = windows.get((record["symbol"], kind), (None, None))
            record["served_window"][kind] = {"first": first, "last": last}
        classes = {a.get("classification") for a in record["absent"]}
        if UNPROBED in classes:
            decision = EXCLUDED_UNPROBED
        elif ERROR in classes:
            decision = EXCLUDED_PROBE_ERROR
        elif classes & set(EXCLUSIONARY_GAP_CLASSES):
            decision = EXCLUDED_UNSERVED_TIMELINE
        elif record["n_absent"] == 0:
            decision = INCLUDED_FULLY_SERVED
        else:
            decision = INCLUDED_PRELISTING_GAPS_ONLY
        record["decision"] = decision
        record["included"] = decision.startswith("INCLUDED")
        record["absent_class_counts"] = _class_counts(record["absent"])

        # Study-month exposure annotation (H40 context only, never a decision).
        required = []
        if feasibility_per_asset:
            ctx = feasibility_per_asset.get(asset) or {}
            required = ctx.get("required_study_months") or []
        outside = []
        for month in required:
            for kind in record["kinds"]:
                first, last = windows.get((record["symbol"], kind), (None, None))
                if first is None or last is None or month < first or month > last:
                    outside.append(month)
                    break
        record["n_required_study_months"] = len(required)
        record["n_required_months_outside_verified_window"] = len(outside)
        if outside:
            record["required_months_outside_verified_window"] = sorted(outside)

    included = sorted(a for a, r in per_asset.items() if r["included"])
    excluded = sorted(a for a, r in per_asset.items() if not r["included"])

    if plan_only:
        verdict = VERDICT_JOIN_MISMATCH
    elif excluded:
        verdict = VERDICT_HAS_UNSERVED
    else:
        verdict = VERDICT_ALL_SERVED

    roster_core = {
        "n_assets_planned": len(per_asset),
        "included_assets": included,
        "excluded_assets": excluded,
        "per_asset": per_asset,
        "verdict": verdict,
    }
    return {
        "join_check": {
            "ok": not plan_only and not probe_only,
            "n_plan_entries": len(plan_entries),
            "n_probe_entries": len(probe_entries),
            "n_plan_keys": len(plan_key_set),
            "n_probe_keys": len(probe_key_set),
            "n_plan_only": len(plan_only),
            "n_probe_only": len(probe_only),
        },
        "n_assets_planned": len(per_asset),
        "n_included": len(included),
        "n_excluded": len(excluded),
        "included_assets": included,
        "excluded_assets": excluded,
        "per_asset": per_asset,
        "verdict": verdict,
        "roster_canonical_sha256": _canonical_sha256(roster_core),
    }


def _class_counts(absent):
    counts = {}
    for a in absent:
        label = a.get("classification")
        counts[label] = counts.get(label, 0) + 1
    return counts


def _canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _feasibility_map(feas):
    per = feas.get("per_asset") or []
    if isinstance(per, dict):
        return per
    return {e.get("asset"): e for e in per if isinstance(e, dict)}


def build_audit(out_path=None):
    """Assemble the roster artifact. Writes only when ``out_path`` is given."""
    plan = _load_json(H41_PLAN)
    probe = _load_json(H43_PROBE)
    feas = _load_json(H40_FEAS)

    roster = build_roster(
        plan["plan_entries"], probe["per_entry"], _feasibility_map(feas)
    )

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": _utc_now(),
        "preregistration": PREREG.relative_to(ROOT).as_posix(),
        "method": (
            "Read-only roster over the H41 plan (920 entries) and the H43 probe "
            "(920 per_entry). Join on (symbol, kind, month); per (asset, kind) "
            "served window is [min, max] month with HTTP 200; every absent file "
            "is classified BEFORE_FIRST_SERVED / AFTER_LAST_SERVED / INTERIOR / "
            "ENTIRELY_ABSENT / ERROR / UNPROBED; each asset gets an "
            "inclusion/exclusion decision under the pre-declared rule. H40 "
            "required-study-month context annotates exposure only. No network, "
            "no downloads, no panels, no outcomes."
        ),
        "audited_inputs": {
            "h41_plan": H41_PLAN.relative_to(ROOT).as_posix(),
            "h43_probe": H43_PROBE.relative_to(ROOT).as_posix(),
            "h40_feasibility_context": H40_FEAS.relative_to(ROOT).as_posix(),
        },
        "join_check": roster["join_check"],
        "n_assets_planned": roster["n_assets_planned"],
        "n_included": roster["n_included"],
        "n_excluded": roster["n_excluded"],
        "included_assets": roster["included_assets"],
        "excluded_assets": roster["excluded_assets"],
        "per_asset": roster["per_asset"],
        "verdict": roster["verdict"],
        "verdict_rule": (
            "ROSTER_JOIN_MISMATCH if any plan key has no probe record; else "
            "ROSTER_HAS_UNSERVED_ASSETS if at least one asset is excluded "
            "(unprobed / probe error / AFTER_LAST_SERVED / INTERIOR / "
            "ENTIRELY_ABSENT gap); else ROSTER_ALL_ASSETS_FULLY_SERVED. "
            "BEFORE_FIRST_SERVED gaps are benign pre-listing absences and do "
            "not exclude an asset; the verified served window bounds it."
        ),
        "roster_canonical_sha256": roster["roster_canonical_sha256"],
        "exploratory_only": True,
        "promotion_allowed": False,
        "confirmatory_claim_allowed": False,
        "non_claims": [
            "No network access, no HEAD probe, no content downloaded.",
            "No panel constructed; no returns/spreads/states/p-values/costs/"
            "inference computed.",
            "Missing archive files are never fabricated; they remain absent.",
            "Does not re-probe the date-gated 2026-11 cutoff month.",
            "Does not alter the confirmatory expanding-universe arm or any "
            "frozen DISP-001/002/003 artifact, config, ledger or forward block.",
            "Cannot validate, replace or unlock H1/H6/H7/H10 or any "
            "confirmatory track.",
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
        description="Panel-coverage eligibility roster (H47, read-only)."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path (default: <experiment>/integrity_audit/"
        "panel_coverage_eligibility_roster_<computed_utc>.json).",
    )
    args = parser.parse_args(argv)

    audit = build_audit(None)
    if args.out:
        out_path = Path(args.out)
    else:
        stamp = audit["computed_utc"].replace("-", "").replace(":", "")
        out_path = AUDIT_DIR / f"panel_coverage_eligibility_roster_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": audit["verdict"],
                "n_included": audit["n_included"],
                "n_excluded": audit["n_excluded"],
                "out": str(out_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
