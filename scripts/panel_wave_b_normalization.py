#!/usr/bin/env python3
"""Wave-B extension panel normalization (DISP-003-PANELNORM-WAVEB-001, H53).

Normalizes exactly the H52-acquired wave-B archives (ARK, ASTR) into four
committed DISP-003-schema panel CSVs and records per-file reconciliation.

Hard properties:
  * Pinned input digests are verified before any panel byte is written.
  * Every cache file is re-hashed against the sha256 H52 recorded.
  * Content is re-validated (one CSV member, documented header, >=1 data row,
    non-decreasing integer timestamps); malformed input is reported, never
    repaired, interpolated or backfilled.
  * Only rows inside their source month's UTC window contribute; the union of
    contributing months must equal the H51-a admissible months.
  * Row accounting is exact: rows written == sum of contributing n_csv_rows.
  * Duplicate timestamps are reported and fail completeness, never collapsed.
  * No network I/O.

Usage:
    python3 scripts/panel_wave_b_normalization.py            # plan only, no I/O
    python3 scripts/panel_wave_b_normalization.py --execute  # write panels + audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001"
EXP_DIR = ROOT / "artifacts" / EXP
PANEL_DIR = EXP_DIR / "panels"
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELNORM_WAVEB_001_v1.md"

H52_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEB-001"
    / "integrity_audit"
    / "panel_wave_b_acquisition_20261119T032343Z.json"
)
H51A_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-PLAN-001"
    / "integrity_audit"
    / "panel_normalization_plan_20261118T231800Z.json"
)
H50_TRIM = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001"
    / "integrity_audit"
    / "panel_wave_b_window_trim_20261118T221212Z.json"
)
CACHE_DIR = ROOT / "data" / "panel_archive_wave_b"

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

H52_AUDIT_FILE_SHA256 = "fb2b7cf7642d616b51e303ffc37382dc2a79e355e4df11f150fffad19ac7c5ef"
H52_RECORDS_CANONICAL_SHA256 = "887970ebbf3e06fadc1f7e265bd72e5de94aea605e3cba3a34938193562a335c"
H51A_PLAN_FILE_SHA256 = "dc8e100682cf3eab147787973536dd0de1517c740e5075a7c3f3db43796b9768"
H50_TRIM_FILE_SHA256 = "5aed05f1615a3cc2983c6e1be86ef9f35306aed7cfab86aea9f1d8fab9f61e66"
H50_TRIM_CANONICAL_SHA256 = "b43f71bf239254152288b8eaf89a7748680117c7ecc10a16564c4a9b6a115a5d"

EXPERIMENT_ID = EXP
AUDIT_ID = "H004V106_PANELNORM_WAVEB_001"
HYPOTHESIS = "H53"

KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"
KLINES_FIELDS = KLINES_HEADER.split(",")
FUNDING_FIELDS = FUNDING_HEADER.split(",")[1:]

KINDS = ("klines", "funding")
EXPECTED_ASSETS = ("ark", "astr")
EXPECTED_RECORDS = 166
EXPECTED_PANELS = 4
EXPECTED_FILES_PER_ASSET = {"ark": 76, "astr": 90}
FORBIDDEN_ASSETS = ("alice", "ankr", "ape", "api3", "apt", "ar", "arpa", "alpha")

SCOPE_MISMATCH = "PANELNORM_WAVEB_SCOPE_MISMATCH"
INCOMPLETE = "PANELNORM_WAVEB_INCOMPLETE"
COMPLETE = "PANELNORM_WAVEB_COMPLETE"


def _canonical_sha256(obj):
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def panel_filename(symbol, kind):
    return f"binance_{kind}_{symbol}.csv"


def month_window(month):
    """UTC [start, end) epoch-millisecond bounds for a 'YYYY-MM' month."""
    year, mon = (int(part) for part in month.split("-"))
    start = int(datetime(year, mon, 1, tzinfo=timezone.utc).timestamp()) * 1000
    if mon == 12:
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp()) * 1000
    else:
        end = int(datetime(year, mon + 1, 1, tzinfo=timezone.utc).timestamp()) * 1000
    return start, end


def planned_scope(plan):
    """{asset: {kind: [months]}} restricted to the wave-B assets.

    Months come from the plan's ``admissible_months`` per series (H50 decision
    carried forward), never from a hard-coded calendar.
    """
    scope = {}
    for series in plan.get("series") or []:
        asset = series.get("asset")
        if asset in FORBIDDEN_ASSETS or asset not in EXPECTED_ASSETS:
            continue
        kind = series.get("kind")
        if kind not in KINDS:
            continue
        months = [m for m in (series.get("admissible_months") or []) if m]
        scope.setdefault(asset, {})[kind] = list(dict.fromkeys(months))
    return scope


def expected_panels(plan):
    """Ordered [(asset, symbol, kind, months, filename)] for the 4 panels."""
    symbol_map = plan.get("symbol_map") or {}
    out = []
    for asset in EXPECTED_ASSETS:
        symbol = symbol_map.get(asset)
        for kind in KINDS:
            months = (planned_scope(plan).get(asset) or {}).get(kind) or []
            out.append((asset, symbol, kind, months, panel_filename(symbol, kind)))
    return out


def index_records(h52_audit):
    """{(asset, kind, month): record} from the H52 acquisition audit."""
    out = {}
    for rec in h52_audit.get("records") or []:
        key = (rec.get("asset"), rec.get("kind"), rec.get("month"))
        out[key] = rec
    return out


def plan_record_keys(scope):
    keys = set()
    for asset in EXPECTED_ASSETS:
        for kind in KINDS:
            for month in (scope.get(asset) or {}).get(kind) or []:
                keys.add((asset, kind, month))
    return keys


def scope_problems(h52_audit, plan, h50_trim):
    """Pre-declared scope guard. Returns a list of human-readable problems."""
    problems = []
    if h52_audit.get("verdict") != "WAVEB_ACQUISITION_COMPLETE":
        problems.append(
            f"h52_verdict={h52_audit.get('verdict')!r} is not WAVEB_ACQUISITION_COMPLETE"
        )
    if h52_audit.get("hypothesis") != "H52":
        problems.append(f"h52_hypothesis={h52_audit.get('hypothesis')!r}")
    records = h52_audit.get("records") or []
    if len(records) != EXPECTED_RECORDS:
        problems.append(f"h52_record_count={len(records)} != {EXPECTED_RECORDS}")
    if _canonical_sha256(records) != H52_RECORDS_CANONICAL_SHA256:
        problems.append("h52_records_canonical_sha256 mismatch")
    if plan.get("hypothesis") != "H51":
        problems.append(f"plan_hypothesis={plan.get('hypothesis')!r}")

    scope = planned_scope(plan)
    if sorted(scope) != list(EXPECTED_ASSETS):
        problems.append(f"planned_asset_set={sorted(scope)} != {list(EXPECTED_ASSETS)}")
    for asset in EXPECTED_ASSETS:
        kinds = sorted(scope.get(asset) or {})
        if kinds != sorted(KINDS):
            problems.append(f"{asset}_planned_kinds={kinds}")
        n = sum(len((scope.get(asset) or {}).get(k) or []) for k in KINDS)
        if n != EXPECTED_FILES_PER_ASSET[asset]:
            problems.append(
                f"{asset}_planned_files={n} != {EXPECTED_FILES_PER_ASSET[asset]}"
            )

    records_index = index_records(h52_audit)
    planned_keys = plan_record_keys(scope)
    missing = sorted(planned_keys - set(records_index))
    if missing:
        problems.append(f"planned_months_without_h52_record={len(missing)}")
    extra = sorted(
        k for k in records_index if k[0] in EXPECTED_ASSETS and k not in planned_keys
    )
    if extra:
        problems.append(f"h52_records_outside_plan={len(extra)}")
    if len(planned_keys) != EXPECTED_RECORDS:
        problems.append(f"planned_keys={len(planned_keys)} != {EXPECTED_RECORDS}")
    if len(expected_panels(plan)) != EXPECTED_PANELS:
        problems.append("expected_panel_count != 4")

    declared = (h50_trim.get("scope_declaration") or {}).get(
        "admissible_months_by_asset"
    ) or {}
    for asset in EXPECTED_ASSETS:
        want = sorted(declared.get(asset) or [])
        have = sorted((scope.get(asset) or {}).get("klines") or [])
        if want and want != have:
            problems.append(f"{asset}_months_disagree_with_h50_trim")
    return problems


def parse_archive(path, kind):
    """Re-validate an archived monthly CSV. Returns (header, rows) or raises."""
    with zipfile.ZipFile(path) as zf:
        members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"expected exactly one csv member, found {len(members)}")
        text = zf.read(members[0]).decode("utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("empty csv")
    header_field = "open_time" if kind == "klines" else "calc_time"
    expected = KLINES_FIELDS if kind == "klines" else FUNDING_FIELDS
    if lines[0].split(",")[0].strip() != header_field:
        raise ValueError(f"unexpected header first field {lines[0].split(',')[0]!r}")
    if [c.strip() for c in lines[0].split(",")] != expected:
        raise ValueError("unexpected csv header")
    rows = []
    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) != len(expected):
            raise ValueError(f"row field count {len(fields)} != {len(expected)}")
        ts_index = 0
        if kind == "funding" and fields[0].strip() == "symbol":
            continue
        try:
            ts = int(fields[ts_index].strip())
        except ValueError as exc:
            raise ValueError(f"non-integer timestamp {fields[ts_index]!r}") from exc
        if kind == "klines":
            for value in fields[1:]:
                float(value)
        else:
            int(fields[1])
            float(fields[2])
        rows.append((ts, fields))
    if not rows:
        raise ValueError("no data rows")
    stamps = [ts for ts, _ in rows]
    if stamps != sorted(stamps):
        raise ValueError("timestamps not non-decreasing")
    return [c.strip() for c in lines[0].split(",")], rows


def normalize_series(records, cache_dir, asset, symbol, kind):
    """Normalize one (asset, kind) series. Returns a result dict, never raises."""
    rows_out = []
    months_seen = []
    files_ok = 0
    files_bad = []
    out_of_window = 0
    duplicate_ts = 0
    raw_rows = 0
    seen = set()
    for rec in records:
        month = rec.get("month")
        path = Path(cache_dir) / Path(rec.get("archive_path") or "")
        entry = {
            "month": month,
            "path": str(Path(rec.get("archive_path") or "")),
            "expected_sha256": rec.get("sha256"),
            "http_status": rec.get("http_status"),
            "content_ok_h52": bool(rec.get("content_ok")),
        }
        if not path.exists():
            entry.update(status="MISSING", detail="cache file absent")
            files_bad.append(entry)
            continue
        actual = _file_sha256(path)
        entry["actual_sha256"] = actual
        if actual != rec.get("sha256"):
            entry.update(status="SHA256_MISMATCH", detail="cache file differs from H52")
            files_bad.append(entry)
            continue
        try:
            header, rows = parse_archive(path, kind)
        except Exception as exc:  # noqa: BLE001 - reported, never repaired
            entry.update(status="CONTENT_INVALID", detail=str(exc))
            files_bad.append(entry)
            continue
        start, end = month_window(month)
        kept = []
        for ts, fields in rows:
            if ts < start or ts >= end:
                out_of_window += 1
                continue
            if ts in seen:
                duplicate_ts += 1
            seen.add(ts)
            kept.append(fields)
        raw_rows += len(rows)
        rows_out.extend(kept)
        months_seen.append(month)
        files_ok += 1
        entry.update(
            status="OK",
            n_rows=len(rows),
            n_rows_in_window=len(kept),
            header=header,
            first_timestamp=rows[0][0],
            last_timestamp=rows[-1][0],
        )
    return {
        "asset": asset,
        "symbol": symbol,
        "kind": kind,
        "rows": rows_out,
        "months_seen": sorted(months_seen),
        "n_files_ok": files_ok,
        "n_files_bad": len(files_bad),
        "bad_files": files_bad,
        "n_rows_in": raw_rows,
        "n_rows_out": len(rows_out),
        "n_rows_out_of_window": out_of_window,
        "n_duplicate_timestamps": duplicate_ts,
        "files": [
            {
                "month": rec.get("month"),
                "n_csv_rows": rec.get("n_csv_rows"),
                "sha256": rec.get("sha256"),
            }
            for rec in records
        ],
    }


def render_panel(symbol, kind, rows_out):
    header = KLINES_HEADER if kind == "klines" else FUNDING_HEADER
    if kind == "funding":
        body = [f"{symbol}," + ",".join(fields) for fields in rows_out]
    else:
        body = [",".join(fields) for fields in rows_out]
    return header + "\n" + "\n".join(body) + "\n"


def evaluate_verdict(scope_problems_found, series_results, plan):
    """Pre-declared verdict rule (section 5, outcome-blind)."""
    if scope_problems_found:
        return SCOPE_MISMATCH
    panels = expected_panels(plan)
    if len(panels) != EXPECTED_PANELS:
        return SCOPE_MISMATCH
    for (asset, _symbol, kind, months, _name), result in zip(panels, series_results):
        if result["n_files_bad"]:
            return INCOMPLETE
        if sorted(result["months_seen"]) != sorted(months):
            return INCOMPLETE
        if result["n_rows_out_of_window"] or result["n_duplicate_timestamps"]:
            return INCOMPLETE
        if result["n_rows_out"] != result["n_rows_in"]:
            return INCOMPLETE
        if result["n_files_ok"] != len(months):
            return INCOMPLETE
    return COMPLETE


def build(plan, h52_audit, h50_trim, cache_dir):
    """Pure-ish assembly: reconcile inputs and render panels in memory."""
    problems = scope_problems(h52_audit, plan, h50_trim)
    scope = planned_scope(plan)
    symbol_map = plan.get("symbol_map") or {}
    records_index = index_records(h52_audit)
    series_results = []
    rendered = []
    for asset, symbol, kind, months, name in expected_panels(plan):
        asset_months = (scope.get(asset) or {}).get(kind) or []
        records = [
            records_index[(asset, kind, month)]
            for month in asset_months
            if (asset, kind, month) in records_index
        ]
        result = normalize_series(records, cache_dir, asset, symbol, kind)
        series_results.append(result)
        rendered.append(
            {
                "asset": asset,
                "symbol": symbol_map.get(asset) or symbol,
                "kind": kind,
                "months": months,
                "filename": name,
                "text": render_panel(symbol, kind, result["rows"]),
            }
        )
    verdict = evaluate_verdict(problems, series_results, plan)
    return {
        "scope_problems": problems,
        "series_results": series_results,
        "panels": rendered,
        "verdict": verdict,
    }


def frozen_hashes():
    out = {}
    for name, expected in EXPECTED_FROZEN_SHA256.items():
        path = {
            "canonical_forward_block": CANONICAL_FORWARD_BLOCK,
            "h10_fresh_block": H10_FRESH_BLOCK,
            "universe_frontier": UNIVERSE_FRONTIER,
            "grid_v3_config": GRID_V3_CONFIG,
        }[name]
        actual = _file_sha256(path) if path.exists() else None
        out[name] = {
            "path": str(path.relative_to(ROOT)),
            "expected": expected,
            "actual": actual,
            "match": actual == expected,
        }
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="write panels + audit")
    args = parser.parse_args(argv)

    if not H52_AUDIT.exists() or not H51A_PLAN.exists():
        print(f"[plan] missing pinned input; H52 audit exists={H52_AUDIT.exists()}")
        return 2
    if PREREG.exists() is False:
        print(f"[plan] missing preregistration {PREREG.relative_to(ROOT)}")
        return 2

    h52 = _load_json(H52_AUDIT)
    plan = _load_json(H51A_PLAN)
    h50 = _load_json(H50_TRIM) if H50_TRIM.exists() else {}

    pinned = {
        "h52_audit_file_sha256": _file_sha256(H52_AUDIT) == H52_AUDIT_FILE_SHA256,
        "h52_records_canonical_sha256": _canonical_sha256(h52.get("records") or [])
        == H52_RECORDS_CANONICAL_SHA256,
        "h51a_plan_file_sha256": _file_sha256(H51A_PLAN) == H51A_PLAN_FILE_SHA256,
        "h50_trim_file_sha256": (not H50_TRIM.exists())
        or _file_sha256(H50_TRIM) == H50_TRIM_FILE_SHA256,
        "h50_trim_canonical_sha256": (not h50)
        or h50.get("trim_canonical_sha256") == H50_TRIM_CANONICAL_SHA256,
    }
    frozen = frozen_hashes()

    result = build(plan, h52, h50, CACHE_DIR)
    print(f"[plan] pinned={pinned}")
    print(f"[plan] frozen_match={all(v['match'] for v in frozen.values())}")
    print(f"[plan] scope_problems={result['scope_problems']}")
    for series in result["series_results"]:
        print(
            f"[plan] {series['asset']}/{series['kind']}: files_ok={series['n_files_ok']}"
            f" bad={series['n_files_bad']} months={len(series['months_seen'])}"
            f" rows_in={series['n_rows_in']} rows_out={series['n_rows_out']}"
            f" oow={series['n_rows_out_of_window']}"
            f" dup={series['n_duplicate_timestamps']}"
        )
    print(f"[plan] verdict={result['verdict']}")

    if not args.execute:
        print("[plan] dry run; pass --execute to write panels and audit")
        return 0

    if not all(pinned.values()):
        print("[abort] pinned input digest mismatch; no panel written", file=sys.stderr)
        return 1

    PANEL_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    panel_evidence = []
    for panel in result["panels"]:
        path = PANEL_DIR / panel["filename"]
        blob = panel["text"].encode("utf-8")
        path.write_bytes(blob)
        panel_evidence.append(
            {
                "asset": panel["asset"],
                "symbol": panel["symbol"],
                "kind": panel["kind"],
                "path": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "n_bytes": len(blob),
                "n_rows": len(panel["text"].strip().splitlines()) - 1,
                "months": panel["months"],
                "n_months": len(panel["months"]),
            }
        )

    stamp = _utc_now()
    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "exploratory_only": True,
        "confirmatory_claim_allowed": False,
        "promotion_allowed": False,
        "computed_utc": stamp,
        "preregistration": str(PREREG.relative_to(ROOT)),
        "verdict": result["verdict"],
        "verdict_rule": (
            "SCOPE_MISMATCH on any pinned-digest, asset-set, month-set or panel-count "
            "failure; INCOMPLETE on any cache sha256 mismatch, content-invalid archive, "
            "uncovered month, out-of-window row, duplicate timestamp or row-identity "
            "failure; COMPLETE only when all 166 files reconcile into 4 panels."
        ),
        "method": (
            "Read-only normalization of the 166 H52 wave-B archives into 4 "
            "DISP-003-schema panels; per-file sha256 re-verified against H52, content "
            "re-validated, rows restricted to their source-month UTC window, exact row "
            "accounting, no interpolation/backfill and no network I/O."
        ),
        "pinned_input_checks": pinned,
        "audited_input_sha256": {
            "h52_wave_b_acquisition": H52_AUDIT_FILE_SHA256,
            "h51a_normalization_plan": H51A_PLAN_FILE_SHA256,
            "h50_wave_b_trim": H50_TRIM_FILE_SHA256,
        },
        "h52_records_canonical_sha256": H52_RECORDS_CANONICAL_SHA256,
        "h50_trim_canonical_sha256": H50_TRIM_CANONICAL_SHA256,
        "scope_problems": result["scope_problems"],
        "scope_checks": {
            "h52_verdict_is_complete": h52.get("verdict") == "WAVEB_ACQUISITION_COMPLETE",
            "asset_set_is_ark_astr": sorted(planned_scope(plan)) == list(EXPECTED_ASSETS),
            "planned_files_per_asset_match": all(
                sum(
                    len((planned_scope(plan).get(a) or {}).get(k) or [])
                    for k in KINDS
                )
                == EXPECTED_FILES_PER_ASSET[a]
                for a in EXPECTED_ASSETS
            ),
            "planned_keys_equal_h52_records": len(plan_record_keys(planned_scope(plan)))
            == EXPECTED_RECORDS,
            "panel_count_is_4": len(result["panels"]) == EXPECTED_PANELS,
        },
        "series": [
            {k: v for k, v in series.items() if k != "rows"}
            for series in result["series_results"]
        ],
        "panels": panel_evidence,
        "reconciliation": {
            "n_files_expected": EXPECTED_RECORDS,
            "n_files_reconciled": sum(
                s["n_files_ok"] for s in result["series_results"]
            ),
            "n_files_bad": sum(s["n_files_bad"] for s in result["series_results"]),
            "n_rows_written": sum(p["n_rows"] for p in panel_evidence),
            "n_rows_in": sum(s["n_rows_in"] for s in result["series_results"]),
            "n_rows_out_of_window": sum(
                s["n_rows_out_of_window"] for s in result["series_results"]
            ),
            "n_duplicate_timestamps": sum(
                s["n_duplicate_timestamps"] for s in result["series_results"]
            ),
            "row_accounting_identity_holds": sum(p["n_rows"] for p in panel_evidence)
            == sum(s["n_rows_in"] for s in result["series_results"]),
            "per_asset": {
                asset: {
                    "months_klines": len(
                        (planned_scope(plan).get(asset) or {}).get("klines") or []
                    ),
                    "months_funding": len(
                        (planned_scope(plan).get(asset) or {}).get("funding") or []
                    ),
                    "files_ok": sum(
                        s["n_files_ok"]
                        for s in result["series_results"]
                        if s["asset"] == asset
                    ),
                }
                for asset in EXPECTED_ASSETS
            },
        },
        "frozen_hashes_verified": {
            "all_match": all(v["match"] for v in frozen.values()),
            "details": frozen,
        },
        "network_io": "none",
        "non_claims": [
            "A normalized panel is not market evidence and is not an economic result.",
            "No returns, spreads, dispersion states, p-values, costs or inference computed.",
            "No candidate promoted; no confirmatory claim; H10 gate unchanged and date-gated to 2026-11-30.",
            "Wave A (7 assets, 644 files) is out of scope here: its raw bytes are absent in this checkout.",
            "Malformed or missing archives are reported, never interpolated, backfilled or forward-filled.",
            "Does not alter any frozen DISP-001/002/003 artifact, config, ledger, existing panel or forward block, and does not unlock H1/H6/H7/H10.",
            "A green test suite proves only what the tests cover.",
        ],
    }
    audit_path = AUDIT_DIR / f"panel_wave_b_normalization_{stamp.replace(':', '')}.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"[done] verdict={result['verdict']}")
    print(f"[done] panels={PANEL_DIR.relative_to(ROOT)}")
    print(f"[done] audit={audit_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
