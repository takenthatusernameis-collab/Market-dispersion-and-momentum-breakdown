"""Regression guard for scripts/audit_preregistration_coverage.py.

The script existed (scripts/audit_preregistration_coverage.py) but had never
been run: it contained an f-string syntax error (an unmatched ']'), so the
single-source-of-truth check it was written to perform had never executed. The
2026-11-05 pass ran it for the first time and found 8 of 14 integrity-audit
JSONs with no prereq field at all -- the field was never written, not that the
prereq is missing. Resolution is by experiment-id match against the prereq
filenames on disk, mirroring tests/test_preregistration_completeness.py's
AUDIT_TO_HYPOTHESIS map.

This test pins:
  * the script is importable and its audit() is deterministic across runs;
  * every audit under integrity_audit/ resolves to a prereq that exists on
    disk (no missing_prereq);
  * every prereq on disk is covered by at least one audit (no uncovered);
  * the overlap-aware audit (H004V106_FORWARD_BLOCK_OVERLAP_AWARE_AUDIT_20261102)
    is correctly classified as having no prereq of its own -- it is an additive
    computation on the sealed canonical block, and its prereq is the H10
    fresh-block preregistration, which must not be misattributed to it;
  * the H10 feasibility analysis resolves to the H10 fresh-block prereq, not
    to some other prereq;
  * the four addenda to the 2026-10-24 integrity audit are recognised as
    addenda and carry no prereq of their own.

Only local files are read: no network, no secrets, no trading endpoints.
"""
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_preregistration_coverage.py"

