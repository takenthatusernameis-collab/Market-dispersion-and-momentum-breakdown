#!/usr/bin/env python3
"""Wave-A extension panel normalization (DISP-003-PANELNORM-WAVEA-001, H56).

Normalizes exactly the H49-acquired wave-A archives (ALICE, ANKR, APE, API3,
APT, AR, ARPA) into 14 committed DISP-003-schema panel CSVs and records
per-file reconciliation plus a descriptive per-month breadth inventory.

Hard properties:
  * Pinned input digests are verified before any network call or panel byte.
  * Only the 644 URLs pinned in the H49 acquisition audit are fetched; the URL
    allowlist is derived from that committed artifact, never from a listing.
  * Every fetched byte string must hash to the H49-recorded sha256; a mismatch
    is a reported reproducibility failure, never patched.
  * Content is re-validated (one CSV member, documented header, >=1 data row,
    non-decreasing integer timestamps); malformed input is reported, never
    repaired, interpolated or backfilled.
  * Only rows inside their source month's UTC window contribute; the union of
    contributing months must equal the declared study months.
  * Row accounting is exact: rows written == sum of contributing n_csv_rows.
  * Duplicate timestamps are reported and fail completeness, never collapsed.
  * No outcome, return, spread, state, p-value, cost or inference is computed.

Usage:
    python3 scripts/panel_wave_a_normalization.py             # plan only, no I/O
    python3 scripts/panel_wave_a_normalization.py --execute   # fetch + write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEA-001"
EXP_DIR = ROOT / "artifacts" / EXP
PANEL_DIR = EXP_DIR / "panels"
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELNORM_WAVEA_001_v1.md"

H49_AUDIT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEA-001"
    / "integrity_audit"
    / "panel_wave_a_acquisition_20261118T211130Z.json"
)
CACHE_DIR = ROOT / "data" / "panel_archive_wave_a"

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
LEGACY_PANEL_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003" / "data" / "panels"
WAVEB_PANEL_DIR = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELNORM-WAVEB-001"
    / "panels"
)

EXPECTED_FROZEN_SHA256 = {
    "canonical_forward_block": "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "h10_fresh_block": "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
    "universe_frontier": "9ba08f3f7718815dae95b92e7b3011cdb16f3bac2ceddba6b7ec914744ba4f4e",
    "grid_v3_config": "1ff4c1f20958e57b30dd4054a43c1fa0dd86faa4aa3bcd10191158b066302176",
}

H49_AUDIT_FILE_SHA256 = "37605fc803451c910014085d3903fcd1978df2afa4576f692e6b00b1b027cbf1"
H49_RECORDS_CANONICAL_SHA256 = "f94072df03e2b15c950c244e6938d75048bc8f90fd616b20022848048ceb758d"

EXPERIMENT_ID = EXP
AUDIT_ID = "H004V106_PANELNORM_WAVEA_001"
HYPOTHESIS = "H56"

SOURCE_BASE = "https://data.binance.vision"
KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"
KLINES_FIELDS = KLINES_HEADER.split(",")
FUNDING_FIELDS = FUNDING_HEADER.split(",")[1:]

KINDS = ("klines", "funding")
EXPECTED_ASSETS = ("alice", "ankr", "ape", "api3", "apt", "ar", "arpa")
FORBIDDEN_ASSETS = ("ark", "astr", "alpha")
EXPECTED_RECORDS = 644
EXPECTED_FILES_PER_ASSET = 92
EXPECTED_PANELS = 14
FRESH_WINDOW_START = "2025-01"
FRESH_WINDOW_END = "2026-10"

SCOPE_MISMATCH = "PANELNORM_WAVEA_SCOPE_MISMATCH"
INCOMPLETE = "PANELNORM_WAVEA_INCOMPLETE"
COMPLETE = "PANELNORM_WAVEA_COMPLETE"


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


def declared_months(h49_audit):
    """Study months from the H49 scope declaration, never a hard-coded calendar."""
    decl = h49_audit.get("scope_declaration") or {}
    return [m for m in (decl.get("study_months") or []) if m]


def planned_scope(h49_audit):
    """({asset: {kind: [months]}}) derived from the H49 declaration and records."""
    months = declared_months(h49_audit)
    present = {}
    for rec in h49_audit.get("records") or []:
        asset = rec.get("asset")
        if asset in FORBIDDEN_ASSETS or asset not in EXPECTED_ASSETS:
            continue
        present.setdefault(asset, {}).setdefault(rec.get("kind"), set()).add(
            rec.get("month")
        )
    scope = {}
    for asset in EXPECTED_ASSETS:
        scope[asset] = {}
        for kind in KINDS:
            served = present.get(asset, {}).get(kind) or set()
            scope[asset][kind] = [m for m in months if m in served]
    return scope


def symbol_map(h49_audit):
    out = {}
    for rec in h49_audit.get("records") or []:
        asset = rec.get("asset")
        if asset in EXPECTED_ASSETS and rec.get("symbol") and asset not in out:
            out[asset] = rec["symbol"]
    return out


def expected_panels(h49_audit):
    """Ordered [(asset, symbol, kind, months, filename)] for the 14 panels."""
    scope = planned_scope(h49_audit)
    symbols = symbol_map(h49_audit)
    out = []
    for asset in EXPECTED_ASSETS:
        symbol = symbols.get(asset) or f"{asset.upper()}USDT"
        for kind in KINDS:
            months = (scope.get(asset) or {}).get(kind) or []
            out.append((asset, symbol, kind, months, panel_filename(symbol, kind)))
    return out


def index_records(h49_audit):
    """{(asset, kind, month): record} from the H49 acquisition audit."""
    out = {}
    for rec in h49_audit.get("records") or []:
        out[(rec.get("asset"), rec.get("kind"), rec.get("month"))] = rec
    return out


def scope_problems(h49_audit, records_pin=None):
    """Pre-declared scope guard. Returns a list of human-readable problems."""
    if records_pin is None:
        records_pin = H49_RECORDS_CANONICAL_SHA256
    problems = []
    if h49_audit.get("hypothesis") != "H49":
        problems.append(f"h49_hypothesis={h49_audit.get('hypothesis')!r}")
    if h49_audit.get("verdict") != "WAVEA_ACQUISITION_COMPLETE":
        problems.append(
            f"h49_verdict={h49_audit.get('verdict')!r} is not WAVEA_ACQUISITION_COMPLETE"
        )
    records = h49_audit.get("records") or []
    if len(records) != EXPECTED_RECORDS:
        problems.append(f"h49_record_count={len(records)} != {EXPECTED_RECORDS}")
    if _canonical_sha256(records) != records_pin:
        problems.append("h49_records_canonical_sha256 mismatch")

    scope = planned_scope(h49_audit)
    if sorted(scope) != list(EXPECTED_ASSETS):
        problems.append(f"planned_asset_set={sorted(scope)} != {list(EXPECTED_ASSETS)}")
    months = declared_months(h49_audit)
    if len(months) != 46:
        problems.append(f"declared_study_months={len(months)} != 46")
    for asset in EXPECTED_ASSETS:
        for kind in KINDS:
            n = len((scope.get(asset) or {}).get(kind) or [])
            if n != EXPECTED_FILES_PER_ASSET // len(KINDS):
                problems.append(
                    f"{asset}/{kind}_planned_files={n} != "
                    f"{EXPECTED_FILES_PER_ASSET // len(KINDS)}"
                )
    for rec in records:
        if rec.get("asset") in FORBIDDEN_ASSETS:
            problems.append(f"forbidden_asset_in_records={rec.get('asset')}")
            break
        url = rec.get("archive_url") or ""
        if not url.startswith(SOURCE_BASE + "/"):
            problems.append(f"record_url_off_documented_base={url!r}")
            break
    if len(expected_panels(h49_audit)) != EXPECTED_PANELS:
        problems.append("expected_panel_count != 14")
    return problems


def parse_archive_bytes(blob, kind):
    """Re-validate an archived monthly CSV from bytes. Returns (header, rows)."""
    import io

    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
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
        if kind == "funding" and fields[0].strip() == "symbol":
            continue
        try:
            ts = int(fields[0].strip())
        except ValueError as exc:
            raise ValueError(f"non-integer timestamp {fields[0]!r}") from exc
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


def fetch_archives(h49_audit, cache_dir, opener=None, max_attempts=2):
    """Fetch exactly the pinned H49 URLs, verifying each recorded sha256."""
    opener = opener or (lambda url: urllib.request.urlopen(url, timeout=60))
    cache_dir = Path(cache_dir)
    results = []
    for rec in h49_audit.get("records") or []:
        rel = rec.get("archive_path") or ""
        url = f"{SOURCE_BASE}/{rel}"
        entry = {
            "asset": rec.get("asset"),
            "kind": rec.get("kind"),
            "month": rec.get("month"),
            "archive_path": rel,
            "archive_url": url,
            "url_is_pinned": url == rec.get("archive_url"),
        }
        target = cache_dir / rel
        blob = None
        error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with opener(url) as response:
                    blob = response.read()
                    entry["http_status"] = getattr(response, "status", 200)
                break
            except Exception as exc:  # noqa: BLE001 - reported, retried once
                error = f"{type(exc).__name__}: {exc}"
        if blob is None:
            entry.update(status="FETCH_FAILED", error=error, sha256_match=False)
            results.append(entry)
            continue
        actual = hashlib.sha256(blob).hexdigest()
        entry["sha256_actual"] = actual
        entry["sha256_expected"] = rec.get("sha256")
        entry["sha256_match"] = actual == rec.get("sha256")
        entry["n_bytes"] = len(blob)
        if not entry["sha256_match"]:
            entry.update(status="SHA256_MISMATCH", error=None)
            results.append(entry)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
        entry["status"] = "OK"
        results.append(entry)
    return results


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
            "content_ok_h49": bool(rec.get("content_ok")),
        }
        if not path.exists():
            entry.update(status="MISSING", detail="cache file absent")
            files_bad.append(entry)
            continue
        actual = _file_sha256(path)
        entry["actual_sha256"] = actual
        if actual != rec.get("sha256"):
            entry.update(status="SHA256_MISMATCH", detail="cache file differs from H49")
            files_bad.append(entry)
            continue
        try:
            header, rows = parse_archive_bytes(path.read_bytes(), kind)
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


def evaluate_verdict(scope_problems_found, series_results, h49_audit):
    """Pre-declared verdict rule (preregistration, outcome-blind)."""
    if scope_problems_found:
        return SCOPE_MISMATCH
    if len(expected_panels(h49_audit)) != EXPECTED_PANELS:
        return SCOPE_MISMATCH
    for (asset, _symbol, kind, months, _name), result in zip(
        expected_panels(h49_audit), series_results
    ):
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


def build(h49_audit, cache_dir, records_pin=None):
    """Pure-ish assembly: reconcile inputs and render panels in memory."""
    problems = scope_problems(h49_audit, records_pin=records_pin)
    records_index = index_records(h49_audit)
    scope = planned_scope(h49_audit)
    symbols = symbol_map(h49_audit)
    series_results = []
    rendered = []
    for asset, symbol, kind, months, name in expected_panels(h49_audit):
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
                "symbol": symbols.get(asset) or symbol,
                "kind": kind,
                "months": months,
                "filename": name,
                "text": render_panel(symbol, kind, result["rows"]),
            }
        )
    verdict = evaluate_verdict(problems, series_results, h49_audit)
    return {
        "scope_problems": problems,
        "series_results": series_results,
        "panels": rendered,
        "verdict": verdict,
    }


def panel_inventory_breadth(panel_dirs, months):
    """Per-month count of assets with a klines panel in the declared inventory.

    Coverage accounting only: an asset contributes to a month when its klines
    panel covers that month. No returns, states or outcome are computed.
    """
    files = _inventory_files(panel_dirs)
    out = {}
    for month in months:
        start, end = month_window(month)
        n = 0
        for _asset, _symbol, path in files:
            if _klines_month_stamps(path, start, end):
                n += 1
        out[month] = n
    return out


def _inventory_files(panel_dirs):
    """[(asset, symbol, klines_path)] across the declared committed panel dirs."""
    files = []
    for label, directory in panel_dirs:
        directory = Path(directory)
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("binance_klines_*.csv")):
            symbol = path.stem.split("binance_klines_")[-1]
            files.append((symbol, symbol, path))
    return files


def _klines_month_stamps(path, start, end):
    count = 0
    with open(path, "r", encoding="utf-8") as handle:
        handle.readline()
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                ts = int(line.split(",", 1)[0])
            except ValueError:
                continue
            if start <= ts < end:
                count += 1
    return count


def frozen_hashes():
    paths = {
        "canonical_forward_block": CANONICAL_FORWARD_BLOCK,
        "h10_fresh_block": H10_FRESH_BLOCK,
        "universe_frontier": UNIVERSE_FRONTIER,
        "grid_v3_config": GRID_V3_CONFIG,
    }
    out = {}
    for name, expected in EXPECTED_FROZEN_SHA256.items():
        path = paths[name]
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
    parser.add_argument("--execute", action="store_true", help="fetch + write panels")
    args = parser.parse_args(argv)

    if not H49_AUDIT.exists():
        print("[plan] missing pinned H49 audit", file=sys.stderr)
        return 2
    if not PREREG.exists():
        print(f"[plan] missing preregistration {PREREG.relative_to(ROOT)}", file=sys.stderr)
        return 2

    h49 = _load_json(H49_AUDIT)
    pinned = {
        "h49_audit_file_sha256": _file_sha256(H49_AUDIT) == H49_AUDIT_FILE_SHA256,
        "h49_records_canonical_sha256": _canonical_sha256(h49.get("records") or [])
        == H49_RECORDS_CANONICAL_SHA256,
    }
    frozen = frozen_hashes()

    if not args.execute:
        problems = scope_problems(h49)
        print(f"[plan] pinned={pinned}")
        print(f"[plan] frozen_match={all(v['match'] for v in frozen.values())}")
        print(f"[plan] scope_problems={problems}")
        print(
            f"[plan] panels={len(expected_panels(h49))} records={len(h49.get('records') or [])}"
        )
        print("[plan] dry run; pass --execute to fetch, write panels and audit")
        return 0

    if not all(pinned.values()):
        print("[abort] pinned input digest mismatch; nothing fetched", file=sys.stderr)
        return 1

    fetch_results = fetch_archives(h49, CACHE_DIR)
    fetched_ok = sum(1 for r in fetch_results if r.get("status") == "OK")
    fetch_bad = [r for r in fetch_results if r.get("status") != "OK"]
    print(f"[fetch] ok={fetched_ok} bad={len(fetch_bad)}")

    result = build(h49, CACHE_DIR)
    for series in result["series_results"]:
        print(
            f"[plan] {series['asset']}/{series['kind']}: files_ok={series['n_files_ok']}"
            f" bad={series['n_files_bad']} months={len(series['months_seen'])}"
            f" rows_in={series['n_rows_in']} rows_out={series['n_rows_out']}"
            f" oow={series['n_rows_out_of_window']}"
            f" dup={series['n_duplicate_timestamps']}"
        )
    print(f"[plan] verdict={result['verdict']}")

    if fetch_bad or result["verdict"] != COMPLETE:
        print("[abort] reconciliation failed; no panel written", file=sys.stderr)
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

    months = declared_months(h49)
    inventory = [
        ("committed_disp003_panels", LEGACY_PANEL_DIR),
        ("h53_wave_b_panels", WAVEB_PANEL_DIR),
        ("h56_wave_a_panels", PANEL_DIR),
    ]
    breadth = panel_inventory_breadth(inventory, months)
    fresh = [m for m in months if FRESH_WINDOW_START <= m <= FRESH_WINDOW_END]
    fresh_breadth = {m: breadth[m] for m in fresh}
    max_breadth = max(breadth.values()) if breadth else 0

    stamp = _utc_now()
    given = (h49.get("computed_utc") or "")
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
            "SCOPE_MISMATCH on any pinned-digest, asset-set, month-set, URL-base or "
            "panel-count failure; INCOMPLETE on any fetch/digest/content failure, "
            "uncovered month, out-of-window row, duplicate timestamp or row-identity "
            "failure; COMPLETE only when all 644 H49 archives reconcile into 14 panels."
        ),
        "method": (
            "Re-fetch of exactly the 644 H49-pinned wave-A archives (each byte string "
            "must hash to the H49-recorded sha256) followed by read-only normalization "
            "into 14 DISP-003-schema panels: content re-validation, source-month UTC "
            "window restriction, exact row accounting, no interpolation/backfill, plus "
            "descriptive per-month coverage breadth over the declared panel inventory."
        ),
        "pinned_input_checks": pinned,
        "audited_inputs": {
            "h49_wave_a_acquisition": str(H49_AUDIT.relative_to(ROOT)),
            "preregistration": str(PREREG.relative_to(ROOT)),
        },
        "audited_input_sha256": {
            "h49_wave_a_acquisition": H49_AUDIT_FILE_SHA256,
            "h49_records_canonical": H49_RECORDS_CANONICAL_SHA256,
        },
        "h49_acquisition_computed_utc": given,
        "scope_declaration": {
            "assets": list(EXPECTED_ASSETS),
            "forbidden_assets": list(FORBIDDEN_ASSETS),
            "kinds": list(KINDS),
            "n_study_months": len(months),
            "study_months": months,
            "expected_files": EXPECTED_RECORDS,
            "expected_panels": EXPECTED_PANELS,
            "fresh_window": [FRESH_WINDOW_START, FRESH_WINDOW_END],
        },
        "scope_problems": result["scope_problems"],
        "scope_checks": {
            "h49_verdict_is_complete": h49.get("verdict") == "WAVEA_ACQUISITION_COMPLETE",
            "asset_set_is_wave_a_7": sorted(planned_scope(h49)) == list(EXPECTED_ASSETS),
            "planned_files_per_asset_is_92": all(
                sum(len((planned_scope(h49).get(a) or {}).get(k) or []) for k in KINDS)
                == EXPECTED_FILES_PER_ASSET
                for a in EXPECTED_ASSETS
            ),
            "panel_count_is_14": len(result["panels"]) == EXPECTED_PANELS,
            "all_urls_pinned_by_h49": all(r.get("url_is_pinned") for r in fetch_results),
        },
        "fetch": {
            "n_expected": len(fetch_results),
            "n_ok": fetched_ok,
            "n_bad": len(fetch_bad),
            "bad": fetch_bad,
            "all_digests_match_h49": all(
                r.get("sha256_match") for r in fetch_results
            ),
            "total_bytes": sum(r.get("n_bytes") or 0 for r in fetch_results),
        },
        "series": [
            {k: v for k, v in series.items() if k != "rows"}
            for series in result["series_results"]
        ],
        "panels": panel_evidence,
        "reconciliation": {
            "n_files_expected": EXPECTED_RECORDS,
            "n_files_reconciled": sum(s["n_files_ok"] for s in result["series_results"]),
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
                    "months_klines": len((planned_scope(h49).get(asset) or {}).get("klines") or []),
                    "months_funding": len(
                        (planned_scope(h49).get(asset) or {}).get("funding") or []
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
        "coverage_breadth": {
            "panel_inventory": [
                {"label": label, "path": str(Path(directory).relative_to(ROOT))}
                for label, directory in inventory
            ],
            "definition": (
                "per study month, the number of assets with at least one klines "
                "observation inside that UTC month across the declared inventory "
                "(coverage accounting only; not a signal, state or outcome)"
            ),
            "per_month": breadth,
            "max_month_breadth": max_breadth,
            "n_months_breadth_ge_20": sum(1 for v in breadth.values() if v >= 20),
            "fresh_window_months": fresh,
            "fresh_window_breadth": fresh_breadth,
            "fresh_window_min_breadth": min(fresh_breadth.values()) if fresh_breadth else 0,
            "fresh_window_max_breadth": max(fresh_breadth.values()) if fresh_breadth else 0,
            "arity_requirement": 20,
            "arity_requirement_met_in_fresh_window": bool(fresh_breadth)
            and min(fresh_breadth.values()) >= 20,
        },
        "frozen_hashes_verified": {
            "all_match": all(v["match"] for v in frozen.values()),
            "details": frozen,
        },
        "network_io": "644 pinned keyless GETs to data.binance.vision only",
        "non_claims": [
            "A normalized panel is not market evidence and is not an economic result.",
            "No returns, spreads, dispersion states, p-values, costs or inference computed.",
            "No candidate promoted; no confirmatory claim; H10 gate unchanged and date-gated to 2026-11-30.",
            "Breadth counts are coverage accounting, not point-in-time rank truth and not an eligibility claim.",
            "Wave B (ARK/ASTR) and excluded ALPHA are out of scope; no wave-B or extra month fetched.",
            "Malformed, missing or digest-mismatched archives are reported, never interpolated, backfilled or forward-filled.",
            "The re-fetch reproduces the already-completed H49 acquisition; it is not a new attempt at a failed gate and is not fresh mechanism evidence.",
            "Does not alter any frozen DISP-001/002/003 artifact, config, ledger, committed panel or forward block.",
            "A green test suite proves only what the tests cover.",
        ],
    }
    audit_path = AUDIT_DIR / f"panel_wave_a_normalization_{stamp.replace(':', '')}.json"
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"[done] verdict={result['verdict']}")
    print(f"[done] panels={PANEL_DIR.relative_to(ROOT)}")
    print(f"[done] audit={audit_path.relative_to(ROOT)}")
    print(f"[done] fresh_window_breadth={fresh_breadth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
