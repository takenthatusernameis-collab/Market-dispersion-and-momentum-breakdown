#!/usr/bin/env python3
"""Panel-coverage acquisition queue (DISP-003-PANELCOV-QUEUE-001, H48).

Read-only, stdlib-only planning adjudication that turns the H47 eligibility
roster into a **bounded acquisition queue**: which included extension assets are
acquirable with no window trim (wave A), which need a separately preregistered
window trim first (wave B), how many planned archive files each wave needs, and
which of the 46 required study months each included asset can actually populate.

This is the natural successor to H47: H47 decided *which assets are admissible*;
this study decides *what a bounded acquisition may fetch, and what it would buy*.
It is EXPLORATORY_ONLY source-coverage/planning work: no network, no downloads,
no panels, no returns/spreads/states/p-values/costs/inference, no promotion, and
it does not re-probe the date-gated ``2026-11`` cutoff month.

Hard properties:
  * Missing files are never fabricated; absent months stay absent and are listed.
  * Every status is read from the committed H43 probe evidence.
  * Frozen artifacts are read-only (only read).
  * Import-safe: pure helpers importable without side effects or network.

Usage:
    python3 scripts/panel_coverage_acquisition_queue.py
    python3 scripts/panel_coverage_acquisition_queue.py --out <path>

Pure stdlib; no market data; no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELCOV_QUEUE_001_v1.md"

# Committed read-only inputs (H47 roster + H41 plan + H43 probe + H40 context).
H47_ROSTER = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001"
    / "integrity_audit"
    / "panel_coverage_eligibility_roster_20261118T191152Z.json"
)
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
AUDIT_ID = "H004V106_PANELCOV_QUEUE_001"
HYPOTHESIS = "H48"

# H47 roster canonical hash this study binds to (pinned, not re-derived).
H47_ROSTER_CANONICAL_SHA256 = (
    "171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579"
)

KINDS = ("klines", "funding")

# Pre-declared wave labels and queue verdicts (preregistration section 4).
WAVE_A = "WAVE_A_UNCONDITIONAL"
WAVE_B = "WAVE_B_REQUIRES_WINDOW_TRIM"
QUEUE_READY = "ACQUISITION_QUEUE_READY"
QUEUE_JOIN_MISMATCH = "QUEUE_JOIN_MISMATCH"
QUEUE_NO_UNCONDITIONAL_WAVE = "QUEUE_NO_UNCONDITIONAL_WAVE"


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


def classify_wave(symbol, required_months, status, kinds=KINDS):
    """Return (wave, absent_months, served_file_count) for one asset.

    A required month is absent when **either** required kind is not HTTP 200.
    Uses verified per-file probe evidence only; no window arithmetic.
    """
    absent = []
    served = 0
    for month in required_months:
        month_ok = True
        for kind in kinds:
            if status.get((symbol, kind, month)) == 200:
                served += 1
            else:
                month_ok = False
        if not month_ok:
            absent.append(month)
    wave = WAVE_A if not absent else WAVE_B
    return wave, absent, served


def build_queue(plan_entries, probe_entries, roster, study_months):
    """Pure acquisition-queue adjudication over committed evidence only."""
    study = sorted({m for m in study_months if m})
    study_set = set(study)
    status = probe_status_map(probe_entries)
    planned = planned_months_by_asset(plan_entries)

    included = sorted(roster.get("included_assets") or [])
    excluded = sorted(roster.get("excluded_assets") or [])
    per_asset_roster = roster.get("per_asset") or {}

    join_ok = bool(roster.get("join_check", {}).get("ok", False))
    waves = {}
    for asset in included:
        symbol = (per_asset_roster.get(asset) or {}).get("symbol") or planned.get(asset, (None, []))[0]
        if symbol is None or asset not in planned:
            join_ok = False
            continue
        required = [m for m in planned[asset][1] if m in study_set]
        wave, absent, served = classify_wave(symbol, required, status)
        waves[asset] = {
            "asset": asset,
            "symbol": symbol,
            "wave": wave,
            "n_required_months": len(required),
            "n_planned_files": 2 * len(required),
            "n_served_planned_files": served,
            "n_absent_planned_files": 2 * len(required) - served,
            "absent_required_months": absent,
        }

    wave_a = sorted(a for a, r in waves.items() if r["wave"] == WAVE_A)
    wave_b = sorted(a for a, r in waves.items() if r["wave"] == WAVE_B)

    def _sum(assets, key):
        return sum(waves[a][key] for a in assets)

    excluded_files = 0
    for asset in excluded:
        months = planned.get(asset, (None, []))[1]
        excluded_files += 2 * len([m for m in months if m in study_set])

    wave_counts = {
        "wave_a": {
            "assets": wave_a,
            "n_assets": len(wave_a),
            "planned_files": _sum(wave_a, "n_planned_files"),
            "served_files": _sum(wave_a, "n_served_planned_files"),
            "absent_files": _sum(wave_a, "n_absent_planned_files"),
        },
        "wave_b": {
            "assets": wave_b,
            "n_assets": len(wave_b),
            "planned_files": _sum(wave_b, "n_planned_files"),
            "served_files": _sum(wave_b, "n_served_planned_files"),
            "absent_files": _sum(wave_b, "n_absent_planned_files"),
        },
        "excluded": {
            "assets": excluded,
            "n_assets": len(excluded),
            "planned_files": excluded_files,
        },
    }

    # Per-study-month utility, wave A first then the wave B increment.
    wave_a_symbols = {a: waves[a]["symbol"] for a in wave_a}
    all_symbols = {a: waves[a]["symbol"] for a in waves}
    utility = []
    for month in study:
        wa = [a for a in wave_a if all(status.get((wave_a_symbols[a], k, month)) == 200 for k in KINDS)]
        inc = [a for a in all_symbols if all(status.get((all_symbols[a], k, month)) == 200 for k in KINDS)]
        utility.append(
            {
                "month": month,
                "n_wave_a": len(wa),
                "n_all_included": len(inc),
                "wave_a_assets": wa,
                "wave_b_assets": sorted(set(inc) - set(wa)),
            }
        )

    total_files = (
        wave_counts["wave_a"]["planned_files"]
        + wave_counts["wave_b"]["planned_files"]
        + wave_counts["excluded"]["planned_files"]
    )

    if not join_ok:
        verdict = QUEUE_JOIN_MISMATCH
    elif not wave_a:
        verdict = QUEUE_NO_UNCONDITIONAL_WAVE
    else:
        verdict = QUEUE_READY

    core = {
        "study_months": study,
        "waves": waves,
        "wave_file_counts": wave_counts,
        "monthly_utility": utility,
        "n_included_assets": len(included),
        "n_excluded_assets": len(excluded),
        "total_planned_files_reconciled": total_files,
    }
    return {
        "join_ok": join_ok,
        "verdict": verdict,
        "waves": waves,
        "included_assets": included,
        "excluded_assets": excluded,
        "wave_file_counts": wave_counts,
        "monthly_utility": utility,
        "n_study_months": len(study),
        "total_planned_files_reconciled": total_files,
        "total_possible_asset_months": len(all_symbols) * len(study),
        "served_asset_months": sum(u["n_all_included"] for u in utility),
        "queue_canonical_sha256": _canonical_sha256(core),
    }


def _canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path):
    with open(path) as f:
        return json.load(f)


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


def build_audit(out_path=None):
    """Assemble the acquisition-queue artifact. Writes only when ``out_path`` given."""
    roster = _load_json(H47_ROSTER)
    plan = _load_json(H41_PLAN)
    probe = _load_json(H43_PROBE)
    feas = _load_json(H40_FEAS)

    study_months = feas.get("study_months") or []
    queue = build_queue(plan["plan_entries"], probe["per_entry"], roster, study_months)

    frozen = frozen_hash_checks()
    roster_hash_ok = roster.get("roster_canonical_sha256") == H47_ROSTER_CANONICAL_SHA256

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": _utc_now(),
        "preregistration": PREREG.relative_to(ROOT).as_posix(),
        "method": (
            "Read-only queue over the committed H47 roster, H41 plan (920 "
            "entries), H43 probe (920 per_entry) and H40 study_months. For every "
            "H47-included asset, a required study month is absent when either "
            "required kind has no HTTP 200 probe record; assets with no absent "
            "required month form the unconditional acquisition wave A and assets "
            "with at least one absent required month form wave B (admissible only "
            "after a separately preregistered window trim). Per-study-month "
            "utility lists the included assets whose both kinds are verified "
            "served that month. No network, no downloads, no panels, no outcomes."
        ),
        "audited_inputs": {
            "h47_roster": H47_ROSTER.relative_to(ROOT).as_posix(),
            "h41_plan": H41_PLAN.relative_to(ROOT).as_posix(),
            "h43_probe": H43_PROBE.relative_to(ROOT).as_posix(),
            "h40_feasibility_context": H40_FEAS.relative_to(ROOT).as_posix(),
        },
        "audited_input_sha256": {
            "h47_roster": _file_sha256(H47_ROSTER),
            "h41_plan": _file_sha256(H41_PLAN),
            "h43_probe": _file_sha256(H43_PROBE),
            "h40_feasibility_context": _file_sha256(H40_FEAS),
        },
        "h47_roster_canonical_sha256": roster.get("roster_canonical_sha256"),
        "h47_roster_canonical_sha256_expected": H47_ROSTER_CANONICAL_SHA256,
        "h47_roster_binding_ok": roster_hash_ok,
        "frozen_hashes_verified": frozen,
        "all_frozen_hashes_match": all(v["match"] for v in frozen.values()),
        "join_ok": queue["join_ok"],
        "verdict": queue["verdict"],
        "verdict_rule": (
            "QUEUE_JOIN_MISMATCH if the H47 roster canonical hash does not match "
            "the pinned value, the H47 join was not clean, or an included asset "
            "has no H41 plan entries; else QUEUE_NO_UNCONDITIONAL_WAVE if wave A "
            "is empty; else ACQUISITION_QUEUE_READY."
        ),
        "n_study_months": queue["n_study_months"],
        "n_included_assets": len(queue["included_assets"]),
        "n_excluded_assets": len(queue["excluded_assets"]),
        "included_assets": queue["included_assets"],
        "excluded_assets": queue["excluded_assets"],
        "waves": queue["waves"],
        "wave_file_counts": queue["wave_file_counts"],
        "total_planned_files_reconciled": queue["total_planned_files_reconciled"],
        "total_possible_asset_months": queue["total_possible_asset_months"],
        "served_asset_months": queue["served_asset_months"],
        "monthly_utility": queue["monthly_utility"],
        "queue_canonical_sha256": queue["queue_canonical_sha256"],
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
        description="Panel-coverage acquisition queue (H48, read-only)."
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output path (default: <experiment>/integrity_audit/"
        "panel_coverage_acquisition_queue_<computed_utc>.json).",
    )
    args = parser.parse_args(argv)

    audit = build_audit(None)
    if args.out:
        out_path = Path(args.out)
    else:
        stamp = audit["computed_utc"].replace("-", "").replace(":", "")
        out_path = AUDIT_DIR / f"panel_coverage_acquisition_queue_{stamp}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": audit["verdict"],
                "wave_a_assets": audit["wave_file_counts"]["wave_a"]["assets"],
                "wave_b_assets": audit["wave_file_counts"]["wave_b"]["assets"],
                "total_planned_files_reconciled": audit["total_planned_files_reconciled"],
                "out": str(out_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
