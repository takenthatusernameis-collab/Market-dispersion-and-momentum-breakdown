#!/usr/bin/env python3
"""H004V106 Expanding Universe Eligibility Coverage Audit.

DISP-003-EXP-ELIG-001 (H33, EXPLORATORY_ONLY). Independently reconstructs the
point-in-time expanding universe eligibility map from committed raw panels and
compares it to the grid ledger's recorded eligible_assets_per_date summaries.

Read-only. Writes a diagnostic artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
PANEL_DIR = ART / "data" / "panels"
LEDGER_PATH = ART / "grid_result_ledger.json"
SUMMARY_PATH = ART / "grid_summary.json"
AUDIT_DIR = ART / "integrity_audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

LEGACY_ASSETS = [
    "btc", "eth", "sol", "bnb", "xrp", "ada", "doge", "dot", "matic", "avax",
    "link", "uni", "ltc", "bch", "etc", "xlm", "atom", "algo", "vet", "fil",
    "trx", "eos", "neo", "iost", "qtum", "zec", "dash", "rune",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_marketcap() -> pd.DataFrame:
    p = PANEL_DIR / "marketcap_panel.csv"
    df = pd.read_csv(p, dtype={"CapMrktCurUSD": str, "CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    return df[["date", "asset", "CapMrktEstUSD"]].dropna(subset=["CapMrktEstUSD"])


def load_binance_panel(kind: str) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for p in sorted(PANEL_DIR.glob(f"binance_{kind}_*.csv")):
        symbol = p.stem.replace(f"binance_{kind}_", "")
        df = pd.read_csv(p)
        if kind == "klines":
            df = df.rename(columns={"open_time": "ts"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            out[symbol] = df[["date", "close"]].copy()
        else:
            df = df.rename(columns={"calc_time": "ts", "last_funding_rate": "funding_rate"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
            out[symbol] = df[["date", "funding_rate"]].copy()
    return out


def build_eligibility_map(mc: pd.DataFrame, px: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Returns {date: {asset: cap}} for eligible assets at each date (expanding arm)."""
    asset_to_symbol: dict[str, str] = {}
    for symbol in px:
        if symbol.endswith("USDT"):
            asset = symbol[:-4].lower()
            asset_to_symbol[asset] = symbol

    allowed = set(asset_to_symbol.keys())

    px_dates: dict[str, set[str]] = {}
    for symbol, df_px in px.items():
        px_dates[symbol] = set(df_px["date"].astype(str).str.slice(0, 10).unique())

    mc_dates = sorted(mc["date"].unique())
    result: dict[str, dict] = {}
    for d in mc_dates:
        mc_d = mc[mc["date"] == d][["asset", "CapMrktEstUSD"]].dropna()
        elig: dict[str, float] = {}
        for _, r in mc_d.iterrows():
            asset = r["asset"]
            if asset not in allowed:
                continue
            symbol = asset_to_symbol.get(asset)
            if symbol is None:
                continue
            if d not in px_dates.get(symbol, set()):
                continue
            cap = float(r["CapMrktEstUSD"])
            if math.isnan(cap):
                continue
            elig[asset] = cap
        if elig:
            result[d] = elig
    return result


