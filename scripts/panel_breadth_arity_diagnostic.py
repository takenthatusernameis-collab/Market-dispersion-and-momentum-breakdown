#!/usr/bin/env python3
"""Breadth/arity and 2-asset identification diagnostic (DISP-003-BREADTH-ARITY-001, H55).

Read-only feasibility/identification diagnostic for the dispersion-conditioned
momentum mechanism. Answers two structural questions that decide whether a
narrow ARK/ASTR (wave-B) mechanism test can test the registered mechanism:

  M1  How much cross-sectional breadth does the registered outer-decile portfolio
      rule require before both tails are non-empty?
  M2  With a 2-asset cross-section, is the dispersion statistic a deterministic
      function of the trailing momentum spread (so dispersion conditioning is not
      identifiable)?
  M3  What breadth is actually committed per calendar month in this checkout?
  M4  What narrow-test sample would be attainable on the ARK/ASTR overlap?

Hard properties:
  * No network I/O; stdlib only; writes only the ``--execute`` audit file.
  * No forward return, realized spread, cost, p-value or inference is computed.
  * Panels are read as committed; nothing is repaired or interpolated.
  * Frozen hashes are re-verified before any figure is trusted.

Usage:
    python3 scripts/panel_breadth_arity_diagnostic.py            # plan only
    python3 scripts/panel_breadth_arity_diagnostic.py --execute  # write the audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-BREADTH-ARITY-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "BREADTH_ARITY_001_v1.md"

WAVEB_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001"
WAVEB_PANELS = WAVEB_DIR / "panels"
LEGACY_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-002" / "data" / "panels"

CANONICAL_FORWARD_BLOCK = (
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block" / "forward_block_evaluation.json"
)
H10_FRESH_BLOCK = (
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "forward_block_h10_fresh" / "forward_block_evaluation.json"
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
AUDIT_ID = "H004V106_BREADTH_ARITY_001"
HYPOTHESIS = "H55"

WAVEB_ASSETS = ("ARKUSDT", "ASTRUSDT")
LOOKBACK_DAYS = 30
HORIZON_DAYS = 30
PANEL_END_UTC = date(2026, 10, 31)
MIN_OUTER_DECILE_TAIL = 2
IDENTITY_TOL = 1e-12
MIN_IDENTITY_FORMATIONS = 30
MIN_MATURITY_FOR_NARROW_TEST = 30

BREADTH_INVENTORY_START = date(2023, 1, 1)
BREADTH_INVENTORY_END = date(2026, 10, 31)
ARITY_SEARCH_MAX_N = 40

CONFIRMED = "BREADTH_ARITY_CONFIRMED"
STRUCTURAL_LIMIT = "BREADTH_ARITY_STRUCTURAL_LIMIT"
UNEXPECTED = "BREADTH_ARITY_UNEXPECTED"
KLINES_MIN_COLUMNS = ("open_time", "close")


def _sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _display_path(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(Path(path).resolve())


def _utc_date(epoch_ms):
    return datetime.fromtimestamp(int(epoch_ms) / 1000.0, tz=timezone.utc).date()


def decile_tail_size(n):
    """Canonical outer-decile tail size ``k = n // 10`` (see eval_forward_block)."""
    return int(n) // 10


def outer_decile_tails_ok(n):
    """True when the registered rule yields two non-empty tails for breadth ``n``."""
    k = decile_tail_size(n)
    return k >= MIN_OUTER_DECILE_TAIL and 2 * k <= int(n)


def min_breadth_outer_deciles(max_n=ARITY_SEARCH_MAX_N):
    """Smallest breadth with two non-empty decile tails, or None if not found."""
    for n in range(1, int(max_n) + 1):
        if outer_decile_tails_ok(n):
            return n
    return None


def read_klines_close(path):
    """{utc_date: close} from a Binance daily klines CSV; header is validated."""
    out = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or [])
        for col in KLINES_MIN_COLUMNS:
            if col not in header:
                raise ValueError(f"{path}: missing required column {col!r}")
        for row in reader:
            d = _utc_date(row["open_time"])
            close = float(row["close"])
            if not math.isfinite(close) or close <= 0:
                raise ValueError(f"{path}: nonpositive/nonfinite close on {d}")
            if d in out:
                raise ValueError(f"{path}: duplicate date {d}")
            out[d] = close
    if not out:
        raise ValueError(f"{path}: no rows")
    return out


def month_keys(start, end):
    keys = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        keys.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return keys


