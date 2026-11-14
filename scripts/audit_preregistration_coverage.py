#!/usr/bin/env python3
"""Preregistration coverage audit for DISPERSION-003 integrity-audit artifacts.

Every integrity-audit JSON under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/ must point to
a preregistration record that exists on disk (preregistrations/), and every
preregistration record must be covered by at least one audit. This is the
single-source-of-truth guard: an audit that silently omits its preregistration
is the same hazard class as a hand-rewritten durable-state summary that drifts
from the record it names (see research_state corrections).

Read-only. Writes a JSON summary to --out (default: research_state/
preregistration_coverage_audit.json) and exits non-zero on any violation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
AUDIT_DIR = ROOT / "artifacts" / EXP / "integrity_audit"
PREREQ_DIR = ROOT / "artifacts" / EXP / "preregistrations"
F1_INTEGRITY_AUDIT_DIRS = [
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001" / "integrity_audit",
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002" / "integrity_audit",
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003" / "integrity_audit",
]
F1_PREREG_DIRS = [
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1COVERAGE-001" / "preregistrations",
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1SENS-002" / "preregistrations",
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-F1STAB-003" / "preregistrations",
]

# Addenda to the 2026-10-24 integrity audit: they carry no experiment id of
# their own and are deliberately not hypotheses (see
# tests/test_preregistration_completeness.py, which excludes the same set).
ADDENDA = {
    "forward_block_hac_addendum_20261024.json",
    "forward_block_independent_recomputation_20261025.json",
    "forward_block_independent_recomputation_20261028.json",
    "forward_block_integrity_audit.json",
}

# Audit IDs whose canonical experiment id does not normalize to a prereq stem.
# Mirrors tests/test_preregistration_completeness.py's AUDIT_TO_HYPOTHESIS map
# (audit_id -> hypothesis id) plus the prereq filenames on disk. Value is the
# prereq filename, or None when the audit genuinely has no prereq of its own:
# the overlap-aware audit (H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102)
# is an additive computation on the sealed canonical block whose prereq is the
# H10 fresh-block preregistration, which is NOT this audit's prereq and must not
# be misattributed to it.
ALIASES = {
    "HARMONY-CRYPTO-EDGE-004-DISPERSION-003-FORWARD-BLOCK-PLACEBO-001":
        "H004V106 Forward Block Placebo Red Team v1.md",
    "DISP-003-H10-FEASIBILITY-001": "H10_FRESH_FORWARD_BLOCK_v1.md",
    "H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102": None,
}

# Pre-declared mapping from F1 sub-experiment audit ids to their preregistration
# filenames on disk. Declared before any computation; not derived from the audits'
# own content, so it cannot be outcome-informed.
F1_ALIASES = {
    "DISP-003-F1COVERAGE-001": "F1_PANEL_COVERAGE_REPAIR_v1.md",
    "DISP-003-F1SENS-002": "F1_COVERAGE_OUTCOME_SENSITIVITY_v1.md",
    "DISP-003-F1STAB-003": "F1_COVERAGE_STABILITY_AUDIT_v1.md",
}
ALIASES.update(F1_ALIASES)


# IDs carried by audits that do not embed the prereq filename verbatim. The
# audit_id is the canonical experiment id (H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_20261029)
# and the prereq stem is the same id with the trailing _YYYYMMDD date suffix
# dropped (H004V106_FORWARD_BLOCK_CLUSTER_BOOTSTRAP_v1). The 2026-11-03 audit
# found 8 of 14 audits with no prereq field at all -- the field was never written,
# not that the prereq is missing. Resolution is by ID match, exactly as
# tests/test_preregistration_completeness.py maps AUDIT_TO_HYPOTHESIS.
DATE_SUFFIX_RE = re.compile(r"_\d{8}$")


def _normalize_id(value: str) -> str:
    """Lowercase, strip a file extension, a trailing _YYYYMMDD date suffix, a
    trailing _vN and a trailing _audit. Prereq filenames carry a .md extension
    and a _vN suffix (H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_AUDIT_v1.md)
    while audit IDs carry a trailing _YYYYMMDD date
    (H004V106_FORWARD_BLOCK_TEMPORAL_STABILITY_AUDIT_20261029); some prereq
    stems additionally append _audit before _vN, so that token is stripped too
    before comparison."""
    s = value.strip().lower()
    s = Path(s).stem.lower()
    s = DATE_SUFFIX_RE.sub("", s)
    s = re.sub(r"_v\d+$", "", s)
    s = re.sub(r"_audit$", "", s)
    return s


def resolve_prereq_for_audit(d: dict, prereq_names) -> str | None:
    """Return the prereq filename that names this audit's experiment, or None."""
    # direct path field, if present (already-resolved audits)
    prereq = d.get("preregistration")
    if prereq:
        return prereq
    candidates = []
    for key in ("audit_id", "experiment_id", "artifact_id", "addendum_id"):
        v = d.get(key)
        if v:
            candidates.append(str(v))
    for cand in candidates:
        if cand in ALIASES:
            return ALIASES[cand]
        target = _normalize_id(cand)
        for name in prereq_names:
            if _normalize_id(name) == target:
                return name
    return None


