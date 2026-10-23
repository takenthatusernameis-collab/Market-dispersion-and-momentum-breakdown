import csv, json, unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
EXP = "HARMONY-CRYPTO-EDGE-004-DISPERSION-002"
ART = root / "artifacts" / EXP


def _json(name):
    return json.loads((ART / name).read_text())


class DataPipeline(unittest.TestCase):
    def test_universe_coverage_columns(self):
        p = ART / "data" / "panels" / "universe_coverage.csv"
        self.assertTrue(p.exists())
        with p.open() as fh:
            header = fh.readline().strip().split(",")
        required = ["date", "rank", "asset_id", "contract_symbol",
                    "CapMrktEstUSD", "CapMrktCurUSD", "eligible",
                    "has_price", "has_funding", "included", "exclusion_reason"]
        for col in required:
            self.assertIn(col, header)

    def test_universe_ranking_monotonic(self):
        p = ART / "data" / "panels" / "universe_coverage.csv"
        with p.open() as fh:
            rows = list(csv.DictReader(fh))
        by_date = {}
        for r in rows:
            by_date.setdefault(r["date"], []).append(r)
        for date, group in by_date.items():
            elig = [r for r in group if r["eligible"] == "yes" and r["rank"] != ""]
            if not elig:
                continue
            ranks = [int(r["rank"]) for r in elig]
            self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_formation_returns_conditioned_columns(self):
        p = ART / "formation_returns_conditioned.csv"
        self.assertTrue(p.exists())
        with p.open() as fh:
            header = fh.readline().strip().split(",")
        required = ["formation_date", "n_assets", "dispersion",
                    "momentum_spread_gross", "momentum_spread_net_1x", "state"]
        for col in required:
            self.assertIn(col, header)

    def test_phase_summaries_exist(self):
        self.assertTrue((ART / "phase_c_summary.json").exists())
        self.assertTrue((ART / "phase_e_summary.json").exists())
        self.assertTrue((ART / "phase_f_summary.json").exists())

    def test_experiment_setup_valid(self):
        setup = _json("experiment_setup.json")
        self.assertEqual(setup["experiment_id"], "HARMONY-CRYPTO-EDGE-004-DISPERSION-002")
        self.assertTrue(setup["controls"]["free_data_only"])


if __name__ == "__main__":
    unittest.main()
