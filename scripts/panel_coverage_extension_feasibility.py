#!/usr/bin/env python3
"""H004V106 committed-panel coverage extension feasibility study (H40, EXPLORATORY_ONLY).

DISP-003-PANELCOV-FEAS-001. Answers a prior planning question after H39: for the
188 H39 PIT-union assets without committed Binance kline/funding panels, do
committed free artifacts provide deterministic symbol mapping, verified Binance
USD-M perpetual existence, and Coin Metrics cap observations in the study window?
Quantifies the bounded monthly-archive scope implied by the study window. This is
measurement/planning only — no network access, no archive fetch, no panel
construction, no returns/spreads/states/p-values/costs/inference.

Read-only. Writes one diagnostic artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001/integrity_audit/.
Cannot validate, replace or unlock any confirmatory track.

Import-safe: pure helpers importable without side effects. CLI:
    python3 scripts/panel_coverage_extension_feasibility.py [--out <path>]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

H39_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json"
)
CANDIDATE_VALIDATION = ART / "data" / "panels" / "candidate_batch_validation.json"
RAW_CAP_DIR = ART / "data" / "raw" / "coinmetrics_candidates"
KLINE_INDEX = ART / "data" / "panels" / "binance_klines_BTCUSDT.csv"
RAW_KLINES_DIR = ART / "data" / "raw" / "binance" / "klines"
RAW_FUNDING_DIR = ART / "data" / "raw" / "binance" / "funding"
PANEL_DIR = ART / "data" / "panels"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
AUDIT_ID = "H004V106_PANELCOV_FEAS_001"
HYPOTHESIS = "H40"
STUDY_START = "2023-01-01"
STUDY_END = "2026-10-31"
SERIES_KINDS = ["klines", "funding"]

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
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_h39_missing(path: Path = H39_AUDIT) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assets = data.get("universe_assets_without_committed_kline_panel")
    if not isinstance(assets, list):
        raise ValueError("H39 audit missing universe_assets_without_committed_kline_panel list")
    return list(assets)


def load_candidate_index(path: Path = CANDIDATE_VALIDATION) -> dict[str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for rec in data.get("candidates_processed", []):
        if isinstance(rec, dict) and "asset" in rec:
            out[str(rec["asset"])] = rec
    return out


def load_study_dates(path: Path = KLINE_INDEX) -> list[str]:
    dates: set[str] = set()
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            ms = int(row["open_time"])
            d = datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            if STUDY_START <= d <= STUDY_END:
                dates.add(d)
    return sorted(dates)


def study_months(study_dates: list[str]) -> list[str]:
    return sorted({d[:7] for d in study_dates})


def load_cap_dates_in_window(asset: str, study_set: set[str], raw_dir: Path = RAW_CAP_DIR) -> list[str]:
    path = raw_dir / f"{asset}_CapMrktEstUSD.json"
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: set[str] = set()
    for row in rows:
        d = str(row.get("time", ""))[:10]
        raw = row.get("CapMrktEstUSD")
        if d in study_set and raw not in (None, ""):
            try:
                float(raw)
            except (TypeError, ValueError):
                continue
            out.add(d)
    return sorted(out)


def verify_frozen() -> dict:
    verified = {}
    for name, (path, expected) in FROZEN_EXPECTED.items():
        actual = sha256_file(path)
        verified[name] = {
            "path": str(path.relative_to(ROOT)),
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        }
    return verified


def decide_label(aggregate: dict) -> tuple[str, str]:
    n = aggregate["n_assets"]
    cond_a = (
        aggregate["n_in_candidate_validation"] == n
        and aggregate["n_binance_exists_true"] == n
        and aggregate["n_status_verified"] == n
        and aggregate["n_missing_symbol_mapping"] == 0
    )
    cond_b = aggregate["n_with_cap_obs_in_study_window"] == n
    cond_c = (
        aggregate["n_with_committed_raw_kline_dir"] == 0
        and aggregate["n_with_committed_raw_funding_dir"] == 0
        and aggregate["n_with_committed_kline_panel"] == 0
        and aggregate["n_with_committed_funding_panel"] == 0
    )
    cond_d = aggregate["n_missing_symbol_mapping"] == 0
    passed = cond_a and cond_b and cond_c and cond_d
    label = "PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE" if passed else "PANEL_EXTENSION_LIMITED"
    detail = (
        f"a_symbol_and_validation={cond_a},b_cap_obs={cond_b},"
        f"c_gap_unfilled={cond_c},d_symbol_mapping={cond_d}"
    )
    return label, detail


def build_audit(out_path: Path | None = None) -> dict:
    frozen = verify_frozen()
    all_frozen_ok = all(v["match"] for v in frozen.values())
    h39_sha = frozen["h39_rank_breadth_feasibility"]["actual"]

    missing = load_h39_missing()
    cand = load_candidate_index()
    study_dates = load_study_dates()
    study_set = set(study_dates)
    months = study_months(study_dates)

    per_asset = []
    for asset in sorted(missing):
        rec = cand.get(asset, {})
        binance = rec.get("binance") if isinstance(rec.get("binance"), dict) else {}
        symbol = binance.get("symbol")
        cap_dates = load_cap_dates_in_window(asset, study_set)
        sym_str = str(symbol) if symbol else None
        per_asset.append({
            "asset": asset,
            "symbol": sym_str,
            "in_candidate_validation": asset in cand,
            "binance_exists": bool(binance.get("exists")),
            "binance_error": binance.get("error"),
            "validation_status": rec.get("status"),
            "cap_obs_in_study_window": len(cap_dates),
            "cap_first_in_window": cap_dates[0] if cap_dates else None,
            "cap_last_in_window": cap_dates[-1] if cap_dates else None,
            "cap_coverage_frac": (len(cap_dates) / len(study_dates)) if study_dates else 0.0,
            "committed_raw_kline_dir": bool(sym_str and (RAW_KLINES_DIR / sym_str).is_dir()),
            "committed_raw_funding_dir": bool(sym_str and (RAW_FUNDING_DIR / sym_str).is_dir()),
            "committed_kline_panel": bool(sym_str and (PANEL_DIR / f"binance_klines_{sym_str}.csv").exists()),
            "committed_funding_panel": bool(sym_str and (PANEL_DIR / f"binance_funding_{sym_str}.csv").exists()),
            "required_study_months": months,
            "expected_zip_kinds": SERIES_KINDS,
            "expected_zip_files_upper_bound": len(months) * len(SERIES_KINDS),
        })

    n = len(per_asset)
    aggregate = {
        "n_assets": n,
        "n_in_candidate_validation": sum(1 for r in per_asset if r["in_candidate_validation"]),
        "n_binance_exists_true": sum(1 for r in per_asset if r["binance_exists"]),
        "n_status_verified": sum(1 for r in per_asset if r["validation_status"] == "verified"),
        "n_missing_symbol_mapping": sum(1 for r in per_asset if not r["symbol"]),
        "n_with_cap_obs_in_study_window": sum(1 for r in per_asset if r["cap_obs_in_study_window"] >= 1),
        "n_with_committed_raw_kline_dir": sum(1 for r in per_asset if r["committed_raw_kline_dir"]),
        "n_with_committed_raw_funding_dir": sum(1 for r in per_asset if r["committed_raw_funding_dir"]),
        "n_with_committed_kline_panel": sum(1 for r in per_asset if r["committed_kline_panel"]),
        "n_with_committed_funding_panel": sum(1 for r in per_asset if r["committed_funding_panel"]),
        "study_window": {"start": STUDY_START, "end": STUDY_END, "n_dates": len(study_dates)},
        "n_study_months": len(months),
        "study_month_first": months[0] if months else None,
        "study_month_last": months[-1] if months else None,
        "total_expected_zip_files_upper_bound_all_assets": n * len(months) * len(SERIES_KINDS),
    }
    label, detail = decide_label(aggregate)

    artifact = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "label": label,
        "decision": label,
        "decision_detail": detail,
        "computed_utc": now_utc(),
        "all_frozen_hashes_match": all_frozen_ok,
        "frozen_hashes_verified": frozen,
        "h39_input_sha256": h39_sha,
        "study_window": {"start": STUDY_START, "end": STUDY_END},
        "n_study_dates": len(study_dates),
        "study_months": months,
        "source_inputs": {
            "h39_audit": str(H39_AUDIT.relative_to(ROOT)),
            "candidate_batch_validation": str(CANDIDATE_VALIDATION.relative_to(ROOT)),
            "kline_date_index": str(KLINE_INDEX.relative_to(ROOT)),
            "raw_cap_dir": str(RAW_CAP_DIR.relative_to(ROOT)),
        },
        "aggregate": aggregate,
        "per_asset": per_asset,
        "question": (
            "Are committed metadata and PIT cap observations sufficient to plan a bounded "
            "Binance kline/funding panel-coverage extension for the 188 H39 union assets "
            "lacking committed panels?"
        ),
        "decision_rule": (
            "PANEL_EXTENSION_FEASIBLE_IN_PRINCIPLE iff all 188 have committed candidate "
            "validation with binance.exists==true & status==verified, cap_obs_in_study_window>=1, "
            "deterministic symbol mapping, and no committed raw/panel files (gap real/unfilled)."
        ),
        "interpretation": (
            "Descriptive/planning measurement only. No network fetch, no panel construction, "
            "no returns/spreads/states/p-values/costs/inference. Does not claim per-symbol "
            "monthly archive publication. EXPLORATORY_ONLY/INCONCLUSIVE for confirmation; "
            "cannot validate, replace, or unlock any confirmatory track."
        ),
        "note": (
            "Expected zip counts are upper bounds (months * kinds * assets) assuming full "
            "study-window publication; actual availability may be limited by listing/delisting "
            "or archive gaps and must be verified by keyless probes/downloads in a separate "
            "bounded data-acquisition step if pursued."
        ),
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if out_path is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = AUDIT_DIR / f"H004V106_panel_coverage_extension_feasibility_{ts}.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    artifact["_output_path"] = str(out_path)
    return artifact


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    a = build_audit(args.out)
    print(json.dumps({
        "audit_id": a["audit_id"],
        "label": a["label"],
        "decision_detail": a["decision_detail"],
        "all_frozen_hashes_match": a["all_frozen_hashes_match"],
        "n_assets": a["aggregate"]["n_assets"],
        "output": a["_output_path"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