def _find_prereq(rel: str, search_dirs: list[Path]) -> Path | None:
    if rel.startswith("/"):
        p = Path(rel)
        return p if p.exists() and p.is_file() else None
    if rel.startswith("artifacts/"):
        p = ROOT / rel
        return p if p.exists() and p.is_file() else None
    for d in search_dirs:
        p = d / rel
        if p.exists() and p.is_file():
            return p
    return None


def audit(f1_integrity_audit_dirs: list[Path] | None = None,
          f1_prereg_dirs: list[Path] | None = None) -> dict:
    f1_integrity_audit_dirs = (
        f1_integrity_audit_dirs
        if f1_integrity_audit_dirs is not None
        else F1_INTEGRITY_AUDIT_DIRS
    )
    f1_prereg_dirs = (
        f1_prereg_dirs
        if f1_prereg_dirs is not None
        else F1_PREREG_DIRS
    )

    audits = sorted(AUDIT_DIR.glob("*.json"))
    prereq_names = sorted(p.name for p in PREREQ_DIR.glob("*.md"))
    search_dirs = [PREREQ_DIR] + [d for d in f1_prereg_dirs if d.exists()]
    for fd in f1_prereg_dirs:
        if fd.exists():
            prereq_names.extend(p.name for p in fd.glob("*.md"))
    prereq_names = sorted(set(prereq_names))

    audit_rows = []
    missing_prereq = []
    addenda_rows = []
    f1_rows = []
    for a in audits:
        try:
            d = json.loads(a.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - record, do not crash
            audit_rows.append({"audit": a.name, "error": f"unreadable: {e!r}"})
            missing_prereq.append(a.name)
            continue
        if a.name in ADDENDA:
            addenda_rows.append({"audit": a.name, "preregistration": None,
                                 "exists": True, "resolved": None,
                                 "note": "addendum to the 2026-10-24 integrity audit; "
                                         "no separate experiment id or prereq"})
            continue
        prereq = resolve_prereq_for_audit(d, prereq_names)
        if prereq is None:
            audit_rows.append({"audit": a.name, "preregistration": None,
                               "exists": True, "resolved": None,
                               "note": "additive computation on the sealed canonical "
                                       "block; no separate prereq"})
            continue
        if not prereq:
            missing_prereq.append(a.name)
            audit_rows.append({"audit": a.name, "preregistration": None,
                               "exists": False, "error": "preregistration field absent "
                               "and no ID match to a prereq on disk"})
            continue
        rel = prereq.replace("\\", "/")
        p = _find_prereq(rel, search_dirs)
        ok = p is not None
        audit_rows.append({"audit": a.name, "preregistration": prereq,
                           "exists": ok,
                           "resolved": str(p.relative_to(ROOT)) if ok else None})
        if not ok:
            missing_prereq.append(a.name)

    for fd in f1_integrity_audit_dirs:
        if not fd.exists():
            continue
        for a in sorted(fd.glob("*.json")):
            try:
                d = json.loads(a.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001 - record, do not crash
                f1_rows.append({"audit": a.name, "error": f"unreadable: {e!r}",
                                "frozen_record": True, "exists": True})
                continue
            prereq = resolve_prereq_for_audit(d, prereq_names)
            if prereq is None:
                f1_rows.append({"audit": a.name, "preregistration": None,
                                "exists": True, "resolved": None,
                                "frozen_record": True,
                                "note": "no prereq field and no ID match to a "
                                        "prereq on disk"})
                continue
            if not prereq:
                f1_rows.append({"audit": a.name, "preregistration": None,
                                "exists": False,
                                "error": "preregistration field absent and no "
                                "ID match to a prereq on disk",
                                "frozen_record": True})
                continue
            p = _find_prereq(prereq, search_dirs)
            ok = p is not None
            f1_rows.append({"audit": a.name, "preregistration": prereq,
                            "exists": ok,
                            "resolved": str(p.relative_to(ROOT)) if ok else None,
                            "frozen_record": True,
                            "note": None if ok else
                            f"prereq {prereq} not found on disk"})

    f1_missing = {r["preregistration"] for r in f1_rows
                  if r.get("preregistration") and not r.get("exists")}
    covered = set()
    for r in audit_rows + addenda_rows + f1_rows:
        if r.get("exists") and r.get("preregistration"):
            covered.add(Path(r["preregistration"]).name)
    uncovered = sorted(p for p in prereq_names if p not in covered
                       and p not in f1_missing)

    ok = not missing_prereq and not uncovered
    return {
        "audit_id": "PREREGISTRATION_COVERAGE_AUDIT_20261103",
        "audited_dir": str(AUDIT_DIR.relative_to(ROOT)),
        "prereg_dir": str(PREREQ_DIR.relative_to(ROOT)),
        "f1_integrity_audit_dirs": [
            str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
            for d in f1_integrity_audit_dirs
        ],
        "f1_prereg_dirs": [
            str(d.relative_to(ROOT)) if d.is_relative_to(ROOT) else str(d)
            for d in f1_prereg_dirs
        ],
        "audits_scanned": len(audit_rows) + len(addenda_rows) + len(f1_rows),
        "main_audits_scanned": len(audit_rows) + len(addenda_rows),
        "f1_audit_files_scanned": len(f1_rows),
        "preregistrations_on_disk": prereq_names,
        "audits_missing_prereq": missing_prereq,
        "preregistrations_uncovered_by_any_audit": uncovered,
        "rows": audit_rows + addenda_rows + f1_rows,
        "pass": ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="research_state/preregistration_coverage_audit.json")
    ap.add_argument("--no-f1-frozen-coverage", action="store_true",
                    help="Disable the default scan of DISP-003 sub-experiment "
                         "integrity_audit dirs (F1COVERAGE-001, F1SENS-002, "
                         "F1STAB-003) as frozen records.")
    args = ap.parse_args()
    f1 = [] if args.no_f1_frozen_coverage else None
    res = audit(f1_integrity_audit_dirs=f1, f1_prereg_dirs=f1)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[prereg-coverage] pass={res['pass']} audits={res['audits_scanned']} "
          f"main={res['main_audits_scanned']} f1={res['f1_audit_files_scanned']} "
          f"missing_prereq={len(res['audits_missing_prereq'])} "
          f"uncovered_prereq={len(res['preregistrations_uncovered_by_any_audit'])}")
    print(f"[prereg-coverage] wrote {out.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())