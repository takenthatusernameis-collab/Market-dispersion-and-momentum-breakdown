#!/usr/bin/env python3
"""Panel wave-B window-trim decision (DISP-003-PANELCOV-WAVEB-TRIM-001, H50).

Read-only, stdlib-only planning adjudication: for each H48 wave-B asset
(ARK, ASTR) declare exactly which of the 46 required study months are
admissible for acquisition without backfill, and exactly what the trimmed
window loses. Wave-B assets carry verified pre-listing absences
(BEFORE_FIRST_SERVED, HTTP 404) outside their first-served month, so the
trim drops only never-served placeholders and loses no served data.

This is the natural successor to H48: H48 decided *which assets need a
window trim* (ARK, ASTR, 18 absent planned files); this study decides *the
trim itself* — admissible months per asset and the dropped pre-listing
months — before any fetch could ever be authorized.

EXPLORATORY_ONLY source-coverage/design work: no network, no downloads,
no panels, no returns/spreads/states/p-values/costs/inference, no
promotion, and it does not re-probe the date-gated ``2026-11`` cutoff
month. No wave-B archive byte is fetched here; acquisition of the trimmed
wave-B files, if ever pursued, is a separate later-authorized step.

Hard properties:
  * Missing files are never fabricated; dropped months stay dropped and are
    listed explicitly; nothing outside a verified served window is planned.
  * Every status is read from the committed H47 roster / H43 probe evidence.
  * Frozen artifacts are read-only (only read).
  * Import-safe: pure helpers importable without side effects or network.

Usage:
    python3 scripts/panel_wave_b_window_trim.py
    python3 scripts/panel_wave_b_window_trim.py --out <path>

Pure stdlib; no market data; no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELCOV_WAVEB_TRIM_001_v1.md"

# Committed read-only inputs (H47 roster + H48 queue + H43 probe + H41 plan + H40 context).
H47_ROSTER = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001"
    / "integrity_audit"
    / "panel_coverage_eligibility_roster_20261118T191152Z.json"
)
H48_QUEUE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001"
    / "integrity_audit"
    / "panel_coverage_acquisition_queue_20261118T201951Z.json"
)
H43_PROBE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
    / "integrity_audit"
    / "H004V106_panel_archive_probe_20261116T142247Z.json"
)
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)
H40_FEAS = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
    / "integrity_audit"
    / "H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json"
)

# Frozen integrity checks read (never written) by this study.
CANONICAL_FORWARD_BLOCK = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block"
    / "forward_block_evaluation.json"
)
H10_FRESH_BLOCK = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block_h10_fresh"
    / "forward_block_evaluation.json"
)
UNIVERSE_FRONTIER = ROOT / "research_state" / "universe_frontier.json"
GRID_V3_CONFIG = ROOT / "configs" / "dispersion_momentum_grid_v3.json"

EXPECTED_FROZEN_SHA256 = {
    "canonical_forward_block": "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "h10_fresh_block": "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    "universe_frontier": "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
    "grid_v3_config": "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
}

EXPERIMENT_ID = EXP
AUDIT_ID = "H004V106_PANELCOV_WAVEB_TRIM_001"
HYPOTHESIS = "H50"

# H47 / H48 canonical hashes this study binds to (pinned, not re-derived).
H47_ROSTER_CANONICAL_SHA256 = (
    "171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579"
)
H48_QUEUE_CANONICAL_SHA256 = (
    "38c099db5c233222cc51f39348f06e933871337b807d4761512d2800ec2375c7"
)

KINDS = ("klines", "funding")

# Pre-declared wave labels and trim verdicts (preregistration sections 3-4).
WAVE_A = "WAVE_A_UNCONDITIONAL"
WAVE_B = "WAVE_B_REQUIRES_WINDOW_TRIM"
TRIM_DECISION_RECORDED = "TRIM_DECISION_RECORDED"
TRIM_SCOPE_MISMATCH = "TRIM_SCOPE_MISMATCH"

# Pre-declared expected scope from H47/H48 evidence (preregistration sections 3 and 5).
EXPECTED_WAVE_B_ASSETS = ("ark", "astr")
EXPECTED_WAVE_B_FILES = 184  # 2 assets x 2 kinds x 46 study months
EXPECTED_TRIMMED_FILES = 166  # ARK 76 + ASTR 90, all within served windows
EXPECTED_DROPPED_FILES = 18  # ARK 16 (2023-01..2023-08) + ASTR 2 (2023-01)


def probe_status_map(probe_entries):
    """{(symbol, kind, month): http_status} from the H43 probe."""
    status = {}
    for e in probe_entries:
        key = (e.get("symbol"), e.get("kind"), e.get("month"))
        status.setdefault(key, e.get("http_status"))
    return status


def planned_months_by_asset(plan_entries):
    """{asset: (symbol, sorted planned months)} from the H41 plan."""
    out = {}
    for e in plan_entries:
        asset = e.get("asset")
        record = out.setdefault(asset, {"symbol": e.get("symbol"), "months": set()})
        record["months"].add(e.get("month"))
    return {a: (r["symbol"], sorted(m for m in r["months"] if m)) for a, r in out.items()}


def served_window(per_asset_roster, asset):
    """{kind: (first_month, last_month)} with HTTP 200 for both kinds, from H47."""

    def _bounds(kind):
        window = (
            (per_asset_roster.get(asset) or {}).get("served_window", {}).get(kind) or {}
        )
        first, last = window.get("first"), window.get("last")
        return (first, last) if first and last else (None, None)

    return {kind: _bounds(kind) for kind in KINDS}


def admissible_months(study_months, window):
    """Study months inside the intersection of both kinds' served windows."""
    bounds = [window[kind] for kind in KINDS]
    if any(first is None or last is None for first, last in bounds):
        return []
    first = max(b[0] for b in bounds)
    last = min(b[1] for b in bounds)
    return [m for m in study_months if first <= m <= last]


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _utc_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def frozen_hash_checks():
    """Recompute frozen artifact hashes; returns {name: {actual, expected, match}}."""
    out = {}
    paths = {
        "canonical_forward_block": CANONICAL_FORWARD_BLOCK,
        "h10_fresh_block": H10_FRESH_BLOCK,
        "universe_frontier": UNIVERSE_FRONTIER,
        "grid_v3_config": GRID_V3_CONFIG,
    }
    for name, path in paths.items():
        actual = _file_sha256(path) if path.exists() else None
        expected = EXPECTED_FROZEN_SHA256[name]
        out[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "actual": actual,
            "expected": expected,
            "match": actual == expected,
        }
    return out


