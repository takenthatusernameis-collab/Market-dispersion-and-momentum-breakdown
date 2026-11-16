#!/usr/bin/env python3
"""H004V106 planned-archive source-coverage probe (H43, EXPLORATORY_ONLY).

DISP-003-PANELACQ-PROBE-001. Bounded, keyless, free-public source-coverage
measurement: HEAD-probe every H41-planned monthly (symbol, kind, month) archive
entry against the Binance Public Data Archive and record which files are
actually served (HTTP 200) vs absent (HTTP 404) vs errored.

This is the bounded keyless probe that H41 section 8 names as the next step:
H40 concluded panel extension is feasible *in principle* and H41 enumerated 920
planned targets with ``published_verified: null``; nothing had verified the
archive actually serves them.

Hard properties:
  * HEAD only -- response bodies are NEVER read or downloaded.
  * No panel construction, no returns/spreads/states/p-values/costs/inference.
  * Does not probe the date-gated ``2026-11`` cutoff month.
  * Frozen artifacts are read-only and hash-verified before/after.
  * Import-safe: pure helpers importable without side effects or network.

CLI:
    python3 scripts/panel_archive_probe.py [--out <path>] [--workers N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

# Committed H41 plan (read-only input) and its pinned SHA256.
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)
H41_PLAN_SHA256 = "39e740b65fbe65541aa42f55b0e231469c49dda7e04d9e22e04eae3ac9ce441b"

# Documented free public archive base (keyless).
BINANCE_DATA_BASE = "https://data.binance.vision"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
AUDIT_ID = "H004V106_PANELACQ_PROBE_001"
HYPOTHESIS = "H43"

# Bounded probe parameters (predeclared).
MAX_WORKERS = 8
PER_REQUEST_TIMEOUT = 15
MAX_ATTEMPTS = 3

# Positive control: long-published BTCUSDT monthly archives (must be HTTP 200).
CONTROL_KLINES_URL = f"{BINANCE_DATA_BASE}/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2023-01.zip"
CONTROL_FUNDING_URL = f"{BINANCE_DATA_BASE}/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2023-01.zip"
# Negative control: well-formed far-future URL that must be absent (HTTP 404).
NEGATIVE_CONTROL_URL = f"{BINANCE_DATA_BASE}/data/futures/um/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2099-01.zip"

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
}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Pure helpers (no network) -- import-safe and unit-testable.
# --------------------------------------------------------------------------- #
def load_plan(path: Path = H41_PLAN) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_targets(plan: dict) -> list[dict]:
    """Project the committed H41 plan into a deterministic probe-target list.

    Each target mirrors the plan entry verbatim (asset, symbol, kind, month,
    archive_url). Order follows the committed plan order, which is deterministic.
    """
    targets = []
    for entry in plan.get("plan_entries", []):
        targets.append(
            {
                "asset": entry.get("asset"),
                "symbol": entry.get("symbol"),
                "kind": entry.get("kind"),
                "month": entry.get("month"),
                "archive_path": entry.get("archive_path"),
                "archive_url": entry.get("archive_url"),
            }
        )
    return targets


def target_keys(targets: list[dict]) -> list[tuple]:
    return [(t.get("symbol"), t.get("kind"), t.get("month")) for t in targets]


def summarize(results: list[dict]) -> dict:
    """Aggregate per-entry probe results into counts (pure)."""
    n_total = len(results)
    n_200 = sum(1 for r in results if r.get("http_status") == 200)
    n_404 = sum(1 for r in results if r.get("http_status") == 404)
    n_other = sum(
        1
        for r in results
        if r.get("http_status") is not None and r.get("http_status") not in (200, 404)
    )
    n_error = sum(1 for r in results if r.get("http_status") is None)
    per_kind: dict[str, dict] = {}
    per_asset: dict[str, dict] = {}
    for r in results:
        for bucket, key in ((per_kind, r.get("kind")), (per_asset, r.get("asset"))):
            row = bucket.setdefault(str(key), {"total": 0, "n_200": 0, "n_404": 0, "n_error": 0})
            row["total"] += 1
            status = r.get("http_status")
            if status == 200:
                row["n_200"] += 1
            elif status == 404:
                row["n_404"] += 1
            elif status is None:
                row["n_error"] += 1
    coverage_frac = (n_200 / n_total) if n_total else 0.0
    return {
        "n_total": n_total,
        "n_200": n_200,
        "n_404": n_404,
        "n_other_status": n_other,
        "n_error": n_error,
        "coverage_frac": coverage_frac,
        "per_kind": per_kind,
        "per_asset": per_asset,
    }


def decide_label(control_ok: bool, summary: dict) -> tuple[str, dict]:
    """Predeclared outcome-blind decision rule (pure)."""
    checks = {
        "control_ok": bool(control_ok),
    }
    n_total = summary.get("n_total", 0)
    n_200 = summary.get("n_200", 0)
    n_error = summary.get("n_error", 0)
    if not control_ok:
        label = "PROBE_CONTROL_FAILED"
    elif n_error == 0 and n_200 == n_total and n_total > 0:
        label = "ARCHIVE_PLAN_FULLY_SERVED"
    elif n_200 > 0:
        label = "ARCHIVE_PLAN_PARTIALLY_SERVED"
    elif n_total > 0:
        label = "ARCHIVE_PLAN_UNSERVED"
    else:
        label = "PROBE_CONTROL_FAILED"
    return label, checks


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
    plan_actual = sha256_file(H41_PLAN) if H41_PLAN.exists() else None
    out["h41_plan"] = {
        "path": str(H41_PLAN.relative_to(ROOT)),
        "expected": H41_PLAN_SHA256,
        "actual": plan_actual,
        "match": plan_actual == H41_PLAN_SHA256,
    }
    return out


# --------------------------------------------------------------------------- #
# Network probe (injectable for hermetic tests).
# --------------------------------------------------------------------------- #
def http_head(url: str, timeout: int = PER_REQUEST_TIMEOUT, attempts: int = MAX_ATTEMPTS) -> dict:
    """Keyless HTTP HEAD. Returns {http_status, content_length, error}.

    Reads no response body. Retries transient errors with exponential backoff.
    """
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                length = resp.headers.get("Content-Length")
                return {
                    "http_status": resp.getcode(),
                    "content_length": int(length) if length is not None else None,
                    "error": None,
                }
        except urllib.error.HTTPError as exc:
            # A definite HTTP status (e.g. 404) is a real availability signal.
            return {"http_status": exc.code, "content_length": None, "error": None}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < attempts:
                time.sleep(2.0 ** attempt)
    return {"http_status": None, "content_length": None, "error": last_err or "exhausted_retries"}


def probe_targets(
    targets: list[dict],
    probe_fn=http_head,
    workers: int = MAX_WORKERS,
) -> list[dict]:
    """Probe every target concurrently; return per-entry result rows."""

    def _one(t: dict) -> dict:
        res = probe_fn(t["archive_url"])
        return {
            "asset": t.get("asset"),
            "symbol": t.get("symbol"),
            "kind": t.get("kind"),
            "month": t.get("month"),
            "archive_url": t.get("archive_url"),
            "http_status": res.get("http_status"),
            "content_length": res.get("content_length"),
            "error": res.get("error"),
        }

    if workers <= 1 or len(targets) <= 1:
        return [_one(t) for t in targets]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, targets))


def probe_controls(probe_fn=http_head) -> dict:
    pos_k = probe_fn(CONTROL_KLINES_URL)
    pos_f = probe_fn(CONTROL_FUNDING_URL)
    neg = probe_fn(NEGATIVE_CONTROL_URL)
    positive_ok = pos_k.get("http_status") == 200 and pos_f.get("http_status") == 200
    negative_ok = neg.get("http_status") == 404
    return {
        "positive_control": {
            "klines_url": CONTROL_KLINES_URL,
            "klines_status": pos_k.get("http_status"),
            "funding_url": CONTROL_FUNDING_URL,
            "funding_status": pos_f.get("http_status"),
            "ok": positive_ok,
        },
        "negative_control": {
            "url": NEGATIVE_CONTROL_URL,
            "status": neg.get("http_status"),
            "ok": negative_ok,
        },
        "control_ok": positive_ok and negative_ok,
    }


# --------------------------------------------------------------------------- #
# Audit assembly.
# --------------------------------------------------------------------------- #
def build_audit(
    out_path: Path | None = None,
    probe_fn=http_head,
    workers: int = MAX_WORKERS,
) -> dict:
    frozen_before = verify_frozen_hashes()
    plan = load_plan()
    targets = build_targets(plan)
    keys = target_keys(targets)
    unique_ok = len(keys) == len(set(keys))

    controls = probe_controls(probe_fn=probe_fn)
    results = probe_targets(targets, probe_fn=probe_fn, workers=workers)
    summary = summarize(results)

    # The decision uses the positive control (archive reachable). The negative
    # control validates the probe distinguishes absence; it is reported but a
    # failed negative control alone does not overturn target measurements.
    label, checks = decide_label(controls["positive_control"]["ok"], summary)
    checks["targets_unique"] = unique_ok
    checks["negative_control_ok"] = controls["negative_control"]["ok"]

    frozen_after = verify_frozen_hashes()
    all_frozen_match = all(v["match"] for v in frozen_after.values()) and all(
        v["match"] for v in frozen_before.values()
    )

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "label": label,
        "computed_utc": now_utc(),
        "decision": label,
        "decision_rule": (
            "PROBE_CONTROL_FAILED if positive control (BTCUSDT 2023-01 klines AND funding) "
            "is not HTTP 200; else ARCHIVE_PLAN_FULLY_SERVED if n_error==0 and n_200==n_total; "
            "else ARCHIVE_PLAN_PARTIALLY_SERVED if n_200>0; else ARCHIVE_PLAN_UNSERVED. "
            "Descriptive source-coverage only; missing files are never fabricated."
        ),
        "all_frozen_hashes_match": all_frozen_match,
        "frozen_hashes_verified_before": frozen_before,
        "frozen_hashes_verified_after": frozen_after,
        "inputs": {
            "h41_plan": str(H41_PLAN.relative_to(ROOT)),
            "h41_plan_sha256": H41_PLAN_SHA256,
            "h41_plan_sha256_matches": frozen_after["h41_plan"]["match"],
            "archive_base": BINANCE_DATA_BASE,
            "probe_method": "keyless HTTP HEAD (no body read, no download)",
        },
        "probe_parameters": {
            "max_workers": workers,
            "per_request_timeout_s": PER_REQUEST_TIMEOUT,
            "max_attempts": MAX_ATTEMPTS,
            "targets_planned": len(targets),
            "targets_unique": unique_ok,
            "study_window": {"start": "2023-01", "end": "2026-10"},
        },
        "controls": controls,
        "summary": summary,
        "checks": checks,
        "per_entry": results,
        "interpretation": (
            "EXPLORATORY_ONLY source-coverage measurement from keyless HEAD metadata only. "
            "Reports which H41-planned archive files the Binance Public Data Archive actually "
            "serves now. No content downloaded, no panels constructed, no returns/spreads/"
            "states/p-values/costs/inference. Does not claim archive publication for the "
            "date-gated 2026-11 cutoff month and does not re-open the H10 gate. Cannot "
            "validate, replace or unlock H1/H6/H7/H10 or any confirmatory track."
        ),
        "non_claims": [
            "no_content_downloaded",
            "no_panel_constructed",
            "no_outcome_or_inference",
            "no_confirmatory_promotion",
            "no_historical_rank_backfill",
            "no_cutoff_month_reprobe",
            "no_fabricated_missing_files",
        ],
    }
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit["_output_path"] = str(out_path.relative_to(ROOT))
    return audit


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", help="Output JSON path (default: timestamped in integrity_audit/)")
    ap.add_argument("--workers", type=int, default=MAX_WORKERS, help="Concurrent HEAD workers")
    args = ap.parse_args()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else (AUDIT_DIR / f"H004V106_panel_archive_probe_{ts}.json")
    if not out.is_absolute():
        out = ROOT / out
    audit = build_audit(out_path=out, workers=args.workers)
    print(
        json.dumps(
            {
                "label": audit["label"],
                "n_total": audit["summary"]["n_total"],
                "n_200": audit["summary"]["n_200"],
                "n_404": audit["summary"]["n_404"],
                "n_error": audit["summary"]["n_error"],
                "coverage_frac": round(audit["summary"]["coverage_frac"], 4),
                "out": audit.get("_output_path"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()