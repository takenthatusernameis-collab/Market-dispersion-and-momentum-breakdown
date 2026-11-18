#!/usr/bin/env python3
"""
Extension-Panel Normalization Plan — DISP-003 wave-A + wave-B into point-in-time aligned panel.

EXPLORATORY_ONLY — planning artifact; no panel bytes, no outcomes, no network.
Reads only committed H47/H49/H50/H41 evidence. Writes plan JSON under --out.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


# Pinned input paths and expected hashes (from preregistration)
H47_ROSTER_PATH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001/integrity_audit/panel_coverage_eligibility_roster_20261118T191152Z.json"
H47_ROSTER_SHA256 = "ac9b7cbf8d4ac22d0526017eff5b20ac659f9d0d3db3c41721c7a463a77d7a6e"

H49_AUDIT_PATH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001/integrity_audit/panel_wave_a_acquisition_20261118T211130Z.json"
H49_RECORDS_SHA256 = "37605fc803451c910014085d3903fcd1978df2afa4576f692e6b00b1b027cbf1"

H50_TRIM_PATH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001/integrity_audit/panel_wave_b_window_trim_20261118T221212Z.json"
H50_TRIM_SHA256 = "5aed05f1615a3cc2983c6e1be86ef9f35306aed7cfab86aea9f1d8fab9f61e66"

H41_PLAN_PATH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001/integrity_audit/H004V106_panel_acquisition_plan_20261116T085222Z.json"
H41_PLAN_SHA256 = "39e740b65fbe65541aa42f55b0e231469c49dda7e04d9e22e04eae3ac9ce441b"

DISP003_MANIFEST_PATH = "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_panel_manifest.json"

# Frozen DISP-003 hashes
FROZEN_HASHES = {
    "canonical_forward_block": "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "grid_v3_config": "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
    "h10_fresh_block": "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    "universe_frontier": "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
}

FROZEN_PATHS = {
    "canonical_forward_block": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json",
    "grid_v3_config": "configs/dispersion_momentum_grid_v3.json",
    "h10_fresh_block": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json",
    "universe_frontier": "research_state/universe_frontier.json",
}

STUDY_MONTHS = [f"{y:04d}-{m:02d}" for y in range(2023, 2027) for m in range(1, 13) if not (y == 2026 and m > 10)]

KLINES_HEADER = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
FUNDING_HEADER = ["calc_time", "funding_interval_hours", "last_funding_rate"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_hash(path: Path, expected: str, label: str) -> bool:
    actual = sha256_file(path)
    if actual != expected:
        print(f"HASH MISMATCH {label}: expected {expected}, got {actual}", file=sys.stderr)
        return False
    return True


def verify_frozen_hashes() -> dict[str, Any]:
    results = {}
    all_ok = True
    for name, expected in FROZEN_HASHES.items():
        path = Path(FROZEN_PATHS[name])
        actual = sha256_file(path) if path.exists() else "MISSING"
        match = actual == expected
        all_ok = all_ok and match
        results[name] = {"actual": actual, "expected": expected, "match": match, "path": str(path)}
    return {"all_match": all_ok, "details": results}


def build_plan() -> dict[str, Any]:
    # Load inputs
    h47 = load_json(Path(H47_ROSTER_PATH))
    h49 = load_json(Path(H49_AUDIT_PATH))
    h50 = load_json(Path(H50_TRIM_PATH))
    h41 = load_json(Path(H41_PLAN_PATH))
    disp003_manifest = load_json(Path(DISP003_MANIFEST_PATH))

    # Verify input hashes
    h47_ok = verify_hash(Path(H47_ROSTER_PATH), H47_ROSTER_SHA256, "H47 roster")
    h49_ok = verify_hash(Path(H49_AUDIT_PATH), H49_RECORDS_SHA256, "H49 audit")
    h50_ok = verify_hash(Path(H50_TRIM_PATH), H50_TRIM_SHA256, "H50 trim")
    h41_ok = verify_hash(Path(H41_PLAN_PATH), H41_PLAN_SHA256, "H41 plan")

    input_hashes = {
        "h47_roster": h47_ok,
        "h49_audit": h49_ok,
        "h50_trim": h50_ok,
        "h41_plan": h41_ok,
    }

    # Frozen hash verification
    frozen = verify_frozen_hashes()

    # Build extension asset list from H47 included assets
    included_assets = [a for a in h47["per_asset"].values() if a["included"]]
    asset_names = sorted([a["asset"] for a in included_assets])

    # Expected 9 assets
    expected_assets = ["alice", "ankr", "ape", "api3", "apt", "ar", "ark", "arpa", "astr"]
    if asset_names != expected_assets:
        return {
            "status": "PLAN_SCOPE_MISMATCH",
            "error": f"asset set mismatch: got {asset_names}, expected {expected_assets}",
            "input_hashes_verified": input_hashes,
            "frozen_hashes_verified": frozen,
        }

    # Build H49 records index for wave-A
    h49_records = {r["asset"]: {} for r in h49["records"]}
    for r in h49["records"]:
        key = (r["kind"], r["month"])
        h49_records[r["asset"]][key] = r

    # Build H41 plan index for wave-B (ark, astr)
    h41_entries = {}
    for e in h41.get("plan_entries", []):
        key = (e["asset"], e["kind"], e["month"])
        h41_entries[key] = e

    # Build H50 admissible months per asset
    h50_admissible = {}
    for a in h50["per_asset"].values():
        h50_admissible[a["asset"]] = set(a["admissible_study_months"])

    # Build series plan
    series = []
    total_planned_files = 0

    for asset_info in included_assets:
        asset = asset_info["asset"]
        symbol = asset_info["symbol"]
        served_window = asset_info["served_window"]

        for kind in ["klines", "funding"]:
            first_month = served_window[kind]["first"]
            last_month = served_window[kind]["last"]

            # Admissible months = intersection of served window with study months
            admissible = [m for m in STUDY_MONTHS if first_month <= m <= last_month]

            # For wave-B assets, cross-check with H50
            if asset in h50_admissible:
                h50_months = h50_admissible[asset]
                if set(admissible) != h50_months:
                    return {
                        "status": "PLAN_SCOPE_MISMATCH",
                        "error": f"admissible months mismatch for {asset} {kind}: H47-derived {admissible} vs H50 {sorted(h50_months)}",
                        "input_hashes_verified": input_hashes,
                        "frozen_hashes_verified": frozen,
                    }

            expected_header = KLINES_HEADER if kind == "klines" else FUNDING_HEADER
            provenance = "H49" if asset in ["alice", "ankr", "ape", "api3", "apt", "ar", "arpa"] else "H51-b"

            # Plan each monthly file
            monthly_files = []
            for month in admissible:
                if provenance == "H49":
                    # Look up H49 record
                    key = (kind, month)
                    if key not in h49_records[asset]:
                        return {
                            "status": "PLAN_SCOPE_MISMATCH",
                            "error": f"missing H49 record for {asset} {kind} {month}",
                            "input_hashes_verified": input_hashes,
                            "frozen_hashes_verified": frozen,
                        }
                    rec = h49_records[asset][key]
                    monthly_files.append({
                        "month": month,
                        "archive_url": rec["archive_url"],
                        "cache_path": rec["cache_path"],
                        "sha256": rec["sha256"],
                        "csv_header": rec["csv_header"],
                        "n_csv_rows": rec["n_csv_rows"],
                        "first_timestamp": rec["first_timestamp"],
                        "last_timestamp": rec["last_timestamp"],
                        "provenance": "H49",
                    })
                else:
                    # Wave-B: look up H41 plan entry
                    key = (asset, kind, month)
                    if key not in h41_entries:
                        return {
                            "status": "PLAN_SCOPE_MISMATCH",
                            "error": f"missing H41 plan entry for {asset} {kind} {month}",
                            "input_hashes_verified": input_hashes,
                            "frozen_hashes_verified": frozen,
                        }
                    plan_e = h41_entries[key]
                    monthly_files.append({
                        "month": month,
                        "archive_url": plan_e["archive_url"],
                        "archive_path": plan_e["archive_path"],
                        "sha256": None,  # to be filled by H51-b
                        "csv_header": expected_header,
                        "provenance": "H51-b",
                    })

            total_planned_files += len(monthly_files)

            series.append({
                "asset": asset,
                "symbol": symbol,
                "kind": kind,
                "admissible_months": admissible,
                "monthly_files": monthly_files,
                "provenance": provenance,
                "expected_header": expected_header,
            })

    # Verify total count
    if total_planned_files != 810:
        return {
            "status": "PLAN_SCOPE_MISMATCH",
            "error": f"total planned files {total_planned_files} != 810",
            "input_hashes_verified": input_hashes,
            "frozen_hashes_verified": frozen,
        }

    # Build extension manifest structure
    symbol_map = {s["asset"]: s["symbol"] for s in series}
    # Deduplicate symbol_map
    symbol_map = dict(sorted(symbol_map.items()))

    plan = {
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001",
        "hypothesis": "H51",
        "status": "PLAN_RECORDED",
        "computed_utc": None,  # filled at runtime
        "confirmatory_claim_allowed": False,
        "exploratory_only": True,
        "extension_assets": len(included_assets),
        "total_planned_files": total_planned_files,
        "series": series,
        "symbol_map": symbol_map,
        "frozen_hashes_verified": frozen,
        "input_hashes_verified": {
            "h47_roster": h47_ok,
            "h49_audit": h49_ok,
            "h50_trim": h50_ok,
            "h41_plan": h41_ok,
        },
        "non_claims": [
            "No panel constructed; no returns/spreads/states/p-values/costs/inference computed.",
            "No candidate promoted; no confirmatory or economic claim.",
            "Missing archive files are never fabricated; they remain absent.",
            "Wave-B acquisition (H51-b) remains a separate later step.",
            "Does not re-probe the date-gated 2026-11 cutoff month.",
            "Does not alter any frozen DISP-001/002/003 artifact, config, ledger or forward block.",
        ],
    }

    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Build DISP-003 extension panel normalization plan")
    parser.add_argument("--out", type=Path, help="Output JSON path (required to write)")
    parser.add_argument("--print", action="store_true", help="Print plan to stdout")
    args = parser.parse_args()

    if not args.out and not args.print:
        parser.error("At least one of --out or --print is required")

    plan = build_plan()

    # Add timestamp
    from datetime import datetime, timezone
    plan["computed_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Determine overall status
    input_ok = all(plan["input_hashes_verified"].values())
    frozen_ok = plan["frozen_hashes_verified"]["all_match"]
    if plan.get("status") == "PLAN_SCOPE_MISMATCH" or not input_ok or not frozen_ok:
        plan["status"] = "PLAN_SCOPE_MISMATCH"
        plan["confirmatory_claim_allowed"] = False

    if args.print:
        json.dump(plan, sys.stdout, indent=2)
        print()

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)

    return 0 if plan["status"] == "PLAN_RECORDED" else 1


if __name__ == "__main__":
    sys.exit(main())