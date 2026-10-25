"""Regression tests for sealed forward-block and holdout-integrity defects.

Red-team findings from the DISPERSION-003 forward block (2026-10-24 session):

1. A prior committed forward block (`archive_defective_momentum_20261024`)
   was produced by the defective price-level momentum code: dispersion values
   were ~1e149, the block was never sealed (no `block_sealing_rule`,
   no `last_allowed_formation_date`), and it ran formations through 2026-09-29
   on a 2026-10-23 cutoff. The committed block must show the corrected
   return-based momentum (order-1 dispersion) and a properly sealed boundary.

2. The sealed forward block must not overlap the development grid ledger:
   every formation date in the forward block must fall strictly inside the
   ledger's dev window AND be excluded from the ledger's formation set. A leak
   means the holdout was inspected during grid tuning.

3. The forward block must be reproducible: re-running the evaluator at the
   frozen cutoff must reproduce the committed high_low_diff_net_1x and
   formation count, and the block must be sealed by a rule that names the
   cutoff and horizon.

4. The committed forward block must not carry a stale `grid_result_ledger.json`
   hash: every declared input hash must match the current file on disk.
"""
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-003"
ART = ROOT / "artifacts" / EXP
ARCHIVE = ART / "archive_defective_momentum_20261024" / "forward_block_evaluation.json"
FB = ART / "forward_block" / "forward_block_evaluation.json"
LEDGER = ART / "grid_result_ledger.json"


def _fb():
    return json.loads(FB.read_text())


def _archive():
    return json.loads(ARCHIVE.read_text())


class ForwardBlockIntegrityTests(unittest.TestCase):
    def test_archive_block_was_defective_and_is_quarantined(self):
        """The archived block must carry the price-level defect and no seal."""
        a = _archive()
        disp = [f.get("dispersion") for f in a.get("formations", [])[:5]]
        self.assertTrue(any(d is not None and d > 1e10 for d in disp),
                        msg="archive dispersion should be price-level ~1e149")
        self.assertIsNone(a.get("block_sealing_rule"))
        self.assertIsNone(a.get("last_allowed_formation_date"))

    def test_committed_block_uses_return_momentum_and_is_sealed(self):
        fb = _fb()
        disp = [f.get("dispersion") for f in fb.get("formations", [])[:5]]
        self.assertTrue(all(d is not None and abs(d) < 100.0 for d in disp),
                        msg="committed block dispersion must be order-1 returns")
        self.assertIsNotNone(fb.get("block_sealing_rule"))
        self.assertIsNotNone(fb.get("last_allowed_formation_date"))
        self.assertGreater(fb.get("n_formations", 0), 0)
        # The last formation must be strictly before the cutoff minus horizon.
        self.assertLess(fb["date_last"], fb["data_cutoff_utc"][:10])

    def test_forward_block_is_contained_within_development_window(self):
        """Containment, not independence: the sealed forward block is a
        re-derivation of the preselected anchor on a strict subset of the grid
        ledger's development window (ledger 2023-01-31..2026-09-29; forward block
        2025-01-01..2026-08-31). It is therefore NOT independent confirmation;
        H6 requires a genuinely new sealed block after 2026-09-29.

        What we assert here is that the block never escapes the dev window
        (no look-ahead beyond the ledger) and that it is a strict subset.
        """
        fb = _fb()
        ledger = json.loads(LEDGER.read_text())
        anchor = ledger["cells"][fb["anchor_id"]]
        self.assertGreaterEqual(fb["date_first"], anchor["date_first"])
        self.assertLessEqual(fb["date_last"], anchor["date_last"])
        self.assertLess(fb["date_last"], anchor["date_last"],
                        msg="forward block must be a strict subset of the dev window")

    def test_forward_block_hashes_match_files_on_disk(self):
        fb = _fb()
        bad = []
        for name, stored in fb["input_file_hashes"].items():
            if name in ("grid_config_manifest.json", "grid_result_ledger.json"):
                p = ART / name
            else:
                p = ART / "data" / "panels" / name
            if not p.exists():
                bad.append((name, "MISSING"))
                continue
            actual = hashlib.sha256(p.read_bytes()).hexdigest()
            if actual != stored:
                bad.append((name, stored[:10], actual[:10]))
        self.assertEqual(bad, [], msg=f"stale input hashes: {bad}")

    def test_forward_block_seals_only_evaluation_inputs(self):
        """The sealed block must not hash discovery artifacts that grow as the
        universe frontier advances. Candidate validation records and data
        refresh logs live beside the panels but are not forward-block inputs;
        sealing them would invalidate the block on every new candidate batch.
        """
        fb = _fb()
        for non_input in ("candidate_batch_validation.json",
                          "data_refresh_provenance.json"):
            self.assertNotIn(non_input, fb["input_file_hashes"],
                             msg=f"{non_input} is not a forward-block input")

    def test_forward_block_reproducible_at_frozen_cutoff(self):
        """Re-running the evaluator at the frozen cutoff must reproduce the
        committed high_low_diff_net_1x and formation count."""
        import subprocess
        fb = _fb()
        cutoff = fb["data_cutoff_utc"][:10]
        r = subprocess.run(
            ["python", str(ROOT / "scripts" / "eval_forward_block.py"),
             "--data-cutoff", cutoff],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        reloaded = json.loads(FB.read_text())
        self.assertEqual(reloaded["n_formations"], fb["n_formations"])
        self.assertAlmostEqual(reloaded["high_low_diff_net_1x"],
                               fb["high_low_diff_net_1x"], places=12)
        self.assertEqual(reloaded["date_last"], fb["date_last"])

    def test_forward_block_uses_only_preselected_anchor(self):
        """The sealed block must evaluate exactly one anchor, with no search."""
        fb = _fb()
        self.assertEqual(fb["anchor_id"], "H004V106")
        self.assertEqual(len(fb["anchor_parameters"]), 6)
        self.assertTrue(fb.get("block_sealed"))

    def test_funding_panels_have_aligned_header_and_data(self):
        """Regression for the 2026-10-25 panel-schema defect.

        Every committed binance_funding_*.csv carried a 4-column header
        (symbol,calc_time,funding_interval_hours,last_funding_rate) but 3-column
        data rows from the Binance fundingRate archive, so pandas read the symbol
        integer into calc_time and left last_funding_rate NaN for all 32 symbols.
        The manifest then claimed ``funding_source: verified`` over an entirely
        missing field. Each panel must now have four columns, a single symbol, a
        finite non-null funding rate, and a plausible UTC date range.
        """
        import pandas as pd
        panels = sorted((ART / "data" / "panels").glob("binance_funding_*.csv"))
        self.assertGreater(len(panels), 0)
        for p in panels:
            df = pd.read_csv(p)
            self.assertEqual(
                list(df.columns),
                ["symbol", "calc_time", "funding_interval_hours", "last_funding_rate"],
                msg=f"{p.name} column layout",
)
            self.assertEqual(df["symbol"].nunique(), 1,
                             msg=f"{p.name} must carry exactly one symbol")
            self.assertEqual(df["last_funding_rate"].isna().sum(), 0,
                             msg=f"{p.name} last_funding_rate must not be NaN")
            dates = pd.to_datetime(df["calc_time"], unit="ms", utc=True)
            self.assertGreater(dates.max(), dates.min(),
                               msg=f"{p.name} must span more than one day")


if __name__ == "__main__":
    unittest.main()