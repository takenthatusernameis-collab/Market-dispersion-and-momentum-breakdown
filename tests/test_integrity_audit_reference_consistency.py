"""Regression guard for scripts/audit_integrity_audit_references.py.

Read-only: scans existing integrity_audit/ JSONs for stale pointers, recorded
hash mismatches, and frozen-artifact drift. Writes nothing (tests call
run_audit(), not main()).

Pins:
- script is importable and run_audit() is deterministic in structure;
- no CRITICAL/ERROR findings (stale pointer, disk/git-HEAD drift, or hash
  mismatch requires investigation);
- H004V106 canonical and H10 fresh frozen hashes match disk and git HEAD;
- audited artifacts referenced by integrity audits resolve on disk;
- frozen_git_head_checks present for known frozen artifacts;
- the F1 sub-experiment integrity_audit dirs (F1COVERAGE-001, F1SENS-002,
  F1STAB-003) are scanned by default as frozen records: their 5 JSONs are
  included in files_scanned, parse OK, carry no CRITICAL/ERROR, and the scan
  can be opted out of with f1_integrity_audit_dirs=[].
"""
import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_integrity_audit_references.py"

spec = importlib.util.spec_from_file_location("integrity_audit_ref", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FROZEN = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json":
        "324ab1e6dbcf8069b1f747c3e289bc60737df36cefdc806f3779a1c73e5df18f",
}

F1_INTEGRITY_AUDIT_FILES = {
    "f1_panel_coverage_repair_20261112T172845Z.json",
    "f1_panel_coverage_repair_20261112T172913Z.json",
    "f1_panel_coverage_repair_20261112T183449Z.json",
    "f1_coverage_outcome_sensitivity_20261113T025950Z.json",
    "f1_coverage_stability_audit_20261113T054921Z.json",
}


class IntegrityAuditReferenceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = mod.run_audit()

    def test_no_critical_or_error_findings(self):
        self.assertFalse(self.res["critical"],
                         f"CRITICAL: {self.res['critical']}")
        self.assertFalse(self.res["errors"],
                         f"ERROR: {self.res['errors']}")
        self.assertTrue(self.res["pass"], self.res)

    def test_scanned_expected_integrity_audit_dir(self):
        self.assertGreaterEqual(self.res["files_scanned"], 14)
        for row in self.res["rows"]:
            self.assertTrue(row["parse_ok"], f"{row['file']} failed to parse")

    def test_frozen_hashes_match_disk(self):
        for rel, expected in FROZEN.items():
            p = ROOT / rel
            self.assertTrue(p.is_file(), f"frozen artifact missing: {rel}")
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(actual, expected, f"FROZEN drift: {rel}")

    def test_frozen_git_head_checks_present_and_clean(self):
        checks = self.res.get("frozen_git_head_checks", [])
        self.assertEqual(len(checks), len(FROZEN), checks)
        by_path = {c["path"]: c for c in checks}
        for rel, expected in FROZEN.items():
            self.assertIn(rel, by_path, checks)
            c = by_path[rel]
            self.assertTrue(c["matches_frozen"], c)
            self.assertEqual(c["disk_sha256"], expected, c)
            # git_head_drift is CRITICAL only when HEAD is the expected frozen
            # blob but disk diverged. A repaired artifact (disk+pin updated, HEAD
            # still at the old blob until commit) is not drift; it must match the
            # FROZEN pin and not be flagged as drift.
            self.assertFalse(c.get("git_head_drift", False), c)
            if c["git_head_sha256"] is not None and c["git_head_sha256"] == expected:
                self.assertTrue(c["matches_git_head"], c)
                self.assertEqual(c["git_head_sha256"], expected, c)

    def test_all_referenced_paths_exist(self):
        for row in self.res["rows"]:
            for ref in row["references"]:
                self.assertTrue(ref["exists"],
                                f"{row['file']} references missing {ref['key']}={ref['path']}")
                if ref["frozen_expected"]:
                    self.assertTrue(ref["matches_frozen"],
                                    f"{row['file']} frozen mismatch for {ref['path']}")
                if "matches_git_head" in ref and ref.get("git_head_sha256"):
                    self.assertTrue(ref["matches_git_head"],
                                    f"{row['file']} git-HEAD mismatch for {ref['path']}")

    def test_recorded_hash_checks_match_when_present(self):
        for row in self.res["rows"]:
            for chk in row.get("recorded_hash_checks", []):
                if chk["match"] is not None:
                    self.assertTrue(
                        chk["match"],
                        f"{row['file']} {chk['hash_key']} recorded={chk['recorded']} "
                        f"disk={chk['disk_sha256']} target={chk['target_path']}")

    def test_f1_frozen_integrity_audit_dirs_scanned_by_default(self):
        """The F1 sub-experiment integrity_audit dirs (F1COVERAGE-001,
        F1SENS-002, F1STAB-003) are scanned by default as frozen records, so
        their committed audit JSONs cannot hide outside the consistency check."""
        self.assertGreaterEqual(
            self.res.get("frozen_integrity_audit_files_scanned", 0), 5,
            self.res)
        self.assertGreaterEqual(self.res["files_scanned"], 19, self.res)
        scanned_names = {r["file"] for r in self.res["rows"]}
        self.assertTrue(F1_INTEGRITY_AUDIT_FILES.issubset(scanned_names),
                        f"F1 integrity audit files missing from scan: "
                        f"{sorted(F1_INTEGRITY_AUDIT_FILES - scanned_names)}")
        f1_rows = [r for r in self.res["rows"] if r.get("frozen_record") is True]
        self.assertGreaterEqual(len(f1_rows), 5, "expected at least 5 frozen F1 rows")
        for row in f1_rows:
            with self.subTest(file=row["file"]):
                self.assertEqual(row["frozen_record"], True, row)
                self.assertIn(row["severity"], ("OK", "INFO"), row)

    def test_f1_frozen_integrity_audit_rows_parse_ok(self):
        f1_rows = [r for r in self.res["rows"] if r.get("frozen_record") is True]
        for row in f1_rows:
            self.assertTrue(row["parse_ok"],
                            f"F1 integrity audit {row['file']} failed to parse")

    def test_f1_frozen_integrity_audit_no_critical_or_error_from_frozen_rows(self):
        """Frozen F1 audit records must never flip pass=False: any stale
        pointer is INFO (frozen_record_stale_pointer), never ERROR."""
        f1_rows = [r for r in self.res["rows"] if r.get("frozen_record") is True]
        for row in f1_rows:
            with self.subTest(file=row["file"]):
                self.assertNotEqual(row["severity"], "CRITICAL", row)
                self.assertNotEqual(row["severity"], "ERROR", row)
                for f in row["findings"]:
                    self.assertNotIn("missing referenced artifact:", f, row)
        self.assertFalse(self.res["critical"], self.res["critical"])
        self.assertFalse(self.res["errors"], self.res["errors"])
        self.assertTrue(self.res["pass"], self.res)

    def test_f1_frozen_integrity_audit_scan_can_be_disabled(self):
        """The default F1 frozen-integrity-audit scan is opt-out for callers
        that need a narrow scope."""
        res = mod.run_audit(f1_integrity_audit_dirs=[])
        self.assertEqual(res.get("frozen_integrity_audit_files_scanned", 0), 0)
        self.assertFalse(any(r.get("frozen_record") is True for r in res["rows"]))
        self.assertEqual(res.get("main_integrity_audit_files_scanned"), 14, res)
        self.assertTrue(res["pass"], res.get("errors"))


if __name__ == "__main__":
    unittest.main()
