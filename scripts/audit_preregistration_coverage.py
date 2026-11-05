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


def audit() -> dict:
    audits = sorted(AUDIT_DIR.glob("*.json"))
    prereq_names = sorted(p.name for p in PREREQ_DIR.glob("*.md"))

    audit_rows = []
    missing_prereq = []
    addenda_rows = []
    for a in audits:
        try:
            d = json.loads(a.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - record, do not crash
            audit_rows.append({"audit": a.name, "error": f"unreadable: {e!r}"})
            missing_prereq.append(a.name)
            continue
        if a.name in ADDENDA:
            # Addenda to the 2026-10-24 integrity audit carry no experiment id
            # and no prereq of their own; they are covered by the parent audit
            # (H004V106_FORWARD_BLOCK_FINAL_INTEGRITY_AUDIT_20261102, H16).
            addenda_rows.append({"audit": a.name, "preregistration": None,
                                 "exists": True, "resolved": None,
                                 "note": "addendum to the 2026-10-24 integrity audit; "
                                         "no separate experiment id or prereq"})
            continue
        prereq = resolve_prereq_for_audit(d, prereq_names)
        if prereq is None:
            # No prereq of its own: additive computation on the sealed canonical
            # block (H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102). Its
            # prereq is the H10 fresh-block preregistration, which is NOT this
            # audit's prereq and must not be misattributed to it.
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
        # stored prereq paths are repo-relative from the artifact root, e.g.
        # "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/X.md"
        if rel.startswith("artifacts/"):
            p = ROOT / rel
        elif rel.startswith("/"):
            p = Path(rel)
        else:
            p = PREREQ_DIR / rel
        ok = p.exists() and p.is_file()
        audit_rows.append({"audit": a.name, "preregistration": prereq,
                           "exists": ok,
                           "resolved": str(p.relative_to(ROOT)) if ok else None})
        if not ok:
            missing_prereq.append(a.name)

    covered = set()
    for r in audit_rows + addenda_rows:
        if r.get("exists") and r.get("preregistration"):
            covered.add(Path(r["preregistration"]).name)
    uncovered = sorted(p for p in prereq_names if p not in covered)

    ok = not missing_prereq and not uncovered
    return {
        "audit_id": "PREREGISTRATION_COVERAGE_AUDIT_20261103",
        "audited_dir": str(AUDIT_DIR.relative_to(ROOT)),
        "prereg_dir": str(PREREQ_DIR.relative_to(ROOT)),
        "audits_scanned": len(audit_rows) + len(addenda_rows),
        "preregistrations_on_disk": prereq_names,
        "audits_missing_prereq": missing_prereq,
        "preregistrations_uncovered_by_any_audit": uncovered,
        "rows": audit_rows + addenda_rows,
        "pass": ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="research_state/preregistration_coverage_audit.json")
    args = ap.parse_args()
    res = audit()
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[prereg-coverage] pass={res['pass']} audits={res['audits_scanned']} "
          f"missing_prereq={len(res['audits_missing_prereq'])} "
          f"uncovered_prereq={len(res['preregistrations_uncovered_by_any_audit'])}")
    print(f"[prereg-coverage] wrote {out.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())