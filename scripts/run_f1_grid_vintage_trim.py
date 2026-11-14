#!/usr/bin/env python3
"""DISPERSION-003 full 216-cell sensitivity grid on F1-repaired panels, trimmed
to the frozen ledger vintage (as-of 2026-09-30).

DISP-003-F1GRID-002 (H27, EXPLORATORY_ONLY). Implements path (a) from the
F1GRID-001 execution-state audit: the committed panels now end 2026-10-31, so
arm A on the untrimmed panels cannot reproduce the frozen DISPERSION-003 grid
ledger (vintage ending 2026-09-30). This script trims price, funding and
marketcap inputs to <= 2026-09-30 for BOTH arms so arm A is estimand-compatible
with the committed ledger, requires arm A to reproduce that ledger within 1e-9
on every cell (fidelity anchor), then evaluates arm B (four F1-repaired kline
panels overriding the committed versions in memory; funding NOT substituted) on
the same trimmed vintage.

Descriptive sensitivity only: bootstrap p-values and Holm rejections are per-arm
contrast evidence, never promotion. No network; all committed inputs and frozen
artifacts are read-only and never written.

Outputs are written only under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002/.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import run_f1_grid as f1  # unmodified helpers (read-only import)
import run_dispersion003_grid as ge

OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1GRID-002"
F1_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001"

OLD_EXP_DIR = ROOT / "artifacts" / OLD_EXP
NEW_EXP_DIR = ROOT / "artifacts" / NEW_EXP
OLD_PANELS = OLD_EXP_DIR / "data" / "panels"
F1_PANELS = ROOT / "artifacts" / F1_EXP / "data" / "panels"
F1_SYMBOLS = ["1INCHUSDT", "AAVEUSDT", "ACHUSDT", "AGLDUSDT"]

COMMITTED_LEDGER = OLD_EXP_DIR / "grid_result_ledger.json"
GRID_MANIFEST = OLD_EXP_DIR / "grid_config_manifest.json"

ASOF_DATE = "2026-09-30"
FIDELITY_TOL = 1e-9
SKIP_FIELDS = {"evaluated_utc", "pvalue_note", "pvalue_bootstrap_two_sided", "holm_rejected"}


def trim_panel(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    d = df.copy()
    d = d[d[col].astype(str).str.slice(0, 10) <= ASOF_DATE]
    return d


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


def load_trimmed_panels():
    px_raw = f1.load_binance_panel(OLD_PANELS, "klines")
    fd_raw = f1.load_binance_panel(OLD_PANELS, "funding")
    mc_raw = f1.load_marketcap(OLD_PANELS)
    px = {k: trim_panel(v, "date") for k, v in px_raw.items()}
    fd = {k: trim_panel(v, "date") for k, v in fd_raw.items()}
    mc = trim_panel(mc_raw, "date")

    px_b = {symbol: df.copy() for symbol, df in px.items()}
    f1_px = f1.load_binance_panel(F1_PANELS, "klines")
    for symbol in F1_SYMBOLS:
        if symbol not in f1_px:
            raise FileNotFoundError(f"F1-repaired kline panel missing: {symbol}")
        px_b[symbol] = trim_panel(f1_px[symbol], "date")
    return (px, fd, mc), (px_b, fd, mc.copy())


def evaluate_arm(arm_label, px, fd, mc, rows, checkpoint, ckpt_path):
    px_wide = ge.build_price_wide_all(px)
    mom_cache = ge.MomentumCache(px_wide)
    elig_legacy = ge.build_eligibility_map(mc, px, fd, "legacy28_comparator")
    elig_expanding = ge.build_eligibility_map(mc, px, fd, "expanding_point_in_time")
    elig_by_arm = {
        "legacy28_comparator": elig_legacy,
        "expanding_point_in_time": elig_expanding,
    }
    expected = len(rows)
    print(f"[grid] arm {arm_label}: {expected} cells, "
          f"{len(checkpoint)} already checkpointed", flush=True)
    for i, row in enumerate(rows, start=1):
        params = row["parameters"]
        ge.evaluate_cell(row["config_id"], params,
                         elig_by_arm[params["universe_arm"]],
                         px_wide, mom_cache, checkpoint)
        if i % 10 == 0 or i == expected:
            ckpt_path.write_text(
                json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
            res = checkpoint[row["config_id"]]
            print(f"[grid] arm {arm_label} {i}/{expected} cells done, "
                  f"last={row['config_id']} status={res['status']}", flush=True)
    # per-arm descriptive bootstrap/Holm (contrast only)
    pvals, pval_meta = {}, {}
    for cid, res in checkpoint.items():
        if res["status"] != "OK":
            continue
        formations = res.get("formations", [])
        hi = [r["spread_net_1x"] for r in formations if r.get("state") == "high"]
        lo = [r["spread_net_1x"] for r in formations if r.get("state") == "low"]
        p = ge.bootstrap_diff_pvalue(hi, lo)
        pvals[cid] = p
        pval_meta[cid] = {"n_high": len(hi), "n_low": len(lo),
                          "bootstrap_p_two_sided": p}
    holm_reject = ge.holm_step_down(pvals, ge.HOLM_ALPHA) if pvals else {}
    for cid, meta in pval_meta.items():
        checkpoint[cid]["pvalue_bootstrap_two_sided"] = meta["bootstrap_p_two_sided"]
        checkpoint[cid]["pvalue_note"] = (
            "two-sided block-bootstrap p-value on high/low dispersion-state "
            "net-1x series (block_len=21, n_boot=1000); Holm step-down across "
            "all 216 cells of this arm; descriptive contrast only")
        checkpoint[cid]["holm_rejected"] = bool(holm_reject.get(cid, False))
    ckpt_path.write_text(
        json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
    return {
        "cells_evaluated": len(checkpoint),
        "cells_ok": sum(1 for r in checkpoint.values() if r["status"] == "OK"),
        "cells_blocked": sum(1 for r in checkpoint.values() if r["status"] == "BLOCKED"),
        "cells_failed": sum(1 for r in checkpoint.values() if r["status"] == "FAILED"),
        "holm_rejected_count": sum(1 for v in holm_reject.values() if v),
        "cells": checkpoint,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(NEW_EXP_DIR))
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    out_checkpoints = out_dir / "grid_checkpoints"
    out_checkpoints.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(GRID_MANIFEST.read_text(encoding="utf-8"))
    rows = manifest["configurations"]
    expected = manifest["combination_count"]
    if len(rows) != expected:
        raise ValueError(f"manifest has {len(rows)} cells, expected {expected}")

    (px_a, fd_a, mc_a), (px_b, fd_b, mc_b) = load_trimmed_panels()

    ckpt_a = out_checkpoints / "cell_checkpoint_armA_ledger_vintage.json"
    ckpt_b = out_checkpoints / "cell_checkpoint_armB_f1_repaired_ledger_vintage.json"
    checkpoint_a = (json.loads(ckpt_a.read_text(encoding="utf-8"))
                    if ckpt_a.exists() else {})
    checkpoint_b = (json.loads(ckpt_b.read_text(encoding="utf-8"))
                    if ckpt_b.exists() else {})

    arm_a = evaluate_arm("A (ledger-vintage committed)", px_a, fd_a, mc_a,
                         rows, checkpoint_a, ckpt_a)
    committed = json.loads(COMMITTED_LEDGER.read_text(encoding="utf-8"))
    fidelity = fidelity_check(arm_a["cells"], committed["cells"])
    print(f"[grid] fidelity anchor: {'PASS' if fidelity['passed'] else 'FAIL'} "
          f"(compared {fidelity['compared_cells']}, "
          f"drifts {fidelity['drift_count']})", flush=True)
    for d in fidelity.get("drifted", [])[:10]:
        print(f"[grid] drift: {d}", flush=True)
    if not fidelity["passed"]:
        print("[grid] FIDELITY FAILED: aborting, no comparison written.")
        return 1

    arm_b = evaluate_arm("B (ledger-vintage F1-repaired)", px_b, fd_b, mc_b,
                         rows, checkpoint_b, ckpt_b)

    # descriptive contrasts (reuse run_f1_grid summary logic via inline minimal form)
    cell_deltas = []
    n_compare = toward_zero = coverage_delta_count = holm_status_changes = 0
    coverage_delta_sum = 0.0
    for cid in sorted(set(arm_a["cells"]) & set(arm_b["cells"])):
        ra, rb = arm_a["cells"][cid], arm_b["cells"][cid]
        if ra["status"] != "OK" or rb["status"] != "OK":
            continue
        n_compare += 1
        da = ra["high_low_diff_net_1x"]; db = rb["high_low_diff_net_1x"]
        delta_el = (rb["eligible_assets_per_date"]["mean"]
                    - ra["eligible_assets_per_date"]["mean"])
        coverage_delta_sum += delta_el
        if delta_el >= 2.0:
            coverage_delta_count += 1
        if da is not None and db is not None and abs(db) < abs(da):
            toward_zero += 1
        if bool(ra.get("holm_rejected")) != bool(rb.get("holm_rejected")):
            holm_status_changes += 1
        cell_deltas.append({
            "config_id": cid, "universe_arm": ra["parameters"]["universe_arm"],
            "delta_n_formations": rb["n_formations"] - ra["n_formations"],
            "delta_n_high": rb["n_high"] - ra["n_high"],
            "delta_n_low": rb["n_low"] - ra["n_low"],
            "delta_n_mid": rb["n_mid"] - ra["n_mid"],
            "delta_high_low_diff_net_1x": (db - da) if da is not None and db is not None else None,
            "delta_eligible_assets_mean": delta_el,
            "holm_rejected_a": bool(ra.get("holm_rejected")),
            "holm_rejected_b": bool(rb.get("holm_rejected")),
        })

    labels = {
        "DIRECTIONAL_ATTENUATION": toward_zero > n_compare / 2 if n_compare else False,
        "COVERAGE_EXPANSION": coverage_delta_count > n_compare / 2 if n_compare else False,
        "HOLM_STATUS_CHANGE": holm_status_changes > 0,
        "ANCHOR_HOLM_CHANGE": bool(arm_a["cells"].get("H004V106", {}).get("holm_rejected")) != bool(arm_b["cells"].get("H004V106", {}).get("holm_rejected")),
        "COMPARATOR_HOLM_CHANGE": bool(arm_a["cells"].get("H004V105", {}).get("holm_rejected")) != bool(arm_b["cells"].get("H004V105", {}).get("holm_rejected")),
    }

    ledger = {
        "experiment_id": NEW_EXP,
        "grid_id": manifest["grid_id"],
        "source_manifest": str(GRID_MANIFEST.relative_to(ROOT)),
        "asof_date_trim": ASOF_DATE,
        "evaluated_utc": f1.now_utc(),
        "expected_cells": expected,
        "arms": {"A_ledger_vintage_committed": arm_a,
                 "B_ledger_vintage_f1_repaired": arm_b},
        "fidelity_anchor": {
            "passed": fidelity["passed"],
            "against": str(COMMITTED_LEDGER.relative_to(ROOT)),
            "compared_cells": fidelity["compared_cells"],
            "drift_count": fidelity["drift_count"],
            "asof_date": ASOF_DATE,
            "note": "arm A trimmed to 2026-09-30 must reproduce the committed DISPERSION-003 ledger within 1e-9 on every cell",
        },
    }
    out_ledger = out_dir / "grid_result_ledger.json"
    out_summary = out_dir / "grid_summary.json"
    out_ledger.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    summary = {
        "experiment_id": NEW_EXP,
        "asof_date_trim": ASOF_DATE,
        "evaluated_utc": f1.now_utc(),
        "expected_cells": expected,
        "arms": {
            "A_ledger_vintage_committed": {k: arm_a[k] for k in ("cells_evaluated","cells_ok","cells_blocked","cells_failed","holm_rejected_count")},
            "B_ledger_vintage_f1_repaired": {k: arm_b[k] for k in ("cells_evaluated","cells_ok","cells_blocked","cells_failed","holm_rejected_count")},
        },
        "n_cells_ok_both_arms": n_compare,
        "delta_mean_eligible_assets": (coverage_delta_sum / n_compare) if n_compare else 0.0,
        "aggregate_labels": labels,
        "cell_deltas": cell_deltas,
        "note": "EXPLORATORY_ONLY ledger-vintage (as-of 2026-09-30) descriptive sensitivity contrast; not confirmation, not comparable to current-vintage checkpoints, no promotion.",
    }
    out_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"[grid] labels: {labels}")
    print(f"[grid] ledger -> {out_ledger.relative_to(ROOT)}")
    print(f"[grid] summary -> {out_summary.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
