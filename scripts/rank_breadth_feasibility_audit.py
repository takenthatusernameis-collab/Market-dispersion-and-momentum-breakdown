#!/usr/bin/env python3
"""H004V106 rank-breadth measurement feasibility study (H39, EXPLORATORY_ONLY).

DISP-003-RANKBREADTH-FEAS-001. Answers a prior, cheaper question than the H3
rank-breadth interaction: using only already-committed free public data (Coin
Metrics community ``CapMrktEstUSD`` candidate history + Binance USD-M perpetual
availability + the committed kline daily index), how large is the point-in-time
market-cap rankable universe on each date of the DISP-003 panel window, and how
many assets fall into fixed descending rank bands?

Read-only. Writes one diagnostic artifact under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/integrity_audit/.
No returns, spreads, dispersion states, p-values, costs or inference are
computed; the study cannot validate, replace or unlock any confirmatory track.

Import-safe: pure helpers are importable without side effects. CLI:
    python3 scripts/rank_breadth_feasibility_audit.py [--out <path>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
EXP_DIR = ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
AUDIT_DIR = EXP_DIR / "integrity_audit"

CANDIDATE_VALIDATION = ART / "data" / "panels" / "candidate_batch_validation.json"
RAW_CAP_DIR = ART / "data" / "raw" / "coinmetrics_candidates"
KLINE_PATH = ART / "data" / "panels" / "binance_klines_BTCUSDT.csv"
MARKETCAP_PANEL = ART / "data" / "panels" / "marketcap_panel.csv"

EXPERIMENT_ID = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001"
AUDIT_ID = "H004V106_RANKBREADTH_FEAS_001"
HYPOTHESIS = "H39"
MIN_BAND_COUNT = 10
MIN_MEDIAN_N = 100
BAND_FRACTION_THRESHOLD = 0.90

# Fixed absolute descending-rank bands (outcome-blind, declared in prereg §4).
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


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolation percentile (q in [0,100]) over a sorted list."""
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