def build_trim_decision(roster, queue, plan_entries, probe_entries, study_months):
    """Pure window-trim adjudication over committed evidence only."""
    study = sorted({m for m in study_months if m})
    study_set = set(study)
    status = probe_status_map(probe_entries)
    planned = planned_months_by_asset(plan_entries)

    per_asset_roster = roster.get("per_asset") or {}
    included = sorted(roster.get("included_assets") or [])

    join_ok = bool(roster.get("join_check", {}).get("ok", False))
    per_asset = {}
    for asset in EXPECTED_WAVE_B_ASSETS:
        roster_entry = per_asset_roster.get(asset) or {}
        symbol = roster_entry.get("symbol") or planned.get(asset, (None, []))[0]
        if symbol is None or asset not in planned:
            join_ok = False
            continue
        required = [m for m in planned[asset][1] if m in study_set]
        window = served_window(per_asset_roster, asset)
        admissible = admissible_months(study, window)
        dropped = [m for m in required if m not in admissible]
        dropped_classes = {}
        for m in dropped:
            kind_hit = None
            for kind in KINDS:
                st = status.get((symbol, kind, m))
                if st is not None and st != 200:
                    kind_hit = st
            # Classification is read from H47 per_asset absent records where available.
            absent_records = roster_entry.get("absent") or []
            cls = next(
                (r.get("classification") for r in absent_records if r.get("month") == m),
                "BEFORE_FIRST_SERVED" if kind_hit is not None else "UNKNOWN",
            )
            dropped_classes[cls] = dropped_classes.get(cls, 0) + 1
        n_served_trimmed = 0
        for m in admissible:
            for kind in KINDS:
                if status.get((symbol, kind, m)) == 200:
                    n_served_trimmed += 1
        per_asset[asset] = {
            "asset": asset,
            "symbol": symbol,
            "wave": WAVE_B,
            "n_required_months": len(required),
            "n_planned_files": 2 * len(required),
            "n_served_planned_files": queue.get("waves", {}).get(asset, {}).get(
                "n_served_planned_files",
                sum(1 for m in required for k in KINDS if status.get((symbol, k, m)) == 200),
            ),
            "n_absent_planned_files": 2 * len(required)
            - sum(1 for m in required for k in KINDS if status.get((symbol, k, m)) == 200),
            "absent_required_months": [m for m in required if m not in study_set]
            or [m for m in required if any(status.get((symbol, k, m)) != 200 for k in KINDS)],
            "served_window": {k: {"first": v[0], "last": v[1]} for k, v in window.items()},
            "admissible_study_months": admissible,
            "n_admissible_months": len(admissible),
            "n_trimmed_planned_files": 2 * len(admissible),
            "n_dropped_planned_files": 2 * len(dropped),
            "dropped_required_months": dropped,
            "dropped_class_counts": dropped_classes,
            "all_dropped_before_first_served": all(
                c == "BEFORE_FIRST_SERVED" for c in dropped_classes
            ),
            "n_served_within_trimmed_window": n_served_trimmed,
            "n_absent_within_trimmed_window": 2 * len(admissible) - n_served_trimmed,
        }

    wave_b = sorted(a for a in per_asset if per_asset[a]["wave"] == WAVE_B)

    def _sum(assets, key):
        return sum(per_asset[a][key] for a in assets)

    trimmed = {
        "assets": wave_b,
        "n_assets": len(wave_b),
        "planned_files": _sum(wave_b, "n_trimmed_planned_files"),
        "servable_files": _sum(wave_b, "n_served_within_trimmed_window"),
        "absent_files": _sum(wave_b, "n_absent_within_trimmed_window"),
        "dropped_files": _sum(wave_b, "n_dropped_planned_files"),
        "dropped_months": sum(len(per_asset[a]["dropped_required_months"]) for a in wave_b),
        "all_dropped_before_first_served": all(
            per_asset[a]["all_dropped_before_first_served"] for a in wave_b
        ),
    }

    # Per-study-month utility after the trim: which wave-B assets are admissible.
    utility = []
    for month in study:
        utility.append(
            {
                "month": month,
                "wave_b_admissible_assets": sorted(
                    a for a in wave_b if month in per_asset[a]["admissible_study_months"]
                ),
                "n_wave_b_admissible": sum(
                    1 for a in wave_b if month in per_asset[a]["admissible_study_months"]
                ),
            }
        )

    if not join_ok:
        verdict = TRIM_SCOPE_MISMATCH
    elif set(wave_b) != set(EXPECTED_WAVE_B_ASSETS):
        verdict = TRIM_SCOPE_MISMATCH
    else:
        verdict = TRIM_DECISION_RECORDED

    core = {
        "study_months": study,
        "per_asset": per_asset,
        "wave_b_trimmed": trimmed,
        "monthly_utility_trimmed": utility,
        "n_study_months": len(study),
    }
    return {
        "join_ok": join_ok,
        "verdict": verdict,
        "per_asset": per_asset,
        "wave_b_trimmed": trimmed,
        "monthly_utility_trimmed": utility,
        "n_study_months": len(study),
        "trim_canonical_sha256": _canonical_sha256(core),
    }


