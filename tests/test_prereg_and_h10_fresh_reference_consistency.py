"""Regression guard for scripts/audit_prereg_and_h10_fresh_references.py.

Read-only: scans preregistration markdown under
artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/preregistrations/ and the
forward_block_h10_fresh JSON for stale path references, missing referenced
files, recorded hash mismatches and frozen/git-HEAD drift. Writes nothing (tests
call run_audit(), not main()).

Pins:
- script is importable and run_audit() is deterministic across calls;
- no CRITICAL or ERROR findings (a stale pointer, a missing referenced file, a
  disk/frozen/git-HEAD drift or a recorded-hash mismatch is a defect, not noise);
- the two frozen forward-block hashes match disk and git HEAD;
- every path reference in every prereg doc resolves to a file on disk and
  matches its frozen hash where one is declared;
- the path-shape guard (_path_like) is pinned: a prose field value such as
  data_cutoff_source="derived from latest fully closed UTC daily Binance kline
  candle (or --data-cutoff)" must NOT be treated as a path reference and must
  NOT be reported as a missing artifact. This is the guard that prevents the
  false positive that made the 20261107T194102Z report pass=false with 3 ERRORs.
"""
import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "scripts" / "audit_prereg_and_h10_fresh_references.py"

spec = importlib.util.spec_from_file_location("prereg_h10_ref", SPEC_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FROZEN = {
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block/forward_block_evaluation.json":
        "7234fc4e23b8dd07e0a2f5b1af111d4d5eaff14b93991d10737239c42f815390",
    "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh/forward_block_evaluation.json":
        "9bdee66f737e492b3302a730af29ab9f811611e5a908ccf6002d08eab3e8bc5a",
}

PROSE = "derived from latest fully closed UTC daily Binance kline candle (or --data-cutoff)"


class PreregAndH10FreshReferenceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first = mod.run_audit()
        cls.second = mod.run_audit()

    def test_script_is_importable_and_deterministic(self):
        self.assertEqual(self.first, self.second)

    def test_no_critical_or_error_findings(self):
        self.assertFalse(self.first["critical"], f"CRITICAL: {self.first['critical']}")
        self.assertFalse(self.first["errors"], f"ERROR: {self.first['errors']}")
        self.assertTrue(self.first["pass"], self.first)

    def test_frozen_hashes_match_disk_and_git_head(self):
        self.assertEqual(len(self.first["frozen_checks"]), len(FROZEN))
        by_path = {c["path"]: c for c in self.first["frozen_checks"]}
        for rel, expected in FROZEN.items():
            with self.subTest(artifact=rel):
                self.assertIn(rel, by_path)
                c = by_path[rel]
                self.assertEqual(c["expected"], expected)
                self.assertTrue(c["matches_frozen"], c)
                self.assertEqual(c["disk_sha256"], expected, c)
                if c["git_head_sha256"] is not None:
                    self.assertTrue(c["matches_git_head"], c)
                    self.assertEqual(c["git_head_sha256"], expected, c)

    def test_all_prereg_path_refs_resolve_on_disk(self):
        for row in self.first["rows"]:
            if row["kind"] != "preregistration_md":
                continue
            for ref in row["path_refs"]:
                with self.subTest(file=row["file"], path=ref["path"]):
                    self.assertTrue(ref["exists"],
                                    f"{row['file']} references missing path {ref['path']}")
                    if ref["frozen_expected"]:
                        self.assertTrue(ref["matches_frozen"],
                                        f"{row['file']} frozen mismatch for {ref['path']}: "
                                        f"disk={ref['disk_sha256']} expected={ref['frozen_expected']}")

    def test_all_h10_json_references_resolve_on_disk(self):
        for row in self.first["rows"]:
            if row["kind"] != "h10_fresh_json":
                continue
            for ref in row["references"]:
                with self.subTest(file=row["file"], key=ref["key"], path=ref["path"]):
                    self.assertTrue(ref["exists"],
                                    f"{row['file']} {ref['key']}={ref['path']} missing")
                    if ref["frozen_expected"]:
                        self.assertTrue(ref["matches_frozen"], ref)
                    if ref.get("git_head_sha256"):
                        self.assertTrue(ref["matches_git_head"], ref)

    def test_recorded_hash_checks_match_when_present(self):
        for row in self.first["rows"]:
            for chk in row.get("recorded_hash_checks", []):
                if chk["match"] is not None:
                    self.assertTrue(
                        chk["match"],
                        f"{row['file']} {chk['hash_key']} recorded={chk['recorded']} "
                        f"disk={chk['disk_sha256']} target={chk['target_path']}")

    def test_path_like_rejects_prose_field_values(self):
        """The data_cutoff_source field carries a prose description, not a
        path. _path_like must reject it so it is not reported as a missing
        artifact. Genuine path references (slash + known extension) still pass.
        """
        self.assertFalse(mod._path_like(PROSE))
        self.assertFalse(mod._path_like(""))
        self.assertFalse(mod._path_like("the panel was refreshed"))
        self.assertTrue(mod._path_like("artifacts/HARMONY-CRYPTO-EDGE-004-"
                                       "DISPERSION-003/forward_block/forward_block_evaluation.json"))
        self.assertTrue(mod._path_like("scripts/eval_forward_block.py"))

    def test_data_cutoff_source_is_not_a_path_reference(self):
        """End-to-end pin on the exact false positive that made the
        20261107T194102Z report pass=false: the h10 fresh JSON's
        data_cutoff_source must not appear in the errors list."""
        self.assertNotIn(
            "forward_block_evaluation.json:missing referenced artifact: "
            "data_cutoff_source=" + PROSE,
            self.first["errors"],
        )


if __name__ == "__main__":
    unittest.main()