def compute_lifecycle(px: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Returns {asset: {listing_date, delisting_date}} from price panel."""
    lifecycle = {}
    for symbol, df in px.items():
        if not symbol.endswith("USDT"):
            continue
        asset = symbol[:-4].lower()
        dates = sorted(df["date"].astype(str).str.slice(0, 10).unique())
        if dates:
            lifecycle[asset] = {"listing_date": dates[0], "delisting_date": dates[-1]}
    return lifecycle


def main() -> int:
    print("[audit] Loading committed panels...", flush=True)
    mc = load_marketcap()
    px = load_binance_panel("klines")
    fd = load_binance_panel("funding")  # not used for eligibility, but loaded for completeness

    print(f"[audit] Marketcap: {len(mc)} rows, {mc['date'].nunique()} dates, {mc['asset'].nunique()} assets", flush=True)
    print(f"[audit] Kline symbols: {len(px)}", flush=True)
    print(f"[audit] Funding symbols: {len(fd)}", flush=True)

    print("[audit] Building eligibility map...", flush=True)
    elig_map = build_eligibility_map(mc, px)
    lifecycle = compute_lifecycle(px)

    print(f"[audit] Eligible dates: {len(elig_map)}", flush=True)

    # Per-date detail
    per_date = []
    all_eligible_assets = set()
    listing_events = []
    delisting_events = []
    exclusion_counts = {"no_market_cap_observation": 0, "no_perpetual_contract": 0,
                        "not_yet_listed": 0, "delisted": 0}

    for d in sorted(elig_map.keys()):
        elig = elig_map[d]
        # Rank by CapMrktEstUSD desc, tie asset asc
        ranked = sorted(elig.items(), key=lambda x: (-x[1], x[0]))
        assets_with_ranks = [{"asset": a, "rank": i + 1, "cap": c} for i, (a, c) in enumerate(ranked)]
        all_eligible_assets.update(elig.keys())

        # Lifecycle events on this date
        for asset, lc in lifecycle.items():
            if lc["listing_date"] == d:
                listing_events.append({"date": d, "asset": asset, "symbol": asset.upper() + "USDT"})
            if lc["delisting_date"] == d:
                delisting_events.append({"date": d, "asset": asset, "symbol": asset.upper() + "USDT"})

        # Exclusion counts for this date (assets in marketcap but not eligible)
        mc_assets_d = set(mc[mc["date"] == d]["asset"])
        asset_to_symbol = {s[:-4].lower(): s for s in px if s.endswith("USDT")}
        px_dates = {s: set(df["date"].astype(str).str.slice(0, 10).unique()) for s, df in px.items()}
        for asset in mc_assets_d:
            if asset in elig:
                continue
            if asset not in asset_to_symbol:
                exclusion_counts["no_perpetual_contract"] += 1
            elif d not in px_dates.get(asset_to_symbol[asset], set()):
                if d < lifecycle.get(asset, {}).get("listing_date", ""):
                    exclusion_counts["not_yet_listed"] += 1
                else:
                    exclusion_counts["delisted"] += 1
            else:
                exclusion_counts["no_market_cap_observation"] += 1

        per_date.append({
            "date": d,
            "eligible_count": len(elig),
            "assets": assets_with_ranks,
            "exclusion_counts": {k: v for k, v in exclusion_counts.items()},  # cumulative snapshot
        })

    # Aggregate statistics
    eligible_counts = [d["eligible_count"] for d in per_date]
    if eligible_counts:
        eligible_stats = {
            "mean": sum(eligible_counts) / len(eligible_counts),
            "min": min(eligible_counts),
            "max": max(eligible_counts),
            "median": sorted(eligible_counts)[len(eligible_counts) // 2],
            "n_dates": len(eligible_counts),
        }
    else:
        eligible_stats = {"mean": 0, "min": 0, "max": 0, "median": 0, "n_dates": 0}

    # Rank distribution across all eligible (date, asset) pairs
    all_ranks = []
    for d in per_date:
        all_ranks.extend([a["rank"] for a in d["assets"]])
    rank_dist = {}
    if all_ranks:
        for pct in [10, 25, 50, 75, 90, 95, 99]:
            idx = int(len(all_ranks) * pct / 100)
            rank_dist[f"p{pct}"] = sorted(all_ranks)[min(idx, len(all_ranks) - 1)]
        rank_dist["mean"] = sum(all_ranks) / len(all_ranks)
        rank_dist["max"] = max(all_ranks)

    # Load ledger for comparison
    print("[audit] Loading grid ledger for comparison...", flush=True)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    ledger_cells = ledger.get("cells", {})

    expanding_cells = {
        k: v for k, v in ledger_cells.items()
        if v.get("parameters", {}).get("universe_arm") == "expanding_point_in_time"
    }

    # Compare per-cell formation dates to reconstructed eligibility
    ledger_comparison = []
    for cid, cell in sorted(expanding_cells.items()):
        formations = cell.get("formations", [])
        formation_dates = [f["formation_date"] for f in formations]
        ledger_eapd = cell.get("eligible_assets_per_date", {})

        # Reconstructed eligible counts on those formation dates
        recon_counts = []
        missing_dates = []
        for fd in formation_dates:
            # Find the eligibility date (could be formation_date itself or need to map)
            # The eligibility map uses marketcap dates; formations are a subset
            if fd in elig_map:
                recon_counts.append(len(elig_map[fd]))
            else:
                missing_dates.append(fd)

        if recon_counts:
            recon_mean = sum(recon_counts) / len(recon_counts)
            recon_min = min(recon_counts)
            recon_max = max(recon_counts)
        else:
            recon_mean = recon_min = recon_max = 0

        ledger_mean = ledger_eapd.get("mean", 0)
        ledger_min = ledger_eapd.get("min", 0)
        ledger_max = ledger_eapd.get("max", 0)

        # Tolerance: reconstructed mean within 1.0 of ledger mean, min/max within ledger bounds
        mean_ok = abs(recon_mean - ledger_mean) <= 1.0
        min_ok = recon_min >= ledger_min - 1
        max_ok = recon_max <= ledger_max + 1

        ledger_comparison.append({
            "config_id": cid,
            "formation_count": len(formations),
            "ledger_eligible_assets_per_date": ledger_eapd,
            "reconstructed": {
                "mean": recon_mean,
                "min": recon_min,
                "max": recon_max,
                "missing_dates_count": len(missing_dates),
            },
            "consistency": {
                "mean_ok": mean_ok,
                "min_ok": min_ok,
                "max_ok": max_ok,
                "overall_ok": mean_ok and min_ok and max_ok,
            },
        })

    # Frozen hash verification
    canonical_sha = "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390"
    h10_fresh_sha = "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f"
    ledger_sha = "0184f2d3e5d63dc6fb23a45f0ddfb226a195324d153615588c6c1363a74ce04c"
    frontier_sha = "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e"

    canonical_path = ART / "forward_block" / "forward_block_evaluation.json"
    h10_fresh_path = ART / "forward_block_h10_fresh" / "forward_block_evaluation.json"
    ledger_path = LEDGER_PATH
    frontier_path = ROOT / "research_state" / "universe_frontier.json"

    frozen_hashes = {
        "canonical_forward_block": {
            "expected": canonical_sha,
            "actual": sha256_file(canonical_path) if canonical_path.exists() else "MISSING",
            "match": sha256_file(canonical_path) == canonical_sha if canonical_path.exists() else False,
        },
        "h10_fresh_block": {
            "expected": h10_fresh_sha,
            "actual": sha256_file(h10_fresh_path) if h10_fresh_path.exists() else "MISSING",
            "match": sha256_file(h10_fresh_path) == h10_fresh_sha if h10_fresh_path.exists() else False,
        },
        "grid_result_ledger": {
            "expected": ledger_sha,
            "actual": sha256_file(ledger_path) if ledger_path.exists() else "MISSING",
            "match": sha256_file(ledger_path) == ledger_sha if ledger_path.exists() else False,
        },
        "universe_frontier": {
            "expected": frontier_sha,
            "actual": sha256_file(frontier_path) if frontier_path.exists() else "MISSING",
            "match": sha256_file(frontier_path) == frontier_sha if frontier_path.exists() else False,
        },
    }

    all_frozen_ok = all(v["match"] for v in frozen_hashes.values())

    # Overall PASS/FAIL
    comparison_ok = all(c["consistency"]["overall_ok"] for c in ledger_comparison)
    audit_pass = comparison_ok and all_frozen_ok

    artifact = {
        "audit_id": "H004V106_EXPANDING_UNIVERSE_ELIGIBILITY_COVERAGE_AUDIT",
        "experiment_id": "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-EXP-ELIG-001",
        "hypothesis": "H33",
        "status": "EXPLORATORY_ONLY",
        "audited_utc": now_utc(),
        "audit_pass": audit_pass,
        "frozen_hashes_verified": frozen_hashes,
        "all_frozen_hashes_match": all_frozen_ok,
        "per_date_eligibility": per_date,
        "eligible_stats": eligible_stats,
        "rank_distribution": rank_dist,
        "lifecycle_events": {
            "listings": listing_events,
            "delistings": delisting_events,
            "total_listings": len(listing_events),
            "total_delistings": len(delisting_events),
        },
        "exclusion_counts_total": exclusion_counts,
        "ledger_comparison": ledger_comparison,
        "note": "EXPLORATORY_ONLY diagnostic on committed development inputs. Does not validate, replace or unlock any confirmatory track. No returns, spreads, states, p-values, costs or inference computed.",
    }

    out_name = f"H004V106_expanding_universe_eligibility_coverage_{now_utc().replace(':', '-')}.json"
    out_path = AUDIT_DIR / out_name
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[audit] Wrote artifact -> {out_path.relative_to(ROOT)}", flush=True)
    print(f"[audit] PASS={audit_pass}, frozen_ok={all_frozen_ok}, comparison_ok={comparison_ok}", flush=True)
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())