def month_end_on_or_before(d, target_month_key):
    """Last calendar day of the month containing ``d`` capped at month end."""
    y, m = int(target_month_key[:4]), int(target_month_key[5:7])
    if m == 12:
        nxt = date(y + 1, 1, 1)
    else:
        nxt = date(y, m + 1, 1)
    return nxt - timedelta(days=1)


def month_of(d):
    return f"{d.year:04d}-{d.month:02d}"


def breadth_by_month(panel_dates_by_symbol, months):
    """{month: sorted symbols with >=1 observation in that month}."""
    out = {k: [] for k in months}
    for symbol, dates in panel_dates_by_symbol.items():
        seen = set()
        for d in dates:
            k = month_of(d)
            if k in out and k not in seen:
                out[k].append(symbol)
                seen.add(k)
    for k in out:
        out[k].sort()
    return out


def formation_dates(close_a, close_b, start, end, lookback):
    """Monthly formation dates with a complete lookback in both assets.

    Formation date is the last common observation date in each month. A
    formation is kept only when the merged positional window
    ``[end_loc - lookback, end_loc]`` is fully populated for both assets,
    mirroring MomentumCache's completeness rule.
    """
    common = sorted(set(close_a) & set(close_b))
    if not common:
        return []
    positional = common
    loc = {d: i for i, d in enumerate(positional)}
    by_month = {}
    for d in positional:
        if start <= d <= end:
            by_month[month_of(d)] = d
    out = []
    for key in sorted(by_month):
        t = by_month[key]
        i = loc[t]
        if i - lookback < 0:
            continue
        window = positional[i - lookback:i + 1]
        if all(d in close_a and d in close_b for d in window):
            out.append(t)
    return out


def cumulative_momentum(close_by_date, window_dates):
    """Cumulative product of daily returns over ``window_dates`` (canonical form)."""
    if len(window_dates) < 2:
        return None
    prod = 1.0
    for prev, cur in zip(window_dates[:-1], window_dates[1:]):
        prod *= close_by_date[cur] / close_by_date[prev]
    return prod - 1.0


def dispersion_identity(a, b):
    """Population std of two cross-sectional values and the algebraic identity."""
    d = float(math.sqrt(((a - (a + b) / 2.0) ** 2 + (b - (a + b) / 2.0) ** 2) / 2.0))
    absdiff = abs(a - b)
    return {
        "dispersion_pop_std_ddof0": d,
        "abs_momentum_spread": absdiff,
        "ratio_dispersion_over_abs_spread": (d / absdiff) if absdiff > 0 else None,
        "abs_deviation_from_half_abs_spread": abs(d - absdiff / 2.0),
        "identity_holds": abs(d - absdiff / 2.0) <= IDENTITY_TOL,
    }


def arity_table(max_n=ARITY_SEARCH_MAX_N):
    table = []
    for n in range(1, int(max_n) + 1):
        k = decile_tail_size(n)
        table.append(
            {
                "n_assets": n,
                "tail_size_k": k,
                "long_leg_size": k,
                "short_leg_size": k,
                "both_tails_nonempty": outer_decile_tails_ok(n),
            }
        )
    return table


def evaluate_verdict(arity_min_n, identity_max_dev, identity_n, waveb_only_months_below_20,
                     narrow_matured, breadth_ge_20_months, legacy_latest_month):
    """Predeclared verdict rule; returns (verdict, reasons)."""
    reasons = []
    if arity_min_n != 20:
        reasons.append(f"min_breadth_outer_deciles={arity_min_n} (expected 20)")
    if identity_max_dev is None or identity_max_dev > IDENTITY_TOL:
        reasons.append(f"two_asset_identity_max_deviation={identity_max_dev}")
    if identity_n < MIN_IDENTITY_FORMATIONS:
        reasons.append(f"identity_formations={identity_n} < {MIN_IDENTITY_FORMATIONS}")
    if reasons:
        return UNEXPECTED, reasons
    if waveb_only_months_below_20 and narrow_matured < MIN_MATURITY_FOR_NARROW_TEST:
        if breadth_ge_20_months > 0 and legacy_latest_month == "2024-12":
            return STRUCTURAL_LIMIT, [
                "registered outer-decile rule needs breadth>=20 (M1)",
                "2-asset dispersion is |spread|/2 exactly (M2), so dispersion conditioning "
                "is not identifiable in a 2-asset cross-section",
                "wave-B-only breadth is <20 in every month (M3)",
                f"attainable narrow-test matured formations={narrow_matured} (M4)",
                "months with breadth>=20 come only from already-inspected legacy-28 panels "
                "ending 2024-12-31",
            ]
        return CONFIRMED, ["structural limits hold; no legacy breadth>=20 month exists"]
    return UNEXPECTED, ["wave-B or narrow-maturity condition not met"]


