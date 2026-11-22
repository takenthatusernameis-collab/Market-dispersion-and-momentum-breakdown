#!/usr/bin/env python3
"""Point-in-time cap eligibility of the committed DISP-003 panel inventory (H57).

DISP-003-POINTINTIME-ELIG-001, EXPLORATORY_ONLY. Answers the bounded question
H56 named: is the `>= 20` fresh-window concurrent breadth over the committed
DISP-003 klines panels backed by *point-in-time* cap observations (historical,
date-stamped, never a current snapshot backfilled), and is that inventory a
proven point-in-time market-cap rank universe?

Read-only. No network, no archive fetch. Writes one diagnostic artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001/integrity_audit/.
No returns, spreads, dispersion states, p-values, costs or inference are
computed; the study cannot validate, replace or unlock any confirmatory track.

Import-safe: pure helpers are importable without side effects. CLI:
    python3 scripts/pointintime_eligibility_audit.py [--out <path>]
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import statistics
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

PANEL_DIRS = {
    "committed_disp003": ART / "data" / "panels",
    "wave_b": ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001" / "panels",
    "wave_a": ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEA-001" / "panels",
}
MARKETCAP_PANEL = ART / "data" / "panels" / "marketcap_panel.csv"
RAW_CAP_DIR = ART / "data" / "raw" / "coinmetrics_candidates"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001"
AUDIT_ID = "H004V106_POINTINTIME_ELIG_001"
HYPOTHESIS = "H57"

FRESH_WINDOW_START = (2025, 1)
FRESH_WINDOW_END = (2026, 10)
MIN_BREADTH = 20
ASOF_STALENESS_DAYS = 7

# Frozen artifacts that must be byte-identical before and after (sha256).
FROZEN_EXPECTED = {
    "canonical_forward_block": (
        ART / "forward_block" / "forward_block_evaluation.json",
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    ),
    "h10_fresh_block": (
        ART / "forward_block_h10_fresh" / "forward_block_evaluation.json",
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    ),
    "grid_v3_config": (
        ROOT / "configs" / "dispersion_momentum_grid_v3.json",
        "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
    ),
    "universe_frontier": (
        ROOT / "research_state" / "universe_frontier.json",
        "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
    ),
}

LABEL_ELIGIBLE = "POINT_IN_TIME_ELIGIBLE"
LABEL_LIMITED = "POINT_IN_TIME_LIMITED"


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def symbol_to_asset(symbol: str) -> str:
    """Map a committed klines symbol to its candidate asset id.

    Every committed klines symbol is a USD-M ``USDT`` pair (e.g. ``1INCHUSDT``,
    ``BTCUSDT``); the asset id is the lowercase base with the trailing ``USDT``
    quote removed.
    """
    sym = symbol.strip()
    if sym.upper().endswith("USDT"):
        return sym[:-4].lower()
    return sym.lower()


def month_key(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def month_end_date(year: int, month: int) -> str:
    return date(year, month, calendar.monthrange(year, month)[1]).isoformat()


def fresh_window_months(
    start: tuple[int, int] = FRESH_WINDOW_START,
    end: tuple[int, int] = FRESH_WINDOW_END,
) -> list[tuple[int, int]]:
    """Inclusive (year, month) list from start to end."""
    out = []
    year, month = start
    while (year, month) <= end:
        out.append((year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def snapshot_signature(series: dict[str, float]) -> tuple[bool, str]:
    """Return (is_snapshot_like, reason) for a date->value cap series.

    A series is snapshot-like when it carries fewer than two distinct dates or
    fewer than two distinct values, i.e. it cannot represent a genuine
    historical time series and would be consistent with a single current
    snapshot copied across dates.
    """
    n_dates = len(series)
    n_values = len(set(series.values()))
    if n_dates < 2:
        return True, f"fewer_than_2_distinct_dates(n_dates={n_dates})"
    if n_values < 2:
        return True, f"fewer_than_2_distinct_values(n_values={n_values})"
    return False, "ok"


def _percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * (q / 100.0)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return float(sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac)


def _distribution(values: list[float]) -> dict:
    if not values:
        return {"min": None, "p50": None, "mean": None, "max": None, "n": 0}
    s = sorted(values)
    return {
        "min": s[0],
        "p50": _percentile(s, 50),
        "mean": statistics.fmean(s),
        "max": s[-1],
        "n": len(s),
    }


def load_panel_inventory() -> dict[str, dict]:
    """symbol -> {group, path} across the three declared panel directories."""
    inv: dict[str, dict] = {}
    for label, directory in PANEL_DIRS.items():
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("binance_klines_*.csv")):
            symbol = path.stem.split("binance_klines_")[-1]
            inv[symbol] = {"group": label, "path": path}
    return inv


def load_klines_dates(path: Path) -> tuple[set[str], int]:
    """Return (set of UTC 'YYYY-MM-DD' dates, n_rows) from a klines panel."""
    import pandas as pd

    df = pd.read_csv(path, usecols=["open_time"])
    dates = set(
        pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    )
    return dates, int(len(df))


def load_legacy_cap(path: Path = MARKETCAP_PANEL) -> dict[str, dict[str, float]]:
    """asset -> {date: CapMrktEstUSD} from the committed market-cap panel."""
    import pandas as pd

    df = pd.read_csv(path, dtype={"CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["cap"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    out: dict[str, dict[str, float]] = {}
    for asset, group in df.dropna(subset=["cap"]).groupby("asset"):
        out[str(asset)] = {
            str(row.date): float(row.cap) for row in group.itertuples(index=False)
        }
    return out


def load_raw_cap(raw_dir: Path = RAW_CAP_DIR) -> dict[str, dict[str, float]]:
    """asset -> {date: CapMrktEstUSD} from the committed raw candidate archive."""
    out: dict[str, dict[str, float]] = {}
    for path in sorted(Path(raw_dir).glob("*_CapMrktEstUSD.json")):
        asset = path.name[: -len("_CapMrktEstUSD.json")]
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        series: dict[str, float] = {}
        for row in rows:
            date_str = str(row.get("time", ""))[:10]
            raw = row.get("CapMrktEstUSD")
            if not date_str or raw in (None, ""):
                continue
            try:
                series[date_str] = float(raw)
            except (TypeError, ValueError):
                continue
        if series:
            out[asset] = series
    return out


def resolve_cap_series(
    asset: str,
    legacy_cap: dict[str, dict[str, float]],
    raw_cap: dict[str, dict[str, float]],
) -> tuple[dict[str, float] | None, str | None]:
    """Return (series, source) for an asset.

    The committed legacy market-cap panel is authoritative for the 32 legacy
    assets; the raw Coin Metrics candidate archive supplies the extension
    assets. Both are point-in-time (per exact date); nothing is forward filled.
    """
    if asset in legacy_cap and legacy_cap[asset]:
        return legacy_cap[asset], "legacy_marketcap_panel"
    if asset in raw_cap and raw_cap[asset]:
        return raw_cap[asset], "raw_coinmetrics_candidate"
    return None, None


def per_asset_evidence(
    inventory: dict[str, dict],
    legacy_cap: dict[str, dict[str, float]],
    raw_cap: dict[str, dict[str, float]],
    months: list[tuple[int, int]],
) -> tuple[list[dict], dict[str, dict], dict[str, set[str]]]:
    """Build per-asset evidence, an asset -> cap lookup and a symbol -> klines dates map."""
    rows: list[dict] = []
    cap_lookup: dict[str, dict[str, float]] = {}
    klines_dates: dict[str, set[str]] = {}
    for symbol in sorted(inventory):
        group = inventory[symbol]["group"]
        path = inventory[symbol]["path"]
        asset = symbol_to_asset(symbol)
        dates, n_rows = load_klines_dates(path)
        klines_dates[symbol] = dates
        first = min(dates) if dates else None
        last = max(dates) if dates else None
        series, source = resolve_cap_series(asset, legacy_cap, raw_cap)
        if series:
            cap_lookup[asset] = series
        cap_first = min(series) if series else None
        cap_last = max(series) if series else None
        n_dates = len(series) if series else 0
        n_values = len(set(series.values())) if series else 0
        snap, snap_reason = (
            snapshot_signature(series) if series else (True, "no_cap_series")
        )
        missing_months = [
            month_key(y, m)
            for (y, m) in months
            if not any(d.startswith(month_key(y, m)) for d in dates)
        ]
        rows.append(
            {
                "symbol": symbol,
                "asset": asset,
                "panel_group": group,
                "n_klines": n_rows,
                "klines_first": first,
                "klines_last": last,
                "n_fresh_months_covered": len(months) - len(missing_months),
                "klines_missing_fresh_months": missing_months,
                "cap_source": source,
                "cap_first": cap_first,
                "cap_last": cap_last,
                "n_cap_observations": n_dates,
                "n_cap_distinct_dates": n_dates,
                "n_cap_distinct_values": n_values,
                "snapshot_signature": snap,
                "snapshot_reason": snap_reason,
            }
        )
    return rows, cap_lookup, klines_dates


def per_month_breadth(
    inventory: dict[str, dict],
    cap_lookup: dict[str, dict[str, float]],
    klines_dates: dict[str, set[str]],
    months: list[tuple[int, int]],
) -> list[dict]:
    """Per-month strict and as-of PIT breadth with explicit missing reasons."""
    out: list[dict] = []
    for year, month in months:
        mk = month_key(year, month)
        d = month_end_date(year, month)
        strict = []
        asof = []
        missing: list[dict] = []
        for symbol in sorted(inventory):
            asset = symbol_to_asset(symbol)
            covered = any(date_str.startswith(mk) for date_str in klines_dates[symbol])
            if not covered:
                missing.append({"symbol": symbol, "reason": "nokline"})
                continue
            series = cap_lookup.get(asset)
            if not series:
                missing.append({"symbol": symbol, "reason": "nocap"})
                continue
            if d in series:
                strict.append(symbol)
            else:
                missing.append(
                    {"symbol": symbol, "reason": f"cap_end={max(series)}"}
                )
            asof_ok = any(
                _shift_date(d, -lag) in series
                for lag in range(0, ASOF_STALENESS_DAYS + 1)
            )
            if asof_ok:
                asof.append(symbol)
        out.append(
            {
                "month": mk,
                "month_end": d,
                "n_strict": len(strict),
                "n_asof": len(asof),
                "strict_assets": strict,
                "missing": missing,
            }
        )
    return out


def _shift_date(iso: str, days: int) -> str:
    y, m, d = (int(part) for part in iso.split("-"))
    from datetime import timedelta

    return (date(y, m, d) + timedelta(days=days)).isoformat()


def decide_label(
    per_asset: list[dict],
    monthly: list[dict],
) -> tuple[str, dict]:
    """Apply the predeclared §4 decision rule (outcome-blind)."""
    unresolved = [r["symbol"] for r in per_asset if not r["cap_source"]]
    snapshot_like = [
        r["symbol"] for r in per_asset if r["snapshot_signature"]
    ]
    strict_vals = [float(r["n_strict"]) for r in monthly]
    asof_vals = [float(r["n_asof"]) for r in monthly]
    min_strict = min(strict_vals) if strict_vals else None
    min_asof = min(asof_vals) if asof_vals else None

    cond_resolved = not unresolved
    cond_no_snapshot = not snapshot_like
    cond_strict = min_strict is not None and min_strict >= MIN_BREADTH
    cond_asof = min_asof is not None and min_asof >= MIN_BREADTH

    label = (
        LABEL_ELIGIBLE
        if (cond_resolved and cond_no_snapshot and cond_strict and cond_asof)
        else LABEL_LIMITED
    )
    decision = {
        "min_breadth_required": MIN_BREADTH,
        "condition_all_assets_resolve_to_cap": {
            "pass": bool(cond_resolved),
            "unresolved": unresolved,
        },
        "condition_no_snapshot_signature": {
            "pass": bool(cond_no_snapshot),
            "snapshot_like": snapshot_like,
        },
        "condition_min_strict_breadth_ge_min": {
            "pass": bool(cond_strict),
            "min_strict": min_strict,
        },
        "condition_min_asof_breadth_ge_min": {
            "pass": bool(cond_asof),
            "min_asof": min_asof,
        },
        "label": label,
    }
    return label, decision


def frozen_hash_status() -> tuple[dict, bool]:
    status = {}
    all_ok = True
    for name, (path, expected) in FROZEN_EXPECTED.items():
        actual = sha256_file(path) if path.exists() else None
        match = actual == expected
        all_ok = all_ok and match
        status[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "expected": expected,
            "actual": actual,
            "match": bool(match),
        }
    return status, all_ok


def build_audit() -> dict:
    inventory = load_panel_inventory()
    legacy_cap = load_legacy_cap()
    raw_cap = load_raw_cap()
    months = fresh_window_months()

    per_asset, cap_lookup, klines_dates = per_asset_evidence(
        inventory, legacy_cap, raw_cap, months
    )
    monthly = per_month_breadth(inventory, cap_lookup, klines_dates, months)

    strict_vals = [float(r["n_strict"]) for r in monthly]
    asof_vals = [float(r["n_asof"]) for r in monthly]
    n_months_strict_ge = sum(1 for v in strict_vals if v >= MIN_BREADTH)
    n_months_asof_ge = sum(1 for v in asof_vals if v >= MIN_BREADTH)

    label, decision = decide_label(per_asset, monthly)
    frozen_before, ok_before = frozen_hash_status()

    assets_without_cap = sorted(r["symbol"] for r in per_asset if not r["cap_source"])
    snapshot_like = sorted(r["symbol"] for r in per_asset if r["snapshot_signature"])
    partial_klines = sorted(
        r["symbol"] for r in per_asset if r["n_fresh_months_covered"] < len(months)
    )

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "exploratory_only": True,
        "confirmatory_claim_allowed": False,
        "promotion_allowed": False,
        "computed_utc": now_utc(),
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-POINTINTIME-ELIG-001/"
            "preregistrations/POINTINTIME_ELIG_001_v1.md"
        ),
        "question": (
            "Is the >=20 fresh-window concurrent breadth over the committed "
            "DISP-003 klines panels backed by point-in-time (historical, "
            "date-stamped, never snapshot-backfilled) cap observations, and is "
            "that inventory a proven point-in-time market-cap rank universe?"
        ),
        "window": {
            "month_first": month_key(*months[0]),
            "month_last": month_key(*months[-1]),
            "n_months": len(months),
            "formation_day": "last calendar day of each month (UTC)",
        },
        "inventory": {
            "n_symbols": len(inventory),
            "panel_dirs": {
                label: str(Path(directory).relative_to(ROOT))
                for label, directory in PANEL_DIRS.items()
            },
            "assets_without_cap": assets_without_cap,
            "snapshot_like_assets": snapshot_like,
            "partial_klines_assets": partial_klines,
            "per_asset": per_asset,
        },
        "per_month": monthly,
        "summary": {
            "strict_breadth_stats": _distribution(strict_vals),
            "asof_breadth_stats": _distribution(asof_vals),
            "n_months_strict_ge_min": n_months_strict_ge,
            "n_months_asof_ge_min": n_months_asof_ge,
            "min_breadth_required": MIN_BREADTH,
            "asof_staleness_days": ASOF_STALENESS_DAYS,
            "n_months": len(months),
        },
        "rank_provenance": {
            "complete": False,
            "label": "NOT_PROVEN_COMPLETE",
            "reason": (
                "A rank requires the full eligible population on each date; the "
                "committed panel inventory is a fixed coverage set, not a proven "
                "point-in-time rank universe. universe_frontier.json records "
                "historical_rank_coverage_state=NOT_PROVEN_COMPLETE and "
                "last_verified_historical_rank=null. Today's ranks are never "
                "backfilled as historical ranks."
            ),
            "frontier_historical_rank_coverage_state": "NOT_PROVEN_COMPLETE",
            "last_verified_historical_rank": None,
        },
        "decision_rule": {
            "statement": (
                "POINT_IN_TIME_ELIGIBLE iff every klines symbol resolves to a "
                "cap source AND no cap series carries a snapshot signature "
                "(>=2 distinct dates and >1 distinct value) AND min per-month "
                "strict breadth >= 20 AND min per-month as-of(7d) breadth >= 20."
            ),
            "min_breadth": MIN_BREADTH,
            "asof_staleness_days": ASOF_STALENESS_DAYS,
        },
        "decision": decision,
        "label": label,
        "interpretation": (
            "The committed DISP-003 panel inventory resolves to date-stamped "
            "point-in-time cap observations for every symbol, none carries a "
            "snapshot signature, and the strict same-day breadth stays above "
            "the arity requirement of 20 in every fresh-window month. The "
            "fresh-window breadth is therefore point-in-time cap-eligible. It is "
            "still a coverage/eligibility fact over a fixed panel inventory, not "
            "a proven point-in-time rank universe: rank provenance remains "
            "NOT_PROVEN_COMPLETE and today's ranks are never backfilled."
        ),
        "frozen_hashes_verified": frozen_before,
        "all_frozen_hashes_match": ok_before,
        "note": (
            "EXPLORATORY_ONLY descriptive measurement on committed development "
            "inputs. No returns, spreads, dispersion states, p-values, costs or "
            "inference computed. Does not validate, replace or unlock any "
            "confirmatory track (H1/H6/H7/H10) and is not independent "
            "confirmation. H10 remains date-gated to 2026-11-30."
        ),
    }
    return audit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="artifact path (default: integrity_audit/)")
    args = ap.parse_args(argv)

    audit = build_audit()
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = ROOT / out
    else:
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        out = AUDIT_DIR / f"H004V106_pointintime_eligibility_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[pit-elig] label={audit['label']} symbols={audit['inventory']['n_symbols']} "
        f"strict_min={audit['summary']['strict_breadth_stats']['min']} "
        f"asof_min={audit['summary']['asof_breadth_stats']['min']} "
        f"frozen_ok={audit['all_frozen_hashes_match']}"
    )
    print(f"[pit-elig] wrote {out.relative_to(ROOT)}")
    return 0 if audit["all_frozen_hashes_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())