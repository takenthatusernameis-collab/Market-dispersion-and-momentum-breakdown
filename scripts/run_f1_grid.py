#!/usr/bin/env python3
"""DISPERSION-003 full 216-cell sensitivity grid on the F1-repaired panels.

DISP-003-F1GRID-001 (H26, EXPLORATORY_ONLY). The F1COVERAGE-001 repair (H23)
re-acquired four symbols (1INCHUSDT, AAVEUSDT, ACHUSDT, AGLDUSDT) missing from
the committed DISPERSION-003 Binance archive for 2025-01..2026-09, raising the
descriptive eligible-asset count on the canonical H004V106 formation dates from
26-27 to 29-31. F1SENS-002 (H24) measured the anchor point-estimate move only;
F1STAB-003 (H25) checked two stability warnings under the repair. This script
runs the complete 216-cell DISPERSION-003 sensitivity grid on the F1-repaired
panel set, in two arms:

  Arm A -- committed panels exactly as-is (baseline).
  Arm B -- committed panels with the four F1-repaired kline panels overriding
           the committed versions in memory (funding panels NOT substituted).

No p-value promotion, no multiple-testing family for inference, no hypothesis
conclusion: bootstrap p-values and Holm rejections are computed per arm for
descriptive contrast only. The committed panels, raw archive, canonical grid
ledger/summary and frozen forward blocks are read-only and byte-verified
unchanged before and after the run. Arm A must reproduce the committed
DISPERSION-003 grid_result_ledger.json within 1e-9 on every cell (fidelity
anchor); on fidelity failure the script aborts and writes no comparison.

All inputs are read-only; no network; all outputs are written under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/ (never into the
committed HARMONY-CRYPTO-EDGE-004-DISPERSION-003/ tree).

Usage:
    python3 scripts/run_f1_grid.py [--out-dir <path>]

Preregistration: artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001/
preregistrations/F1_GRID_COVERAGE_REPAIR_v1.md (committed before computation).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import run_dispersion003_grid as ge  # unmodified grid engine (read-only import)

OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-001"
F1_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"

OLD_EXP_DIR = ROOT / "artifacts" / OLD_EXP
NEW_EXP_DIR = ROOT / "artifacts" / NEW_EXP
OLD_PANELS = OLD_EXP_DIR / "data" / "panels"
F1_PANELS = ROOT / "artifacts" / F1_EXP / "data" / "panels"
F1_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]

COMMITTED_LEDGER = OLD_EXP_DIR / "grid_result_ledger.json"
GRID_MANIFEST = OLD_EXP_DIR / "grid_config_manifest.json"
FROZEN_ARTIFACT_RELS = [
    "forward_block/forward_block_evaluation.json",
    "forward_block_h10_fresh/forward_block_evaluation.json",
    "grid_result_ledger.json",
    "grid_summary.json",
]

OUT_CHECKPOINTS = NEW_EXP_DIR / "grid_checkpoints"
OUT_LEDGER = NEW_EXP_DIR / "grid_result_ledger.json"
OUT_SUMMARY = NEW_EXP_DIR / "grid_summary.json"

FIDELITY_TOL = 1e-9
SKIP_FIELDS = {"evaluated_utc"}


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_binance_panel(panel_dir: Path, kind: str) -> dict:
    out = {}
    for p in sorted(panel_dir.glob(f"binance_{kind}_*.csv")):
        symbol = p.stem.replace(f"binance_{kind}_", "")
        df = pd.read_csv(p)
        if kind == "klines":
            df = df.rename(columns={"open_time": "ts"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["close"] = pd.to_numeric(df["close"], errors="coerce")
            out[symbol] = df[["date", "close"]].copy()
        else:
            df = df.rename(columns={"calc_time": "ts", "last_funding_rate": "funding_rate"})
            df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
            df["funding_rate"] = pd.to_numeric(df["funding_rate"], errors="coerce")
            out[symbol] = df[["date", "funding_rate"]].copy()
    return out


def load_marketcap(panel_dir: Path) -> pd.DataFrame:
    p = panel_dir / "marketcap_panel.csv"
    df = pd.read_csv(p, dtype={"CapMrktCurUSD": str, "CapMrktEstUSD": str})
    df["date"] = df["date"].astype(str).str.slice(0, 10)
    df["CapMrktEstUSD"] = pd.to_numeric(df["CapMrktEstUSD"], errors="coerce")
    return df[["date", "asset", "CapMrktEstUSD"]]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def inventory_hashes(panel_dirs: list[Path]) -> dict[str, str]:
    hashes = {}
    for panel_dir in panel_dirs:
        for p in sorted(panel_dir.rglob("*.csv")):
            rel = p.relative_to(ROOT).as_posix()
            hashes[rel] = sha256_file(p)
    return hashes


def frozen_hashes() -> dict[str, str]:
    hashes = {}
    for rel in FROZEN_ARTIFACT_RELS:
        p = OLD_EXP_DIR / rel
        hashes[rel] = sha256_file(p) if p.exists() else None
    return hashes


def build_arm_panels(committed_px: dict, committed_fd: dict):
    """Return (arm_A, arm_B) where each is (px, fd, mc).

    Arm B overrides the four F1 kline panels in memory; funding is shared with
    arm A (F1COVERAGE-001 repaired klines only).
    """
    mc = load_marketcap(OLD_PANELS)
    px_a = committed_px
    fd_a = committed_fd
    px_b = {symbol: df.copy() for symbol, df in committed_px.items()}
    f1_px = load_binance_panel(F1_PANELS, "klines")
    for symbol in F1_SYMBOLS:
        if symbol not in f1_px:
            raise FileNotFoundError(f"F1-repaired kline panel missing: {symbol}")
        px_b[symbol] = f1_px[symbol]
    return (px_a, fd_a, mc), (px_b, fd_a, mc)


def evaluate_arm(arm_label: str, px: dict, fd: dict, mc: pd.DataFrame,
                 rows: list[dict], checkpoint: dict, ckpt_path: Path):
    """Evaluate all manifest rows for one panel arm; returns post-processed cells."""
    px_wide = ge.build_price_wide_all(px)
    mom_cache = ge.MomentumCache(px_wide)
    elig_legacy = ge.build_eligibility_map(mc, px, fd, "legacy28_comparator")
    elig_expanding = ge.build_eligibility_map(mc, px, fd, "expanding_point_in_time")
    elig_by_arm = {"legacy28_comparator": elig_legacy,
                   "expanding_point_in_time": elig_expanding}

    expected = len(rows)
    print(f"[grid] arm {arm_label}: {expected} cells, "
          f"{len(checkpoint)} already checkpointed", flush=True)
    for i, row in enumerate(rows, start=1):
        params = row["parameters"]
        elig_map = elig_by_arm[params["universe_arm"]]
        ge.evaluate_cell(row["config_id"], params, elig_map, px_wide,
                         mom_cache, checkpoint)
        if i % 10 == 0 or i == expected:
            ckpt_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
            res = checkpoint[row["config_id"]]
            print(f"[grid] arm {arm_label} {i}/{expected} cells done, "
                  f"last={row['config_id']} status={res['status']}", flush=True)

    # Per-look p-values via dependence-aware block bootstrap; Holm step-down
    # across the complete 216-cell family for the registered 1x net endpoint,
    # per arm (descriptive contrast only; not a confirmation family).
    pvals = {}
    pval_meta = {}
    for cid, res in checkpoint.items():
        if res["status"] != "OK":
            continue
        formations = res.get("formations", [])
        hi = [r["spread_net_1x"] for r in formations if r.get("state") == "high"]
        lo = [r["spread_net_1x"] for r in formations if r.get("state") == "low"]
        p = ge.bootstrap_diff_pvalue(hi, lo)
        pvals[cid] = p
        pval_meta[cid] = {
            "n_high": len(hi), "n_low": len(lo),
            "high_low_diff_net_1x": res.get("high_low_diff_net_1x"),
            "bootstrap_p_two_sided": p,
        }
    holm_reject = ge.holm_step_down(pvals, ge.HOLM_ALPHA) if pvals else {}
    for cid in checkpoint:
        meta = pval_meta.get(cid)
        if meta is None:
            continue
        checkpoint[cid]["pvalue_bootstrap_two_sided"] = meta["bootstrap_p_two_sided"]
        checkpoint[cid]["pvalue_note"] = (
            "two-sided block-bootstrap p-value on high/low dispersion-state "
            "net-1x series (block_len=21, n_boot=1000); Holm step-down across "
            "all 216 cells of this arm"
        )
        checkpoint[cid]["holm_rejected"] = bool(holm_reject.get(cid, False))
    ckpt_path.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
    ok = [r for r in checkpoint.values() if r["status"] == "OK"]
    blocked = [r for r in checkpoint.values() if r["status"] == "BLOCKED"]
    failed = [r for r in checkpoint.values() if r["status"] == "FAILED"]
    return {
        "cells_evaluated": len(checkpoint),
        "cells_ok": len(ok),
        "cells_blocked": len(blocked),
        "cells_failed": len(failed),
        "holm_rejected_count": sum(1 for v in holm_reject.values() if v),
        "cells": checkpoint,
    }


def values_close(a, b, path: str, drifted: list[str]) -> None:
    if isinstance(a, float) or isinstance(b, float):
        try:
            fa, fb = float(a), float(b)
        except (TypeError, ValueError):
            drifted.append(f"  {path}: type mismatch {a!r} vs {b!r}")
            return
        if math.isnan(fa) and math.isnan(fb):
            return
        if abs(fa - fb) > FIDELITY_TOL:
            drifted.append(f"  {path}: {a!r} vs {b!r} (diff {abs(fa - fb):.3e})")
        return
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            drifted.append(f"  {path}: key mismatch "
                           f"{sorted(set(a) ^ set(b))}")
            for k in sorted(set(a) & set(b)):
                values_close(a[k], b[k], f"{path}.{k}", drifted)
        else:
            for k in sorted(a):
                values_close(a[k], b[k], f"{path}.{k}", drifted)
        return
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            drifted.append(f"  {path}: list length {len(a)} vs {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            values_close(x, y, f"{path}[{i}]", drifted)
        return
    if a != b:
        drifted.append(f"  {path}: {a!r} vs {b!r}")


def fidelity_check(arm_a_cells: dict, committed_cells: dict) -> dict:
    drifted = []
    if set(arm_a_cells) != set(committed_cells):
        drifted.append("  cell id mismatch: "
                       f"{sorted(set(arm_a_cells) ^ set(committed_cells))}")
    for cid in sorted(set(arm_a_cells) & set(committed_cells)):
        a, b = arm_a_cells[cid], committed_cells[cid]
        for key in sorted(set(a) | set(b)):
            if key in SKIP_FIELDS:
                continue
            aval = a.get(key, "<MISSING>")
            bval = b.get(key, "<MISSING>")
            if key == "formations":
                values_close(aval, bval, f"{cid}.formations", drifted)
                continue
            values_close(aval, bval, f"{cid}.{key}", drifted)
    return {
        "passed": len(drifted) == 0,
        "max_abs_diff": None,
        "drifted": drifted[:50],
        "drift_count": len(drifted),
        "compared_cells": len(set(arm_a_cells) & set(committed_cells)),
    }


def cell_counts(summary_block: dict) -> dict:
    cells = summary_block["cells"]
    return {
        "cells_evaluated": len(cells),
        "cells_ok": sum(1 for r in cells.values() if r["status"] == "OK"),
        "cells_blocked": sum(1 for r in cells.values() if r["status"] == "BLOCKED"),
        "cells_failed": sum(1 for r in cells.values() if r["status"] == "FAILED"),
        "holm_rejected_count": sum(1 for r in cells.values()
                                   if r.get("holm_rejected") is True),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("Usage:")[0])
    parser.add_argument("--out-dir", default=str(NEW_EXP_DIR),
                        help="output directory (default: the F1GRID-001 experiment root)")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    out_checkpoints = out_dir / "grid_checkpoints"
    out_checkpoints.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- read-only verification: capture input hashes BEFORE computation ---
    panels_before = inventory_hashes([OLD_PANELS, F1_PANELS])
    frozen_before = frozen_hashes()
    missing_frozen = [rel for rel, h in frozen_before.items() if h is None]
    if missing_frozen:
        print(f"[grid] ERROR: missing frozen artifacts: {missing_frozen}")
        return 1
    print(f"[grid] pre-run hashes captured: {len(panels_before)} panel CSVs, "
          f"{len(frozen_before)} frozen artifacts", flush=True)

    manifest = json.loads(GRID_MANIFEST.read_text(encoding="utf-8"))
    rows = manifest["configurations"]
    expected = manifest["combination_count"]
    if len(rows) != expected:
        raise ValueError(f"manifest has {len(rows)} cells, expected {expected}")

    committed_px = load_binance_panel(OLD_PANELS, "klines")
    committed_fd = load_binance_panel(OLD_PANELS, "funding")
    (px_a, fd_a, mc), (px_b, fd_b, mc_b) = build_arm_panels(committed_px, committed_fd)

    ckpt_a = out_checkpoints / "cell_checkpoint_armA_committed.json"
    ckpt_b = out_checkpoints / "cell_checkpoint_armB_f1_repaired.json"
    checkpoint_a = json.loads(ckpt_a.read_text(encoding="utf-8")) if ckpt_a.exists() else {}
    checkpoint_b = json.loads(ckpt_b.read_text(encoding="utf-8")) if ckpt_b.exists() else {}

    arm_a = evaluate_arm("A (committed panels)", px_a, fd_a, mc, rows,
                         checkpoint_a, ckpt_a)

    # Fidelity anchor: arm A must reproduce the committed ledger exactly.
    committed = json.loads(COMMITTED_LEDGER.read_text(encoding="utf-8"))
    committed_cells = committed["cells"]
    fidelity = fidelity_check(arm_a["cells"], committed_cells)
    print(f"[grid] fidelity anchor vs committed ledger: "
          f"{'PASS' if fidelity['passed'] else 'FAIL'} "
          f"(compared {fidelity['compared_cells']} cells, "
          f"{fidelity['drift_count']} drifts)", flush=True)
    for d in fidelity["drifted"][:10]:
        print(f"[grid] fidelity drift: {d}", flush=True)
    if not fidelity["passed"]:
        print("[grid] FIDELITY FAILED: aborting, no comparison written.")
        return 1

    arm_b = evaluate_arm("B (F1-repaired klines)", px_b, fd_b, mc_b, rows,
                         checkpoint_b, ckpt_b)

    # --- read-only verification: input hashes must be unchanged AFTER ---
    panels_after = inventory_hashes([OLD_PANELS, F1_PANELS])
    frozen_after = frozen_hashes()
    panels_match = panels_before == panels_after
    frozen_match = all(frozen_before[rel] == frozen_after[rel]
                       for rel in FROZEN_ARTIFACT_RELS)
    print(f"[grid] post-run hash check: panels_match={panels_match} "
          f"frozen_match={frozen_match}", flush=True)
    if not (panels_match and frozen_match):
        print("[grid] ERROR: input hash mismatch after run; aborting.")
        return 1

    # --- descriptive contrasts: cells OK in both arms ---
    cell_deltas = []
    toward_zero = 0
    coverage_delta_count = 0
    coverage_delta_sum = 0.0
    n_compare = 0
    holm_status_changes = 0
    for cid in sorted(set(arm_a["cells"]) & set(arm_b["cells"])):
        ra, rb = arm_a["cells"][cid], arm_b["cells"][cid]
        if ra["status"] != "OK" or rb["status"] != "OK":
            continue
        n_compare += 1
        d = {
            "config_id": cid,
            "universe_arm": ra["parameters"]["universe_arm"],
            "status_a": ra["status"], "status_b": rb["status"],
            "delta_n_formations": rb["n_formations"] - ra["n_formations"],
            "delta_n_high": rb["n_high"] - ra["n_high"],
            "delta_n_low": rb["n_low"] - ra["n_low"],
            "delta_n_mid": rb["n_mid"] - ra["n_mid"],
            "delta_high_low_diff_net_1x": (
                (rb["high_low_diff_net_1x"] - ra["high_low_diff_net_1x"])
                if ra["high_low_diff_net_1x"] is not None
                and rb["high_low_diff_net_1x"] is not None else None),
            "delta_spread_net_1x_mean": (
                (rb["spread_net_1x_mean"] - ra["spread_net_1x_mean"])
                if ra["spread_net_1x_mean"] is not None
                and rb["spread_net_1x_mean"] is not None else None),
            "delta_spread_net_1x_median": (
                (rb["spread_net_1x_median"] - ra["spread_net_1x_median"])
                if ra["spread_net_1x_median"] is not None
                and rb["spread_net_1x_median"] is not None else None),
            "delta_eligible_assets_mean": (
                rb["eligible_assets_per_date"]["mean"]
                - ra["eligible_assets_per_date"]["mean"]),
            "holm_rejected_a": bool(ra.get("holm_rejected")),
            "holm_rejected_b": bool(rb.get("holm_rejected")),
        }
        if d["holm_rejected_a"] != d["holm_rejected_b"]:
            holm_status_changes += 1
        diff_a = ra["high_low_diff_net_1x"]
        diff_b = rb["high_low_diff_net_1x"]
        if diff_a is not None and diff_b is not None:
            if abs(diff_b) < abs(diff_a):
                toward_zero += 1
            delta_el = d["delta_eligible_assets_mean"]
            coverage_delta_sum += delta_el
            if delta_el >= 2.0:
                coverage_delta_count += 1
        cell_deltas.append(d)

    labels = {
        "DIRECTIONAL_ATTENUATION": (
            toward_zero > n_compare / 2 if n_compare else False),
        "COVERAGE_EXPANSION": (
            coverage_delta_count > n_compare / 2 if n_compare else False),
        "HOLM_STATUS_CHANGE": holm_status_changes > 0,
    }
    anchor_a = arm_a["cells"].get("H004V106", {})
    anchor_b = arm_b["cells"].get("H004V106", {})
    comp_a = arm_a["cells"].get("H004V105", {})
    comp_b = arm_b["cells"].get("H004V105", {})
    labels["ANCHOR_HOLM_CHANGE"] = (
        bool(anchor_a.get("holm_rejected")) != bool(anchor_b.get("holm_rejected")))
    labels["COMPARATOR_HOLM_CHANGE"] = (
        bool(comp_a.get("holm_rejected")) != bool(comp_b.get("holm_rejected")))
    coverage_delta_mean = (coverage_delta_sum / n_compare) if n_compare else 0.0

    ledger = {
        "experiment_id": NEW_EXP,
        "grid_id": manifest["grid_id"],
        "source_manifest": str(GRID_MANIFEST.relative_to(ROOT)),
        "evaluated_utc": now_utc(),
        "expected_cells": expected,
        "cells_total": 2 * expected,
        "arms": {
            "A_committed_panels": arm_a,
            "B_f1_repaired_klines": arm_b,
        },
        "fidelity_anchor": {
            "passed": fidelity["passed"],
            "against": str(COMMITTED_LEDGER.relative_to(ROOT)),
            "compared_cells": fidelity["compared_cells"],
            "drift_count": fidelity["drift_count"],
            "note": "arm A must reproduce the committed DISPERSION-003 "
                    "grid_result_ledger.json within 1e-9 on every cell; "
                    "on failure the script aborts and writes no comparison",
        },
        "read_only_checks": {
            "panel_files": len(panels_before),
            "panels_before_after_hashes_match": panels_match,
            "frozen_artifacts": {
                rel: {"before": frozen_before[rel], "after": frozen_after[rel],
                      "match": frozen_before[rel] == frozen_after[rel]}
                for rel in FROZEN_ARTIFACT_RELS
            },
            "frozen_hashes_match": frozen_match,
        },
        "pvalue_method": (
            "two-sided block-bootstrap p-value on high/low dispersion-state "
            "net-1x series (block_len=21, n_boot=1000); Holm step-down across "
            "all 216 cells per arm; descriptive contrast only"),
    }
    out_ledger = out_dir / "grid_result_ledger.json"
    out_summary = out_dir / "grid_summary.json"
    out_ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")

    summary = {
        "experiment_id": NEW_EXP,
        "evaluated_utc": now_utc(),
        "expected_cells": expected,
        "arms": {
            "A_committed_panels": cell_counts(arm_a),
            "B_f1_repaired_klines": cell_counts(arm_b),
        },
        "holm_alpha": ge.HOLM_ALPHA,
        "n_cells_ok_both_arms": n_compare,
        "delta_mean_eligible_assets": coverage_delta_mean,
        "aggregate_labels": labels,
        "primary_anchor_legacy_H004V105": {
            "arm_a": {k: comp_a.get(k) for k in
                      ("n_formations", "n_high", "n_low", "n_mid",
                       "high_low_diff_net_1x", "spread_net_1x_mean",
                       "spread_net_1x_median", "holm_rejected")},
            "arm_b": {k: comp_b.get(k) for k in
                      ("n_formations", "n_high", "n_low", "n_mid",
                       "high_low_diff_net_1x", "spread_net_1x_mean",
                       "spread_net_1x_median", "holm_rejected")},
        },
        "primary_anchor_expanding_H004V106": {
            "arm_a": {k: anchor_a.get(k) for k in
                      ("n_formations", "n_high", "n_low", "n_mid",
                       "high_low_diff_net_1x", "spread_net_1x_mean",
                       "spread_net_1x_median", "holm_rejected")},
            "arm_b": {k: anchor_b.get(k) for k in
                      ("n_formations", "n_high", "n_low", "n_mid",
                       "high_low_diff_net_1x", "spread_net_1x_mean",
                       "spread_net_1x_median", "holm_rejected")},
        },
        "cell_deltas": cell_deltas,
        "note": "Descriptive sensitivity contrast only: no p-value promotion, "
                "no multiple-testing family for inference, no hypothesis "
                "conclusion; EXPLORATORY_ONLY development evidence on "
                "already-inspected panels.",
    }
    out_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")

    ok_a = arm_a["cells_ok"]; ok_b = arm_b["cells_ok"]
    rej_a = arm_a["holm_rejected_count"]; rej_b = arm_b["holm_rejected_count"]
    print(f"[grid] arm A: {ok_a}/{expected} OK, holm_rejected={rej_a}")
    print(f"[grid] arm B: {ok_b}/{expected} OK, holm_rejected={rej_b}")
    print(f"[grid] cells OK in both arms: {n_compare}")
    print(f"[grid] labels: {labels}")
    print(f"[grid] mean delta eligible assets (B - A): {coverage_delta_mean:+.4f}")
    print(f"[grid] ledger -> {out_ledger.relative_to(ROOT)}")
    print(f"[grid] summary -> {out_summary.relative_to(ROOT)}")
    print(f"[grid] checkpoints -> {out_checkpoints.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