def verdict_checks(arity_min_n, identity_max_dev, identity_n, waveb_only_below_20,
                   narrow_matured, breadth_ge_20_months, legacy_latest_month):
    """Per-condition record of the predeclared verdict rule, unchanged and explicit."""
    return [
        {
            "condition": "M1 min_breadth_outer_deciles == 20",
            "observed": arity_min_n,
            "held": arity_min_n == 20,
        },
        {
            "condition": "M2 max_abs_deviation <= 1e-12",
            "observed": identity_max_dev,
            "held": identity_max_dev is not None and identity_max_dev <= IDENTITY_TOL,
        },
        {
            "condition": f"M2 n_formations >= {MIN_IDENTITY_FORMATIONS}",
            "observed": identity_n,
            "held": identity_n >= MIN_IDENTITY_FORMATIONS,
        },
        {
            "condition": "M3 wave-B-only breadth < 20 in every wave-B-only month",
            "observed": waveb_only_below_20,
            "held": bool(waveb_only_below_20),
        },
        {
            "condition": f"M4 n_forward_matured < {MIN_MATURITY_FOR_NARROW_TEST}",
            "observed": narrow_matured,
            "held": narrow_matured < MIN_MATURITY_FOR_NARROW_TEST,
        },
        {
            "condition": "breadth>=20 months exist and are legacy months",
            "observed": {
                "n_months_breadth_ge_20": breadth_ge_20_months,
                "legacy_latest_month": legacy_latest_month,
            },
            "held": breadth_ge_20_months > 0 and legacy_latest_month == "2024-12",
        },
    ]


def build_plan():
    return {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "preregistration": _display_path(PREREG),
        "inputs": {
            "waveb_panels_dir": _display_path(WAVEB_PANELS),
            "legacy_panels_dir": _display_path(LEGACY_DIR),
            "lookback_days": LOOKBACK_DAYS,
            "horizon_days": HORIZON_DAYS,
            "panel_end_utc": PANEL_END_UTC.isoformat(),
        },
        "measurements": [
            "M1 arity of the registered outer-decile rule (n=1..40)",
            "M2 ARK/ASTR dispersion = |momentum spread|/2 identity",
            "M3 committed breadth per calendar month 2023-01..2026-10",
            "M4 attainable narrow-test formations on the ARK/ASTR overlap",
        ],
        "execute": False,
    }