spec = importlib.util.spec_from_file_location("prereg_coverage_audit", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PreregistrationCoverageAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = mod.audit()
        cls.second = mod.audit()

    def test_script_is_importable_and_deterministic(self):
        self.assertEqual(self.first, self.second)

    def test_audit_passes_with_no_missing_or_uncovered(self):
        self.assertTrue(self.first["pass"], self.first["audits_missing_prereq"]
                        or self.first["preregistrations_uncovered_by_any_audit"])
        self.assertEqual(self.first["audits_missing_prereq"], [])
        self.assertEqual(self.first["preregistrations_uncovered_by_any_audit"], [])
        self.assertEqual(self.first["main_audits_scanned"], 15)
        self.assertEqual(self.first["f1_audit_files_scanned"], 5)
        self.assertEqual(self.first["audits_scanned"], 20)
        self.assertEqual(len(self.first["preregistrations_on_disk"]), 13)

    def test_overlap_aware_audit_has_no_prereq_of_its_own(self):
        row = next(r for r in self.first["rows"]
                   if r["audit"] == "H004V106_forward_block_overlap_aware_audit_20261102.json")
        self.assertIsNone(row["preregistration"])
        self.assertTrue(row["exists"])
        self.assertIn("no separate prereq", row["note"])

    def test_h10_feasibility_resolves_to_h10_fresh_block_prereq(self):
        row = next(r for r in self.first["rows"]
                   if r["audit"] == "H10_feasibility_analysis_20261103.json")
        self.assertEqual(row["preregistration"], "H10_FRESH_FORWARD_BLOCK_v1.md")
        self.assertTrue(row["exists"])

    def test_f1_audits_scanned_as_frozen_records(self):
        """The F1 sub-experiment integrity audits (F1COVERAGE-001, F1SENS-002,
        F1STAB-003) are scanned by default as frozen records; their committed
        audit JSONs cannot hide outside the coverage check."""
        f1_rows = [r for r in self.first["rows"] if r.get("frozen_record") is True]
        self.assertEqual(len(f1_rows), 5, self.first)
        scanned = {r["audit"] for r in f1_rows}
        expected = {
            "f1_panel_coverage_repair_20261112T172845Z.json",
            "f1_panel_coverage_repair_20261112T172913Z.json",
            "f1_panel_coverage_repair_20261112T183449Z.json",
            "f1_coverage_outcome_sensitivity_20261113T025950Z.json",
            "f1_coverage_stability_audit_20261113T054921Z.json",
        }
        self.assertTrue(expected.issubset(scanned),
                        f"F1 audit files missing from scan: {sorted(expected - scanned)}")
        for row in f1_rows:
            with self.subTest(file=row["audit"]):
                self.assertEqual(row["frozen_record"], True, row)
                self.assertTrue(row.get("exists", False), row)

    def test_f1_audits_resolve_to_f1_prereqs(self):
        expected = {
            "f1_panel_coverage_repair_20261112T183449Z.json":
                "F1_PANEL_COVERAGE_REPAIR_v1.md",
            "f1_coverage_outcome_sensitivity_20261113T025950Z.json":
                "F1_COVERAGE_OUTCOME_SENSITIVITY_v1.md",
            "f1_coverage_stability_audit_20261113T054921Z.json":
                "F1_COVERAGE_STABILITY_AUDIT_v1.md",
        }
        for audit_name, prereq in expected.items():
            with self.subTest(audit=audit_name):
                row = next(r for r in self.first["rows"]
                           if r["audit"] == audit_name)
                self.assertEqual(row["preregistration"], prereq, row)
                self.assertTrue(row["exists"], row)

    def test_f1_prereqs_covered_by_f1_audits(self):
        f1_prereqs = {"F1_PANEL_COVERAGE_REPAIR_v1.md",
                      "F1_COVERAGE_OUTCOME_SENSITIVITY_v1.md",
                      "F1_COVERAGE_STABILITY_AUDIT_v1.md"}
        self.assertTrue(f1_prereqs.issubset(set(self.first["preregistrations_on_disk"])),
                        self.first["preregistrations_on_disk"])
        self.assertFalse(f1_prereqs & set(self.first["preregistrations_uncovered_by_any_audit"]),
                         self.first["preregistrations_uncovered_by_any_audit"])

    def test_source_coverage_gap_audit_resolves_to_its_prereq(self):
        row = next(r for r in self.first["rows"]
                   if r["audit"] == "source_coverage_gap_binance_no_capmkt_20261114.json")
        # The preregistration field carries the full relative path, matching the
        # convention used by every other DISP-003 audit artifact (e.g. the
        # placebo red-team audit quotes
        # artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/
        # H004V106 Forward Block Placebo Red Team v1.md verbatim).
        self.assertEqual(
            row["preregistration"],
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
            "preregistrations/SOURCE_COVERAGE_GAP_AUDIT_v1.md",
            row)
        self.assertTrue(row["exists"], row)
        self.assertEqual(row["resolved"],
                         "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/"
                         "preregistrations/SOURCE_COVERAGE_GAP_AUDIT_v1.md")

    def test_f1_coverage_opt_out(self):
        """The default F1 frozen-coverage scan is opt-out for callers that need
        a narrow scope."""
        res = mod.audit(f1_integrity_audit_dirs=[], f1_prereg_dirs=[])
        self.assertEqual(res["f1_audit_files_scanned"], 0, res)
        self.assertEqual(res["main_audits_scanned"], 15, res)
        self.assertEqual(res["audits_scanned"], 15, res)
        self.assertFalse(any(r.get("frozen_record") is True for r in res["rows"]), res)
        self.assertTrue(res["pass"], res)

    def test_addenda_are_recognised_as_addenda(self):
        addenda = {"forward_block_hac_addendum_20261024.json",
                   "forward_block_independent_recomputation_20261025.json",
                   "forward_block_independent_recomputation_20261028.json",
                   "forward_block_integrity_audit.json"}
        for name in addenda:
            with self.subTest(addendum=name):
                row = next(r for r in self.first["rows"] if r["audit"] == name)
                self.assertIsNone(row["preregistration"])
                self.assertTrue(row["exists"])
                self.assertIn("addendum", row["note"])

    def test_every_resolved_prereq_path_exists_on_disk(self):
        for row in self.first["rows"]:
            if row.get("preregistration") and row.get("exists"):
                self.assertTrue((ROOT / row["resolved"]).is_file(),
                                f"{row['resolved']} does not exist on disk")

    def test_output_file_matches_in_memory_audit(self):
        out = ROOT / "research_state" / "preregistration_coverage_audit.json"
        self.assertTrue(out.is_file(), "coverage audit must write its JSON output")
        on_disk = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, self.first)


if __name__ == "__main__":
    unittest.main()