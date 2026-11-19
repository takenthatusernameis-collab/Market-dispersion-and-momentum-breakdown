#!/usr/bin/env python3
"""Wave-B extension panel usability and coverage audit (DISP-003-PANELQA-WAVEB-001, H54).

Read-only QA of the four H53-normalized ARK/ASTR panels. Measures calendar-day
continuity, gap structure, OHLC plausibility, zero-volume days, funding cadence
and end-of-panel staleness, and records a predeclared verdict.

Hard properties:
  * No network I/O and no writes outside the ``--execute`` audit file.
  * Panels are read as committed; nothing is repaired, interpolated, reindexed
    or dropped. Issues are reported with counts and offending dates.
  * Every panel is re-hashed and reconciled against the H53 audit sha256 and
    row count before any quality metric is trusted.
  * No returns, spreads, states, p-values, costs or inference are computed.

Usage:
    python3 scripts/panel_wave_b_quality_audit.py            # plan only, no I/O
    python3 scripts/panel_wave_b_quality_audit.py --execute  # write the audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELQA-WAVEB-001"
EXP_DIR = ROOT / "artifacts" / EXP
QA_DIR = EXP_DIR / "qa"
PREREG = EXP_DIR / "preregistrations" / "PANELQA_WAVEB_001_v1.md"

H53_DIR = (
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001"
)
H53_AUDIT = (
    H53_DIR / "integrity_audit" / "panel_wave_b_normalization_2026-11-19T054929Z.json"
)
PANEL_DIR = H53_DIR / "panels"

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
AUDIT_ID = "H004V106_PANELQA_WAVEB_001"
HYPOTHESIS = "H54"

PANEL_END_UTC = date(2026, 10, 31)
MAX_ALLOWED_STALENESS_DAYS = 3
MIN_KLINES_COMPLETENESS = 0.98
ALLOWED_FUNDING_INTERVALS = (1.0, 2.0, 4.0, 8.0)

KINDS = ("klines", "funding")
EXPECTED_ASSETS = ("ark", "astr")
EXPECTED_PANELS = 4

SCOPE_MISMATCH = "PANELQA_WAVEB_SCOPE_MISMATCH"
ISSUES_FOUND = "PANELQA_WAVEB_ISSUES_FOUND"
COMPLETE = "PANELQA_WAVEB_COMPLETE"


def _file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _display_path(path):
    """Repo-relative when inside the checkout, absolute otherwise (tests)."""
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(Path(path).resolve())


def _utc_date(epoch_ms):
    return datetime.fromtimestamp(int(epoch_ms) / 1000.0, tz=timezone.utc).date()


def panel_filename(symbol, kind):
    return f"binance_{kind}_{symbol}.csv"


def expected_panels(h53_audit):
    """Ordered [(asset, symbol, kind, filename, sha256, n_rows)] from H53."""
    out = []
    for panel in h53_audit.get("panels") or []:
        out.append(
            (
                panel.get("asset"),
                panel.get("symbol"),
                panel.get("kind"),
                Path(panel.get("path", "")).name,
                panel.get("sha256"),
                panel.get("n_rows"),
            )
        )
    order = {(a, k): i for i, (a, k) in enumerate(
        (a, k) for a in EXPECTED_ASSETS for k in KINDS
    )}
    out.sort(key=lambda r: order.get((r[0], r[2]), 99))
    return out


def read_csv_rows(path):
    """Rows as dicts; the header must match the DISP-003 schema field set."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def expected_days(first_ms, last_ms):
    return (_utc_date(last_ms) - _utc_date(first_ms)).days + 1


def gap_profile(dates):
    """(missing_dates, max_gap_run_days) over the inclusive calendar span."""
    if not dates:
        return [], 0
    ordered = sorted(set(dates))
    first, last = ordered[0], ordered[-1]
    span = (last - first).days + 1
    present = set(ordered)
    missing = [first.fromordinal(first.toordinal() + i) for i in range(span)]
    missing = [d for d in missing if d not in present]
    best = run = 0
    cursor = first
    present_sorted = ordered
    idx = 0
    while cursor <= last:
        if idx < len(present_sorted) and present_sorted[idx] == cursor:
            run = 0
            idx += 1
        else:
            run += 1
            best = max(best, run)
        cursor = cursor.fromordinal(cursor.toordinal() + 1)
    return missing, best


