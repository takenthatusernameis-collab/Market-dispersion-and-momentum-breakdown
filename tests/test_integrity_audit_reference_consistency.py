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
- frozen_git_head_checks present for known frozen artifacts.
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
        "9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a",
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
            if c["git_head_sha256"] is not None:
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
            for chk in row["recorded_hash_checks"]:
                if chk["match"] is not None:
                    self.assertTrue(
                        chk["match"],
                        f"{row['file']} {chk['hash_key']} recorded={chk['recorded']} "
                        f"disk={chk['disk_sha256']} target={chk['target_path']}")


if __name__ == "__main__":
    unittest.main()
