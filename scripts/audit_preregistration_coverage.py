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
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
AUDIT_DIR = ROOT / "artifacts" / EXP / "integrity_audit"
PREREQ_DIR = ROOT / "artifacts" / EXP / "preregistrations"


def audit() -> dict:
    audits = sorted(AUDIT_DIR.glob("*.json"))
    prereqs = {p.name for p in PREREQ_DIR.glob("*.md")}

    audit_rows = []
    missing_prereq = []
    for a in audits:
        try:
            d = json.loads(a.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 - record, do not crash
            audit_rows.append({"audit": a.name, "error": f"unreadable: {e!r}"})
            missing_prereq.append(a.name)
            continue
        prereq = d.get("preregistration")
        if not prereq:
            missing_prereq.append(a.name)
            audit_rows.append({"audit": a.name, "preregistration": None,
                               "exists": False, "error": "preregistration field absent"})
            continue
        rel = prereq.replace("\\", "/")
        # stored paths are repo-relative from the artifact root
        p = (ROOT / rel) if not rel.startswith("/") else Path(rel)
        ok = p.exists() and p.is_file()
        audit_rows.append({"audit": a.name, "preregistration": prereq,
                           "exists": ok, "resolved": str(p.relative_to(ROOT)) if ok else None})
        if not ok:
            missing_prereq.append(a.name)

    covered = set()
    for r in audit_rows:
        if r.get("exists") and r.get("preregistration"):
            covered.add(Path(r["preregistration"]).name)
    uncovered = sorted(p for p in prereqs if p not in covered)

    ok = not missing_prereq and not uncovered
    return {
        "audit_id": "PREREGISTRATION_COVERAGE_AUDIT_20261103",
        "audited_dir": str(AUDIT_DIR.relative_to(ROOT)),
        "prereg_dir": str(PREREQ_DIR.relative_to(ROOT)),
        "audits_scanned": len(audit_rows),
        "preregistrations_on_disk": sorted(prereqs),
        "audits_missing_prereq": missing_prereq,
        "preregistrations_uncovered_by_any_audit": uncovered,
        "rows": audit_rows,
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
          f"missing_prereq={len(res['audits_missing_prereq'])]} "
          f"uncovered_prereq={len(res['preregistrations_uncovered_by_any_audit'])}")
    print(f"[prereg-coverage] wrote {out.relative_to(ROOT)}")
    return 0 if res["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())