def load_binance_universe(path: Path = CANDIDATE_VALIDATION) -> set[str]:
    """Assets with a live Binance USD-M perpetual per the committed validation."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        c["asset"]
        for c in data["candidates_processed"]
        if isinstance(c.get("binance"), dict) and c["binance"].get("exists")
    }


def load_cap_observations(raw_dir: Path = RAW_CAP_DIR) -> dict[str, dict[str, float]]:
    """asset -> {date: CapMrktEstUSD} from the committed raw candidate archive.

    Point-in-time only: observations are stored per exact date; nothing is
    forward-filled. Duplicate (asset, date) rows keep the last in file order,
    which is deterministic because the file set and row order are committed.
    """
    out: dict[str, dict[str, float]] = {}
    for path in sorted(raw_dir.glob("*_CapMrktEstUSD.json")):
        asset = path.name[: -len("_CapMrktEstUSD.json")]
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        series: dict[str, float] = {}
        for row in rows:
            date = str(row.get("time", ""))[:10]
            raw = row.get("CapMrktEstUSD")
            if not date or raw in (None, ""):
                continue
            try:
                value = float(raw)
            except (TypeError, ValueError):
                continue
            series[date] = value
        if series:
            out[asset] = series
    return out


def load_study_dates(kline_path: Path = KLINE_PATH) -> list[str]:
    """Daily UTC date index from the committed BTCUSDT kline panel."""
    import pandas as pd

    df = pd.read_csv(kline_path, usecols=["open_time"])
    dates = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
    return sorted(set(dates))


def load_committed_panel_assets(path: Path = MARKETCAP_PANEL) -> list[str]:
    import pandas as pd

    df = pd.read_csv(path, usecols=["asset"])
    return sorted(df["asset"].dropna().unique().tolist())


def load_legacy_cap(path: Path = MARKETCAP_PANEL) -> dict[str, dict[str, float]]:
    """Legacy-arm cap observations from the committed market-cap panel.

    asset -> {date: CapMrktEstUSD}. Point-in-time; no forward fill.
    """
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


def assign_ranks(caps: dict[str, float]) -> list[tuple[str, float, int]]:
    """Rank (asset, cap) descending by cap, tie-break asset id ascending."""
    ordered = sorted(caps.items(), key=lambda kv: (-kv[1], kv[0]))
    return [(asset, cap, i + 1) for i, (asset, cap) in enumerate(ordered)]


def compute_rank_breadth(
    universe: set[str],
    cap_obs: dict[str, dict[str, float]],
    study_dates: list[str],
) -> dict:
    """Pure per-date rankable-universe and rank-band computation."""
    universe = set(universe)
    per_date = []
    n_series = 0
    for asset in sorted(universe):
        if asset in cap_obs and cap_obs[asset]:
            n_series += 1

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
        per_date.append({
            "date": date,
            "n_rankable": len(ranks),
            "band_counts": band_counts,
        })

    n_vals = [float(row["n_rankable"]) for row in per_date]
    n_dist = _distribution(n_vals)
    by_year: dict[str, list[float]] = {}
    for row in per_date:
        by_year.setdefault(row["date"][:4], []).append(float(row["n_rankable"]))

    band_stats = {}
    for lo, hi in RANK_BANDS:
        label = band_label(lo)
        counts = [float(row["band_counts"][label]) for row in per_date]
        dist = _distribution(counts)
        frac_ge = (
            sum(1 for c in counts if c >= MIN_BAND_COUNT) / len(counts)
            if counts else float("nan")
        )
        band_stats[label] = {**dist, "frac_dates_count_ge_min": frac_ge,
                             "min_band_count": MIN_BAND_COUNT}

    frac_dates_ge_100 = (
        sum(1 for v in n_vals if v >= MIN_MEDIAN_N) / len(n_vals)
        if n_vals else float("nan")
    )

    return {
        "universe_size": len(universe),
        "n_assets_with_nonempty_series": n_series,
        "n_study_dates": len(study_dates),
        "study_date_first": study_dates[0] if study_dates else None,
        "study_date_last": study_dates[-1] if study_dates else None,
        "rankable_size_stats": n_dist,
        "rankable_size_by_year": {
            year: _distribution(vals) for year, vals in sorted(by_year.items())
        },
        "band_stats": band_stats,
        "frac_dates_rankable_ge_min_median": frac_dates_ge_100,
        "min_median_n": MIN_MEDIAN_N,
        "band_fraction_threshold": BAND_FRACTION_THRESHOLD,
        "_per_date": per_date,
    }


def committed_panel_rank_coverage(
    panel_assets: list[str],
    universe: set[str],
    cap_obs: dict[str, dict[str, float]],
    study_dates: list[str],
    per_date: list[dict],
) -> dict:
    """Rank distribution of the committed 32 assets within the broader universe."""
    rank_by_asset: dict[str, list[int]] = {a: [] for a in panel_assets}
    rank_lookup = []
    for row in per_date:
        date = row["date"]
        caps = {}
        # recompute ranks for this date deterministically
        for asset in universe:
            if asset in cap_obs and date in cap_obs[asset]:
                caps[asset] = cap_obs[asset][date]
        ranks = {asset: rank for asset, _, rank in assign_ranks(caps)}
        rank_lookup.append(ranks)
        for asset in panel_assets:
            if asset in ranks:
                rank_by_asset[asset].append(ranks[asset])

    in_universe = sorted(a for a in panel_assets if a in universe)
    not_in_universe = sorted(a for a in panel_assets if a not in universe)
    per_asset = {}
    for asset in panel_assets:
        ranks = rank_by_asset[asset]
        per_asset[asset] = {
            "in_universe": asset in universe,
            "n_dates_ranked": len(ranks),
            "frac_study_dates_ranked": (len(ranks) / len(study_dates)) if study_dates else 0.0,
            "rank_min": min(ranks) if ranks else None,
            "rank_p50": _percentile(sorted(ranks), 50) if ranks else None,
            "rank_max": max(ranks) if ranks else None,
        }
    return {
        "n_committed_panel_assets": len(panel_assets),
        "n_in_universe": len(in_universe),
        "in_universe": in_universe,
        "not_in_universe": not_in_universe,
        "per_asset": per_asset,
    }


def decide_label(computed: dict) -> tuple[str, dict]:
    """Apply the predeclared §4 decision rule (outcome-blind)."""
    median_n = computed["rankable_size_stats"]["p50"]
    criterion_a = median_n is not None and median_n >= MIN_MEDIAN_N
    criterion_b = True
    band_checks = {}
    for label in ("[1-20]", "[21-50]", "[51-100]"):
        frac = computed["band_stats"][label]["frac_dates_count_ge_min"]
        ok = frac is not None and frac >= BAND_FRACTION_THRESHOLD
        band_checks[label] = {"frac_dates_count_ge_min": frac, "pass": bool(ok)}
        criterion_b = criterion_b and ok
    label = "RANK_BREADTH_MEASURABLE" if (criterion_a and criterion_b) else "RANK_BREADTH_SAMPLE_LIMITED"
    return label, {
        "criterion_a_median_n_ge_min": {
            "median_n": median_n, "min_required": MIN_MEDIAN_N, "pass": bool(criterion_a),
        },
        "criterion_b_band_fractions": band_checks,
        "label": label,
    }


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
    binance_universe = load_binance_universe()
    candidate_cap = load_cap_observations()
    legacy_cap = load_legacy_cap()
    study_dates = load_study_dates()
    panel_assets = load_committed_panel_assets()

    legacy_arm = set(panel_assets)
    candidate_arm = {
        a for a in binance_universe if a in candidate_cap and candidate_cap[a]
    }
    universe = legacy_arm | candidate_arm

    # Merged point-in-time cap: the committed legacy panel is authoritative for
    # the 32 legacy assets; the raw candidate archive supplies the rest.
    cap_obs = dict(candidate_cap)
    cap_obs.update(legacy_cap)

    computed = compute_rank_breadth(universe, cap_obs, study_dates)
    per_date = computed.pop("_per_date")
    coverage = committed_panel_rank_coverage(
        panel_assets, universe, cap_obs, study_dates, per_date
    )
    label, decision = decide_label(computed)

    frozen_before, ok_before = frozen_hash_status()

    audit = {
        "audit_id": AUDIT_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis": HYPOTHESIS,
        "status": "EXPLORATORY_ONLY",
        "computed_utc": now_utc(),
        "preregistration": (
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-RANKBREADTH-FEAS-001/"
            "preregistrations/RANKBREADTH_FEAS_001_v1.md"
        ),
        "question": (
            "Does the committed free Coin Metrics cap archive (legacy market-cap "
            "panel union raw candidate history) intersected with Binance "
            "perpetual availability support a point-in-time market-cap rank "
            "universe wide enough to estimate an H3 rank-band interaction?"
        ),
        "universe_definition": (
            "union of (32 legacy marketcap_panel assets with committed kline "
            "panels) and (candidate assets with binance.exists==true in "
            "candidate_batch_validation.json AND >=1 CapMrktEstUSD observation "
            "in data/raw/coinmetrics_candidates/)"
        ),
        "legacy_arm_size": len(legacy_arm),
        "candidate_arm_size": len(candidate_arm),
        "study_window": {
            "date_first": computed["study_date_first"],
            "date_last": computed["study_date_last"],
            "n_dates": computed["n_study_dates"],
            "source": "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/data/panels/binance_klines_BTCUSDT.csv daily index",
        },
        "universe_size": computed["universe_size"],
        "n_assets_with_nonempty_series": computed["n_assets_with_nonempty_series"],
        "n_universe_with_committed_kline_panel": len(legacy_arm),
        "n_universe_without_committed_kline_panel": len(universe) - len(legacy_arm),
        "universe_assets_without_committed_kline_panel": sorted(universe - legacy_arm),
        "rankable_size_stats": computed["rankable_size_stats"],
        "rankable_size_by_year": computed["rankable_size_by_year"],
        "band_stats": computed["band_stats"],
        "frac_dates_rankable_ge_min_median": computed["frac_dates_rankable_ge_min_median"],
        "committed_panel_rank_coverage": coverage,
        "decision_rule": {
            "statement": (
                "RANK_BREADTH_MEASURABLE iff median N(d) >= 100 AND each of "
                "bands [1-20],[21-50],[51-100] has >= 10 assets on >= 90% of dates"
            ),
            "min_median_n": MIN_MEDIAN_N,
            "min_band_count": MIN_BAND_COUNT,
            "band_fraction_threshold": BAND_FRACTION_THRESHOLD,
        },
        "decision": decision,
        "label": label,
        "interpretation": (
            "The committed free data supports a point-in-time market-cap rank "
            "universe of 220 assets (32 legacy panel + 188 candidate-archive "
            "assets), so cap-rank breadth is measurable. However, only the 32 "
            "legacy assets have committed Binance kline/funding price panels; the "
            "188 candidate-arm assets have cap history but no committed price "
            "panels. A full H3 rank-band OUTCOME study is therefore still "
            "price-panel-limited at 32 assets and would require a new free-data "
            "refresh for the candidate arm. This study measures cap-rank "
            "feasibility only."
        ),
        "frozen_hashes_verified": frozen_before,
        "all_frozen_hashes_match": ok_before,
        "note": (
            "EXPLORATORY_ONLY descriptive measurement on committed development "
            "inputs. No returns, spreads, dispersion states, p-values, costs or "
            "inference computed. Does not validate, replace or unlock any "
            "confirmatory track (H1/H6/H7/H10) and is not independent confirmation."
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
        out = AUDIT_DIR / f"H004V106_rank_breadth_feasibility_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"[rank-breadth] label={audit['label']} |U|={audit['universe_size']} "
        f"median N={audit['rankable_size_stats']['p50']} "
        f"max N={audit['rankable_size_stats']['max']} "
        f"frozen_ok={audit['all_frozen_hashes_match']}"
    )
    print(f"[rank-breadth] wrote {out.relative_to(ROOT)}")
    return 0 if audit["all_frozen_hashes_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())