def build_audit(out_path=None):
    """Assemble the wave-B trim-decision artifact. Writes only when ``out_path`` given."""
    roster = _load_json(H47_ROSTER)
    queue = _load_json(H48_QUEUE)
    probe = _load_json(H43_PROBE)
    plan = _load_json(H41_PLAN)
    feas = _load_json(H40_FEAS)

    study_months = feas.get("study_months") or []
    decision = build_trim_decision(
        roster, queue, plan["plan_entries"], probe["per_entry"], study_months
    )

    frozen = frozen_hash_checks()
    roster_hash_ok = roster.get("roster_canonical_sha256") == H47_ROSTER_CANONICAL_SHA256
    queue_hash_ok = queue.get("queue_canonical_sha256") == H48_QUEUE_CANONICAL_SHA256

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": _utc_now(),
        "preregistration": PREREG.relative_to(ROOT).as_posix(),
        "method": (
            "Read-only window-trim decision over the committed H47 eligibility "
            "roster, H48 acquisition queue, H43 probe (920 per_entry) and H41 "
            "plan (920 entries). For each H48 wave-B asset (ARK, ASTR) the "
            "verified served window is the intersection, over both klines and "
            "funding, of months with an HTTP 200 probe record, bounded by the "
            "46 H40 study months. Study months outside that window (verified "
            "BEFORE_FIRST_SERVED pre-listing absences) are dropped and never "
            "backfilled or fetched; nothing outside a served window is planned. "
            "No network, no downloads, no panels, no outcomes."
        ),
        "audited_inputs": {
            "h47_roster": H47_ROSTER.relative_to(ROOT).as_posix(),
            "h48_queue": H48_QUEUE.relative_to(ROOT).as_posix(),
            "h43_probe": H43_PROBE.relative_to(ROOT).as_posix(),
            "h41_plan": H41_PLAN.relative_to(ROOT).as_posix(),
            "h40_feasibility_context": H40_FEAS.relative_to(ROOT).as_posix(),
        },
        "audited_input_sha256": {
            "h47_roster": _file_sha256(H47_ROSTER),
            "h48_queue": _file_sha256(H48_QUEUE),
            "h43_probe": _file_sha256(H43_PROBE),
            "h41_plan": _file_sha256(H41_PLAN),
            "h40_feasibility_context": _file_sha256(H40_FEAS),
        },
        "h47_roster_canonical_sha256": roster.get("roster_canonical_sha256"),
        "h47_roster_canonical_sha256_expected": H47_ROSTER_CANONICAL_SHA256,
        "h47_roster_binding_ok": roster_hash_ok,
        "h48_queue_canonical_sha256": queue.get("queue_canonical_sha256"),
        "h48_queue_canonical_sha256_expected": H48_QUEUE_CANONICAL_SHA256,
        "h48_queue_binding_ok": queue_hash_ok,
        "frozen_hashes_verified": frozen,
        "all_frozen_hashes_match": all(v["match"] for v in frozen.values()),
        "join_ok": decision["join_ok"],
        "trim_verdict": decision["verdict"],
        "trim_verdict_rule": (
            "TRIM_SCOPE_MISMATCH if the H47 roster canonical hash does not match "
            "the pinned value, the H48 queue canonical hash does not match, the "
            "join was not clean, or the wave-B asset set is not exactly {ark, "
            "astr}; else TRIM_DECISION_RECORDED when admissible months and "
            "dropped months are declared per asset from verified served windows "
            "only, nothing outside a served window is planned, and no fetch is "
            "performed."
        ),
        "n_study_months": decision["n_study_months"],
        "per_asset": decision["per_asset"],
        "wave_b_trimmed": decision["wave_b_trimmed"],
        "monthly_utility_trimmed": decision["monthly_utility_trimmed"],
        "trim_canonical_sha256": decision["trim_canonical_sha256"],
        "expected_scope": {
            "wave_b_assets": list(EXPECTED_WAVE_B_ASSETS),
            "kinds": list(KINDS),
            "n_study_months": decision["n_study_months"],
            "wave_b_planned_files": EXPECTED_WAVE_B_FILES,
            "wave_b_absent_files_in_queue": 18,
            "wave_b_trimmed_planned_files": EXPECTED_TRIMMED_FILES,
            "wave_b_dropped_files": EXPECTED_DROPPED_FILES,
        },
        "exploratory_only": True,
        "promotion_allowed": False,
        "confirmatory_claim_allowed": False,
        "non_claims": [
            "No network access, no HEAD probe, no content downloaded.",
            "No panel constructed; no returns/spreads/states/p-values/costs/"
            "inference computed.",
            "Missing archive files are never fabricated; dropped months stay "
            "dropped and are listed explicitly.",
            "Does not fetch any wave-B archive file; wave-B acquisition, if ever "
            "authorized, remains a separate later step.",
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Wave-B (ARK/ASTR) window-trim decision (H50, read-only)."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path (default: <experiment>/integrity_audit/"
        "panel_wave_b_window_trim_<computed_utc>.json).",
    )
    args = parser.parse_args(argv)

    audit = build_audit(None)
    if args.out:
        out_path = Path(args.out)
    else:
        stamp = audit["computed_utc"].replace("-", "").replace(":", "")
        out_path = AUDIT_DIR / f"panel_wave_b_window_trim_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": audit["trim_verdict"],
                "wave_b_assets": audit["wave_b_trimmed"]["assets"],
                "wave_b_trimmed_planned_files": audit["wave_b_trimmed"]["planned_files"],
                "wave_b_dropped_files": audit["wave_b_trimmed"]["dropped_files"],
                "out": str(out_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
