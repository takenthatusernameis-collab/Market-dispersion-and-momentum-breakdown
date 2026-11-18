#!/usr/bin/env python3
"""Wave-B panel archive acquisition (DISP-003-PANELACQ-WAVEB-001, H51).

Bounded, keyless, free-public source-coverage **acquisition** of exactly the
H50-trimmed wave-B set: the H41-planned monthly ``(symbol, kind, month)``
archives for ARK and ASTR restricted to each asset's H50 admissible study
months. ARK 38 months x 2 kinds = 76 files; ASTR 45 months x 2 kinds = 90
files; 166 files total. Nothing else is fetched.

This is the natural successor to H50: H47 decided *which assets are
admissible*, H48 *what a bounded acquisition may fetch*, H49 fetched wave A,
H50 declared the wave-B served windows, and this study fetches exactly those
trimmed wave-B bytes and records their content integrity. It is
EXPLORATORY_ONLY source-coverage work: no panel construction, no
returns/spreads/states/p-values/costs/inference, no promotion, and it does not
touch the date-gated ``2026-11`` cutoff month.

Hard properties:
  * Only URLs that appear verbatim in the pinned H41 plan are ever fetched.
  * Wave A (ALICE..ARPA), ALPHA and the 18 H50-dropped pre-listing months
    (ARK 2023-01..2023-08, ASTR 2023-01) are never fetched.
  * Missing files stay missing and are reported; nothing is fabricated.
  * Frozen artifacts are read-only and hash-verified before/after.
  * Network and filesystem writes happen only under ``--execute``.
  * Import-safe: pure helpers importable without side effects or network.

Usage:
    python3 scripts/panel_wave_b_acquisition.py            # plan only, no I/O
    python3 scripts/panel_wave_b_acquisition.py --execute  # fetch + write audit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-WAVEB-001"
EXP_DIR = ROOT / "artifacts" / EXP
AUDIT_DIR = EXP_DIR / "integrity_audit"
PREREG = EXP_DIR / "preregistrations" / "PANELACQ_WAVEB_001_v1.md"

# Committed read-only inputs.
H41_PLAN = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PLAN-001"
    / "integrity_audit"
    / "H004V106_panel_acquisition_plan_20261116T085222Z.json"
)
H43_PROBE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELACQ-PROBE-001"
    / "integrity_audit"
    / "H004V106_panel_archive_probe_20261116T142247Z.json"
)
H47_ROSTER = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-NARROW-001"
    / "integrity_audit"
    / "panel_coverage_eligibility_roster_20261118T191152Z.json"
)
H48_QUEUE = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-QUEUE-001"
    / "integrity_audit"
    / "panel_coverage_acquisition_queue_20261118T201951Z.json"
)
H50_TRIM = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-WAVEB-TRIM-001"
    / "integrity_audit"
    / "panel_wave_b_window_trim_20261118T221212Z.json"
)
H40_FEAS = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-PANELCOV-FEAS-001"
    / "integrity_audit"
    / "H004V106_panel_coverage_extension_feasibility_20261116T215857Z.json"
)

# Frozen integrity checks read (never written) by this study.
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

# Pinned input digests (verified before fetching anything).
H41_PLAN_SHA256 = "39e740b65fbe65541aa42f55b0e231469c49dda7e04d9e22e04eae3ac9ce441b"
H43_PROBE_SHA256 = "69b6e632b5d6b01ecaf9c7f625eeb8e4ad5bcd1f8d1e2ec6b946efb62dd40974"
H47_ROSTER_CANONICAL_SHA256 = (
    "171cd174d527ff34c9ba0162f2b38c7e673f7c5b210daa118d8acdb99c067579"
)
H48_QUEUE_CANONICAL_SHA256 = (
    "38c099db5c233222cc51f39348f06e933871337b807d4761512d2800ec2375c7"
)
H50_TRIM_SHA256 = "5aed05f1615a3cc2983c6e1be86ef9f35306aed7cfab86aea9f1d8fab9f61e66"
H50_TRIM_CANONICAL_SHA256 = (
    "b43f71bf239254152288b8eaf89a7748680117c7ecc10a16564c4a9b6a115a5d"
)

EXPERIMENT_ID = EXP
AUDIT_ID = "H004V106_PANELACQ_WAVEB_001"
HYPOTHESIS = "H51"

KINDS = ("klines", "funding")
# Pre-declared expected wave-B scope (H50).
EXPECTED_WAVE_B_ASSETS = ("ark", "astr")
EXPECTED_WAVE_B_FILES = 166
EXPECTED_WAVE_B_FILES_PER_ASSET = {"ark": 76, "astr": 90}
FORBIDDEN_ASSETS = ("alice", "ankr", "ape", "api3", "apt", "ar", "arpa", "alpha")

# Documented free public archive base (keyless).
BINANCE_DATA_BASE = "https://data.binance.vision"
DEFAULT_CACHE_DIR = ROOT / "data" / "panel_archive_wave_b"

MAX_WORKERS = 8
PER_REQUEST_TIMEOUT = 20
MAX_ATTEMPTS = 3

SCOPE_MISMATCH = "WAVEB_SCOPE_MISMATCH"
ACQ_INCOMPLETE = "WAVEB_ACQUISITION_INCOMPLETE"
ACQ_COMPLETE = "WAVEB_ACQUISITION_COMPLETE"

EXPECTED_HEADER_FIRST = {"klines": "open_time", "funding": "calc_time"}


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


def probe_status_map(probe_entries):
    """{(symbol, kind, month): http_status} from the H43 probe."""
    status = {}
    for e in probe_entries:
        key = (e.get("symbol"), e.get("kind"), e.get("month"))
        status.setdefault(key, e.get("http_status"))
    return status


def select_wave_b_entries(
    plan_entries,
    probe_entries,
    admissible_months_by_asset,
    dropped_months_by_asset=None,
    kinds=KINDS,
):
    """Pure selection of the expected wave-B acquisition entries.

    An entry is selected only when its asset is one of the wave-B assets, its
    month is in that asset's H50 ``admissible_study_months``, its kind is
    required, its H41 plan row carries an archive_url, and the H43 probe
    recorded HTTP 200 for that exact (symbol, kind, month). Any month listed in
    the H50 ``dropped_required_months`` is removed unconditionally, so a
    pre-listing placeholder can never leak into the acquisition list.
    """
    admissible = {a: {m for m in months if m} for a, months in admissible_months_by_asset.items()}
    dropped = {
        a: {m for m in months if m} for a, months in (dropped_months_by_asset or {}).items()
    }
    status = probe_status_map(probe_entries)
    selected = []
    for e in plan_entries:
        asset = e.get("asset")
        kind = e.get("kind")
        month = e.get("month")
        if asset in FORBIDDEN_ASSETS or asset not in admissible:
            continue
        if month not in admissible[asset] or month in dropped.get(asset, set()):
            continue
        if kind not in kinds:
            continue
        url = e.get("archive_url")
        if not url:
            continue
        if status.get((e.get("symbol"), kind, month)) != 200:
            continue
        selected.append(
            {
                "asset": asset,
                "symbol": e.get("symbol"),
                "kind": kind,
                "month": month,
                "archive_url": url,
                "archive_path": e.get("archive_path"),
            }
        )
    selected.sort(key=lambda r: (r["asset"], r["kind"], r["month"]))
    return selected


def is_allowlisted_url(url, allowlist):
    """Strict allowlist check: only plan URLs, only the documented archive base."""
    return url in allowlist and url.startswith(BINANCE_DATA_BASE + "/data/futures/um/")


def verify_archive_bytes(payload, kind):
    """Content integrity of one downloaded archive, using stdlib only.

    Returns descriptive fields; never interprets prices or computes outcomes.
    """
    out = {
        "bytes_downloaded": len(payload),
        "is_zip": False,
        "n_members": 0,
        "csv_member": None,
        "csv_header": None,
        "n_csv_rows": 0,
        "first_timestamp": None,
        "last_timestamp": None,
        "content_ok": False,
        "content_error": None,
    }
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            out["is_zip"] = True
            members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
            out["n_members"] = len(zf.namelist())
            if len(members) != 1:
                out["content_error"] = f"expected exactly one csv member, found {len(members)}"
                return out
            name = members[0]
            out["csv_member"] = name
            raw = zf.read(name).decode("utf-8", errors="replace").splitlines()
            if not raw:
                out["content_error"] = "empty csv"
                return out
            reader = list(csv.reader(raw))
            header = [c.strip() for c in reader[0]]
            out["csv_header"] = header
            expected_first = EXPECTED_HEADER_FIRST.get(kind)
            if expected_first and (not header or header[0] != expected_first):
                out["content_error"] = (
                    f"unexpected header[0]={header[0] if header else None!r}, "
                    f"expected {expected_first!r}"
                )
                return out
            rows = [r for r in reader[1:] if r and any(c.strip() for c in r)]
            out["n_csv_rows"] = len(rows)
            if not rows:
                out["content_error"] = "no data rows"
                return out
            stamps = [r[0].strip() for r in rows]
            out["first_timestamp"] = stamps[0]
            out["last_timestamp"] = stamps[-1]
            try:
                numeric = [int(s) for s in stamps]
            except ValueError:
                out["content_error"] = "non-integer timestamp column"
                return out
            if numeric != sorted(numeric):
                out["content_error"] = "timestamps not monotonically non-decreasing"
                return out
            out["content_ok"] = True
            return out
    except zipfile.BadZipFile:
        out["content_error"] = "not a zip archive"
        return out
    except Exception as exc:  # pragma: no cover - defensive
        out["content_error"] = f"{type(exc).__name__}: {exc}"
        return out


def reconcile(expected_entries, records):
    """Expected vs observed reconciliation over (asset, kind, month) keys."""
    def key(r):
        return (r["asset"], r["kind"], r["month"])

    expected_keys = {key(e) for e in expected_entries}
    observed_keys = {key(r) for r in records if r.get("http_status") == 200}
    missing = sorted(expected_keys - observed_keys)
    extra = sorted(observed_keys - expected_keys)
    per_asset = {}
    for e in expected_entries:
        per_asset.setdefault(e["asset"], {"expected": 0, "ok": 0, "bytes": 0})
        per_asset[e["asset"]]["expected"] += 1
    ok = 0
    ok_bytes = 0
    for r in records:
        if r.get("http_status") == 200 and r.get("sha256") and r.get("content_ok"):
            ok += 1
            ok_bytes += int(r.get("bytes_downloaded") or 0)
            bucket = per_asset.setdefault(r["asset"], {"expected": 0, "ok": 0, "bytes": 0})
            bucket["ok"] += 1
            bucket["bytes"] += int(r.get("bytes_downloaded") or 0)
    return {
        "n_expected": len(expected_entries),
        "n_records": len(records),
        "n_http_200": len(observed_keys),
        "n_content_ok": ok,
        "n_missing": len(missing),
        "n_extra": len(extra),
        "missing_keys": [list(k) for k in missing],
        "extra_keys": [list(k) for k in extra],
        "per_asset": per_asset,
        "bytes_content_ok": ok_bytes,
    }


def decide_verdict(scope_ok, recon):
    """Pre-declared outcome-blind verdict (preregistration section 5)."""
    if not scope_ok:
        return SCOPE_MISMATCH
    if (
        recon["n_content_ok"] == recon["n_expected"]
        and recon["n_missing"] == 0
        and recon["n_extra"] == 0
    ):
        return ACQ_COMPLETE
    return ACQ_INCOMPLETE


def fetch_one(entry, allowlist, cache_dir):
    """Fetch a single allowlisted archive; returns a descriptive record."""
    record = dict(entry)
    record.update(
        {
            "http_status": None,
            "content_length_header": None,
            "sha256": None,
            "cache_path": None,
            "n_attempts": 0,
            "error": None,
            "bytes_downloaded": 0,
            "is_zip": False,
            "n_members": 0,
            "csv_member": None,
            "csv_header": None,
            "n_csv_rows": 0,
            "first_timestamp": None,
            "last_timestamp": None,
            "content_ok": False,
            "content_error": None,
        }
    )
    url = entry.get("archive_url")
    if not is_allowlisted_url(url, allowlist):
        record["error"] = "url not in pinned H41 plan allowlist; refused"
        return record

    payload = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        record["n_attempts"] = attempt
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=PER_REQUEST_TIMEOUT) as resp:
                record["http_status"] = resp.status
                record["content_length_header"] = resp.headers.get("Content-Length")
                payload = resp.read()
            break
        except urllib.error.HTTPError as exc:
            record["http_status"] = exc.code
            record["error"] = f"HTTPError {exc.code}"
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(0.5 * attempt)

    if record["http_status"] != 200 or payload is None:
        record["content_error"] = "not fetched"
        return record

    record["sha256"] = hashlib.sha256(payload).hexdigest()
    record["error"] = None
    record.update(verify_archive_bytes(payload, entry["kind"]))

    if cache_dir is not None:
        dest = Path(cache_dir) / (entry.get("archive_path") or Path(url).name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(payload)
        record["cache_path"] = str(Path(cache_dir).name) + "/" + (
            entry.get("archive_path") or dest.name
        )
    return record


def frozen_hash_checks():
    """Recompute frozen artifact hashes; returns {name: {actual, expected, match}}."""
    out = {}
    paths = {
        "canonical_forward_block": CANONICAL_FORWARD_BLOCK,
        "h10_fresh_block": H10_FRESH_BLOCK,
        "universe_frontier": UNIVERSE_FRONTIER,
        "grid_v3_config": GRID_V3_CONFIG,
    }
    for name, path in paths.items():
        actual = _file_sha256(path) if path.exists() else None
        expected = EXPECTED_FROZEN_SHA256[name]
        out[name] = {
            "path": path.relative_to(ROOT).as_posix(),
            "actual": actual,
            "expected": expected,
            "match": actual == expected,
        }
    return out


def build_plan():
    """Assemble the expected wave-B acquisition set and scope checks (no network)."""
    plan = _load_json(H41_PLAN)
    probe = _load_json(H43_PROBE)
    roster = _load_json(H47_ROSTER)
    queue = _load_json(H48_QUEUE)
    trim = _load_json(H50_TRIM)
    feas = _load_json(H40_FEAS)

    study_months = sorted(m for m in (feas.get("study_months") or []) if m)
    trim_assets = tuple(sorted((trim.get("per_asset") or {}).keys()))
    admissible = {
        a: list(v.get("admissible_study_months") or [])
        for a, v in (trim.get("per_asset") or {}).items()
    }
    dropped = {
        a: list(v.get("dropped_required_months") or [])
        for a, v in (trim.get("per_asset") or {}).items()
    }

    entries = select_wave_b_entries(plan["plan_entries"], probe["per_entry"], admissible, dropped)

    per_asset_counts = {}
    for e in entries:
        per_asset_counts[e["asset"]] = per_asset_counts.get(e["asset"], 0) + 1

    selected_months_by_asset = {}
    for e in entries:
        selected_months_by_asset.setdefault(e["asset"], set()).add(e["month"])

    dropped_month_selected = sorted(
        [
            [a, m]
            for a, months in dropped.items()
            for m in months
            if m in selected_months_by_asset.get(a, set())
        ]
    )

    scope_checks = {
        "h41_plan_sha256_ok": _file_sha256(H41_PLAN) == H41_PLAN_SHA256,
        "h43_probe_sha256_ok": _file_sha256(H43_PROBE) == H43_PROBE_SHA256,
        "h47_roster_canonical_sha256_ok": roster.get("roster_canonical_sha256")
        == H47_ROSTER_CANONICAL_SHA256,
        "h48_queue_canonical_sha256_ok": queue.get("queue_canonical_sha256")
        == H48_QUEUE_CANONICAL_SHA256,
        "h50_artifact_sha256_ok": _file_sha256(H50_TRIM) == H50_TRIM_SHA256,
        "h50_trim_canonical_sha256_ok": trim.get("trim_canonical_sha256")
        == H50_TRIM_CANONICAL_SHA256,
        "h50_verdict_ok": trim.get("trim_verdict") == "TRIM_DECISION_RECORDED",
        "wave_b_asset_set_matches_expected": trim_assets == tuple(EXPECTED_WAVE_B_ASSETS),
        "selected_asset_set_matches_expected": tuple(sorted(per_asset_counts))
        == tuple(EXPECTED_WAVE_B_ASSETS),
        "selected_file_count_matches_expected": len(entries) == EXPECTED_WAVE_B_FILES,
        "per_asset_file_counts_match_expected": per_asset_counts
        == EXPECTED_WAVE_B_FILES_PER_ASSET,
        "no_forbidden_asset_selected": not any(e["asset"] in FORBIDDEN_ASSETS for e in entries),
        "no_dropped_month_selected": not dropped_month_selected,
        "all_selected_months_admissible": all(
            m in set(admissible.get(a, [])) for a, months in selected_months_by_asset.items()
            for m in months
        ),
        "all_selected_months_in_study_window": all(e["month"] in set(study_months) for e in entries),
        "all_urls_on_documented_archive_base": all(
            e["archive_url"].startswith(BINANCE_DATA_BASE + "/data/futures/um/") for e in entries
        ),
    }
    scope_ok = all(scope_checks.values())
    return {
        "entries": entries,
        "scope_checks": scope_checks,
        "scope_ok": scope_ok,
        "study_months": study_months,
        "trim_assets": list(trim_assets),
        "admissible_months_by_asset": {a: sorted(v) for a, v in admissible.items()},
        "dropped_months_by_asset": {a: sorted(v) for a, v in dropped.items()},
        "per_asset_counts": per_asset_counts,
        "dropped_month_selected": dropped_month_selected,
        "h41_plan_sha256": _file_sha256(H41_PLAN),
        "h43_probe_sha256": _file_sha256(H43_PROBE),
        "h47_roster_canonical_sha256": roster.get("roster_canonical_sha256"),
        "h48_queue_canonical_sha256": queue.get("queue_canonical_sha256"),
        "h50_trim_canonical_sha256": trim.get("trim_canonical_sha256"),
    }


def build_audit(records=None, cache_dir=DEFAULT_CACHE_DIR, fetched_utc=None):
    """Assemble the acquisition artifact. Network only if ``records`` is None."""
    plan = build_plan()
    entries = plan["entries"]
    if records is None:
        allowlist = {e["archive_url"] for e in entries}
        if plan["scope_ok"]:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                records = list(pool.map(lambda e: fetch_one(e, allowlist, cache_dir), entries))
            fetched_utc = _utc_now()
        else:
            records = []
    recon = reconcile(entries, records)
    verdict = decide_verdict(plan["scope_ok"], recon)
    frozen = frozen_hash_checks()

    audit = {
        "experiment_id": EXPERIMENT_ID,
        "audit_id": AUDIT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": _utc_now(),
        "fetched_utc": fetched_utc,
        "preregistration": PREREG.relative_to(ROOT).as_posix(),
        "method": (
            "Bounded keyless GET of exactly the H50-trimmed wave-B set: H41-planned "
            "monthly klines+funding archives for ARK (38 admissible study months, 76 "
            "files) and ASTR (45 months, 90 files), 166 files total. Each response is "
            "hashed and its content checked with stdlib zipfile/csv (single csv member, "
            "documented header, non-empty, monotone timestamps). Wave A, ALPHA and the "
            "18 H50-dropped pre-listing months are never fetched and no month outside "
            "an H50 admissible window is fetched. No panel, no outcomes."
        ),
        "source_base": BINANCE_DATA_BASE,
        "audited_inputs": {
            "h41_plan": H41_PLAN.relative_to(ROOT).as_posix(),
            "h43_probe": H43_PROBE.relative_to(ROOT).as_posix(),
            "h47_roster": H47_ROSTER.relative_to(ROOT).as_posix(),
            "h48_queue": H48_QUEUE.relative_to(ROOT).as_posix(),
            "h50_window_trim": H50_TRIM.relative_to(ROOT).as_posix(),
            "h40_feasibility_context": H40_FEAS.relative_to(ROOT).as_posix(),
        },
        "audited_input_sha256": {
            "h41_plan": plan["h41_plan_sha256"],
            "h43_probe": plan["h43_probe_sha256"],
            "h50_window_trim": _file_sha256(H50_TRIM),
        },
        "h47_roster_canonical_sha256": plan["h47_roster_canonical_sha256"],
        "h48_queue_canonical_sha256": plan["h48_queue_canonical_sha256"],
        "h50_trim_canonical_sha256": plan["h50_trim_canonical_sha256"],
        "scope_checks": plan["scope_checks"],
        "scope_ok": plan["scope_ok"],
        "scope_declaration": {
            "expected_wave_b_assets": list(EXPECTED_WAVE_B_ASSETS),
            "expected_files": EXPECTED_WAVE_B_FILES,
            "expected_files_per_asset": dict(EXPECTED_WAVE_B_FILES_PER_ASSET),
            "kinds": list(KINDS),
            "n_study_months": len(plan["study_months"]),
            "admissible_months_by_asset": plan["admissible_months_by_asset"],
            "dropped_months_by_asset": plan["dropped_months_by_asset"],
            "excluded_wave_a_assets_not_acquired": [
                "alice",
                "ankr",
                "ape",
                "api3",
                "apt",
                "ar",
                "arpa",
            ],
            "excluded_wave_a_files_not_acquired": 644,
            "excluded_alpha_files_not_acquired": 92,
            "excluded_dropped_wave_b_files_not_acquired": 18,
        },
        "reconciliation": recon,
        "verdict": verdict,
        "verdict_rule": (
            "WAVEB_SCOPE_MISMATCH if a pinned input digest fails, the derived wave-B "
            "asset set is not {ark,astr}, the trimmed month set differs from the H50 "
            "admissible months, the count is not 166 (ark 76 / astr 90), or any "
            "selected file falls outside an admissible window or into a dropped month; "
            "WAVEB_ACQUISITION_INCOMPLETE if any expected file lacks HTTP 200, a "
            "sha256, or content_ok; else WAVEB_ACQUISITION_COMPLETE."
        ),
        "frozen_hashes_verified": frozen,
        "all_frozen_hashes_match": all(v["match"] for v in frozen.values()),
        "total_bytes_content_ok": recon["bytes_content_ok"],
        "records": records,
        "records_canonical_sha256": _canonical_sha256(records),
        "exploratory_only": True,
        "promotion_allowed": False,
        "confirmatory_claim_allowed": False,
        "non_claims": [
            "No panel constructed; no returns/spreads/states/p-values/costs/"
            "inference computed.",
            "No candidate promoted; no confirmatory or economic claim.",
            "Missing archive files are never fabricated; they remain absent.",
            "Wave A archives are not re-fetched; ALPHA and the 18 H50-dropped "
            "pre-listing months remain unacquired by declared decision.",
            "Does not re-probe the date-gated 2026-11 cutoff month.",
            "Does not alter any frozen DISP-001/002/003 artifact, config, ledger "
            "or forward block, and does not unlock H1/H6/H7/H10.",
        ],
    }
    return audit


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Wave-B panel archive acquisition (H51, exploratory only)."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Fetch the 166 trimmed wave-B archives and write the audit artifact.",
    )
    parser.add_argument("--out", default=None, help="Audit output path.")
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Directory for raw archive bytes (gitignored, outside version control).",
    )
    args = parser.parse_args(argv)

    plan = build_plan()
    if not args.execute:
        print(
            json.dumps(
                {
                    "mode": "plan_only",
                    "scope_ok": plan["scope_ok"],
                    "n_expected_files": len(plan["entries"]),
                    "per_asset_counts": plan["per_asset_counts"],
                    "wave_b_assets": sorted({e["asset"] for e in plan["entries"]}),
                    "scope_checks": plan["scope_checks"],
                },
                sort_keys=True,
            )
        )
        return 0 if plan["scope_ok"] else 1

    audit = build_audit(None, cache_dir=args.cache_dir)
    out_path = Path(args.out) if args.out else (
        AUDIT_DIR
        / f"panel_wave_b_acquisition_{audit['computed_utc'].replace('-', '').replace(':', '')}.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "verdict": audit["verdict"],
                "n_expected": audit["reconciliation"]["n_expected"],
                "n_content_ok": audit["reconciliation"]["n_content_ok"],
                "total_bytes_content_ok": audit["total_bytes_content_ok"],
                "out": str(out_path),
            },
            sort_keys=True,
        )
    )
    return 0 if audit["verdict"] == ACQ_COMPLETE else 2


if __name__ == "__main__":
    sys.exit(main())
