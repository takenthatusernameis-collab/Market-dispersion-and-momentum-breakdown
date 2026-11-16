#!/usr/bin/env python3
"""H004V106 rank-breadth reproducibility + raw-series integrity audit (H42).

DISP-003-RANKBREADTH-REPRO-001. Independently re-derives the H39
``RANK_BREADTH_MEASURABLE`` verdict from the committed raw cap archive, the
committed BTCUSDT kline daily index and the committed candidate validation using
a SEPARATE, stdlib-only implementation (csv/json only; no pandas), and
characterizes committed candidate-cap series integrity (page-chunked ordering,
duplicate/conflicting dates, non-finite/non-positive values, availability).

Read-only. Writes one diagnostic artifact under
``artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001/integrity_audit/``.
No returns, spreads, dispersion states, p-values, costs or inference are
computed. This is a computational-reproducibility check on the SAME committed
inputs as H39, not an independent data-source verification, and it does not
validate, replace or unlock any confirmatory track.

Import-safe: pure helpers are importable without side effects. CLI:
    python3 scripts/rank_breadth_reproducibility_audit.py [--out <path>]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
DATA = ART / "data"

EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

CANDIDATE_VALIDATION = DATA / "panels" / "candidate_batch_validation.json"
RAW_CAP_DIR = DATA / "raw" / "coinmetrics_candidates"
KLINE_PATH = DATA / "panels" / "binance_klines_BTCUSDT.csv"
MARKETCAP_PANEL = DATA / "panels" / "marketcap_panel.csv"

H39_ARTIFACT = (
    ROOT
    / "artifacts"
    / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
    / "integrity_audit"
    / "H004V106_rank_breadth_feasibility_2026-11-16T06-57-08Z.json"
)

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001"
AUDIT_ID = "H004V106_RANKBREADTH_REPRO_001"
HYPOTHESIS = "H42"
TOL = 1e-9

MIN_MEDIAN_N = 100
MIN_BAND_COUNT = 10
BAND_FRACTION_THRESHOLD = 0.90
RANK_BANDS = [(1, 20), (21, 50), (51, 100), (101, 200), (201, None)]

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


def _percentile(sorted_values: list[float], q: float):
    """Linear-interpolation percentile (q in [0,100]) over a sorted list.

    Same estimator definition as H39 (rank_breadth_feasibility_audit.py) so the
    recomputation is comparable; implemented independently here.
    """
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * (q / 100.0)
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return float(sorted_values[lo] * (1.0 - frac) + sorted_values[hi] * frac)


def _distribution(values: list[float]) -> dict:
    if not values:
        return {"min": None, "p10": None, "p50": None, "mean": None,
                "p90": None, "max": None, "n": 0}
    s = sorted(values)
    return {
        "min": s[0],
        "p10": _percentile(s, 10),
        "p50": _percentile(s, 50),
        "mean": statistics.fmean(s),
        "p90": _percentile(s, 90),
        "max": s[-1],
        "n": len(s),
    }


def band_label(rank: int) -> str:
    for lo, hi in RANK_BANDS:
        if rank >= lo and (hi is None or rank <= hi):
            return f"[{lo}-{hi if hi is not None else '+'}]"
    raise ValueError(f"rank out of band range: {rank}")


def load_binance_universe(path: Path = CANDIDATE_VALIDATION) -> set:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        c["asset"]
        for c in data["candidates_processed"]
        if isinstance(c.get("binance"), dict) and c["binance"].get("exists")
    }


def load_raw_groups(raw_dir: Path = RAW_CAP_DIR) -> dict:
    """asset -> list[(date, raw_value_string)] preserving committed file order."""
    groups: dict = {}
    for path in sorted(raw_dir.glob("*_CapMrktEstUSD.json")):
        asset = path.name[: -len("_CapMrktEstUSD.json")]
        rows = json.loads(path.read_text(encoding="utf-8"))
        groups[asset] = [
            (str(row.get("time", ""))[:10], row.get("CapMrktEstUSD"))
            for row in rows
        ]
    return groups


def load_panel_groups(path: Path = MARKETCAP_PANEL) -> dict:
    """asset -> list[(date, raw_value_string)] preserving committed CSV order."""
    groups: dict = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            asset = row.get("asset")
            if asset is None:
                continue
            groups.setdefault(asset, []).append(
                (str(row.get("date", ""))[:10], row.get("CapMrktEstUSD"))
            )
    return groups


def groups_to_cap(groups: dict) -> dict:
    """asset -> {date: float}; last value per date wins; skip non-finite."""
    out: dict = {}
    for asset, rows in groups.items():
        series: dict = {}
        for date, raw in rows:
            if not date or raw in (None, ""):
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(value):
                continue
            series[date] = value
        if series:
            out[asset] = series
    return out


def load_study_dates(kline_path: Path = KLINE_PATH) -> list:
    """Sorted unique UTC dates from the committed BTCUSDT kline open_time index."""
    dates = set()
    with kline_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = row.get("open_time")
            if raw in (None, ""):
                continue
            try:
                ms = int(float(raw))
            except (TypeError, ValueError):
                continue
            d = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).strftime("%Y-%m-%d")
            dates.add(d)
    return sorted(dates)


def load_panel_assets(path: Path = MARKETCAP_PANEL) -> list:
    assets = set()
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            a = row.get("asset")
            if a:
                assets.add(a)
    return sorted(assets)


def assign_ranks(caps: dict) -> list:
    ordered = sorted(caps.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(asset, cap, i + 1) for i, (asset, cap) in enumerate(ordered)]


def compute_rank_breadth(universe: set, cap_obs: dict, study_dates: list) -> dict:
    universe = set(universe)
    n_series = sum(1 for a in universe if a in cap_obs and cap_obs[a])

    per_date = []
    for date in study_dates:
        caps = {
            asset: cap_obs[asset][date]
            for asset in universe
            if asset in cap_obs and date in cap_obs[asset]
        }
        ranks = assign_ranks(caps)
        band_counts = {band_label(lo): 0 for lo, _ in RANK_BANDS}
        for _, _, rank in ranks:
            band_counts[band_label(rank)] += 1
        per_date.append({"date": date, "n_rankable": len(ranks),
                         "band_counts": band_counts})

    n_vals = [float(row["n_rankable"]) for row in per_date]
    band_stats = {}
    for lo, hi in RANK_BANDS:
        label = band_label(lo)
        counts = [float(row["band_counts"][label]) for row in per_date]
        frac_ge = (
            sum(1 for c in counts if c >= MIN_BAND_COUNT) / len(counts)
            if counts else None
        )
        band_stats[label] = {**_distribution(counts), "frac_dates_count_ge_min": frac_ge,
                             "min_band_count": MIN_BAND_COUNT}

    frac_ge_min = (
        sum(1 for v in n_vals if v >= MIN_MEDIAN_N) / len(n_vals)
        if n_vals else None
    )
    return {
        "universe_size": len(universe),
        "n_assets_with_nonempty_series": n_series,
        "n_study_dates": len(study_dates),
        "study_date_first": study_dates[0] if study_dates else None,
        "study_date_last": study_dates[-1] if study_dates else None,
        "rankable_size_stats": _distribution(n_vals),
        "band_stats": band_stats,
        "frac_dates_rankable_ge_min_median": frac_ge_min,
        "_per_date": per_date,
    }


def committed_panel_rank_coverage(panel_assets: list, universe: set,
                                  cap_obs: dict, study_dates: list) -> dict:
    rank_by_asset = {a: [] for a in panel_assets}
    for date in study_dates:
        caps = {
            asset: cap_obs[asset][date]
            for asset in universe
            if asset in cap_obs and date in cap_obs[asset]
        }
        ranks = {asset: rank for asset, _, rank in assign_ranks(caps)}
        for asset in panel_assets:
            if asset in ranks:
                rank_by_asset[asset].append(ranks[asset])
    per_asset = {}
    for asset in panel_assets:
        ranks = rank_by_asset[asset]
        per_asset[asset] = {
            "n_dates_ranked": len(ranks),
            "frac_study_dates_ranked": (len(ranks) / len(study_dates)) if study_dates else 0.0,
            "rank_min": min(ranks) if ranks else None,
            "rank_p50": _percentile(sorted(ranks), 50) if ranks else None,
            "rank_max": max(ranks) if ranks else None,
        }
    return {"per_asset": per_asset}


def series_integrity(groups: dict, assets: list) -> dict:
    """Per-asset integrity of the committed cap series actually used for ranking."""
    per_asset = {}
    totals = {
        "n_assets": len(assets),
        "n_missing_source": 0,
        "n_empty": 0,
        "n_with_duplicate_date_rows": 0,
        "n_with_conflicting_duplicate_dates": 0,
        "n_with_nonfinite_or_nonpositive": 0,
        "n_nonfinite_or_nonpositive_values": 0,
        "n_conflicting_duplicate_dates": 0,
        "n_descents_total": 0,
        "n_assets_not_strictly_increasing": 0,
    }
    for asset in assets:
        rows = groups.get(asset)
        if rows is None:
            totals["n_missing_source"] += 1
            per_asset[asset] = {"source_present": False}
            continue
        if not rows:
            totals["n_empty"] += 1
            per_asset[asset] = {"source_present": True, "n_rows": 0}
            continue
        dates = [d for d, _ in rows]
        n_rows = len(rows)
        distinct = set(dates)
        # duplicate-date conflicts: a date whose values disagree
        by_date: dict = {}
        for d, raw in rows:
            by_date.setdefault(d, set()).add(raw)
        conflicting = [d for d, vals in by_date.items() if len(vals) > 1]
        # non-finite / non-positive raw values
        bad = 0
        for _, raw in rows:
            try:
                v = float(raw)
                if not math.isfinite(v) or v <= 0:
                    bad += 1
            except (TypeError, ValueError):
                bad += 1
        descents = sum(1 for i in range(1, n_rows) if dates[i] < dates[i - 1])
        strictly_increasing = all(dates[i] > dates[i - 1] for i in range(1, n_rows))
        per_asset[asset] = {
            "source_present": True,
            "n_rows": n_rows,
            "n_distinct_dates": len(distinct),
            "n_duplicate_date_rows": n_rows - len(distinct),
            "n_conflicting_dates": len(conflicting),
            "n_nonfinite_or_nonpositive": bad,
            "first_date": min(distinct),
            "last_date": max(distinct),
            "n_descents": descents,
            "strictly_increasing": strictly_increasing,
        }
        totals["n_with_duplicate_date_rows"] += 1 if n_rows != len(distinct) else 0
        totals["n_with_conflicting_duplicate_dates"] += 1 if conflicting else 0
        totals["n_conflicting_duplicate_dates"] += len(conflicting)
        totals["n_with_nonfinite_or_nonpositive"] += 1 if bad else 0
        totals["n_nonfinite_or_nonpositive_values"] += bad
        totals["n_descents_total"] += descents
        totals["n_assets_not_strictly_increasing"] += 0 if strictly_increasing else 1
    return {"totals": totals, "per_asset": per_asset}


def _dist_close(a, b, tol: float = TOL) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, int) and isinstance(b, int):
        return a == b
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def _dist_match(rec, ref, tol: float = TOL) -> dict:
    keys = ("min", "p10", "p50", "mean", "p90", "max", "n")
    diffs = {}
    ok = True
    for k in keys:
        rv = rec.get(k) if isinstance(rec, dict) else None
        fv = ref.get(k) if isinstance(ref, dict) else None
        match = _dist_close(rv, fv, tol)
        ok = ok and match
        diffs[k] = {"recomputed": rv, "h39": fv, "match": bool(match)}
    return {"match": bool(ok), "fields": diffs}


def compare_to_h39(computed: dict, h39: dict, coverage: dict) -> dict:
    ref_stats = h39.get("rankable_size_stats", {})
    ref_bands = h39.get("band_stats", {})
    ref_cov = h39.get("committed_panel_rank_coverage", {}).get("per_asset", {})

    universe_match = computed["universe_size"] == h39.get("universe_size")
    nonempty_match = (
        computed["n_assets_with_nonempty_series"]
        == h39.get("n_assets_with_nonempty_series")
    )

    n_match = _dist_match(computed["rankable_size_stats"], ref_stats)
    band_matches = {}
    for label in computed["band_stats"]:
        band_matches[label] = _dist_match(computed["band_stats"][label], ref_bands.get(label, {}))

    per_asset = {}
    n_per_asset_match = 0
    mismatches = []
    cov = coverage["per_asset"]
    for asset, ref in ref_cov.items():
        rec = cov.get(asset, {})
        checks = {
            "n_dates_ranked": rec.get("n_dates_ranked") == ref.get("n_dates_ranked"),
            "rank_min": rec.get("rank_min") == ref.get("rank_min"),
            "rank_max": rec.get("rank_max") == ref.get("rank_max"),
            "frac_study_dates_ranked": _dist_close(
                rec.get("frac_study_dates_ranked"), ref.get("frac_study_dates_ranked")
            ),
            "rank_p50": _dist_close(rec.get("rank_p50"), ref.get("rank_p50")),
        }
        ok = all(checks.values())
        per_asset[asset] = {"match": bool(ok), "checks": checks}
        if ok:
            n_per_asset_match += 1
        else:
            mismatches.append(asset)

    all_match = (
        universe_match
        and nonempty_match
        and n_match["match"]
        and all(b["match"] for b in band_matches.values())
        and n_per_asset_match == len(ref_cov)
    )
    return {
        "universe_size_match": bool(universe_match),
        "n_assets_with_nonempty_series_match": bool(nonempty_match),
        "rankable_size_stats": n_match,
        "band_stats": band_matches,
        "per_asset": {
            "n_match": n_per_asset_match,
            "n_total": len(ref_cov),
            "mismatches": mismatches,
            "detail": per_asset,
        },
        "all_match": bool(all_match),
    }


def frozen_hash_status() -> tuple:
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
    h39 = json.loads(H39_ARTIFACT.read_text(encoding="utf-8"))

    binance_universe = load_binance_universe()
    raw_groups = load_raw_groups()
    panel_groups = load_panel_groups()

    candidate_cap = groups_to_cap(raw_groups)
    legacy_cap = groups_to_cap(panel_groups)
    study_dates = load_study_dates()
    panel_assets = load_panel_assets()

    legacy_arm = set(panel_assets)
    candidate_arm = {a for a in binance_universe if a in candidate_cap and candidate_cap[a]}
    universe = legacy_arm | candidate_arm

    cap_obs = dict(candidate_cap)
    cap_obs.update(legacy_cap)

    computed = compute_rank_breadth(universe, cap_obs, study_dates)
    coverage = committed_panel_rank_coverage(
        panel_assets, universe, cap_obs, study_dates
    )
    computed.pop("_per_date", None)

    # Integrity of the cap source actually used: legacy from panel, candidate from raw.
    integrity_groups = {}
    integrity_groups.update({a: raw_groups[a] for a in candidate_arm if a in raw_groups})
    integrity_groups.update({a: panel_groups[a] for a in legacy_arm if a in panel_groups})
    integrity_assets = sorted(candidate_arm | legacy_arm)
    integrity = series_integrity(integrity_groups, integrity_assets)

    comparison = compare_to_h39(computed, h39, coverage)

    criteria = {
        "a_universe_size_match": comparison["universe_size_match"],
        "a_n_assets_with_nonempty_series_match": comparison[
            "n_assets_with_nonempty_series_match"
        ],
        "b_rankable_size_stats_match": comparison["rankable_size_stats"]["match"],
        "b_band_stats_match": all(
            b["match"] for b in comparison["band_stats"].values()
        ),
        "c_per_asset_rank_stats_match": (
            comparison["per_asset"]["n_match"] == comparison["per_asset"]["n_total"]
        ),
        "d_integrity_clean": (
            integrity["totals"]["n_missing_source"] == 0
            and integrity["totals"]["n_empty"] == 0
            and integrity["totals"]["n_conflicting_duplicate_dates"] == 0
            and integrity["totals"]["n_nonfinite_or_nonpositive_values"] == 0
        ),
    }
    label = (
        "RANK_BREADTH_REPRODUCED"
        if all(criteria.values())
        else "RANK_BREADTH_REPRODUCTION_FAILED"
    )

    frozen_before, ok_before = frozen_hash_status()

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": now_utc(),
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-REPRO-001/"
            "preregistrations/RANKBREADTH_REPRO_001_v1.md"
        ),
        "question": (
            "Does an independent, stdlib-only re-derivation from the committed raw "
            "cap archive, kline daily index and candidate validation reproduce the "
            "H39 RANK_BREADTH_MEASURABLE verdict, and are the committed candidate "
            "cap series free of conflicting duplicate dates and non-finite/"
            "non-positive values that would undermine that verdict?"
        ),
        "scope_note": (
            "Computational reproducibility on the SAME committed inputs as H39; "
            "NOT an independent data-source verification. Does not change "
            "universe_frontier.json:historical_rank_coverage_state."
        ),
        "h39_reference": {
            "path": H39_ARTIFACT.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(H39_ARTIFACT),
        },
        "universe": {
            "universe_size": computed["universe_size"],
            "legacy_arm_size": len(legacy_arm),
            "candidate_arm_size": len(candidate_arm),
            "n_assets_with_nonempty_series": computed["n_assets_with_nonempty_series"],
            "match_h39": comparison["universe_size_match"],
        },
        "study_window": {
            "date_first": computed["study_date_first"],
            "date_last": computed["study_date_last"],
            "n_dates": computed["n_study_dates"],
            "source": "binance_klines_BTCUSDT.csv open_time (ms) daily UTC index",
        },
        "recomputed": {
            "rankable_size_stats": computed["rankable_size_stats"],
            "band_stats": computed["band_stats"],
            "frac_dates_rankable_ge_min_median": computed[
                "frac_dates_rankable_ge_min_median"
            ],
        },
        "comparison_to_h39": comparison,
        "raw_series_integrity": integrity,
        "availability": {
            "forward_fill_used": False,
            "note": (
                "Each cap value is keyed to its own observation date (time[:10]); "
                "no value is carried forward. Look-ahead is structurally impossible "
                "by construction; duplicate-date conflicts would be the only "
                "ambiguity and are counted above."
            ),
        },
        "decision_rule": {
            "statement": (
                "RANK_BREADTH_REPRODUCED iff universe/nonempty sizes match H39; "
                "median N(d) and all band fracs/distributions match within 1e-9; "
                "every legacy per-asset rank stat matches H39; and integrity is "
                "clean (no missing source, no conflicting duplicate dates, no "
                "non-finite/non-positive values used)."
            ),
            "tolerance": TOL,
            "min_median_n": MIN_MEDIAN_N,
            "min_band_count": MIN_BAND_COUNT,
            "band_fraction_threshold": BAND_FRACTION_THRESHOLD,
        },
        "decision": {"criteria": criteria, "label": label},
        "label": label,
        "frozen_hashes_verified": frozen_before,
        "all_frozen_hashes_match": ok_before,
        "note": (
            "EXPLORATORY_ONLY reproducibility + integrity diagnostic on committed "
            "development inputs. No returns, spreads, dispersion states, p-values, "
            "costs or inference computed. Does not validate, replace or unlock any "
            "confirmatory track (H1/H6/H7/H10) and is not independent confirmation. "
            "A green result proves only that H39 is reproducible from the committed "
            "inputs and that the committed cap series are internally consistent."
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
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        out = AUDIT_DIR / f"H004V106_rank_breadth_reproducibility_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out.relative_to(ROOT)), "label": audit["label"],
                      "all_match": audit["comparison_to_h39"]["all_match"],
                      "integrity_clean": audit["decision"]["criteria"]["d_integrity_clean"]}))
    return 0 if audit["all_frozen_hashes_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())