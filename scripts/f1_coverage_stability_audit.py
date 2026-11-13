#!/usr/bin/env python3
"""F1 coverage stability audit for the frozen H004V106 anchor.

DISP-003-F1STAB-003 (H25, EXPLORATORY_ONLY). The two pre-registered stability
diagnostics that drive the discounted verdict on the canonical H004V106 positive
estimate were computed only on the 26-27-asset committed universe (arm A):

  * H8  / DISP-003-STATEAUDIT-001  -- leave-one-calendar-month-out
        (CLUSTER_DOMINATED; dropping 2025-10 moves +0.617 -> +0.093, -0.849).
  * H19 / DISP-003-TEMPSTABILITY-001 -- median formation-date split at 2025-11-01
        (sign not stable: +0.6456 over 2025-01..2025-10 vs -0.1629 after).

H24 (DISP-003-F1SENS-002) measured only whether the point estimate moves under the
four-asset F1 repair (arm A +0.6165 -> arm B +0.5398). This script measures
whether the two stability VERDICTS survive that repair, using the identical
per-formation records committed in the F1SENS-002 artifact. It computes no p-value,
no multiple-testing family and no promotion; it never writes to the committed
panels, the F1SENS artifact, the canonical block or the H10 fresh block; all inputs
are read-only and byte-verified unchanged at the end of the run.

The decision rule is inherited verbatim from H8 (0.50 leave-one-month-out band)
and H19 (sign flip across the median-date split); it is not chosen after seeing
arm B's outcome. Label F1_STABILITY_PRESERVED iff BOTH warnings persist on arm B.

Usage:
    python3 scripts/f1_coverage_stability_audit.py [--out PATH]

No network: reuses the already-committed F1SENS-002 per-formation records.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

OLD_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
F1SENS_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002"
NEW_EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003"

F1SENS_DIR = ROOT / "artifacts" / F1SENS_EXP / "integrity_audit"
OLD_PANELS = ROOT / "artifacts" / OLD_EXP / "data" / "panels"
CANONICAL_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block" / "forward_block_evaluation.json"
H10_FRESH_BLOCK = ROOT / "artifacts" / OLD_EXP / "forward_block_h10_fresh" / "forward_block_evaluation.json"
AUDIT_DIR = ROOT / "artifacts" / NEW_EXP / "integrity_audit"

# Frozen artifact hashes that must be byte-identical after the run.
FROZEN_HASHES = {
    "forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}

# Predeclared thresholds and fidelity anchors (inherited from H8 / H19 / H24).
THRESHOLD_FRAC = 0.50            # H8 leave-one-month-out band
N_BOOT = 2000
RNG_SEED = 20261113
FIELDS_TOL = 1e-9

CANONICAL_BASELINE = 0.6165223953929935          # frozen canonical block
F1SENS_ARM_B_BASELINE = 0.5397762360511249       # H24 stored arm B value
H8_2025_10_DELTA_FRAC = -0.8487210159492463      # H8 CLUSTER_DOMINATED anchor
H19_SPLIT_DATE = "2025-11-01"
H19_FIRST_DIFF = 0.6456322213084524              # H19 first-half (n_high=53, n_low=21)
H19_SECOND_DIFF = -0.16288800752983412           # H19 second-half (n_high=8, n_low=69)
H19_FIRST_COUNTS = (53, 21)
H19_SECOND_COUNTS = (8, 69)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _latest_f1sens_artifact() -> Path:
    files = sorted(F1SENS_DIR.glob("f1_coverage_outcome_sensitivity_*.json"))
    if not files:
        raise FileNotFoundError(f"no F1SENS artifact under {F1SENS_DIR}")
    return files[-1]


def diff_from_forms(forms) -> float | None:
    """high-minus-low net-1x spread from per-formation records (H8/H19 formula)."""
    high = [f["spread_net_1x"] for f in forms if f["state"] == "high"]
    low = [f["spread_net_1x"] for f in forms if f["state"] == "low"]
    if not high or not low:
        return None
    return statistics.mean(high) - statistics.mean(low)


def month_groups(forms) -> dict:
    months = defaultdict(list)
    for f in forms:
        months[f["formation_date"][:7]].append(f)
    return dict(sorted(months.items()))


def leave_one_month_out(forms) -> dict:
    """Drop each calendar month, recompute the spread, report delta fractions."""
    baseline = diff_from_forms(forms)
    months = month_groups(forms)
    rows = {}
    max_abs_frac = None
    max_abs_month = None
    for m in months:
        keep = [f for f in forms if not f["formation_date"].startswith(m)]
        hi = [f["spread_net_1x"] for f in keep if f["state"] == "high"]
        lo = [f["spread_net_1x"] for f in keep if f["state"] == "low"]
        diff = (statistics.mean(hi) - statistics.mean(lo)) if hi and lo else None
        delta_frac = ((diff - baseline) / baseline) if (diff is not None and baseline) else None
        rows[m] = {
            "formations_kept": len(keep),
            "n_high": len(hi),
            "n_low": len(lo),
            "high_low_diff_net_1x": diff,
            "delta_frac_vs_baseline": delta_frac,
        }
        if delta_frac is not None and (max_abs_frac is None or abs(delta_frac) > max_abs_frac):
            max_abs_frac = abs(delta_frac)
            max_abs_month = m
    return {
        "baseline": baseline,
        "threshold_frac": THRESHOLD_FRAC,
        "max_abs_delta_frac": max_abs_frac,
        "max_abs_month": max_abs_month,
        "cluster_dominated": bool(max_abs_frac is not None and max_abs_frac > THRESHOLD_FRAC),
        "months": rows,
    }


def _bootstrap(months: dict, rng) -> dict:
    keys = list(months.keys())
    boot = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(keys), size=len(keys))
        sample = []
        for i in idx:
            sample.extend(months[keys[i]])
        d = diff_from_forms(sample)
        if d is not None:
            boot.append(d)
    if not boot:
        return {"mean": None, "se": None, "ci_lo": None, "ci_hi": None,
                "ci_includes_zero": None, "n_boot": 0}
    arr = np.asarray(boot, dtype=float)
    ci_lo = float(np.percentile(arr, 2.5))
    ci_hi = float(np.percentile(arr, 97.5))
    return {
        "mean": float(arr.mean()),
        "se": float(arr.std(ddof=1)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "ci_includes_zero": bool(ci_lo <= 0 <= ci_hi),
        "n_boot": len(boot),
    }


def _half_stats(forms, rng) -> dict:
    months = month_groups(forms)
    both = sum(
        1 for mk in months
        if any(f["state"] == "high" for f in months[mk])
        and any(f["state"] == "low" for f in months[mk])
    )
    return {
        "n_formations": len(forms),
        "n_high": sum(1 for f in forms if f["state"] == "high"),
        "n_low": sum(1 for f in forms if f["state"] == "low"),
        "n_mid": sum(1 for f in forms if f["state"] == "mid"),
        "high_low_diff_net_1x": diff_from_forms(forms),
        "n_months": len(months),
        "n_months_with_both_states": both,
        "bootstrap": _bootstrap(months, rng),
    }


def temporal_split(forms) -> dict:
    """Median formation-date split (H19) with per-half month-cluster bootstrap."""
    forms = sorted(forms, key=lambda f: f["formation_date"])
    split = len(forms) // 2
    split_date = forms[split]["formation_date"]
    rng = np.random.default_rng(RNG_SEED)
    first = _half_stats(forms[:split], rng)
    second = _half_stats(forms[split:], rng)
    d1 = first["high_low_diff_net_1x"]
    d2 = second["high_low_diff_net_1x"]
    sign_flip = bool(
        d1 is not None and d2 is not None and d1 != 0 and d2 != 0
        and (d1 > 0) != (d2 > 0)
    )
    return {
        "split_date": split_date,
        "n_first": split,
        "n_second": len(forms) - split,
        "first_half": first,
        "second_half": second,
        "sign_flip": sign_flip,
        "temporal_instability": sign_flip,
    }


def analyze_arm(forms) -> dict:
    forms = sorted(forms, key=lambda f: f["formation_date"])
    return {
        "n_formations": len(forms),
        "n_high": sum(1 for f in forms if f["state"] == "high"),
        "n_low": sum(1 for f in forms if f["state"] == "low"),
        "n_mid": sum(1 for f in forms if f["state"] == "mid"),
        "baseline_high_low_diff_net_1x": diff_from_forms(forms),
        "leave_one_month_out": leave_one_month_out(forms),
        "temporal_split": temporal_split(forms),
    }


def _close(actual, expected, tol=FIELDS_TOL) -> bool:
    return actual is not None and expected is not None and abs(float(actual) - float(expected)) <= tol


def fidelity_check(arm_a: dict, arm_b: dict) -> dict:
    """Confirm arm A reproduces H8/H19 and both baselines match committed values."""
    anchors = {}

    a_base = arm_a["baseline_high_low_diff_net_1x"]
    anchors["arm_a_baseline"] = {
        "expected": CANONICAL_BASELINE, "actual": a_base,
        "match": _close(a_base, CANONICAL_BASELINE),
    }

    a_2025_10 = arm_a["leave_one_month_out"]["months"].get("2025-10", {}).get("delta_frac_vs_baseline")
    anchors["arm_a_2025_10_delta_frac"] = {
        "expected": H8_2025_10_DELTA_FRAC, "actual": a_2025_10,
        "match": _close(a_2025_10, H8_2025_10_DELTA_FRAC, tol=1e-6),
    }

    a_split = arm_a["temporal_split"]
    a_first = a_split["first_half"]
    a_second = a_split["second_half"]
    anchors["arm_a_split_date"] = {
        "expected": H19_SPLIT_DATE, "actual": a_split["split_date"],
        "match": a_split["split_date"] == H19_SPLIT_DATE,
    }
    anchors["arm_a_first_diff"] = {
        "expected": H19_FIRST_DIFF, "actual": a_first["high_low_diff_net_1x"],
        "match": _close(a_first["high_low_diff_net_1x"], H19_FIRST_DIFF),
    }
    anchors["arm_a_second_diff"] = {
        "expected": H19_SECOND_DIFF, "actual": a_second["high_low_diff_net_1x"],
        "match": _close(a_second["high_low_diff_net_1x"], H19_SECOND_DIFF),
    }
    anchors["arm_a_first_counts"] = {
        "expected": H19_FIRST_COUNTS,
        "actual": (a_first["n_high"], a_first["n_low"]),
        "match": (a_first["n_high"], a_first["n_low"]) == H19_FIRST_COUNTS,
    }
    anchors["arm_a_second_counts"] = {
        "expected": H19_SECOND_COUNTS,
        "actual": (a_second["n_high"], a_second["n_low"]),
        "match": (a_second["n_high"], a_second["n_low"]) == H19_SECOND_COUNTS,
    }

    b_base = arm_b["baseline_high_low_diff_net_1x"]
    anchors["arm_b_baseline"] = {
        "expected": F1SENS_ARM_B_BASELINE, "actual": b_base,
        "match": _close(b_base, F1SENS_ARM_B_BASELINE),
    }

    return {
        "pass": all(v["match"] for v in anchors.values()),
        "tolerance": FIELDS_TOL,
        "anchors": anchors,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="artifact path (default: integrity_audit/)")
    args = ap.parse_args()

    started = now_utc()

    # Read-only snapshots before computing.
    source_path = _latest_f1sens_artifact()
    source_hash_before = sha256_file(source_path)
    frozen_before = {rel: sha256_file(ROOT / "artifacts" / OLD_EXP / rel) for rel in FROZEN_HASHES}
    panels_before = {p.name: sha256_file(p) for p in sorted(OLD_PANELS.glob("*.csv"))}

    source = json.loads(source_path.read_text(encoding="utf-8"))
    arm_a_forms = source["arm_a_committed"]["formations"]
    arm_b_forms = source["arm_b_repaired"]["formations"]

    arm_a = analyze_arm(arm_a_forms)
    arm_b = analyze_arm(arm_b_forms)
    fid = fidelity_check(arm_a, arm_b)

    # Predeclared label (section 4): both warnings must persist on arm B.
    cluster_persists = bool(arm_b["leave_one_month_out"]["cluster_dominated"])
    temporal_persists = bool(arm_b["temporal_split"]["temporal_instability"])
    label = "F1_STABILITY_PRESERVED" if (cluster_persists and temporal_persists) else "F1_STABILITY_CHANGED"

    # Read-only checks after computing.
    source_hash_after = sha256_file(source_path)
    frozen_after = {}
    for rel in FROZEN_HASHES:
        actual = sha256_file(ROOT / "artifacts" / OLD_EXP / rel)
        frozen_after[rel] = {"expected": FROZEN_HASHES[rel], "actual": actual,
                             "match": actual == FROZEN_HASHES[rel]}
    frozen_unchanged = all(v["match"] for v in frozen_after.values())
    panels_after = {p.name: sha256_file(p) for p in sorted(OLD_PANELS.glob("*.csv"))}
    panels_unchanged = (panels_before == panels_after)
    # Cross-check against the hashes the F1SENS-002 audit itself recorded.
    recorded_panels = source.get("read_only_checks", {}).get("committed_panel_sha256", {})
    panels_match_f1sens = bool(recorded_panels) and recorded_panels == panels_after

    if not fid["pass"]:
        verdict = "FAIL"
    elif not (frozen_unchanged and panels_unchanged and panels_match_f1sens and source_hash_before == source_hash_after):
        verdict = "FAIL"
    else:
        verdict = "PASS"

    comparison = {
        "arm_a_label": {
            "cluster_dominated": bool(arm_a["leave_one_month_out"]["cluster_dominated"]),
            "temporal_instability": bool(arm_a["temporal_split"]["temporal_instability"]),
            "max_abs_month": arm_a["leave_one_month_out"]["max_abs_month"],
            "max_abs_delta_frac": arm_a["leave_one_month_out"]["max_abs_delta_frac"],
        },
        "arm_b_label": {
            "cluster_dominated": cluster_persists,
            "temporal_instability": temporal_persists,
            "max_abs_month": arm_b["leave_one_month_out"]["max_abs_month"],
            "max_abs_delta_frac": arm_b["leave_one_month_out"]["max_abs_delta_frac"],
        },
        "cluster_domination_persists": cluster_persists,
        "temporal_instability_persists": temporal_persists,
        "label": label,
        "conclusion": (
            f"Arm B (29-31 assets) max |leave-one-month-out delta frac| = "
            f"{arm_b['leave_one_month_out']['max_abs_delta_frac']} at "
            f"{arm_b['leave_one_month_out']['max_abs_month']} "
            f"(threshold {THRESHOLD_FRAC}); temporal split {H19_SPLIT_DATE}: "
            f"{arm_b['temporal_split']['first_half']['high_low_diff_net_1x']} -> "
            f"{arm_b['temporal_split']['second_half']['high_low_diff_net_1x']}. "
            f"Label {label}. This is EXPLORATORY_ONLY development evidence on "
            f"already-inspected data; it does not validate, replace, unlock or "
            f"re-run any frozen experiment and is not independent confirmation."
        ),
    }

    artifact = {
        "audit_id": "DISP-003-F1STAB-003",
        "experiment_id": NEW_EXP,
        "hypothesis": "H25",
        "audit_type": "COVERAGE_STABILITY_AUDIT",
        "status": "EXPLORATORY_ONLY",
        "started_utc": started,
        "completed_utc": now_utc(),
        "offline": True,
        "estimand": "whether the H8 leave-one-month-out CLUSTER_DOMINATION and the "
                    "H19 median-date TEMPORAL-INSTABILITY verdicts on the canonical "
                    "H004V106 estimate are robust to the four-asset F1 coverage "
                    "repair (26-27 -> 29-31 eligible assets), over the identical "
                    "sealed canonical formation window; descriptive only, no p-value, "
                    "no multiple-testing family, no promotion",
        "source": {
            "f1sens_artifact": str(source_path.relative_to(ROOT)),
            "f1sens_sha256_before": source_hash_before,
            "f1sens_sha256_after": source_hash_after,
            "arm_a_forms": len(arm_a_forms),
            "arm_b_forms": len(arm_b_forms),
        },
        "decision_rule": {
            "source": "inherited verbatim from H8 (0.50 leave-one-month-out band) "
                      "and H19 (sign flip across the median-date split); not outcome-tuned",
            "threshold_frac": THRESHOLD_FRAC,
            "cluster_domination_persists": cluster_persists,
            "temporal_instability_persists": temporal_persists,
            "label": label,
        },
        "fidelity_check": fid,
        "arm_a_committed": arm_a,
        "arm_b_repaired": arm_b,
        "comparison": comparison,
        "read_only_checks": {
            "old_panels_byte_unchanged": panels_unchanged,
            "old_panels_match_f1sens_recorded_hashes": panels_match_f1sens,
            "committed_panel_sha256": panels_after,
            "frozen_artifacts": frozen_after,
            "f1sens_source_byte_unchanged": source_hash_before == source_hash_after,
        },
        "disposition": {
            "frozen_artifacts_modified": not frozen_unchanged,
            "old_panels_modified": not panels_unchanged,
            "f1sens_source_modified": source_hash_before != source_hash_after,
            "outcomes_computed": True,
            "note": "stability diagnostics are computed on already-inspected "
                    "development data from the committed F1SENS-002 records; this is "
                    "EXPLORATORY_ONLY and is not independent confirmation of any hypothesis",
        },
        "verdict": verdict,
        "notes": [
            "Arm A must reproduce H8 (-0.849 on 2025-10) and H19 (+0.6456 / -0.1629 "
            "at split 2025-11-01) and the canonical/F1SENS baselines exactly "
            "(fidelity_check); if it does not, the script fails and writes no verdict.",
            "Arm B uses the same per-formation records and the same functions as arm A; "
            "only the underlying eligible universe differs.",
            "No network: reuses the committed F1SENS-002 per-formation records.",
            "The F1SENS-002 source artifact, the committed panels and both frozen blocks "
            "are read-only and byte-verified unchanged at the end of the run.",
        ],
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = AUDIT_DIR / f"f1_coverage_stability_audit_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")

    print(f"[f1stab] verdict={verdict} fidelity_pass={fid['pass']} label={label}")
    print(f"[f1stab] arm_a baseline={arm_a['baseline_high_low_diff_net_1x']} "
          f"cluster={arm_a['leave_one_month_out']['cluster_dominated']} "
          f"temporal={arm_a['temporal_split']['temporal_instability']}")
    print(f"[f1stab] arm_b baseline={arm_b['baseline_high_low_diff_net_1x']} "
          f"max_abs_month={arm_b['leave_one_month_out']['max_abs_month']} "
          f"max_abs_frac={arm_b['leave_one_month_out']['max_abs_delta_frac']} "
          f"temporal={arm_b['temporal_split']['temporal_instability']}")
    print(f"[f1stab] frozen_unchanged={frozen_unchanged} panels_unchanged={panels_unchanged} "
          f"panels_match_f1sens={panels_match_f1sens} source_unchanged={source_hash_before == source_hash_after}")
    try:
        shown = out_path.relative_to(ROOT)
    except ValueError:
        shown = out_path
    print(f"[f1stab] output -> {shown}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())