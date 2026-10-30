"""Regression test for the outcome ledger <-> frozen manifest parameter binding.

The 216-cell grid result ledger (artifacts/.../grid_result_ledger.json) is the
only artifact that carries forward outcomes, and each of its cells declares a
`parameters` block and a `config_id`. The frozen grid config manifest
(grid_config_manifest.json) is the parameter authority: it is generated
deterministically from configs/dispersion_momentum_grid_v3.json before any
outcome is computed, and it is what the forward-block integrity tests hash.

Nothing previously asserted that the ledger's per-cell parameters actually
agree with the manifest. A drift there is the exact defect that would let an
outcome be silently attached to the wrong configuration -- for example a
hand-edited ledger row whose parameters no longer match its config_id, or a
regeneration that re-ordered the enumeration and left stale outcomes behind.
The deterministic-regeneration test in test_grid_validation.py only checks
the manifest against the config; it never looks at the ledger at all.

This test pins the binding in both directions:
  1. every ledger config_id is present in the manifest and vice versa;
  2. every ledger cell's `parameters` dict equals the manifest row's
     `parameters` dict exactly;
  3. every ledger cell's `universe_arm` agrees with its parameters;
  4. the canonical JSON of each ledger cell's parameters hashes to the manifest
     row's `config_sha256`, so a cell cannot carry parameters that hash to a
     different identity than the one the manifest assigns its config_id.

Read-only: no files are written.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
MANIFEST = ART / "grid_config_manifest.json"
LEDGER = ART / "grid_result_ledger.json"


def _canonical(parameters):
    return json.dumps(parameters, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


class LedgerManifestBindingTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.rows = {r["config_id"]: r for r in self.manifest["configurations"]}
        self.cells = self.ledger["cells"]

    def test_ledger_and_manifest_share_the_same_config_id_set(self):
        self.assertEqual(
            sorted(self.cells.keys()),
            sorted(self.rows.keys()),
            msg="ledger config_id set must equal the manifest config_id set",
        )
        self.assertEqual(len(self.cells), 216)
        self.assertEqual(len(self.rows), 216)

    def test_every_ledger_cell_parameters_match_the_manifest_row(self):
        mismatches = []
        for cid, cell in self.cells.items():
            if cell.get("parameters") != self.rows[cid]["parameters"]:
                mismatches.append(cid)
        self.assertEqual(
            mismatches, [],
            msg=f"ledger cells whose parameters differ from the manifest: {mismatches}",
        )

    def test_every_ledger_universe_arm_matches_its_parameters(self):
        bad = []
        for cid, cell in self.cells.items():
            arm = cell.get("universe_arm")
            params_arm = cell["parameters"].get("universe_arm")
            if arm != params_arm:
                bad.append((cid, arm, params_arm))
        self.assertEqual(bad, [], msg=f"universe_arm drift: {bad}")

    def test_ledger_parameter_hash_matches_manifest_sha256(self):
        bad = []
        for cid, cell in self.cells.items():
            expected = self.rows[cid]["config_sha256"]
            actual = hashlib.sha256(
                _canonical(cell["parameters"]).encode("utf-8")
            ).hexdigest()
            if actual != expected:
                bad.append((cid, expected[:12], actual[:12]))
        self.assertEqual(
            bad, [],
            msg=f"ledger cells whose parameter hash differs from manifest sha256: {bad}",
        )

    def test_ledger_cells_carry_no_outcome_for_a_nonexistent_config(self):
        # Guard against a cell being attached to a config_id the manifest does
        # not declare (e.g. a hand-added H004V999 row).
        orphans = sorted(set(self.cells) - set(self.rows))
        self.assertEqual(orphans, [], msg=f"ledger cells absent from manifest: {orphans}")

    def test_ledger_terminal_statuses_are_recorded_for_every_cell(self):
        # Every cell must declare one of the protocol's terminal statuses and
        # carry a `reason` field; an outcome-bearing ledger must not contain a
        # not-run cell. A successful cell legitimately has an empty reason
        # string, but any blocked/failed/invalid cell must say why it stopped.
        allowed = {"OK", "BLOCKED", "INVALID", "FAILED", "NOT_RUN"}
        unrecorded = [
            cid for cid, cell in self.cells.items()
            if cell.get("status") not in allowed or "reason" not in cell
        ]
        self.assertEqual(
            unrecorded, [],
            msg=f"cells missing a terminal status and reason: {unrecorded}",
        )
        unexplained = [
            cid for cid, cell in self.cells.items()
            if cell["status"] != "OK" and not cell.get("reason")
        ]
        self.assertEqual(
            unexplained, [],
            msg=f"non-OK cells with no explanatory reason: {unexplained}",
        )
        self.assertNotIn("NOT_RUN", {c["status"] for c in self.cells.values()},
                         msg="outcome ledger must not contain not-run cells")


if __name__ == "__main__":
    unittest.main()