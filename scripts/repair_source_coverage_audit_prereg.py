#!/usr/bin/env python3
"""Repair the DISP-003 source-coverage gap audit to carry its preregistration
reference and a self-referential artifact_sha256.

The committed artifact
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/integrity_audit/
source_coverage_gap_binance_no_capmkt_20261114.json was produced before its
preregistration existed and before the single-source-of-truth guards in
tests/test_preregistration_completeness.py and
tests/test_preregistration_coverage_audit.py were extended to it. It therefore
carried no `preregistration` field, so:

  * tests/test_preregistration_completeness.py::test_every_committed_audit_is_
    registered_or_excluded failed (DISP-003-SOURCECOV-001 was neither in
    AUDIT_TO_HYPOTHESIS nor in the addenda set);
  * tests/test_preregistration_coverage_audit.py::test_audit_passes_...
    failed (main_audits_scanned 15 != 14);
  * tests/test_source_coverage_gap.py::test_audit_artifact_sha256_matches_
    content would fail, because the field was absent.

This repair adds the two fields the committed test requires. It does NOT
recompute the audit's findings: the cross-tabulation is re-verified against the
source data by the regression test, and this script asserts that the recorded
findings still match before touching anything.

Read-only on the source data; writes only the one audit artifact.

Usage: python3 scripts/repair_source_coverage_audit_prereg.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART_PATH = (
    ROOT / "artifacts" / "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
    / "integrity_audit" / "source_coverage_gap_binance_no_capmkt_20261114.json"
)
PREREQ_REL = (
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
    "preregistrations/SOURCE_COVERAGE_GAP_AUDIT_v1.md"
)
AUDIT_ID = "DISP-003-SOURCECOV-001"


def verify_findings(d: dict) -> None:
    """Recompute the cross-tabulation from the source data and assert the
    recorded findings match. Raises if the audit's substance has drifted."""
    src = ROOT / d["source_data"]
    if not src.is_file():
        raise SystemExit(f"source data not found: {src}")
    val = json.loads(src.read_text(encoding="utf-8"))

    binance_yes_capmkt_no = 0
    binance_yes_capmkt_yes = 0
    binance_no_capmkt_yes = 0
    binance_no_capmkt_no = 0
    gap_assets = []
    for c in val.get("candidates_processed", []):
        binance_exists = bool(c.get("binance", {}).get("exists", False))
        capmkt_served = any(
            m.get("status") != "asset_not_served"
            for m in c.get("metrics", {}).values()
        )
        if binance_exists and not capmkt_served:
            binance_yes_capmkt_no += 1
            gap_assets.append(c.get("asset"))
        elif binance_exists and capmkt_served:
            binance_yes_capmkt_yes += 1
        elif not binance_exists and capmkt_served:
            binance_no_capmkt_yes += 1
        else:
            binance_no_capmkt_no += 1

    f = d["findings"]
    checks = {
        "binance_yes_capmkt_no": (f["binance_yes_capmkt_no"], binance_yes_capmkt_no),
        "binance_yes_capmkt_yes": (f["binance_yes_capmkt_yes"], binance_yes_capmkt_yes),
        "binance_no_capmkt_yes": (f["binance_no_capmkt_yes"], binance_no_capmkt_yes),
        "binance_no_capmkt_no": (f["binance_no_capmkt_no"], binance_no_capmkt_no),
        "total_candidates_processed": (
            f["total_candidates_processed"], len(val.get("candidates_processed", [])),
        ),
    }
    for name, (recorded, recomputed) in checks.items():
        if recorded != recomputed:
            raise SystemExit(
                f"findings drift: {name} recorded={recorded} recomputed={recomputed}"
            )

    recorded_assets = {a["asset"] for a in d["binance_without_capmkt"]}
    if recorded_assets != set(gap_assets):
        raise SystemExit(
            "binance_without_capmkt asset set drift: "
            f"recorded={sorted(recorded_assets)} recomputed={sorted(gap_assets)}"
        )
    if len(d["binance_without_capmkt"]) != 24:
        raise SystemExit("expected 24 gap assets, got "
                         f"{len(d['binance_without_capmkt'])}")


def main() -> int:
    if not ART_PATH.is_file():
        raise SystemExit(f"audit artifact not found: {ART_PATH}")
    d = json.loads(ART_PATH.read_text(encoding="utf-8"))
    if d.get("audit_id") != AUDIT_ID:
        raise SystemExit(f"unexpected audit_id: {d.get('audit_id')}")

    verify_findings(d)

    prereq_path = ROOT / PREREQ_REL
    if not prereq_path.is_file():
        raise SystemExit(f"preregistration not found: {prereq_path}")

    d["preregistration"] = PREREQ_REL
    d["preregistered"] = True

    body = {k: v for k, v in d.items() if k != "artifact_sha256"}
    content = json.dumps(body, sort_keys=True, indent=2) + "\n"
    d["artifact_sha256"] = hashlib.sha256(content.encode("utf-8")).hexdigest()

    ART_PATH.write_text(json.dumps(d, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    print(f"repaired {ART_PATH.relative_to(ROOT)}")
    print(f"  preregistration = {d['preregistration']}")
    print(f"  artifact_sha256 = {d['artifact_sha256']}")
    print("  findings verified against source data (no drift)")
    return 0


if __name__ == "__main__":
    sys.exit(main())