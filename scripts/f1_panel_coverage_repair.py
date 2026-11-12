#!/usr/bin/env python3
"""Repair the F1 panel-coverage gap for DISPERSION-003 into a NEW experiment.

The lineage audit DISP-003-PANEL-COVERAGE-LINEAGE-001 (F1) found that four of
the 32 committed DISPERSION-003 panel symbols (1INCHUSDT, AAVEUSDT, ACHUSDT,
AGLDUSDT) have no Binance klines or funding monthly archives for 2025-01 ..
2026-09 (168 zips). This script fetches ONLY those missing keyless zips from the
free Binance Public Data Archive, rebuilds ONLY those four symbols' panels into a
new experiment directory, and reports the descriptive eligible-asset coverage
delta. It never writes to the committed DISPERSION-003 panels, raw archive or
any frozen artifact, and it computes no return, spread, state or inference.

Usage:
    python3 scripts/f1_panel_coverage_repair.py [--offline]

--offline skips the network fetch and rebuilds/reports from whatever zips are
already present under the new raw directory (useful for a deterministic re-run).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"

OLD_PANELS = ROOT / "artifacts" / OLD_EXP / "data" / "panels"
OLD_RAW = ROOT / "artifacts" / OLD_EXP / "data" / "raw" / "binance"
NEW_RAW = ROOT / "artifacts" / NEW_EXP / "data" / "raw" / "binance"
NEW_PANELS = ROOT / "artifacts" / NEW_EXP / "data" / "panels"
NEW_AUDIT = ROOT / "artifacts" / NEW_EXP / "integrity_audit"

CANONICAL_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block" / "forward_block_evaluation.json"

ARCHIVE = "https://data.binance.vision/data/futures/um"
SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]
GAP_START = "2025-01"
GAP_END = "2026-09"

KLINES_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore"
)
FUNDING_HEADER = "symbol,calc_time,funding_interval_hours,last_funding_rate"

REQUEST_TIMEOUT = 60
MAX_RETRIES = 4
BACKOFF_BASE = 2.0
SLEEP_BETWEEN = 0.2

# sha256 of the four affected committed kline panels, recorded by the lineage
# audit (DISP-003-PANEL-COVERAGE-LINEAGE-001). Used as a read-only drift check.
EXPECTED_OLD_KLINES_SHA256 = {
    "binance_klines_1INCHUSDT.csv": "9c2f21351bae85dcff364402b1d503dce882126514c6f6e786099ae6f57f7b67",
    "binance_klines_AAVEUSDT.csv": "61b506827d4c6b5d3ad30a46b8b1541089c30314b6c82d6f24440ec31e464cc4",
    "binance_klines_AGLDUSDT.csv": "9681ca2f3581a87b6ccb0a160ab6cd9377c6e09ea33374e80f95e3f9ae8ddc1d",
    "binance_klines_ACHUSDT.csv": "84cfb20aecefa3ddcc414547f84704b271d83d66812391b5efeb106532d7f6a6",
}

FROZEN_HASHES = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def month_range(start_ym: str, end_ym: str) -> list[str]:
    y, m = map(int, start_ym.split("-"))
    ey, em = map(int, end_ym.split("-"))
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def kline_url(symbol: str, ym: str) -> str:
    return f"{ARCHIVE}/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"


def funding_url(symbol: str, ym: str) -> str:
    return f"{ARCHIVE}/monthly/fundingRate/{symbol}/{symbol}-fundingRate-{ym}.zip"


def fetch_bytes(url: str) -> tuple[bytes | None, int | None, str | None]:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"Accept": "application/zip"})
            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = resp.read()
                return data, resp.getcode(), sha256_bytes(data)
        except HTTPError as exc:
            if exc.code == 404:
                return None, 404, "404_not_found"
            last_err = f"HTTP {exc.code}"
            if exc.code in (429, 502, 503, 504):
                time.sleep(BACKOFF_BASE ** attempt)
                continue
            return None, exc.code, last_err
        except (URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            time.sleep(BACKOFF_BASE ** attempt)
            continue
    return None, None, last_err or "exhausted_retries"


def _ym_key(p: Path) -> tuple[int, int]:
    parts = p.stem.split("-")
    return int(parts[-2]), int(parts[-1].split(".")[0])


def existing_months(raw_kind_dir: Path) -> set[str]:
    if not raw_kind_dir.exists():
        return set()
    out = set()
    for z in raw_kind_dir.glob("*/*.zip"):
        parts = z.stem.split("-")
        out.add(f"{int(parts[-2]):04d}-{int(parts[-1].split('.')[0]):02d}")
    return out


def seed_existing_zips() -> list[dict]:
    """Copy already-present monthly zips for the four symbols into the new raw dir.

    The committed raw archive (read-only) holds the pre-gap (2023..2024) and the
    post-gap (2026-10) months for these symbols. Copying them (never moving or
    modifying the originals) lets the rebuilt new panels span the full
    2023-01..2026-10 range, so coverage outside the gap is preserved. The copy is
    byte-identical (same sha256) to the committed zip.
    """
    copied: list[dict] = []
    for symbol in SYMBOLS:
        for kind, ext in (("klines", "klines"), ("funding", "funding")):
            src_dir = OLD_RAW / kind / symbol
            dst_dir = NEW_RAW / kind / symbol
            if not src_dir.exists():
                continue
            dst_dir.mkdir(parents=True, exist_ok=True)
            for src in sorted(src_dir.glob("*.zip")):
                dst = dst_dir / src.name
                if dst.exists():
                    continue
                shutil.copy2(src, dst)
                copied.append({
                    "symbol": symbol, "kind": kind, "raw_path": str(dst.relative_to(ROOT)),
                    "raw_sha256": sha256_file(dst), "status": "copied_from_old_raw",
                })
    return copied


def fetch_gap_zips(offline: bool) -> list[dict]:
    months = month_range(GAP_START, GAP_END)
    records: list[dict] = []
    for symbol in SYMBOLS:
        for kind, url_fn, ext in (
            ("klines", kline_url, "klines"),
            ("funding", funding_url, "funding"),
        ):
            raw_kind = NEW_RAW / kind / symbol
            raw_kind.mkdir(parents=True, exist_ok=True)
            for ym in months:
                rel = f"data/raw/binance/{kind}/{symbol}/{symbol}-{ext}-{ym}.zip"
                out = raw_kind / f"{symbol}-{ext}-{ym}.zip"
                if out.exists():
                    records.append({
                        "symbol": symbol, "kind": kind, "ym": ym,
                        "status": "present_on_disk", "raw_path": rel,
                        "raw_sha256": sha256_file(out),
                    })
                    continue
                if offline:
                    records.append({
                        "symbol": symbol, "kind": kind, "ym": ym,
                        "status": "absent_offline", "raw_path": rel,
                    })
                    continue
                data, status, sha = fetch_bytes(url_fn(symbol, ym))
                if data is None:
                    records.append({
                        "symbol": symbol, "kind": kind, "ym": ym,
                        "status": "missing" if status == 404 else "error",
                        "http_status": status, "error": None if status == 404 else sha,
                        "raw_path": rel,
                    })
                    time.sleep(SLEEP_BETWEEN)
                    continue
                out.write_bytes(data)
                records.append({
                    "symbol": symbol, "kind": kind, "ym": ym,
                    "status": "ok", "raw_path": rel, "raw_sha256": sha,
                    "rows": _count_zip_rows(data, kind),
                })
                time.sleep(SLEEP_BETWEEN)
    return records


def _count_zip_rows(data: bytes, kind: str) -> int:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = [n for n in zf.namelist() if n.endswith(".csv")]
            if not names:
                return 0
            lines = [ln for ln in zf.read(names[0]).decode("utf-8").splitlines() if ln.strip()]
            if lines and lines[0].startswith(("open_time,", "calc_time,", "symbol,")):
                lines = lines[1:]
            return len(lines)
    except (zipfile.BadZipFile, KeyError):
        return 0


def rebuild_panels() -> dict:
    """Rebuild ONLY the new experiment's four-symbol panels from its raw zips."""
    NEW_PANELS.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict] = {}
    total_rows = 0
    for kind, header in (("klines", KLINES_HEADER), ("funding", FUNDING_HEADER)):
        zips = sorted((NEW_RAW / kind).glob("*/*.zip"), key=_ym_key)
        by_symbol: dict[str, list[str]] = {}
        zip_count: dict[str, int] = {}
        for z in zips:
            symbol = z.parent.name
            zip_count[symbol] = zip_count.get(symbol, 0) + 1
            with zipfile.ZipFile(z) as zf:
                names = [n for n in zf.namelist() if n.endswith(".csv")]
                if not names:
                    continue
                text = zf.read(names[0]).decode("utf-8")
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if lines and lines[0].startswith(("open_time,", "calc_time,", "symbol,")):
                lines = lines[1:]
            by_symbol.setdefault(symbol, []).extend(lines)
            total_rows += len(lines)
        for symbol, lines in by_symbol.items():
            prefixed = [f"{symbol},{ln}" for ln in lines] if kind == "funding" else lines
            out = NEW_PANELS / f"binance_{kind}_{symbol}.csv"
            out.write_text(header + "\n" + "\n".join(prefixed) + "\n")
            dates = sorted({ln.split(",")[0] for ln in lines if ln.strip()})
            summary[f"{kind}/{symbol}"] = {
                "rows": len(lines),
                "date_first": _ms_to_date(dates[0]),
                "date_last": _ms_to_date(dates[-1]),
                "n_months": zip_count.get(symbol, 0),
                "sha256": sha256_file(out),
            }
    return {"total_rows": total_rows, "panels": summary}


