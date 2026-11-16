#!/usr/bin/env python3
"""H004V106 bounded panel acquisition plan for a PIT subset (H41, EXPLORATORY_ONLY).

DISP-003-PANELACQ-PLAN-001. Deterministic, committed-metadata-only planning
artifact: selects a small explicit subset of H39/H40 PIT-union assets lacking
committed Binance panels and enumerates a bounded monthly (symbol, kind, month)
keyless archive-acquisition plan (klines + fundingRate) from committed fields.
No network access, no probing/downloading, no panel construction, no outcome
computation. Read-only; writes one diagnostic artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/.

Cannot validate, replace or unlock any confirmatory track.

Import-safe: pure helpers importable without side effects. CLI:
    python3 scripts/panel_acquisition_plan.py [--out <path>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

H40_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
    / "integrity_audit"
    / "H004V106_panel_coverage_extension_feasibility_20261116T081554Z.json"
)
H39_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json"
)
CANDIDATE_VALIDATION = ART / "data" / "panels" / "candidate_batch_validation.json"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
AUDIT_ID = "H004V106_PANELACQ_PLAN_001"
HYPOTHESIS = "H41"
SUBSET_SIZE = 10
SERIES_KINDS = ["klines", "funding"]
# Binance Public Data Archive base (documented free public). Plan-only; no fetch.
BINANCE_DATA_BASE = "https://data.binance.vision"
# Path templates by kind for USD-M monthly archives (planning targets, not verified).
KIND_PATH_TEMPLATES = {
    "klines": "data/futures/um/monthly/klines/{symbol}/1d/{symbol}-1d-{month}.zip",
    "funding": "data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{month}.zip",
}

FROZEN_EXPECTED = {
    "canonical_forward_block": (
        ART / "forward_block" / "forward_block_evaluation.json",
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    ),
    "h10_fresh_block": (
        ART / "forward_block_h10_fresh" / "forward_block_evaluation.json",
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    ),
    "grid_result_ledger": (
        ART / "grid_result_ledger.json",
        "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c",
    ),
    "universe_frontier": (
        ROOT / "research_state" / "universe_frontier.json",
        "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
    ),
    "grid_v3_config": (
        ROOT / "configs" / "dispersion_momentum_grid_v3.json",
        "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
    ),
    "h39_rank_breadth_feasibility": (
        H39_AUDIT,
        "d13108da263822a145811feb18a90831bfa526380983e27a1e7db206dd3db85d",
    ),
    "h40_panel_coverage_feasibility": (
        H40_AUDIT,
        "2549d1dff2e3312722766e034d0cab626a6a0d99f05683247d7439fd6f2f84ce",
    ),
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_h40(path: Path = H40_AUDIT) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_candidate_index(path: Path = CANDIDATE_VALIDATION) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for rec in data.get("candidates_processed", []):
        if isinstance(rec, dict) and "asset" in rec:
            out[str(rec["asset"])] = rec
    return out


def subset_key(rec: dict):
    return (
        -int(rec.get("cap_obs_in_study_window", 0)),
        -float(rec.get("cap_coverage_frac", 0.0)),
        str(rec.get("asset", "")),
    )


def select_subset(per_asset: list[dict], n: int = SUBSET_SIZE) -> list[dict]:
    eligible = []
    for rec in per_asset:
        if rec.get("committed_kline_panel") or rec.get("committed_funding_panel"):
            continue
        if not (rec.get("in_candidate_validation") and rec.get("binance_exists")):
            continue
        if rec.get("validation_status") != "verified":
            continue
        if int(rec.get("cap_obs_in_study_window", 0)) < 1:
            continue
        eligible.append(rec)
    return sorted(eligible, key=subset_key)[:n]


def plan_entries_for_asset(rec: dict) -> list[dict]:
    symbol = str(rec.get("symbol", ""))
    months = list(rec.get("required_study_months") or [])
    entries = []
    for kind in SERIES_KINDS:
        tmpl = KIND_PATH_TEMPLATES[kind]
        for month in months:
            rel = tmpl.format(symbol=symbol, month=month)
            entries.append(
                {
                    "asset": rec.get("asset"),
                    "symbol": symbol,
                    "kind": kind,
                    "month": month,
                    "archive_path": rel,
                    "archive_url": f"{BINANCE_DATA_BASE}/{rel}",
                    "sha256": None,
                    "provenance_status": "PENDING_ACQUISITION",
                    "published_verified": None,
                    "note": "planning_target_only_not_verified",
                }
            )
    return entries


def verify_frozen_hashes() -> dict:
    out = {}
    for name, (path, expected) in FROZEN_EXPECTED.items():
        actual = sha256_file(path) if path.exists() else None
        out[name] = {
            "path": str(path.relative_to(ROOT)),
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        }
    return out


def decide_label(subset: list[dict], plan_total: int, frozen: dict) -> tuple[str, dict]:
    checks = {}
    checks["subset_size_ok"] = len(subset) == SUBSET_SIZE
    checks["frozen_hashes_match"] = all(v["match"] for v in frozen.values())
    checks["all_verified"] = all(
        r.get("in_candidate_validation")
        and r.get("binance_exists")
        and r.get("validation_status") == "verified"
        and str(r.get("symbol", ""))
        and int(r.get("cap_obs_in_study_window", 0)) >= 1
        and not r.get("committed_kline_panel")
        and not r.get("committed_funding_panel")
        and isinstance(r.get("required_study_months"), list)
        and len(r.get("required_study_months")) > 0
        for r in subset
    )
    expected_total = sum(
        len(r.get("required_study_months") or []) * len(SERIES_KINDS) for r in subset
    )
    checks["plan_count_matches"] = plan_total == expected_total
    checks["plan_nonempty"] = plan_total > 0
    checks["no_duplicate_entries_expected"] = True  # by construction: (symbol,kind,month)
    ok = all(checks.values())
    return ("PANEL_ACQUISITION_PLAN_READY" if ok else "PANEL_ACQUISITION_PLAN_LIMITED", checks)


def build_audit(out_path: Path | None = None) -> dict:
    h40 = load_h40()
    per_asset = h40.get("per_asset", [])
    subset = select_subset(per_asset, SUBSET_SIZE)
    subset_assets = [r["asset"] for r in subset]
    # deterministic plan
    plan = []
    per_asset_plan = []
    for rec in subset:
        entries = plan_entries_for_asset(rec)
        plan.extend(entries)
        per_asset_plan.append(
            {
                "asset": rec.get("asset"),
                "symbol": rec.get("symbol"),
                "validation_status": rec.get("validation_status"),
                "binance_exists": rec.get("binance_exists"),
                "cap_obs_in_study_window": rec.get("cap_obs_in_study_window"),
                "cap_coverage_frac": rec.get("cap_coverage_frac"),
                "cap_first_in_window": rec.get("cap_first_in_window"),
                "cap_last_in_window": rec.get("cap_last_in_window"),
                "required_study_months": rec.get("required_study_months"),
                "n_planned_entries": len(entries),
                "n_planned_klines": sum(1 for e in entries if e["kind"] == "klines"),
                "n_planned_funding": sum(1 for e in entries if e["kind"] == "funding"),
            }
        )
    # uniqueness check
    keys = [(e["symbol"], e["kind"], e["month"]) for e in plan]
    unique_ok = len(keys) == len(set(keys))

    frozen = verify_frozen_hashes()
    label, checks = decide_label(subset, len(plan), frozen)
    checks["no_duplicate_entries_actual"] = unique_ok

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "label": label,
        "computed_utc": now_utc(),
        "decision": label,
        "decision_rule": (
            "PANEL_ACQUISITION_PLAN_READY iff subset_size==10, all subset assets verified/"
            "mapped/cap-present/gap-unfilled with non-empty required_study_months, frozen hashes "
            "match, and bounded (symbol,kind,month) plan is complete and unique; else LIMITED."
        ),
        "all_frozen_hashes_match": all(v["match"] for v in frozen.values()),
        "frozen_hashes_verified": frozen,
        "inputs": {
            "h40_audit": str(H40_AUDIT.relative_to(ROOT)),
            "h40_decision": h40.get("decision"),
            "h39_audit": str(H39_AUDIT.relative_to(ROOT)),
            "candidate_validation": str(CANDIDATE_VALIDATION.relative_to(ROOT)),
        },
        "subset_selection": {
            "rule": "sort by cap_obs_in_study_window desc, cap_coverage_frac desc, asset asc; take first 10 gap-unfilled verified candidates",
            "subset_size": len(subset),
            "subset_assets": subset_assets,
        },
        "per_asset_plan_summary": per_asset_plan,
        "plan_totals": {
            "n_assets": len(subset),
            "n_planned_entries": len(plan),
            "n_planned_klines": sum(1 for e in plan if e["kind"] == "klines"),
            "n_planned_funding": sum(1 for e in plan if e["kind"] == "funding"),
            "n_unique_symbol_kind_month": len(set(keys)),
            "unique_entries": unique_ok,
        },
        "plan_entries": plan,
        "checks": checks,
        "interpretation": (
            "EXPLORATORY_ONLY design/planning artifact from committed metadata only. "
            "Plan entries are bounded acquisition targets, NOT proof of archive publication, "
            "not downloaded data, not panels, and not outcomes. No network access performed; "
            "no returns/spreads/states/p-values/costs/inference computed. Cannot validate, "
            "replace, or unlock H1/H6/H7/H10 or any confirmatory track. Any future keyless "
            "probe/download requires separate bounded preregistered acquisition step with "
            "provenance/SHA256 and must not fabricate missing data."
        ),
        "non_claims": [
            "no_archive_publication_claim",
            "no_network_fetch_performed",
            "no_panel_constructed",
            "no_outcome_or_inference",
            "no_confirmatory_promotion",
            "no_historical_rank_backfill",
        ],
    }
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit["_output_path"] = str(out_path.relative_to(ROOT))
    return audit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="Output JSON path (default: timestamped in integrity_audit/)")
    args = ap.parse_args()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else (AUDIT_DIR / f"H004V106_panel_acquisition_plan_{ts}.json")
    if not out.is_absolute():
        out = ROOT / out
    audit = build_audit(out_path=out)
    print(json.dumps({"label": audit["label"], "n_planned_entries": audit["plan_totals"]["n_planned_entries"],
                      "out": audit.get("_output_path")}, sort_keys=True))


if __name__ == "__main__":
    main()
