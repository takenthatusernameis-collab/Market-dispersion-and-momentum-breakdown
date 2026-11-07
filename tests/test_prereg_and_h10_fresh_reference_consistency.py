"""Regression guard for scripts/audit_prereg_and_h10_fresh_references.py.

Read-only: scans DISP-003 preregistration markdown, the canonical
forward_block_evaluation.json, and forward_block_h10_fresh JSON for stale path
references, missing referenced files, recorded hash mismatches and frozen/git-HEAD
drift. Writes nothing (tests call run_audit(), not main()).

Pins:
- script is importable and run_audit() is deterministic across calls;
- no CRITICAL or ERROR findings in default scope (a stale pointer, a missing
  referenced file, a disk/frozen/git-HEAD drift or a recorded-hash mismatch is
  a defect, not noise);
- the two frozen forward-block hashes match disk and git HEAD;
- every path reference in every prereg doc resolves to a file on disk and
  matches its frozen hash where one is declared;
- the path-shape guard (_path_like) is pinned: a prose field value such as
  data_cutoff_source="derived from latest fully closed UTC daily Binance kline
  candle (or --data-cutoff)" must NOT be treated as a path reference and must
  NOT be reported as a missing artifact. This is the guard that prevents the
  false positive that made the 20261107T194102Z report pass=false with 3 ERRORs.
- canonical forward_block_evaluation.json is scanned by default (kind
  forward_block_canonical_json) and has no CRITICAL/ERROR findings;
- frozen pre-DISP-003 prereg dirs (DISP-002, via --include-disp002-preregs path
  in CLI / frozen_prereg_dirs in API) report stale pointers as INFO
  (frozen_record_stale_pointer) and do NOT flip pass=False, because immutable
  closed preregistration records must never be modified.
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

    def test_canonical_forward_block_scanned_by_default(self):
        """Canonical forward_block_evaluation.json must be in default scope
        (task 20261107T205304Z: extend audit coverage to canonical forward_block
        JSON ref fields). Its frozen hash is checked in frozen_checks; the row
        must exist with no CRITICAL/ERROR."""
        kinds = {(r["file"], r["kind"]) for r in self.first["rows"]}
        self.assertIn(("forward_block_evaluation.json", "forward_block_canonical_json"), kinds)
        canon = [r for r in self.first["rows"] if r["file"] == "forward_block_evaluation.json"]
        self.assertTrue(canon)
        self.assertNotEqual(canon[0]["severity"], "CRITICAL", canon[0])
        self.assertNotEqual(canon[0]["severity"], "ERROR", canon[0])
        self.assertGreaterEqual(self.first.get("forward_block_json_files_scanned", 0), 1)

    def test_frozen_predisp003_prereg_stale_pointer_is_info_not_error(self):
        """DISPERSION-002 preregistration is an immutable closed record. A stale
        path pointer inside it (e.g. DISPENSITY typo in PHASE-B-PLACEBO-V1.md)
        must be surfaced as INFO (frozen_record_stale_pointer), not as ERROR, and
        must not flip pass=False. The file itself is never modified."""
        res = mod.run_audit(frozen_prereg_dirs=[mod.DISP002_PREREG_DIR])
        self.assertTrue(res["pass"], res["errors"])
        self.assertFalse(res["errors"], res["errors"])
        self.assertGreaterEqual(res.get("frozen_prereg_files_scanned", 0), 1)
        frozen_rows = [r for r in res["rows"] if r.get("frozen_record") is True]
        self.assertTrue(frozen_rows, "expected at least one frozen prereg row")
        for row in frozen_rows:
            self.assertIn(row["severity"], ("OK", "INFO"), row)
            for f in row["findings"]:
                self.assertNotIn("missing referenced path:", f)
        # the known DISP-002 stale pointer remains visible as INFO
        info_joined = "\n".join(res["info"])
        self.assertIn("frozen_record_stale_pointer", info_joined)
        self.assertIn("PHASE-B-PLACEBO-V1.md", info_joined)

    def test_h10_variant_dirs_scanned_read_only_by_default(self):
        """Non-frozen H10 variant dirs (forward_block_h10/, forward_block_h10_fresh_check/)
        exist as unreferenced throwaway outputs. The audit scans them read-only as
        h10_variant_json (they are not FROZEN targets) so stale internal refs cannot hide.
        They must not introduce CRITICAL/ERROR or flip pass=False, and FROZEN still pins
        only forward_block/ + forward_block_h10_fresh/."""
        variants = [r for r in self.first["rows"] if r["kind"] == "h10_variant_json"]
        # if dirs are present on disk, they must be scanned; if absent, count is 0 (no false fail)
        self.assertEqual(self.first.get("h10_variant_json_files_scanned"), len(variants))
        for r in variants:
            with self.subTest(file=r["file"], variant_dir=r.get("variant_dir")):
                self.assertNotEqual(r["severity"], "CRITICAL", r)
                self.assertNotEqual(r["severity"], "ERROR", r)
                self.assertIn("variant_dir", r)
                self.assertNotEqual(r["variant_dir"], "forward_block_h10_fresh")
        frozen_paths = set(self.first.get("frozen_hashes_checked", {}).keys())
        self.assertNotIn(
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10/forward_block_evaluation.json",
            frozen_paths,
        )
        self.assertNotIn(
            "artifacts/HARMONY-CRYPTO-EDGE-004-DISPERSION-003/forward_block_h10_fresh_check/forward_block_evaluation.json",
            frozen_paths,
        )
        self.assertTrue(self.first["pass"], self.first.get("errors"))

    def test_h10_variant_scan_can_be_disabled(self):
        """Disabling variant scan is supported for callers that need a narrow scope."""
        res = mod.run_audit(include_h10_variants=False)
        self.assertEqual(res.get("h10_variant_json_files_scanned", 0), 0)
        self.assertFalse(any(r["kind"] == "h10_variant_json" for r in res["rows"]))
        self.assertTrue(res["pass"], res.get("errors"))


if __name__ == "__main__":
    unittest.main()