def klines_metrics(rows):
    """Deterministic QA metrics for a daily klines panel."""
    timestamps = []
    nonpositive = 0
    inconsistent = 0
    negative_volume = 0
    zero_volume_days = 0
    for row in rows:
        ms = int(row["open_time"])
        timestamps.append(ms)
        o, h, l, c = (float(row[f]) for f in ("open", "high", "low", "close"))
        v = float(row["volume"])
        if min(o, h, l, c) <= 0.0:
            nonpositive += 1
        if h < max(o, c) or l > min(o, c) or h < l:
            inconsistent += 1
        if v < 0.0:
            negative_volume += 1
        if v == 0.0:
            zero_volume_days += 1
    dates = [_utc_date(ms) for ms in timestamps]
    n_duplicates = len(timestamps) - len(set(timestamps))
    nonmonotone = any(b <= a for a, b in zip(timestamps, timestamps[1:]))
    miss, max_run = gap_profile(dates)
    exp = expected_days(min(timestamps), max(timestamps)) if timestamps else 0
    obs = len(set(dates))
    return {
        "n_rows": len(rows),
        "n_duplicate_timestamps": n_duplicates,
        "timestamps_monotone": not nonmonotone,
        "first_ts_utc": (
            datetime.fromtimestamp(min(timestamps) / 1000.0, tz=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
            if timestamps
            else None
        ),
        "last_ts_utc": (
            datetime.fromtimestamp(max(timestamps) / 1000.0, tz=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
            if timestamps
            else None
        ),
        "n_observed_days": obs,
        "expected_days": exp,
        "completeness_ratio": (obs / exp) if exp else 0.0,
        "n_missing_days": len(miss),
        "missing_days": [d.isoformat() for d in miss],
        "max_gap_run_days": max_run,
        "n_nonpositive_price": nonpositive,
        "n_ohlc_inconsistent": inconsistent,
        "n_negative_volume": negative_volume,
        "n_zero_volume_days": zero_volume_days,
        "days_stale": (PANEL_END_UTC - max(dates)).days if dates else None,
    }


def funding_metrics(rows):
    """Deterministic QA metrics for a funding panel (descriptive, no inference)."""
    times = [int(row["calc_time"]) for row in rows]
    intervals = [float(row["funding_interval_hours"]) for row in rows]
    rates = []
    nonfinite = 0
    zero = 0
    extreme = 0
    for row in rows:
        value = float(row["last_funding_rate"])
        if not math.isfinite(value):
            nonfinite += 1
            continue
        rates.append(value)
        if value == 0.0:
            zero += 1
        if abs(value) > 0.1:
            extreme += 1
    hist = {}
    for value in intervals:
        hist[str(value)] = hist.get(str(value), 0) + 1
    span_days = expected_days(min(times), max(times)) if times else 0
    return {
        "n_rows": len(rows),
        "n_duplicate_calc_time": len(times) - len(set(times)),
        "calc_time_monotone": not any(b <= a for a, b in zip(times, times[1:])),
        "first_ts_utc": (
            datetime.fromtimestamp(min(times) / 1000.0, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            if times
            else None
        ),
        "last_ts_utc": (
            datetime.fromtimestamp(max(times) / 1000.0, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            if times
            else None
        ),
        "funding_interval_hours_histogram": dict(sorted(hist.items())),
        "interval_values_allowed": all(
            value in ALLOWED_FUNDING_INTERVALS for value in intervals
        ),
        "rows_per_day": (len(times) / span_days) if span_days else 0.0,
        "n_nonfinite_rate": nonfinite,
        "n_zero_rate": zero,
        "n_abs_rate_gt_0_1": extreme,
        "days_stale": (
            (PANEL_END_UTC - _utc_date(max(times))).days if times else None
        ),
    }


def panel_issues(kind, metrics):
    """Predeclared issue list for one panel (empty means clean)."""
    issues = []
    stale = metrics.get("days_stale")
    if stale is not None and stale > MAX_ALLOWED_STALENESS_DAYS:
        issues.append(f"stale_{stale}_days")
    if kind == "klines":
        if metrics["n_duplicate_timestamps"]:
            issues.append("duplicate_timestamps")
        if not metrics["timestamps_monotone"]:
            issues.append("non_monotone_timestamps")
        if metrics["completeness_ratio"] < MIN_KLINES_COMPLETENESS:
            issues.append("calendar_completeness_below_0_98")
        for key in ("n_nonpositive_price", "n_ohlc_inconsistent", "n_negative_volume"):
            if metrics[key]:
                issues.append(key)
    else:
        if metrics["n_duplicate_calc_time"]:
            issues.append("duplicate_calc_time")
        if not metrics["calc_time_monotone"]:
            issues.append("non_monotone_calc_time")
        if not metrics["interval_values_allowed"]:
            issues.append("unexpected_funding_interval")
        if metrics["n_nonfinite_rate"]:
            issues.append("nonfinite_funding_rate")
    return issues


def frozen_hashes():
    actual = {
        "canonical_forward_block": _file_sha256(CANONICAL_FORWARD_BLOCK),
        "h10_fresh_block": _file_sha256(H10_FRESH_BLOCK),
        "universe_frontier": _file_sha256(UNIVERSE_FRONTIER),
        "grid_v3_config": _file_sha256(GRID_V3_CONFIG),
    }
    detail = {}
    for key, expected in EXPECTED_FROZEN_SHA256.items():
        detail[key] = {
            "expected": expected,
            "actual": actual[key],
            "match": actual[key] == expected,
        }
    return detail


def run_audit(panel_dir=PANEL_DIR, h53_audit_path=H53_AUDIT):
    """Compute the audit body. Pure read of committed CSVs; no writes."""
    h53 = _load_json(h53_audit_path)
    panels = []
    scope_problems = []
    for asset, symbol, kind, name, sha, n_rows in expected_panels(h53):
        path = Path(panel_dir) / name
        if not path.exists():
            scope_problems.append(f"missing_panel:{name}")
            continue
        actual_sha = _file_sha256(path)
        rows, header = read_csv_rows(path)
        if actual_sha != sha:
            scope_problems.append(f"sha256_mismatch:{name}")
        if len(rows) != int(n_rows):
            scope_problems.append(f"row_count_mismatch:{name}")
        metrics = klines_metrics(rows) if kind == "klines" else funding_metrics(rows)
        panels.append(
            {
                "asset": asset,
                "symbol": symbol,
                "kind": kind,
                "path": _display_path(path),
                "header": header,
                "sha256_matches_h53": actual_sha == sha,
                "row_count_matches_h53": len(rows) == int(n_rows),
                "metrics": metrics,
                "issues": panel_issues(kind, metrics),
            }
        )
    kline_dates = {
        p["asset"]: set()
        for p in panels
        if p["kind"] == "klines"
    }
    for p in panels:
        if p["kind"] != "klines":
            continue
        rows, _ = read_csv_rows(Path(p["path"]))
        kline_dates[p["asset"]] = {_utc_date(int(r["open_time"])) for r in rows}
    both = kline_dates.get("ark", set()) & kline_dates.get("astr", set())
    one_only = kline_dates.get("ark", set()) ^ kline_dates.get("astr", set())
    overlap = {
        "n_days_both_assets": len(both),
        "n_days_single_asset": len(one_only),
        "ark_only_days": len(kline_dates.get("ark", set()) - kline_dates.get("astr", set())),
        "astr_only_days": len(kline_dates.get("astr", set()) - kline_dates.get("ark", set())),
    }
    if scope_problems or len(panels) != EXPECTED_PANELS:
        verdict = SCOPE_MISMATCH
    elif any(p["issues"] for p in panels):
        verdict = ISSUES_FOUND
    else:
        verdict = COMPLETE
    return {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "confirmatory_claim_allowed": False,
        "promotion_allowed": False,
        "computed_utc": _utc_now(),
        "method": (
            "Read-only usability audit of the 4 committed H53 wave-B panels: "
            "sha256 and row-count reconciliation against H53, calendar-day "
            "completeness and gap runs, OHLC plausibility, duplicate and "
            "monotonicity checks, zero-volume days, funding cadence and "
            "end-of-panel staleness. No repair, no interpolation, no network."
        ),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "audited_input_sha256": {
            "h53_audit_file": _file_sha256(h53_audit_path),
        },
        "verdict": verdict,
        "verdict_rule": (
            "SCOPE_MISMATCH on any missing panel, H53 sha256 or row-count "
            "mismatch, or panel count != 4; ISSUES_FOUND on any predeclared "
            "panel issue (completeness < 0.98, nonpositive price, OHLC "
            "inconsistency, negative volume, duplicate/non-monotone timestamp, "
            "unexpected funding interval, nonfinite rate, staleness > 3 days); "
            "COMPLETE only when all four panels are clean."
        ),
        "thresholds": {
            "panel_end_utc": PANEL_END_UTC.isoformat(),
            "max_allowed_staleness_days": MAX_ALLOWED_STALENESS_DAYS,
            "min_klines_completeness": MIN_KLINES_COMPLETENESS,
            "allowed_funding_intervals_hours": list(ALLOWED_FUNDING_INTERVALS),
        },
        "panels": panels,
        "cross_panel": overlap,
        "scope_problems": scope_problems,
        "frozen_hashes_verified": {
            "all_match": all(v["match"] for v in frozen_hashes().values()),
            "details": frozen_hashes(),
        },
        "network_io": "none",
        "non_claims": [
            "A panel quality audit is not market evidence and not an economic result.",
            "No returns, spreads, dispersion states, momentum signals, p-values, costs or inference computed.",
            "No candidate promoted; no confirmatory claim; H10 gate unchanged and date-gated to 2026-11-30.",
            "Wave A (7 assets, 644 files) is out of scope: its raw bytes are absent in this checkout.",
            "Issues are reported with counts and offending dates; nothing is repaired, interpolated or dropped.",
            "Does not alter any frozen DISP-001/002/003 artifact, config, ledger, panel or forward block, and does not unlock H1/H6/H7/H10.",
            "A green test suite proves only what the tests cover.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="write the audit JSON")
    args = parser.parse_args(argv)
    audit = run_audit()
    print(f"[plan] verdict={audit['verdict']} panels={len(audit['panels'])}")
    for panel in audit["panels"]:
        print(
            f"  {panel['symbol']:>9} {panel['kind']:<7} rows={panel['metrics']['n_rows']:>5}"
            f" issues={panel['issues'] or 'none'}"
        )
    if not args.execute:
        print("[plan] no file written; pass --execute")
        return 0
    QA_DIR.mkdir(parents=True, exist_ok=True)
    stamp = audit["computed_utc"].replace(":", "")
    out = QA_DIR / f"panel_wave_b_quality_audit_{stamp}.json"
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"[done] audit={out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