def _ms_to_date(ms: str) -> str:
    return pd.to_datetime(int(ms), unit="ms", utc=True).strftime("%Y-%m-%d")


def load_klines_dates(panel_dir: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p in sorted(panel_dir.glob("binance_klines_*.csv")):
        symbol = p.stem.replace("binance_klines_", "")
        df = pd.read_csv(p)
        dates = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        out[symbol] = set(dates.unique())
    return out


def load_funding_dates(panel_dir: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for p in sorted(panel_dir.glob("binance_funding_*.csv")):
        symbol = p.stem.replace("binance_funding_", "")
        df = pd.read_csv(p)
        dates = pd.to_datetime(df["calc_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        out[symbol] = set(dates.unique())
    return out


def load_marketcap() -> pd.DataFrame:
    df = pd.read_csv(OLD_PANELS / "marketcap_panel.csv",
                     dtype={"CapMrktCurUSD": str, "CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    return df[["date", "asset", "CapMrktEstUSD"]]


def eligible_counts(mc: pd.DataFrame, px_dates: dict[str, set[str]],
                    fd_dates: dict[str, set[str]] | None = None) -> dict[str, int]:
    """{date: n_assets} under the canonical eligibility rule.

    Canonical rule (eval_forward_block.py:154-183 / run_dispersion003_grid.py:92):
    non-null CapMrktEstUSD on the date AND a kline observation on the date.
    When fd_dates is supplied, a funding observation on the date is also required.
    """
    counts: dict[str, int] = {}
    for d, grp in mc.groupby("date"):
        n = 0
        for asset, cap in zip(grp["asset"], grp["CapMrktEstUSD"]):
            if pd.isna(cap):
                continue
            symbol = f"{asset.upper()}USDT"
            if d not in px_dates.get(symbol, set()):
                continue
            if fd_dates is not None and d not in fd_dates.get(symbol, set()):
                continue
            n += 1
        counts[str(d)] = n
    return counts


def summarize(counts: dict[str, int], dates: list[str]) -> dict:
    vals = [counts[d] for d in dates if d in counts]
    if not vals:
        return {"n_dates": 0}
    return {
        "n_dates": len(vals),
        "min": min(vals),
        "max": max(vals),
        "mean": sum(vals) / len(vals),
        "distribution": {str(k): vals.count(k) for k in sorted(set(vals))},
    }


def snapshot_panel_hashes(panel_dir: Path) -> dict[str, str]:
    return {p.name: sha256_file(p) for p in sorted(panel_dir.glob("*.csv"))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true",
                    help="skip network; rebuild/report from zips already on disk")
    args = ap.parse_args()

    started = now_utc()

    old_panel_hashes_before = snapshot_panel_hashes(OLD_PANELS)

    seeded = seed_existing_zips()
    fetch_records = fetch_gap_zips(offline=args.offline)
    rebuild = rebuild_panels()

    old_panel_hashes_after = snapshot_panel_hashes(OLD_PANELS)

    # Load original and repaired date sets, overriding only the four symbols.
    old_px = load_klines_dates(OLD_PANELS)
    old_fd = load_funding_dates(OLD_PANELS)
    new_px = load_klines_dates(NEW_PANELS)
    new_fd = load_funding_dates(NEW_PANELS)

    merged_px = dict(old_px)
    merged_fd = dict(old_fd)
    for sym in SYMBOLS:
        if sym in new_px:
            merged_px[sym] = new_px[sym]
        if sym in new_fd:
            merged_fd[sym] = new_fd[sym]

    mc = load_marketcap()

    old_counts = eligible_counts(mc, old_px)
    new_counts = eligible_counts(mc, merged_px)
    old_counts_fd = eligible_counts(mc, old_px, old_fd)
    new_counts_fd = eligible_counts(mc, merged_px, merged_fd)

    block = json.loads(CANONICAL_BLOCK.read_text(encoding="utf-8"))
    formation_dates = [f["formation_date"] for f in block.get("formations", [])]

    # Read-only checks: committed panels and frozen artifacts unchanged.
    frozen_now = {}
    for rel, expected in FROZEN_HASHES.items():
        p = ROOT / "artifacts" / OLD_EXP / rel
        actual = sha256_file(p)
        frozen_now[rel] = {"expected": expected, "actual": actual, "match": actual == expected}

    old_kline_checks = {}
    for name, expected in EXPECTED_OLD_KLINES_SHA256.items():
        actual = sha256_file(OLD_PANELS / name)
        old_kline_checks[name] = {"expected": expected, "actual": actual, "match": actual == expected}

    fetch_summary = {
        "n_records": len(fetch_records),
        "n_ok": sum(r["status"] == "ok" for r in fetch_records),
        "n_present_on_disk": sum(r["status"] == "present_on_disk" for r in fetch_records),
        "n_missing": sum(r["status"] == "missing" for r in fetch_records),
        "n_error": sum(r["status"] == "error" for r in fetch_records),
        "n_absent_offline": sum(r["status"] == "absent_offline" for r in fetch_records),
        "expected_records": len(SYMBOLS) * 2 * len(month_range(GAP_START, GAP_END)),
    }

    # Coverage deltas.
    all_dates = sorted(set(old_counts) | set(new_counts))
    delta_examples = []
    increased = 0
    decreased = 0
    for d in all_dates:
        o = old_counts.get(d, 0)
        n = new_counts.get(d, 0)
        if n > o:
            increased += 1
            if len(delta_examples) < 10:
                delta_examples.append({"date": d, "old": o, "new": n, "delta": n - o})
        elif n < o:
            decreased += 1

    artifact = {
        "audit_id": "DISP-003-F1COVERAGE-001",
        "experiment_id": f"HARMONY-CRYPTO-EDGE-004-{NEW_EXP}",
        "hypothesis": "H23",
        "audit_type": "SOURCE_COVERAGE_REPAIR",
        "status": "EXPLORATORY_ONLY",
        "started_utc": started,
        "completed_utc": now_utc(),
        "offline": bool(args.offline),
        "estimand": "descriptive input coverage only; no return/spread/state/inference",
        "notes": [
            "The 168 gap zips are downloaded from https://data.binance.vision (free, keyless) on first execution; on re-runs they are present_on_disk and are not re-fetched. Each record carries its sha256.",
            "The pre-gap/post-gap zips are byte-identical copies of the committed raw archive; the originals are never modified.",
            "Descriptive coverage only: no return, spread, state, cost or inference is computed.",
        ],
        "gap": {
            "symbols": SYMBOLS,
            "months": f"{GAP_START}..{GAP_END}",
            "expected_zips": len(SYMBOLS) * 2 * len(month_range(GAP_START, GAP_END)),
        },
        "fetch": fetch_summary,
        "seeded_from_committed_raw": {
            "n": len(seeded),
            "note": "byte-identical copies of already-present pre-gap/post-gap zips; originals untouched",
            "records": seeded,
        },
        "fetch_records": fetch_records,
        "rebuilt_panels": rebuild,
        "coverage": {
            "rule_canonical_cap_and_klines": {
                "all_dates": summarize(old_counts, all_dates),
                "repaired_all_dates": summarize(new_counts, all_dates),
                "canonical_block_dates": summarize(old_counts, formation_dates),
                "canonical_block_dates_repaired": summarize(new_counts, formation_dates),
                "dates_increased": increased,
                "dates_decreased": decreased,
                "delta_examples": delta_examples,
            },
            "rule_cap_and_klines_and_funding": {
                "all_dates": summarize(old_counts_fd, all_dates),
                "repaired_all_dates": summarize(new_counts_fd, all_dates),
                "canonical_block_dates": summarize(old_counts_fd, formation_dates),
                "canonical_block_dates_repaired": summarize(new_counts_fd, formation_dates),
            },
        },
        "read_only_checks": {
            "old_panels_byte_unchanged": old_panel_hashes_before == old_panel_hashes_after,
            "old_kline_panel_hashes": old_kline_checks,
            "frozen_artifacts": frozen_now,
        },
        "disposition": {
            "old_panels_modified": False,
            "old_raw_modified": False,
            "frozen_artifacts_modified": False,
            "outcomes_computed": False,
        },
        "verdict": None,
    }

    ok_fetch = (fetch_summary["n_missing"] == 0 and fetch_summary["n_error"] == 0
                and (fetch_summary["n_ok"] + fetch_summary["n_present_on_disk"])
                == fetch_summary["expected_records"])
    coverage_ok = increased > 0 and decreased == 0
    unchanged_ok = (old_panel_hashes_before == old_panel_hashes_after
                    and all(v["match"] for v in old_kline_checks.values())
                    and all(v["match"] for v in frozen_now.values()))
    if ok_fetch and coverage_ok and unchanged_ok:
        artifact["verdict"] = "PASS"
    elif fetch_summary["n_missing"] or fetch_summary["n_error"]:
        artifact["verdict"] = "PARTIAL"
    else:
        artifact["verdict"] = "FAIL"

    NEW_AUDIT.mkdir(parents=True, exist_ok=True)
    out = NEW_AUDIT / f"f1_panel_coverage_repair_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[f1] verdict={artifact['verdict']} fetch={fetch_summary}")
    print(f"[f1] coverage canonical: old={artifact['coverage']['rule_canonical_cap_and_klines']['all_dates']} "
          f"new={artifact['coverage']['rule_canonical_cap_and_klines']['repaired_all_dates']}")
    print(f"[f1] block-window: old={artifact['coverage']['rule_canonical_cap_and_klines']['canonical_block_dates']} "
          f"new={artifact['coverage']['rule_canonical_cap_and_klines']['canonical_block_dates_repaired']}")
    print(f"[f1] artifact -> {out.relative_to(ROOT)}")
    return 0 if artifact["verdict"] in ("PASS", "PARTIAL") else 1


if __name__ == "__main__":
    raise SystemExit(main())