def execute():
    if not PREREG.exists():
        raise SystemExit(f"preregistration missing: {PREREG}")

    frozen = {}
    for name, expected in EXPECTED_FROZEN_SHA256.items():
        path = {
            "canonical_forward_block": CANONICAL_FORWARD_BLOCK,
            "h10_fresh_block": H10_FRESH_BLOCK,
            "universe_frontier": UNIVERSE_FRONTIER,
            "grid_v3_config": GRID_V3_CONFIG,
        }[name]
        actual = _sha256_file(path)
        frozen[name] = {
            "path": _display_path(path),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "match": actual == expected,
        }
    if not all(v["match"] for v in frozen.values()):
        raise SystemExit("frozen hash mismatch; refusing to compute")

    # M1 — arity
    table = arity_table()
    arity_min_n = min_breadth_outer_deciles()

    # M2 — 2-asset identity on monthly formations
    closes = {}
    panel_dates = {}
    for symbol in WAVEB_ASSETS:
        path = WAVEB_PANELS / f"binance_klines_{symbol}.csv"
        series = read_klines_close(path)
        closes[symbol] = series
        panel_dates[symbol] = sorted(series)

    overlap_start = max(min(d) for d in panel_dates.values())
    overlap_end = min(max(d) for d in panel_dates.values())
    formations = formation_dates(
        closes[WAVEB_ASSETS[0]], closes[WAVEB_ASSETS[1]], overlap_start, overlap_end, LOOKBACK_DAYS
    )
    merged = sorted(set(closes[WAVEB_ASSETS[0]]) & set(closes[WAVEB_ASSETS[1]]))
    loc = {d: i for i, d in enumerate(merged)}
    identity_rows = []
    for t in formations:
        i = loc[t]
        window = merged[i - LOOKBACK_DAYS:i + 1]
        m_a = cumulative_momentum(closes[WAVEB_ASSETS[0]], window)
        m_b = cumulative_momentum(closes[WAVEB_ASSETS[1]], window)
        row = {"formation_date": t.isoformat(), "m_ark": m_a, "m_astr": m_b}
        row.update(dispersion_identity(m_a, m_b))
        identity_rows.append(row)
    identity_max_dev = (
        max(r["abs_deviation_from_half_abs_spread"] for r in identity_rows)
        if identity_rows else None
    )
    ratios = [r["ratio_dispersion_over_abs_spread"] for r in identity_rows
              if r["ratio_dispersion_over_abs_spread"] is not None]
    identity_holds_all = all(r["identity_holds"] for r in identity_rows)

    # M3 — committed breadth inventory
    legacy_files = sorted(LEGACY_DIR.glob("binance_klines_*.csv"))
    legacy_symbols = [p.name[len("binance_klines_"):-4] for p in legacy_files]
    all_dates = {}
    for p in legacy_files:
        all_dates[p.name[len("binance_klines_"):-4]] = sorted(read_klines_close(p))
    for symbol in WAVEB_ASSETS:
        all_dates[symbol] = panel_dates[symbol]
    months = month_keys(BREADTH_INVENTORY_START, BREADTH_INVENTORY_END)
    breadth = breadth_by_month(all_dates, months)
    waveb_set = set(WAVEB_ASSETS)
    breadth_rows = []
    for key in months:
        syms = breadth[key]
        legacy_n = len([s for s in syms if s not in waveb_set])
        waveb_n = len([s for s in syms if s in waveb_set])
        breadth_rows.append(
            {
                "month": key,
                "n_assets": len(syms),
                "n_legacy_assets": legacy_n,
                "n_waveb_assets": waveb_n,
                "breadth_ge_20": len(syms) >= 20,
                "waveb_only": legacy_n == 0 and waveb_n > 0,
            }
        )
    max_breadth = max(r["n_assets"] for r in breadth_rows)
    breadth_ge_20 = [r["month"] for r in breadth_rows if r["breadth_ge_20"]]
    waveb_only_months = [r["month"] for r in breadth_rows if r["waveb_only"]]
    waveb_only_below_20 = all(
        r["n_assets"] < 20 for r in breadth_rows if r["waveb_only"]
    ) and len(waveb_only_months) > 0
    legacy_latest_month = max(
        (month_of(max(all_dates[s])) for s in legacy_symbols), default=None
    )

    # M4 — attainable narrow-test sample
    narrow = []
    for t in formations:
        i = loc[t]
        fwd_end = i + HORIZON_DAYS
        matured = fwd_end < len(merged) and merged[fwd_end] <= PANEL_END_UTC
        narrow.append(
            {
                "formation_date": t.isoformat(),
                "lookback_complete": True,
                "forward_end_date": merged[fwd_end].isoformat() if fwd_end < len(merged) else None,
                "forward_matured": bool(matured),
            }
        )
    n_matured = sum(1 for r in narrow if r["forward_matured"])

    verdict, reasons = evaluate_verdict(
        arity_min_n,
        identity_max_dev,
        len(identity_rows),
        waveb_only_below_20,
        n_matured,
        len(breadth_ge_20),
        legacy_latest_month,
    )

    checks = verdict_checks(
        arity_min_n,
        identity_max_dev,
        len(identity_rows),
        waveb_only_below_20,
        n_matured,
        len(breadth_ge_20),
        legacy_latest_month,
    )
    failed = [c["condition"] for c in checks if not c["held"]]
    if failed == [f"M4 n_forward_matured < {MIN_MATURITY_FOR_NARROW_TEST}"]:
        interpretation = (
            "All structural conditions held exactly (M1 arity=20, M2 identity deviation=0, "
            "M3 wave-B-only breadth<20). Only the predeclared M4 sample-size expectation "
            f"failed: the overlap carries {n_matured} matured monthly formations, not fewer "
            f"than {MIN_MATURITY_FOR_NARROW_TEST}. The narrow 2-asset route is therefore closed "
            "by arity and by algebraic non-identifiability, not by insufficient sample size; "
            "the preregistered expectation about maturity was wrong and is reported as-is."
        )
    elif not failed:
        interpretation = "All predeclared conditions held."
    else:
        interpretation = "Deviating predeclared conditions: " + "; ".join(failed)

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "label": "feasibility_identification_diagnostic",
        "status": "EXPLORATORY_ONLY",
        "computed_utc": _utc_now(),
        "preregistration": _display_path(PREREG),
        "preregistration_created_utc": "2026-11-20T02:33:35Z",
        "network_io": "none",
        "confirmatory_claim_allowed": False,
        "frozen_hashes_verified": {
            "all_match": all(v["match"] for v in frozen.values()),
            "details": frozen,
        },
        "inputs": {
            "waveb_panels": [
                _display_path(WAVEB_PANELS / f"binance_klines_{s}.csv") for s in WAVEB_ASSETS
            ],
            "legacy_panel_count": len(legacy_files),
            "legacy_symbols": legacy_symbols,
            "legacy_panels_modified": False,
            "lookback_days": LOOKBACK_DAYS,
            "horizon_days": HORIZON_DAYS,
            "panel_end_utc": PANEL_END_UTC.isoformat(),
        },
        "m1_arity": {
            "min_breadth_outer_deciles": arity_min_n,
            "required_tail_size": MIN_OUTER_DECILE_TAIL,
            "rule": "trailing_window_outer_deciles with k = n // 10, k >= 2",
            "table": table,
            "implied_requirement": (
                "a fresh forward block must carry at least "
                f"{arity_min_n} concurrently eligible assets for the registered "
                "long/short decile tails to be non-empty"
            ),
        },
        "m2_identity": {
            "assets": list(WAVEB_ASSETS),
            "n_formations": len(identity_rows),
            "identity": "population std of two momentum values == |m1 - m2| / 2",
            "max_abs_deviation": identity_max_dev,
            "identity_holds_all_formations": identity_holds_all,
            "ratio_min": min(ratios) if ratios else None,
            "ratio_max": max(ratios) if ratios else None,
            "sign_invariance": (
                "the dispersion statistic is unchanged when the two assets are swapped; "
                "the signed spread changes sign, so a dispersion-only state cannot select "
                "a long leg or a short leg in a 2-asset cross-section"
            ),
            "formations": identity_rows,
        },
        "m3_breadth_inventory": {
            "window": [BREADTH_INVENTORY_START.isoformat(), BREADTH_INVENTORY_END.isoformat()],
            "max_breadth": max_breadth,
            "n_months": len(breadth_rows),
            "months_with_breadth_ge_20": breadth_ge_20,
            "n_months_with_breadth_ge_20": len(breadth_ge_20),
            "months_waveb_only": waveb_only_months,
            "n_months_waveb_only": len(waveb_only_months),
            "waveb_only_breadth_below_20_in_every_month": waveb_only_below_20,
            "legacy_latest_observed_month": legacy_latest_month,
            "rows": breadth_rows,
        },
        "m4_narrow_sample": {
            "overlap_window": [overlap_start.isoformat(), overlap_end.isoformat()],
            "n_candidate_formations": len(narrow),
            "n_lookback_complete": sum(1 for r in narrow if r["lookback_complete"]),
            "n_forward_matured": n_matured,
            "min_maturity_required": MIN_MATURITY_FOR_NARROW_TEST,
            "rows": narrow,
        },
        "verdict": verdict,
        "verdict_reasons": reasons,
        "verdict_checks": checks,
        "verdict_interpretation": interpretation,
        "decision": {
            "narrow_two_asset_mechanism_test": "CLOSED_BY_CONSTRUCTION",
            "why": (
                "the registered rule needs breadth>=20 and, at breadth 2, the dispersion "
                "statistic is an exact deterministic function of the momentum spread, so a "
                "2-asset sample cannot identify a dispersion-conditioning mechanism"
            ),
            "binding_requirement": (
                "acquire >=20 concurrently priced, point-in-time eligible assets in a fresh "
                "period (wave A and later waves); no further wave-B asset adds identification"
            ),
            "confirmatory_track_impact": "none; H10 fresh sealed block remains date-gated to 2026-11-30",
        },
        "non_claims": [
            "Not market evidence and not an economic result.",
            "No forward return, realized spread, dispersion-state outcome, cost, funding PnL, p-value or interval computed.",
            "Dispersion is a feature-side statistic used only to demonstrate an algebraic identity.",
            "No candidate promoted; confirmatory_claim_allowed=false.",
            "Frozen DISP-001/002/003 artifacts, configs, ledgers, panels, forward blocks and frontier unchanged.",
            "Does not unlock H1/H6/H7/H10; legacy panels are already-inspected development data.",
            "A green test suite proves only what the tests cover.",
        ],
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / f"panel_breadth_arity_diagnostic_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(audit, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"written": _display_path(out), "verdict": verdict,
                      "min_breadth_outer_deciles": arity_min_n,
                      "identity_max_deviation": identity_max_dev,
                      "n_forward_matured": n_matured,
                      "max_breadth": max_breadth}, indent=1))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                        help="write the audit JSON under integrity_audit/")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps(build_plan(), indent=1, sort_keys=True))
        return 0
    return execute()


if __name__ == "__main__":
    raise SystemExit(main())
